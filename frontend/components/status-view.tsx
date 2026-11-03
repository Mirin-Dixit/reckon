import type { ReactNode } from "react";
import { failureMessage } from "../lib/api";
import type { SystemStatusState } from "../lib/system-status";

function HealthTable({ state }: { state: SystemStatusState }) {
  const health = state.phase === "ready" ? state.health : undefined;
  const missing = <span className="missing-value" aria-label={state.phase === "loading" ? "Awaiting response" : "No response"}>{"\u2014"}</span>;
  const rows: readonly [string, string, ReactNode][] = [
    ["Service", "application", health?.application ?? missing],
    ["API version", "api_version", health ? <code>{health.api_version}</code> : missing],
    ["Backend status", "status", health ? <span className="status-value">{health.status === "ok" ? "Available" : "Degraded"}<code>{health.status}</code></span> : missing],
    ["Runtime initialized", "runtime_initialized", health ? health.runtime_initialized ? "Yes" : "No" : missing],
    ["Generation configured", "generation_configured", health ? health.generation_configured ? "Yes" : "No" : missing],
    ["Provider connection tested", "provider_connection_tested", health ? "Not tested" : missing],
  ];
  return (
    <details className="health-details"><summary>Inspect health fields</summary>
    <table className="health-table">
      <caption>Backend health response</caption>
      <tbody>
        {rows.map(([label, field, value]) => (
          <tr key={field}>
            <th scope="row">{label}<code className="field-name">{field}</code></th>
            <td>{value}</td>
          </tr>
        ))}
      </tbody>
    </table></details>
  );
}

export function StatusView({ state }: { state: SystemStatusState }) {
  if (state.phase === "loading") {
    return <div className="health-output" data-state="loading">
      <div className="status-body" role="status" aria-live="polite">
        <p className="status-label">Checking backend</p>
        <p className="status-description">Waiting for the local health endpoint. No model request is made.</p>
      </div>
      <HealthTable state={state} />
    </div>;
  }
  if (state.phase === "error") {
    return <div className="health-output" data-state="unavailable">
      <div className="status-body status-error" role="alert">
        <p className="status-label">{state.failure.kind === "configuration" ? "Configuration needs attention" : "Status check unavailable"}</p>
        <p className="status-description">{failureMessage(state.failure)}</p>
        <p className="error-qualification">No health result is available. This does not indicate an intentional abstention.</p>
      </div>
      <HealthTable state={state} />
    </div>;
  }
  const health = state.health;
  const degraded = health.status === "degraded";
  const title = degraded ? "Backend degraded" : health.generation_configured ? "Backend configured" : "Generation not configured";
  return <div className="health-output" data-state={degraded ? "degraded" : health.generation_configured ? "configured" : "unconfigured"}>
    <div className="status-body" role="status" aria-live="polite" aria-atomic="true">
      <span className={`status-label ${degraded || !health.generation_configured ? "status-attention" : "status-ready"}`}>{title}</span>
      <p className="status-description">{degraded
        ? "The backend responded, but its runtime did not initialize. Check the local backend configuration and retry."
        : health.generation_configured
          ? "Runtime and generation settings are available. Configuration alone does not confirm a working provider connection."
          : "The backend runtime is available. Model generation is not configured; provider credentials remain on the backend."}</p>
    </div>
    <HealthTable state={state} />
  </div>;
}
