# Eufy and tank setup

1. In the Eufy app, open the Indoor Cam 2K → Settings → Storage (sometimes under
   General) → NAS / RTSP. Enable it and choose **Continuous Recording**.
2. Keep the Mac and camera on the same home network. Reserve the camera's IP address
   in the router so the saved stream address stays stable.
3. Paste the generated RTSP URL into Reef Watch's password-style camera field on the Mac.
   Use the URL Eufy provides; don't guess its path. The NAS label does not require buying
   a NAS: FFmpeg is the local RTSP client here.
4. Keep the camera outside the glass, dry and away from splashes. Use a fixed position
   where the water surface and display are visible. If it is the Pan & Tilt version,
   disable automatic tracking so the view stays fixed.
5. Start with the tank lights on at a stable point in their schedule. Inspect reflections,
   focus, blue-light visibility, and any infrared reflection. Disable the camera's IR
   illumination if it causes glare. Do not extend the tank's photoperiod for monitoring.
6. Save a surface region using percentage coordinates. The dashboard outlines the region
   after saving. Prefer water motion without a fish's habitual resting area, room reflection,
   or a large static piece of rock dominating the selected region.
7. Confirm pump operation yourself and choose **Record surface reference**. It needs two
   uninterrupted minutes of stable daytime video. A near-static view is rejected.
8. Observe image brightness with the light on/off and tune thresholds if necessary. The
   default values are unvalidated starting values, not a calibration for a Red Sea light.

## First acceptance run

- Use **Capture now**, open the image, and verify it is fresh and from the intended camera.
- Use the maintenance pause and resume controls; verify the countdown changes.
- Unplug only the camera, leaving aquarium equipment running. Within the configured outage
  interval plus a small scheduling delay, an outage event should appear. Reconnect it and
  verify fresh video and a recovery event.
- Let the normal sunrise/sunset and nighttime periods occur. Check whether room lights
  or camera night vision create misleading brightness observations.
- Review every event during the first 48 hours. Reposition/tune before relying on notices.
- Verify login restart on the Mac; the development environment cannot establish macOS
  LaunchAgent behavior or this camera's actual firmware compatibility.

## Troubleshooting

**No picture:** check power, same-LAN access, continuous RTSP mode, stream address, and
FFmpeg installation. The service deliberately suppresses decoder text that could contain
credentials. Eufy's regular app live-view limit is distinct from the RTSP path.

**Motion reference fails:** wait for stable daytime lighting, clean the glass, keep the
camera fixed, and adjust the surface region. A still or very dark image cannot supply a
meaningful motion reference.

**Unexpected dark/light events:** camera exposure, infrared mode, room lights, blue-heavy
lighting, or an obstructed lens can cause these. Inspect the event evidence and tune the
schedule/thresholds. No event proves a light fixture failed.

**No daily picture:** verify that the target time and its next thirty minutes fall within
the stable daytime period. The Mac and camera must be running then, with maintenance paused
off. Manual snapshots remain available whenever a fresh frame exists.

**Port already in use:** stop the foreground process or uninstall the login service before
starting another instance. A separate demo may run on `--port 8766` with its own data folder.
