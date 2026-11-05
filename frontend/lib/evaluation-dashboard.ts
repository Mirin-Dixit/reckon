import { ApiClientError, createJsonRequest } from "./api";
import { createAnalysisClient, analysisFailure, type AnalysisReport } from "./analysis-api";
import { parseJob, parseResults, type Job, type Results } from "./experiment-api";

const object = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const uuid = (id: string) => {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) throw new ApiClientError("configuration");
  return id;
};
export function createEvaluationClient(origin?: string, options: { fetch?: typeof fetch } = {}) {
  return {
    list: async (offset: number, signal?: AbortSignal): Promise<Job[]> => {
      if (!Number.isSafeInteger(offset) || offset < 0 || offset > 100000) throw new ApiClientError("configuration");
      return createJsonRequest(`/api/v1/analysis/experiments?limit=20&offset=${offset}`, v => {
        if (!object(v) || Object.keys(v).length !== 1 || !Array.isArray(v.jobs) || v.jobs.length > 20) throw new ApiClientError("malformed");
        const jobs = v.jobs.map(parseJob);
        if (new Set(jobs.map(j => j.id)).size !== jobs.length) throw new ApiClientError("malformed");
        return jobs;
      }, origin, { ...options, method: "GET", timeoutMs: 10000 })(signal);
    },
    results: async (id: string, signal?: AbortSignal): Promise<Results> => {
      const result = await createJsonRequest(`/api/v1/analysis/experiments/${uuid(id)}`, parseResults, origin, { ...options, method: "GET", timeoutMs: 10000 })(signal);
      if (result.id !== id) throw new ApiClientError("malformed");
      return result;
    },
    analyze: createAnalysisClient(origin, options).analyze,
  };
}
export type EvaluationClient = ReturnType<typeof createEvaluationClient>;

export function evaluationFailure(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.failure.kind === "malformed") return "Saved evaluation data is malformed. No result is confirmed.";
    if (error.failure.kind === "timeout") return "Loading saved evaluation data timed out. Retry without starting a new experiment.";
    if (error.failure.httpStatus === 404) return "The selected saved experiment was not found. Refresh the list.";
    if (error.failure.httpStatus === 422) return "This saved record cannot be used as a synthetic evaluation.";
  }
  return "Cannot load read-only evaluation data. Check the local backend, its version and storage configuration.";
}

/** Configuration equality only; never a substitute for R1 provenance validation. */
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (object(value)) return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
  return JSON.stringify(value) ?? "undefined";
}
export function comparisonBlocker(selected: Job, candidate: Job, thresholdOnly: boolean): string | null {
  if (selected.id === candidate.id) return "This is the selected experiment.";
  if (![selected, candidate].every(j => ["done", "partial", "failed"].includes(j.status) && j.observed_run_count === j.expected_run_count)) return "Incomplete saved observations.";
  const a = selected.configuration, b = candidate.configuration;
  if (a.profile !== "p4-synthetic.v1" || b.profile !== a.profile) return "Unsupported evaluation profile.";
  if (a.split !== b.split) return "Different dataset split.";
  if (!Array.isArray(a.question_ids) || !Array.isArray(b.question_ids) || canonical([...a.question_ids].sort()) !== canonical([...b.question_ids].sort())) return "Different or unavailable question cohort.";
  if (canonical(selected.dataset_fingerprint) !== canonical(candidate.dataset_fingerprint)) return "Different dataset fingerprints.";
  if (selected.runtime_source_sha256 !== candidate.runtime_source_sha256) return "Different runtime provenance.";
  if (!object(a.retrieval) || !object(b.retrieval) || canonical(a.retrieval) !== canonical(b.retrieval)) return "Different or unavailable retrieval settings.";
  if (a.random_seed !== b.random_seed || a.random_seed === undefined) return "Different or unavailable experiment seed.";
  const policies = (config: Record<string, unknown>) => Array.isArray(config.policies) ? config.policies.filter(object).filter(p => !thresholdOnly || p.name === "threshold") : [];
  const x = policies(a), y = policies(b);
  if (!x.length || !y.length) return "Requested policy settings are unavailable.";
  const repeats = (left: Record<string, unknown>[], right: Record<string, unknown>[]) => left.some(p => right.some(q => canonical(p) === canonical(q)));
  if (repeats(x, y)) {
    const thresholdsA = x.filter(p => p.name === "threshold"), thresholdsB = y.filter(p => p.name === "threshold");
    if (repeats(thresholdsA, thresholdsB)) return "These runs repeat the same threshold policy settings. Threshold trials only will not make this pair eligible. Choose a saved run with different threshold settings; repeated runs are not independent samples.";
    if (!thresholdOnly && thresholdsA.length && thresholdsB.length) return "These runs repeat control policies. Enable Threshold trials only above to exclude those controls and compare their different saved threshold settings. Full R1 compatibility validation still applies.";
    return "These runs repeat policy settings and do not both contain distinct threshold trials. Choose a saved run with different policy settings; changing the analysis setting cannot resolve this duplicate.";
  }
  return null; // Metadata match only: gold/evidence/generation compatibility is checked by R1.
}

