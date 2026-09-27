# Reef Watch implementation plan

## Goal

Help the owner notice meaningful visual changes in a 20-gallon reef using an existing
Eufy Indoor Cam 2K and an always-on M4 Mac mini. Add read-only status from the owner's
Red Sea ReefLED 50 to help interpret camera observations. Make every observation
inspectable with its time, source, and available evidence. Avoid broad claims about tank health.

## Phase 1 — local prototype (implemented in v0.1)

Capture a continuous RTSP stream, reconnect after failures, display fresh frames,
record deterministic observations, collect daily comparisons, and provide local setup
and maintenance controls. Keep secrets and recordings outside Git. Provide a Mac login
service, repeatable dependency installation, automated tests, and a separate demo mode.

**Exit criteria:** automated detector/API/capture tests pass; dashboard flows work at
desktop/mobile widths; failed or stale capture is visibly unavailable; no credential
appears in API output. Real hardware qualification below remains outstanding.

## Phase 1b — qualify on the actual tank (next)

1. Enable NAS/RTSP continuous mode and verify the stream on the same LAN.
2. Fix the camera position; show the water surface and as much of the display as possible.
3. Set timezone, lighting times/ramps, image thresholds, and the surface region from actual footage.
4. Confirm the return pump is operating normally before recording the motion reference.
5. Run a 48-hour observation trial spanning daylight, sunrise/sunset, night, feeding,
   cleaning, and normal room activity. Review every event for false positives.
6. Test a camera disconnect and reconnection; verify stale-frame hiding, event/recovery
   recording, and automatic reconnect. Do not interrupt tank life-support equipment for tests.
7. Test application restart, Mac login restart, and storage retention using disposable data.
8. Measure Mac CPU/memory, sustained storage growth, and the fraction of time video is usable.

**Exit criteria:** a documented setup profile, no secrets in logs, reliable reconnect in
the tested scenarios, and an agreed alert sensitivity. Do not label the tank healthy
merely because no event appeared. Recent rehabilitation means the reference can change.

## Phase 1c — microbubble observation (planned, not implemented)

The owner reports a tank-specific low-water symptom: the return pump draws air and
fills the display with microbubbles. Treat a sudden, sustained increase in visible
bubbles as a reason to inspect the return chamber, ATO, and pump intake. It is not a
measurement of water level or confirmation of the cause. Red Sea's troubleshooting
guidance also associates pump-injected bubbles with low rear-chamber water, restricted
water supply, and skimmer bubbles; see the manufacturer reference below.

The existing low-motion detector cannot stand in for this feature: bubbles may increase
pixel movement. Build and evaluate a separate observation path:

1. Select a visible region around the return outlet and adjacent open water. Record
   normal appearance under representative lighting, feeding, and skimmer operation.
2. Evaluate changes in the density and motion of small bright specks across short clips.
   Compare with labelled, naturally occurring bubble episodes and normal clips from
   separate days. Keep all owner footage local and outside this public repository.
3. Check whether the current 640×360, 2 fps decode preserves enough detail. Compare
   source-resolution crops and higher sampling rates before choosing capture settings;
   measure the effect on the Mac and retained evidence. Do not claim visibility at night
   or under blue lighting until tested.
4. Require repeated evidence, with a separately tuned persistence interval, deduplication,
   and recovery handling. Test confusion with food, stirred debris, fish, glare, exposure
   changes, and ordinary skimmer bubbles. Maintenance pause suppresses this observation.
   Missing or unusable video must produce uncertainty, never a reassuring water-level state.
5. Proposed event: **"Unusual microbubbles — check return chamber water level, ATO,
   and pump intake."** Attach an image and available clip. Surface it in the existing
   dashboard; phone delivery remains Phase 2. Do not operate equipment automatically.

This detects a symptom after air intake begins. An earlier warning requires a directly
observable water level or a separate level sensor. Do not lower water, disable the ATO,
or let the pump draw air deliberately to collect test footage.

**Exit criteria:** demonstrate that real bubble episodes are visible in the chosen capture
settings; report missed episodes, false events per day, time to detection, and lighting
coverage on held-out recordings. Agree acceptable sensitivity with the owner before
enabling the feature. Synthetic tests alone do not establish real-tank reliability.

## Phase 1d — ReefLED 50 status integration (planned, not implemented)

Connect the Mac directly to the light over the home network, starting with a read-only
connection test. The community `ha-reefbeat-component` project lists the G1 RSLED50 as
supported and documents local device access. This establishes a promising integration
path, not compatibility with the owner's firmware. Use that project's protocol research
as a reference; the planned Reef Watch connector does not require Home Assistant.

1. Confirm that the ReefLED is on the home network and reachable from the Mac. Enter its
   local address in private app settings; verify the reported model and firmware where
   available. A router address reservation can keep the address stable. Do not commit
   device addresses, identifiers, credentials, or raw device responses to GitHub.
2. Verify documented read endpoints against the actual device before implementing a
   small, read-only client. Allow only the required status requests; do not send changes
   to channels, schedules, acclimation, network settings, or device power.
3. Target blue, white, and moon channel percentages, operating mode, and available fixture
   temperature/fan readings. Confirm field meanings and units against ReefBeat. Show
   unsupported or missing fields as unavailable; device-reported percentages do not
   measure emitted light or PAR, and fixture temperature is not aquarium temperature.
