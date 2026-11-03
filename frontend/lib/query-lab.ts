import type { QueryRequest, QueryResponse, PolicyRequest } from "./query-contracts";
import { queryFailure } from "./query-api";

export interface QueryDraft {
  question: string; method: "bm25" | "dense" | "hybrid";
  policy: PolicyRequest["name"]; topK: string; candidateK: string; rrfK: string; threshold: string;
}
export const initialDraft: QueryDraft = { question: "", method: "bm25", policy: "prompt_abstention", topK: "3", candidateK: "", rrfK: "60", threshold: "0" };
export function buildQuery(draft: QueryDraft): QueryRequest {
  const question = draft.question.trim();
  if (!question || [...question].length > 8000) throw new Error("Enter a question between 1 and 8,000 characters.");
  const integer = (text: string, max: number, label: string) => {
    if (!/^\d+$/.test(text) || +text < 1 || +text > max) throw new Error(`${label} must be a whole number between 1 and ${max}.`);
    return +text;
  };
  if (!["bm25", "dense", "hybrid"].includes(draft.method) || !["always_answer", "threshold", "prompt_abstention"].includes(draft.policy)) throw new Error("Choose a supported retrieval method and policy.");
  const top_k = integer(draft.topK, 20, "Top k");
  const retrieval: QueryRequest["retrieval"] = { method: draft.method, top_k };
  if (draft.method === "hybrid") {
    retrieval.rrf_k = integer(draft.rrfK, 1000, "RRF k");
    if (draft.candidateK.trim()) {
      retrieval.candidate_k = integer(draft.candidateK, 256, "Candidate k");
      if (retrieval.candidate_k < top_k) throw new Error("Candidate k must be at least top k.");
    }
  }
  const policy: PolicyRequest = { name: draft.policy };
  if (draft.policy === "threshold") {
    if (!draft.threshold.trim() || !Number.isFinite(Number(draft.threshold))) throw new Error("Enter a finite numeric threshold.");
    policy.score_type = { bm25: "bm25", dense: "dense_cosine", hybrid: "hybrid_rrf" }[draft.method] as PolicyRequest["score_type"];
    policy.threshold = Number(draft.threshold);
    policy.direction = "at_least";
    policy.missing_score_decision = "ABSTAIN";
  }
  return { question, retrieval, policy };
}

export type QueryState = { phase: "idle" } | { phase: "loading" } |
  { phase: "ready"; result: QueryResponse; request: QueryRequest } |
  { phase: "error"; message: string } | { phase: "cancelled"; message: string };

/** One active browser request, no retries, stale completion and unmount guards. */
export function querySession(query: (request: QueryRequest, signal: AbortSignal) => Promise<QueryResponse>, publish: (state: QueryState) => void) {
  let active: AbortController | undefined;
  let disposed = false;
  return {
    async submit(request: QueryRequest) {
      if (disposed || active) return;
      const controller = new AbortController(); active = controller;
      publish({ phase: "loading" });
      try {
        const result = await query(request, controller.signal);
        if (!disposed && active === controller) publish({ phase: "ready", result, request });
      } catch (error: unknown) {
        if (!disposed && active === controller) publish({ phase: "error", message: queryFailure(error) });
      } finally { if (active === controller) active = undefined; }
    },
    cancel() {
      active?.abort(); active = undefined;
      if (!disposed) publish({ phase: "cancelled", message: "Request cancelled. Backend inference may still be running; wait before submitting again." });
    },
    dispose() { disposed = true; active?.abort(); active = undefined; },
  };
}
