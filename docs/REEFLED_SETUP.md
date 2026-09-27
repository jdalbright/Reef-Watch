# ReefLED 50 read-only qualification

The direct connector is **experimental software, tested with synthetic HTTP fixtures**.
The owner's RSLED50 and firmware have not yet been contacted or qualified. It does not
require Home Assistant, a ReefBeat login, or cloud access. No equipment write endpoint
is implemented. Do not enable comparison observations until actual readings are checked.

## Private setup

1. Keep the light and Mac on the same LAN. Find the light's IPv4 address in ReefBeat or
   the router's device list. Reserve its address if appropriate; Reef Watch does not change it.
2. Open `http://127.0.0.1:8765` → **Camera & monitoring setup**. Enter the address in
   **ReefLED 50 local IPv4 address** and save. Use the address alone, without a URL,
   credentials, or port. Only RFC1918 IPv4 addresses are accepted in this first version.
3. The address stays in the existing private `settings.json`, outside the checkout.
   The API never returns it. Blank input preserves it; **Disconnect light status** clears it.
4. Check the model, firmware, channel percentages, mode, fixture temperature and fan
   against ReefBeat. Missing, invalid, or unsupported fields show **Unavailable**, not zero.
   A partial response is labelled explicitly. Record only non-identifying model/firmware
   and qualification conclusions in public documentation, never raw device responses.
5. Observe stable daylight and the normal sunrise/sunset ramps. Do not change the fixture's
   settings for testing. If readings agree and the camera's dark threshold is calibrated,
   enable the comparison checkbox. It is disabled by default.

A reported channel percentage does not measure emitted light or PAR. Fixture temperature
is not aquarium temperature. Fan is interpreted as a reported percentage, not RPM; both
units still need verification against this fixture's firmware and ReefBeat.

## Read contract

Only HTTP port 80 and these fixed GET paths are used:

| Endpoint | Selected fields | Handling |
| --- | --- | --- |
| `/device-info` | `hw_model` | Must equal `RSLED50` before further requests. Other identity fields discarded. |
| `/firmware` | `version` | Numeric dotted version only; other formats unavailable pending review. |
| `/mode` | `mode` | `auto`, `manual`, `timer`; unknown modes unavailable. |
| `/manual` | `blue`, `white`, `moon`, `temperature`, `fan` | Finite numeric channels/fan 0–100; fixture temperature −40–150 °C. Missing/invalid values remain null. |

The `/manual` name is a **read endpoint**, not a command to switch operating mode.
Whether it reflects current output in every operating mode must be established on hardware.
No fallback to guessed paths, device writes, redirects, environment HTTP proxies, cloud
login, schedule import, program import, or automatic model adaptation is performed.

Each request has a 3-second HTTP timeout and a 5-second overall deadline, a 64 KiB body
limit, and generic error handling. After model identification, the other three reads run
concurrently. A poll is bounded to about 10 seconds. Successful/partial polls repeat after
30 seconds; failed polls back off to 60 then 120 seconds. Camera capture is independent.

Readings include the poll-completion time, which may lag individual responses by up to
5 seconds. Values are historical immediately on a failed poll; after 75 seconds they are
also labelled stale. The current panel hides their values while retaining the timestamp;
the local history preserves up to 20 recent polls for inspection. SQLite retains light
history under the same configured retention as camera history.

## Camera comparison

The opt-in observation requires fresh device status, all three channels, `auto` mode,
steady scheduled daytime, fresh camera frames, at least one channel ≥10%, and camera
brightness below the configured dark threshold for the configured persistence duration.
It emits once until the condition clears. Pause, gaps, unavailable fields, stale status,
manual/timer mode, and lighting ramps reset the comparison. Evidence uses the existing
image/clip pipeline; the event records device and frame timestamps and channel values.
Expected schedule checks continue independently when the fixture cannot be reached.
Acclimation/program interpretation is not imported; channel thresholds need real validation.

## Research and licensing

Reviewed on 2026-09-27: [Elwinmage/ha-reefbeat-component](https://github.com/Elwinmage/ha-reefbeat-component)
at commit `88ab3309adffe7581e72587bd03191b0b044385f`.

- [MIT license, copyright 2024 Elwinmage](https://github.com/Elwinmage/ha-reefbeat-component/blob/88ab3309adffe7581e72587bd03191b0b044385f/LICENSE).
  Reusing its code requires retaining its copyright and permission notice.
- [Base local API](https://github.com/Elwinmage/ha-reefbeat-component/blob/88ab3309adffe7581e72587bd03191b0b044385f/custom_components/redsea/reefbeat/api.py)
  establishes HTTP reads and endpoint names.
- [LED API](https://github.com/Elwinmage/ha-reefbeat-component/blob/88ab3309adffe7581e72587bd03191b0b044385f/custom_components/redsea/reefbeat/led.py),
  [field constants](https://github.com/Elwinmage/ha-reefbeat-component/blob/88ab3309adffe7581e72587bd03191b0b044385f/custom_components/redsea/const.py),
  and [sensors](https://github.com/Elwinmage/ha-reefbeat-component/blob/88ab3309adffe7581e72587bd03191b0b044385f/custom_components/redsea/sensor.py)
  document G1 channels and fixture temperature/fan field units.

Reef Watch's connector is independently written against these protocol observations; it
neither vendors nor runs the community integration or its equipment-control code. Its
RSLED50 support listing is a research lead, not proof of this owner's hardware compatibility.
