import assert from "node:assert/strict";
import { test } from "node:test";
import { spawnSync } from "node:child_process";
import { ApiClientError, backendOrigin, createApiClient, parseHealth, type HealthResponse } from "../lib/api";
import { checkSystemStatus } from "../lib/system-status";

const healthy: HealthResponse = {
  status: "ok", application: "RAGBench Studio", api_version: "0.1.0",
  runtime_initialized: true, generation_configured: true, provider_connection_tested: false,
};
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), {
  status, headers: { "Content-Type": "application/json" },
});

test("default URL and explicit local origins are normalized", () => {
  assert.equal(backendOrigin(), "http://127.0.0.1:8000");
  assert.equal(backendOrigin("http://localhost:9000/"), "http://localhost:9000");
  assert.equal(backendOrigin("http://[::1]:8000"), "http://[::1]:8000");
});

for (const value of ["", "https://example.com", "javascript:alert(1)",
  "http://private:secret@localhost:8000", "http://localhost:8000/api/v1",
  "http://localhost:8000?api_key=private", "http://localhost:8000/#secret"]) {
  test(`reject unsafe configuration ${value.split(":")[0] || "empty"}`, () => {
    assert.throws(() => backendOrigin(value), (error: unknown) =>
      error instanceof ApiClientError && error.failure.kind === "configuration" &&
      !error.message.includes("private:secret"));
  });
}

for (const [label, data] of [
  ["configured", healthy],
  ["unconfigured", { ...healthy, generation_configured: false }],
  ["degraded", { ...healthy, status: "degraded", runtime_initialized: false, generation_configured: false }],
] as const) {
  test(`read actual ${label} health contract`, async () => {
    let calls = 0;
    const client = createApiClient(undefined, { fetch: async (input, options) => {
      calls++;
      assert.equal(input, "http://127.0.0.1:8000/api/v1/health");
      assert.equal(options?.method, "GET");
      assert.equal(options?.credentials, "omit");
      assert.equal(options?.redirect, "error");
      assert.equal(options?.cache, "no-store");
      assert.equal(options?.body, undefined);
      return json(data);
    } });
    const state = await checkSystemStatus(client);
    assert.deepEqual(state, { phase: "ready", health: data });
    assert.equal(calls, 1);
  });
}

for (const payload of [null, [], {}, { ...healthy, runtime_initialized: "yes" },
  { ...healthy, provider_connection_tested: true }, { ...healthy, status: "healthy" },
  { ...healthy, expected_answer: "GOLD_SENTINEL" },
  { ...healthy, api_version: "<img src=x onerror=alert(1)>" },
  { ...healthy, application: "sk-proj-privatecredentialnotfordisplay" },
  { ...healthy, status: "degraded" },
]) {
  test("malformed or unexpected health fields are not trusted", () => {
    assert.throws(() => parseHealth(payload), ApiClientError);
  });
}

test("unreachable backend and raw network errors are safely normalized", async () => {
  const client = createApiClient(undefined, { fetch: async () => {
    throw new Error("private credentials and C:/private/path");
  } });
  const state = await checkSystemStatus(client);
  assert.deepEqual(state, { phase: "error", failure: { kind: "connection" } });
  assert.doesNotMatch(JSON.stringify(state), /credentials|private\/path/);
});

test("HTTP error envelopes never expose backend text or unknown codes", async () => {
  const client = createApiClient(undefined, { fetch: async () => json({ error: {
    code: "private-code", message: "server-only-secret", execution_status: null,
  } }, 503) });
  await assert.rejects(client.getHealth(), (error: unknown) =>
    error instanceof ApiClientError && error.failure.httpStatus === 503 &&
    !error.message.includes("server-only-secret") && !JSON.stringify(error).includes("private-code"));
});

test("malformed error envelopes and non-JSON responses fail safely", async () => {
  for (const response of [json({ detail: "private" }, 500),
    new Response("<script>private</script>", { headers: { "Content-Type": "text/html" } }),
    new Response("{broken", { headers: { "Content-Type": "application/json" } })]) {
    const state = await checkSystemStatus(createApiClient(undefined, { fetch: async () => response }));
    assert.deepEqual(state, { phase: "error", failure: { kind: "malformed" } });
  }
});

