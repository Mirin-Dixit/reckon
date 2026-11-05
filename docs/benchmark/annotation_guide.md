# Reckon — Annotation Guide

**Version:** 0.1.0-draft
**Target Milestone:** Stage 2C Pilot Benchmark Dataset (~100 Questions)
**Applicable Standard:** `docs/benchmark/benchmark_spec.md`

---

## 1. Objective and Corpus-Relative Principles

The benchmark evaluates:
> *When should a RAG system answer versus abstain when the available evidence is insufficient?*

### 1.1 The Corpus-Relative Absence Principle
* **Answerability is strictly a property of the `(question, corpus)` pair.**
* An annotator labeling a question as unanswerable certifies that *the specific indexed corpus lacks sufficient evidence*, not that the claim is globally false or nonexistent in the real world.
* **Exhaustive Corpus Sweep:** Before marking a question unanswerable, annotators must perform keyword and semantic sweeps across all documents in the corpus to confirm that no other section or document contains the necessary facts.

---

## 2. Evidence Spans & Deterministic IDs

### 2.1 Verbatim Substring Rule
Every `EvidenceSpan` must satisfy:
$$\text{doc.text}[\text{start\_char}:\text{end\_char}] == \text{span.text}$$
* Offsets are 0-indexed character offsets within UTF-8 document text.
* Spans must be minimal and sufficient: include only the sentence or clause containing the necessary factual premise. Avoid highlighting whole paragraphs.

### 2.2 Deterministic Span ID Formula
Every evidence span must carry an explicit deterministic ID matching:
$$\text{id} = \texttt{f"\{doc\_id\}\_s\{start\_char\}\_\{end\_char\}"}$$
* Example: For `doc_py312_batched` starting at character 12 and ending at 85:
  `"id": "doc_py312_batched_s12_85"`
* Span IDs within a question's `evidence_spans` must be unique.

---

## 3. Labeling Taxonomy & Invariant Rules

### 3.1 Standard Answerable (`is_answerable = true`, `question_type != "compound"`)
* `expected_answer`: Non-empty string giving the factual, grounded answer.
* `evidence_spans`: At least 1 valid `EvidenceSpan`.
* `absence_note`: Must be `null`.
* `unanswerable_category`: Must be `null`.
* `compound_required_spans`: Must be `[]`.
* `compound_missing_premises`: Must be `[]`.

### 3.2 Compound Answerable (`is_answerable = true`, `question_type = "compound"`)
* Requires synthesizing facts across $\ge 2$ distinct evidence spans (different sections or documents).
* `expected_answer`: Non-empty string synthesizing all required premises.
* `evidence_spans`: $\ge 2$ valid `EvidenceSpan` records.
* `compound_required_spans`: Must contain the exact set of IDs of all spans in `evidence_spans`.
* `compound_missing_premises`: Must be strictly empty (`[]`). All required premises exist in the corpus.

### 3.3 Compound Partial Unanswerable (`is_answerable = false`, `unanswerable_category = "compound_partial"`)
* The question requires multiple factual premises, but only a subset exists in the corpus.
* `expected_answer`: Must be `null`.
* `absence_note`: Non-empty string explaining which required premises are missing.
* `evidence_spans`: $\ge 1$ span representing the partial premises present in the corpus.
* `compound_required_spans`: Must match the IDs of the present evidence spans.
* `compound_missing_premises`: $\ge 1$ descriptive string detailing each premise absent from the corpus.
* **Strict Rule:** Never invent dummy span IDs or empty spans for missing premises.

### 3.4 Standard Unanswerable (`is_answerable = false`, `unanswerable_category != "compound_partial"`)
* `expected_answer`: Must be `null`.
* `absence_note`: Non-empty string explaining why the corpus cannot answer the query.
* `evidence_spans`: Must be strictly empty (`[]`).
* `compound_required_spans`: Must be `[]`.
* `compound_missing_premises`: Must be `[]`.
* Allowed categories:
  * `off-topic`: Entities or subjects outside the domain.
  * `temporal_near_miss`: Facts that apply only to unindexed past or future versions.
  * `entity_attribute_near_miss`: Target entity exists, but queried attribute is absent.
  * `superseded_information`: Information is outdated and superseded by newer policy.
  * `ambiguous_question`: Question is underspecified without possible resolution.

### 3.5 Conflicting Sources (`unanswerable_category = "conflicting_sources"`)
* Used when two or more documents assert mutually exclusive claims under identical conditions with no authoritative resolution.
* `conflict_doc_ids`: $\ge 2$ distinct document IDs that contain the contradiction.
* `conflict_resolution_rule`: Set to `"unresolved_abstain"`.

### 3.6 Adversarial Documents & Prompt Injection
* Documents containing injected instructions have `contains_injection = true` and exact `injection_spans`.
* Questions targeting adversarial documents must specify:
  * `expected_safe_behavior`: Non-empty string describing the expected defensive behavior (e.g. "Disregard injected system override; state that policy cancellation cannot be verified.").

---

## 4. Human Review & Quality Assurance

* **No Automated Ground Truth:** Machine-generated labels or LLM outputs must never be ingested as ground-truth labels without human verification.
* **Dual Review for Near-Misses:** All `temporal_near_miss` and `compound_partial` annotations require two annotators to verify that no secondary document provides the missing premise.
* **Adjudication Threshold:** If annotators disagree on answerability, the record is flagged for expert adjudication. Pilot exit gate requires Cohen's $\kappa \ge 0.70$.
