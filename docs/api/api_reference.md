# RAGBench Studio API

## Scope and architecture

The API is a synchronous FastAPI transport layer over the existing ingestion,
BM25 retrieval, generation contracts, decision policies, and Stage 3F evaluation
runner. HTTP validation and serialization live under `backend/app/api/`; domain
logic remains in the existing modules.

The built-in HTTP runtime defaults to BM25 and also supports dense and hybrid
retrieval through the local Ollama embedding adapter and persistent cache.
P2 Batches 1-4 are accepted after deterministic tests and bounded genuine local
Train verification. This is integration evidence, not corpus-wide retrieval-quality
measurement. The underlying
BM25, cosine ranking and RRF algorithms remain unchanged.

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

Retrieval methods and threshold score families are distinct:

| Request `method` | Evidence `retrieval_method` / threshold `score_type` |
|---|---|
| `bm25` (default) | `bm25` |
| `dense` | `dense_cosine` |
| `hybrid` | `hybrid_rrf` |

`top_k` retains its default 5 and range 1-20. Hybrid alone accepts `rrf_k`
(integer 1-1000, default 60) and `candidate_k` (integer from `top_k` through
256). Omitted candidate depth preserves the existing HybridIndex default:
`max(top_k*3, 50, number_of_chunks)`. Explicit booleans/fractional fusion settings,
wrong score families and fusion settings on BM25/dense are rejected with 422.
The same retrieval contract applies to `POST /api/v1/evaluations`.

Dense/hybrid are opt-in: set `RAGBENCH_EMBEDDING_MODEL=all-minilm:22m` on the
server only after separate model-download approval. They reuse the numeric
loopback `RAGBENCH_OLLAMA_URL`, with CPU embedding, no cloud aliases, zero retries
and Batch 1 memory checks. The cache directory is server-side
`RAGBENCH_DENSE_CACHE_DIR`, default `.ragbench-cache/dense`; clients cannot set
model identities or paths. Cache and in-memory index keys include the exact
supplied document snapshot and settings; evaluation uses its own loaded snapshot.
The effective embedding identity is recorded in evaluation retrieval provenance.
An eight-entry in-memory LRU reuses indexes; dense vectors also persist on disk.

Unconfigured/missing models, incompatible identities and resource errors never
fall back to BM25. Setup failures use safe error envelopes (503 for unavailable
embedding configuration/resources, 422 for incompatible retrieval settings).
Query-time retrieval failure returns 502 with `retrieval_execution_failure` and
`execution_status=failed`, without a decision. Evaluation retains its existing
per-run failure/partial-result semantics. Invalid output, timeouts and cache
failures are execution failures rather than intentional abstentions. These
retrieval scores remain uncalibrated ranking values, not answerability probabilities;
Batch 3 adds typed score reporting. Batch 4 subsequently verified live score
transport but found the reason-code defect documented below; no calibration
verification has occurred.

### Typed observed scores (P2 Batch 3)

Successful queries expose `scores` and `retrieval_parameters`; every returned
evidence chunk also carries its typed `score` beside the unchanged numeric
`retrieval_score`. Evaluation observations and nested retrieval metadata carry
the same signals, including on failed executions when a signal was observed
before the failure. A score does not imply successful execution or a decision.

Each `ragbench.score.v1` signal records `kind`, `value`, `source`,
`retrieval_method`, `parameters`, `role`, `availability`, `unavailable_reason`,
`lower_bound`, `upper_bound`, `direction` and `calibration`. Threshold inputs
add the actual `threshold` and `threshold_direction` used by the existing policy.

| Kind | Range | Interpretation |
|---|---|---|
| `bm25` | [0, no fixed upper bound] | Lexical relevance |
| `dense_cosine` | [-1,1] | Vector similarity |
| `hybrid_rrf` | [0, rank_lists/(rrf_k+1)] | Rank fusion; effective k and nonempty contributing lists recorded |
| `prompt_self_assessment` | [0,1] | Model-reported evidence sufficiency; not confidence in its chosen decision |

