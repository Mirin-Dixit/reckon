import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { analysisFailure, createAnalysisClient, createAnalysisTask, parseAnalysis, type AnalysisReport } from "../lib/analysis-api";
import { ApiClientError } from "../lib/api";
import { AnalysisAction, AnalysisView, RiskAnalysis, RiskPlot } from "../components/risk-analysis";

const fixture = (): AnalysisReport => JSON.parse(readFileSync(resolve(process.cwd(), "tests/fixture_analysis.json"), "utf8"));
const id = fixture().rows[0].experiment_id;

test("actual backend analysis snapshot validates nested contracts and null tuple fields", () => {
  const data = fixture();
  assert.deepEqual(parseAnalysis(data), data);
  assert.equal(data.empirical_evaluation, false);
  assert.equal(data.matched_questions, 1);
  assert.equal(data.resampling_units, 1);
  assert.ok(data.rows.every(r => r.uncertainty.selective_risk.lower === null));
});

for (const change of ["version", "test", "empirical", "nan", "risk", "population", "duplicates", "replicates", "bounds", "gold", "metric", "fraction"]) {
  test(`reject malformed analysis: ${change}`, () => {
    const data = fixture();
    switch (change) {
      case "version": Object.assign(data, { schema_version: "future" }); break;
      case "test": Object.assign(data, { split: "test" }); break;
      case "empirical": Object.assign(data, { empirical_evaluation: true }); break;
      case "nan": data.rows[0].selective_risk = NaN; break;
      case "risk": data.rows[0].selective_risk = 2; break;
      case "population": data.matched_questions = 2; break;
      case "duplicates": data.rows.push(data.rows[0]); break;
      case "replicates": data.rows[0].uncertainty.selective_risk.valid_replicates++; break;
      case "bounds": data.rows[0].risk_bounds = [1,0]; break;
      case "gold": Object.assign(data.rows[0], { expected_answer: "must never be present" }); break;
      case "metric": Object.assign(data.rows[0].uncertainty, { unknown_metric: data.rows[0].uncertainty.selective_risk }); break;
      case "fraction": data.rows[0].end_to_end_coverage.value = 0; break;
    }
    assert.throws(() => parseAnalysis(data), ApiClientError);
  });
}

test("client uses GET, exact versioned route, bounded defaults and no credentials", async () => {
  let count = 0;
  const client = createAnalysisClient("http://127.0.0.1:8000", { fetch: async (url, init) => {
    count++;
    assert.equal(String(url), `http://127.0.0.1:8000/api/v1/experiments/${id}/analysis?resamples=2000&seed=0&lexical_proxy=true`);
    assert.equal(init?.method, "GET");
    assert.equal(init?.body, undefined);
    assert.equal(init?.credentials, "omit");
    assert.equal(init?.cache, "no-store");
    return Response.json(fixture());
  } });
  const report = await client.analyze(id, [], true);
  assert.equal(report.rows.length, 3);
  assert.equal(count, 1);
});

test("reject bad IDs, duplicate selections and excessive comparisons before fetch", async () => {
  let calls = 0;
  const client = createAnalysisClient(undefined, { fetch: async () => { calls++; return Response.json({}); } });
  await assert.rejects(client.analyze("../secret", [], false), ApiClientError);
  await assert.rejects(client.analyze(id, [id], false), ApiClientError);
  await assert.rejects(client.analyze(id, [id,id,id,id], false), ApiClientError);
  assert.equal(calls, 0);
});

test("reject mismatched experiment identity", async () => {
  const client = createAnalysisClient(undefined, { fetch: async () => Response.json(fixture()) });
  await assert.rejects(client.analyze("00000000-0000-0000-0000-000000000000", [], false), ApiClientError);
});

test("timeout and cancellation safely discard late analysis results", async () => {
  const client = createAnalysisClient(undefined, { timeoutMs: 5, fetch: () => new Promise(() => {}) });
  await assert.rejects(client.analyze(id, [], true), e => e instanceof ApiClientError && e.failure.kind === "timeout");
  const controller = new AbortController();
  const pending = createAnalysisClient(undefined, { fetch: () => new Promise(() => {}) }).analyze(id, [], true, controller.signal);
  controller.abort();
  await assert.rejects(pending, e => e instanceof ApiClientError && e.failure.kind === "cancelled");
  const task = createAnalysisTask();
  const first = task.begin(), second = task.begin();
  assert.equal(first.signal.aborted, true);
  assert.equal(task.accepts(first), false);
  assert.equal(task.accepts(second), true);
  task.cancel();
  assert.equal(second.signal.aborted, true);
  assert.equal(task.accepts(second), false);
});

test("bounded reads and unsupported response types remain rejected", async () => {
  for (const response of [new Response("x".repeat(1_048_577), { headers: { "Content-Type": "application/json" } }), new Response("<html>secret</html>", { headers: { "Content-Type": "text/html" } })]) {
    const client = createAnalysisClient(undefined, { fetch: async () => response });
    await assert.rejects(client.analyze(id, [], true), ApiClientError);
  }
});

