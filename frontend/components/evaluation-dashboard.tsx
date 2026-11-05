"use client";

import { useEffect, useRef, useState } from "react";
import { metrics, type AnalysisReport } from "../lib/analysis-api";
import { canAnalyze, comparisonBlocker, createEvaluationClient, evaluationSession, initialEvaluationState, type EvaluationState } from "../lib/evaluation-dashboard";
import type { Job, Results } from "../lib/experiment-api";
import { IntervalText, RiskPlot } from "./risk-analysis";
import { EvaluationObservations } from "./evaluation-observations";
import { EvaluationReport } from "./evaluation-report";

const metric = (n: number | null) => n === null ? "Undefined" : n.toFixed(3);
const present = (v: unknown) => typeof v === "string" || typeof v === "number" ? String(v) : "Unavailable";
const names = { end_to_end_coverage: "End-to-end coverage A/N", successful_execution_coverage: "Successful-execution coverage A/(A+B+C)", selective_risk: "Selective risk", failure_rate: "Execution failure rate" };

export function PolicyPerformance({ report }: { report: AnalysisReport }) {
  return <section className="evaluation-section" aria-labelledby="performance-heading">
    <h2 id="performance-heading">Policy performance</h2>
    <p>{report.loss_basis === "unknown" ? "Answer judgments are unknown. Selective risk remains undefined." : "Synthetic lexical exact-match proxy only, not verified semantic correctness."} Each policy uses the same {report.matched_questions} matched questions; observations across policies are not independent samples.</p>
    <div className="ledger-scroll" role="region" aria-label="Saved policy metrics" tabIndex={0}><table className="evidence-table">
      <caption>R1 policy metrics, with undefined values retained</caption><thead><tr><th scope="col">Policy / experiment</th><th scope="col">End-to-end coverage A/N</th><th scope="col">Successful-execution coverage A/(A+B+C)</th><th scope="col">Selective risk</th><th scope="col">Failure rate</th><th scope="col">Missing observation rate</th><th scope="col">Judgment completeness</th></tr></thead>
      <tbody>{report.rows.map(row => <tr key={row.id}><th scope="row">{row.policy}<br /><code>{row.experiment_id}</code>{row.threshold !== null && <p>{row.direction} threshold {row.threshold}</p>}</th>
        {[row.end_to_end_coverage, row.successful_execution_coverage].map((f, i) => <td key={i}>{metric(f.value)} ({f.numerator}/{f.denominator})</td>)}
        <td>{metric(row.selective_risk)}{row.undefined_reason && <p>{row.undefined_reason}</p>}{row.risk_bounds && <p>Identification bounds [{row.risk_bounds.map(metric).join(", ")}], not a confidence interval.</p>}</td>
        {[row.failure_rate, row.missing_rate, row.judgment_completeness].map((f, i) => <td key={i}>{metric(f.value)} ({f.numerator}/{f.denominator})</td>)}
      </tr>)}</tbody></table></div>
    <details><summary>Paired bootstrap uncertainty and sample sizes</summary><p>{report.resampling_units} resampling units / {report.matched_questions} questions; grouping: {report.grouping}. {report.resamples} resamples, seed {report.seed}. Intervals may be unavailable for zero answers, unknown judgments or small samples.</p>
      {report.rows.map(row => <div key={row.id}><h3>{row.policy} / <code>{row.experiment_id}</code></h3><ul>{metrics.map(key => <li key={key}>{names[key]}: <IntervalText interval={row.uncertainty[key]} /></li>)}</ul></div>)}
    </details>
    {report.comparisons.length > 0 && <details><summary>Validated matched-policy differences</summary><p>Left minus right on matched questions. Risk differences require compatible coverage. Raw thresholds are not compared across score families.</p><div className="ledger-scroll" role="region" aria-label="Matched-policy differences" tabIndex={0}><table className="evidence-table"><caption>R1 validated differences</caption><thead><tr><th scope="col">Pair</th><th scope="col">Metric</th><th scope="col">Difference</th><th scope="col">Uncertainty</th></tr></thead><tbody>{report.comparisons.flatMap((pair, i) => metrics.map(key => <tr key={`${i}:${key}`}><th scope="row"><code>{pair.left}</code> minus <code>{pair.right}</code></th><td>{names[key]}</td><td>{metric(pair.uncertainty[key].estimate)}</td><td><IntervalText interval={pair.uncertainty[key]} /></td></tr>))}</tbody></table></div></details>}
  </section>;
}

