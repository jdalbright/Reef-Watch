"""Synthetic HTTP fixtures only. These tests do not establish firmware compatibility."""

import asyncio
import json
import time

import httpx
import pytest

from reefwatch.config import Settings
from reefwatch.reefled import LightMonitor, ReefLEDClient
from reefwatch.storage import Store

ADDRESS = "192.168.200.250"  # Synthetic RFC1918 fixture, never contacted.


def fixture(path):
    return {
        "/device-info": {"hw_model": "RSLED50", "hwid": "private-device-id"},
        "/firmware": {"version": "1.2.3"},
        "/mode": {"mode": "auto"},
        "/manual": {"blue": 60, "white": 20, "moon": 0, "temperature": 41.5, "fan": 35},
    }[path]


def read(handler):
    return asyncio.run(ReefLEDClient(ADDRESS, httpx.MockTransport(handler)).read())


def test_only_four_gets_and_allowlisted_fields():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json=fixture(request.url.path))

    result = read(handler)
    assert seen == [("GET", p) for p in ("/device-info", "/firmware", "/mode", "/manual")]
    assert result["state"] == "connected"
    assert result["moon"] == 0
    assert result["fixture_temperature_c"] == 41.5
    assert "private-device-id" not in json.dumps(result)
    assert ADDRESS not in json.dumps(result)


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "8.8.8.8",
        "169.254.1.1",
        "224.0.0.1",
        "light.local",
        "http://host",
        "192.168.1.2:80",
        "user:pass@host",
    ],
)
def test_non_lan_and_url_addresses_rejected(address):
    with pytest.raises(ValueError):
        Settings(reefled_address=address)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(302, headers={"Location": "https://example.com/private"}),
        httpx.Response(500),
        httpx.Response(200, text="not-json"),
        httpx.Response(200, json=[]),
        httpx.Response(200, text="x" * 65537),
    ],
)
def test_bad_response_does_not_follow_redirect_or_echo_body(response):
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return response

    assert read(handler) == {"state": "unavailable"}
    assert seen == ["/device-info"]


def test_timeout_and_unsupported_model():
    def timeout(request):
        raise httpx.ReadTimeout("private-address-and-secret")

    assert read(timeout) == {"state": "unavailable"}
    assert read(lambda r: httpx.Response(200, json={"hw_model": "OTHER"})) == {
        "state": "unsupported"
    }


def test_partial_and_invalid_fields_are_never_zero():
    def handler(request):
        data = fixture(request.url.path)
        if request.url.path == "/manual":
            data = {"blue": True, "white": 101, "moon": 0, "fan": "35"}
        if request.url.path == "/firmware":
            return httpx.Response(404)
        if request.url.path == "/mode":
            data = {"mode": "private-identifier"}
        return httpx.Response(200, json=data)

    result = read(handler)
    assert result["state"] == "partial"
    assert result["blue"] is result["white"] is result["fan_percent"] is result["mode"] is None
    assert result["moon"] == 0


def test_stale_failure_recovery_history_and_retention(tmp_path):
    store = Store(tmp_path)
    results = iter(
        [
            {"state": "partial", "blue": 0, "at": time.time()},
            {"state": "unavailable"},
            {"state": "partial", "blue": 20, "at": time.time()},
        ]
    )

    class Client:
        async def read(self):
            return next(results)

    monitor = LightMonitor(ADDRESS, store, lambda address: Client())
    asyncio.run(monitor.poll())
    assert monitor.status()["fresh"]
    assert monitor.status(monitor.last_clock + 76)["state"] == "stale"
    asyncio.run(monitor.poll())
    assert not monitor.status()["fresh"]
    assert monitor.status()["reading"]["blue"] == 0
    asyncio.run(monitor.poll())
    assert monitor.status()["fresh"]
    assert monitor.status()["reading"]["blue"] == 20
    assert len(store.light_history()) == 3
    store.prune(1, now=time.time() + 86401)
    assert store.light_history() == []
    store.close()


def test_comparison_persistence_pause_stale_mode_and_rearming(tmp_path):
    store = Store(tmp_path)
    monitor = LightMonitor(ADDRESS, store)
    settings = Settings(reefled_comparison_enabled=True, persistence_seconds=10)
    monitor.state = "connected"
    monitor.last_clock = 100
    monitor.reading = {"at": 1000, "blue": 50, "white": 0, "moon": 0, "mode": "auto"}
    dark = {"phase": "day", "brightness": 1}
    assert monitor.compare(dark, 1001, 100, False, settings) is None
    event = monitor.compare(dark, 1011, 110, False, settings)
    assert event.kind == "light_camera_disagreement"
    assert "1000.000" in event.detail and "1011.000" in event.detail
    assert monitor.compare(dark, 1012, 111, False, settings) is None
    assert monitor.compare(dark, 1013, 112, True, settings) is None
    assert monitor.since is None
    assert monitor.compare(dark, 1014, 113, False, settings) is None
    assert monitor.compare(dark, 1080, 180, False, settings) is None
    assert monitor.since is None
    monitor.last_clock = 180
    monitor.reading["mode"] = "manual"
    assert monitor.compare(dark, 1081, 181, False, settings) is None
    monitor.reading["mode"] = "auto"
    assert monitor.compare(dark, 1082, 182, False, settings) is None
    assert monitor.compare(dark, 1092, 192, False, settings) is not None
    settings.reefled_comparison_enabled = False
    assert monitor.compare(dark, 1093, 193, False, settings) is None
    store.close()


def test_poll_cancellation_is_prompt_and_camera_independent(tmp_path):
    async def scenario():
        store = Store(tmp_path)

        class SlowClient:
            async def read(self):
                await asyncio.sleep(100)

        monitor = LightMonitor(ADDRESS, store, lambda address: SlowClient())
        monitor.start()
        await asyncio.sleep(0)
        await asyncio.wait_for(monitor.stop(), 0.5)
        store.close()

    asyncio.run(scenario())


def test_slow_request_has_total_deadline(monkeypatch):
    import reefwatch.reefled as module

    monkeypatch.setattr(module, "REQUEST_DEADLINE", 0.02)

    async def slow(request):
        await asyncio.sleep(100)
        return httpx.Response(200, json={})

    async def run():
        return await asyncio.wait_for(ReefLEDClient(ADDRESS, httpx.MockTransport(slow)).read(), 0.5)

    assert asyncio.run(run()) == {"state": "unavailable"}


def test_failed_reads_back_off_and_recovery_resets_delay(tmp_path, monkeypatch):
    import reefwatch.reefled as module

    results = iter([False, False, False, True])
    delays = []
    store = Store(tmp_path)
    monitor = LightMonitor(ADDRESS, store)

    async def poll():
        return next(results)

    async def sleep(delay):
        delays.append(delay)
        if len(delays) == 4:
            raise asyncio.CancelledError()

    monkeypatch.setattr(monitor, "poll", poll)
    monkeypatch.setattr(module.asyncio, "sleep", sleep)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(monitor.run())
    assert delays == [60, 120, 120, 30]
    store.close()
