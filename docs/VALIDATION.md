# Validation record — v0.1.0

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
- Mac M4 CPU/memory use over time and macOS LaunchAgent installation/login behavior.
- Overnight recovery, normal maintenance, real feeding, and camera/network interruptions.
- Phone access and notification delivery are not implemented and were not claimed as tested.

GitHub Actions is configured for Linux/macOS backend tests and a reproducible frontend build.
Adding this workflow is not itself proof that its remote runs passed; check the repository's
Actions tab for their results.
