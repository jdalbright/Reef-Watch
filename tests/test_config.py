import json
import stat

import pytest
from pydantic import ValidationError

from reefwatch.config import Settings, load_settings, save_json


@pytest.mark.parametrize(
    "value",
    [
        "http://camera/",
        "file:///etc/passwd",
        "rtsp://",
        "rtsp://host:bad/",
        "rtsp://host/with space",
    ],
)
def test_invalid_camera_urls(value):
    with pytest.raises(ValidationError):
        Settings(camera_url=value)


@pytest.mark.parametrize(
    "changes",
    [
        dict(lights_on="7:30"),
        dict(timezone="Invalid/Zone"),
        dict(surface_roi=(0.9, 0, 0.2, 0.2)),
        dict(surface_roi=(0, 0, 0, 0.2)),
        dict(lights_on="07:30", lights_off="08:00"),
        dict(dark_brightness=30, lit_brightness=20),
        dict(motion_ratio=float("nan")),
    ],
)
def test_settings_constraints(changes):
    with pytest.raises(ValidationError):
        Settings(**changes)


def test_credentials_private_on_disk_and_omitted_from_public_status(tmp_path):
    settings = Settings(camera_url="rtsp://user:secret@192.0.2.1/live0")
    save_json(tmp_path / "settings.json", settings.model_dump())
    assert stat.S_IMODE((tmp_path / "settings.json").stat().st_mode) == 0o600
    assert load_settings(tmp_path) == settings
    assert "secret" not in repr(settings)
    assert "secret" not in json.dumps(settings.public())
