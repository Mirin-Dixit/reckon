import { parseAnalysis, type AnalysisReport } from "./analysis-api";
import { parseJob, type Job, type Observation, type Results } from "./experiment-api";
import { downloadJson } from "./workspace-actions";

export interface AnalysisSelection {
  experiment_id: string; compare: string[]; lexical_proxy: boolean; threshold_only: boolean;
}
export const metricDefinitions = {
  end_to_end_coverage: "ANSWER observations / all selected questions (A/N). Failures and missing observations remain in N.",
  successful_execution_coverage: "ANSWER / successful ANSWER, ABSTAIN and CLARIFY observations (A/(A+B+C)). Failures and missing observations are excluded from this denominator.",
  selective_risk: "Incorrect answered questions / answered questions, only when every answer has a judgment. Zero answers or unknown judgments make risk undefined. Lexical proxies are not semantic judgments.",
  failure_rate: "Recorded execution failures / all selected questions. Failures are never abstentions.",
  missing_rate: "Missing observations / all selected questions. Missing observations are never correct answers.",
  judgment_completeness: "Answered questions with known judgments / answered questions. Undefined when there are no answers.",
  aurc: "R1 right-step area on end-to-end coverage. Partial domains are not extrapolated; operating points alone do not establish full AURC.",
};

/** No new statistics: capture the validated R1 response and its exact request. */
export function buildEvaluationReport(detail: Results, value: AnalysisReport, selection: AnalysisSelection, jobs: Job[]) {
  const analysis = parseAnalysis(value);
  const ids = [selection.experiment_id, ...selection.compare];
  const sources = [...new Set(analysis.rows.map(row => row.experiment_id))].sort();
  if (detail.id !== selection.experiment_id || new Set(ids).size !== ids.length ||
      JSON.stringify([...ids].sort()) !== JSON.stringify(sources) ||
      analysis.loss_basis !== (selection.lexical_proxy ? "synthetic_lexical_proxy" : "unknown") ||
      (selection.threshold_only && analysis.rows.some(row => row.policy !== "threshold"))) throw Error("Report selection mismatch");
  const records = sources.map(id => {
    const job = parseJob(id === detail.id ? (() => { const { observations, result, ...summary } = detail; void observations; void result; return summary; })() : jobs.find(job => job.id === id));
    const questions = job.configuration.question_ids;
    if (job.configuration.profile !== "p4-synthetic.v1" || job.configuration.split !== analysis.split || !Array.isArray(questions) || JSON.stringify([...questions].sort()) !== JSON.stringify([...analysis.question_ids].sort())) throw Error("Report source mismatch");
    // Export a projection, never arbitrary configuration, raw gold or environment fields.
    return { id: job.id, status: job.status, dataset_fingerprint: job.dataset_fingerprint,
      runtime_source_sha256: job.runtime_source_sha256,
      experiment_seed: typeof job.configuration.random_seed === "number" ? job.configuration.random_seed : null,
      source_record_sha256: [...new Set(analysis.rows.filter(row => row.experiment_id === id).map(row => row.source_record_sha256))].sort() };
  });
  return { schema_version: "ragbench.evaluation-report.v1", empirical_evaluation: false,
    notice: analysis.notice, request: { ...selection, compare: [...selection.compare].sort(), resamples: analysis.resamples, seed: analysis.seed },
    experiments: records, metric_definitions: metricDefinitions, analysis };
}

export function exportEvaluationReport(detail: Results, report: AnalysisReport, selection: AnalysisSelection, jobs: Job[], download = downloadJson): { message: string; failed: boolean } {
  try {
    download(buildEvaluationReport(detail, report, selection, jobs), `synthetic-evaluation-${detail.id}.json`);
    return { message: "Research report JSON prepared. Check your browser downloads.", failed: false };
  } catch {
    return { message: "Could not prepare the report. Refresh the saved experiment and rerun read-only analysis before exporting.", failed: true };
  }
}

export function observationCategory(row: Observation): string {
  return row.gold.unanswerable_category ?? row.gold.question_type ?? "Unspecified";
}
export function observationOutcome(row: Observation): string {
  if (row.error !== null || row.observed.execution_status !== "succeeded") return "EXECUTION_FAILURE";
  return ["ANSWER", "ABSTAIN", "CLARIFY"].includes(row.observed.decision ?? "") ? row.observed.decision! : "UNCLASSIFIED";
}
export function filterObservations(rows: Observation[], policy: string, category: string) {
  return rows.filter(row => (!policy || row.policy_name === policy) && (!category || observationCategory(row) === category));
}

/** Stored aggregate only. Invalid/unavailable values never become zero. */
export function savedRetrievalRecall(detail: Results): { value: number | null; note: string } {
  const quality = detail.result?.metrics.evidence_quality;
  if (typeof quality !== "object" || quality === null || !("gold_evidence_retrieval_recall" in quality)) return { value: null, note: "No saved retrieval-recall metric." };
  const metric = quality.gold_evidence_retrieval_recall;
  if (typeof metric !== "object" || metric === null || !("value" in metric) || !("status" in metric) || metric.status !== "available" || typeof metric.value !== "number" || !Number.isFinite(metric.value) || metric.value < 0 || metric.value > 1) return { value: null, note: "Saved retrieval recall is unavailable or invalid." };
  return { value: metric.value, note: "Saved gold-span retrieval recall across recorded policy observations, not independent question samples or semantic retrieval quality." };
}