All signals explicitly remain `uncalibrated`. Ranking scores have direction
`higher_is_more_relevant`; model self-assessment uses `higher_is_more_support`.
Neither means a calibrated probability of correctness or answerability.
Always-answer reports scores observationally. Threshold uses its unchanged
maximum-score comparison; no score normalization or threshold clamping occurs.
Prompt self-assessment is reported separately and never overrides ANSWER,
ABSTAIN, CLARIFY or the independent evidence-assessment fields.

Missing scores remain null with `availability=unavailable` and a reason; a real
zero remains available. Custom/legacy RRF observations without fusion provenance
cannot acquire an invented bound: their typed score is unavailable. Unsupported
custom retrievers have no invented score family. Effective parameters preserve
aggregation, chunk/index settings and the supplied document-snapshot fingerprint;
dense/hybrid also preserve embedding identity, cache key and vector fingerprint.
Fusion metadata is per query and does not change RRF ranking mathematics.

The prompt decision contract requires a `self_assessment`
number or explicit JSON null. Booleans, strings, nonfinite/out-of-range values
and omitted required fields fail validation; they are not silently corrected.
The current pipeline prompt version is `api-v4` / `prompt-decision-v3`.
Previous accepted P1 live
results used `api-v2` and remain historical evidence for that version only.
The updated decision/reason contract passed the final targeted real-model HTTP
check below; the earlier broad batch remains evidence for its original version.

Score fields are additive and optional for older API/experiment observations.
The experiment envelope remains `ragbench.experiment.v2`; the score structure
has its own version. The reader validates new score fields when present and
continues accepting older v2 observations without them. No evaluation metrics,
calibration fitting or threshold sweeps are introduced by this batch.

### P2 Batch 4 reason-code finding and offline remediation

The genuine `api-v3` / `prompt-decision-v2` run completed all planned calls:
10 query POSTs, one Train evaluation POST, 12 embedding calls and 13 generation
attempts, with zero retries and zero paid spending. All nine combinations on
Train `q_pilot_020` returned HTTP 200 / ANSWER. The dense prompt query on
`q_batch2_011` returned ABSTAIN with null self-assessment; the hybrid threshold
evaluation at tau=1 deliberately abstained above the attainable RRF bound.
All 13 citations passed exact-offset validation and manual support review.

The three prompt-policy ANSWER outputs nevertheless used
`reason_code=ambiguous_intent`, despite supported explanations and no clarification
request. Enum membership alone did not enforce cross-field consistency. These
are genuine metadata defects, not schema failures or successful clarification.
Original raw responses, experiment records and review artifacts remain outside
Git and unchanged; they must not be relabeled as results of the remediated prompt.

The prompt-policy validator now enforces this table:

| Decision | Allowed `reason_code` values |
|---|---|
| ANSWER | `other` |
| ABSTAIN | `insufficient_evidence`, `conflicting_evidence`, `unsupported_premise`, `out_of_scope`, `other` |
| CLARIFY | `ambiguous_intent`, `other` |

`other` preserves the existing generic fallback. Specific evidence/premise/scope
codes describe why the policy abstains; unresolved intent belongs to clarification.
An ANSWER can still report generator-observed unsupported premises separately;
that does not turn its decision reason into an abstention code. No reason enums,
threshold comparisons, scores or citation rules changed.

`prompt-decision-v3` gives the model explicit allowed pairs; `api-v4` identifies
the revised runtime prompt. Inconsistent pairs raise validation errors and become
execution failures, never silently remapped answers, abstentions or clarifications.
The field layout, nullable self-assessment semantics and uncalibrated status are
unchanged. Historical archived results remain readable without retroactive edits.

Equivalent instructions were compacted to preserve existing context limits.
Offline reconstruction against captured Batch 4 evidence and the recorded Qwen3
template fits context 8192, including the 1024 output allowance. The largest
conservative bound is 8144; future evidence/template changes may still exceed the
budget and must fail rather than truncate. This sizing check is not live inference.
The remediated prompt subsequently passed separately approved targeted live
verification, described below. Offline remediation itself authorized no inference.

### Accepted P2 installation and final targeted verification

