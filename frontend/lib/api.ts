/** Bounded, loopback-only JSON transport shared by health and query operations. */
import { localBackendOrigin } from "./configuration";

export interface HealthResponse {
  status: "ok" | "degraded";
  application: "RAGBench Studio";
  api_version: string;
  runtime_initialized: boolean;
  generation_configured: boolean;
  provider_connection_tested: false;
}

type ExecutionStatus = "succeeded" | "failed" | "timed_out" | "refused" | "incomplete";

export interface BackendErrorEnvelope {
  error: { code: string; message: string; execution_status: ExecutionStatus | null };
}

export type FailureKind = "configuration" | "connection" | "timeout" | "cancelled" | "http" | "malformed";
export interface PublicFailure { kind: FailureKind; httpStatus?: number }

export function failureMessage(failure: PublicFailure): string {
  switch (failure.kind) {
    case "configuration":
      return "Invalid backend address. Set NEXT_PUBLIC_RAGBENCH_API_BASE_URL to an HTTP(S) loopback origin without credentials, a path, query, or fragment, then restart the frontend.";
    case "timeout":
      return "The backend status check timed out. Check the local backend and try again.";
    case "cancelled":
      return "The status check was cancelled. Check the backend again when ready.";
    case "malformed":
      return "The backend returned an unexpected health response. Check that the frontend and backend versions match.";
    case "http":
      return failure.httpStatus === 503
        ? "The backend is unavailable (HTTP 503). Check its local configuration and try again."
        : `The backend could not complete the status check (HTTP ${failure.httpStatus ?? "error"}).`;
    case "connection":
      return "Cannot reach the backend. Check that it is running and that its CORS configuration allows this frontend origin.";
  }
}

export class ApiClientError extends Error {
  readonly failure: PublicFailure;
  constructor(kind: FailureKind, httpStatus?: number) {
    const failure = { kind, ...(httpStatus === undefined ? {} : { httpStatus }) };
    super(failureMessage(failure));
    this.name = "ApiClientError";
    this.failure = failure;
  }
}

export function backendOrigin(value?: string): string {
  try {
    return localBackendOrigin(value);
  } catch {
    throw new ApiClientError("configuration");
  }
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, keys: string[]): boolean {
  return Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
}

export function parseHealth(value: unknown): HealthResponse {
  if (!object(value) || !exactKeys(value, ["status", "application", "api_version",
    "runtime_initialized", "generation_configured", "provider_connection_tested"]) ||
    (value.status !== "ok" && value.status !== "degraded") ||
    value.application !== "RAGBench Studio" ||
    typeof value.api_version !== "string" || value.api_version.length > 64 ||
    !/^\d{1,4}\.\d{1,4}\.\d{1,4}$/.test(value.api_version) ||
    typeof value.runtime_initialized !== "boolean" ||
    typeof value.generation_configured !== "boolean" || value.provider_connection_tested !== false ||
    (value.status === "ok") !== value.runtime_initialized ||
    (value.generation_configured && !value.runtime_initialized)) {
    throw new ApiClientError("malformed");
  }
  return {
    status: value.status, application: value.application, api_version: value.api_version,
    runtime_initialized: value.runtime_initialized,
    generation_configured: value.generation_configured, provider_connection_tested: false,
  };
}

function isErrorEnvelope(value: unknown): value is BackendErrorEnvelope {
  return object(value) && exactKeys(value, ["error"]) && object(value.error) &&
    exactKeys(value.error, ["code", "message", "execution_status"]) &&
    typeof value.error.code === "string" && typeof value.error.message === "string" &&
    (value.error.execution_status === null ||
      (typeof value.error.execution_status === "string" &&
        ["succeeded", "failed", "timed_out", "refused", "incomplete"].includes(value.error.execution_status)));
}

function discardBody(response: Response): void {
  if (response.body && !response.body.locked) {
    // Do not await cancellation: an untrusted stream may stall or reject cleanup.
    void response.body.cancel().catch(() => undefined);
  }
}

