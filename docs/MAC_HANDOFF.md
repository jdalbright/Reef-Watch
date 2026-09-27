# M1 Pro testing → M4 mini always-on host

The owner confirmed on 2026-09-27 that the current M1 Pro / 16 GiB Mac is for testing;
the M4 Mac mini is the intended main host. Nothing has been installed on the M4 by this
session. The M1 Pro dashboard runs in the foreground; its tested LaunchAgent was removed.
Stopping the foreground process stops testing. Do not infer M4 performance from M1 results.

## On the M4 mini

1. Inspect for an existing checkout and preserve any uncommitted changes. If absent:

   ```bash
   git clone https://github.com/jdalbright/Reef-Watch.git
   cd Reef-Watch
   ```

   For an existing clean checkout, fetch and update with `git pull --ff-only`.
2. Run `bash scripts/setup-mac.sh`. Homebrew is required; the script reuses installed
   Python 3.12/FFmpeg and avoids unrelated Homebrew app upgrades.
3. Stop the test Mac's camera capture before starting the M4 camera connection. This
   avoids competing RTSP clients; actual Eufy client limits have not been qualified.
4. Run `.venv/bin/python -m reefwatch` and open `http://127.0.0.1:8765` **on the M4**.
   Enter camera credentials and the fixture IPv4 address directly into that local dashboard.
   Each Mac has independent private settings and history; neither is in GitHub.
5. Verify fresh camera frames, a manual snapshot, pause/resume, and read-only fixture
   status against ReefBeat. Keep camera/light comparisons disabled until readings are
   qualified. Recalibrate the surface reference after starting on the new host.
6. Once foreground behavior works, stop it and run:

   ```bash
   .venv/bin/python scripts/install-service.py
   ```

7. Verify the loopback dashboard, login-service restart, and eventually an actual login
   after reboot. The service starts **after user login**, not before it. Verify on the M4
   that idle sleep is prevented. Do not rely on its ability to report its own power failure.
8. Perform the actual-camera reconnect check and 48-hour tank trial from
   [camera setup](CAMERA_SETUP.md). Measure decoder CPU/RAM/storage on the M4 itself.

No remote access, public port, credential synchronization, or unattended equipment control
is configured. This is a deployment checklist, not evidence that M4 deployment occurred.
Private evidence/history can remain on the test Mac; moving it is a separate local data
migration, with both applications stopped, if the owner decides it is useful.
