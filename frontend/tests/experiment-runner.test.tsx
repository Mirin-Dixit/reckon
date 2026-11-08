import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { test } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import { Children, isValidElement, type ReactNode, type ReactElement } from "react";
import {
  buildExperiment,
  createExperimentClient,
  experimentFailure,
  notice,
  parseJob,
  parseResults,
  type Freeze,
  type Job,
  type Results,
} from "../lib/experiment-api";
import { ApiClientError } from "../lib/api";
import { createMutationGate, downloadJson } from "../lib/workspace-actions";
import { ExperimentRunner, ExperimentResults, ExperimentHistory, ExperimentDetail, ExperimentStatusOverview, nextExperimentSelection } from "../components/experiment-runner";

const fixturePath = resolve(process.cwd(), "tests/fixture_job_result.json");
const validResults: Results = JSON.parse(readFileSync(fixturePath, "utf-8"));

const validJob: Job = {
  schema_version: validResults.schema_version,
  id: validResults.id,
  status: validResults.status,
  notice: validResults.notice,
  empirical_evaluation: validResults.empirical_evaluation,
  created_at: validResults.created_at,
  updated_at: validResults.updated_at,
  expected_run_count: validResults.expected_run_count,
  observed_run_count: validResults.observed_run_count,
  configuration: validResults.configuration,
  dataset_fingerprint: validResults.dataset_fingerprint,
  runtime_source_sha256: validResults.runtime_source_sha256,
  error: validResults.error,
};

test("notice constant matches exact approved synthetic disclosure", () => {
  assert.equal(notice, "Synthetic fixture — development only; no empirical claims.");
});

test("buildExperiment generates valid configurations across methods and policies", () => {
  const bm25All = buildExperiment("dev", "bm25", "all", "0.5", "42", "", "5", false);
  assert.equal(bm25All.split, "dev");
  assert.equal(bm25All.random_seed, 42);
  assert.equal(bm25All.retrieval.method, "bm25");
  assert.equal(bm25All.retrieval.top_k, 5);
  assert.equal(bm25All.policies.length, 3);
  assert.deepEqual(
    bm25All.policies.map(p => p.name),
    ["always_answer", "prompt_abstention", "threshold"],
  );
  const thresholdPolicy = bm25All.policies.find(p => p.name === "threshold");
  assert.equal(thresholdPolicy?.threshold, 0.5);
  assert.equal(thresholdPolicy?.score_type, "bm25");
  assert.equal(thresholdPolicy?.direction, "at_least");

  const hybridTrain = buildExperiment(
    "train",
    "hybrid",
    "threshold",
    "0.02",
    "0",
    "synthetic_train_01, synthetic_train_02",
    "3",
    true,
  );
  assert.equal(hybridTrain.split, "train");
  assert.equal(hybridTrain.retrieval.method, "hybrid");
  assert.equal(hybridTrain.retrieval.rrf_k, 60);
  assert.equal(hybridTrain.retrieval.candidate_k, 50);
  assert.deepEqual(hybridTrain.question_ids, ["synthetic_train_01", "synthetic_train_02"]);
  assert.equal(hybridTrain.fail_fast, true);
  const hybridThreshold = hybridTrain.policies[0];
  assert.equal(hybridThreshold.score_type, "hybrid_rrf");

  const dense = buildExperiment("dev", "dense", "always_answer", "0", "1", "", "10", false);
  assert.equal(dense.retrieval.method, "dense");
  assert.equal(dense.policies[0].name, "always_answer");
});