async function readJson(response: Response, signal: AbortSignal, maxBytes: number): Promise<unknown> {
  if (response.headers.get("content-type")?.split(";")[0].trim().toLowerCase() !== "application/json" || !response.body) {
    discardBody(response);
    throw new ApiClientError("malformed");
  }
  const reader = response.body.getReader();
  const abort = () => { void reader.cancel().catch(() => undefined); };
  signal.addEventListener("abort", abort, { once: true });
  if (signal.aborted) abort();
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > maxBytes) throw new ApiClientError("malformed");
      chunks.push(value);
    }
    const bytes = new Uint8Array(length);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const parsed: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
    return parsed;
  } catch (error: unknown) {
    if (error instanceof ApiClientError) throw error;
    throw new ApiClientError("malformed");
  } finally {
    signal.removeEventListener("abort", abort);
    void reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

export interface HealthClient { getHealth(signal?: AbortSignal): Promise<HealthResponse> }

export function createJsonRequest<T>(
  path: "/api/v1/health" | "/api/v1/query" | `/api/v1/experiments${string}` | `/api/v1/analysis/experiments${string}`, parse: (value: unknown) => T,
  origin?: string, options: { fetch?: typeof fetch; timeoutMs?: number; method?: "GET" | "POST" } = {},
): (signal?: AbortSignal, body?: unknown) => Promise<T> {
  return async (signal, requestBody) => {
    const base = backendOrigin(origin);
    if (path.startsWith("/api/v1/analysis/experiments") &&
        !/^\/api\/v1\/analysis\/experiments(?:\?limit=20&offset=\d+|\/[0-9a-f-]{36})$/.test(path)) throw new ApiClientError("configuration");
    if (path.startsWith("/api/v1/experiments") &&
        !/^\/api\/v1\/experiments(?:\?limit=50&offset=\d+|\/[0-9a-f-]{36}(?:\/results|\/freeze)?)?$/.test(path) &&
        !/^\/api\/v1\/experiments\/[0-9a-f-]{36}\/analysis\?resamples=2000&seed=0&lexical_proxy=(?:true|false)(?:&threshold_only=true)?(?:&compare=[0-9a-f-]{36}){0,7}$/.test(path)) throw new ApiClientError("configuration");
    const timeoutMs = options.timeoutMs ?? (path === "/api/v1/health" ? 5_000 : 270_000);
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0 || timeoutMs > (path === "/api/v1/health" ? 30_000 : 300_000)) throw new ApiClientError("configuration");
    if (signal?.aborted) throw new ApiClientError("cancelled");
    const controller = new AbortController();
    let listener: (() => void) | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const cancelled = new Promise<never>((_, reject) => {
      listener = () => { reject(new ApiClientError("cancelled")); controller.abort(); };
      signal?.addEventListener("abort", listener, { once: true });
    });
    const deadline = new Promise<never>((_, reject) => {
      timer = setTimeout(() => { reject(new ApiClientError("timeout")); controller.abort(); }, timeoutMs);
    });
    const operation = async (): Promise<T> => {
      const response = await (options.fetch ?? fetch)(`${base}${path}`, {
        method: options.method ?? (path === "/api/v1/health" ? "GET" : "POST"),
        headers: { Accept: "application/json", ...(requestBody === undefined ? {} : { "Content-Type": "application/json" }) },
        body: requestBody === undefined ? undefined : JSON.stringify(requestBody), cache: "no-store",
        credentials: "omit", redirect: "error", referrerPolicy: "no-referrer",
        signal: controller.signal,
      });
      // A non-cooperative fetch can resolve after our deadline or cancellation.
      // Release that late response rather than starting a new body read.
      if (controller.signal.aborted) {
        discardBody(response);
        throw new ApiClientError("cancelled");
      }
      const body = await readJson(response, controller.signal, path === "/api/v1/health" ? 16_384 : 1_048_576);
      if (!response.ok) {
        if (!isErrorEnvelope(body)) throw new ApiClientError("malformed");
        // The backend's message/code are untrusted and never retained or reflected.
        throw new ApiClientError("http", response.status);
      }
      return parse(body);
    };
    try {
      return await Promise.race([operation(), deadline, cancelled]);
    } catch (error: unknown) {
      if (error instanceof ApiClientError) throw error;
      throw new ApiClientError("connection");
    } finally {
      clearTimeout(timer);
      if (listener) signal?.removeEventListener("abort", listener);
      // Always terminate this client's private request after it settles.
      // This also covers failures before a response reader was acquired.
      controller.abort();
    }
  };
}

export function createApiClient(origin?: string, options: { fetch?: typeof fetch; timeoutMs?: number } = {}): HealthClient {
  return { getHealth: createJsonRequest("/api/v1/health", parseHealth, origin, options) };
}
