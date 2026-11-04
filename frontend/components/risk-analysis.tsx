"use client";

import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { downloadJson } from "../lib/workspace-actions";
import { analysisFailure, createAnalysisClient, createAnalysisTask, metrics, type AnalysisReport, type Interval } from "../lib/analysis-api";

const value = (n: number | null) => n === null ? "Undefined" : n.toFixed(3);
const names = { end_to_end_coverage: "End-to-end coverage A/N", successful_execution_coverage: "Successful-execution coverage A/(A+B+C)", selective_risk: "Selective lexical-proxy risk", failure_rate: "Execution failure rate E/N" };

export function IntervalText({ interval }: { interval: Interval }) {
  return <span>{interval.lower === null ? `Interval unavailable: ${interval.unavailable_reason}` : `95% paired percentile interval [${value(interval.lower)}, ${value(interval.upper)}]`}
    {` · ${interval.valid_replicates} valid / ${interval.undefined_replicates} undefined resamples`}{interval.degenerate && " · degenerate distribution; not certainty"}</span>;
}

export function RiskPlot({ report }: { report: AnalysisReport }) {
  const title = useId();
  const visible = report.rows.filter(row => row.selective_risk !== null);
  if (!visible.length) return <p>No defined risk points. Zero answers or unknown judgments cannot be plotted as zero risk.</p>;
  const x = (c: number) => 65 + c*440;
  const y = (r: number) => 230 - r*185;
  return <figure className="risk-plot" tabIndex={0} aria-label="Scrollable synthetic risk–coverage chart">
    <svg viewBox="0 0 560 295" role="img" aria-labelledby={title}>
      <title id={title}>Synthetic risk versus end-to-end coverage. Saved operating points; lines only for complete native threshold sweeps.</title>
      <path d="M65 35V230H515" fill="none" stroke="currentColor" />
      {[0,.25,.5,.75,1].map(t => <g key={t}><text x={x(t)} y="250" textAnchor="middle">{t}</text><text x="54" y={y(t)+4} textAnchor="end">{t}</text></g>)}
      <text x="285" y="280" textAnchor="middle">End-to-end coverage A/N</text>
      <text transform="translate(17 140) rotate(-90)" textAnchor="middle">Selective lexical-proxy risk</text>
      {report.curves.filter(c => c.area.undefined_reason === null).map(curve => {
        let previous = curve.points[0]?.coverage ?? 0;
        let path = "";
        for (const point of curve.points) {
          if (point.risk !== null) {
            path += `${path ? "L" : "M"}${x(previous)} ${y(point.risk)} L${x(point.coverage)} ${y(point.risk)} `;
          }
          previous = point.coverage;
        }
        return <path key={curve.id} d={path} stroke="var(--accent)" fill="none" strokeWidth="1.5" />;
      })}
      {visible.map(row => <circle key={row.id} cx={x(row.end_to_end_coverage.value!)} cy={y(row.selective_risk!)} r="5" fill="var(--accent)" stroke="var(--ink)"><title>{`${row.policy}: coverage ${value(row.end_to_end_coverage.value)}, risk ${value(row.selective_risk)}`}</title></circle>)}
    </svg>
    <figcaption>Saved operating points, not a fitted confidence curve. Exact values and uncertainty are in the tables below. No zero-risk point is invented.</figcaption>
  </figure>;
}

