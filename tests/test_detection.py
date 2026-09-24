from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from reefwatch.config import Settings
from reefwatch.detection import Detector, light_phase


def at(value):
    return datetime.fromisoformat(f"2026-09-24T{value}:00").replace(
        tzinfo=ZoneInfo("America/New_York")
    )


def frame(value):
    return np.full((36, 64, 3), value, dtype=np.uint8)


@pytest.mark.parametrize(
    "hour,phase",
    [
        ("07:29", "night"),
        ("07:30", "ramp"),
        ("08:29", "ramp"),
        ("08:30", "day"),
        ("17:29", "day"),
        ("17:30", "ramp"),
        ("18:30", "night"),
    ],
)
def test_schedule(hour, phase):
    assert light_phase(at(hour), Settings()) == phase


def test_overnight_and_timezone():
    settings = Settings(lights_on="20:00", lights_off="08:00")
    assert light_phase(at("23:00"), settings) == "day"
    assert light_phase(at("07:30"), settings) == "ramp"
    assert light_phase(at("12:00"), settings) == "night"
    assert light_phase(at("12:00").astimezone(ZoneInfo("UTC")), Settings()) == "day"


def test_sustained_darkness_only_emits_once_then_rearms():
    detector = Detector(Settings(persistence_seconds=10))
    events = []
    for n in range(30):
        events.extend(detector.process(frame(0), at("12:00"), n))
    assert [e.kind for e in events] == ["unexpected_dark"]
    detector.process(frame(90), at("12:00"), 30)
    assert not detector.process(frame(0), at("12:00"), 31)
    assert detector.process(frame(0), at("12:00"), 41)[0].kind == "unexpected_dark"


def test_no_alerts_during_ramps_pause_or_normal_darkness():
    for when, paused in [(at("08:00"), False), (at("23:00"), False), (at("12:00"), True)]:
        detector = Detector(Settings(persistence_seconds=10))
        assert not sum([detector.process(frame(0), when, n, paused) for n in range(20)], [])


def test_low_motion_needs_manual_calibration():
    detector = Detector(Settings(persistence_seconds=10))
    for n in range(20):
        assert not detector.process(frame(60), at("12:00"), n)
    detector.baseline = 8
    for n in range(20, 30):
        assert not detector.process(frame(60), at("12:00"), n)
    assert detector.process(frame(60), at("12:00"), 30)[0].kind == "low_movement"


def test_calibration_rejects_static_view_and_accepts_visible_motion():
    detector = Detector(Settings(calibration_seconds=30))
    detector.start_calibration(0)
    for n in range(32):
        detector.process(frame(60), at("12:00"), n)
    assert detector.baseline is None
    assert "Too little motion" in detector.calibration_message
    detector.start_calibration(32)
    for n in range(32, 64):
        detector.process(frame(60 + 4 * (n % 2)), at("12:00"), n)
    assert detector.baseline == 4


def test_disconnect_cancels_calibration_and_resets_pending_conditions():
    detector = Detector(Settings(persistence_seconds=10))
    detector.process(frame(0), at("12:00"), 0)
    detector.start_calibration(2)
    detector.reset_temporal()
    assert detector.calibration_start is None
    assert not detector.pending
    assert not detector.process(frame(0), at("12:00"), 20)


def test_exposure_jump_is_not_motion_evidence():
    detector = Detector(Settings())
    detector.process(frame(40), at("12:00"), 1)
    detector.process(frame(90), at("12:00"), 2)
    assert detector.metrics["motion"] is None