P2 Batches 1-4 are accepted. Official `all-minilm:22m` was installed and verified:
45,960,996 bytes, F16, BERT architecture, 384 dimensions, Apache 2.0, digest
`1b226e2802dbb772b5fc32a58f103ca1804ef7501331012de126ab22f67475ef`.
The artifact config uses context 256; architecture metadata reports maximum 512.
The embedding adapter retains its explicit 256 context and `truncate:false`.
The broad run built 25 chunk vectors using four embedding calls, then made eight
query embeddings. One disk-cache miss, one disk-cache hit and eight memory-index
hits preserved matching snapshot/cache/vector fingerprints; cache hits were not
counted as embedding calls. The minimum sampled RAM was 2.11 GiB.

After offline reason-code remediation, a one-POST, one-generation-attempt check
produced a genuine ANSWER/other decision and valid 0.9 self-assessment, but HTTP
returned 502 / failed when the adapter blocked the second call needed for answer
generation. It was a budget-limited execution failure, not intentional abstention
or a successful complete HTTP verification. The original record remains intact.

The final targeted run used a fresh independent two-attempt budget:

| Item | Actual result |
|---|---|
| Train question | `q_pilot_020` only |
| Retrieval / policy | BM25 top-k 3 / prompt-abstention |
| Versions | `api-v4` / `prompt-decision-v3` |
| Provider / model | Local Ollama 0.40.14 / `qwen3:4b-q4_K_M` |
| Settings | Context 8192, output 1024 per attempt, thinking disabled, temperature 0, zero retries, concurrency 1 |
| HTTP / execution | 200 / `succeeded` (the actual API success value, not `completed`) |
| Decision / reason | ANSWER / `other` |
| Self-assessment | 0.9, explicitly uncalibrated |
| Calls | One query POST, two generation attempts, zero embedding calls |
| Tokens | 1604 input / 289 output total across both model calls |
| HTTP latency | 30.01 seconds |
| Minimum sampled available RAM | 2.46 GiB |
| Conservative decision-context bound | 7389 of 8192 |

The answer correctly described obtaining aware UTC with
`datetime.datetime.now(timezone.utc)`. Its supplied evidence ID was
`doc_py311_datetime_c0000`; the exact quote resolved to original Python 3.11
source offsets [84,259), end exclusive. Structural offset validation passed;
manual review separately confirmed semantic support. The BM25 maximum was
27.10194614811292, observational and uncalibrated, with the document fingerprint
preserved. There was no silent decision/reason remapping or fallback.

Accepted offline validation recorded 649 passing backend tests, Ruff and diff
checks passing, and unchanged dataset hashes. These historical results are not
claimed as newly executed documentation checks. All genuine inference was
loopback-only, cloud disabled, with zero paid spending and no Test inference or
gold labels in model prompts. Prior failures, original responses, usage, review
and experiment artifacts remain outside Git, unchanged.

These small Train checks establish local integration only. They do not establish
benchmark-wide retrieval quality, calibrated confidence, held-out performance or
generalization. Nullable self-assessment, short embedding context, narrow context
headroom, model-swapping latency, sampled memory guards and process-local budgets
remain limitations. Future live work requires separate authorization; P3 is not
part of this checkpoint.

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
  "prompt_version": "api-v4",
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
| `RAGBENCH_PROVIDER` | `ollama` | Local Ollama by default; optional OpenAI code requires explicit selection and is inactive under the zero-spending constraint |
| `RAGBENCH_MODEL` | unset | Default model; a request may specify the same model or supply one when no server default exists |
| `RAGBENCH_API_KEY_ENV` | `OPENAI_API_KEY` | Name of the environment variable holding the provider key (the key value is never returned) |
| `RAGBENCH_TIMEOUT_SECONDS` | `120` for Ollama; `30` for OpenAI | Provider attempt timeout, greater than 0 and at most 120 seconds |
| `RAGBENCH_RETRY_COUNT` | `0` for Ollama; `2` for OpenAI | Ollama rejects nonzero retries |
| `RAGBENCH_TEMPERATURE` | `0` for Ollama; unset for OpenAI | Provider sampling setting |
| `RAGBENCH_MAX_OUTPUT_TOKENS` | `1024` | Explicit output-token ceiling, integer 1 through 32768; requests may lower but cannot exceed it |
| `RAGBENCH_MAX_PROVIDER_REQUESTS` | `4` | Maximum SDK request attempts per adapter lifetime, including retries and failed attempts; integer 0 through 100 |
| `RAGBENCH_OLLAMA_URL` | `http://127.0.0.1:11434` | Numeric loopback origin only |
| `RAGBENCH_CONTEXT_SIZE` | `4096` | Local context size, integer 2048 through 32768 |
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
# Only install project dependencies after authorization, if missing:
# .\.venv\Scripts\python.exe -m pip install -e ".[server,dev]"
$env:RAGBENCH_PROVIDER = "ollama"
$env:RAGBENCH_MODEL = "qwen3:4b-q4_K_M"
$env:RAGBENCH_CONTEXT_SIZE = "8192"
$env:RAGBENCH_CORS_ORIGINS = "http://127.0.0.1:3000,http://127.0.0.1:3001"
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

