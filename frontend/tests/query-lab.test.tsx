import assert from "node:assert/strict";
import { test } from "node:test";
import { renderToStaticMarkup, renderToString } from "react-dom/server";
import { QueryLab, QueryResult } from "../components/query-lab";
import { WorkbenchShell } from "../components/workbench-shell";
import { ApiClientError } from "../lib/api";
import { createQueryClient, parseQuery, queryFailure } from "../lib/query-api";
import { buildQuery, initialDraft, querySession, type QueryState } from "../lib/query-lab";
import type { QueryResponse, ScoreResponse } from "../lib/query-contracts";

const response: QueryResponse = {
  experiment_id: null, run_id: null, decision: "ANSWER", answer: "Supported response", clarification_question: null,
  decision_reason: { code: "other", explanation: "Evidence supports the answer." }, citations: [], retrieved_evidence: [],
  evidence_assessment: { relevance: "relevant", sufficiency: "sufficient", supporting_evidence_ids: [], contradictions: [], missing_premises: [], unsupported_assumptions: [], ambiguity_requiring_clarification: null },
  policy_name: "always_answer", policy_parameters: {}, provider: null, execution_status: "succeeded", unsupported_premises: [], surfaced_contradictions: [], prompt_version: null, latency_ms: null, token_usage: null, scores: [], retrieval_parameters: {},
};
const request = buildQuery({ ...initialDraft, question: "A corpus question" });
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

for (const method of ["bm25", "dense", "hybrid"] as const) for (const policy of ["always_answer", "threshold", "prompt_abstention"] as const) {
  test(`${method} × ${policy}: exact query POST without credentials or generation overrides`, async () => {
    const body = buildQuery({ ...initialDraft, question: "  A question  ", method, policy });
    const client = createQueryClient(undefined, { fetch: async (url, init) => {
      assert.equal(url, "http://127.0.0.1:8000/api/v1/query"); assert.equal(init?.method, "POST");
      assert.equal(init?.credentials, "omit"); assert.equal(init?.redirect, "error");
      assert.deepEqual(JSON.parse(String(init?.body)), body);
      assert.equal(body.question, "A question"); assert.equal(body.generation, undefined);
      assert.equal(body.policy.score_type, policy === "threshold" ? { bm25: "bm25", dense: "dense_cosine", hybrid: "hybrid_rrf" }[method] : undefined);
      assert.equal(body.retrieval?.rrf_k, method === "hybrid" ? 60 : undefined);
      return json(response);
    } });
    assert.equal((await client.query(body)).execution_status, "succeeded");
  });
}

for (const change of [{ question: " " }, { question: "x".repeat(8001) }, { topK: "0" }, { topK: "21" }, { topK: "1.5" }, { policy: "threshold", threshold: "" }, { policy: "threshold", threshold: "Infinity" }, { method: "hybrid", rrfK: "1001" }, { method: "hybrid", candidateK: "2" }, { method: "hybrid", candidateK: "257" }] as const) {
  test(`validation rejects ${JSON.stringify(change).slice(0, 65)}`, () => assert.throws(() => buildQuery({ ...initialDraft, question: "valid", ...change })));
}
test("Unicode code-point limit and finite out-of-range thresholds remain honest", () => {
  assert.equal([...buildQuery({ ...initialDraft, question: "😀".repeat(8000) }).question].length, 8000);
  assert.equal(buildQuery({ ...initialDraft, question: "valid", method: "hybrid", policy: "threshold", threshold: "1" }).policy.threshold, 1);
});

