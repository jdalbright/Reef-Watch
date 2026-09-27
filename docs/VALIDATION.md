# Validation record — v0.1 prototype

## Owner's Mac setup — 2026-09-27

**Installed and software-qualified; aquarium hardware is not yet qualified.** The workspace
was an empty Git repository with no uncommitted files; current `origin/main` was fetched
before setup. Private camera/light settings did not exist and were still unconfigured at
completion of these checks. No actual camera or fixture connection is claimed.

Environment: **Apple M1 Pro, 16 GiB RAM**, macOS 27.0 (arm64), Python 3.12.14,
FFmpeg 9.0.2, reported by `sysctl`/`sw_vers`. This differs from the handoff's M4 Mac mini.
These results must not be attributed to an M4. Confirmation of the intended host is pending.

- **63 automated tests pass on this Mac**, including the original 39 tests, new GET-only
  ReefLED fixtures, privacy/validation, bad/oversized/redirected responses, total request
  deadline, backoff/recovery, stale/partial fields, comparison persistence/suppression,
  local history retention, and synthetic clip-study preparation.
- `uv run ruff check reefwatch tests scripts`, formatting check, and Mac setup shell
  syntax check pass. The known Starlette/httpx test-transport deprecation warning remains.
- `npm ci` and `npm run build` pass. Built dashboard assets, including the favicon, are
  committed; no Node runtime is required for monitoring.
- Foreground dashboard responds on **127.0.0.1:8765 only**. Host/origin protections and
  private-address redaction continue to pass automated tests.
- LaunchAgent installed, bootstrap verified, and `launchctl kickstart -k` successfully
  restarted it; the loopback listener returned under a new PID. `caffeinate` holds the
  intended idle-system-sleep assertion. Actual logout/login/reboot was **not** performed.
  After discovering the M1 Pro/M4 host mismatch, the newly created LaunchAgent was
  uninstalled and the dashboard returned to foreground operation pending host confirmation.
- Before removal, LaunchAgent file mode was 0600; application-data directory is 0700. Settings privacy is
  covered by tests; production settings had not yet been saved. Demo configuration was
  written only under disposable private temporary data, separate from real tank history.

### Local browser checks

Browser plugin not available; used installed Playwright with headless Chrome. Tested the
actual backend at 1440×1000 and 390×844, with screenshots inspected. Pause/resume changed
real API state. Separate demo checks exercised light-address save, blank-field clearing,
reload/preservation, and explicit disconnect. Synthetic HTTP response interception checked
partial readings, stale-value hiding, and lost-backend hiding of both live frame and light
values; these are UI fixtures, not fixture-hardware results.

| Check | Result |
| --- | --- |
| Page URL/title and meaningful content | Pass |
| Framework error overlay | None |
| Final baseline browser console/page errors | None |
| Desktop and narrow layout | Pass; no horizontal overflow |
| Pause/resume and private setup controls | Pass |
| Partial/stale/backend-loss states | Pass with explicitly synthetic fixtures |

The initial run exposed a missing favicon request and checkbox alignment issue; both were
fixed, rebuilt, and rechecked. Temporary screenshots and browser scripts are outside Git.

### Short resource sample, not RTSP qualification

Six samples over about 30 seconds, using `ps` process CPU and resident memory:

| Workload | CPU range | Resident memory |
| --- | --- | --- |
| Real service, camera/light unconfigured | 0.3–1.3% | 62.7–62.8 MiB |
| Separate in-process synthetic demo at 2 fps | 0.9–1.7% | 76.0–76.2 MiB |

The demo produced a valid JPEG snapshot. Neither row includes real RTSP decoding or light
polling. These short samples cannot establish sustained storage growth, decoder resource
use, 48-hour availability, or thermal behavior. The disposable demo was stopped afterward.

### Implementation and remaining gates

- Experimental ReefLED connector and local status/history are implemented. Protocol and
  MIT license research is pinned in [ReefLED setup](REEFLED_SETUP.md). No request has been
  made to the owner's fixture. Model/firmware, current-output semantics of `/manual`,
  temperature/fan units, ramp behavior, and read-only compatibility need actual validation.
  Camera comparison observations default **off** until that qualification.
- Microbubble **study tooling only** is implemented. Actual FFmpeg output from synthetic
  input was checked for source-detail/prototype dimensions and private permissions. No
  normal or natural-bubble tank footage was evaluated. No detector, sensitivity result,
  false-event rate, or low-water measurement is claimed; see [study](MICROBUBBLE_STUDY.md).
- Camera credentials and the fixture address must be entered in local private setup before
  real RTSP, disconnect/reconnect, and fixture reads can proceed. Never paste them into Git.
- The 48-hour trial, a real camera outage/recovery, sustained resource/storage sampling,
  and a genuine login/reboot on the intended host remain outstanding. No aquarium equipment settings were changed.