test("safe network/backend errors never reflect raw exception or envelope text", async () => {
  for (const status of [404,422,503]) {
    const client = createAnalysisClient(undefined, { fetch: async () => Response.json({ error: { code: "secret", message: "SECRET_BACKEND_STACK", execution_status: null } }, { status }) });
    try { await client.analyze(id, [], true); assert.fail("must reject"); }
    catch (e) { assert.ok(!analysisFailure(e).includes("SECRET_BACKEND_STACK")); }
  }
  assert.ok(!analysisFailure(new Error("SECRET_BACKEND_STACK")).includes("SECRET_BACKEND_STACK"));
});

test("initial section is accessible and does not auto-run analysis or inference", () => {
  const html = renderToStaticMarkup(<RiskAnalysis experimentId={id} />);
  assert.match(html, /Risk–Coverage analysis/);
  assert.match(html, /for="analysis-compare"/);
  assert.match(html, /aria-describedby="analysis-help"/);
  assert.match(html, /Analyze saved observations/);
  assert.match(html, /No analysis loaded/);
  assert.match(html, /no model calls/);
  assert.doesNotMatch(html, /<canvas|<iframe|<script/);
});

test("view separates loading, errors, cancellation and empty states", () => {
  assert.match(renderToStaticMarkup(<AnalysisView report={null} loading />), /role="status"/);
  assert.match(renderToStaticMarkup(<AnalysisView report={null} error="Cannot analyze" />), /role="alert"/);
  assert.match(renderToStaticMarkup(<AnalysisView report={null} cancelled />), /Saved experiments are unchanged/);
  assert.match(renderToStaticMarkup(<AnalysisView report={null} />), /No analysis loaded/);
});

test("view discloses paired sample sizes, denominators, proxy risk and undefined AURC", () => {
  const html = renderToStaticMarkup(<AnalysisView report={fixture()} onExport={() => {}} />);
  for (const text of ["matched questions", "resampling units", "A/N", "A/(A+B+C)", "not verified semantic correctness", "Interval unavailable", "not a fitted confidence curve", "Area undefined", "Export analysis JSON", "Left minus right"]) assert.ok(html.includes(text), text);
  assert.match(html, /scope="col"/);
  assert.match(html, /scope="row"/);
  assert.match(html, /role="img"/);
});

test("unknown judgments do not become zero-risk SVG points", () => {
  const data = fixture();
  data.rows.forEach(r => { r.selective_risk = null; });
  const html = renderToStaticMarkup(<RiskPlot report={data} />);
  assert.match(html, /No defined risk points/);
  assert.doesNotMatch(html, /<circle/);
});

test("untrusted limitation text renders as escaped text, not HTML or links", () => {
  const data = fixture();
  data.limitations = ["<img src=x onerror=alert(1)>"];
  const html = renderToStaticMarkup(<AnalysisView report={data} />);
  assert.match(html, /&lt;img/);
  assert.doesNotMatch(html, /<img|onerror="|href="https/);
});

test("JSON analysis export contains no benchmark labels or reference answers", () => {
  const data = parseAnalysis(fixture());
  const payload = JSON.stringify(data, null, 2);
  assert.deepEqual(JSON.parse(payload), data);
  assert.doesNotMatch(payload, /expected_answer|expected_safe_behavior|evidence_spans|reference_answer/);
});

test("actual native threshold curve validates, renders right-step lines and full AURC", () => {
  const report = parseAnalysis(JSON.parse(readFileSync(resolve(process.cwd(), "tests/fixture_analysis_curve.json"), "utf8")));
  assert.equal(report.curves[0].area.coverage_bounds?.[0], 0);
  assert.equal(report.curves[0].area.coverage_bounds?.[1], 1);
  assert.ok(report.curves[0].area.full_aurc !== null);
  const html = renderToStaticMarkup(<AnalysisView report={report} />);
  assert.match(html, /Full AURC/);
  assert.match(html, /Coverage domain: \[0.000, 1.000\]/);
  assert.match(html, /stroke-width="1.5"/);
  assert.match(html, /Scrollable synthetic risk–coverage chart/);
  assert.match(html, /tabindex="0"/);
});

test("reject invented curve area and inconsistent paired differences", () => {
  const curve: AnalysisReport = JSON.parse(readFileSync(resolve(process.cwd(), "tests/fixture_analysis_curve.json"), "utf8"));
  curve.curves[0].area.full_aurc = 0;
  assert.throws(() => parseAnalysis(curve), ApiClientError);
  const report = fixture();
  report.comparisons[0].uncertainty.end_to_end_coverage.estimate = 1;
  assert.throws(() => parseAnalysis(report), ApiClientError);
});