for (const contentType of [undefined, "text/html", "text/plain", "application/octet-stream"]) {
  test(`unsupported Content-Type ${contentType ?? "missing"} cancels body and aborts request`, async () => {
    let cancelled = 0;
    let requestSignal: AbortSignal | null | undefined;
    const body = new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new TextEncoder().encode("private body")); },
      cancel() { cancelled++; },
    });
    const client = createApiClient(undefined, { fetch: async (_input, options) => {
      requestSignal = options?.signal;
      return new Response(body, { headers: contentType ? { "Content-Type": contentType } : {} });
    } });
    await assert.rejects(client.getHealth(), (error: unknown) =>
      error instanceof ApiClientError && error.failure.kind === "malformed" &&
      !error.message.includes("private body"));
    assert.equal(cancelled, 1);
    assert.equal(body.locked, false);
    assert.equal(requestSignal?.aborted, true);
  });
}

test("body cancellation rejection is handled without masking the safe failure", async () => {
  const body = new ReadableStream<Uint8Array>({
    cancel() { return Promise.reject(new Error("private cleanup error")); },
  });
  const client = createApiClient(undefined, { fetch: async () =>
    new Response(body, { headers: { "Content-Type": "text/html" } }) });
  await assert.rejects(client.getHealth(), (error: unknown) =>
    error instanceof ApiClientError && error.failure.kind === "malformed" &&
    !error.message.includes("private cleanup error"));
  // Node's test runner fails on an unhandled rejection, including deferred ones.
  await new Promise<void>(resolve => setImmediate(resolve));
  assert.equal(body.locked, false);
});

test("a stalled cancellation cannot delay rejection or prevent request abort", async () => {
  let requestSignal: AbortSignal | null | undefined;
  const body = new ReadableStream<Uint8Array>({
    cancel() { return new Promise<void>(() => undefined); },
  });
  const client = createApiClient(undefined, { timeoutMs: 25, fetch: async (_input, options) => {
    requestSignal = options?.signal;
    return new Response(body, { headers: { "Content-Type": "text/html" } });
  } });
  await assert.rejects(client.getHealth(), (error: unknown) =>
    error instanceof ApiClientError && error.failure.kind === "malformed");
  assert.equal(requestSignal?.aborted, true);
  const reader = body.getReader();
  assert.equal((await reader.read()).done, true);
  reader.releaseLock();
});

for (const outcome of ["healthy", "unsupported", "malformed", "oversized", "unreachable", "timeout", "cancelled"] as const) {
  test(`${outcome} completion clears the deadline and releases its abort listener`, async context => {
    const scheduled = context.mock.method(globalThis, "setTimeout");
    const cleared = context.mock.method(globalThis, "clearTimeout");
    const caller = new AbortController();
    const added = context.mock.method(caller.signal, "addEventListener");
    const removed = context.mock.method(caller.signal, "removeEventListener");
    let requestSignal: AbortSignal | null | undefined;
    const timeoutMs = outcome === "timeout" ? 10 : 12_345;
    const client = createApiClient(undefined, { timeoutMs, fetch: async (_input, options) => {
      requestSignal = options?.signal;
      if (outcome === "timeout" || outcome === "cancelled") return new Promise<Response>(() => undefined);
      if (outcome === "unreachable") throw new Error("private network error");
      if (outcome === "unsupported") return new Response("private", { headers: { "Content-Type": "text/html" } });
      if (outcome === "malformed") return json({ wrong: true });
      if (outcome === "oversized") return json({ ...healthy, api_version: "x".repeat(16_385) });
      return json(healthy);
    } });
    const pending = client.getHealth(caller.signal);
    if (outcome === "cancelled") caller.abort();
    if (outcome === "healthy") assert.deepEqual(await pending, healthy);
    else await assert.rejects(pending, ApiClientError);
    const deadline = scheduled.mock.calls.find(call => call.arguments[1] === timeoutMs);
    assert.ok(deadline);
    assert.ok(cleared.mock.calls.some(call => call.arguments[0] === deadline.result));
    const listener = added.mock.calls.find(call => call.arguments[0] === "abort");
    assert.ok(listener);
    assert.ok(removed.mock.calls.some(call => call.arguments[0] === "abort" &&
      call.arguments[1] === listener.arguments[1]));
    assert.equal(requestSignal?.aborted, true);
    assert.equal(caller.signal.aborted, outcome === "cancelled");
  });
}

