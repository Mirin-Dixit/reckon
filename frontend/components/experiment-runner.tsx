"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { buildExperiment, createExperimentClient, experimentFailure, notice, type Freeze, type Job, type Results } from "../lib/experiment-api";
import { RiskAnalysis } from "./risk-analysis";
import { createMutationGate, downloadJson } from "../lib/workspace-actions";

export function nextExperimentSelection(previous: { id: string; revision: number }, id: string) {
  // A repeated click must invalidate the request too, not just clear its result.
  return { id, revision: previous.revision + 1 };
}

export function ExperimentHistory({ jobs, selected, busy, onSelect }: {
  jobs: Job[]; selected: string; busy: boolean; onSelect: (id: string) => void;
}) {
  return <ul className="experiment-history">{jobs.map(job => <li key={job.id}><button type="button" aria-controls="selected-experiment" aria-pressed={selected === job.id} disabled={busy} onClick={() => onSelect(job.id)}><strong>{String(job.configuration.split)}</strong> / {job.status} / {job.observed_run_count}/{job.expected_run_count}<br /><code>{job.id}</code><br />{job.created_at}<progress value={job.observed_run_count} max={job.expected_run_count} aria-label={`${job.observed_run_count} of ${job.expected_run_count} observations saved`} /><span className="experiment-view-label">View saved results</span></button></li>)}</ul>;
}

export function ExperimentDetail({ result, loading, error, busy, freezing = false, freeze, actionError = "", exportFeedback, onRetry, onFreeze, onExport }: {
  result: Results | null; loading: boolean; error: string; busy: boolean; freeze: Freeze | null;
  actionError?: string;
  freezing?: boolean;
  exportFeedback?: { message: string; failed: boolean } | null;
  onRetry: () => void; onFreeze: () => void; onExport: (value: unknown, filename: string) => void;
}) {
  return <section id="selected-experiment" aria-labelledby="selected-experiment-heading" aria-busy={loading}>
    <h2 id="selected-experiment-heading">Selected experiment</h2>
    {loading ? <p role="status">Loading saved experiment results…</p> : error ? <div role="alert"><p>{error}</p><button type="button" onClick={onRetry}>Retry loading results</button></div> : !result ? <p>No saved experiment selected. Choose View saved results in the history.</p> : <>
      <div className="query-actions">
        <button type="button" onClick={() => onExport(result, `synthetic-${result.id}.json`)}>Export synthetic result JSON</button>
        <button type="button" disabled={busy || result.status !== "done" || result.configuration.split !== "dev"} onClick={onFreeze}>{freezing ? "Freezing Dev configuration…" : "Freeze this Dev configuration"}</button></div>
      {exportFeedback && <p className="workspace-feedback" role={exportFeedback.failed ? "alert" : "status"}>{exportFeedback.message}</p>}
      <p>Freezes are immutable fixture configurations. They do not accept a benchmark or authorize held-out evaluation.</p>
      {actionError && <p role="alert">{actionError}</p>}
      {freeze?.job_id === result.id && <div role="status"><p>Dev configuration frozen: <code>{freeze.sha256}</code></p><button type="button" onClick={() => onExport(freeze, `synthetic-freeze-${freeze.job_id}.json`)}>Export freeze JSON</button></div>}
      <ExperimentResults key={result.id} value={result} />
    </>}
  </section>;
}

