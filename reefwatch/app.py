import fcntl
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings, default_data_dir, load_settings
from .monitor import Monitor
from .storage import MEDIA_NAME


def create_app(directory=None, demo=False, ffmpeg="ffmpeg"):
    directory = Path(directory or default_data_dir())
    if demo:
        directory = directory / "demo"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)

    @asynccontextmanager
    async def lifespan(app):
        with (directory / "monitor.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError(
                    "Another Reef Watch process already uses this data directory."
                ) from None
            try:
                settings = load_settings(directory)
            except (ValidationError, ValueError):
                raise RuntimeError(
                    "Settings file is invalid. Correct or remove settings.json locally."
                ) from None
            app.state.monitor = Monitor(settings, directory, demo, ffmpeg)
            await app.state.monitor.start()
            try:
                yield
            finally:
                await app.state.monitor.stop()

    app = FastAPI(
        title="Reef Watch", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]"])

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        if request.method not in {"GET", "HEAD"}:
            origin = request.headers.get("origin")
            if request.headers.get("x-reef-watch") != "1" or (
                origin and urlsplit(origin).netloc != request.headers.get("host")
            ):
                return JSONResponse(
                    {"detail": "Use the local Reef Watch dashboard."}, status_code=403
                )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' blob:; media-src 'self'; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        # Framework validation normally echoes submitted values, including camera credentials.
        return JSONResponse(
            {"detail": "Invalid request. Check the submitted fields."}, status_code=422
        )

    @app.get("/api/status")
    async def status():
        return app.state.monitor.status()

    @app.get("/api/frame")
    async def frame():
        monitor = app.state.monitor
        if not monitor.fresh() or monitor.frame is None:
            raise HTTPException(503, "No fresh frame")
        return Response(monitor.frame, media_type="image/jpeg")

    @app.put("/api/settings")
    async def settings(request: Request):
        monitor = app.state.monitor
        try:
            if int(request.headers.get("content-length", "0")) > 8192:
                raise ValueError()
            raw = await request.body()
            if len(raw) > 8192:
                raise ValueError()
            import json

            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError()
            # A blank password field keeps the existing URL; disconnect uses an explicit flag.
            disconnect = payload.pop("disconnect", False)
            if disconnect is not True and not payload.get("camera_url"):
                payload.pop("camera_url", None)
            if disconnect is True:
                payload["camera_url"] = ""
            updated = Settings.model_validate({**monitor.settings.model_dump(), **payload})
        except (ValueError, TypeError):
            raise HTTPException(
                422, "Invalid settings. Check the schedule, timezone, RTSP URL, and surface region."
            ) from None
        await monitor.configure(updated)
        return updated.public()

    @app.post("/api/pause")
    async def pause():
        monitor = app.state.monitor
        monitor.paused_until = time.monotonic() + 15 * 60
        monitor.detector.reset_temporal()
        return {"paused": True}

    @app.post("/api/resume")
    async def resume():
        monitor = app.state.monitor
        monitor.paused_until = 0
        monitor.detector.reset_temporal()
        return {"paused": False}

    @app.post("/api/calibrate")
    async def calibrate():
        monitor = app.state.monitor
        if not monitor.fresh() or monitor.detector.metrics["phase"] != "day":
            raise HTTPException(
                409, "Calibration requires fresh daytime video outside lighting ramps."
            )
        if monitor.paused_until > time.monotonic():
            raise HTTPException(409, "Resume checks before calibrating.")
        monitor.detector.start_calibration(time.monotonic())
        return {"started": True}

    @app.post("/api/snapshots")
    async def snapshot():
        try:
            return {"file": app.state.monitor.snapshot()}
        except ValueError:
            raise HTTPException(
                409, "Connect the camera before taking a comparison photo."
            ) from None

    @app.post("/api/events/{item_id}/acknowledge")
    async def acknowledge(item_id: str):
        if not app.state.monitor.store.acknowledge(item_id):
            raise HTTPException(404, "Event not found")
        return {"acknowledged": True}

    @app.get("/media/{filename}")
    async def media(filename: str):
        if not MEDIA_NAME.fullmatch(filename):
            raise HTTPException(404)
        path = app.state.monitor.store.media / filename
        if not path.is_file() or path.is_symlink():
            raise HTTPException(404)
        return FileResponse(path)

    static = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=static, html=True), name="dashboard")
    return app
