import schemas from "./experiment-schema.json";
import { ApiClientError, createJsonRequest } from "./api";
import { matches } from "./query-api";

export const notice = "Synthetic fixture — development only; no empirical claims.";
export interface Job {
  schema_version: "ragbench.experiment-job.v1"; id: string;
  status: "queued" | "running" | "done" | "partial" | "failed";
  notice: typeof notice; empirical_evaluation: false;
  created_at: string; updated_at: string; expected_run_count: number; observed_run_count: number;
  configuration: Record<string, unknown>; dataset_fingerprint: Record<string, string>;
  runtime_source_sha256: string; error: string | null;
}
interface Observation { question_id: string; policy_name: string; error: unknown;
  observed: { decision: string | null; answer: string | null; clarification_question: string | null; execution_status: string } }
export interface Results extends Job {
  observations: Observation[];
  result: { experiment_id: string; runs: Observation[]; dataset_fingerprint: Record<string, string>;
    selected_question_ids: string[]; benchmark_split: "train" | "dev" | "test";
    random_seed: number | null; stopped_early: boolean;
    retrieval_configuration: Record<string, unknown>; policy_configurations: Record<string, unknown>[];
    generation_configuration: Record<string, unknown>; environment_metadata: Record<string, unknown>;
    software_metadata: Record<string, unknown>; metrics: Record<string, unknown> } | null;
}
export interface Freeze {
  schema_version: "ragbench.dev-freeze.v1";
  job_id: string;
  sha256: string;
  empirical_evaluation: false;
  notice: typeof notice;
  created_at: string;
  configuration: Record<string, unknown>;
  dataset_fingerprint: Record<string, string>;
  software_metadata: Record<string, unknown>;
  generation_configuration: Record<string, unknown>;
}

function schema<T>(name: keyof typeof schemas, value: unknown): T {
  const definition = schemas[name];
  if (!matches(value, definition, definition.$defs)) throw new ApiClientError("malformed");
  return value as T;
}
const uuid = (id: string) => {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) throw new ApiClientError("configuration");
  return id;
};
export function parseJob(value: unknown): Job {
  const job = schema<Job>("JobSummary", value);
  uuid(job.id);
  if (job.observed_run_count > job.expected_run_count ||
      (job.status === "done" && (job.observed_run_count !== job.expected_run_count || job.error !== null))) throw new ApiClientError("malformed");
  return job;
}
export function parseResults(value: unknown): Results {
  const result = schema<Results>("JobResults", value);
  const { observations, result: record, ...summary } = result;
  parseJob(summary);
  if (observations.length !== result.observed_run_count ||
      (record !== null && (record.experiment_id !== result.id || record.runs.length !== observations.length)) ||
      (result.status === "done" && (record === null || observations.some(o => o.error !== null || o.observed.execution_status !== "succeeded")))) throw new ApiClientError("malformed");
  return result;
}
export function experimentFailure(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.failure.httpStatus === 429) return "Queue is full. One job may run and four may wait. Refresh and try later.";
    if (error.failure.httpStatus === 409) return "Only a fully successful Dev job can be frozen.";
    if (error.failure.httpStatus === 503) return "Experiment storage or worker is unavailable. Check the backend; restart it to recover interrupted jobs.";
    if (error.failure.kind === "malformed") return "The experiment response is inconsistent or malformed. No success is confirmed.";
  }
  return "Experiment request failed. Refresh history before resubmitting: a timed-out submission may already be saved.";
}
export function createExperimentClient(origin?: string, options: { fetch?: typeof fetch } = {}) {
  const request = <T,>(path: `/api/v1/experiments${string}`, parse: (v: unknown) => T, method: "GET" | "POST" = "GET") =>
    createJsonRequest(path, parse, origin, { ...options, method, timeoutMs: 10000 });
  return {
    list: (signal?: AbortSignal, offset = 0) => request(`/api/v1/experiments?limit=50&offset=${offset}`, v => {
      const list = schema<{ jobs: Job[] }>("JobList", v); list.jobs.forEach(parseJob); return list.jobs;
    })(signal),
    start: (body: unknown, signal?: AbortSignal) => request("/api/v1/experiments", parseJob, "POST")(signal, body),
    results: async (id: string, signal?: AbortSignal) => {
      const result = await request(`/api/v1/experiments/${uuid(id)}/results`, parseResults)(signal);
      if (result.id !== id) throw new ApiClientError("malformed");
      return result;
    },
    freeze: async (id: string, signal?: AbortSignal) => {
      const result = await request(`/api/v1/experiments/${uuid(id)}/freeze`, v => schema<Freeze>("DevFreeze", v), "POST")(signal, {});
      if (result.job_id !== id) throw new ApiClientError("malformed");
      return result;
    },
  };
}

export function buildExperiment(split: string, method: string, policy: string, threshold: string, seed: string, questionIds: string, topK: string, failFast: boolean) {
  if (!["train", "dev"].includes(split) || !["bm25", "dense", "hybrid"].includes(method) || !["always_answer", "prompt_abstention", "threshold", "all"].includes(policy)) throw new Error("Choose valid fixture settings.");
  if (!/^-?\d+$/.test(seed) || !Number.isSafeInteger(Number(seed))) throw new Error("Seed must be a safe integer.");
  if (!/^\d+$/.test(topK) || Number(topK) < 1 || Number(topK) > 20) throw new Error("Top-k must be an integer from 1 to 20.");
  if ((policy === "all" || policy === "threshold") && (!threshold.trim() || !Number.isFinite(Number(threshold)))) throw new Error("Threshold must be finite.");
  const names = policy === "all" ? ["always_answer", "prompt_abstention", "threshold"] : [policy];
  const ids = questionIds.split(",").map(s => s.trim()).filter(Boolean);
  if (new Set(ids).size !== ids.length || ids.some(id => !new RegExp(`^synthetic_${split}_0[1-4]$`).test(id))) throw new Error("Use distinct question IDs from the selected fixture split (01–04).");
  return { profile: "p4-synthetic.v1", split, random_seed: Number(seed), question_ids: ids.length ? ids : null,
    retrieval: { method, top_k: Number(topK), ...(method === "hybrid" ? { rrf_k: 60, candidate_k: 50 } : {}) },
    policies: names.map(name => ({ name, ...(name === "threshold" ? { threshold: Number(threshold), score_type: { bm25: "bm25", dense: "dense_cosine", hybrid: "hybrid_rrf" }[method], direction: "at_least", missing_score_decision: "ABSTAIN" } : {}) })), fail_fast: failFast };
}
