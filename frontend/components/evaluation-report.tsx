"use client";

import { useState } from "react";
import type { AnalysisReport } from "../lib/analysis-api";
import type { Job, Results } from "../lib/experiment-api";
import { exportEvaluationReport, metricDefinitions, type AnalysisSelection } from "../lib/evaluation-report";

export function EvaluationReport({ detail, report, selection, jobs }: { detail: Results; report: AnalysisReport; selection: AnalysisSelection; jobs: Job[] }) {
  const [feedback, setFeedback] = useState<{ message: string; failed: boolean } | null>(null);
  function exportReport() {
    setFeedback(exportEvaluationReport(detail, report, selection, jobs));
  }
  return <section className="evaluation-section" aria-labelledby="evaluation-report-heading"><h2 id="evaluation-report-heading">Research report</h2>
    <p>Selected experiment <code>{detail.id}</code>. {report.rows.length} policy configurations across {new Set(report.rows.map(row => row.experiment_id)).size} saved experiments; {report.matched_questions} matched questions. Judgment basis: <strong>{report.loss_basis}</strong>.</p>
    <p>This export packages the validated R1 response, source fingerprints, exact analysis request, experiment seeds and metric definitions. It contains no reference answers, gold evidence or environment variables. It does not create a new experiment or certify semantic correctness.</p>
    <button type="button" onClick={exportReport}>Export research report JSON</button>
    {feedback && <p className="workspace-feedback" role={feedback.failed ? "alert" : "status"}>{feedback.message}</p>}
    <details><summary>Metric definitions and interpretation</summary><dl className="evaluation-definitions">{Object.entries(metricDefinitions).map(([name, definition]) => <div key={name}><dt>{name.replaceAll("_", " ")}</dt><dd>{definition}</dd></div>)}</dl><p>Percentile intervals use jointly resampled matched questions or declared families. Small or degenerate samples do not establish certainty. Identification bounds for unknown judgments are not confidence intervals.</p></details>
  </section>;
}