export interface EvaluationState {
  jobs: Job[]; offset: number; listPhase: "loading" | "ready" | "error"; listError: string;
  selectedId: string; detail: Results | null; detailPhase: "idle" | "loading" | "ready" | "error"; detailError: string;
  analysis: AnalysisReport | null; analysisPhase: "idle" | "loading" | "ready" | "error" | "cancelled"; analysisError: string;
}
export const initialEvaluationState: EvaluationState = { jobs: [], offset: 0, listPhase: "loading", listError: "", selectedId: "", detail: null, detailPhase: "idle", detailError: "", analysis: null, analysisPhase: "idle", analysisError: "" };
export function canAnalyze(detail: Results): boolean {
  return ["done", "partial", "failed"].includes(detail.status) && detail.result !== null && !detail.result.stopped_early && detail.observed_run_count === detail.expected_run_count;
}

/** One request per channel; superseded requests cannot publish after selection changes. */
export function evaluationSession(api: EvaluationClient, publish: (state: EvaluationState) => void) {
  let state = { ...initialEvaluationState };
  let disposed = false;
  let list: AbortController | null = null, detail: AbortController | null = null, analysis: AbortController | null = null;
  const update = (value: Partial<EvaluationState>) => { state = { ...state, ...value }; if (!disposed) publish(state); };
  const clearAnalysis = () => { analysis?.abort(); analysis = null; update({ analysis: null, analysisPhase: "idle", analysisError: "" }); };
  const select = async (id: string, force = false) => {
    if (disposed || (!force && state.selectedId === id && (detail || state.detail))) return;
    if (!state.jobs.some(j => j.id === id)) return;
    detail?.abort(); clearAnalysis();
    const controller = new AbortController(); detail = controller;
    update({ selectedId: id, detail: null, detailPhase: "loading", detailError: "" });
    try {
      const result = await api.results(id, controller.signal);
      if (!disposed && detail === controller && !controller.signal.aborted) update({ detail: result, detailPhase: "ready" });
    } catch (e) {
      if (!disposed && detail === controller && !controller.signal.aborted) update({ detailPhase: "error", detailError: evaluationFailure(e) });
    } finally { if (detail === controller) detail = null; }
  };
  return {
    async refresh(offset = state.offset) {
      if (disposed || (list && state.offset === offset)) return;
      list?.abort(); detail?.abort(); detail = null; clearAnalysis();
      const controller = new AbortController(); list = controller;
      const changed = offset !== state.offset;
      update({ offset, listPhase: "loading", listError: "", detailPhase: state.detail ? "ready" : "idle", ...(changed ? { jobs: [], selectedId: "", detail: null, detailPhase: "idle" as const } : {}) });
      try {
        const jobs = await api.list(offset, controller.signal);
        if (disposed || list !== controller || controller.signal.aborted) return;
        update({ jobs, listPhase: "ready" });
        const id = jobs.some(j => j.id === state.selectedId) ? state.selectedId : jobs[0]?.id;
        if (id) await select(id, true);
        else update({ selectedId: "", detail: null, detailPhase: "idle" });
      } catch (e) {
        if (!disposed && list === controller && !controller.signal.aborted) update({ listPhase: "error", listError: evaluationFailure(e) });
      } finally { if (list === controller) list = null; }
    },
    select,
    invalidateAnalysis: clearAnalysis,
    async analyze(compare: string[], proxy: boolean, thresholdOnly: boolean) {
      if (disposed || analysis || state.listPhase !== "ready" || state.detailPhase !== "ready" || !state.detail || !canAnalyze(state.detail)) return;
      const controller = new AbortController(); analysis = controller;
      update({ analysis: null, analysisPhase: "loading", analysisError: "" });
      try {
        const report = await api.analyze(state.selectedId, compare, proxy, controller.signal, thresholdOnly);
        if (!disposed && analysis === controller && !controller.signal.aborted) update({ analysis: report, analysisPhase: "ready" });
      } catch (e) {
        if (!disposed && analysis === controller && !controller.signal.aborted) update({ analysisPhase: "error", analysisError: analysisFailure(e) });
      } finally { if (analysis === controller) analysis = null; }
    },
    cancelAnalysis() { analysis?.abort(); analysis = null; update({ analysis: null, analysisPhase: "cancelled", analysisError: "" }); },
    dispose() { disposed = true; list?.abort(); detail?.abort(); analysis?.abort(); },
  };
}
