# RAGBench Studio

**An experimental workbench investigating retrieval strategies and selective prediction (answer vs. abstain) in Retrieval-Augmented Generation.**

---

## Overview

A fundamental failure mode of Retrieval-Augmented Generation (RAG) systems is generating fluent, confident responses when retrieved context is irrelevant, contradictory, or absent. Evaluating RAG solely on final text generation conflates retrieval quality with generation behavior, making it difficult to diagnose why a system failed.

**RAGBench Studio** is designed to address this problem. The project investigates:
1. How different retrieval strategies—lexical (BM25), dense vector, and hybrid rank fusion—affect the quality of evidence provided to the generator.
2. How a system should decide whether to **answer or abstain** when evidence is insufficient, comparing always-answer baselines, prompt-based refusal, and score/confidence thresholding.
3. How to evaluate selective prediction rigorously using risk–coverage curves, selective classification metrics, and statistical confidence intervals.

---

## Stage 1: Retrieval Foundation

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

Automated tests are located under [`backend/tests/`](backend/tests/) and run completely offline without downloading models or accessing the network.

> [!WARNING]
> **Dense and Hybrid Testing Note:**
> Dense and hybrid unit tests use deterministic synthetic vectors (token hash projections and geometric test coordinates) to verify normalization, ranking math, tie-breaking, and error handling. **These tests verify software correctness and interface contracts only; they do not establish or measure real-world semantic retrieval quality.** Real semantic evaluation will occur when pretrained models are evaluated on the expanded benchmark.

---

## Development & Testing Commands

The project uses Python 3.11+ (tested on Python 3.13) with `pytest` and `ruff`.

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
ragbench/
├── backend/
│   ├── app/
│   │   ├── api/            # API endpoints (scaffolded)
│   │   ├── core/           # Shared configuration (scaffolded)
│   │   ├── db/             # Storage and persistence (scaffolded)
│   │   ├── evaluation/     # Metrics, risk-coverage curves (planned)
│   │   ├── generation/     # Generation & abstention policies (planned)
│   │   ├── ingestion/      # Document schema, JSONL loader, and chunker
│   │   └── retrieval/      # BM25, dense, and hybrid RRF indices
│   └── tests/              # 59 automated unit and integration tests
├── data/
│   └── sample/             # 5 Python 3.11 docs, 10 labeled questions
├── docs/                   # Decisions, reference notes, and results
├── frontend/               # Next.js web interface (scaffolded)
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