test("buildExperiment rejects invalid inputs and split leakage", () => {
  assert.throws(
    () => buildExperiment("test", "bm25", "all", "0", "0", "", "3", false),
    /valid fixture settings/,
  );
  assert.throws(
    () => buildExperiment("pilot30", "bm25", "all", "0", "0", "", "3", false),
    /valid fixture settings/,
  );
  assert.throws(
    () => buildExperiment("dev", "bm25", "all", "not-a-number", "0", "", "3", false),
    /Threshold must be finite/,
  );
  assert.throws(
    () => buildExperiment("dev", "bm25", "all", "0", "not-a-seed", "", "3", false),
    /Seed must be a safe integer/,
  );
  assert.throws(
    () => buildExperiment("dev", "bm25", "all", "0", "0", "", "0", false),
    /Top-k must be an integer from 1 to 20/,
  );
  assert.throws(
    () => buildExperiment("dev", "bm25", "all", "0", "0", "", "25", false),
    /Top-k must be an integer from 1 to 20/,
  );
  assert.throws(
    () => buildExperiment("dev", "bm25", "all", "0", "0", "synthetic_train_01", "3", false),
    /Use distinct question IDs from the selected fixture split/,
  );
  assert.throws(
    () => buildExperiment("dev", "bm25", "all", "0", "0", "synthetic_dev_01, synthetic_dev_01", "3", false),
    /Use distinct question IDs from the selected fixture split/,
  );
  assert.throws(
    () => buildExperiment("dev", "bm25", "all", "0", "0", "py311v2_dev_001", "3", false),
    /Use distinct question IDs from the selected fixture split/,
  );
});

test("parseJob validates structure and rejects invalid state combinations", () => {
  const parsed = parseJob(validJob);
  assert.equal(parsed.id, validJob.id);
  assert.equal(parsed.status, "done");
  assert.equal(parsed.empirical_evaluation, false);

  assert.throws(() => parseJob({ ...validJob, id: "not-a-uuid" }), ApiClientError);
  assert.throws(() => parseJob({ ...validJob, observed_run_count: 15 }), ApiClientError);
  assert.throws(
    () => parseJob({ ...validJob, status: "done", observed_run_count: 10 }),
    ApiClientError,
  );
  assert.throws(
    () => parseJob({ ...validJob, status: "done", error: "some_error" }),
    ApiClientError,
  );
});

test("parseResults validates observations consistency", () => {
  const parsed = parseResults(validResults);
  assert.equal(parsed.observations.length, 3);
  assert.equal(parsed.status, "done");

  // Count mismatch
  assert.throws(
    () => parseResults({ ...validResults, observed_run_count: 2 }),
    ApiClientError,
  );

  // Done with observation failure
  const badObservation = {
    ...validResults.observations[0],
    error: { kind: "execution_failure", message: "fail", retryable: false },
  };
  const doneWithFailure: Results = {
    ...validResults,
    observations: [badObservation, ...validResults.observations.slice(1)],
  };
  assert.throws(() => parseResults(doneWithFailure), ApiClientError);
});

test("experimentFailure formats clear and safe error messages", () => {
  const err429 = new ApiClientError("http", 429);
  assert.match(experimentFailure(err429), /Queue is full/);

  const err409 = new ApiClientError("http", 409);
  assert.match(experimentFailure(err409), /Only a fully successful Dev job can be frozen/);

  const err503 = new ApiClientError("http", 503);
  assert.match(experimentFailure(err503), /Experiment storage or worker is unavailable/);

  const errMalformed = new ApiClientError("malformed");
  assert.match(experimentFailure(errMalformed), /inconsistent or malformed/);

  const generic = new Error("network reset");
  assert.match(experimentFailure(generic), /Experiment request failed/);
});