for (const reason of ["timeout", "cancelled"] as const) {
  test(`a response arriving after ${reason} is cancelled without a new read`, async () => {
    let finishFetch: ((response: Response) => void) | undefined;
    let cancelled = false;
    const caller = new AbortController();
    const client = createApiClient(undefined, { timeoutMs: 10,
      fetch: () => new Promise<Response>(resolve => { finishFetch = resolve; }) });
    const pending = client.getHealth(caller.signal);
    if (reason === "cancelled") caller.abort();
    await assert.rejects(pending, (error: unknown) =>
      error instanceof ApiClientError && error.failure.kind === reason);
    const body = new ReadableStream<Uint8Array>({ cancel() { cancelled = true; } });
    assert.ok(finishFetch);
    finishFetch(new Response(body, { headers: { "Content-Type": "application/json" } }));
    await new Promise<void>(resolve => setImmediate(resolve));
    assert.equal(cancelled, true);
    assert.equal(body.locked, false);
  });
}

test("timeout bounds a fetch that never resolves", async () => {
  const client = createApiClient(undefined, { timeoutMs: 10,
    fetch: () => new Promise<Response>(() => undefined) });
  await assert.rejects(client.getHealth(), (error: unknown) =>
    error instanceof ApiClientError && error.failure.kind === "timeout");
});

test("timeout also bounds and cancels a response body that stalls", async () => {
  let cancelled = false;
  const body = new ReadableStream<Uint8Array>({ cancel() { cancelled = true; } });
  const client = createApiClient(undefined, { timeoutMs: 10, fetch: async () =>
    new Response(body, { headers: { "Content-Type": "application/json" } }) });
  await assert.rejects(client.getHealth(), (error: unknown) =>
    error instanceof ApiClientError && error.failure.kind === "timeout");
  assert.equal(cancelled, true);
});

test("oversized response bytes are rejected and stream cancelled", async () => {
  let cancelled = false;
  const body = new ReadableStream<Uint8Array>({
    start(controller) { controller.enqueue(new Uint8Array(16_385)); },
    cancel() { cancelled = true; },
  });
  const client = createApiClient(undefined, { fetch: async () =>
    new Response(body, { headers: { "Content-Type": "application/json" } }) });
  await assert.rejects(client.getHealth(), (error: unknown) =>
    error instanceof ApiClientError && error.failure.kind === "malformed");
  assert.equal(cancelled, true);
});

test("caller cancellation is distinct from timeout and connection failure", async () => {
  const controller = new AbortController();
  const client = createApiClient(undefined, {
    fetch: () => new Promise<Response>(() => undefined) });
  const pending = client.getHealth(controller.signal);
  controller.abort("private reason");
  await assert.rejects(pending, (error: unknown) =>
    error instanceof ApiClientError && error.failure.kind === "cancelled" &&
    !error.message.includes("private reason"));
});

test("Next config rejects credential-bearing public URLs before bundling without reflecting them", () => {
  const canary = "synthetic-secret-do-not-bundle";
  const result = spawnSync(process.execPath, ["node_modules/next/dist/bin/next", "build"], {
    encoding: "utf-8", timeout: 15_000,
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1",
      NEXT_PUBLIC_RAGBENCH_API_BASE_URL: `http://user:${canary}@127.0.0.1:8000` },
  });
  assert.equal(result.status, 1);
  assert.match(result.stdout + result.stderr, /Invalid backend origin/);
  assert.doesNotMatch(result.stdout + result.stderr, new RegExp(canary));
});