export function EvaluationAnalysis({ report }: { report: AnalysisReport }) {
  return <><PolicyPerformance report={report} />
    <section className="evaluation-section" aria-labelledby="curve-heading"><h2 id="curve-heading">Risk-Coverage</h2><p>Dots are saved operating points. Step lines represent compatible native threshold trials only; unrelated policies are never joined. Partial domains are not extrapolated.</p><RiskPlot report={report} />
      {!report.curves.length ? <p>No saved threshold series. Individual operating points do not establish AURC.</p> : report.curves.map(curve => <div className="evaluation-area" key={curve.id}><h3>{curve.area.full_aurc !== null ? "Complete threshold sweep" : curve.area.partial_aurc !== null ? "Partial threshold curve" : "Undefined AURC"}</h3><p>Series <code>{curve.id}</code> / {curve.points.length} saved operating points. {curve.area.full_aurc !== null ? `Full right-step AURC: ${metric(curve.area.full_aurc)}` : curve.area.partial_aurc !== null ? `Partial right-step area: ${metric(curve.area.partial_aurc)}` : `Unavailable: ${curve.area.undefined_reason}`}</p><p>Coverage domain: {curve.area.coverage_bounds ? `[${curve.area.coverage_bounds.map(metric).join(", ")}]` : "Unavailable"}.</p><IntervalText interval={curve.uncertainty} /></div>)}
      {report.curve_comparisons.map(pair => <p key={`${pair.left}:${pair.right}`}>Validated AURC difference <code>{pair.left}</code> minus <code>{pair.right}</code>: {metric(pair.uncertainty.estimate)}. <IntervalText interval={pair.uncertainty} /></p>)}
    </section>
    <section className="evaluation-section" aria-labelledby="analysis-provenance"><h2 id="analysis-provenance">Analysis provenance and limitations</h2><dl className="ledger-metadata">
      <div><dt>Analysis schema</dt><dd><code>{report.schema_version}</code></dd></div><div><dt>Compatibility fingerprint</dt><dd><code>{report.provenance_sha256}</code></dd></div><div><dt>Split / retrieval</dt><dd>{report.split} / {report.retrieval_method}</dd></div><div><dt>Judgment basis</dt><dd>{report.loss_basis}; no verified human semantic judgments are supplied.</dd></div><div><dt>Bootstrap</dt><dd>{report.interval_method}; {report.resamples} resamples; seed {report.seed}; {report.resampling_units} units</dd></div>
    </dl><details><summary>Source-record fingerprints</summary><ul>{report.rows.map(row => <li key={row.id}><code>{row.experiment_id}</code> / {row.policy}: <code>{row.source_record_sha256}</code></li>)}</ul></details><ul>{report.limitations.map(text => <li key={text}>{text}</li>)}</ul></section>
  </>;
}

export function EvaluationOverview({ detail }: { detail: Results }) {
  const config = detail.configuration;
  const retrieval = detail.result?.retrieval_configuration ?? config.retrieval;
  const method = typeof retrieval === "object" && retrieval !== null && "method" in retrieval ? retrieval.method : undefined;
  return <><p className="evaluation-identity"><code>{detail.id}</code></p><dl className="ledger-metadata">
    <div><dt>Evaluation status</dt><dd>Synthetic development only. Empirical evaluation is unavailable.</dd></div><div><dt>Dataset split</dt><dd>{present(config.split)}</dd></div><div><dt>Retrieval</dt><dd>{present(method)}</dd></div><div><dt>Execution status</dt><dd>{detail.status}{detail.error !== null && " / a recorded error is present; not an intentional abstention"}</dd></div><div><dt>Selected questions</dt><dd>{detail.result ? detail.result.selected_question_ids.length : "Unavailable until a saved result snapshot exists"}</dd></div><div><dt>Saved observations</dt><dd>{detail.observed_run_count} / {detail.expected_run_count}</dd></div><div><dt>Available evaluation results</dt><dd>{canAnalyze(detail) ? "Complete saved cohort; R1 analysis can be requested below." : "Incomplete or unavailable snapshot. Matched analysis is unavailable."}</dd></div><div><dt>Saved experiment seed</dt><dd>{detail.result ? present(detail.result.random_seed) : present(config.random_seed)}</dd></div><div><dt>Runtime fingerprint</dt><dd><code>{detail.runtime_source_sha256}</code></dd></div>
  </dl><details><summary>Saved retrieval and policy configuration</summary><pre>{JSON.stringify({ retrieval: retrieval ?? "Unavailable", policies: detail.result?.policy_configurations ?? config.policies ?? "Unavailable", dataset_fingerprint: detail.dataset_fingerprint }, null, 2)}</pre></details></>;
}