4. Poll independently of camera capture with bounded request timeouts and retry backoff.
   Start by evaluating a 30-second interval. Timestamp readings, mark stale data clearly,
   and distinguish an unreachable light from a light reporting zero output. A failed light
   connection must not stop the camera or be treated as proof of a lighting failure.
5. Add a dashboard light-status panel and local history. Compare fresh reported channel
   levels with sustained camera brightness changes. Example observation: **"Light reports
   active channels, but the camera view is unusually dark."** Include both sources and
   their timestamps; use persistence and maintenance suppression to limit nuisance events.
6. Keep the owner's expected light schedule as a separate reference. A device unexpectedly
   reporting off during daytime should not redefine that as normal. Account for known
   ramps, manual overrides, and acclimation when interpreting observations. Continue the
   existing camera schedule checks when device status is unavailable.

The first connector uses local status without a ReefBeat cloud login. Full schedule and
program-library import needs separate investigation: the community project documents
cloud support for G1 program names and values. Do not promise automatic schedule import
as part of this phase. Equipment control remains outside scope; phone delivery is Phase 2.

**Exit criteria:** verify reads on the owner's RSLED50/firmware without changing settings;
compare values with ReefBeat across daylight and ramp periods; test timeouts, malformed or
partial responses, stale readings, reconnection, and camera-only fallback using synthetic
fixtures. Confirm that every client request is read-only and that persistent camera/device
disagreement is recorded with evidence. Record actual hardware results separately from tests.

## Phase 2 — useful notifications and phone access (not implemented)

- Choose notification delivery with the owner; configure it only with explicit destination
  authorization. Add deduplication, cooldown, retries, delivery status, and a test action.
- Offer secure private phone access, with authentication and TLS before expanding the
  loopback-only service. Prefer an authenticated private network or reverse proxy.
- Add an independent heartbeat receiver for Mac/app/network failure; a process cannot
  reliably alert when its own power or network is gone.
- Add a separate temperature sensor feed if desired. Sensor readings must retain their
  provenance and never be inferred from ordinary video.

**Exit criteria:** alerts reach the intended phone under controlled tests; failed delivery
is visible; unauthorized dashboard requests are rejected; disconnected monitoring has
an independent failure signal where configured.

## Phase 3 — fish sightings and activity (experimental, not implemented)

Initial subjects: ocellaris clownfish, yellow watchman goby, royal gramma. Collect real
footage across time of day, occlusion, blue light, and feeding. Manually annotate a small,
representative sample before choosing a model. Do not promise a general pretrained model
will recognize these fish accurately.

- Start with sightings and uncertainty; store last observed time and evidence.
- Evaluate local inference on Apple silicon using an appropriate supported model runtime.
- Separate a fish being out of view from an actual disappearance.
- Evaluate temporal behavior on clips, not isolated pictures.
- Train/evaluate on separate recording days to avoid near-identical train/test frames.
- Report per-species precision/recall, missed visible sightings, and false alerts per day.
- Add confidence thresholds and an explicit “insufficient visibility” state.

**Exit criteria:** publish actual measured performance on this tank, review false positives
with the owner, and enable alerts only for behaviors that pass the agreed evaluation.
No health percentage, disease diagnosis, or “fish dead” inference from absence.

## Phase 4 — coral and longer-term visual trends (not implemented)

When coral is present, collect same-position, same-lighting reference images with
exposure/white balance kept consistent. Review expansion and visible coverage over time.
Treat appearance changes as prompts to inspect/test, not as proof of bleaching or disease.
Perspective, refraction, coral motion, and light spectrum complicate growth/color measurements.

## Deliberately outside the current scope

Automatic dosing, heating, pump shutdown, feeding control, chemical measurements from
ordinary images, a general-purpose cloud aquarium agent, and unattended medical judgments.
This first prototype runs deterministic vision checks; it does not call an AI model.

## Technical references

- [Eufy camera model comparison](https://service.eufy.com/article-description/Differences-Between-eufy-Indoor-Cams)
- [Eufy RTSP configuration](https://service.eufy.com/article-description/Device-NAS-RTSP-Configuration-Guide)
- [Red Sea MAX C manual, English p. 23: pump-injected microbubbles](https://redseafish.com/wp-content/uploads/2014/07/4191-MAX-C-Series-Manual_ENG.SP_.PT_.v14B.pdf)
- [Red Sea ReefLED manual: home-network connection](https://g1.redseafish.com/wp-content/uploads/2018/10/7029_ReefLED-Manual_EN_-v19A.pdf)
- [Community ReefBeat integration: RSLED50 compatibility and ReefLED capabilities](https://github.com/Elwinmage/ha-reefbeat-component/blob/main/README.md)
- [FFmpeg RTSP protocol options](https://ffmpeg.org/ffmpeg-protocols.html#rtsp)
- [FastAPI application lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [Video-based fish locomotion research](https://arxiv.org/abs/2603.05407)

Manufacturer support for RTSP establishes an integration path, not proof this particular
camera/firmware has been tested. Fish-tracking research establishes feasibility in its
reported dataset, not performance on this reef.