No API key is needed. Do not configure paid-provider credentials. Ollama and its
model require the separate installation/download approval described below.
For offline threshold-policy queries that abstain, no model call is needed. Queries that choose
`ANSWER`, prompt-based decisions, and evaluations that generate answers require
a configured provider and model.

## CORS, authentication, and deployment limits

CORS is disabled when `RAGBENCH_CORS_ORIGINS` is empty. Configure exact
comma-separated origins for browser clients. Wildcard origins are rejected;
credentials are not enabled. CORS is not authentication.
The local Workbench uses port 3001 when port 3000 is occupied. Configure its
exact origin before starting Uvicorn and restart the backend after changes; CORS
settings are captured when the application is created. Defaults remain empty.

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
Request values override those defaults within the server output-token ceiling;
an explicit `timeout_seconds: 30` means
30 seconds. The API resolves these values before constructing policies and
pipelines. Experiment records contain those same effective model, temperature,
output-token, timeout, retry and SDK-retry settings, plus prompt version and
provider storage behavior and the provider request budget. Retrieval provenance includes character chunk size
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

## P1 local Ollama integration (zero spending)

The active P1 direction is local inference only. All earlier paid-provider
verification plans are cancelled. OpenAI remains optional adapter code for
compatibility and offline tests; it is never selected automatically or used as
fallback. Do not configure its credentials or make remote model requests.

The adapter uses standard-library HTTP to a numeric loopback origin. It bypasses
proxy environment variables, rejects redirects, sends no credentials or tools,
and never calls model-download endpoints. Model IDs require an explicit local
tag without registry paths or cloud suffixes. Readiness inspects local inventory
and model metadata, rejecting remote aliases and entries without local weights.
The initial supported architecture is Qwen3. Health checks inspect local
metadata only, not inference, and do not consume the generation-attempt budget.

Limits: 64 KiB request, 1 MiB response, one inference at a time per adapter,
zero retries, explicit output ceiling (default 1024), context size (default
4096), and bounded timeout (default 120 seconds). One adapter owns a shared
four-attempt budget across its queries and evaluations. Failed attempts count;
metadata requests do not. The budget resets on restart and is not a persistent
resource quota. Multiple worker processes have separate budgets and inference
locks; use one worker and set Ollama server parallelism to one.

The adapter estimates a conservative input allowance using the serialized UTF-8
request byte length (including instructions, question, evidence and JSON
schema), plus 256 framing tokens and any reported model-template bytes. It
reserves the requested output allowance separately. This is deliberately a
loose Qwen3 byte-level-tokenization bound, not an exact token count. Oversized
context fails before generation; evidence is never silently dropped. A custom
model/template is not an audited replacement for the approved stock model.
A later exact local tokenizer can improve utilization without changing policy
semantics. A 4096-token context can reject otherwise tokenizable requests;
report this honestly rather than increasing it or dropping evidence silently.

Responses retain the existing decision and citation validation. Provider
metadata adds nullable `model_digest`, `quantization`, and `completion_reason`;
`api_version` records the Ollama server version when available. Token counts map
from `prompt_eval_count` and `eval_count`, and `latency_ms` maps Ollama's
`total_duration` from nanoseconds to milliseconds, including load time. Unknown
fields remain null. Missing models/server, malformed output, context overflow,
timeouts and length-limited output are execution failures, not abstentions.
Ollama does not expose a universal structured refusal flag; invalid refusal
text is an output-validation failure, not an inferred ABSTAIN decision.