type Actions = Pick<ReturnType<typeof evaluationSession>, "analyze" | "invalidateAnalysis" | "cancelAnalysis">;
export function ComparisonCandidate({ selected, job, thresholdOnly, checked, limitReached, validated, onChange }: {
  selected: Job; job: Job; thresholdOnly: boolean; checked: boolean;
  limitReached: boolean; validated: boolean; onChange: (checked: boolean) => void;
}) {
  const reason = comparisonBlocker(selected, job, thresholdOnly);
  const description = `comparison-${job.id}`;
  return <label className="analysis-option"><input type="checkbox" checked={checked} disabled={reason !== null || (!checked && limitReached)} aria-describedby={description} onChange={e => onChange(e.target.checked)} /><span><code>{job.id}</code><span id={description} className="analysis-help">{reason ? `Unavailable: ${reason}` : !checked && limitReached ? "Selection limit reached. Uncheck another candidate to select this run." : validated ? "R1 compatibility validated in the current report." : "Metadata match; full R1 validation still required."}</span></span></label>;
}

function SelectedEvaluation({ state, actions }: { state: EvaluationState; actions: Actions }) {
  const [proxy, setProxy] = useState(false), [thresholdOnly, setThresholdOnly] = useState(false);
  const [compare, setCompare] = useState<string[]>([]);
  const detail = state.detail!;
  const pending = state.analysisPhase === "loading";
  const selected = state.jobs.find(j => j.id === detail.id) ?? detail;
  const candidates = state.jobs.filter(j => j.id !== detail.id);
  return <><EvaluationOverview detail={detail} /><EvaluationObservations detail={detail} /><section className="risk-analysis" aria-labelledby="evaluation-settings-heading"><h2 id="evaluation-settings-heading">Analysis configuration</h2><p>Read-only R1 analysis, not model inference. Unknown judgments are the default. No threshold tuning or held-out evaluation is started.</p>
    <fieldset disabled={pending || state.listPhase !== "ready"}><legend>Judgments and saved trials</legend>
      <label className="analysis-option"><input type="checkbox" checked={proxy} onChange={e => { actions.invalidateAnalysis(); setProxy(e.target.checked); }} /><span><span className="analysis-option-title">Use synthetic lexical proxy judgments</span><span className="analysis-help">Explicit opt-in. Lexical exact match is not semantic correctness.</span></span></label>
      <label className="analysis-option"><input type="checkbox" checked={thresholdOnly} onChange={e => { actions.invalidateAnalysis(); setThresholdOnly(e.target.checked); setCompare([]); }} /><span><span className="analysis-option-title">Threshold trials only</span><span className="analysis-help">Exclude repeated controls when comparing saved native threshold trials. Changing this setting clears comparison selections.</span></span></label>
    </fieldset>
    <fieldset disabled={pending || state.listPhase !== "ready"} className="evaluation-candidates"><legend>Comparison candidates</legend><p>Metadata matches are provisional. R1 validates the full question cohort, evidence, generation settings and provenance before any comparison. Up to seven additional experiments.</p>
      {!candidates.length && <p>No other saved experiments on this history page.</p>}{candidates.map(job => <ComparisonCandidate key={job.id} selected={selected} job={job} thresholdOnly={thresholdOnly} checked={compare.includes(job.id)} limitReached={compare.length >= 7} validated={state.analysis?.rows.some(row => row.experiment_id === job.id) ?? false} onChange={checked => { actions.invalidateAnalysis(); setCompare(previous => checked ? [...previous, job.id] : previous.filter(id => id !== job.id)); }} />)}
    </fieldset>
    {!canAnalyze(detail) && <p role="status">This experiment is incomplete or has no usable result snapshot. Missing observations cannot become zero-risk results.</p>}
    <div className="query-actions"><button className="check-button" type="button" disabled={pending || state.listPhase !== "ready" || !canAnalyze(detail)} onClick={() => void actions.analyze(compare, proxy, thresholdOnly)}>{pending ? "Loading R1 analysis..." : "Analyze saved observations"}</button>{pending && <button type="button" onClick={actions.cancelAnalysis}>Cancel analysis</button>}</div>
  </section>{pending && <p role="status">Loading analysis of the selected saved observations...</p>}{state.analysisPhase === "error" && <p className="workspace-feedback" role="alert">{state.analysisError}</p>}{state.analysisPhase === "cancelled" && <p role="status">Stopped waiting for analysis. Backend computation may continue; saved records are unchanged.</p>}{state.analysis ? <><EvaluationAnalysis report={state.analysis} />{state.analysisSelection && <EvaluationReport key={JSON.stringify(state.analysisSelection)} detail={detail} report={state.analysis} selection={state.analysisSelection} jobs={state.jobs} />}</> : !pending && <p className="evaluation-section">No policy metrics loaded. Request R1 analysis above; undefined or unavailable judgments will remain explicit.</p>}</>;
}