export function AnalysisView({ report, loading = false, error = "", cancelled = false, exportFeedback, onExport }: {
  report: AnalysisReport | null; loading?: boolean; error?: string; cancelled?: boolean;
  onExport?: () => void;
  exportFeedback?: { message: string; failed: boolean } | null;
}) {
  if (loading) return <p className="analysis-status" role="status">Analyzing saved synthetic observations…</p>;
  if (error) return <p className="analysis-error" id="analysis-error" role="alert">{error}</p>;
  if (cancelled) return <p role="status">Stopped waiting for analysis. Saved experiments are unchanged.</p>;
  if (!report) return <p>No analysis loaded. Analyze this saved experiment without running inference.</p>;
  return <div>
    <p><strong>{report.notice}</strong></p>
    <p>{report.matched_questions} matched questions; {report.resampling_units} resampling units ({report.grouping}). {report.resamples} paired resamples; seed {report.seed}. Retrieval: {report.retrieval_method}.</p>
    <p>{report.loss_basis === "unknown" ? "Answer judgments are unknown. Risk remains undefined." : "Risk uses a synthetic normalized lexical exact-match proxy, not verified semantic correctness."} Failures remain failures; ABSTAIN and CLARIFY are uncovered.</p>
    <RiskPlot report={report} />
    <div className="ledger-scroll" role="region" aria-label="Matched-policy operating points" tabIndex={0}><table className="evidence-table"><caption>Matched-policy operating points</caption><thead><tr><th scope="col">Policy / experiment</th><th scope="col">End-to-end coverage A/N</th><th scope="col">Successful-execution coverage A/(A+B+C)</th><th scope="col">Selective risk</th><th scope="col">Failures E/N</th><th scope="col">Judgment completeness</th></tr></thead>
      <tbody>{report.rows.map(row => <tr key={row.id}><th scope="row">{row.policy}<br /><code>{row.experiment_id}</code>{row.threshold !== null && <p>{row.direction} τ={row.threshold}</p>}</th>
        <td>{value(row.end_to_end_coverage.value)} ({row.end_to_end_coverage.numerator}/{row.end_to_end_coverage.denominator})</td>
        <td>{value(row.successful_execution_coverage.value)} ({row.successful_execution_coverage.numerator}/{row.successful_execution_coverage.denominator})</td>
        <td>{value(row.selective_risk)}{row.undefined_reason && <p>{row.undefined_reason}</p>}{row.risk_bounds && <p>Identification bounds [{row.risk_bounds.map(value).join(", ")}]; not a confidence interval.</p>}</td>
        <td>{value(row.failure_rate.value)} ({row.failure_rate.numerator}/{row.failure_rate.denominator})</td><td>{value(row.judgment_completeness.value)} ({row.judgment_completeness.numerator}/{row.judgment_completeness.denominator})</td></tr>)}</tbody></table></div>
    <details><summary>Operating-point uncertainty</summary>{report.rows.map(row => <div key={row.id}><h5>{row.policy} / <code>{row.experiment_id}</code></h5><ul>{metrics.map(metric => <li key={metric}>{names[metric]}: <IntervalText interval={row.uncertainty[metric]} /></li>)}</ul></div>)}</details>
    <h5>Paired policy differences</h5>
    {report.comparisons.length ? <div className="ledger-scroll" role="region" aria-label="Paired policy differences" tabIndex={0}><table className="evidence-table"><caption>Left minus right on matched questions, never pooled observations</caption><thead><tr><th scope="col">Pair</th><th scope="col">Metric</th><th scope="col">Difference</th><th scope="col">Uncertainty</th></tr></thead><tbody>{report.comparisons.flatMap((pair, i) => metrics.map(metric => <tr key={`${i}:${metric}`}><th scope="row"><code>{pair.left}</code><br />minus <code>{pair.right}</code></th><td>{names[metric]}</td><td>{value(pair.uncertainty[metric].estimate)}</td><td><IntervalText interval={pair.uncertainty[metric]} /></td></tr>))}</tbody></table></div> : <p>Only one policy configuration is available. No paired comparison.</p>}
    <h5>Right-step AURC / coverage domain</h5>
    {report.curves.length ? report.curves.map(curve => <div key={curve.id}><p>Threshold series <code>{curve.id}</code>: {curve.area.full_aurc !== null ? `Full AURC ${value(curve.area.full_aurc)}` : curve.area.partial_aurc !== null ? `Partial area ${value(curve.area.partial_aurc)}` : `Area undefined: ${curve.area.undefined_reason}`}. Coverage domain: {curve.area.coverage_bounds ? `[${curve.area.coverage_bounds.map(value).join(", ")}]` : "unavailable"}.</p><p><IntervalText interval={curve.uncertainty} /></p></div>) : <p>No native threshold trials available. An operating point is not an AURC curve.</p>}
    {report.curve_comparisons.map(pair => <p key={`${pair.left}:${pair.right}`}>AURC difference {pair.left} minus {pair.right}: {value(pair.uncertainty.estimate)}. <IntervalText interval={pair.uncertainty} /></p>)}
    <details><summary>Methodology, provenance and limitations</summary><p>Compatibility fingerprint: <code>{report.provenance_sha256}</code></p><ul>{report.limitations.map(text => <li key={text}>{text}</li>)}</ul><p>Unknown judgments and incomplete cohorts cannot become zero-risk results. Thresholds are uncalibrated ranking scores and are never compared across score families.</p></details>
    <button type="button" onClick={onExport} disabled={!onExport}>Export analysis JSON</button>
    {exportFeedback && <p className="workspace-feedback" role={exportFeedback.failed ? "alert" : "status"}>{exportFeedback.message}</p>}
  </div>;
}

