import asyncio
import contextlib
import io
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from .capture import FPS, Camera, DemoCamera, encode_clip
from .config import Settings, minutes, save_json
from .detection import Detector, Observation
from .storage import Store


def jpeg_bytes(frame, demo=False):
    image = Image.fromarray(frame)
    if demo:
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 640, 28), fill="black")
        draw.text((12, 8), "DEMO - SYNTHETIC TEST PATTERN - NOT TANK FOOTAGE", fill="white")
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=82)
    return buffer.getvalue()


class Monitor:
    def __init__(self, settings: Settings, directory, demo=False, ffmpeg="ffmpeg"):
        self.settings, self.directory, self.demo, self.ffmpeg = settings, directory, demo, ffmpeg
        self.store = Store(directory)
        self.detector = Detector(settings)
        self.frame = None
        self.last_frame_at = self.last_frame_clock = None
        self.started = time.monotonic()
        self.camera_state = "not_configured"
        self.capture_task = self.watch_task = None
        self.clip_tasks = set()
        self.buffer = deque(maxlen=FPS * 15)
        self.paused_until = 0
        self.offline_reported = False
        self.last_metric = self.last_prune = 0
        self.last_error = None

    async def start(self):
        self.store.prune(self.settings.retention_days)
        self.watch_task = asyncio.create_task(self.watchdog())
        self.restart_capture()

    def restart_capture(self):
        self.started = time.monotonic()
        self.last_frame_at = self.last_frame_clock = None
        self.frame = None
        self.buffer.clear()
        self.offline_reported = False
        self.last_error = None
        self.detector = Detector(self.settings)
        if self.settings.camera_url or self.demo:
            self.camera_state = "connecting"
            self.capture_task = asyncio.create_task(self.capture_loop())
        else:
            self.camera_state = "not_configured"
            self.capture_task = None

    async def configure(self, settings):
        if self.capture_task:
            self.capture_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.capture_task
        save_json(self.directory / "settings.json", settings.model_dump())
        self.settings = settings
        self.restart_capture()

    def fresh(self):
        return self.last_frame_clock is not None and time.monotonic() - self.last_frame_clock < 3

    async def capture_loop(self):
        delay = 2
        while True:
            source = DemoCamera() if self.demo else Camera(self.settings.camera_url, self.ffmpeg)
            try:
                async for frame in source.frames():
                    clock, at = time.monotonic(), time.time()
                    recovering = self.offline_reported
                    if self.last_frame_clock is None or clock - self.last_frame_clock > 2:
                        self.buffer.clear()
                        self.detector.reset_temporal()
                    self.frame = jpeg_bytes(frame, self.demo)
                    self.buffer.append(self.frame)
                    self.last_frame_clock, self.last_frame_at = clock, at
                    self.camera_state, self.last_error = "connected", None
                    self.offline_reported = False
                    delay = 2
                    if recovering:
                        self.record(
                            Observation(
                                "camera_recovered",
                                "Camera connection restored",
                                "Fresh frames are arriving again.",
                            )
                        )
                    now = datetime.fromtimestamp(at, timezone.utc)
                    for event in self.detector.process(
                        frame, now, clock, clock < self.paused_until
                    ):
                        self.record(event)
                    if clock - self.last_metric >= 30:
                        self.store.metric(at, self.detector.metrics)
                        self.last_metric = clock
                    self.daily_snapshot(now)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.camera_state = "reconnecting"
                self.last_error = (
                    "Unable to read video. Check FFmpeg, camera power, Wi-Fi, and RTSP settings."
                )
                self.detector.reset_temporal()
                self.buffer.clear()
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)

    async def watchdog(self):
        while True:
            await asyncio.sleep(1)
            clock = time.monotonic()
            configured = bool(self.settings.camera_url) or self.demo
            reference = self.last_frame_clock if self.last_frame_clock is not None else self.started
            if configured and clock - reference >= self.settings.offline_seconds:
                self.camera_state = "offline"
                if not self.offline_reported:
                    self.offline_reported = True
                    self.record(
                        Observation(
                            "camera_offline",
                            "Camera feed unavailable",
                            "No fresh frames. Tank observations are unavailable.",
                        ),
                        evidence=False,
                    )
            if clock - self.last_prune >= 3600:
                self.store.prune(self.settings.retention_days)
                self.last_prune = clock

    def record(self, event, evidence=True):
        item_id = uuid.uuid4().hex
        snapshot = None
        if evidence and self.fresh() and self.frame:
            snapshot = f"{item_id}.jpg"
            (self.store.media / snapshot).write_bytes(self.frame)
        self.store.event(item_id, event, time.time(), snapshot)
        if snapshot and len(self.buffer) >= FPS * 2 and len(self.clip_tasks) < 2:
            task = asyncio.create_task(self.make_clip(item_id, list(self.buffer)))
            self.clip_tasks.add(task)
            task.add_done_callback(self.clip_tasks.discard)

    async def make_clip(self, item_id, frames):
        filename = f"{item_id}.mp4"
        path = self.store.media / filename
        try:
            await encode_clip(frames, path, self.ffmpeg)
            self.store.attach_clip(item_id, filename)
        except (Exception, asyncio.CancelledError):
            path.unlink(missing_ok=True)

    def snapshot(self, automatic=False):
        if not self.fresh() or self.frame is None:
            raise ValueError("A fresh camera frame is required.")
        item_id = uuid.uuid4().hex
        filename = f"{item_id}.jpg"
        now = datetime.now(ZoneInfo(self.settings.timezone))
        day = now.date().isoformat()
        (self.store.media / filename).write_bytes(self.frame)
        self.store.snapshot(item_id, time.time(), day, filename, automatic)
        return filename

    def daily_snapshot(self, now):
        local = now.astimezone(ZoneInfo(self.settings.timezone))
        target = minutes(self.settings.snapshot_at)
        minute = local.hour * 60 + local.minute
        if (
            0 <= minute - target < 30
            and self.detector.metrics["phase"] == "day"
            and time.monotonic() >= self.paused_until
            and not self.store.has_daily(local.date().isoformat())
        ):
            self.snapshot(automatic=True)

    def status(self):
        fresh = self.fresh()
        paused = max(0, self.paused_until - time.monotonic())
        metrics = (
            self.detector.metrics
            if fresh
            else {"brightness": None, "motion": None, "phase": "unknown"}
        )
        return {
            "camera": self.camera_state,
            "fresh": fresh,
            "last_frame_at": self.last_frame_at,
            "error": self.last_error,
            "demo": self.demo,
            "metrics": metrics,
            "calibration": self.detector.calibration_message,
            "calibration_active": self.detector.calibration_start is not None,
            "motion_reference": self.detector.baseline,
            "active_checks": sorted(self.detector.active) if fresh else [],
            "paused_seconds": round(paused),
            "settings": self.settings.public(),
            "events": self.store.events(),
            "snapshots": self.store.snapshots(),
        }

    async def stop(self):
        for task in (self.capture_task, self.watch_task):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        pending = list(self.clip_tasks)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        self.store.close()
