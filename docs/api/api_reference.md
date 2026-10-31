# RAGBench Studio API

## Scope and architecture

The API is a synchronous FastAPI transport layer over the existing ingestion,
BM25 retrieval, generation contracts, decision policies, and Stage 3F evaluation
runner. HTTP validation and serialization live under `backend/app/api/`; domain
logic remains in the existing modules.

The built-in HTTP runtime currently configures **BM25 only**. Dense and hybrid
retrieval interfaces exist, but the repository has no concrete production
embedder to configure for this API. Requests for other methods are rejected;
the underlying retrieval modules are unchanged.

The benchmark files are fixed server-side paths. Requests cannot provide file
paths, Python objects, benchmark annotations, expected answers, or credentials.
The default chunk settings are 500 characters with 50 characters of overlap.

## Endpoints

Interactive OpenAPI documentation is available at `/api/v1/docs`.

### `GET /api/v1/health`

Initializes the local dataset/retrieval runtime if needed and reports whether
model generation is configured. `provider_connection_tested` is always `false`;
health does not make a live provider request.

```json
{
  "status": "ok",
  "application": "RAGBench Studio",
  "api_version": "0.1.0",
  "runtime_initialized": true,
  "generation_configured": false,
  "provider_connection_tested": false
}
```

The runtime can initialize for offline BM25 and threshold-policy use even when
no provider key is configured. A query that needs model generation then returns
a safe configuration error.

### `POST /api/v1/query`

Runs one question through the existing `RagPipeline`. Example request:

```json
{
  "question": "What is the requisition approval limit?",
  "retrieval": {"method": "bm25", "top_k": 5},
  "policy": {"name": "threshold", "score_type": "bm25", "threshold": 0.8},
  "generation": {"model": "configured-model", "timeout_seconds": 30},
  "experiment_id": null,
  "run_id": null
}
```

Policy names are `always_answer`, `prompt_abstention`, and `threshold`. The
threshold policy requires `score_type` and `threshold`; its score type must match
the selected retrieval method. Its existing maximum-score aggregation and
decision behavior are unchanged. `experiment_id` and `run_id` are optional
caller-provided UUID-shaped correlation values only; the query route does not use them to
load or score benchmark records.

Example answer response (abridged):

```json
{
  "experiment_id": null,
  "run_id": null,
  "decision": "ANSWER",
  "answer": "The policy sets the limit at 12 units.",
  "clarification_question": null,
  "decision_reason": {"code": "other", "explanation": "..."},
  "citations": [
    {"claim": "...", "evidence_id": "policy_c0000", "quote": "...", "start_char": 80, "end_char": 96}
  ],
  "retrieved_evidence": [
    {"chunk_id": "policy_c0000", "document_id": "policy", "retrieval_rank": 1, "retrieval_score": 1.2, "retrieval_method": "bm25", "text": "..."}
  ],
  "evidence_assessment": {"relevance": "not_assessed", "sufficiency": "not_assessed"},
  "policy_name": "threshold_based_abstention",
  "policy_parameters": {"score_type": "bm25", "threshold": 0.8},
  "provider": {"provider": "openai", "model": "configured-model", "request_id": null},
  "execution_status": "succeeded",
  "unsupported_premises": [],
  "surfaced_contradictions": [],
  "prompt_version": "api-v1",
  "latency_ms": 125.0,
  "token_usage": {"input_tokens": 100, "output_tokens": 30, "total_tokens": 130}
}
```

`ABSTAIN` returns the policy rationale in `decision_reason` and has no answer.
`CLARIFY` returns `clarification_question`. Successful decisions have
`execution_status: "succeeded"`.

### `POST /api/v1/evaluations`

Runs the existing `EvaluationRunner` synchronously. Example:

```json
{
  "split": "dev",
  "question_ids": null,
  "policies": [
    {"name": "threshold", "score_type": "bm25", "threshold": 0.8}
  ],
  "retrieval": {"method": "bm25", "top_k": 5},
  "generation": {"model": "configured-model", "timeout_seconds": 30},
  "random_seed": 17,
  "fail_fast": false
}
```

The response contains the experiment ID, completion status, split, selected
question count, and observed run count. Fail-fast or otherwise incomplete runs
are marked `partial`; detailed per-policy missing-run accounting is preserved
in the results.

### `GET /api/v1/evaluations/{experiment_id}`

Returns metadata, selected IDs, policy names, observed run count, and completion
status. It does not return gold answers or labels.

### `GET /api/v1/evaluations/{experiment_id}/results`

Returns the serialized experiment record, run results, metrics, and evaluator
gold fields. This is the only API response that exposes gold-derived data and
should be treated as evaluation data, not runtime query output.

## Error responses

Errors use a stable envelope and do not include stack traces, raw provider
exceptions, request input values, or filesystem paths:

```json
{
  "error": {
    "code": "runtime_execution_failure",
    "message": "The provider returned an incomplete response.",
    "execution_status": "incomplete"
  }
}
```

| Status | Meaning |
|---|---|
| 400 | Invalid content length |
| 404 | Experiment ID or route not found |
| 405 | HTTP method not allowed |
| 413 | Actual request bytes or declared length exceed the body limit |
| 422 | Invalid request, split, question filter, or configuration |
| 500 | Unexpected internal failure |
| 502 | Provider or runtime execution failed/refused/incomplete |
| 503 | Runtime or model generation is not configured |
| 504 | Runtime timed out |

Execution failures never become successful abstentions. Provider refusal and
incomplete statuses are preserved in `execution_status` on the error response.
Request validation errors intentionally omit submitted values, which could
contain sensitive text.