test("createExperimentClient executes list, start, results, and freeze calls", async () => {
  const calls: { url: string; method: string; body?: unknown }[] = [];
  const mockFetch: typeof fetch = async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ url, method, body });

    if (url.endsWith("/experiments?limit=50&offset=0")) {
      return new Response(JSON.stringify({ jobs: [validJob] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.endsWith("/experiments") && method === "POST") {
      return new Response(JSON.stringify(validJob), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.includes("/results")) {
      return new Response(JSON.stringify(validResults), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.includes("/freeze")) {
      const freezePayload: Freeze = {
        schema_version: "ragbench.dev-freeze.v1",
        job_id: validJob.id,
        sha256: "abcdef123456",
        empirical_evaluation: false,
        notice,
        created_at: "2026-11-04T12:05:00Z",
        configuration: validJob.configuration,
        dataset_fingerprint: validJob.dataset_fingerprint,
        software_metadata: { project_version: "0.1.0" },
        generation_configuration: { provider: "synthetic" },
      };
      return new Response(JSON.stringify(freezePayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response("Not found", { status: 404 });
  };

  const client = createExperimentClient("http://127.0.0.1:8000", { fetch: mockFetch });
  const list = await client.list();
  assert.equal(list.length, 1);
  assert.equal(list[0].id, validJob.id);

  const started = await client.start({ split: "dev" });
  assert.equal(started.id, validJob.id);

  const results = await client.results(validJob.id);
  assert.equal(results.id, validJob.id);
  assert.equal(results.observations.length, 3);

  const frozen = await client.freeze(validJob.id);
  assert.equal(frozen.job_id, validJob.id);
  assert.equal(frozen.sha256, "abcdef123456");

  assert.equal(calls.length, 4);
  assert.equal(calls[0].method, "GET");
  assert.equal(calls[1].method, "POST");
  assert.equal(calls[2].method, "GET");
  assert.equal(calls[3].method, "POST");
});

test("ExperimentResults renders exact notice, provenance, and outcome table", () => {
  const html = renderToStaticMarkup(<ExperimentResults value={validResults} />);
  assert.match(html, /Synthetic fixture — development only; no empirical claims\./);
  assert.match(html, /Status: <strong>done<\/strong>/);
  assert.match(html, /Failures are separate from abstentions\./);
  assert.match(html, new RegExp(validResults.id));
  assert.match(html, new RegExp(validResults.runtime_source_sha256));

  assert.match(html, /synthetic_dev_01/);
  assert.match(html, /always_answer/);
  assert.match(html, /ANSWER/);
});

test("ExperimentRunner renders configuration controls and deferred empirical disclaimers", () => {
  const html = renderToStaticMarkup(<ExperimentRunner />);
  assert.match(html, /<h1 id="experiments-title">Experiments<\/h1>/);
  assert.match(html, /Synthetic fixture — development only; no empirical claims\./);
  assert.match(
    html,
    /Pilot30 and full benchmark review are deferred\. Empirical execution and held-out evaluation are blocked\./,
  );
  assert.match(html, /p4-synthetic\.v1 \/ fictional inventory ledger/);
  assert.match(html, /fixture-rules\.v1 \/ no model inference/);
  assert.match(html, /Synthetic Train/);
  assert.match(html, /Synthetic Dev/);
  assert.match(html, /BM25/);
  assert.match(html, /Dense \/ token hash fixture/);
  assert.match(html, /Hybrid \/ RRF/);
  assert.match(html, /All three policies/);
  assert.match(html, /Always answer/);
  assert.match(html, /Prompt abstention \/ fixture rules/);
  assert.match(html, /Retrieval threshold/);
  assert.match(html, /Stop after the first execution failure/);
  assert.match(html, /Run synthetic experiment/);
  assert.match(html, /Experiment history/);
  assert.match(html, /Results survive a backend restart/);
});

function buttons(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  return Children.toArray(node).flatMap(child => {
    if (!isValidElement<{ children?: ReactNode }>(child)) return [];
    return [...(child.type === "button" ? [child as ReactElement<Record<string, unknown>>] : []), ...buttons(child.props.children)];
  });
}

const detailProps = () => ({
  result: validResults, loading: false, error: "", busy: false, freeze: null,
  onRetry: () => {}, onFreeze: () => {}, onExport: () => {},
});

test("history buttons select their exact ID and repeated selections invalidate the request", () => {
  const second = { ...validJob, id: "11111111-1111-4111-8111-111111111111" };
  let selection = { id: validJob.id, revision: 0 };
  const tree = ExperimentHistory({ jobs: [validJob, second], selected: selection.id, busy: false,
    onSelect: id => { selection = nextExperimentSelection(selection, id); } });
  const entries = buttons(tree);
  assert.equal(entries.length, 2);
  assert.equal(entries[0].props["aria-pressed"], true);
  assert.equal(entries[0].props["aria-controls"], "selected-experiment");
  for (const index of [0, 0, 1]) {
    const click = entries[index].props.onClick;
    assert.equal(typeof click, "function");
    if (typeof click === "function") click();
  }
  assert.deepEqual(selection, { id: second.id, revision: 3 });
  assert.match(renderToStaticMarkup(tree), /View saved results/);
});

for (const state of [
  { loading: true, error: "", text: /Loading saved experiment results/ },
  { loading: false, error: "", text: /No saved experiment selected/ },
  { loading: false, error: "Saved results unavailable <script>unsafe</script>", text: /Retry loading results/ },
]) test(`selected results has an explicit ${state.loading ? "loading" : state.error ? "error" : "empty"} state`, () => {
  const html = renderToStaticMarkup(<ExperimentDetail {...detailProps()} result={null} loading={state.loading} error={state.error} />);
  assert.match(html, /id="selected-experiment"/);
  assert.match(html, state.text);
  assert.doesNotMatch(html, /Export synthetic result JSON|Freeze this Dev configuration|<script>/);
});

test("result retry is a read action and controls export the selected record", () => {
  let retries = 0, freezes = 0;
  const exports: { value: unknown; filename: string }[] = [];
  const errorButtons = buttons(ExperimentDetail({ ...detailProps(), result: null, error: "Unavailable",
    onRetry: () => { retries++; } }));
  const retry = errorButtons[0].props.onClick;
  if (typeof retry === "function") retry();
  assert.equal(retries, 1);
  const tree = ExperimentDetail({ ...detailProps(), onFreeze: () => { freezes++; },
    onExport: (value, filename) => { exports.push({ value, filename }); } });
  const controls = buttons(tree);
  for (const control of controls.slice(0, 2)) {
    const click = control.props.onClick;
    if (typeof click === "function") click();
  }
  assert.equal(freezes, 1);
  assert.deepEqual(exports, [{ value: validResults, filename: `synthetic-${validResults.id}.json` }]);
  const html = renderToStaticMarkup(tree);
  assert.ok(html.indexOf("Export synthetic result JSON") < html.indexOf("Recorded observations"));
  assert.match(html, /Effective configuration and provenance/);
  assert.match(html, /generation|software/);
});

for (const [split, status, busy, disabled] of [
  ["dev", "done", false, false], ["train", "done", false, true],
  ["dev", "partial", false, true], ["dev", "running", false, true],
  ["dev", "failed", false, true], ["dev", "done", true, true],
] as const) test(`freeze eligibility: ${split}/${status}, busy=${busy}`, () => {
  const result = { ...validResults, status, configuration: { ...validResults.configuration, split } };
  const tree = ExperimentDetail({ ...detailProps(), result, busy });
  assert.equal(buttons(tree)[1].props.disabled, disabled);
});

test("freeze receipts only appear for their matching result and failures remain visible", () => {
  const freeze: Freeze = { schema_version: "ragbench.dev-freeze.v1", job_id: validResults.id,
    sha256: "a".repeat(64), empirical_evaluation: false, notice, created_at: validResults.created_at,
    configuration: validResults.configuration, dataset_fingerprint: validResults.dataset_fingerprint,
    software_metadata: {}, generation_configuration: {} };
  const html = renderToStaticMarkup(<ExperimentDetail {...detailProps()} freeze={freeze} />);
  assert.match(html, /Export freeze JSON/);
  const other = renderToStaticMarkup(<ExperimentDetail {...detailProps()} freeze={{ ...freeze, job_id: "other-job" }} actionError="Freeze was rejected." />);
  assert.doesNotMatch(other, /Export freeze JSON/);
  assert.match(other, /role="alert">Freeze was rejected/);
});

test("recorded execution errors are text and remain distinct from abstentions", () => {
  const error = { kind: "fixture_failure", message: "<script>not HTML</script>", retryable: false };
  const value: Results = { ...validResults, status: "partial", observations: [{ ...validResults.observations[0], error,
    observed: { ...validResults.observations[0].observed, decision: null, answer: null, execution_status: "failed" } }] };
  const html = renderToStaticMarkup(<ExperimentResults value={value} />);
  assert.match(html, /Recorded error|fixture_failure/);
  assert.match(html, /No decision/);
  assert.doesNotMatch(html, /<script>/);
});

test("results and freeze responses cannot silently refer to another selected experiment", async () => {
  const requested = "11111111-1111-4111-8111-111111111111";
  const client = createExperimentClient(undefined, { fetch: async () => new Response(JSON.stringify(validResults), {
    status: 200, headers: { "Content-Type": "application/json" },
  }) });
  await assert.rejects(client.results(requested), ApiClientError);
  const freeze: Freeze = { schema_version: "ragbench.dev-freeze.v1", job_id: validResults.id,
    sha256: "a".repeat(64), empirical_evaluation: false, notice, created_at: validResults.created_at,
    configuration: {}, dataset_fingerprint: {}, software_metadata: {}, generation_configuration: {} };
  const freezeClient = createExperimentClient(undefined, { fetch: async () => new Response(JSON.stringify(freeze), {
    status: 200, headers: { "Content-Type": "application/json" },
  }) });
  await assert.rejects(freezeClient.freeze(requested), ApiClientError);
});

test("aborted old result requests cannot win over a newer selection", async () => {
  let release: (() => void) | undefined;
  const gate = new Promise<void>(resolve => { release = resolve; });
  const nextId = "11111111-1111-4111-8111-111111111111";
  const next: Results = { ...validResults, id: nextId, result: { ...validResults.result!, experiment_id: nextId } };
  const client = createExperimentClient(undefined, { fetch: async input => {
    const isOld = String(input).includes(validResults.id);
    if (isOld) await gate;
    return new Response(JSON.stringify(isOld ? validResults : next), { status: 200, headers: { "Content-Type": "application/json" } });
  } });
  const old = new AbortController();
  const oldRequest = assert.rejects(client.results(validResults.id, old.signal), (e: unknown) => e instanceof ApiClientError && e.failure.kind === "cancelled");
  old.abort();
  assert.equal((await client.results(nextId)).id, nextId);
  release?.();
  await oldRequest;
});

test("mutation gate rejects same-tick reentry and releases after a failure", async () => {
  const gate = createMutationGate();
  assert.equal(gate.enter(), true);
  assert.equal(gate.enter(), false);
  assert.equal(gate.enter(), false);
  try { throw new Error("simulated failure"); } catch { /* caller shows safe error */ }
  finally { gate.leave(); }
  assert.equal(gate.enter(), true);
  gate.leave();
});

test("JSON export preserves data and releases the URL after browser handoff", async t => {
  const oldDocument = Object.getOwnPropertyDescriptor(globalThis, "document");
  let blob: Blob | undefined;
  let clicked = 0;
  const revoked: string[] = [];
  const link = { href: "", download: "", click: () => { clicked++; } };
  t.mock.method(URL, "createObjectURL", (value: Blob) => { blob = value; return "blob:export-test"; });
  t.mock.method(URL, "revokeObjectURL", (url: string) => { revoked.push(url); });
  Object.defineProperty(globalThis, "document", { configurable: true, value: { createElement: (tag: string) => { assert.equal(tag, "a"); return link; } } });
  try {
    downloadJson({ label: "evidence 😀", score: null }, "synthetic-result.json");
    assert.equal(clicked, 1);
    assert.equal(link.download, "synthetic-result.json");
    assert.equal(link.href, "blob:export-test");
    assert.deepEqual(JSON.parse(await blob!.text()), { label: "evidence 😀", score: null });
    await new Promise(resolve => setTimeout(resolve, 10));
    assert.deepEqual(revoked, ["blob:export-test"]);
  } finally {
    if (oldDocument) Object.defineProperty(globalThis, "document", oldDocument);
    else Reflect.deleteProperty(globalThis, "document");
  }
});

test("failed download handoff still releases its temporary resource", async t => {
  const oldDocument = Object.getOwnPropertyDescriptor(globalThis, "document");
  const revoked: string[] = [];
  t.mock.method(URL, "createObjectURL", () => "blob:failed-export");
  t.mock.method(URL, "revokeObjectURL", (url: string) => { revoked.push(url); });
  Object.defineProperty(globalThis, "document", { configurable: true, value: { createElement: () => ({ click() { throw new Error("blocked"); } }) } });
  try {
    assert.throws(() => downloadJson({}, "synthetic.json"));
    await new Promise(resolve => setTimeout(resolve, 10));
    assert.deepEqual(revoked, ["blob:failed-export"]);
  } finally {
    if (oldDocument) Object.defineProperty(globalThis, "document", oldDocument);
    else Reflect.deleteProperty(globalThis, "document");
  }
});

test("history progress, scroll regions and export feedback use actual saved state", () => {
  const history = renderToStaticMarkup(<ExperimentHistory jobs={[validJob]} selected={validJob.id} busy={false} onSelect={() => {}} />);
  assert.match(history, /<progress value="3" max="3"/);
  assert.match(history, /aria-label="3 of 3 observations saved"/);
  const detail = renderToStaticMarkup(<ExperimentDetail result={validResults} loading={false} error="" busy freezing freeze={null} exportFeedback={{ message: "JSON export prepared. Check your browser downloads.", failed: false }} onRetry={() => {}} onFreeze={() => {}} onExport={() => {}} />);
  assert.match(detail, /Freezing Dev configuration…/);
  assert.match(detail, /role="status">JSON export prepared/);
  assert.match(detail, /role="region" aria-label="Synthetic per-question results" tabindex="0"/);
});

test("shared research controls remain visible, responsive and reduced-motion safe", () => {
  const css = readFileSync(resolve(process.cwd(), "app/globals.css"), "utf8");
  assert.match(css, /Shared application controls and research-ledger rhythm/);
  assert.match(css, /\.query-lab button:not\(\.check-button\)[^}]*min-height: 44px/);
  assert.match(css, /\.query-lab :is\(input, select, textarea, button\):focus-visible[^}]*outline: 2px solid var\(--accent\)/);
  assert.match(css, /@media \(max-width: 1200px\) and \(min-width: 601px\)/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)[\s\S]*transition: none/);
  assert.match(css, /experiment-history progress[^}]*accent-color: var\(--accent\)/);
});

test("experiment status overview visualizes real persisted job counts with proportional meter and accessibility", () => {
  const sampleJobs: Job[] = [
    { ...validJob, id: "00000000-0000-0000-0000-000000000001", status: "done" },
    { ...validJob, id: "00000000-0000-0000-0000-000000000002", status: "running" },
    { ...validJob, id: "00000000-0000-0000-0000-000000000003", status: "queued" },
    { ...validJob, id: "00000000-0000-0000-0000-000000000004", status: "failed" },
  ];
  const html = renderToStaticMarkup(<ExperimentStatusOverview jobs={sampleJobs} />);
  assert.match(html, /class="experiment-status-overview"/);
  assert.match(html, /Saved run cohort \(4 total\)/);
  assert.match(html, /Completed<\/span><span class="status-chip-count">1 <small>\(25%\)<\/small><\/span>/);
  assert.match(html, /Running<\/span><span class="status-chip-count">1 <small>\(25%\)<\/small><\/span>/);
  assert.match(html, /Queued<\/span><span class="status-chip-count">1 <small>\(25%\)<\/small><\/span>/);
  assert.match(html, /Failed \/ Partial<\/span><span class="status-chip-count">1 <small>\(25%\)<\/small><\/span>/);
  assert.match(html, /role="img" aria-label="Status breakdown: 1 completed \(25%\), 1 running \(25%\), 1 queued \(25%\), 1 failed \(25%\)"/);

  // Empty state test
  const emptyHtml = renderToStaticMarkup(<ExperimentStatusOverview jobs={[]} />);
  assert.match(emptyHtml, /class="experiment-status-overview is-empty"/);
  assert.match(emptyHtml, /No saved experiments recorded on this page/);
});
