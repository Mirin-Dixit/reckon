# Reckon

**Reckon | Evidence-Aware RAG Evaluation & Selective Prediction Platform**

An evidence-aware RAG evaluation workbench that studies when retrieval-augmented generation systems should answer, abstain, or request clarification.

**An experimental workbench investigating retrieval strategies and selective prediction (answer vs. abstain) in Retrieval-Augmented Generation.**

---

## Overview

A fundamental failure mode of Retrieval-Augmented Generation (RAG) systems is generating fluent, confident responses when retrieved context is irrelevant, contradictory, or absent. Evaluating RAG solely on final text generation conflates retrieval quality with generation behavior, making it difficult to diagnose why a system failed.

**Reckon** is designed to address this problem. The project investigates:
1. How different retrieval strategies—lexical (BM25), dense vector, and hybrid rank fusion—affect the quality of evidence provided to the generator.
2. How a system should decide whether to **answer or abstain** when evidence is insufficient, comparing always-answer baselines, prompt-based refusal, and score/confidence thresholding.
3. How to evaluate selective prediction rigorously using risk–coverage curves, selective classification metrics, and statistical confidence intervals.

---

See [identity and storage compatibility](docs/rebranding.md) before restarting an existing Docker installation.

## Current Backend Status

P1 now defaults to a local-only Ollama provider with structured JSON, bounded
context/output, one-inference concurrency and a shared attempt budget. The
project has a strict zero-spending constraint: paid inference plans are cancelled.
OpenAI remains optional, inactive compatibility code, never an automatic fallback.
P1 is accepted within the local BM25 integration scope. On 3 November 2026,
three genuine Train POST requests to `/api/v1/query` returned HTTP 200:
always-answer and threshold (tau=0) on `q_pilot_020` returned ANSWER;
prompt-abstention on `q_batch2_011` returned ABSTAIN. Verification used Ollama
0.40.14, exact local model `qwen3:4b-q4_K_M`, BM25 top-k 3, context 8192,
thinking disabled, output limit 1024, zero retries and concurrency 1. One shared
adapter consumed 3 of 4 allowed provider attempts. Cloud was disabled and the
server bound to loopback. Spending was ₹0; existing hardware, electricity and
internet remain resource costs.

All four answer citations matched exact source offsets and passed manual
semantic-support review. Backend validation passed 380 tests, Ruff and
`git diff --check`. These Train checks establish local BM25 integration only,
not benchmark-wide reliability, held-out performance or generalization.
Structural citation validation is not an automated semantic judge.