export function AnalysisAction({ loading, error, onCancel }: {
  loading: boolean; error: string; onCancel: () => void;
}) {
  return <div className="analysis-action">
    <h4>Run analysis</h4>
    <p className="analysis-help">Read saved observations without starting inference.</p>
    <div className="query-actions">
      <button className="check-button" type="submit" disabled={loading} aria-busy={loading} aria-describedby={error ? "analysis-error" : undefined}>{loading ? "Analyzing saved observations…" : "Analyze saved observations"}</button>
      {loading && <button type="button" onClick={onCancel}>Cancel analysis</button>}
    </div>
  </div>;
}

export function RiskAnalysis({ experimentId }: { experimentId: string }) {
  const [compare, setCompare] = useState("");
  const [exportFeedback, setExportFeedback] = useState<{ message: string; failed: boolean } | null>(null);
  const [proxy, setProxy] = useState(true);
  const [thresholdOnly, setThresholdOnly] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [error, setError] = useState("");
  const task = useRef(createAnalysisTask());
  useEffect(() => { const pending = task.current; return () => pending.cancel(); }, []);
  async function submit(event: FormEvent) {
    event.preventDefault();
    const controller = task.current.begin();
    setLoading(true); setCancelled(false); setError(""); setReport(null); setExportFeedback(null);
    try {
      const result = await createAnalysisClient(process.env.NEXT_PUBLIC_RAGBENCH_API_BASE_URL).analyze(experimentId, compare.split(",").map(s => s.trim()).filter(Boolean), proxy, controller.signal, thresholdOnly);
      if (task.current.accepts(controller)) setReport(result);
    } catch (e) { if (task.current.accepts(controller)) setError(analysisFailure(e)); }
    finally { if (task.current.accepts(controller)) setLoading(false); }
  }
  function exportJson() {
    if (!report) return;
    try { downloadJson(report, `synthetic-analysis-${experimentId}.json`); setExportFeedback({ message: "Analysis JSON export prepared. Check your browser downloads.", failed: false }); }
    catch { setExportFeedback({ message: "Could not prepare analysis export. Please try again.", failed: true }); }
  }
  return <section className="risk-analysis" aria-labelledby="risk-analysis-heading">
    <header className="analysis-heading">
      <div><h3 id="risk-analysis-heading">Risk–Coverage analysis</h3><p>Compare saved observations, coverage and selective risk.</p></div>
      <span className="analysis-label">Synthetic only</span>
    </header>
    <p className="analysis-scope">Synthetic development only. Read-only saved-results analysis; no model calls, threshold tuning, freeze changes or held-out evaluation.</p>
    <form className="analysis-form" onSubmit={submit}>
      <fieldset className="analysis-selection" disabled={loading}>
        <legend>Experiment selection</legend>
        <label htmlFor="analysis-compare">Additional compatible saved experiment IDs <span className="analysis-optional">(optional)</span></label>
        <input id="analysis-compare" type="text" value={compare} maxLength={258} disabled={loading} onChange={e => setCompare(e.target.value)} aria-describedby="analysis-help" placeholder="Paste experiment IDs, separated by commas" autoComplete="off" spellCheck={false} />
        <p id="analysis-help" className="analysis-help">Leave empty to analyze this experiment only. Add up to seven compatible experiment IDs, separated by commas. Questions, split, runtime, retrieval and generation settings must match.</p>
      </fieldset>
      <fieldset className="analysis-settings" disabled={loading}>
        <legend>Analysis settings</legend>
        <label className="analysis-option" htmlFor="analysis-proxy">
          <input id="analysis-proxy" type="checkbox" checked={proxy} disabled={loading} onChange={e => setProxy(e.target.checked)} aria-describedby="analysis-proxy-help" />
          <span><span className="analysis-option-title">Use synthetic lexical proxy judgments</span><span id="analysis-proxy-help" className="analysis-help">Normalized lexical exact match, not semantic correctness. Uncheck to keep answer judgments unknown.</span></span>
        </label>
        <label className="analysis-option" htmlFor="analysis-threshold">
          <input id="analysis-threshold" type="checkbox" checked={thresholdOnly} disabled={loading} onChange={e => setThresholdOnly(e.target.checked)} aria-describedby="analysis-threshold-help" />
          <span><span className="analysis-option-title">Threshold trials only</span><span id="analysis-threshold-help" className="analysis-help">Explicitly exclude repeated control policies for saved sweeps. Trials must span every score boundary for AURC.</span></span>
        </label>
      </fieldset>
      <AnalysisAction loading={loading} error={error} onCancel={() => { task.current.cancel(); setLoading(false); setCancelled(true); }} />
    </form>
    <section className="analysis-results" aria-labelledby="analysis-results-heading">
      <h4 id="analysis-results-heading">Analysis results</h4>
      <AnalysisView report={report} loading={loading} error={error} cancelled={cancelled} exportFeedback={exportFeedback} onExport={exportJson} />
    </section>
  </section>;
}
