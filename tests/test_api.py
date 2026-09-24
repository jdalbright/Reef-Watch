from fastapi.testclient import TestClient

from reefwatch.app import create_app

HEADERS = {"X-Reef-Watch": "1"}


def client(tmp_path, demo=False):
    return TestClient(create_app(tmp_path, demo=demo), base_url="http://127.0.0.1:8765")


def test_initial_state_and_mutations(tmp_path):
    with client(tmp_path) as c:
        assert c.get("/api/status").json()["camera"] == "not_configured"
        assert c.get("/api/frame").status_code == 503
        assert c.post("/api/pause", headers=HEADERS).status_code == 200
        assert c.get("/api/status").json()["paused_seconds"] > 890
        assert c.post("/api/resume", headers=HEADERS).status_code == 200
        assert c.post("/api/calibrate", headers=HEADERS).status_code == 409
        assert c.post("/api/snapshots", headers=HEADERS).status_code == 409
        assert c.post("/api/events/not-found/acknowledge", headers=HEADERS).status_code == 404


def test_cross_origin_and_dns_rebinding_blocked(tmp_path):
    with client(tmp_path) as c:
        assert c.get("/api/status", headers={"host": "attacker.example"}).status_code == 400
        assert c.post("/api/pause").status_code == 403
        assert (
            c.post("/api/pause", headers={**HEADERS, "Origin": "http://evil.example"}).status_code
            == 403
        )
        assert (
            c.post("/api/pause", headers={**HEADERS, "Origin": "http://127.0.0.1:8765"}).status_code
            == 200
        )


def test_settings_validation_never_echoes_secret(tmp_path):
    with client(tmp_path) as c:
        for payload in [
            {"camera_url": "rtsp://user:supersecret@host:bad/"},
            {"camera_url": ["supersecret"]},
            ["supersecret"],
        ]:
            response = c.put("/api/settings", json=payload, headers=HEADERS)
            assert response.status_code == 422
            assert "supersecret" not in response.text


def test_credentials_preserved_and_explicitly_cleared(tmp_path):
    with client(tmp_path) as c:
        response = c.put(
            "/api/settings",
            json={"camera_url": "rtsp://user:secret@127.0.0.1:1/live0"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        assert "secret" not in response.text
        assert (
            c.put(
                "/api/settings", json={"camera_url": "", "lights_on": "06:30"}, headers=HEADERS
            ).status_code
            == 200
        )
        assert c.get("/api/status").json()["settings"]["camera_configured"]
        assert c.put("/api/settings", json={"disconnect": True}, headers=HEADERS).status_code == 200
        assert c.get("/api/status").json()["camera"] == "not_configured"


def test_invalid_media_paths_and_security_headers(tmp_path):
    with client(tmp_path) as c:
        assert c.get("/media/settings.json").status_code == 404
        assert c.get("/media/" + "0" * 32 + ".jpg").status_code == 404
        response = c.get("/api/status")
        assert response.headers["cache-control"] == "no-store"
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_demo_uses_separate_storage(tmp_path):
    with client(tmp_path, demo=True) as c:
        assert c.get("/api/status").json()["demo"] is True
    assert (tmp_path / "demo/reef.sqlite3").exists()
    assert not (tmp_path / "reef.sqlite3").exists()
