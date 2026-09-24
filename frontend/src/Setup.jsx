import React, { useState } from "react";

export default function Setup({
  settings,
  act,
  fresh,
  calibrationActive,
  metrics,
}) {
  const [draft, setDraft] = useState(() => ({ ...settings, camera_url: "" }));
  const field = (name, value) => setDraft((d) => ({ ...d, [name]: value }));
  const roi = (index, value) =>
    field(
      "surface_roi",
      draft.surface_roi.map((v, i) => (i === index ? Number(value) / 100 : v)),
    );
  async function save(event) {
    event.preventDefault();
    const { camera_configured, ...payload } = draft;
    if (await act("settings", "PUT", payload)) field("camera_url", "");
  }
  return (
    <details className="setup">
      <summary>Camera &amp; monitoring setup</summary>
      <div className="setup-body">
        <p>
          In Eufy: camera settings → Storage → NAS (RTSP Stream) → Continuous
          Recording.
        </p>
        <form onSubmit={save}>
          <label className="wide">
            Camera stream address
            <input
              type="password"
              autoComplete="off"
              value={draft.camera_url}
              onChange={(e) => field("camera_url", e.target.value)}
              placeholder={
                settings.camera_configured
                  ? "Saved securely on this Mac · leave blank to keep"
                  : "Paste your Eufy RTSP address"
              }
            />
            <small>
              Saved only on this Mac. The dashboard never returns the saved
              address.
            </small>
          </label>
          <label>
            Timezone
            <input
              value={draft.timezone}
              onChange={(e) => field("timezone", e.target.value)}
              required
            />
          </label>
          <label>
            Daily comparison time
            <input
              type="time"
              value={draft.snapshot_at}
              onChange={(e) => field("snapshot_at", e.target.value)}
              required
            />
          </label>
          <label>
            Lights on
            <input
              type="time"
              value={draft.lights_on}
              onChange={(e) => field("lights_on", e.target.value)}
              required
            />
          </label>
          <label>
            Lights off
            <input
              type="time"
              value={draft.lights_off}
              onChange={(e) => field("lights_off", e.target.value)}
              required
            />
          </label>
          <label>
            Sunrise / sunset minutes
            <input
              type="number"
              min="0"
              max="180"
              value={draft.ramp_minutes}
              onChange={(e) => field("ramp_minutes", Number(e.target.value))}
              required
            />
          </label>
          <label>
            Change must persist (seconds)
            <input
              type="number"
              min="10"
              max="900"
              value={draft.persistence_seconds}
              onChange={(e) =>
                field("persistence_seconds", Number(e.target.value))
              }
              required
            />
          </label>
          <fieldset className="wide">
            <legend>Surface region (% of camera view)</legend>
            <p>
              Use a narrow region containing the visible water surface. The
              outlined region appears on the connected view after saving.
            </p>
            <div className="roi-fields">
              {["Left", "Top", "Width", "Height"].map((label, index) => (
                <label key={label}>
                  {label}
                  <input
                    type="number"
                    min={index < 2 ? 0 : 2}
                    max="100"
                    step="1"
                    value={Math.round(draft.surface_roi[index] * 100)}
                    onChange={(e) => roi(index, e.target.value)}
                    required
                  />
                </label>
              ))}
            </div>
          </fieldset>
          <label>
            Dark threshold (0–255)
            <input
              type="number"
              min="0"
              max="100"
              value={draft.dark_brightness}
              onChange={(e) => field("dark_brightness", Number(e.target.value))}
              required
            />
          </label>
          <label>
            Lit threshold (0–255)
            <input
              type="number"
              min="1"
              max="255"
              value={draft.lit_brightness}
              onChange={(e) => field("lit_brightness", Number(e.target.value))}
              required
            />
          </label>
          <label>
            Keep history (days)
            <input
              type="number"
              min="1"
              max="90"
              value={draft.retention_days}
              onChange={(e) => field("retention_days", Number(e.target.value))}
              required
            />
          </label>
          <div className="form-actions wide">
            <button type="submit">Save settings</button>
            {settings.camera_configured && (
              <button
                type="button"
                className="secondary"
                onClick={() => act("settings", "PUT", { disconnect: true })}
              >
                Disconnect camera
              </button>
            )}
          </div>
        </form>
        <section className="calibration">
          <h3>Set a surface reference</h3>
          <p>
            First confirm the pump is running normally, the glass is clean, and
            the camera is fixed. During steady daytime lighting, record two
            minutes of visible surface motion. Repeat after moving the camera,
            changing its settings, or restarting Reef Watch.
          </p>
          <p className="muted">
            Current image brightness: {metrics.brightness ?? "—"} / 255 ·
            Surface change: {metrics.motion ?? "—"}
          </p>
          <button
            className="secondary"
            disabled={!fresh || calibrationActive}
            onClick={() => act("calibrate", "POST")}
          >
            {calibrationActive
              ? "Recording reference…"
              : "Record surface reference"}
          </button>
        </section>
      </div>
    </details>
  );
}