### P1.1 citation and decision contracts

The model-facing grounded-answer citation now contains only `claim`,
`evidence_id`, and `quote`. It no longer supplies source offsets. Application
code searches only the specifically selected supplied evidence chunk for that
exact quote. A unique match produces the original document character offsets
using the trusted chunk start; the existing strict citation validator then
checks the result. The public HTTP citation schema is unchanged.

Unknown chunk IDs, absent/nonexact quotes, repeated/overlapping quote matches,
and extra citation fields (including legacy model offsets) are rejected. There
is no fuzzy matching, whole-corpus fallback, first-match guessing or silent
repair of legacy responses. A longer unique quote can resolve a repeated short
quote; selecting an explicit chunk ID disambiguates identical text in different
chunks. Claim-to-quote associations remain intact. Structural validity does not
prove semantic entailment or complete citation coverage.

Prompt-based decisions retain their existing output fields and semantics.
The schema and instructions explicitly require JSON `null` for
`clarification_question` with ANSWER/ABSTAIN. CLARIFY requires a specific question.
String placeholders such as `"None"`, `"null"`, `"N/A"` and empty strings are
rejected; they are never converted to null. Missing required fields, provider
refusal, incomplete responses and validation failures remain execution failures.
The P1.1 API prompt version was `api-v2`, distinguishing these instructions and the
new model-facing citation format from earlier observations.

The three initial genuine local queries all failed validation: the answer
generations supplied invalid numeric citation offsets, and the prompt policy
supplied the string `"None"` instead of null. P1.1 deterministic replay reproduced
these failures before implementation changes. No new local inference is
authorized by the offline remediation itself.

The subsequently authorized three-request batch succeeded; see the accepted
results below. The earlier memory-blocked readiness attempt made no inference
requests. Further inference still requires explicit authorization.

### Installation and model approval gate

