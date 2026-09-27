import React from "react";
import { when } from "./api";

const states = {
  not_configured: "Not configured",
  connecting: "Connecting",
  connected: "Fresh readings",
  partial: "Some readings unavailable",
  unavailable: "Light status unavailable",
  unsupported: "Device did not identify as RSLED50",
  stale: "Stale readings",
};

export default function LightStatus({ light, history, enabled }) {
  if (!light) return null;
  const reading = light.reading || {};
  const value = (key, suffix = "") =>
    light.fresh && reading[key] != null
      ? `${reading[key]}${suffix}`
      : "Unavailable";
  return (
    <section className="panel light-status">
      <div className="section-heading">
        <h2>ReefLED 50 · read-only</h2>
        <span>{states[light.state]}</span>
      </div>
      <dl className="light-values">
        {[
          ["Model", value("model")],
          ["Firmware", value("firmware")],
          ["Mode", value("mode")],
          ["Blue", value("blue", "%")],
          ["White", value("white", "%")],
          ["Moon", value("moon", "%")],
          ["Fixture temperature", value("fixture_temperature_c", " °C")],
          ["Fan", value("fan_percent", "%")],
        ].map(([label, text]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{text}</dd>
          </div>
        ))}
      </dl>
      <p className="muted">
        Last status received: {reading.at ? when(reading.at) : "None"}. Polls
        every 30 seconds; failed reads back off.
      </p>
      <p className="caveat">
        Fixture temperature is not aquarium temperature. Channel percentages do
        not measure emitted light or PAR.{" "}
        {enabled
          ? "Camera comparisons enabled for steady automatic daytime operation."
          : "Camera comparisons disabled pending qualification with ReefBeat."}
      </p>
      {history?.length > 0 && (
        <details>
          <summary>Recent light reads</summary>
          <ol className="light-history">
            {history.map((item, index) => (
              <li key={`${item.polled_at}-${index}`}>
                {when(item.polled_at)} · {states[item.state]} · Blue{" "}
                {item.blue ?? "—"} / White {item.white ?? "—"} / Moon{" "}
                {item.moon ?? "—"}%
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}