## Configuration

Configuration is server-side only:

| Environment variable | Default | Purpose |
|---|---|---|
| `RAGBENCH_PROVIDER` | `openai` | The configured provider; currently only OpenAI is implemented |
| `RAGBENCH_MODEL` | unset | Default model; a request may specify the same model or supply one when no server default exists |
| `RAGBENCH_API_KEY_ENV` | `OPENAI_API_KEY` | Name of the environment variable holding the provider key (the key value is never returned) |
| `RAGBENCH_TIMEOUT_SECONDS` | `30` | Provider request timeout |
| `RAGBENCH_RETRY_COUNT` | `2` | Bounded provider retry count |
| `RAGBENCH_TEMPERATURE` | unset | Provider sampling setting |
| `RAGBENCH_MAX_OUTPUT_TOKENS` | unset | Provider output limit |
| `RAGBENCH_CORS_ORIGINS` | empty | Comma-separated exact browser origins allowed by CORS |
| `RAGBENCH_ENV` | `development` | Deployment environment label |

No public request model contains an API key or arbitrary provider options. The
adapter resolves credentials from the configured environment variable only
when a model call is needed. Configuration and serialized responses redact
secret-keyed values and recognizable credential formats. Arbitrary values that
cannot be identified as credentials cannot be reliably redacted; never place
secrets in questions, document text, model names, or generated content.

## Local startup

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[server,dev,openai]"
$env:RAGBENCH_MODEL = "your-configured-model"
# Configure OPENAI_API_KEY through your local secret manager or shell profile.
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Do not put a real key in shell history, source control, request bodies, or
result records. For offline threshold-policy
queries that abstain, no OpenAI key or model call is needed. Queries that choose
`ANSWER`, prompt-based decisions, and evaluations that generate answers require
a configured provider and model.

## CORS, authentication, and deployment limits

CORS is disabled when `RAGBENCH_CORS_ORIGINS` is empty. Configure exact
comma-separated origins for browser clients. Wildcard origins are rejected;
credentials are not enabled. CORS is not authentication.

Authentication is out of scope; no placeholder auth is provided. Bind to
localhost for development and place the API behind an authenticated trusted
network boundary before exposing it to other users. The API applies a 1 MiB
body limit based on actual received bytes (including streaming requests),
question and list-size limits, strict Pydantic models,
and rejects unknown fields. It never accepts caller-supplied paths, tools, or
Python object deserialization.

Evaluation execution is synchronous and can occupy a request worker for the
duration of every selected question and provider call. The in-memory registry
is single-process only: records disappear on restart and are not shared across
workers. This prototype does not claim durable or production persistence.

Retrieved document text remains untrusted evidence. The API does not pass
benchmark annotations into query-time policies or generation. Provider and
application errors are logged by safe error category, without logging
credentials, full configurations, or document text.

## Effective settings and reproducibility

Omitted or null generation settings inherit the server provider defaults.
Request values override those defaults; an explicit `timeout_seconds: 30` means
30 seconds. The API resolves these values before constructing policies and
pipelines. Experiment records contain those same effective model, temperature,
output-token, timeout, retry and SDK-retry settings, plus prompt version and
provider storage behavior. Retrieval provenance includes character chunk size
and overlap, BM25 k1/b, tokenizer version, method and top-k. Paired comparisons
reject differing recorded configurations. An unspecified sampling value remains
null and delegates to the provider; it is not a claim about a provider's internal
default or deterministic behavior.

The API records `random_seed` for experiment identity, but does not apply it to
model generation (`seed_applied: false`). Model sampling is not reproducible from
that field alone. The evidence assessor reports `not_assessed`; it does not
infer sufficiency from BM25 scores. Generator-reported unsupported premises and
contradictions are returned as separate observed fields.

Each evaluation uses the runner's validated document snapshot for retrieval.
Parsing and fingerprinting use the same captured bytes, so later file changes
cannot misrepresent the corpus actually used.
Query runtime documents remain the initialization snapshot; restart the process
to load changed query corpus files. Benchmark files are expected to remain frozen.

## Public schemas and lifecycle

OpenAPI declares the common error envelope and error status codes, including
validation and framework HTTP errors. Query citations, evidence, assessment,
provider metadata, token usage, and evaluation run/gold structures have typed
nested schemas. Metric breakdowns and configuration maps retain JSON-valued
maps where their keys vary. Only the explicit evaluation-results route contains
gold data. `completed` means all selected runs were accounted for; inspect the
execution-error metrics to determine success.

Correlation IDs must match the UUID shape; invalid values receive a generic 422
without reflecting the value. The complete query response is sanitized after
adding correlation fields. Redaction can alter displayed text; citation offsets
always refer to the original source document, not redacted display text.

Lazy provider creation is synchronized. Shutdown rejects new calls, drains
active calls, and closes the SDK client through the application lifespan.
Unexpected HTTP failures are contained before Uvicorn can log raw exception
tracebacks; clients receive the documented generic error envelope.
An initialization failure is retried on a later request after a one-second
cooldown, with no public reset endpoint. Runtime initialization and shutdown logs
contain error classes rather than exception details.

Evaluations still use synchronous workers with no cancellation/job queue or
admission control. Disconnecting does not guarantee cancellation; a finished
experiment is registered only after execution returns. The registry has no
retention limit and remains unsuitable for public or multi-worker deployment.

For offline development, install `.[server,dev]`; the `openai` extra is needed
only for configured OpenAI generation. The `dev` extra also includes Uvicorn
so its startup regression runs in a normal test installation. Run it with:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_api_hardening.py -k documented_uvicorn_startup
```
