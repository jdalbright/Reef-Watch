"""Experimental, GET-only RSLED50 status. No equipment control or cloud access.

Protocol references and licensing are documented in docs/REEFLED_SETUP.md.
"""

import asyncio
import json
import math
import re
import time

import httpx

from .config import local_address
from .detection import Observation

ENDPOINTS = ("/device-info", "/firmware", "/mode", "/manual")
STALE_SECONDS = 75
REQUEST_DEADLINE = 5


def number(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value):
        return None
    return value if low <= value <= high else None


def version(value):
    # Never expose arbitrary response text or identifiers in the public API.
    return (
        value if isinstance(value, str) and re.fullmatch(r"[vV]?\d+(?:\.\d+){1,3}", value) else None
    )


class ReefLEDClient:
    def __init__(self, address, transport=None):
        self.address = local_address(address)
        self.transport = transport

    async def read(self):
        async with httpx.AsyncClient(
            timeout=3, follow_redirects=False, trust_env=False, transport=self.transport
        ) as client:

            async def get(path):
                if path not in ENDPOINTS:
                    raise ValueError("Unsupported endpoint")
                try:
                    async with asyncio.timeout(REQUEST_DEADLINE):
                        async with client.stream("GET", f"http://{self.address}{path}") as response:
                            if response.status_code != 200:
                                return None
                            body = bytearray()
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                body.extend(chunk)
                                if len(body) > 65536:
                                    return None
                            result = json.loads(body)
                            return result if isinstance(result, dict) else None
                except (httpx.HTTPError, TimeoutError, ValueError, RecursionError):
                    return None

            info = await get("/device-info")
            if info is None:
                return {"state": "unavailable"}
            if info.get("hw_model") != "RSLED50":
                return {"state": "unsupported"}
            firmware, mode, manual = await asyncio.gather(
                get("/firmware"), get("/mode"), get("/manual")
            )
            manual_at = time.time()
            values = manual or {}
            channels = {key: number(values.get(key), 0, 100) for key in ("blue", "white", "moon")}
            operating_mode = (mode or {}).get("mode")
            result = {
                "state": "connected",
                "model": "RSLED50",
                "firmware": version((firmware or {}).get("version")),
                "mode": operating_mode if operating_mode in ("auto", "manual", "timer") else None,
                **channels,
                "fixture_temperature_c": number(values.get("temperature"), -40, 150),
                "fan_percent": number(values.get("fan"), 0, 100),
                "at": manual_at,
            }
            result["state"] = (
                "connected"
                if all(
                    result[k] is not None
                    for k in (
                        "firmware",
                        "mode",
                        "blue",
                        "white",
                        "moon",
                        "fixture_temperature_c",
                        "fan_percent",
                    )
                )
                else "partial"
            )
            return result


class LightMonitor:
    def __init__(self, address, store, client_factory=ReefLEDClient):
        self.address, self.store, self.client_factory = address, store, client_factory
        self.reading = None
        self.last_clock = None
        self.state = "connecting" if address else "not_configured"
        self.task = None
        self.since = None
        self.reported = False

    def start(self):
        if self.address:
            self.task = asyncio.create_task(self.run())

    async def stop(self):
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def poll(self):
        try:
            result = await self.client_factory(self.address).read()
        except Exception:
            # Never persist exception strings, URLs, or raw device payloads.
            result = {"state": "unavailable"}
        self.state = result["state"]
        if self.state in ("connected", "partial"):
            self.reading, self.last_clock = result, time.monotonic()
        self.store.light_reading(time.time(), result)
        return self.state in ("connected", "partial")

    async def run(self):
        delay = 30
        while True:
            good = await self.poll()
            delay = 30 if good else min(delay * 2, 120)
            await asyncio.sleep(delay)

    def status(self, clock=None):
        clock = time.monotonic() if clock is None else clock
        age = None if self.last_clock is None else max(0, clock - self.last_clock)
        fresh = age is not None and age < STALE_SECONDS and self.state in ("connected", "partial")
        return {
            "state": "stale" if age is not None and age >= STALE_SECONDS else self.state,
            "fresh": fresh,
            "age_seconds": None if age is None else round(age),
            "reading": self.reading,
        }

    def reset_comparison(self):
        self.since, self.reported = None, False

    def compare(self, metrics, camera_at, clock, paused, settings):
        status = self.status(clock)
        reading = self.reading or {}
        channels = [reading.get(key) for key in ("blue", "white", "moon")]
        # Only qualified, steady automatic daylight is compared. Existing schedule
        # checks remain independent; absent fields never imply zero output.
        usable = (
            settings.reefled_comparison_enabled
            and status["fresh"]
            and not paused
            and metrics.get("phase") == "day"
            and reading.get("mode") == "auto"
            and all(value is not None for value in channels)
            and metrics.get("brightness") is not None
        )
        mismatch = (
            usable and max(channels) >= 10 and metrics["brightness"] < settings.dark_brightness
        )
        if not mismatch:
            self.reset_comparison()
            return None
        if self.since is None:
            self.since = clock
        if clock - self.since >= settings.persistence_seconds and not self.reported:
            self.reported = True
            return Observation(
                "light_camera_disagreement",
                "Light reports active channels, but the camera view is unusually dark",
                f"Reported blue/white/moon: {channels[0]}/{channels[1]}/{channels[2]}%. "
                f"Device read: {reading['at']:.3f}; camera frame: {camera_at:.3f} (Unix seconds). "
                "Inspect the camera view and fixture. This does not measure emitted light or PAR.",
            )
        return None
