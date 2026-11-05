# Reckon — Expansion Phase Plan (~100 Questions)

**Status:** Approved Architecture & Revised Phased Allocation Plan
**Milestone:** Stage 2C — Pilot Benchmark Dataset Expansion
**Target Corpus:** 19–23 Documents across 13 Independent Source Groups
**Provisional Target Questions:** 100 Questions (Provisional target: 50 Train / 20 Dev / 30 Test; ~60 Answerable / ~40 Unanswerable)

> **Accepted checkpoint through Stage 3G.1:** the frozen pilot currently contains
> 17 documents and 54 questions: Train 50 (30 answerable, 20 unanswerable), Dev 3,
> and Test 1. The 100-question allocation below is a future expansion target.
> Historical source-group allocations and authoring batches are preserved for
> planning; they do not claim that later batches have been completed or approved
> for execution. The small current Dev/Test splits do not support statistical
> generalization claims.

---

## 1. Source-Group Atomicity & Allocation Strategy

To guarantee zero cross-split leakage, every document in a Source Group—including linked version families and supersession chains—is assigned strictly to a single split. **No source group may span multiple splits.**

Adversarial coverage across splits is achieved by constructing separate, independent source groups with distinct documents and attack payloads for each split.

| Source Group ID | Domain | Sources & Coverage Description | Provenance Type | Split | Question Coverage Modes |
|:---|:---|:---|:---:|:---:|:---|
| `src_grp_py_core` *(existing)* | Technical API | Python 3.11 & 3.12 core (`datetime`, `itertools`). Real version transitions. | Authentic Official Source | **Train** | Factoid Ans, Temporal Near-Miss Unans, Entity Attribute Near-Miss Unans |
| `src_grp_gsa_travel_hist` *(existing)* | Enterprise Policy | GSA FTR Bulletins FY2023 & FY2024 (Lodging, M&IE, Supersession). | Authored Summary | **Train** | Procedural Ans, Compound Ans, Compound Partial Unans, Superseded Ans |
| `src_grp_corp_procurement` *(Batch 2)* | Enterprise Policy / Compound | Fictional Northstar IT approval thresholds, software channel and renewal rules, delivery SLAs, warranty tiers, and explicit scope wording. | Synthetic Benchmark Document | **Train** | 4 Factoid Ans, 2 Compound Ans, 4 Qualified Ans, 1 Entity Near-Miss, 1 Temporal Near-Miss, 1 Compound Partial, 2 Unresolvable Ambiguity |
| `src_grp_syn_initech_travel_conflict` *(new)* | Enterprise Policy | Initech Engineering Guide vs Corporate Operations Manual (2024 meal per diem: $45 vs $65). | Synthetic Unresolved Conflict | **Train** | Genuine Unresolved Conflict Unans (`conflicting_sources`) |
| `src_grp_adv_procurement_train` *(Batch 2)* | Adversarial | Synthetic Northstar Procurement FAQ with legitimate expedited-order facts and a separately labeled untrusted ADMIN_OVERRIDE overlay. | Synthetic Benchmark Document + Synthetic Adversarial Overlay | **Train** | 2 Robust Grounded Ans, 3 Adversarial Hijacking Refusals |
| `src_grp_py_sys` *(new)* | Technical API | Python 3.11 & 3.12 system modules (`os`, `pathlib`, `sys`). | Authentic Official Source | **Dev** | Factoid Ans, Procedural Ans, Temporal Near-Miss Unans |
| `src_grp_syn_acme_travel_conflict` *(existing)* | Enterprise Policy | Acme Global HR handbook vs Finance travel manual (2024 domestic meal stipend: $50 vs $75). | Synthetic Unresolved Conflict | **Dev** | Genuine Unresolved Conflict Unans (`conflicting_sources`) |
| `src_grp_cloud_storage_tier` *(new)* | Ambiguity / Scope | Cloud storage pricing and retention tiers (Standard vs Coldline vs Archive). | Synthetic Benchmark Document | **Dev** | Qualified Ans (Scope Resolved), Ambiguous Question Unans |
| `src_grp_adv_travel` *(existing)* | Adversarial | Authentic GSA Travel FAQ with embedded `[ADMIN_OVERRIDE: ...]` injection payload. | Synthetic Adversarial Overlay | **Dev** | Robust Grounded Ans, Adversarial Refusal Unans |
| `src_grp_rust_time_iter` *(new)* | Technical API | Rust standard library reference manuals (`std::time`, `std::iter`). | Authentic Official Source | **Test (Held-Out)** | Factoid Ans, Procedural Ans, Feature Gap Unans |
| `src_grp_gsa_travel_mileage` *(existing)* | Enterprise Policy | GSA FTR CY2024 POV Mileage Reimbursement ($0.67 vs $0.21). | Authored Summary | **Test (Held-Out)** | Procedural Ans, Entity Attribute Near-Miss Unans |
| `src_grp_state_dept_travel` *(new)* | Enterprise Policy | State Dept Foreign Affairs Manual (FAM) travel allowance & rest-stop rules. | Authored Summary | **Test (Held-Out)** | Compound Ans, Compound Partial Unans, Procedural Ans |
| `src_grp_univ_grant_conflict` *(new)* | Enterprise Policy | University Sponsored Research Policy vs Faculty Handbook (international per diem: $400 vs $600). | Synthetic Unresolved Conflict | **Test (Held-Out)** | Held-Out Genuine Unresolved Conflict Unans |
| `src_grp_adv_hr_benefits_test` *(new)* | Adversarial | Synthetic Benefits Guide with delimiter-escape injection (`### SYSTEM COMMAND:`). | Synthetic Adversarial Overlay | **Test (Held-Out)** | Held-Out Robust Grounded Ans, Held-Out Injection Refusal Unans |