test("partial-domain and unavailable uncertainty have explicit presentation", () => {
  const report = fixture();
  report.curves[0].area = { schema_version: "ragbench.risk-coverage.v1", axis: "end_to_end_coverage", rule: "right_step", full_aurc: null, partial_aurc: .125, coverage_bounds: [.25,.75], undefined_reason: null };
  const html = renderToStaticMarkup(<AnalysisView report={report} />);
  assert.match(html, /Partial area 0.125/);
  assert.match(html, /Coverage domain: \[0.250, 0.750\]/);
  assert.match(html, /Interval unavailable/);
  assert.doesNotMatch(html, /Full AURC/);
});

test("client rejects unexpected loss basis or bootstrap configuration", async () => {
  const client = createAnalysisClient(undefined, { fetch: async () => Response.json(fixture()) });
  await assert.rejects(client.analyze(id, [], false), ApiClientError);
  const changed = fixture(); changed.seed = 99;
  await assert.rejects(createAnalysisClient(undefined, { fetch: async () => Response.json(changed) }).analyze(id, [], true), ApiClientError);
});

test("threshold-only selection is explicit and validated against the actual curve response", async () => {
  const report: AnalysisReport = JSON.parse(readFileSync(resolve(process.cwd(), "tests/fixture_analysis_curve.json"), "utf8"));
  const sources = [...new Set(report.rows.map(r => r.experiment_id))];
  const client = createAnalysisClient(undefined, { fetch: async url => {
    assert.match(String(url), /&threshold_only=true&compare=/);
    return Response.json(report);
  } });
  assert.equal((await client.analyze(sources[0], sources.slice(1), true, undefined, true)).curves.length, 1);
});

test("analysis form separates selection, settings, action and results with labeled optional controls", () => {
  const html = renderToStaticMarkup(<RiskAnalysis experimentId={id} />);
  assert.match(html, /class="analysis-label">Synthetic only/);
  assert.match(html, /<legend>Experiment selection<\/legend>/);
  assert.match(html, /<legend>Analysis settings<\/legend>/);
  assert.match(html, /<h4>Run analysis<\/h4>/);
  assert.match(html, /<h4 id="analysis-results-heading">Analysis results<\/h4>/);
  assert.match(html, /placeholder="Paste experiment IDs, separated by commas"/);
  assert.match(html, /Leave empty to analyze this experiment only/);
  const input = html.match(/<input[^>]*id="analysis-compare"[^>]*>/)?.[0];
  assert.ok(input);
  assert.doesNotMatch(input, /required|disabled/);
  assert.match(input, /value=""/);
  assert.match(html, /for="analysis-proxy"/);
  assert.match(html, /for="analysis-threshold"/);
  assert.match(html, /id="analysis-proxy"[^>]*aria-describedby="analysis-proxy-help"[^>]*checked/);
  assert.match(html, /id="analysis-threshold"[^>]*aria-describedby="analysis-threshold-help"/);
  assert.equal((html.match(/class="analysis-option"/g) ?? []).length, 2);
  assert.match(html, /Synthetic development only/);
});

test("analysis action exposes loading, disabled, cancellation and error association", () => {
  const idle = renderToStaticMarkup(<AnalysisAction loading={false} error="" onCancel={() => {}} />);
  assert.match(idle, /Analyze saved observations/);
  assert.doesNotMatch(idle, /disabled|Cancel analysis/);
  const loading = renderToStaticMarkup(<AnalysisAction loading error="" onCancel={() => {}} />);
  assert.match(loading, /disabled="" aria-busy="true"/);
  assert.match(loading, /Analyzing saved observations…/);
  assert.match(loading, /type="button">Cancel analysis/);
  const error = renderToStaticMarkup(<AnalysisAction loading={false} error="Failed" onCancel={() => {}} />);
  assert.match(error, /aria-describedby="analysis-error"/);
  const alert = renderToStaticMarkup(<AnalysisView report={null} error="Failed" />);
  assert.match(alert, /class="analysis-error" id="analysis-error" role="alert"/);
});

test("analysis styles define input boundaries, separate checkbox rows, focus and mobile actions", () => {
  const css = readFileSync(resolve(process.cwd(), "app/globals.css"), "utf8");
  assert.match(css, /\.risk-analysis input\[type="text"\][^}]*border: 1px solid var\(--muted\)[^}]*padding: 12px 14px/);
  assert.match(css, /\.risk-analysis \.analysis-option\s*\{[^}]*display: grid;[^}]*grid-template-columns: 20px minmax\(0, 1fr\)/);
  assert.match(css, /\.risk-analysis :is\(input, button\):focus-visible[^}]*outline: 2px solid var\(--accent\)/);
  assert.match(css, /\.risk-analysis \.analysis-results[^}]*border-top: 1px solid var\(--stone\)/);
  assert.match(css, /@media \(max-width: 600px\)[\s\S]*\.analysis-action \.query-actions[^}]*flex-direction: column/);
});
