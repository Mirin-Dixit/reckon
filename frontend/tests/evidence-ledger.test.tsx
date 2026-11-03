import assert from "node:assert/strict";
import { test } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryResult } from "../components/query-lab";
import { EvidenceLedger, ScoreLedger, DecisionDetails } from "../components/evidence-ledger";
import { evidenceSegments, validateEvidence } from "../lib/evidence";
import { ApiClientError } from "../lib/api";
import { parseQuery, createQueryClient } from "../lib/query-api";
import { buildQuery, initialDraft, querySession, type QueryState } from "../lib/query-lab";
import type { CitationResponse, EvidenceResponse, QueryResponse, ScoreResponse } from "../lib/query-contracts";

const chunk: EvidenceResponse = { chunk_id: "doc:chunk", document_id: "doc", text: "A😀e\u0301 Z\nnext", start_char: 100, end_char: 111,
  title: "Actual document", source_url: "javascript:alert('unsafe')", retrieval_rank: 1, retrieval_method: "dense_cosine", retrieval_score: 0,
  version: "v1", source_date: "2026-01-01", domain: "procurement", contains_injection: true };
const citation: CitationResponse = { claim: "A claim", evidence_id: chunk.chunk_id, quote: "😀e\u0301", start_char: 101, end_char: 104 };
const response: QueryResponse = { experiment_id: null, run_id: null, decision: "ANSWER", answer: "A grounded claim", clarification_question: null,
  decision_reason: { code: "other", explanation: "Supported" }, citations: [citation], retrieved_evidence: [chunk],
  evidence_assessment: { relevance: "relevant", sufficiency: "partial", supporting_evidence_ids: [chunk.chunk_id], contradictions: ["Two sources disagree"], missing_premises: ["A required date"], unsupported_assumptions: ["An assumed approval"], ambiguity_requiring_clarification: null },
  policy_name: "prompt_based_abstention", policy_parameters: {}, provider: null, execution_status: "succeeded", unsupported_premises: [], surfaced_contradictions: [], prompt_version: null, latency_ms: null, token_usage: null, scores: [], retrieval_parameters: {} };
const request = buildQuery({ ...initialDraft, question: "A question" });
const self: ScoreResponse = { kind: "prompt_self_assessment", value: null, source: "model_self_report", retrieval_method: null, parameters: {}, role: "self_assessment", threshold: null, threshold_direction: null, unavailable_reason: "Model did not supply a score", availability: "unavailable", lower_bound: 0, upper_bound: 1, direction: "higher_is_more_support", calibration: "uncalibrated", schema_version: "ragbench.score.v1" };
const retrieval = (kind: "bm25" | "dense_cosine" | "hybrid_rrf", value: number): ScoreResponse => ({ ...self, kind, value,
  source: "retrieval", retrieval_method: kind, role: "observational", unavailable_reason: null, availability: "available",
  lower_bound: kind === "dense_cosine" ? -1 : 0, upper_bound: kind === "bm25" ? null : kind === "dense_cosine" ? 1 : 2 / 61,
  direction: "higher_is_more_relevant", parameters: kind === "hybrid_rrf" ? { rrf_k: 60, rank_lists: 2 } : {} });

