import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { ComparisonCandidate, EvaluationAnalysis, EvaluationDashboard, EvaluationOverview } from "../components/evaluation-dashboard";
import { WorkbenchNavigationView } from "../components/workbench-navigation";
import { createEvaluationClient, comparisonBlocker, canAnalyze, evaluationFailure, evaluationSession, initialEvaluationState, type EvaluationClient, type EvaluationState } from "../lib/evaluation-dashboard";
import { parseAnalysis } from "../lib/analysis-api";
import { parseResults, type Job, type Results } from "../lib/experiment-api";
import { ApiClientError } from "../lib/api";

const result = (): Results => parseResults(JSON.parse(readFileSync("tests/fixture_job_result.json", "utf8")));
const report = () => parseAnalysis(JSON.parse(readFileSync("tests/fixture_analysis.json", "utf8")));
const job = (): Job => { const { result: _r, observations: _o, ...summary } = result(); void _r; void _o; return summary; };
const second = "11111111-1111-4111-8111-111111111111";
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (error: unknown) => void; const promise = new Promise<T>((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
const tick = () => new Promise<void>(resolve => setImmediate(resolve));
function setup(overrides: Partial<EvaluationClient> = {}) {
  let state: EvaluationState = initialEvaluationState;
  const api: EvaluationClient = { list: async () => [job()], results: async () => result(), analyze: async () => report(), ...overrides };
  const session = evaluationSession(api, next => { state = next; });
  return { session, state: () => state };
}

test("dashboard starts with deterministic loading markup and no invented metrics", () => {
  const html = renderToStaticMarkup(<EvaluationDashboard />);
  assert.match(html, /Evaluation Dashboard/); assert.match(html, /role="status"/);
  assert.match(html, /Synthetic development only/); assert.match(html, /never starts model inference/);
  assert.doesNotMatch(html, /<table|0\.000|dangerouslySetInnerHTML/);
});
test("navigation exposes actual dashboard link with active state and mobile control", () => {
  const html = renderToStaticMarkup(<WorkbenchNavigationView workspace="evaluation" expanded={false} onToggle={() => {}} onNavigate={() => {}} />);
  assert.match(html, /href="\/evaluation" aria-current="page"/);
  assert.match(html, /aria-expanded="false" aria-controls="workspace-links"/);
  assert.doesNotMatch(html, /soon/);
});
test("overview uses persisted counts, zero seed and configuration with safe rendering", () => {
  const data = result(); data.id = "<script>bad</script>";
  const html = renderToStaticMarkup(<EvaluationOverview detail={data} />);
  assert.match(html, /&lt;script&gt;/); assert.doesNotMatch(html, /<script>/);
  assert.match(html, /Saved observations/); assert.match(html, /Saved experiment seed/);
  assert.match(html, /Empirical evaluation is unavailable/); assert.match(html, /Runtime fingerprint/);
});
test("undefined risk, judgment basis, sample size and real denominators stay explicit", () => {
  const data = report(); data.curves = [];
  data.rows[0].selective_risk = null;
  data.rows[0].undefined_reason = "Unknown answer judgment";
  const html = renderToStaticMarkup(<EvaluationAnalysis report={data} />);
  assert.match(html, /No saved threshold series/);
  for (const text of ["A/N", "A/(A+B+C)", "Undefined", "Missing observation rate", "Judgment completeness", "not verified semantic correctness", "not independent samples", "Source-record fingerprints"]) assert.ok(html.includes(text), text);
  assert.match(html, /<caption>/); assert.match(html, /scope="col"/); assert.match(html, /tabindex="0"/);
});
test("unknown judgments and partial/full curves use R1 fields without extrapolation", () => {
  const data = report(); data.loss_basis = "unknown";
  assert.match(renderToStaticMarkup(<EvaluationAnalysis report={data} />), /judgments are unknown/);
  const curve = parseAnalysis(JSON.parse(readFileSync("tests/fixture_analysis_curve.json", "utf8")));
  const html = renderToStaticMarkup(<EvaluationAnalysis report={curve} />);
  assert.match(html, /Partial domains are not extrapolated/);
  assert.ok(/Complete threshold sweep|Partial threshold curve|Undefined AURC/.test(html));
  assert.match(html, /Coverage domain/);
});
test("client uses only bounded read-only routes and omits credentials", async () => {
  const seen: string[] = [];
  const client = createEvaluationClient("http://127.0.0.1:8000", { fetch: async (url, init) => {
    seen.push(String(url)); assert.equal(init?.method, "GET"); assert.equal(init?.credentials, "omit"); assert.equal(init?.body, undefined); assert.equal(init?.cache, "no-store");
    return Response.json(String(url).includes("?limit") ? { jobs: [job()] } : result());
  }});
  assert.equal((await client.list(0)).length, 1); assert.equal((await client.results(job().id)).id, job().id);
  assert.equal(seen[0], "http://127.0.0.1:8000/api/v1/analysis/experiments?limit=20&offset=0");
  assert.equal(seen[1], `http://127.0.0.1:8000/api/v1/analysis/experiments/${job().id}`);
  await assert.rejects(client.list(-1), ApiClientError); await assert.rejects(client.results("../secret"), ApiClientError);
  assert.equal(seen.length, 2);
});
for (const value of [{}, { jobs: [job(), job()] }, { jobs: [], extra: true }, { jobs: [ { ...job(), empirical_evaluation: true } ] }]) {
  test(`malformed history rejects ${JSON.stringify(value).slice(0, 50)}`, async () => {
    await assert.rejects(createEvaluationClient(undefined, { fetch: async () => Response.json(value) }).list(0), ApiClientError);
  });
}
test("wrong selected result ID is rejected", async () => {
  await assert.rejects(createEvaluationClient(undefined, { fetch: async () => Response.json(result()) }).results(second), ApiClientError);
});
test("empty history resolves cleanly without a result request", async () => {
  let calls = 0; const { session, state } = setup({ list: async () => [], results: async () => { calls++; return result(); } });
  await session.refresh(); assert.equal(calls, 0); assert.equal(state().listPhase, "ready"); assert.equal(state().detail, null);
});
test("selection and refresh load real records without automatic analysis", async () => {
  let calls = 0, analyses = 0; const { session, state } = setup({ results: async () => { calls++; return result(); }, analyze: async () => { analyses++; return report(); } });
  await session.refresh(); assert.equal(state().detailPhase, "ready"); await session.select(job().id); assert.equal(calls, 1);
  await session.refresh(); assert.equal(calls, 2); assert.equal(analyses, 0);
  await session.analyze([], true, false); assert.equal(analyses, 1); assert.equal(state().analysisPhase, "ready");
});
test("duplicate refresh and analysis clicks do not duplicate active requests", async () => {
  const wait = deferred<Job[]>(), analysis = deferred<ReturnType<typeof report>>(); let lists = 0, analyses = 0;
  const { session } = setup({ list: async () => { lists++; return wait.promise; }, analyze: async () => { analyses++; return analysis.promise; } });
  const first = session.refresh(); await session.refresh(); assert.equal(lists, 1); wait.resolve([job()]); await first;
  const a = session.analyze([], true, false); await session.analyze([], true, false); assert.equal(analyses, 1); analysis.resolve(report()); await a;
});
test("superseded selection aborts and ignores a stale detail response", async () => {
  const wait = deferred<Results>(); let signal: AbortSignal | undefined;
  const { session, state } = setup({ list: async () => [job(), { ...job(), id: second }], results: async (id, s) => { if (id === job().id) { signal = s; return wait.promise; } return { ...result(), id: second }; } });
  const refresh = session.refresh(); await tick(); await session.select(second); assert.equal(signal?.aborted, true);
  wait.resolve(result()); await refresh; assert.equal(state().detail?.id, second);
});
test("refresh failure after aborted detail does not leave permanent loading state", async () => {
  const wait = deferred<Results>(); let lists = 0;
  const { session, state } = setup({ list: async () => { if (++lists > 1) throw Error("private"); return [job()]; }, results: () => wait.promise });
  const first = session.refresh(); await tick(); // first list remains active until selection finishes
  // A page change supersedes the in-flight selection and can fail independently.
  await session.refresh(20); assert.equal(state().listPhase, "error"); assert.equal(state().detailPhase, "idle");
  wait.resolve(result()); await first; assert.equal(state().detail, null); assert.doesNotMatch(state().listError, /private/);
});
for (const action of ["cancel", "invalidate", "dispose", "refresh"]) test(`analysis ${action} aborts and ignores late results`, async () => {
  const wait = deferred<ReturnType<typeof report>>(); let signal: AbortSignal | undefined;
  const { session, state } = setup({ analyze: async (_id, _compare, _proxy, s) => { signal = s; return wait.promise; } });
  await session.refresh(); const pending = session.analyze([], true, false);
  if (action === "cancel") session.cancelAnalysis(); else if (action === "invalidate") session.invalidateAnalysis(); else if (action === "dispose") session.dispose(); else await session.refresh();
  assert.equal(signal?.aborted, true); wait.resolve(report()); await pending; assert.equal(state().analysis, null);
});
test("network and detail errors allow retry without raw exception leakage", async () => {
  let fail = true; const { session, state } = setup({ results: async () => { if (fail) throw Error("API_KEY=private"); return result(); } });
  await session.refresh(); assert.equal(state().detailPhase, "error"); assert.doesNotMatch(state().detailError, /private/);
  fail = false; await session.select(job().id, true); assert.equal(state().detailPhase, "ready");
  assert.match(evaluationFailure(new ApiClientError("timeout")), /timed out/);
  assert.match(evaluationFailure(new ApiClientError("malformed")), /malformed/);
});
test("incomplete snapshots cannot be analyzed; complete recorded failures remain failures", () => {
  const data = result(); assert.equal(canAnalyze(data), true);
  data.status = "partial"; data.observed_run_count--; assert.equal(canAnalyze(data), false);
  data.observed_run_count++; data.status = "failed"; assert.equal(canAnalyze(data), true);
  data.result!.stopped_early = true; assert.equal(canAnalyze(data), false);
  data.result = null; assert.equal(canAnalyze(data), false);
});
for (const change of ["split", "cohort", "fingerprint", "retrieval", "runtime", "seed", "incomplete", "repeat"]) test(`comparison blocks incompatible ${change}`, () => {
  const a = job(), b = { ...job(), id: second };
  b.configuration = structuredClone(a.configuration);
  if (change === "split") b.configuration.split = "train";
  if (change === "cohort") b.configuration.question_ids = ["synthetic_dev_04"];
  if (change === "fingerprint") b.dataset_fingerprint = { bad: "hash" };
  if (change === "retrieval") b.configuration.retrieval = { method: "dense" };
  if (change === "runtime") b.runtime_source_sha256 = "different";
  if (change === "seed") b.configuration.random_seed = 5;
  if (change === "incomplete") b.observed_run_count = 0;
  assert.notEqual(comparisonBlocker(a, b, false), null);
});
test("different native threshold trials are provisional candidates only in threshold-only mode", () => {
  const a = job(), b = { ...job(), id: second, configuration: structuredClone(job().configuration) };
  const policies = b.configuration.policies as Record<string, unknown>[];
  policies.find(p => p.name === "threshold")!.threshold = 100;
  assert.notEqual(comparisonBlocker(a, b, false), null);
  assert.equal(comparisonBlocker(a, b, true), null);
});

test("identical saved thresholds remain disabled in both modes with an honest remedy", () => {
  const a = job(), b = { ...job(), id: second };
  for (const thresholdOnly of [false, true]) {
    const html = renderToStaticMarkup(<ComparisonCandidate selected={a} job={b} thresholdOnly={thresholdOnly} checked={false} limitReached={false} validated={false} onChange={() => {}} />);
    assert.match(html, /disabled=""/);
    assert.match(html, /Threshold trials only will not make this pair eligible/);
    assert.match(html, /repeated runs are not independent samples/);
    assert.match(html, new RegExp(`aria-describedby="comparison-${second}"`));
    assert.match(html, new RegExp(`id="comparison-${second}"`));
  }
});
test("distinct saved thresholds explain the setting and become selectable only in threshold mode", () => {
  const a = job(), b = { ...job(), id: second, configuration: structuredClone(job().configuration) };
  (b.configuration.policies as Record<string, unknown>[]).find(p => p.name === "threshold")!.threshold = 100;
  const render = (thresholdOnly: boolean) => renderToStaticMarkup(<ComparisonCandidate selected={a} job={b} thresholdOnly={thresholdOnly} checked={false} limitReached={false} validated={false} onChange={() => {}} />);
  assert.match(render(false), /disabled=""/); assert.match(render(false), /Enable Threshold trials only above/);
  assert.doesNotMatch(render(true), /disabled=""/); assert.match(render(true), /full R1 validation still required/);
});
test("repeated controls without threshold trials do not recommend an ineffective setting", () => {
  const a = job(), b = { ...job(), id: second, configuration: structuredClone(job().configuration) };
  b.configuration.policies = (b.configuration.policies as Record<string, unknown>[]).filter(p => p.name !== "threshold");
  assert.match(comparisonBlocker(a, b, false)!, /changing the analysis setting cannot resolve/);
  assert.match(comparisonBlocker(a, b, true)!, /unavailable/);
});
test("comparison selection limit has its own accessible explanation", () => {
  const a = job(), b = { ...job(), id: second, configuration: structuredClone(job().configuration) };
  (b.configuration.policies as Record<string, unknown>[]).find(p => p.name === "threshold")!.threshold = 100;
  const html = renderToStaticMarkup(<ComparisonCandidate selected={a} job={b} thresholdOnly checked={false} limitReached validated={false} onChange={() => {}} />);
  assert.match(html, /disabled=""/); assert.match(html, /Uncheck another candidate/);
});
