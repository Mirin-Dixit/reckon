import schema from "./analysis-schema.json";
import { ApiClientError, createJsonRequest } from "./api";

export type Metric = "end_to_end_coverage" | "successful_execution_coverage" | "selective_risk" | "failure_rate";
export const metrics: Metric[] = ["end_to_end_coverage", "successful_execution_coverage", "selective_risk", "failure_rate"];
export interface Interval {
  estimate: number | null; lower: number | null; upper: number | null;
  valid_replicates: number; undefined_replicates: number; degenerate: boolean;
  unavailable_reason: string | null;
}
interface Fraction { numerator: number; denominator: number; value: number | null }
export interface AnalysisRow {
  id: string; policy: "always_answer" | "threshold" | "prompt_abstention";
  experiment_id: string; source_record_sha256: string;
  threshold: number | null; direction: "at_least" | "at_most" | null;
  end_to_end_coverage: Fraction; successful_execution_coverage: Fraction;
  failure_rate: Fraction; missing_rate: Fraction; judgment_completeness: Fraction;
  selective_risk: number | null; risk_bounds: [number, number] | null;
  undefined_reason: string | null; uncertainty: Record<Metric, Interval>;
}
export interface AnalysisCurve {
  id: string; points: { row_id: string; coverage: number; risk: number | null }[];
  area: { schema_version: "ragbench.risk-coverage.v1"; axis: "end_to_end_coverage";
    rule: "right_step"; full_aurc: number | null; partial_aurc: number | null;
    coverage_bounds: [number, number] | null; undefined_reason: string | null };
  uncertainty: Interval;
}
export interface AnalysisReport {
  schema_version: "ragbench.matched-analysis.v1"; empirical_evaluation: false;
  notice: "Synthetic development only; lexical proxy is not semantic correctness.";
  split: "train" | "dev"; retrieval_method: "bm25" | "dense" | "hybrid";
  provenance_sha256: string; question_ids: string[]; matched_questions: number;
  resampling_units: number; cluster_sizes: number[];
  grouping: "question" | "declared_question_family"; family_map_sha256: string | null;
  seed: number; resamples: number; interval_method: "paired_percentile_95";
  loss_basis: "unknown" | "synthetic_lexical_proxy";
  rows: AnalysisRow[];
  comparisons: { left: string; right: string; difference: "left_minus_right";
    uncertainty: Record<Metric, Interval>; risk_unavailable_reason: string | null }[];
  curves: AnalysisCurve[];
  curve_comparisons: { left: string; right: string; difference: "left_minus_right"; uncertainty: Interval }[];
  limitations: string[];
}

type Schema = { $ref?: string; $defs?: Record<string, Schema>; anyOf?: Schema[];
  type?: string; const?: unknown; enum?: unknown[]; properties?: Record<string, Schema>;
  required?: string[]; additionalProperties?: boolean | Schema; propertyNames?: Schema;
  items?: Schema; prefixItems?: Schema[]; minItems?: number; maxItems?: number;
  minimum?: number; maximum?: number; minLength?: number };