### Setup-script correction

The original `brew install python@3.12 ffmpeg` invoked Homebrew auto-update and dependent
upgrades beyond Reef Watch. That run was interrupted; setup now reuses installed tools
and disables auto-update, installed-dependent upgrades, and cleanup. The pinned Python
application install then completed successfully. This correction prevents repetition; it
does not roll back Homebrew changes already made by the initial run.

## Earlier development-environment record

The following sections describe the original Linux/synthetic prototype validation.
They do not substitute for the actual-device gates above.

## Verified in the development environment

- **39 automated tests pass** on Python 3.12/Linux.
- Python lint and formatting checks pass; Mac setup shell script passes syntax checking.
- The project installs from the locked environment and the `reef-watch` entry point runs.
- Frontend production build succeeds with the committed npm lockfile.
- Real FFmpeg encoding produces a decodable MP4 from synthetic input.
- An actual failed RTSP connection terminates without hanging.
- Tests cover lighting boundaries and overnight schedules, sustained-condition deduplication,
  maintenance pause, manual calibration, exposure jumps, stale-frame hiding, credential
  redaction, settings validation, local API access, retention, and outage/recovery behavior.
- Camera outage monitoring remains active during maintenance pause; the recovery event uses
  fresh synthetic frames. Tests never connect to the owner's camera.
- One upstream Starlette warning reports future deprecation of its `httpx` test transport.
  It does not affect these passing tests or the runtime service.

## Browser validation

The cloud browser could not access the local server (`ERR_BLOCKED_BY_CLIENT`). Local
Playwright was used instead, with Chromium from the `@sparticuz/chromium` npm distribution
after the usual Playwright browser download returned an invalid archive. QA dependencies
are separate from the application and are not needed by users.

Verified against running backend instances, not a static UI mock:

- Desktop rendering at **1505×1045**, the native concept dimensions.
- A **390×844** viewport, including expanded setup, with no horizontal overflow.
- Pause/resume controls and visible countdown changes.
- Invalid camera address validation and a saved light schedule surviving reload.
- Explicit demo labelling, fresh synthetic frames, manual snapshot, and a decodable image.
- Backend shutdown produces a lost-connection notice and hides the live image.
- No uncaught JavaScript errors in the exercised workflows.

## Visual review and fidelity ledger

The built-in image generator produced the initial disconnected dashboard concept; it was
used as the implementation reference without requiring a design-approval interruption.
The concept and rendered desktop/mobile screenshots were opened and visually compared.
Temporary QA images are not part of runtime assets or repository data.

| Review point | Result / intentional decision |
| --- | --- |
| Visible copy | Disconnected-state headings, labels, and empty-state copy match the concept. |
| Layout | Header, camera/status columns, history pair, and expandable setup retain the concept's order. |
| Palette | White background, dark teal text, teal action, gray dividers, dark disconnected camera area. |
| Typography | Explicit shared type sizes/weights; system-compatible Arial stack avoids an external font request. |
| Spacing | Empty-event paragraph's inherited margin was corrected to match the comparison panel. |
| Camera geometry | Disconnected layout follows the concept; a connected feed uses 16:9 to preserve image geometry. |
| Controls | Pause/resume, settings, calibration, snapshots, and event review connect to real API actions. |
| Mobile | The main and history columns stack; setup inputs reflow without overflow. |
| Additional states | Demo, stale-feed, errors, and saved-state notices intentionally appear only when relevant. |

No extra marketing sections, fabricated readings, fish sightings, chemical values, or health
scores were added. “Capture now” appears only when there is fresh video. The expanded
setup form is a functional extension of the concept's collapsed setup row.

## Still requires real hardware validation

- The actual Eufy camera stream, firmware, night mode, focus, glare, and blue-light quality.
- Calibration accuracy, false alerts, and usable surface-region placement on this tank.
- Microbubble detection is planned only. No detector or low-water inference has been
  implemented or tested. Qualification requires normal and naturally occurring bubble
  footage, visibility checks at the chosen resolution/frame rate, and measured false
  events and detection delay; see Phase 1c in the plan.
- Mac M4 CPU/memory with actual RTSP over time and actual login/reboot behavior.
  Installation, launchd restart, and short synthetic samples are now verified above.
- ReefLED 50 software is now implemented experimentally; no connection to the owner's
  light has been made. Local endpoint compatibility, field meanings,
  read-only behavior, stale-data handling, and camera comparisons require qualification
  under Phase 1d of the plan.
- Overnight recovery, normal maintenance, real feeding, and camera/network interruptions.
- Phone access and notification delivery are not implemented and were not claimed as tested.

GitHub Actions is configured for Linux/macOS backend tests and a reproducible frontend build.
Adding this workflow is not itself proof that its remote runs passed; check the repository's
Actions tab for their results.