export function EvaluationDashboard() {
  const [state, setState] = useState<EvaluationState>(initialEvaluationState);
  const session = useRef<ReturnType<typeof evaluationSession> | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { const current = evaluationSession(createEvaluationClient(process.env.NEXT_PUBLIC_RECKON_API_BASE_URL), setState); session.current = current; void current.refresh(); return () => { current.dispose(); session.current = null; }; }, []);
  const actions: Actions = { analyze: (...args) => session.current?.analyze(...args) ?? Promise.resolve(), invalidateAnalysis: () => session.current?.invalidateAnalysis(), cancelAnalysis: () => session.current?.cancelAnalysis() };
  return <section className="query-lab evaluation-dashboard" aria-labelledby="evaluation-title"><header className="query-heading"><p className="page-eyebrow">Saved experiments / Research evaluation</p><h1 id="evaluation-title">Evaluation Dashboard</h1><p><strong>Synthetic development only - no empirical performance claims.</strong></p><p>Inspect persisted observations and validated R1 analysis. This page never starts model inference or changes saved experiments.</p></header>
    <div className="evaluation-browser"><section aria-labelledby="evaluation-history-heading"><h2 id="evaluation-history-heading">Saved experiments</h2><div className="query-actions"><button type="button" disabled={state.listPhase === "loading"} onClick={() => void session.current?.refresh()}>Refresh saved experiments</button></div>
      {state.listPhase === "loading" && <p role="status">Loading read-only experiment history...</p>}{state.listPhase === "error" && <p className="workspace-feedback" role="alert">{state.listError}</p>}{state.listPhase === "ready" && !state.jobs.length && <p>No saved experiments on this history page. Create synthetic runs in <a href="/experiments">Experiments</a>.</p>}
      <ul className="experiment-history">{state.jobs.map(job => <li key={job.id}><button type="button" aria-pressed={state.selectedId === job.id} aria-controls="selected-evaluation" disabled={state.listPhase === "loading"} onClick={() => { void session.current?.select(job.id); heading.current?.focus(); }}><strong>{present(job.configuration.split)}</strong> / {job.status}<br /><code>{job.id}</code><br />{job.observed_run_count}/{job.expected_run_count} observations saved<br /><span className="experiment-view-label">View evaluation</span></button></li>)}</ul>
      <div className="query-actions"><button type="button" disabled={state.offset === 0 || state.listPhase === "loading"} onClick={() => void session.current?.refresh(Math.max(0, state.offset-20))}>Newer</button><button type="button" disabled={state.jobs.length < 20 || state.listPhase === "loading" || state.offset >= 100000} onClick={() => void session.current?.refresh(state.offset+20)}>Older</button></div><p>History and observations are persisted. Dashboard selections and analysis settings are local to this page.</p>
    </section><section id="selected-evaluation" className="evaluation-selected" aria-labelledby="selected-evaluation-heading"><h2 id="selected-evaluation-heading" tabIndex={-1} ref={heading}>Selected experiment</h2>
      {state.detailPhase === "loading" ? <p role="status">Loading the saved evaluation snapshot...</p> : state.detailPhase === "error" ? <div role="alert"><p>{state.detailError}</p><button type="button" onClick={() => void session.current?.select(state.selectedId, true)}>Retry selected experiment</button></div> : state.detail ? <SelectedEvaluation key={state.detail.id} state={state} actions={actions} /> : <p>Select a saved experiment to inspect its evaluation.</p>}
    </section></div><p className="evaluation-section">Raw saved-result and Dev-freeze exports remain in <a href="/experiments">Experiments</a>. The research report above exports the validated dashboard analysis and provenance without duplicating raw observations.</p>
  </section>;
}