for (const decision of ["ANSWER", "ABSTAIN", "CLARIFY"] as const) {
  test(`valid ${decision} remains distinct and safely rendered`, () => {
    const result = parseQuery({ ...response, decision, answer: decision === "ANSWER" ? "<script>untrusted</script>" : null,
      clarification_question: decision === "CLARIFY" ? "Which limit?" : null,
      decision_reason: { code: decision === "CLARIFY" ? "ambiguous_intent" : decision === "ABSTAIN" ? "insufficient_evidence" : "other", explanation: "Observed reason" } });
    const html = renderToStaticMarkup(<QueryResult state={{ phase: "ready", result, request }} />);
    assert.match(html, new RegExp(decision)); assert.doesNotMatch(html, /<script>|href=/);
    if (decision === "ABSTAIN") assert.match(html, /Intentional abstention/);
  });
}
for (const change of [{ decision: "UNKNOWN" }, { decision_reason: { code: "ambiguous_intent", explanation: "wrong" } }, { answer: null }, { execution_status: "failed" }, { gold: { expected_answer: "secret" } }, { citations: [{ claim: 1 }] }, { provider: { provider: "ollama" } }, { token_usage: { input_tokens: "wrong", output_tokens: null, total_tokens: null } }]) {
  test(`reject malformed or failed response ${JSON.stringify(change)}`, () => assert.throws(() => parseQuery({ ...response, ...change }), ApiClientError));
}
test("backend errors discard raw messages and never become abstentions", async () => {
  const client = createQueryClient(undefined, { fetch: async () => json({ error: { code: "secret", message: "private traceback", execution_status: "failed" } }, 502) });
  await assert.rejects(client.query(request), (error: unknown) => {
    assert.match(queryFailure(error), /execution failed.*502/); assert.doesNotMatch(queryFailure(error), /private|secret|traceback/); return true;
  });
});
test("unsupported content type cancels body and aborts request", async () => {
  let cancelled = false; let signal: AbortSignal | null | undefined;
  const client = createQueryClient(undefined, { fetch: async (_, init) => {
    signal = init?.signal;
    return new Response(new ReadableStream({ cancel() { cancelled = true; } }), { headers: { "Content-Type": "text/html" } });
  } });
  await assert.rejects(client.query(request), ApiClientError); assert.equal(cancelled, true); assert.equal(signal?.aborted, true);
});
test("oversized response is rejected with bounded reads", async () => {
  const client = createQueryClient(undefined, { fetch: async () => json("x".repeat(1_048_576)) });
  await assert.rejects(client.query(request), ApiClientError);
});
for (const mode of ["timeout", "cancelled", "connection", "malformed"] as const) test(`safe ${mode} with no retry`, async () => {
  let calls = 0;
  const controller = new AbortController();
  const client = createQueryClient(undefined, { timeoutMs: 10, fetch: async () => {
    calls++; if (mode === "connection") throw new Error("secret");
    if (mode === "malformed") return json({ unexpected: true });
    return new Promise<Response>(() => undefined);
  } });
  const pending = client.query(request, controller.signal);
  if (mode === "cancelled") controller.abort();
  await assert.rejects(pending, (error: unknown) => error instanceof ApiClientError && error.failure.kind === mode);
  assert.equal(calls, 1);
});
test("pre-cancelled requests make no HTTP call", async () => {
  const controller = new AbortController(); controller.abort();
  const client = createQueryClient(undefined, { fetch: async () => { throw new Error("must not run"); } });
  await assert.rejects(client.query(request, controller.signal), (e: unknown) => e instanceof ApiClientError && e.failure.kind === "cancelled");
});
test("session enforces single-flight, cancellation, stale completion and disposal", async () => {
  const states: QueryState[] = []; let finish: ((value: QueryResponse) => void) | undefined;
  let calls = 0; let signal: AbortSignal | undefined;
  const session = querySession(async (_, current) => { calls++; signal = current; return new Promise(resolve => { finish = resolve; }); }, state => states.push(state));
  const pending = session.submit(request); await session.submit(request); assert.equal(calls, 1);
  session.cancel(); assert.equal(signal?.aborted, true); finish?.(response); await pending;
  assert.deepEqual(states.map(s => s.phase), ["loading", "cancelled"]);
  session.dispose(); await session.submit(request); assert.equal(calls, 1);
});
test("session publishes success or safe failure without retry", async () => {
  for (const fail of [false, true]) {
    const states: QueryState[] = [];
    await querySession(async () => { if (fail) throw new Error("private"); return response; }, s => states.push(s)).submit(request);
    assert.equal(states.at(-1)?.phase, fail ? "error" : "ready"); assert.doesNotMatch(JSON.stringify(states), /private/);
  }
});
test("SSR starts idle with accessible controls and stable markup", () => {
  assert.equal(renderToString(<QueryLab />), renderToString(<QueryLab />));
  const html = renderToStaticMarkup(<WorkbenchShell workspace="query-lab"><QueryLab /></WorkbenchShell>);
  assert.match(html, /<label for="question">Question/); assert.match(html, /No query has been submitted/);
  assert.match(html, /href="\/query-lab" aria-current="page"/);
  assert.equal((html.match(/aria-disabled="true"/g) ?? []).length, 1);
  assert.doesNotMatch(html, /particle-wave|expected_answer|expected_safe_behavior|<script/);
  assert.match(html, /href="\/#system-status"/);
});

const selfScore: ScoreResponse = { kind: "prompt_self_assessment", value: null,
  source: "model_self_report", retrieval_method: null, parameters: {}, role: "self_assessment",
  threshold: null, threshold_direction: null, unavailable_reason: "Not supplied",
  availability: "unavailable", lower_bound: 0, upper_bound: 1,
  direction: "higher_is_more_support", calibration: "uncalibrated", schema_version: "ragbench.score.v1" };
test("nullable self-assessment remains unavailable, never zero", () => {
  const parsed = parseQuery({ ...response, scores: [selfScore] });
  assert.equal(parsed.scores?.[0].value, null);
  assert.equal(parsed.scores?.[0].availability, "unavailable");
});
for (const change of [{ value: 2, availability: "available", unavailable_reason: null },
  { value: null, availability: "available" }, { calibration: "calibrated" },
  { upper_bound: 2 }, { source: "retrieval" }]) {
  test(`reject invalid score provenance ${JSON.stringify(change)}`, () => {
    assert.throws(() => parseQuery({ ...response, scores: [{ ...selfScore, ...change }] }), ApiClientError);
  });
}
test("session disposal aborts an in-flight request without publishing later output", async () => {
  const states: QueryState[] = []; let signal: AbortSignal | undefined;
  let finish: ((result: QueryResponse) => void) | undefined;
  const session = querySession(async (_, value) => { signal = value; return new Promise(resolve => { finish = resolve; }); }, s => states.push(s));
  const pending = session.submit(request); session.dispose();
  assert.equal(signal?.aborted, true); finish?.(response); await pending;
  assert.deepEqual(states.map(s => s.phase), ["loading"]);
});