const object = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
function matches(value: unknown, s: Schema, depth = 0): boolean {
  if (!s || depth > 32) return false;
  if (s.$ref) return matches(value, (schema.$defs as Record<string, Schema>)[s.$ref.split("/").at(-1)!], depth + 1);
  if (s.anyOf) return s.anyOf.some(child => matches(value, child, depth + 1));
  if ("const" in s && value !== s.const) return false;
  if (s.enum && !s.enum.includes(value)) return false;
  switch (s.type) {
    case "null": return value === null;
    case "boolean": return typeof value === "boolean";
    case "string": return typeof value === "string" && value.length >= (s.minLength ?? 0);
    case "integer": case "number": return typeof value === "number" && Number.isFinite(value) &&
      (s.type !== "integer" || Number.isSafeInteger(value)) && value >= (s.minimum ?? -Infinity) && value <= (s.maximum ?? Infinity);
    case "array": return Array.isArray(value) && value.length >= (s.minItems ?? 0) && value.length <= (s.maxItems ?? Infinity) &&
      value.every((v, i) => matches(v, s.prefixItems?.[i] ?? s.items!, depth + 1));
    case "object": return object(value) && (s.required ?? []).every(key => Object.hasOwn(value, key)) && Object.entries(value).every(([key, v]) =>
      (!s.propertyNames || matches(key, s.propertyNames, depth + 1)) && (s.properties && Object.hasOwn(s.properties, key)
        ? matches(v, s.properties[key], depth + 1) : s.additionalProperties === false ? false
          : typeof s.additionalProperties === "object" ? matches(v, s.additionalProperties, depth + 1) : true));
    default: return true;
  }
}
const unit = (n: number | null) => n === null || (Number.isFinite(n) && n >= 0 && n <= 1);
export function parseAnalysis(value: unknown): AnalysisReport {
  if (!matches(value, schema)) throw new ApiClientError("malformed");
  const report = value as AnalysisReport;
  const bad = () => { throw new ApiClientError("malformed"); };
  const n = report.matched_questions;
  if (n < 1 || n > 10 || report.question_ids.length !== n || new Set(report.question_ids).size !== n ||
      report.resamples < 2 || report.resamples > 5000 || report.resampling_units < 1 || report.resampling_units > n ||
      report.cluster_sizes.length !== report.resampling_units || report.cluster_sizes.some(s => s < 1) ||
      report.cluster_sizes.reduce((a,b) => a+b, 0) !== n || report.rows.length < 1 || report.rows.length > 24) bad();
  const ids = new Set(report.rows.map(r => r.id));
  if (ids.size !== report.rows.length) bad();
  const interval = (i: Interval) => {
    if (i.valid_replicates < 0 || i.undefined_replicates < 0 || i.valid_replicates + i.undefined_replicates !== report.resamples ||
        (i.estimate !== null && Math.abs(i.estimate) > 1) ||
        (i.lower === null) !== (i.upper === null) ||
        (i.lower !== null && (i.upper === null || i.lower > i.upper || i.lower < -1 || i.upper > 1)) ||
        (i.unavailable_reason !== null && i.lower !== null) ||
        (i.unavailable_reason === null && (i.estimate === null || i.lower === null || i.undefined_replicates > 0 || report.resampling_units < 2))) bad();
  };
  const intervals = (v: Record<Metric, Interval>) => {
    if (Object.keys(v).length !== metrics.length || metrics.some(m => !Object.hasOwn(v, m))) bad();
    metrics.forEach(m => interval(v[m]));
  };
  for (const row of report.rows) {
    for (const [key, f] of Object.entries({ end: row.end_to_end_coverage, success: row.successful_execution_coverage,
      failure: row.failure_rate, missing: row.missing_rate, judgment: row.judgment_completeness })) {
      if (f.numerator < 0 || f.denominator < f.numerator || !unit(f.value) ||
          f.value !== (f.denominator ? f.numerator / f.denominator : null) ||
          (["end", "failure", "missing"].includes(key) && f.denominator !== n)) bad();
    }
    if (!unit(row.selective_risk) || (row.risk_bounds !== null && (row.risk_bounds.length !== 2 || !row.risk_bounds.every(unit) || row.risk_bounds[0] > row.risk_bounds[1])) ||
        (row.selective_risk !== null && (row.end_to_end_coverage.numerator === 0 || row.judgment_completeness.value !== 1)) ||
        (report.loss_basis === "unknown" && row.selective_risk !== null)) bad();
    if (row.missing_rate.numerator !== 0 || row.successful_execution_coverage.denominator !== n - row.failure_rate.numerator ||
        row.successful_execution_coverage.numerator !== row.end_to_end_coverage.numerator ||
        row.judgment_completeness.denominator !== row.end_to_end_coverage.numerator) bad();
    intervals(row.uncertainty);
    for (const metric of metrics) {
      const expected = metric === "selective_risk" ? row.selective_risk : row[metric].value;
      const i = row.uncertainty[metric];
      if (i.estimate !== expected || !unit(i.lower) || !unit(i.upper)) bad();
    }
  }
  const pairs = new Set<string>();
  for (const c of report.comparisons) {
    if (!ids.has(c.left) || !ids.has(c.right) || c.left === c.right) bad();
    const key = [c.left, c.right].sort().join("|");
    if (pairs.has(key)) bad(); pairs.add(key);
    intervals(c.uncertainty);
    const a = report.rows.find(r => r.id === c.left)!, b = report.rows.find(r => r.id === c.right)!;
    for (const metric of metrics) {
      const x = a.uncertainty[metric].estimate, y = b.uncertainty[metric].estimate;
      const expected = x === null || y === null || (metric === "selective_risk" && a.end_to_end_coverage.value !== b.end_to_end_coverage.value) ? null : x-y;
      if (c.uncertainty[metric].estimate !== expected) bad();
    }
  }
  if (pairs.size !== report.rows.length * (report.rows.length - 1) / 2) bad();
  const curves = new Set(report.curves.map(c => c.id));
  if (curves.size !== report.curves.length) bad();
  for (const c of report.curves) {
    if (!unit(c.area.full_aurc) || !unit(c.area.partial_aurc) || c.points.some(p => !ids.has(p.row_id) || !unit(p.coverage) || !unit(p.risk)) ||
        (c.area.coverage_bounds !== null && (!c.area.coverage_bounds.every(unit) || c.area.coverage_bounds[0] > c.area.coverage_bounds[1])) ||
        (c.area.full_aurc !== null && (c.area.coverage_bounds?.[0] !== 0 || c.area.coverage_bounds?.[1] !== 1 || c.area.undefined_reason !== null)) ||
        (c.area.undefined_reason !== null && (c.area.full_aurc !== null || c.area.partial_aurc !== null))) bad();
    if (c.points.length < 1 || new Set(c.points.map(p => p.row_id)).size !== c.points.length) bad();
    for (const [index, point] of c.points.entries()) {
      const row = report.rows.find(r => r.id === point.row_id)!;
      if (row.policy !== "threshold" || row.end_to_end_coverage.value !== point.coverage || row.selective_risk !== point.risk ||
          (index > 0 && point.coverage < c.points[index-1].coverage)) bad();
    }
    const area = c.area.full_aurc ?? c.area.partial_aurc;
    if (c.uncertainty.estimate !== area || (c.area.full_aurc !== null && c.area.partial_aurc !== null)) bad();
    if (area !== null) {
      const low = c.points[0].coverage, high = c.points.at(-1)!.coverage;
      let calculated = 0;
      for (let i = 1; i < c.points.length; i++) {
        const width = c.points[i].coverage - c.points[i-1].coverage;
        if (width > 0) { if (c.points[i].risk === null) bad(); calculated += width * c.points[i].risk!; }
      }
      if (high <= low || c.area.coverage_bounds?.[0] !== low || c.area.coverage_bounds?.[1] !== high || Math.abs(area-calculated) > 1e-12) bad();
    }
    interval(c.uncertainty);
  }
  for (const c of report.curve_comparisons) { if (!curves.has(c.left) || !curves.has(c.right)) bad(); interval(c.uncertainty); }
  return report;
}

