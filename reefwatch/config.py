import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def default_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Reef Watch"
    return Path.home() / ".local/share/reef-watch"


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    camera_url: str = Field(default="", repr=False, max_length=2048)
    timezone: str = "America/New_York"
    lights_on: str = "07:30"
    lights_off: str = "18:30"
    ramp_minutes: int = Field(default=60, ge=0, le=180)
    snapshot_at: str = "12:00"
    # Normalized [left, top, width, height]. Adjust to the actual visible water surface.
    surface_roi: tuple[float, float, float, float] = (0.05, 0.05, 0.90, 0.20)
    persistence_seconds: int = Field(default=90, ge=10, le=900)
    offline_seconds: int = Field(default=30, ge=10, le=300)
    calibration_seconds: int = Field(default=120, ge=30, le=600)
    motion_ratio: float = Field(default=0.25, ge=0.05, le=0.75)
    dark_brightness: float = Field(default=8, ge=0, le=100)
    lit_brightness: float = Field(default=25, ge=1, le=255)
    retention_days: int = Field(default=14, ge=1, le=90)

    @field_validator("camera_url")
    @classmethod
    def valid_url(cls, value):
        if not value:
            return ""
        try:
            url = urlsplit(value)
            valid = url.scheme in {"rtsp", "rtsps"} and url.hostname and url.port != 0
        except ValueError:
            valid = False
        if not valid or any(c.isspace() for c in value):
            raise ValueError("Use the RTSP address from your Eufy app; encode spaces in passwords.")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Use an IANA timezone such as America/New_York.") from None
        return value

    @field_validator("lights_on", "lights_off", "snapshot_at")
    @classmethod
    def valid_time(cls, value):
        try:
            hour, minute = map(int, value.split(":"))
            assert len(value) == 5 and 0 <= hour < 24 and 0 <= minute < 60
        except (ValueError, AssertionError):
            raise ValueError("Use HH:MM in 24-hour time.") from None
        return value

    @field_validator("surface_roi")
    @classmethod
    def valid_roi(cls, value):
        x, y, w, h = value
        if not (
            0 <= x < 1
            and 0 <= y < 1
            and 0.02 <= w <= 1
            and 0.02 <= h <= 1
            and x + w <= 1.000001
            and y + h <= 1.000001
        ):
            raise ValueError("Surface region must fit within the image, with positive dimensions.")
        return value

    @model_validator(mode="after")
    def valid_thresholds(self):
        if self.dark_brightness >= self.lit_brightness:
            raise ValueError("Dark threshold must be below the lit threshold.")
        on = minutes(self.lights_on)
        off = minutes(self.lights_off)
        if on == off or (off - on) % 1440 <= 2 * self.ramp_minutes:
            raise ValueError("Lighting schedule must leave a stable period between ramps.")
        return self

    def public(self):
        return {
            **self.model_dump(exclude={"camera_url"}),
            "camera_configured": bool(self.camera_url),
        }


def minutes(value):
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def save_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_suffix(".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
    temp.replace(path)


def load_settings(directory: Path):
    path = directory / "settings.json"
    return Settings.model_validate_json(path.read_text()) if path.exists() else Settings()
