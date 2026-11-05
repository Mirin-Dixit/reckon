import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";
import { test } from "node:test";
import { parseQuery } from "../lib/query-api";
import { parseHealth } from "../lib/api";
import { parseJob, parseResults, type Freeze } from "../lib/experiment-api";
import { parseAnalysis } from "../lib/analysis-api";
import { buildEvaluationReport } from "../lib/evaluation-report";

const packets = JSON.parse(execFileSync(resolve(process.platform === "win32" ? "../.venv/Scripts/python.exe" : "../.venv/bin/python"), ["tests/workspace_http_bridge.py"], {
  cwd: process.cwd(), encoding: "utf8", timeout: 90_000,
})) as Record<string, { status: number; cors?: string; body: unknown }>;

test("real loopback health and experiment POST preflight permit only the local frontend", () => {
  assert.equal(packets.health.status, 200);
  assert.equal(parseHealth(packets.health.body).status, "ok");
  assert.equal(packets.preflight.status, 200);
  assert.equal(packets.preflight.cors, "http://127.0.0.1:3000");
  assert.equal(packets.external.status, 403);
});
for (const method of ["bm25", "dense", "hybrid"]) for (const policy of ["always_answer", "threshold", "prompt_abstention"]) {
  test(`real HTTP query contract: ${method} / ${policy}, mock inference only`, () => {
    const response = packets[`query-${method}-${policy}`];
    assert.equal(response.status, 200);
    const query = parseQuery(response.body);
    assert.equal(query.decision, "ANSWER");
    assert.equal(query.execution_status, "succeeded");
    assert.ok(query.citations.length > 0);
    assert.equal(query.retrieved_evidence[0].retrieval_method, { bm25: "bm25", dense: "dense_cosine", hybrid: "hybrid_rrf" }[method]);
  });
}
test("real HTTP synthetic submit, history, selection and Dev freeze remain durable and idempotent", () => {
  assert.equal(packets.start.status, 202);
  const job = parseJob(packets.start.body);
  const result = parseResults(packets.completed.body);
  assert.equal(result.id, job.id);
  assert.equal(result.observations.length, 12);
  assert.equal(result.status, "done");
  assert.equal(parseJob(packets.metadata.body).id, job.id);
  assert.equal(packets.history.status, 200);
  assert.equal(packets.freeze.status, 200);
  assert.deepEqual(packets.freeze.body, packets["freeze-again"].body);
  assert.equal((packets.freeze.body as Freeze).job_id, job.id);
});
test("real HTTP analysis validates in frontend, repeats deterministically and honors explicit threshold selection", () => {
  assert.equal(packets.analysis.status, 200);
  const analysis = parseAnalysis(packets.analysis.body);
  assert.equal(analysis.matched_questions, 4);
  assert.equal(analysis.rows.length, 3);
  assert.deepEqual(packets.analysis.body, packets["analysis-again"].body);
  assert.equal(parseAnalysis(packets["analysis-threshold"].body).rows.length, 1);
  assert.equal(packets["analysis-invalid"].status, 422);
});

test("read-only dashboard routes preserve actual frontend result contracts", () => {
  assert.equal(packets["dashboard-history"].status, 200);
  assert.equal(packets["dashboard-results"].status, 200);
  const history = packets["dashboard-history"].body as { jobs: unknown[] };
  const result = parseResults(packets["dashboard-results"].body);
  assert.ok(history.jobs.map(parseJob).some(job => job.id === result.id));
  assert.equal(result.observations.length, 12);
  assert.deepEqual(result, parseResults(packets.completed.body));
});

test("research report exports genuine HTTP analysis deterministically with unknown risk retained", () => {
  assert.equal(packets["analysis-unknown"].status, 200);
  const detail = parseResults(packets["dashboard-results"].body);
  const analysis = parseAnalysis(packets["analysis-unknown"].body);
  const request = { experiment_id: detail.id, compare: [], lexical_proxy: false, threshold_only: false };
  const bundle = buildEvaluationReport(detail, analysis, request, []);
  assert.ok(bundle.analysis.rows.every(row => row.selective_risk === null));
  assert.equal(JSON.stringify(bundle), JSON.stringify(buildEvaluationReport(detail, analysis, request, [])));
  assert.doesNotMatch(JSON.stringify(bundle), /expected_answer|expected_safe_behavior|evidence_spans/);
});
test("real HTTP recorded execution errors stay failures and cannot freeze Dev configuration", () => {
  const result = parseResults(packets.failed.body);
  assert.ok(result.observations.every(row => row.observed.decision === null && row.observed.execution_status !== "succeeded"));
  assert.equal(packets["failed-freeze"].status, 409);
  assert.equal(packets["invalid-query"].status, 422);
});