export function ExperimentResults({ value }: { value: Results }) {
  const [filter, setFilter] = useState("all");
  const rows = value.observations.filter(row => filter === "all" || (filter === "failure" ? row.error !== null : row.observed.decision === filter));
  return <section aria-labelledby="experiment-result-heading">
    <h3 id="experiment-result-heading">Recorded observations</h3>
    <p><strong>{notice}</strong></p>
    <p>Status: <strong>{value.status}</strong> / {value.observed_run_count} of {value.expected_run_count} observations saved.</p>
    {value.error && <p role="status">Recorded failure code: <code>{value.error}</code>. This run is incomplete or failed.</p>}
    <p>Execution completion does not establish model quality. Failures are separate from abstentions.</p>
    <dl className="ledger-metadata">
      <div><dt>Experiment ID</dt><dd><code>{value.id}</code></dd></div>
      <div><dt>Created / updated</dt><dd>{value.created_at} / {value.updated_at}</dd></div>
      <div><dt>Dataset fingerprints</dt><dd><pre>{JSON.stringify(value.dataset_fingerprint, null, 2)}</pre></dd></div>
      <div><dt>Runtime source SHA-256</dt><dd><code>{value.runtime_source_sha256}</code></dd></div>
    </dl>
    <details><summary>Effective configuration and provenance</summary><pre>{JSON.stringify({ configuration: value.configuration, retrieval: value.result?.retrieval_configuration, policies: value.result?.policy_configurations, generation: value.result?.generation_configuration, software: value.result?.software_metadata, environment: value.result?.environment_metadata }, null, 2)}</pre></details>
    <label htmlFor="observation-filter">Filter observations</label>
    <select id="observation-filter" value={filter} onChange={e => setFilter(e.target.value)}>
      {[["all", "All outcomes"], ["ANSWER", "Answer"], ["ABSTAIN", "Abstain"], ["CLARIFY", "Clarify"], ["failure", "Execution failure"]].map(([v, label]) => <option key={v} value={v}>{label}</option>)}
    </select>
    <div className="ledger-scroll" role="region" aria-label="Synthetic per-question results" tabIndex={0}><table className="experiment-table"><caption>Synthetic per-question results</caption><thead><tr><th scope="col">Question</th><th scope="col">Policy</th><th scope="col">Execution</th><th scope="col">Decision</th><th scope="col">Response</th><th scope="col">Recorded error</th></tr></thead>
      <tbody>{rows.map(row => <tr key={`${row.policy_name}:${row.question_id}`}><th scope="row"><code>{row.question_id}</code></th><td>{row.policy_name}</td><td>{row.observed.execution_status}</td><td>{row.observed.decision ?? "No decision"}</td><td>{row.observed.answer ?? row.observed.clarification_question ?? (row.error ? "Execution failure" : "Intentionally withheld")}</td><td>{row.error === null ? "None" : <code>{JSON.stringify(row.error)}</code>}</td></tr>)}</tbody></table></div>
    {rows.length === 0 && <p>No matching observations saved.</p>}
    {value.result && <details><summary>Synthetic summary metrics</summary><p>Fixture accounting only; these values are not empirical benchmark results.</p><pre>{JSON.stringify(value.result.metrics, null, 2)}</pre></details>}
    {value.result && <RiskAnalysis key={value.id} experimentId={value.id} />}
    <details><summary>Full recorded evidence and synthetic reference fields</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>
  </section>;
}