const uuid = (id: string) => {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) throw new ApiClientError("configuration");
  return id;
};
export function createAnalysisClient(origin?: string, options: { fetch?: typeof fetch; timeoutMs?: number } = {}) {
  return { analyze: async (id: string, compare: string[], lexicalProxy: boolean, signal?: AbortSignal, thresholdOnly = false) => {
    if (compare.length > 7 || new Set([id,...compare]).size !== compare.length + 1) throw new ApiClientError("configuration");
    const path = `/api/v1/experiments/${uuid(id)}/analysis?resamples=2000&seed=0&lexical_proxy=${lexicalProxy}${thresholdOnly ? "&threshold_only=true" : ""}${compare.map(c => `&compare=${uuid(c)}`).join("")}` as const;
    const report = await createJsonRequest(path, parseAnalysis, origin, { ...options, method: "GET", timeoutMs: options.timeoutMs ?? 20000 })(signal);
    const sources = new Set(report.rows.map(r => r.experiment_id));
    if (sources.size !== compare.length + 1 || [id,...compare].some(i => !sources.has(i)) || report.seed !== 0 || report.resamples !== 2000 ||
        report.loss_basis !== (lexicalProxy ? "synthetic_lexical_proxy" : "unknown") ||
        (thresholdOnly && report.rows.some(r => r.policy !== "threshold"))) throw new ApiClientError("malformed");
    return report;
  } };
}
export function analysisFailure(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.failure.kind === "cancelled") return "Stopped waiting for analysis. Saved experiments are unchanged.";
    if (error.failure.kind === "timeout") return "Analysis timed out. Saved experiments are unchanged; try a smaller selection.";
    if (error.failure.kind === "malformed") return "Invalid analysis response. No statistical result is confirmed.";
    if (error.failure.kind === "configuration") return "Use up to seven distinct additional experiment IDs and a local backend address.";
    if (error.failure.httpStatus === 422) return "Analysis requires complete, matched synthetic questions and compatible configurations. Duplicate policy configurations cannot be pooled.";
    if (error.failure.httpStatus === 404) return "A selected saved experiment was not found.";
  }
  return "Analysis is unavailable. Check the local backend and saved experiment storage.";
}

/** Invalidate pending updates on cancellation, reselection or unmount. */
export function createAnalysisTask() {
  let current: AbortController | null = null;
  return {
    begin() { current?.abort(); current = new AbortController(); return current; },
    accepts(controller: AbortController) { return current === controller && !controller.signal.aborted; },
    cancel() { current?.abort(); current = null; },
  };
}