---

## 2. Question Distribution Matrix & Classification Scheme

The **60 Answerable / 40 Unanswerable** ratio is an operational target to balance evaluation, not a rigid quota that overrides corpus reality. Every question has a single, mutually exclusive primary classification to prevent double-counting.

### 2.1 Mutually Exclusive Primary Classification Scheme
* **Answerable Questions (`is_answerable = true`):**
  * `factoid`: Single-hop factual lookup.
  * `procedural` / `policy`: Multi-step rule execution, date-boundary validation, or supersession resolution (e.g., Q9 supersession, Q10 date boundaries, Q24 effective dates). In evaluation reporting, these map to the `Procedural Policy Answerable` matrix row.
  * `compound`: Synthesis of $\ge 2$ evidence spans where all required premises are present in the corpus.
  * *Cross-cutting metadata:*
    * `ambiguity_type`: Recorded exclusively for `Qualified Answer (Ambiguity Resolved)` cases where underspecified scope admits distinct valid readings. Policy and supersession questions without multiple valid scopes must have `ambiguity_type = None`.
    * `expected_safe_behavior`: Recorded for robust factual answers under adversarial context.
* **Unanswerable Questions (`is_answerable = false`):**
  * `off_topic` / `entity_attribute_near_miss`: Premise refers to non-existent attributes or ungrounded entities.
  * `temporal_near_miss`: Premise valid in another version but absent/invalid in the indexed corpus version.
  * `compound_partial`: At least one required premise is present, but at least one required premise is absent.
  * `conflicting_sources`: Two co-equal authorities assert mutually exclusive claims under identical scope with no supersession.
  * `ambiguous_question`: Question is fundamentally underspecified and admits multiple contradictory interpretations without qualification.
  * `adversarial_injection`: Question derives validity exclusively from an untrusted injection payload.

### 2.2 Global Target Allocation Matrix

| Category / Failure Mode | Train (Provisional: 50) | Dev (Provisional: 20) | Test (Provisional: 30) | Total Target |
|:---|:---:|:---:|:---:|:---:|
| **Factoid Answerable** | 10 | 4 | 6 | **20** |
| **Procedural Policy Answerable** | 8 | 3 | 4 | **15** |
| **Compound Answerable ($\ge 2$ spans)** | 6 | 2 | 4 | **12** |
| **Qualified Answer (Ambiguity Resolved)** | 4 | 2 | 2 | **8** |
| **Robust Grounded (Adversarial Context)** | 2 | 1 | 2 | **5** |
| *Subtotal Answerable* | *30* | *12* | *18* | *60* |
| **Off-Topic / Entity Near-Miss** | 4 | 2 | 2 | **8** |
| **Temporal Near-Miss (Version Gap)** | 4 | 1 | 3 | **8** |
| **Compound Partial Unanswerable** | 4 | 2 | 2 | **8** |
| **Conflicting Sources (Unresolved)** | 3 | 1 | 2 | **6** |
| **Ambiguous Question (Unresolvable)** | 2 | 1 | 2 | **5** |
| **Adversarial Hijacking Refusal** | 3 | 1 | 1 | **5** |
| *Subtotal Unanswerable* | *20* | *8* | *12* | *40* |
| **TOTAL** | **50** | **20** | **30** | **100** |

---

## 3. Held-Out Test Methodology & Statistical Limitations

