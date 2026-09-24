import asyncio
import shutil
import time
import uuid

import numpy as np
import pytest

from reefwatch.capture import Camera, camera_command, encode_clip
from reefwatch.config import Settings
from reefwatch.detection import Observation
from reefwatch.monitor import Monitor, jpeg_bytes
from reefwatch.storage import Store


def test_camera_command_passes_url_as_one_argument():
    url = "rtsp://user:$(example)@127.0.0.1/live0"
    command = camera_command(url)
    assert command[command.index("-i") + 1] == url
    assert command[command.index("-rtsp_transport") + 1] == "tcp"


def test_stale_frames_not_presented_as_live(tmp_path):
    monitor = Monitor(Settings(), tmp_path)
    monitor.last_frame_clock = time.monotonic() - 10
    monitor.detector.metrics = {"brightness": 30, "motion": 5, "phase": "day"}
    assert monitor.status()["fresh"] is False
    assert monitor.status()["metrics"]["brightness"] is None
    with pytest.raises(ValueError):
        monitor.snapshot()
    monitor.store.close()


def test_retention_prunes_history_and_only_owned_expired_media(tmp_path):
    store = Store(tmp_path)
    identifier = uuid.uuid4().hex
    old_file = store.media / f"{identifier}.jpg"
    old_file.write_bytes(b"old")
    import os

    os.utime(old_file, (0, 0))
    unrelated = store.media / "my-photo.jpg"
    unrelated.write_bytes(b"keep")
    os.utime(unrelated, (0, 0))
    store.event(identifier, Observation("test", "test", "test"), 1, old_file.name)
    store.prune(1, now=200000)
    assert not store.events()
    assert not old_file.exists()
    assert unrelated.exists()
    store.close()


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg required")
def test_clip_is_real_decodable_mp4(tmp_path):
    frames = [jpeg_bytes(np.full((360, 640, 3), n * 20, np.uint8)) for n in range(8)]
    path = tmp_path / "evidence.mp4"
    asyncio.run(encode_clip(frames, path))
    import subprocess

    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True
    )
    assert result.returncode == 0
    assert path.stat().st_size > 1000


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg required")
def test_failed_rtsp_connection_finishes_without_hanging():
    async def run():
        source = Camera("rtsp://127.0.0.1:1/live0")
        with pytest.raises((asyncio.IncompleteReadError, TimeoutError)):
            await asyncio.wait_for(anext(source.frames()), 15)

    asyncio.run(run())


def test_outage_watchdog_works_during_pause_and_records_recovery(tmp_path):
    async def run():
        monitor = Monitor(Settings(), tmp_path, demo=True)
        monitor.last_frame_clock = time.monotonic() - 100
        monitor.paused_until = time.monotonic() + 900
        watch = asyncio.create_task(monitor.watchdog())
        await asyncio.sleep(2.1)
        assert [e["kind"] for e in monitor.store.events()] == ["camera_offline"]
        assert monitor.status()["fresh"] is False
        capture = asyncio.create_task(monitor.capture_loop())
        await asyncio.sleep(0.15)
        assert monitor.fresh()
        assert [e["kind"] for e in monitor.store.events()] == ["camera_recovered", "camera_offline"]
        capture.cancel()
        watch.cancel()
        await asyncio.gather(capture, watch, return_exceptions=True)
        await monitor.stop()

    asyncio.run(run())