No installation or model download is authorized automatically. After explicit
approval, follow the [official Windows instructions](https://docs.ollama.com/windows)
and use the official per-user installer. Ollama's Windows binaries require at
least 4 GB of disk; reserve additional model and temporary-download space.

1. Quit any existing Ollama tray/server instance after identifying it.
2. Configure the Ollama server environment before starting that server:

```powershell
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
ollama serve
```

Changing these in a FastAPI shell does not reconfigure an already-running
Ollama server. Verify the actual server log reports cloud disabled and confirm
its listener is loopback. Do not expose port 11434 publicly. The application
cannot attest another process's environment; server verification is a separate
required operational gate. See the [Ollama FAQ](https://docs.ollama.com/faq).

3. In another terminal, only after download authorization:

```powershell
ollama pull qwen3:4b-q4_K_M
ollama --version
ollama list
ollama show qwen3:4b-q4_K_M
ollama show qwen3:4b-q4_K_M --license
Invoke-RestMethod http://127.0.0.1:11434/api/version
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

The installed `qwen3:4b-q4_K_M` was verified as Q4_K_M, 2,620,788,260 bytes,
under Apache 2.0. Verify the downloaded
license and quantization rather than assuming a mutable tag never changes.
Record the full inventory digest, model info and version before inference.
Plan roughly 4-6 GB working-memory headroom; actual usage depends on context,
GPU offload and runtime version. The inspected machine has 16 GB RAM, an
RTX 3050 Laptop with 4 GB VRAM and ample disk; its previously observed 4.2 GiB
free RAM is a snapshot, not a guarantee. Close memory-heavy applications first.
Reserve at least 8-10 GB disk for binaries, weights and temporary files.

4. Configure and start FastAPI separately:

```powershell
$env:RAGBENCH_PROVIDER = 'ollama'
$env:RAGBENCH_MODEL = 'qwen3:4b-q4_K_M'
$env:RAGBENCH_OLLAMA_URL = 'http://127.0.0.1:11434'
$env:RAGBENCH_CONTEXT_SIZE = '8192'
$env:RAGBENCH_MAX_OUTPUT_TOKENS = '1024'
$env:RAGBENCH_MAX_PROVIDER_REQUESTS = '4'
$env:RAGBENCH_RETRY_COUNT = '0'
$env:RAGBENCH_TIMEOUT_SECONDS = '120'
$env:RAGBENCH_TEMPERATURE = '0'
$env:RAGBENCH_CORS_ORIGINS = 'http://127.0.0.1:3000'
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

No API key is required. Do not set `RAGBENCH_PROVIDER=openai`. Existing browser
CORS configuration is exact-origin and is set in the backend terminal above.
Restart Uvicorn after changing it. If the frontend uses another port, configure
that exact origin explicitly; never use `*` or enable credentials. With an empty
allowlist CORS is disabled, so browser `OPTIONS /api/v1/experiments` preflight
returns 405 even though a plain GET can return 200. With the configured origin,
preflight returns 200 and a valid synthetic experiment POST returns 202.

### Accepted P1 local inference verification

Accepted on 3 November 2026 within the local BM25 scope. Three genuine POSTs
reached `/api/v1/query` through an ephemeral loopback Uvicorn server, using one
runtime and one adapter without restarts. Provider: local Ollama 0.40.14;
model: `qwen3:4b-q4_K_M`, Q4_K_M; digest:
`2bfd38a7daaf4b1037efe517ccb73d1a3bbd4822cf89f1a82be1569050a114e0`.
Prompt version: `api-v2`. The real Ollama listener was `127.0.0.1:11434`;
its server log confirmed cloud disabled. No paid or remote inference occurred.

Approved settings: BM25 top-k 3, context 8192, thinking disabled, maximum 1024
output tokens per attempt, temperature 0, timeout 120 seconds, zero retries,
concurrency 1 and one shared maximum of four provider attempts. Exactly three
HTTP requests consumed three attempts. No Test questions were used.

| Policy | Train question | HTTP / decision | Input / output tokens | HTTP latency |
|---|---|---|---:|---:|
| Always-answer | `q_pilot_020` | 200 / ANSWER | 740 / 136 | 14.40 s |
| Threshold tau=0, BM25 max score | `q_pilot_020` | 200 / ANSWER | 740 / 287 | 28.34 s |
| Prompt-abstention | `q_batch2_011` | 200 / ABSTAIN | 844 / 103 | 10.90 s |

Both answers described obtaining an aware UTC datetime using
`datetime.now(timezone.utc)`. Citation IDs resolved to supplied chunks and exact
original document character offsets (end exclusive):

- Always-answer: `doc_py311_datetime_c0000` [175,259).
- Threshold: `doc_py311_datetime_c0000` [175,259) and [27,82), plus
  `doc_py312_datetime_c0000` [84,215) for its explicitly versioned 3.12 claim.
- Prompt-abstention: no answer or citations; its reason correctly identified
  that retrieved evidence did not specify the Northstar logo color.

All four citation quotes matched the source text exactly. Manual review found
support for their associated claims; this is not an automated semantic judge.
All responses preserved actual provider/model provenance and usage, with
`execution_status=succeeded`. No failed output was silently corrected.

RAM was 5.42 GiB before a non-generating preload and 3.75 GiB afterward.
Pre/post-request readings remained above 3.47 GiB, exceeding the 1.5 GiB reserve;
RAM was checked before every provider attempt. These are sampled readings, not
continuous memory profiling. An earlier readiness check stopped safely before
inference because available RAM was insufficient. Historical initial inference
failures remain described above; they are not counted as successful results.

Post-verification backend validation: 380 tests passed in 20.35 seconds, Ruff
passed, and `git diff --check` passed with LF-to-CRLF notices only. These are
recorded acceptance results, not newly executed documentation-edit checks.
Spending was ₹0; electricity and existing hardware/internet remain resource
costs. Raw local captures remain outside Git, not durable experiment storage.

The adapter's generic context default remains 4096. The accepted configuration
explicitly sets 8192: earlier conservative sizing rejected the top-k 3 request
at 4096. Do not silently truncate evidence, change configuration or rerun failed
outputs. Installation/download and additional inference require authorization.

This small Train-only batch establishes local BM25 integration, not
benchmark-wide reliability, statistical generalization, held-out performance,
prompt-policy ANSWER/CLARIFY coverage or automatic semantic entailment.
Durable storage and semantic judging remain later milestones.

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