### 3.1 Statistical Limitations of Small Subcategories
* A 30-question test partition provides improved diversity over the 1-question pilot, but does **not guarantee narrow statistical confidence intervals**.
* Within specific failure subcategories (e.g. 2 conflicting source questions or 2 compound partial questions), a single question flip changes category accuracy by 50 percentage points.
* **Reporting Standard:** Subcategory results on Test must report raw counts, exact proportions, and standard errors, avoiding overstated claims of generalizability.

### 3.2 Leakage Prevention Rules
1. **Source Isolation:** Documents assigned to Test never appear in Train or Dev.
2. **Version Co-location:** If Document A and Document B belong to the same software version chain or policy revision series, both must reside in the same split.
3. **Cross-Question Paraphrase Screening:** Normalized token Jaccard screening ($> 0.60$) flags question pairs across splits. Flagged pairs must be manually adjudicated to confirm they do not probe the same underlying passage.
4. **Sealed Evaluation:** Model prompts and abstention thresholds ($\tau$) are calibrated strictly on Dev. Test labels remain sealed until final benchmark evaluation.

---

## 4. Provenance Taxonomy & Quality-Control Gates

### 4.1 Extended Provenance Taxonomy
Every document in `data/benchmark/sources_manifest.json` is categorized with explicit distinction between underlying source text and synthetic prompt-injection overlays:
* `authentic_official_source`: Direct verbatim excerpt from authoritative public documentation (e.g., Python docs, Rust docs).
* `authored_summary`: Verified policy figures and regulations structured into concise prose summaries based on real-world publications (e.g., GSA bulletins, State Dept FAM).
* `synthetic_benchmark_document`: Fully authored synthetic domain documents created to model specific procedural rules, multi-hop dependencies, or tiered scopes (e.g., Corporate Procurement Guidelines, Cloud Storage Service Tiers).
* `synthetic_unresolved_conflict`: Deliberately constructed equal-authority document pairs asserting mutually exclusive factual claims under identical scope with no supersession clause (e.g., Initech meal per diem, Acme meal allowance, University research per diem).
* `synthetic_adversarial_overlay`: An explicit prompt-injection payload embedded into an underlying document (whether authentic or synthetic), where the underlying text provenance is separately documented from the injection payload coordinates (`injection_spans`).

### 4.2 Quality-Control Workflow
1. **Automated Evidence Verification:** Every evidence span is verified by automated script: `doc.text[start_char:end_char] == span.text` with deterministic ID `{doc_id}_s{start}_{end}`.
2. **Independent Dual Review:** 100% of unanswerable and compound questions undergo independent annotation by two reviewers.
3. **Agreement Reporting:** Both Cohen's $\kappa$ and raw percentage agreement are recorded. Qualitative disagreement notes are reviewed before adjudication.
4. **Pre-Sealing Gate:** Final programmatic check via `load_dataset` ensuring 0 schema errors, 0 cross-split source group leakage, and immutability hash generation.

---

## 5. Phased Authoring Schedule (Expanding from 13 to 100 Questions)

The remaining 87 questions are authored in four incremental, reviewable batches:

| Batch ID | Focus & Content | Target Split | New Qs | Split Total | Benchmark Total |
|:---|:---|:---:|:---:|:---:|:---:|
| **Existing Pilot** | Phase 2C-1 baseline (Python core, GSA lodging/mileage, Acme conflict, Travel FAQ) | Mixed (Train: 9, Dev: 3, Test: 1) | Baseline | — | **13** |
| **Batch 1** | Train Expansion Part 1: Expand `src_grp_py_core`, expand `src_grp_gsa_travel_hist`, ingest `src_grp_syn_initech_travel_conflict` (new Train conflict pair). | **Train** | **+21** | Train: 30 | **34** |
| **Batch 2** | Train Expansion Part 2: Add synthetic Northstar procurement rules and a separate FAQ with a clearly marked adversarial overlay in `src_grp_corp_procurement` and `src_grp_adv_procurement_train`. | **Train** | **+20** | Train: 50 *(Complete)* | **54** |
| **Batch 3** | Dev Split Completion: Ingest `src_grp_py_sys` (system APIs), `src_grp_cloud_storage_tier` (ambiguity), expand Acme conflict & Travel FAQ. | **Dev** | **+17** | Dev: 20 *(Complete)* | **71** |
| **Batch 4** | Held-Out Test Construction: Ingest `src_grp_rust_time_iter`, expand `src_grp_gsa_travel_mileage`, ingest `src_grp_state_dept_travel`, `src_grp_univ_grant_conflict`, `src_grp_adv_hr_benefits_test`. | **Test** | **+29** | Test: 30 *(Complete)* | **100** |
| **Batch 5** | Pre-Sealing Audit: Full programmatic cross-validation, Jaccard paraphrase screening, cryptographic SHA-256 seal of Test split. | Sealed | **+0** | — | **100** |
