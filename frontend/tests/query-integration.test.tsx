import assert from "node:assert/strict";
import { test } from "node:test";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import type { QueryRequest } from "../lib/query-contracts";
import { QueryLab, QueryResult } from "../components/query-lab";
import { ApiClientError } from "../lib/api";
import { createQueryClient, parseQuery, queryFailure } from "../lib/query-api";
import { buildQuery, initialDraft } from "../lib/query-lab";

const combinations = (["bm25", "dense", "hybrid"] as const).flatMap(method =>
  (["always_answer", "threshold", "prompt_abstention"] as const).map(policy =>
    buildQuery({ ...initialDraft, question: "What approval is required?", method, policy })));
const cases = combinations.map(request => ({ request, outcome: "ANSWER" }));
cases.push(...["ABSTAIN", "CLARIFY", "EXECUTION_FAILURE"].map(outcome => ({ request: combinations[0], outcome })));
const prohibited = ["expected_answer", "expected_safe_behavior", "evidence_spans", "is_answerable", "unanswerable_category", "question_id", "split"];
const negative = prohibited.map(key => ({ request: { ...combinations[0], [key]: "not runtime input" }, outcome: "ANSWER" }));
const packets = JSON.parse(execFileSync(resolve(process.platform === "win32" ? "../.venv/Scripts/python.exe" : "../.venv/bin/python"), ["tests/query_http_bridge.py"], {
  input: JSON.stringify([...cases, ...negative]), cwd: process.cwd(), encoding: "utf8", timeout: 60_000,
})) as { status: number; body: unknown; observed: QueryRequest[]; prompts: unknown[] }[];
assert.ok(Array.isArray(packets));

for (const [index, request] of combinations.entries()) test(`actual FastAPI serialization → frontend: ${request.retrieval?.method} × ${request.policy.name}`, async () => {
  const packet = packets[index];
  assert.equal(packet.status, 200); assert.equal(packet.observed.length, 1);
  assert.equal(packet.observed[0].retrieval?.method, request.retrieval?.method);
  assert.equal(packet.observed[0].policy.name, request.policy.name);
  for (const key of prohibited) assert.equal(Object.hasOwn(packet.observed[0], key), false);
  const result = await createQueryClient(undefined, { fetch: async () => new Response(JSON.stringify(packet.body), { status: packet.status, headers: { "Content-Type": "application/json" } }) }).query(request);
  assert.equal(result.decision, "ANSWER");
  assert.equal(result.retrieved_evidence[0].retrieval_method, { bm25: "bm25", dense: "dense_cosine", hybrid: "hybrid_rrf" }[request.retrieval!.method!]);
  assert.ok(packet.prompts.length > 0);
  for (const prompt of packet.prompts) {
    const keys: string[] = [];
    const collect = (value: unknown): void => { if (typeof value === "object" && value !== null) for (const [key, nested] of Object.entries(value)) { keys.push(key); collect(nested); } };
    collect(prompt);
    for (const key of prohibited) assert.equal(keys.includes(key), false);
  }
  const html = renderToStaticMarkup(<QueryResult state={{ phase: "ready", result, request }} />);
  assert.match(html, /Evidence ledger/); assert.match(html, /<mark aria-label="Citations 1">Approval requires manager approval\.<\/mark>/);
  assert.doesNotMatch(html, /sk-proj-|expected_answer|expected_safe_behavior/);
});
for (const [i, decision] of ["ABSTAIN", "CLARIFY"].entries()) test(`actual FastAPI ${decision} remains intentional and separately rendered`, () => {
  const packet = packets[9 + i]; assert.equal(packet.status, 200);
  const result = parseQuery(packet.body); assert.equal(result.decision, decision);
  const html = renderToStaticMarkup(<QueryResult state={{ phase: "ready", result, request: combinations[0] }} />);
  assert.match(html, new RegExp(decision)); assert.doesNotMatch(html, /Request failed/);
});
test("actual execution failure is HTTP 502, never intentional ABSTAIN", async () => {
  const packet = packets[11]; assert.equal(packet.status, 502);
  const client = createQueryClient(undefined, { fetch: async () => new Response(JSON.stringify(packet.body), { status: packet.status, headers: { "Content-Type": "application/json" } }) });
  await assert.rejects(client.query(combinations[0]), (error: unknown) => {
    assert.ok(error instanceof ApiClientError); assert.equal(error.failure.httpStatus, 502);
    assert.match(queryFailure(error), /not an intentional abstention/); return true;
  });
});
for (const [i, key] of prohibited.entries()) test(`actual query route rejects benchmark-only input ${key} before execution`, () => {
  const packet = packets[12 + i]; assert.equal(packet.status, 422); assert.deepEqual(packet.observed, []);
});
test("failed execution inside HTTP-success shape is malformed without inventing HTTP 502", () => {
  const packet = packets[0];
  const body = packet.body;
  assert.ok(typeof body === "object" && body !== null);
  assert.throws(() => parseQuery({ ...body, execution_status: "failed" }), (error: unknown) => {
    assert.ok(error instanceof ApiClientError); assert.equal(error.failure.kind, "malformed");
    assert.equal(error.failure.httpStatus, undefined); return true;
  });
});
test("validation and response focus targets preserve semantic headings and live announcements", () => {
  const html = renderToStaticMarkup(<QueryLab />);
  assert.match(html, /id="response-title" tabindex="-1"/);
  assert.match(html, /id="query-validation" tabindex="-1"/);
  const result = parseQuery(packets[0].body);
  const observed = renderToStaticMarkup(<QueryResult state={{ phase: "ready", result, request: combinations[0] }} />);
  assert.match(observed, /role="status"><h3>ANSWER<\/h3>/);
  assert.doesNotMatch(observed, /<h3 role="status"/);
});
