"""Deterministic visual checks with sustained conditions and explicit calibration.

Brightness and frame differences are camera observations, not PAR, pump flow, or health.
"""

from dataclasses import dataclass
from datetime import datetime
from statistics import median
from zoneinfo import ZoneInfo

import numpy as np

from .config import Settings, minutes


@dataclass
class Observation:
    kind: str
    title: str
    detail: str


def light_phase(now: datetime, settings: Settings) -> str:
    local = now.astimezone(ZoneInfo(settings.timezone))
    minute = local.hour * 60 + local.minute
    on, off = minutes(settings.lights_on), minutes(settings.lights_off)
    since_on, duration = (minute - on) % 1440, (off - on) % 1440
    if since_on < duration:
        if since_on < settings.ramp_minutes or since_on >= duration - settings.ramp_minutes:
            return "ramp"
        return "day"
    return "night"


class Detector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.previous = None
        self.previous_brightness = None
        self.previous_time = None
        self.baseline = None
        self.calibration_start = None
        self.calibration_values = []
        self.calibration_message = "Needs calibration"
        self.pending = {}
        self.active = set()
        self.metrics = {"brightness": None, "motion": None, "phase": "unknown"}

    def reset_temporal(self):
        self.previous = self.previous_brightness = self.previous_time = None
        self.pending.clear()
        self.active.clear()
        if self.calibration_start is not None:
            self.calibration_start = None
            self.calibration_values.clear()
            self.calibration_message = "Calibration interrupted; try again"

    def start_calibration(self, clock):
        self.baseline = None
        self.calibration_start = clock
        self.calibration_values = []
        self.calibration_message = "Calibrating"
        self.pending.clear()
        self.active.clear()

    def condition(self, key, true, clock, title, detail):
        if not true:
            self.pending.pop(key, None)
            self.active.discard(key)
            return None
        self.pending.setdefault(key, clock)
        if (
            clock - self.pending[key] >= self.settings.persistence_seconds
            and key not in self.active
        ):
            self.active.add(key)
            return Observation(key, title, detail)
        return None

    def process(self, rgb: np.ndarray, now: datetime, clock: float, paused=False):
        gray = rgb.astype(np.float32).mean(axis=2)  # Equal channels preserve blue-lit visibility.
        brightness = float(gray.mean())
        phase = light_phase(now, self.settings)
        gap = self.previous_time is None or clock - self.previous_time > 2
        changed_exposure = (
            self.previous_brightness is not None and abs(brightness - self.previous_brightness) > 12
        )
        x, y, w, h = self.settings.surface_roi
        ih, iw = gray.shape
        region = gray[int(y * ih) : int((y + h) * ih), int(x * iw) : int((x + w) * iw)]
        motion = None
        if not gap and not changed_exposure and self.previous is not None:
            motion = float(np.mean(np.abs(region - self.previous)))
        self.previous = region.copy()
        self.previous_time, self.previous_brightness = clock, brightness
        self.metrics = {
            "brightness": round(brightness, 2),
            "motion": None if motion is None else round(motion, 3),
            "phase": phase,
        }
        events = []
        if paused:
            self.pending.clear()
            self.active.clear()
            return events
        stable = phase == "day" and brightness >= self.settings.lit_brightness
        if self.calibration_start is not None:
            if not stable or gap or changed_exposure:
                # Require an uninterrupted, well-lit calibration window.
                self.calibration_start = clock
                self.calibration_values.clear()
                self.calibration_message = "Waiting for stable daytime video"
            elif motion is not None:
                self.calibration_message = "Calibrating"
                self.calibration_values.append(motion)
                if clock - self.calibration_start >= self.settings.calibration_seconds:
                    value = median(self.calibration_values)
                    self.calibration_start = None
                    if value < 1.0:
                        self.calibration_message = "Too little motion; adjust the surface region"
                    else:
                        self.baseline = value
                        self.calibration_message = "Calibrated for this session"
                        events.append(
                            Observation(
                                "calibrated",
                                "Surface reference captured",
                                "Reference records visible motion only; it does not verify pump flow.",
                            )
                        )
        checks = [
            (
                "unexpected_dark",
                phase == "day" and brightness <= self.settings.dark_brightness,
                "Tank appears darker than scheduled",
                "Check the light, camera exposure, and view.",
            ),
            (
                "unexpected_light",
                phase == "night" and brightness >= self.settings.lit_brightness,
                "Tank appears lit outside its schedule",
                "Room lighting or camera night vision may explain this change.",
            ),
            (
                "low_movement",
                stable
                and motion is not None
                and self.baseline is not None
                and motion < self.baseline * self.settings.motion_ratio,
                "Less visible surface movement",
                "Check the pump and camera view. This is a visual change, not a measured flow rate.",
            ),
        ]
        for key, condition, title, detail in checks:
            event = self.condition(key, condition, clock, title, detail)
            if event:
                events.append(event)
        return events
