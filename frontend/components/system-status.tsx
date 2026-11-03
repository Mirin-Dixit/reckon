"use client";

import { useEffect, useRef, useState } from "react";
import { createApiClient } from "../lib/api";
import { checkSystemStatus, type SystemStatusState } from "../lib/system-status";
import { StatusView } from "./status-view";

const client = createApiClient(process.env.NEXT_PUBLIC_RAGBENCH_API_BASE_URL);

export function SystemStatus() {
  const [state, setState] = useState<SystemStatusState>({ phase: "loading" });
  const active = useRef<AbortController | null>(null);

  const check = async () => {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    const next = await checkSystemStatus(client, controller.signal);
    if (!controller.signal.aborted) setState(next);
  };

  useEffect(() => {
    const controller = new AbortController();
    active.current = controller;
    void checkSystemStatus(client, controller.signal).then(next => {
      if (!controller.signal.aborted) setState(next);
    });
    return () => active.current?.abort();
  }, []);

  return <section id="system-status" className="status-panel" tabIndex={-1} aria-labelledby="backend-heading" aria-busy={state.phase === "loading"}>
    <div className="panel-heading">
      <div><h2 id="backend-heading">System status</h2></div>
      <button className="check-button" type="button" disabled={state.phase === "loading"} onClick={() => {
        setState({ phase: "loading" });
        void check();
      }}>{state.phase === "loading" ? "Checking\u2026" : "Check backend"}</button>
    </div>
    <StatusView key={state.phase} state={state} />
    <div className="panel-footnote"><code>GET /api/v1/health</code><span>{"Read-only \u00b7 no provider call"}</span></div>
  </section>;
}