export function ExperimentRunner() {
  const [split, setSplit] = useState("dev");
  const [method, setMethod] = useState("bm25");
  const [policy, setPolicy] = useState("all");
  const [threshold, setThreshold] = useState("0");
  const [seed, setSeed] = useState("0");
  const [topK, setTopK] = useState("3");
  const [ids, setIds] = useState("");
  const [failFast, setFailFast] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selection, setSelection] = useState({ id: "", revision: 0 });
  const selected = selection.id;
  const [result, setResult] = useState<Results | null>(null);
  const [freeze, setFreeze] = useState<Freeze | null>(null);
  const [error, setError] = useState("");
  const [submissionError, setSubmissionError] = useState("");
  const [exportFeedback, setExportFeedback] = useState<{ message: string; failed: boolean } | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(true);
  const [detailError, setDetailError] = useState("");
  const [freezeError, setFreezeError] = useState("");
  const [busy, setBusy] = useState(false);
  const [freezing, setFreezing] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [offset, setOffset] = useState(0);
  const mutation = useRef<AbortController | null>(null);
  const mutationGate = useRef(createMutationGate());
  const detailPanel = useRef<HTMLDivElement | null>(null);
  useEffect(() => () => mutation.current?.abort(), []);
  useEffect(() => {
    const controller = new AbortController();
    const client = createExperimentClient(process.env.NEXT_PUBLIC_RECKON_API_BASE_URL);
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function poll() {
      try {
        const history = await client.list(controller.signal, offset);
        if (controller.signal.aborted) return;
        setJobs(history); setLoading(false);
        const id = selected || history[0]?.id;
        let detail: Results | null = null;
        try {
          if (id) detail = await client.results(id, controller.signal);
        } catch (e) {
          if (!controller.signal.aborted) { setResult(null); setDetailError(`Saved results could not be loaded. ${experimentFailure(e)}`); setDetailLoading(false); }
          return;
        }
        if (controller.signal.aborted) return;
        setResult(detail); setDetailLoading(false); setDetailError(""); setError("");
        if (history.some(job => ["queued", "running"].includes(job.status)) || (detail && ["queued", "running"].includes(detail.status))) timer = setTimeout(() => void poll(), 1000);
      } catch (e) {
        if (!controller.signal.aborted) { setError(experimentFailure(e)); setResult(null); setDetailError("History could not be loaded. Refresh history or retry loading results."); setLoading(false); setDetailLoading(false); }
      }
    }
    void poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [selection, selected, refresh, offset]);

  function selectJob(id: string) {
    setSelection(previous => nextExperimentSelection(previous, id));
    setResult(null); setFreeze(null); setFreezeError(""); setDetailError(""); setDetailLoading(true); setExportFeedback(null);
    detailPanel.current?.focus({ preventScroll: true });
    detailPanel.current?.scrollIntoView({ block: "start", behavior: "auto" });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!mutationGate.current.enter()) return;
    let body;
    try { body = buildExperiment(split, method, policy, threshold, seed, ids, topK, failFast); }
    catch (e) { setSubmissionError(e instanceof Error ? e.message : "Check the settings."); mutationGate.current.leave(); return; }
    mutation.current?.abort(); const controller = new AbortController(); mutation.current = controller;
    setBusy(true); setSubmissionError(""); setFreezeError("");
    try {
      const job = await createExperimentClient(process.env.NEXT_PUBLIC_RECKON_API_BASE_URL).start(body, controller.signal);
      if (!controller.signal.aborted) { selectJob(job.id); setOffset(0); setRefresh(v => v + 1); }
    } catch (e) { if (!controller.signal.aborted) setSubmissionError(experimentFailure(e)); }
    finally { mutationGate.current.leave(); if (!controller.signal.aborted) setBusy(false); }
  }
  async function freezeDev() {
    if (!result || !mutationGate.current.enter()) return;
    mutation.current?.abort(); const controller = new AbortController(); mutation.current = controller;
    setBusy(true); setFreezing(true); setFreezeError("");
    try {
      const saved = await createExperimentClient(process.env.NEXT_PUBLIC_RECKON_API_BASE_URL).freeze(result.id, controller.signal);
      if (!controller.signal.aborted) setFreeze(saved);
    } catch (e) { if (!controller.signal.aborted) setFreezeError(experimentFailure(e)); }
    finally { mutationGate.current.leave(); if (!controller.signal.aborted) { setBusy(false); setFreezing(false); } }
  }
  function exportJson(value: unknown, filename: string) {
    try { downloadJson(value, filename); setExportFeedback({ message: "JSON export prepared. Check your browser downloads.", failed: false }); }
    catch { setExportFeedback({ message: "Could not prepare JSON export. Please try again.", failed: true }); }
  }
  return <section className="query-lab experiments" aria-labelledby="experiments-title">
    <header className="query-heading"><p className="page-eyebrow">Experiment notebook</p><h1 id="experiments-title">Experiments</h1><p><strong>{notice}</strong></p><p>Pilot30 and full benchmark review are deferred. Empirical execution and held-out evaluation are blocked.</p></header>
    <div className="query-workspace"><form onSubmit={submit} aria-describedby="experiment-validation">
      <fieldset disabled={busy}><legend>Configure a synthetic run</legend>
        <label>Dataset<input value="p4-synthetic.v1 / fictional inventory ledger" readOnly /></label>
        <label>Model<input value="fixture-rules.v1 / no model inference" readOnly /></label>
        <div className="query-settings">
          <label>Split<select value={split} onChange={e => { setSplit(e.target.value); setIds(""); }}><option value="train">Synthetic Train</option><option value="dev">Synthetic Dev</option></select></label>
          <label>Retrieval<select value={method} onChange={e => { setMethod(e.target.value); setThreshold("0"); }}><option value="bm25">BM25</option><option value="dense">Dense / token hash fixture</option><option value="hybrid">Hybrid / RRF</option></select></label>
          <label>Policy<select value={policy} onChange={e => setPolicy(e.target.value)}><option value="all">All three policies</option><option value="always_answer">Always answer</option><option value="prompt_abstention">Prompt abstention / fixture rules</option><option value="threshold">Retrieval threshold</option></select></label>
          <label>Threshold<input value={threshold} disabled={!["all", "threshold"].includes(policy)} onChange={e => setThreshold(e.target.value)} inputMode="decimal" /></label>
          <label>Top-k<input value={topK} onChange={e => setTopK(e.target.value)} inputMode="numeric" /></label>
          <label>Seed<input value={seed} onChange={e => setSeed(e.target.value)} inputMode="numeric" /></label>
        </div>
        <label>Question IDs (optional, comma separated)<input value={ids} onChange={e => setIds(e.target.value)} aria-describedby="fixture-help" /></label>
        <p id="fixture-help">Use synthetic_{split}_01 through synthetic_{split}_04; blank runs all four. Train 04 deliberately fails. Dev contains answer, unknown, and clarification cases. Thresholds are ranking scores, not confidence probabilities. Hybrid uses RRF k=60, candidate-k=50.</p>
        <label className="experiment-checkbox"><input type="checkbox" checked={failFast} onChange={e => setFailFast(e.target.checked)} /> Stop after the first execution failure</label>
        <p id="experiment-validation" className={submissionError ? "experiment-error" : undefined} role={submissionError ? "alert" : undefined}>{submissionError}</p>
        <button className="check-button" type="submit">{busy && !freezing ? "Saving request…" : "Run synthetic experiment"}</button>
      </fieldset>
    </form><section className="query-output" aria-labelledby="job-history"><h2 id="job-history">Experiment history</h2>
      <p>One active job, four waiting. Results survive a backend restart. Interrupted work is marked incomplete and never rerun automatically.</p>
      <button type="button" disabled={busy || loading} onClick={() => { setLoading(true); setRefresh(v => v + 1); }}>{loading ? "Refreshing history…" : "Refresh history"}</button>
      {error && <p className="experiment-error" role="alert">{error}</p>}
      {loading && <p role="status">Loading saved experiments…</p>}
      {!loading && jobs.length === 0 && <p>No saved experiments on this history page.</p>}
      <ExperimentHistory jobs={jobs} selected={selected || jobs[0]?.id || ""} busy={busy} onSelect={selectJob} />
      <div className="query-actions"><button type="button" disabled={offset === 0 || busy || loading} onClick={() => { setExportFeedback(null); setLoading(true); setOffset(v => Math.max(0, v - 50)); setSelection(previous => nextExperimentSelection(previous, "")); setResult(null); setFreeze(null); setDetailLoading(true); }}>Newer</button><button type="button" disabled={jobs.length < 50 || busy || loading} onClick={() => { setExportFeedback(null); setLoading(true); setOffset(v => v + 50); setSelection(previous => nextExperimentSelection(previous, "")); setResult(null); setFreeze(null); setDetailLoading(true); }}>Older</button></div>
    </section></div>
    <div className="experiment-detail" ref={detailPanel} tabIndex={-1}><ExperimentDetail result={result} loading={detailLoading} error={detailError} busy={busy} freezing={freezing} freeze={freeze} actionError={freezeError} exportFeedback={exportFeedback} onRetry={() => { setDetailLoading(true); setDetailError(""); setRefresh(v => v + 1); }} onFreeze={() => void freezeDev()} onExport={exportJson} /></div>
  </section>;
}
