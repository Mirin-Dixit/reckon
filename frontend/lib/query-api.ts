import schemas from "./query-schema.json";
import { ApiClientError, createJsonRequest } from "./api";
import type { QueryRequest, QueryResponse, ScoreResponse } from "./query-contracts";
import { validateEvidence } from "./evidence";

type Schema = { $ref?: string; anyOf?: Schema[]; const?: unknown; enum?: unknown[];
  type?: string; properties?: Record<string, Schema>; required?: string[];
  additionalProperties?: boolean | Schema; items?: Schema; minimum?: number; maximum?: number;
  minLength?: number; maxLength?: number };
const record = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);

/** Validate the query-only Pydantic schema snapshot, including every nested object. */
export function matches(value: unknown, schema: Schema, defs: Record<string, Schema>, depth = 0): boolean {
  if (depth > 40) return false;
  if (schema.$ref) return matches(value, defs[schema.$ref.split("/").at(-1)!], defs, depth + 1);
  if (schema.anyOf) return schema.anyOf.some(s => matches(value, s, defs, depth + 1));
  if ("const" in schema && value !== schema.const) return false;
  if (schema.enum && !schema.enum.includes(value)) return false;
  switch (schema.type) {
    case "null": return value === null;
    case "string": return typeof value === "string" && [...value].length >= (schema.minLength ?? 0) && [...value].length <= (schema.maxLength ?? Infinity);
    case "boolean": return typeof value === "boolean";
    case "integer": case "number": return typeof value === "number" && Number.isFinite(value) && (schema.type !== "integer" || Number.isSafeInteger(value)) && value >= (schema.minimum ?? -Infinity) && value <= (schema.maximum ?? Infinity);
    case "array": return Array.isArray(value) && value.every(v => matches(v, schema.items!, defs, depth + 1));
    case "object": {
      if (!record(value) || (schema.required && !schema.required.every(k => Object.hasOwn(value, k)))) return false;
      return Object.entries(value).every(([k, v]) => schema.properties && Object.hasOwn(schema.properties, k)
        ? matches(v, schema.properties[k], defs, depth + 1)
        : schema.additionalProperties === false ? false : typeof schema.additionalProperties === "object"
          ? matches(v, schema.additionalProperties, defs, depth + 1) : true);
    }
    default: return true;
  }
}

function validScore(score: ScoreResponse): boolean {
  const self = score.kind === "prompt_self_assessment";
  let lower = 0; let upper: number | null = null;
  if (score.kind === "dense_cosine") { lower = -1; upper = 1; }
  if (self) upper = 1;
  if (score.kind === "hybrid_rrf") {
    const { rrf_k: k, rank_lists: lists } = score.parameters;
    if (k !== undefined || lists !== undefined) {
      if (typeof k !== "number" || !Number.isSafeInteger(k) || k <= 0 || typeof lists !== "number" || !Number.isSafeInteger(lists) || lists < 0) return false;
      upper = lists / (k + 1);
    } else if (score.value !== null) return false;
  }
  return score.lower_bound === lower && score.upper_bound === upper &&
    score.source === (self ? "model_self_report" : "retrieval") &&
    score.retrieval_method === (self ? null : score.kind) &&
    score.direction === (self ? "higher_is_more_support" : "higher_is_more_relevant") &&
    (score.role === "self_assessment") === self &&
    (score.role === "threshold_input" ? score.threshold !== null && score.threshold_direction !== null : score.threshold === null && score.threshold_direction === null) &&
    (score.value === null ? score.availability === "unavailable" && !!score.unavailable_reason?.trim()
      : score.availability === "available" && score.unavailable_reason === null && score.value >= lower && (upper === null || score.value <= upper));
}

export function parseQuery(value: unknown): QueryResponse {
  if (!matches(value, schemas.response, schemas.response.$defs)) throw new ApiClientError("malformed");
  const result = value as QueryResponse;
  // An execution error is never a successful decision, even on HTTP 200.
  if (result.execution_status !== "succeeded") throw new ApiClientError("malformed");
  if ((result.decision === "ANSWER" && (!result.answer?.trim() || result.clarification_question !== null)) ||
      (result.decision !== "ANSWER" && result.answer !== null) ||
      (result.decision === "CLARIFY" && !result.clarification_question?.trim()) ||
      (result.decision === "ABSTAIN" && (!result.decision_reason || result.clarification_question !== null))) throw new ApiClientError("malformed");
  const code = result.decision_reason?.code;
  if (code && ((result.decision === "ANSWER" && code !== "other") ||
      (result.decision === "ABSTAIN" && code === "ambiguous_intent") ||
      (result.decision === "CLARIFY" && code !== "ambiguous_intent" && code !== "other"))) throw new ApiClientError("malformed");
  if (![...(result.scores ?? []), ...result.retrieved_evidence.flatMap(e => e.score ? [e.score] : [])].every(validScore)) throw new ApiClientError("malformed");
  try { validateEvidence(result.retrieved_evidence, result.citations); }
  catch { throw new ApiClientError("malformed"); }
  if ((result.latency_ms !== null && result.latency_ms < 0) ||
      (result.token_usage !== null && Object.values(result.token_usage).some(n => n !== null && n < 0))) throw new ApiClientError("malformed");
  return result;
}

export function createQueryClient(origin?: string, options: { fetch?: typeof fetch; timeoutMs?: number } = {}) {
  const request = createJsonRequest("/api/v1/query", parseQuery, origin, options);
  return { query: (body: QueryRequest, signal?: AbortSignal) => request(signal, body) };
}

export function queryFailure(error: unknown): string {
  if (!(error instanceof ApiClientError)) return "Cannot reach the local backend. Check its address and CORS configuration.";
  switch (error.failure.kind) {
    case "cancelled": return "Request cancelled. Backend inference may still be running; cancellation does not guarantee it stops.";
    case "timeout": return "Request timed out. Backend inference may still be running. No retry was made.";
    case "malformed": return "Unexpected query response. Check frontend and backend compatibility. No decision is available.";
    case "http": return `Backend execution failed (HTTP ${error.failure.httpStatus ?? "error"}). This is not an intentional abstention. Check local model availability, memory and provider-attempt limits.`;
    case "configuration": return "Invalid local backend address. Check NEXT_PUBLIC_RECKON_API_BASE_URL.";
    case "connection": return "Cannot reach the local backend. Check its address and CORS configuration.";
  }
}