Historically, the initial three local queries failed strict citation/decision
validation. P1.1 resolved offsets from unique exact quotes and strengthened
JSON-null instructions. A later readiness attempt stopped before inference
due to insufficient RAM; the accepted batch proceeded only after memory checks.
See [local setup](docs/api/api_reference.md#installation-and-model-approval-gate)
and [accepted verification results](docs/api/api_reference.md#accepted-p1-local-inference-verification).

Stage 3G.1 provides a local FastAPI backend, provider-neutral generation contracts,
three decision baselines, an optional OpenAI adapter, and an evaluation runner.
The API supports BM25 retrieval and a synchronous, process-local experiment
registry. P2 Batch 2 wires dense and hybrid retrieval into HTTP using the local
embedding adapter and cache, verified with bounded genuine local calls.
P2 Batches 1-4 are accepted. Stage 4A adds a local frontend
foundation and read-only System Status view. P3 Batch 1 adds the functional
Query Lab foundation; experiment execution UI, analytics and deployment remain
unimplemented. See
[frontend setup and verification](frontend/README.md).

The accepted, frozen pilot contains 17 documents and 54 questions (Train 50,
Dev 3, Test 1). Train contains 30 answerable and 20 unanswerable questions.
The 100-question corpus remains a future expansion target; its historical
allocation plan is preserved in [the pilot plan](docs/benchmark/pilot_plan.md).
These splits do not support statistical generalization claims.
See [API configuration and startup](docs/api/api_reference.md), including the
required `server` extra and local-only deployment limits.

### Accepted P2: local retrieval, scores and provenance

`OllamaEmbedder` implements the existing `Embedder` protocol for the approved
installed `all-minilm:22m` model (384 dimensions, F16, Apache 2.0).
Its verified digest is
`1b226e2802dbb772b5fc32a58f103ca1804ef7501331012de126ab22f67475ef`. It uses numeric-loopback HTTP only, checks local
weights/digest and embedding capability, rejects remote aliases, sends
`truncate:false`, and performs CPU batches of at most eight with zero retries.
Inputs exceeding the model context fail instead of being silently truncated.
The adapter uses the existing bounded HTTP transport (64 KiB requests, 1 MiB
responses), an operation deadline and a shared per-instance attempt budget.
It checks the 1.5 GiB available-RAM reserve before/after batches, requiring an
additional 512 MiB allowance before inference. These sampled checks cannot
reserve OS memory or prevent another process from consuming it during a call.

`DenseIndexCache.get_or_build()` returns the existing `DenseIndex` backed by
validated precomputed vectors. Callers provide the exact chunks, documents-only
snapshot SHA-256 and chunking configuration. Cache keys include these inputs,
ordered chunk IDs/text hashes/offsets, model digest, dimensions, preprocessing,
context, server version and execution settings. JSON entries carry a vector
checksum; malformed, incompatible or corrupt entries rebuild in full. Atomic
same-directory replacement prevents readers from seeing partial writes.

Use a private configured directory such as `.ragbench-cache/dense` (ignored by
Git). Default limits are eight entries, 2 MiB per entry and 16 MiB total;
eviction touches only owned SHA-256-named JSON files. No pickle, raw source text,
benchmark questions or gold annotations are stored. The cache coordinates
threads/instances in one process. Other processes may duplicate a build; strict
cross-process quota coordination is not implemented. Hashes detect corruption,
not deliberate modification by an attacker with cache-directory write access.
Trusted injected Python transports/callbacks are not sandboxed.

Batch 1 introduced no API wiring, model download or real embedding verification.
Batch 2 now supports `bm25`, `dense` and `hybrid` through query and evaluation
HTTP requests. BM25 remains the default and needs no embedding configuration.
Dense/hybrid require server-side `RECKON_EMBEDDING_MODEL=all-minilm:22m` and
use `RECKON_DENSE_CACHE_DIR` (default `.ragbench-cache/dense`). There is no
automatic download or fallback. Runtime indexes reuse an eight-entry LRU keyed
by the supplied document snapshot and effective settings. Evaluation snapshots
remain separate from ordinary runtime documents. See the API reference for
fusion settings and score-family names. Automated tests remain deterministic
and offline; bounded genuine model runs were separately authorized and recorded.
Further downloads or inference require separate approval.

P2 Batch 3 adds versioned typed scores to query responses and evaluation records:
BM25 relevance, dense cosine, bounded RRF and nullable prompt-policy evidence
self-assessment. Signals preserve source, range, direction, effective settings,
availability and uncalibrated status. Threshold scores include the actual value,
threshold and comparison; always-answer scores are observational. Self-assessment
does not override the model's decision or the independent evidence assessment.
Missing values remain null. The runtime prompt version is now `api-v4`
(`prompt-decision-v3` for decision instructions); earlier P1 observations used
`api-v2`, and the P2 Batch 4 live run used `api-v3` / `prompt-decision-v2`.
No calibration, answerability-probability or generalization claim follows.

P2 Batch 4 completed 10 query POSTs and one Train evaluation within its limits:
12 embedding calls, 13 generation attempts, zero retries and zero paid spending.
All nine retrieval/policy combinations answered the Train UTC question; the
logo-color query abstained, and the high-threshold evaluation abstained by design.
All 13 citations matched source offsets and passed manual semantic-support review.
However, all three prompt-policy ANSWER results incorrectly used
`ambiguous_intent`. Those original observations/artifacts are preserved unchanged.
Offline remediation now rejects inconsistent decision/reason pairs rather than
remapping outputs: ANSWER permits `other`; ABSTAIN permits evidence/premise/scope
codes or `other`; CLARIFY permits `ambiguous_intent` or `other`.

A first targeted one-attempt rerun produced ANSWER/other but HTTP 502: the decision
consumed the budget before answer generation. It was not counted as a successful
HTTP query. A separately authorized final rerun used a fresh two-attempt budget
and returned HTTP 200, `execution_status=succeeded`, ANSWER/other under
`api-v4` / `prompt-decision-v3`. Its citation matched Python 3.11 source offsets
[84,259) and passed manual semantic-support review. Self-assessment was 0.9,
explicitly uncalibrated; usage was 1604 input / 289 output tokens and HTTP latency
30.01 seconds. It used one query POST, two generation calls, zero embeddings and
zero retries; minimum sampled RAM was 2.46 GiB. No output was silently remapped.

Accepted P2 validation: 649 backend tests passed, Ruff and diff checks passed,
and dataset hashes remained unchanged. All live work was local-only with cloud
disabled and zero paid spending (₹0), using Train questions only. Raw artifacts
remain outside Git. These checks establish integration, not benchmark-wide
retrieval quality, calibration, statistical performance or generalization.
The 256-token embedding context, conservative generation budget, model swapping,
sampled RAM guards, process-local quotas and prototype deployment limits remain.
P3 has not begun.

## Stage 1: Retrieval Foundation (Historical Snapshot)

The core data ingestion, chunking, and retrieval foundations are implemented and verified against unit and integration test fixtures using the Python standard library with zero external runtime dependencies.

```text
Status Summary:
[x] Ingestion schema & JSONL loader (validated)
[x] Deterministic character chunking & evidence span mapping (validated)
[x] Okapi BM25 retrieval index (validated)
[x] Dense retrieval index & Embedder protocol (validated)
[x] Hybrid retrieval via Reciprocal Rank Fusion (validated)
[x] 59 automated unit and integration tests passing in < 1s
[ ] Real embedding model integration (planned)
[ ] Full evaluation benchmark expansion (planned)
[ ] Answer-generation & abstention policies (planned)
[ ] Risk-coverage evaluation & confidence intervals (planned)
[ ] Web interface & experiment dashboard (planned)
```

---

## Implemented Architecture & Components

Application code lives under [`backend/app/`](backend/app/) and automated tests under [`backend/tests/`](backend/tests/).

### 1. Ingestion Schema & Validation (`backend/app/ingestion/schema.py`)
* **`Document`**: Represents source documents with unique IDs, titles, source URLs, and verbatim text.
* **`EvidenceSpan`**: Ground-truth character offsets (`[start_char, end_char]`) within a document. Validates exact substring equality against parent text.
* **`Question`**: Labelled query supporting answerable and unanswerable queries.
* **`UnanswerableCategory`**: Distinguishes unanswerable query failure modes:
  * `completely_absent`: Topic does not exist anywhere in the corpus.
  * `missing_attribute`: Topic exists, but the queried attribute is absent.
  * `missing_feature`: Topic and related attributes exist, but specific functionality or version is absent.

### 2. Dataset Loader (`backend/app/ingestion/loader.py`)
* Streams and validates JSONL records (`documents.jsonl`, `questions.jsonl`).
* Enforces schema constraints and cross-references document IDs.

### 3. Deterministic Chunker (`backend/app/ingestion/chunking.py`)
* Fixed-size character windowing with configurable overlap (`chunk_size=300, chunk_overlap=80`).
* Generates stable chunk IDs (`{doc_id}_c{index:04d}`) and retains original document character offsets.
* Includes `find_containing_chunks()` to programmatically map `EvidenceSpan` instances to the chunks that contain them.

### 4. BM25 Retrieval (`backend/app/retrieval/bm25.py`)
* Pure Python Okapi BM25 implementation using standard-library regular expressions.
* **Non-Negative Lucene/Okapi IDF**: $\text{IDF}(t) = \ln\left(1.0 + \frac{N - df(t) + 0.5}{df(t) + 0.5}\right)$, guaranteeing non-negative weights for high-frequency terms.
* Document-length normalization ($k_1=1.5, b=0.75$) and deterministic tie-breaking (`score DESC, doc_id ASC, index ASC`).

### 5. Dense Retrieval Interface (`backend/app/retrieval/dense.py`)
* **`Embedder` Protocol**: Decouples retrieval mechanics from specific model libraries (`embed_texts`, `embed_query`).
* **Vector Operations**: Standard-library $L_2$ normalization and cosine similarity.
* **Numerical Safety**: Explicitly validates vectors against empty inputs, dimension mismatches, NaNs, infinities, and booleans. Zero vectors evaluate to similarity `0.0` without division-by-zero.
* **Full-Spectrum Ranking**: Retains finite scores across $[-1.0, 1.0]$ without non-positive score filtering. Scores represent geometric vector alignments, not calibrated probabilities of answerability.

### 6. Hybrid Retrieval with Reciprocal Rank Fusion (`backend/app/retrieval/hybrid.py`)
* **`reciprocal_rank_fusion()`**: Fuses arbitrary ranked candidate lists using:
  $$\text{RRF\_Score}(d) = \sum_{r \in R} \frac{1}{k + \text{rank}_r(d)}$$
  using 1-based ranks and default smoothing constant $k=60$.
* Deduplicates multiple occurrences of chunk IDs within a single ranking, counting only their highest rank.
* **`HybridIndex`**: Validates corpus identity between underlying BM25 and Dense indices, rejects incompatible corpora with `ValueError`, and deterministically breaks score ties.

---

## Development Sample Dataset

The sample dataset in [`data/sample/`](data/sample/) provides a concrete development corpus for unit and integration testing:
* **Documents (`documents.jsonl`)**: 5 verbatim, version-pinned extracts from official Python 3.11 documentation (`functools.lru_cache`, `dataclasses`, `itertools.islice`, `urllib.parse`, and `sqlite3`).
* **Questions (`questions.jsonl`)**: 10 questions:
  * **7 Answerable**: Pinned to exact character evidence spans across the documents.
  * **3 Unanswerable**: Verified negative queries covering completely absent topics (e.g. Google Guava Cache), missing attributes (e.g. `itertools.islice` negative step arguments), and missing features (e.g. `itertools.batched`, added in Python 3.12).
* **Chunk Count**: Using the standard settings (`chunk_size=300, chunk_overlap=80`), the 5 documents yield exactly 10 deterministic chunks.

> [!NOTE]
> This sample dataset is a minimal development fixture for pipeline verification. It is not an evaluation benchmark and cannot support statistical claims about retrieval quality.

---

## Testing Strategy & Semantic Quality Caveat

Automated tests are located under [`backend/tests/`](backend/tests/) and require
no external services, model downloads, or paid model calls. Provider interactions
use deterministic test doubles. The startup smoke test starts Uvicorn and makes
a real HTTP request over loopback (`127.0.0.1`), then shuts the server down.

> [!WARNING]
> **Dense and Hybrid Testing Note:**
> Dense and hybrid unit tests use deterministic synthetic vectors (token hash projections and geometric test coordinates) to verify normalization, ranking math, tie-breaking, and error handling. **These tests verify software correctness and interface contracts only; they do not establish or measure real-world semantic retrieval quality.** Real semantic evaluation will occur when pretrained models are evaluated on the expanded benchmark.

---

## Development & Testing Commands

The project uses Python 3.11+ (tested on Python 3.13) with `pytest` and `ruff`.

The synchronous FastAPI backend is documented in
[`docs/api/api_reference.md`](docs/api/api_reference.md). It currently exposes
the configured BM25 runtime and in-memory evaluation registry.

### Running Tests (Windows PowerShell)
```powershell
.\.venv\Scripts\python.exe -m pytest
```

### Running Linter
```powershell
.\.venv\Scripts\python.exe -m ruff check backend
```

---

## Repository Layout

```text
reckon/
├── backend/
│   ├── app/
│   │   ├── api/            # Versioned FastAPI endpoints
│   │   ├── core/           # Shared configuration (scaffolded)
│   │   ├── db/             # Storage and persistence (scaffolded)
│   │   ├── evaluation/     # Evaluation runner, records, and metrics
│   │   ├── generation/     # Provider contracts, generation, and policies
│   │   ├── ingestion/      # Document schema, JSONL loader, and chunker
│   │   └── retrieval/      # BM25, dense, and hybrid RRF indices
│   └── tests/              # Offline unit, integration, and API tests
├── data/
│   └── sample/             # 5 Python 3.11 docs, 10 labeled questions
├── docs/                   # Decisions, reference notes, and results
├── frontend/               # Next.js foundation and System Status
├── pyproject.toml          # Project configuration and dev dependencies
└── README.md
```

---

## Roadmap & Next Stages

1. **Pretrained Embedding Integration**: Evaluate local candidate models and runtimes (such as `sentence-transformers/all-MiniLM-L6-v2`, `fastembed`, or ONNX Runtime) to connect a concrete implementation to the `Embedder` protocol.
2. **Benchmark Dataset Expansion**: Expand beyond the 10-question sample dataset into an evaluation corpus with designated train, validation, and held-out test splits.
3. **Generation & Abstention Baselines**:
   * *Always-Answer*: Standard generator attempting an answer regardless of context quality.
   * *Prompt-Based Abstention*: Instruction-tuned prompts directing the model to decline when retrieved evidence is insufficient.
   * *Confidence / Threshold Abstention*: Decision rules abstaining based on retrieval similarity and generation confidence metrics.
4. **Selective Evaluation & Analysis**:
   * Risk–coverage curves and Area Under Risk–Coverage Curve (AURC).
   * Bootstrap confidence intervals to assess statistical significance across retrieval methods.
5. **Interactive Workbench UI**: Web interface to inspect retrieved evidence passages, trigger benchmark runs, and visualize selective prediction tradeoffs.


### P3 Batch 1 - Query Lab foundation

The frontend `/query-lab` now provides explicit question submission to
`/api/v1/query`, with BM25/dense/hybrid and all three policies, validated controls,
cancellation and basic observed decisions/answers. Execution errors are distinct
from intentional abstention. No model calls occur automatically on page load.
See [frontend setup and offline checks](frontend/README.md#query-lab-p3-batch-1).
P3 Batch 2 adds the evidence ledger, exact Unicode citation highlights, typed
score provenance and supplied execution metadata. Manual browser acceptance
remains pending; these interfaces do not establish semantic grounding, retrieval
quality or benchmark-wide reliability.
