# Project instructions

Reef Watch is a local observation prototype for a reef camera on an M4 Mac mini.

- Read README.md and docs/PLAN.md before changing scope.
- Preserve the distinction between visual changes, physical measurements, and health.
- Do not present hidden fish as dead, use an unsupported health score, or infer chemical
  readings from ordinary video. Do not add autonomous aquarium equipment control.
- Never commit camera URLs, credentials, local settings, user footage, runtime databases,
  analytics keys, or private network addresses. Use synthetic frames in tests.
- Keep loopback-only serving, host/origin checks, redacted API responses, and private
  settings-file permissions unless a separately reviewed authenticated remote-access design
  replaces them. Never interpolate camera input into a shell command.
- Tests should cover behavior and failure cases: stale frames, reconnect, scheduling,
  calibration, persistence, credentials, and evidence encoding.
- Run `uv run pytest -q`, `uv run ruff check reefwatch tests scripts`, and
  `uv run ruff format --check reefwatch tests scripts` after relevant backend changes.
- Rebuild frontend assets with `cd frontend && npm ci && npm run build` and verify actual
  controls and small-screen layout. Commit the generated reefwatch/static assets.
- Update requirements.txt from uv.lock when dependencies change. Runtime must not require Node.
- Record the boundary between synthetic/Linux validation and real-camera/macOS validation.
- Update docs/PLAN.md and docs/VALIDATION.md when functionality or validation status changes.
