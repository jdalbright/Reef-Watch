import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { request, when } from "./api";
import Setup from "./Setup";
import "./styles.css";

function CameraView({ data }) {
  const [failed, setFailed] = useState(false);
  const [x, y, width, height] = data.settings.surface_roi;
  useEffect(() => setFailed(false), [data.last_frame_at]);
  return (
    <div className="camera" aria-label="Camera view">
      {data.fresh && !failed ? (
        <>
          <img
            className="feed"
            src={`/api/frame?t=${data.last_frame_at}`}
            onError={() => setFailed(true)}
            alt={
              data.demo
                ? "Synthetic demo frames, not tank footage"
                : "Latest tank camera frame, refreshed every two seconds"
            }
          />
          <div
            className="roi"
            title="Surface monitoring region"
            style={{
              left: `${x * 100}%`,
              top: `${y * 100}%`,
              width: `${width * 100}%`,
              height: `${height * 100}%`,
            }}
          />
          <span className="frame-caption">
            {data.demo ? "Synthetic demo" : "Sampled camera view"} ·{" "}
            {when(data.last_frame_at)}
          </span>
        </>
      ) : (
        <div className="camera-empty">
          <h2>
            {data.camera === "not_configured"
              ? "Camera not connected"
              : "Camera feed unavailable"}
          </h2>
          <p>
            {data.camera === "not_configured"
              ? "Connect your Eufy stream to begin."
              : "Waiting for fresh video. Observations are unavailable."}
          </p>
        </div>
      )}
    </div>
  );
}

function MonitorStatus({ data, act }) {
  const camera = {
    not_configured: "Not configured",
    connecting: "Connecting",
    connected: "Connected",
    reconnecting: "Reconnecting",
    offline: "Offline",
  }[data.camera];
  const lighting = !data.fresh
    ? "Waiting for video"
    : data.metrics.phase === "ramp"
      ? "Sunrise / sunset"
      : data.active_checks.some((x) => x.startsWith("unexpected_"))
        ? "Change detected"
        : data.metrics.phase === "day"
          ? "Daytime checks"
          : "Nighttime checks";
  const movement = !data.fresh
    ? "Needs fresh video"
    : data.active_checks.includes("low_movement")
      ? "Reduced movement"
      : data.calibration;
  return (
    <section className="panel monitor">
      <h2>Monitor status</h2>
      <dl>
        {[
          ["Camera", camera],
          ["Lighting", lighting],
          [
            "Surface movement",
            data.camera === "not_configured" ? "Needs calibration" : movement,
          ],
        ].map(([name, value]) => (
          <div key={name}>
            <dt>{name}</dt>
            <dd>
              <span
                className={`dot ${name === "Camera" && data.fresh ? "connected" : ""}`}
              />
              {value}
            </dd>
          </div>
        ))}
      </dl>
      <button
        onClick={() => act(data.paused_seconds ? "resume" : "pause", "POST")}
      >
        {data.paused_seconds
          ? `Resume checks · ${Math.ceil(data.paused_seconds / 60)}m left`
          : "Pause checks for 15 minutes"}
      </button>
      <p className="caveat">
        Visual observations do not measure water chemistry.
      </p>
      {data.error && <p className="error">{data.error}</p>}
    </section>
  );
}

function Events({ events, act }) {
  return (
    <section className="panel events">
      <h2>Recent events</h2>
      {!events.length ? (
        <p className="empty">Your observations will appear here.</p>
      ) : (
        <ol>
          {events.map((event) => (
            <li key={event.id}>
              <div className="event-top">
                <h3>{event.title}</h3>
                <time>{when(event.at)}</time>
              </div>
              <p>{event.detail}</p>
              <div className="event-actions">
                {event.snapshot && (
                  <a
                    href={`/media/${event.snapshot}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    View image
                  </a>
                )}
                {event.clip && (
                  <a
                    href={`/media/${event.clip}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Watch clip
                  </a>
                )}
                {!event.acknowledged ? (
                  <button
                    className="text-button"
                    onClick={() =>
                      act(`events/${event.id}/acknowledge`, "POST")
                    }
                  >
                    Mark reviewed
                  </button>
                ) : (
                  <span className="muted">Reviewed</span>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function Comparisons({ snapshots, fresh, act }) {
  return (
    <section className="panel comparisons">
      <div className="section-heading">
        <h2>Daily comparisons</h2>
        {fresh && (
          <button
            className="text-button"
            onClick={() => act("snapshots", "POST")}
          >
            Capture now
          </button>
        )}
      </div>
      {!snapshots.length ? (
        <p className="empty">Snapshots appear after the camera connects.</p>
      ) : (
        <div className="photos">
          {snapshots.map((item) => (
            <a
              href={`/media/${item.file}`}
              key={item.id}
              target="_blank"
              rel="noreferrer"
            >
              <img
                src={`/media/${item.file}`}
                alt={`Tank comparison from ${when(item.at)}`}
              />
              <span>{when(item.at)}</span>
              <small>{item.automatic ? "Scheduled" : "Manual"}</small>
            </a>
          ))}
        </div>
      )}
    </section>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [lost, setLost] = useState(false);
  const [notice, setNotice] = useState("");
  async function refresh() {
    try {
      setData(await request("status"));
      setLost(false);
    } catch {
      setLost(true);
    }
  }
  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 2000);
    return () => clearInterval(timer);
  }, []);
  async function act(path, method, payload) {
    setError("");
    setNotice("");
    try {
      await request(path, method, payload);
      await refresh();
      setNotice(
        path === "settings"
          ? "Settings saved. The camera is reconnecting; record a new surface reference."
          : "Done.",
      );
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    }
  }
  const effective =
    data && lost
      ? {
          ...data,
          fresh: false,
          camera: "offline",
          metrics: { phase: "unknown" },
        }
      : data;
  return (
    <main>
      <header>
        <a className="brand" href="/">
          Reef Watch
        </a>
        <span>Local monitor</span>
      </header>
      <section className="intro">
        <h1>A window into your reef.</h1>
        <p>20-gallon reef · Eufy Indoor Cam 2K</p>
      </section>
      {lost && (
        <p className="banner error" role="alert">
          Connection to Reef Watch lost. The displayed history may be out of
          date.
        </p>
      )}
      {data?.demo && (
        <p className="banner">
          Demo mode uses synthetic frames and separate history. No tank is being
          monitored.
        </p>
      )}
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="notice" role="status">
          {notice}
        </p>
      )}
      {!effective ? (
        <p className="empty">Connecting to your local monitor…</p>
      ) : (
        <>
          <div className="primary">
            <CameraView data={effective} />
            <MonitorStatus data={effective} act={act} />
          </div>
          <div className="history">
            <Events events={effective.events} act={act} />
            <Comparisons
              snapshots={effective.snapshots}
              fresh={effective.fresh}
              act={act}
            />
          </div>
          <Setup
            settings={effective.settings}
            act={act}
            fresh={effective.fresh}
            calibrationActive={effective.calibration_active}
            metrics={effective.metrics}
          />
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
