# Reef Watch

A local camera monitor for a reef aquarium. Built for an **M4 Mac mini** and an
**Eufy Indoor Cam 2K** using its continuous RTSP stream.

**Status: v0.1 prototype.** It has a working capture service, dashboard, deterministic
visual checks, and local history. It has **not** been tested with the owner's camera
or on the owner's Mac. It does not yet recognize fish or send phone push notifications.

## What works in this version

- One FFmpeg RTSP connection, automatic reconnect, and a watchdog for missing frames.
- A dashboard at `http://127.0.0.1:8765` with a sampled camera view, refreshed every two seconds.
- Sustained unexpected darkness/light checks using your timezone, light schedule, and ramp periods.
- An experimental surface-motion check after a **manual, session-specific calibration**.
- A 15-minute maintenance pause. Camera outage checks continue during the pause.
- An event timeline, review acknowledgements, evidence images, and up to 15 seconds of
  preceding **2 fps, silent** footage when available. This is sampled evidence, not full-rate video.
- Daily comparison images in a 30-minute window after the chosen time; manual snapshots.
- SQLite history and media retention, default 14 days, on the Mac.
- A clearly labelled synthetic demo using its own data directory.
- A macOS login service installer that prevents idle system sleep while running.

The camera observes appearances. It does **not** measure ammonia, nitrate, phosphate,
salinity, temperature, dissolved oxygen, PAR, or actual pump flow. It cannot certify tank
health or diagnose disease. Hidden fish will never be declared dead by this version.

## Start on the Mac mini

1. Install [Homebrew](https://brew.sh) if needed.
2. Clone the repository and run the setup script:

   ```bash
   git clone https://github.com/jdalbright/Reef-Watch.git
   cd Reef-Watch
   bash scripts/setup-mac.sh
   .venv/bin/python -m reefwatch
   ```

3. Open **http://127.0.0.1:8765** on the Mac.
4. Open **Camera & monitoring setup** and paste your Eufy RTSP address there.
   Never put camera credentials in an issue, commit, screenshot, or chat.
5. Check the timezone and lighting schedule. Defaults: America/New_York,
   lights 07:30–18:30, 60-minute sunrise and sunset.
6. Position the camera, save the surface region, and follow [camera setup](docs/CAMERA_SETUP.md).

The setup script installs Python 3.12 and FFmpeg via Homebrew and the pinned Python
dependencies. The built dashboard is committed, so **Node is not needed to run it**.
Stopping the foreground command with Control-C stops monitoring.

### Try it without a camera

```bash
.venv/bin/python -m reefwatch --demo
```

Demo mode shows an explicitly labelled moving test pattern. It uses the `demo/` subfolder
of the application data directory; it never populates the real camera's history.
It follows the same schedule checks, so the test pattern may intentionally generate
an outside-schedule lighting event at night.

### Start automatically at login

Stop the foreground instance first, then:

```bash
.venv/bin/python scripts/install-service.py
```

The LaunchAgent starts at **user login**, not before login after a restart. `caffeinate -i`
prevents idle system sleep while it runs; the display can sleep. Manual sleep, shutdown,
power loss, network loss, and logout interrupt monitoring.

Remove the service without deleting data:

```bash
.venv/bin/python scripts/install-service.py --uninstall
```

To update: stop the service, `git pull --ff-only`, rerun the setup script, then reinstall
the service. Do not move the checkout or delete its virtual environment while the
LaunchAgent is installed.

## Data and privacy

On macOS, data is stored in `~/Library/Application Support/Reef Watch/`:

- `settings.json`: camera URL and settings; file permissions `0600`.
- `reef.sqlite3`: events, measurements, and comparison metadata.
- `media/`: local images and event clips.

Camera credentials are never returned by the API, included in validation responses,
or logged by the decoder. They are stored in a private file, **not encrypted in Keychain**
in v0.1. They are passed to the local FFmpeg process and may be visible to sufficiently
privileged local process inspection. Use a separate camera-stream credential if Eufy
offers one. RTSP itself may be unencrypted on the LAN.

No cloud AI, telemetry, analytics, subscription, account, or remote upload is built in.
The web server is deliberately bound to **127.0.0.1** with host/origin checks. The responsive
layout is ready for smaller screens, but phone access and phone push delivery are future
work. Do not expose the port publicly or remove the local-access checks.

## Calibration and limitations

- The camera feed is decoded to 640×360 at 2 fps for this prototype. Eufy's RTSP output
  is documented as 1080p; the service reduces it to limit processing/storage.
- Surface movement means pixel change in a selected region. Fish, reflections, algae,
  camera exposure, noise, and water ripples can affect it. The threshold requires testing.
- Calibration records a reference, not proof of healthy conditions. Confirm normal pump
  operation yourself. It is discarded on restart or settings changes.
- Frames older than three seconds are hidden from the live view. A persisted event
  is created after the configured outage interval (30 seconds by default).
- Night observation depends on visibility. Do not add light just to enable this monitor.
- The daily image is captured only during the stable daytime phase, outside maintenance.
  If the camera is offline throughout the window, that day's automatic image is skipped.
- Alerts are **dashboard events only** in this release. If the Mac/app loses power, it
  cannot report its own failure; independent heartbeat alerts need a separate service.
- No dosing, heater, pump, feeding, or other equipment control is implemented.

## Development

Python 3.11+ and FFmpeg are required. Node 22.12+ is needed only to change the dashboard.

```bash
uv sync --extra dev --frozen
uv run pytest -q
uv run ruff check reefwatch tests scripts
uv run ruff format --check reefwatch tests scripts
cd frontend
npm ci
npm run build
```

`uv.lock` locks Python dependencies; `requirements.txt` is the corresponding runtime-only
export used by the Mac setup script. Regenerate it after dependency changes:

```bash
uv export --format requirements-txt --no-hashes --no-dev --no-emit-project --output-file requirements.txt
```

The backend serves the built frontend from `reefwatch/static/`. Rebuild and commit those
assets after changing `frontend/src/`. Production uses one process/worker; a file lock
prevents two monitors sharing the same data directory.

See [project plan](docs/PLAN.md), [architecture](docs/ARCHITECTURE.md),
[camera setup](docs/CAMERA_SETUP.md), and [validation record](docs/VALIDATION.md).