test("exact Unicode code-point coordinates preserve emoji, combining marks and original newlines", () => {
  assert.doesNotThrow(() => validateEvidence([chunk], [citation]));
  const segments = evidenceSegments(chunk, [citation]);
  assert.deepEqual(segments, [{ text: "A", citations: [] }, { text: "😀e\u0301", citations: [1] }, { text: " Z\nnext", citations: [] }]);
  assert.equal(segments.map(s => s.text).join(""), chunk.text);
  const html = renderToStaticMarkup(<EvidenceLedger result={parseQuery(response)} />);
  assert.match(html, /<mark aria-label="Citations 1">😀é<\/mark>/u);
  assert.match(html, /101, 104/); assert.match(html, /href="#evidence-1"/); assert.match(html, /id="evidence-1" tabindex="-1"/);
});
test("complete chunk and exact endpoint spans are valid", () => {
  assert.doesNotThrow(() => validateEvidence([chunk], [{ ...citation, start_char: 100, end_char: 111, quote: chunk.text }]));
  assert.doesNotThrow(() => validateEvidence([chunk], [{ ...citation, start_char: 110, end_char: 111, quote: "t" }]));
});
test("overlapping and repeated citations split exact boundaries without duplicated source text", () => {
  const other = { ...citation, start_char: 102, end_char: 105, quote: "e\u0301 " };
  const segments = evidenceSegments(chunk, [citation, other, citation]);
  assert.equal(segments.map(s => s.text).join(""), chunk.text);
  assert.deepEqual(segments.find(s => s.text === "e\u0301")?.citations, [1, 2, 3]);
});
test("repeated quote text uses supplied offsets, never the first text match", () => {
  const repeated = { ...chunk, text: "same same", start_char: 20, end_char: 29 };
  const segments = evidenceSegments(repeated, [{ ...citation, quote: "same", start_char: 25, end_char: 29 }]);
  assert.deepEqual(segments, [{ text: "same ", citations: [] }, { text: "same", citations: [1] }]);
});
for (const change of [{ start_char: 99 }, { end_char: 112 }, { end_char: 101 }, { start_char: 102, end_char: 105 },
  { quote: "😀é" }, { quote: "" }, { claim: " " }, { evidence_id: "not-retrieved" }, { start_char: 101.5 }, { end_char: Number.MAX_SAFE_INTEGER + 1 }]) {
  test(`reject citation rather than approximate ${JSON.stringify(change)}`, () => assert.throws(() => parseQuery({ ...response, citations: [{ ...citation, ...change }] }), ApiClientError));
}
for (const change of [{ start_char: -1 }, { end_char: 112 }, { end_char: 100 }, { text: "different" }, { retrieval_rank: 0 }, { chunk_id: "" }]) {
  test(`reject inconsistent evidence ${JSON.stringify(change)}`, () => assert.throws(() => parseQuery({ ...response, retrieved_evidence: [{ ...chunk, ...change }] }), ApiClientError));
}
test("duplicate chunk IDs are malformed, not alternative citation matches", () => {
  assert.throws(() => parseQuery({ ...response, retrieved_evidence: [chunk, chunk] }), ApiClientError);
});
test("actual source metadata, injection warning and raw zero score are preserved safely", () => {
  const html = renderToStaticMarkup(<EvidenceLedger result={response} />);
  for (const text of ["Actual document", "doc:chunk", "procurement", "2026-01-01", "v1", "untrusted data", "Raw retrieval score"]) assert.ok(html.includes(text));
  assert.doesNotMatch(html, /href="javascript:|<script/);
  assert.match(html, /javascript:alert/); // URL is inert text, never a link.
});
test("backend HTML and source URLs remain plain escaped text", () => {
  const text = '<img src=x onerror="alert(1)">';
  const html = renderToStaticMarkup(<EvidenceLedger result={{ ...response, citations: [], retrieved_evidence: [{ ...chunk, text, end_char: 100 + [...text].length, title: "<script>bad</script>" }] }} />);
  assert.doesNotMatch(html, /<img|<script|href="https?:/); assert.match(html, /&lt;img/);
});
test("no evidence and no citations do not imply corpus absence or a failed execution", () => {
  const html = renderToStaticMarkup(<EvidenceLedger result={{ ...response, citations: [], retrieved_evidence: [] }} />);
  assert.match(html, /No evidence passages/); assert.match(html, /does not establish corpus-wide absence/); assert.match(html, /No claim citations/);
});
for (const [kind, values] of [["bm25", [0, 100000]], ["dense_cosine", [-1, 0, 1]], ["hybrid_rrf", [0, 2 / 61]]] as const) {
  for (const value of values) test(`valid ${kind} boundary ${value}`, () => assert.doesNotThrow(() => parseQuery({ ...response, scores: [retrieval(kind, value)] })));
}
for (const [kind, value] of [["bm25", -0.001], ["dense_cosine", -1.001], ["dense_cosine", 1.001], ["hybrid_rrf", 2 / 61 + 0.00001]] as const) {
  test(`reject ${kind} out-of-range score ${value}`, () => assert.throws(() => parseQuery({ ...response, scores: [retrieval(kind, value)] }), ApiClientError));
}
test("per-passage typed scores receive the same validation", () => assert.throws(() => parseQuery({ ...response, retrieved_evidence: [{ ...chunk, score: retrieval("dense_cosine", 2) }] }), ApiClientError));
test("nullable self-assessment is unavailable, while zero remains available and uncalibrated", () => {
  const zero = { ...self, value: 0, availability: "available" as const, unavailable_reason: null };
  const result = parseQuery({ ...response, scores: [self, zero] });
  const html = renderToStaticMarkup(<ScoreLedger scores={result.scores!} caption="Signals" />);
  assert.match(html, /Unavailable/); assert.match(html, /Model did not supply a score/); assert.match(html, /<td>0<br/);
  assert.match(html, /uncalibrated/); assert.match(html, /model_self_report/); assert.match(html, /higher_is_more_support/);
});
for (const direction of ["at_least", "at_most"] as const) test(`threshold shows actual zero score and ${direction} comparison`, () => {
  const score: ScoreResponse = { ...retrieval("bm25", 0), role: "threshold_input", threshold: 1, threshold_direction: direction };
  const result = parseQuery({ ...response, scores: [score], policy_parameters: { threshold: 1, direction, observed_aggregate_score: 0, score_type: "bm25", aggregation: "max" } });
  const html = renderToStaticMarkup(<DecisionDetails result={result} />);
  assert.match(html, /Compared score: 0/); assert.ok(html.includes(direction === "at_least" ? "&gt;=" : "&lt;="));
  assert.match(html, /Actual aggregate score<\/dt><dd>0/); assert.match(html, /Threshold<\/dt><dd>1/);
});
test("missing compared score is unavailable, never a comparison against zero", () => {
  const score: ScoreResponse = { ...retrieval("bm25", 0), value: null, role: "threshold_input", threshold: 1, threshold_direction: "at_least", unavailable_reason: "No score", availability: "unavailable" };
  const html = renderToStaticMarkup(<ScoreLedger scores={[score]} caption="Threshold" />);
  assert.match(html, /comparison unavailable/); assert.doesNotMatch(html, /Compared score: 0/);
});
test("no scores and null self-assessment are separate presentations", () => {
  assert.match(renderToStaticMarkup(<ScoreLedger scores={[]} caption="Signals" />), /No typed score signals/);
  assert.doesNotMatch(renderToStaticMarkup(<ScoreLedger scores={[self]} caption="Signals" />), /No typed score signals/);
});
for (const decision of ["ANSWER", "ABSTAIN", "CLARIFY"] as const) test(`${decision} uses a distinct labeled presentation and valid reason`, () => {
  const reason = decision === "CLARIFY" ? "ambiguous_intent" : decision === "ABSTAIN" ? "insufficient_evidence" : "other";
  const result = parseQuery({ ...response, decision, answer: decision === "ANSWER" ? response.answer : null, clarification_question: decision === "CLARIFY" ? "Which meaning?" : null, decision_reason: { code: reason, explanation: "Observed rationale" } });
  const html = renderToStaticMarkup(<QueryResult state={{ phase: "ready", request, result }} />);
  assert.ok(html.includes(`decision-${decision.toLowerCase()}`)); assert.match(html, new RegExp(`<code>${reason}</code>`));
  if (decision === "CLARIFY") assert.match(html, /Which meaning/);
  if (decision === "ABSTAIN") assert.match(html, /Intentional abstention/);
});
test("execution failure and malformed payload states do not display evidence as a successful result", async () => {
  for (const body of [{ ...response, execution_status: "failed" }, { ...response, citations: [{ ...citation, quote: "wrong" }] }]) {
    const states: QueryState[] = [];
    const client = createQueryClient(undefined, { fetch: async () => new Response(JSON.stringify(body), { headers: { "Content-Type": "application/json" } }) });
    await querySession(client.query, state => states.push(state)).submit(request);
    const html = renderToStaticMarkup(<QueryResult state={states.at(-1)!} />);
    assert.match(html, /Request failed/); assert.doesNotMatch(html, /Evidence ledger|Intentional abstention|A grounded claim/);
  }
});
test("timing and tokens appear only when supplied, preserving real zero values", () => {
  const absent = renderToStaticMarkup(<DecisionDetails result={response} />);
  assert.doesNotMatch(absent, /<dt>Latency|<dt>Model|<dt>Input tokens/);
  assert.match(absent, /No model, timing or token metadata/);
  const html = renderToStaticMarkup(<DecisionDetails result={parseQuery({ ...response, latency_ms: 0, token_usage: { input_tokens: 0, output_tokens: null, total_tokens: null }, provider: { provider: "ollama", model: "local", model_digest: "digest" }, prompt_version: "prompt-decision-v3" })} />);
  assert.match(html, /Latency \(ms\)<\/dt><dd>0/); assert.match(html, /Input tokens<\/dt><dd>0/);
  assert.doesNotMatch(html, /<dt>Output tokens/); assert.match(html, /prompt-decision-v3|digest/);
});
for (const change of [{ latency_ms: -1 }, { token_usage: { input_tokens: -1, output_tokens: null, total_tokens: null } }]) test("reject negative runtime metadata", () => assert.throws(() => parseQuery({ ...response, ...change }), ApiClientError));
test("cancelled old evidence cannot replace a newer result or survive the next loading state", async () => {
  let finish: ((response: QueryResponse) => void) | undefined; let calls = 0;
  const states: QueryState[] = [];
  const session = querySession(async () => { calls++; return calls === 1 ? new Promise(resolve => { finish = resolve; }) : { ...response, answer: "New answer" }; }, state => states.push(state));
  const old = session.submit(request); session.cancel(); await session.submit(request); finish?.(response); await old;
  const latest = states.at(-1)!;
  assert.equal(latest.phase, "ready"); if (latest.phase === "ready") assert.equal(latest.result.answer, "New answer");
  assert.deepEqual(states.map(s => s.phase), ["loading", "cancelled", "loading", "ready"]);
  assert.doesNotMatch(renderToStaticMarkup(<QueryResult state={states[2]} />), /A grounded claim|Evidence ledger/);
});
