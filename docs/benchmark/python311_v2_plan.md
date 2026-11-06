# Python 3.11 benchmark v2: source and review plan

Status: B2 Batch 2 candidate authoring and offline validation; **not a released or
human-verified benchmark**. Batch 3 now has a [ready human-review queue](human_review_workflow.md)
with zero recorded human decisions and a blocked freeze. The accepted mixed-domain pilot and sample fixtures
remain unchanged.

## Current implementation, superseding historical planning status

The separately versioned [candidate dataset](../../data/benchmark_v2/python311_3_11_9/README.md)
contains 34 authentic source pages pinned to CPython v3.11.9 commit
`de54cf5be371a6f5e2e9f208c38def5f81d3ef02`, plus the upstream license files.
The moving 3.11 documentation URL is not treated as immutable provenance.
The actual capture uses 3.11.9 rather than the newer patch contemplated below.

There are 160 machine-authored candidates: Train 96, Dev 24, Test 40;
96 answerable and 64 negative/clarification candidates, with the category quotas
below. Four are qualified answers, eight require clarification and six are
compound. Source hashes, exact span coordinates, annotation consistency,
near-miss parent ownership and structural split checks are implemented.
There are **zero human reviews**; semantic entailment, corpus-wide negative
verification, independent overlap review and Test freeze remain pending.

`app.evaluation.benchmark_v2.CandidateRecord` implements the separate strict
`ragbench.question.v2` contract, without changing legacy Question or runtime
behavior. It adds explicit `diagnostic_spans` for related negative evidence,
`ambiguity_interpretations` instead of the planned free-text `ambiguity_note`,
candidate/verification statuses and versioned loading for offline curation only.
There is no accepted-data export or evaluation-runner adapter in this batch.
The human gate rejects the current records. The ledger binds the full annotation
and corpus; a deterministic 18-record ordinary-answer sample requires a second
review in addition to mandatory dual review of hard cases.

Run structural validation with:

```powershell
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe -m app.evaluation.benchmark_v2 data/benchmark_v2/python311_3_11_9
```

No model inference, model downloads, Test evaluations or application dataset
switching occurred. Independent human verification is the next acceptance gate,
not automatic permission to start Batch 3.

## Historical Batch 2A design (preserved)

The planning text below records the earlier design, including then-future source
capture and schema work. Statements such as "not captured yet" or "planned
loader" refer to Batch 2A; the current implementation status is above.

## Scope and counts

The approved target is 160 human-verified questions: Train 96, Dev 24, Test 40;
96 answerable and 64 negative/clarification examples. This exceeds the historical
100/30 MVP gate and meets TARGET_SPEC sections 4 and 12 (150 minimum, Test 40).
The pilot's 54 and the sample's 10 are not counted toward the new target.

| Primary category | Train | Dev | Test | Total |
|---|---:|---:|---:|---:|
| Answerable | 58 | 14 | 24 | 96 |
| Off-topic | 5 | 1 | 2 | 8 |
| Temporal near-miss | 10 | 2 | 4 | 16 |
| Entity near-miss | 7 | 2 | 3 | 12 |
| Attribute near-miss | 7 | 2 | 3 | 12 |
| Unsupported false premise | 5 | 1 | 2 | 8 |
| Unresolved ambiguity / CLARIFY | 4 | 2 | 2 | 8 |
| Total | 96 | 24 | 40 | 160 |

Four qualified-answer ambiguity cases are included within the answerable rows:
12 ambiguous examples overall (7.5%). Compound reasoning is a secondary tag.
These are authoring quotas, not permission to force unsupported labels. Do not
manufacture conflicting official text or mix synthetic policy material into the
authentic Python corpus. Any future injection overlays need separate approval,
provenance and reporting as auxiliary stress coverage.

## Proposed source inventory: 34 pages, not captured yet

Every listed path is relative to `https://docs.python.org/3.11/library/` and ends
in `.html`. These are proposed pages, not a claim that every section or immutable
snapshot has been verified. The current official site reports Python 3.11.18;
capture must resolve the corresponding CPython tag to an actual 40-hex commit.
Do not invent that commit or a hash. A moving `/3.11/` URL alone is not a snapshot.

| Cluster | Provisional split | Official library page paths | Pages |
|---|---|---|---:|
| containers | Train | `collections.html`, `collections.abc.html` | 2 |
| iterators-functions | Train | `itertools.html`, `functools.html`, `operator.html` | 3 |
| data-model | Train | `dataclasses.html`, `copy.html`, `enum.html`, `typing.html` | 4 |
| filesystem | Train | `pathlib.html`, `os.html`, `shutil.html`, `tempfile.html`, `glob.html`, `fnmatch.html` | 6 |
| dates-time | Train | `datetime.html`, `calendar.html`, `zoneinfo.html`, `time.html` | 4 |
| numeric | Dev | `math.html`, `decimal.html`, `fractions.html`, `statistics.html` | 4 |
| serialization | Dev | `json.html`, `csv.html` | 2 |
| concurrency | Test | `asyncio-task.html`, `concurrent.futures.html`, `threading.html`, `queue.html` | 4 |
| networking | Test | `urllib.parse.html`, `urllib.request.html`, `http.client.html` | 3 |
| database | Test | `sqlite3.html` | 1 |
| process-control | Test | `subprocess.html` | 1 |

Train topics deliberately include datetime, pathlib, collections, dataclasses,
functools and itertools because pilot/sample development already exposed them.
Do not promote previously seen questions or their paraphrases to Test. New Test
annotations must be fresh. Public-document model pretraining is not excluded by
this split design, and should be disclosed separately.

Split quotas are per question, not proportional to page count. The four proposed
Test clusters initially reserve ten questions each; feasibility must be verified
before authoring. This is not a statistical guarantee of independent examples.

### Source capture and license requirements

Reference sources:
- Official library index: https://docs.python.org/3.11/library/index.html
- License and notices: https://docs.python.org/3.11/license.html
- Immutable source template:
  `https://raw.githubusercontent.com/python/cpython/<commit>/<snapshot_path>`

Python documentation is under the PSF license agreement. Documentation code
examples are also available under the Zero-Clause BSD license; preserve notices
and review any separately attributed material. Store `license_id=PSF-2.0`,
`code_license="PSF-2.0 OR 0BSD"`, the applicable copyright notice and the license
page reference in the dataset-level release documentation.

Each captured source uses the strict `ragbench.source.v2` record implemented in
`app.evaluation.benchmark_review.SourceRecord`:

| Field | Rule |
|---|---|
| `schema_version` | Exact `ragbench.source.v2` |
| `source_id`, `document_id`, `cluster_id` | Nonblank, whitespace-free IDs; source/document IDs unique |
| `split` | `train`, `dev` or `test`; belongs to the approved component |
| `source_url` | HTTPS, exact `docs.python.org`, Python 3.11 library HTML path; no credentials, query or control characters |
| `python_version` | Exact `3.11.<patch>`; must match captured Document.version |
| `snapshot_revision` | Actual immutable CPython commit, 40 lowercase hex digits |
| `snapshot_path` | Verified `Doc/library/<name>.rst` path from that commit; not guessed from an HTML name |
| `retrieved_at_utc` | Timezone-aware UTC capture timestamp, distinct from Python release date |
| `raw_sha256` | SHA-256 of exact captured RST bytes |
| `text_sha256` | SHA-256 of the exact UTF-8 Document.text used for span coordinates |
| `extraction_version` | Exact `rst-identity-lf-v1` |
| license fields | Values above plus a nonblank copyright notice |

The initial extraction is intentionally simple and testable: strict UTF-8 decode,
CRLF and lone CR converted to LF, all other characters and RST markup retained.
No Unicode normalization, HTML renderer, inferred summaries or content rewriting.
`validate_source_snapshot` verifies that transformation as well as both hashes,
document ID, URL, version and absence of synthetic injection flags. A changed
extractor is a new extraction version requiring renewed review. Full RST content
can be long; token-budget suitability must be checked before later experiments.

No source file, commit hash, capture timestamp or source-content digest is
populated by this planning batch. The capture process must independently verify
that bytes really came from the declared commit/path; offline hash checks cannot
authenticate the network origin or prove that a supplied commit exists.

## Topic and split isolation

1. Give each page one owning cluster/split before drafting candidates.
2. Build a declared overlap graph linking shared answer-bearing content, copied
   examples, API aliases, version families, compound dependencies and near-miss
   pairs. All nodes in a connected component must have one split.
3. Treat standard-library cross-references as review triggers, not automatic
   evidence overlap. Compare the actual factual premises and examples.
4. In particular, audit process-control versus filesystem and networking versus
   serialization. Merge/reassign provisional groups if facts overlap; never
   preserve a numerical quota by splitting a component.
5. Screen exact normalized question text, token similarity and human-assessed
   paraphrases. Check against pilot/sample development material as well as v2.
6. `validate_source_isolation` rejects duplicate IDs, shared canonical HTML page,
   raw/text hash or cluster across splits, cross-split declared edges and unknown
   edge endpoints. It does not discover undeclared semantic overlap.

Do not change the pilot's source groups. The new split manifest and overlap edges
are separate artifacts. Test is held out for tuning/evaluation, not omitted from
the shared retrieval corpus: all corpus documents may be indexed without gold.
Human verification may inspect Test annotations; runtime inference may not.

## Taxonomy mapping and version boundary

| v2 category/annotation | Existing schema equivalent | Requirement |
|---|---|---|
| answerable | `is_answerable=true`, `expected_answer`, `evidence_spans` | Complete sufficient spans; category null in legacy Question |
| off_topic | `off-topic` | Preserve v2 canonical spelling in review data |
| temporal_near_miss | Same | Missing requested facts, not a supported negative answer |
| entity_near_miss | `entity_attribute_near_miss` | Preserve entity subtype in v2; do not silently collapse it |
| attribute_near_miss | `entity_attribute_near_miss` | Preserve attribute subtype in v2 |
| false_premise | No dedicated legacy category | Requires versioned annotation/export support before runtime use |
| ambiguous_question | Same; `ambiguity_type=clarification_required` | Explicit expected CLARIFY and clarification instructions |
| qualified answer | Answerable plus `ambiguity_type=qualified_answer` | Expected ANSWER; enumerate supported interpretations |
| compound | `question_type=compound` and compound premise/span fields | Secondary dimension, not a new abstention policy |

The v1 `Question`, loader, API contracts, evaluator metrics and pilot JSONL are
unchanged. A versioned annotation contract is necessary to represent the approved
taxonomy faithfully. This batch implements only `ragbench.review.v2` attestations
and source checks, not a new question loader/exporter or schema migration.
False-premise examples cannot be sent through the legacy loader yet. No fallback
to another category is permitted. The future adapter needs explicit approval and
must preserve evaluator-only labels and corpus snapshot selection.

### Planned candidate annotation fields (design, not an implemented loader)

Required fields: `schema_version=ragbench.question.v2`, `dataset_version`, `id`,
`question`, `split`, `cluster_id`, `source_document_ids`, `near_miss_parent_ids`,
`is_answerable`, `category`, `expected_decision`, `ambiguity_type`, `is_compound`,
`expected_answer`, `expected_safe_behavior`, `absence_note`, `evidence_spans`,
`compound_required_spans`, `compound_missing_premises`, `ambiguity_note`, `notes`,
`author_id`, `candidate_revision`, `corpus_sha256`. Required nullable fields stay
explicitly null; required list fields stay explicit lists. Reject unknown fields,
duplicate IDs, unknown documents/parents and cross-split parent dependencies.

`is_answerable` must agree with expected ANSWER; clarification is distinct from
ABSTAIN even though both are non-answering examples. Answerable references must
entail every claim and carry sufficient spans; negatives require corpus-wide
absence notes, not merely absent retrieval results. A supported "No" or a complete
premise correction is answerable and must not fill an unsupported-false-premise
quota. Ambiguity requires independently plausible alternatives and missing intent.

Spans reuse existing EvidenceSpan semantics and deterministic IDs:
`{doc_id}_s{start}_{end}`; zero-based Unicode code points, half-open `[start,end)`,
strict integer boundaries, nonempty text and exact document slice equality.
No byte/UTF-16 indexing or normalized/fuzzy quote matches. Distinct compound
premises have distinct spans; required-span IDs exactly match present evidence.
Missing premises are descriptions, never dummy spans.

## Candidate-to-human-review workflow

1. Capture and approve immutable sources, extraction, overlap graph and corpus
   manifest before generating questions. Existing document validation still runs.
2. Codex may draft candidates only after approval. Keep them separate from accepted
   data, include author/revision, and never treat generation as ground truth.
3. Compute candidate_sha256 over the complete annotation JSON (excluding its own
   digest and subsequent review log). Compute corpus_sha256 over the canonical,
   sorted source manifest including all content hashes and split/overlap mappings.
   Use sorted keys, UTF-8, compact JSON, no non-finite numbers and no Unicode
   normalization (`canonical_digest`). Canonical hashes and raw-file hashes have
   distinct names and purposes.
4. A first human reviews all candidate claims and cited originals, deriving an
   initial answerability/evidence judgment before viewing the proposed label and
   rationale. Do not show the
   prior review verdict to a second first-pass reviewer. All negatives, ambiguity
   and compound cases require two distinct human reviewers, neither the author.
5. Randomly select at least 20% of remaining ordinary answerable cases for an
   independent second review using a recorded seed. This release-level sample gate
   is planned; the per-record checker does not implement the sample selection.
6. Record answerability/reference/evidence, source/split, corpus-wide negative
   searches, ambiguity interpretations and compound-premise checks as applicable.
   Review text must document actual work, not repeat a model's claim of absence.
7. Any non-accept verdict blocks eligibility without revision or adjudication.
   A third human adjudicator, distinct from author and first-pass reviewers, may
   resolve a complete disagreement. Bind adjudication to the exact ordered review
   log hash. An edited candidate/corpus or review log invalidates prior approval.
8. Compute independent agreement before adjudication (raw agreement and Cohen's
   kappa); the historical guide's kappa >=0.70 gate applies. Report undefined kappa
   honestly, and do not claim observed agreement without actual human decisions.

Implemented ReviewItem fields: `schema_version=ragbench.review.v2`, candidate ID,
candidate/corpus hashes, author ID, canonical category, expected decision, compound
flag, ambiguity type, reviews and optional adjudication. Human decisions require
reviewer ID, literal actor_kind=human, candidate/corpus hashes, UTC timestamp,
accept/revise/reject verdict, checklist keys, rationale and an explicit independent
first-pass attestation. Adjudications instead add review_set_sha256 and may see
prior reviews. Checklists must include source, split, answerability, evidence,
plus reference_answer, negative_absence, ambiguity and compound where applicable.

`acceptance_issues` hashes the supplied complete current candidate, binds author
and review-policy metadata to that candidate, and checks reviews against the
current corpus digest. It returns structural review blockers. An empty result is eligibility only, not proof of human
identity, factual correctness, independence, corpus exhaustion or release freeze.
There is no automatic accept/export action, network access or model call.

## Gold isolation and release gate

The new module lives under evaluation and is not imported by ordinary API,
retrieval, generation or the current evaluation runner. An architectural test
guards that separation. Existing gold-isolation tests stay intact. Review metadata
and complete candidate records must never become document metadata, prompts,
retrieval parameters or policy inputs. Trusted arbitrary Python code/dynamic
imports remain outside the architectural guard's sandboxing guarantees.

Freeze only after 160 approved records meet counts, every offset and reference
passes, overlap/duplicate reviews close, reviews and adjudications are current,
agreement gates pass and the human-reviewed immutable Test membership is approved.
Bundle source revision/license notices, raw/text/file hashes, annotation and review
schema versions, overlap graph, reviewer logs and a dataset fingerprint. Record
future intentional changes as a new release; do not overwrite pilot history.
All later expansion must recheck corpus-wide absence because added documents can
make previously unanswerable questions answerable. No Test model evaluation before
freeze; tune prompts and thresholds on Train/Dev only.

Offline validation commands:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_benchmark_review.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check backend
git diff --check
```

Next approval gate: inventory and split/overlap design review, then pinned source
capture and the candidate annotation/export schema implementation. Candidate
authoring cannot honestly begin against uncaptured sources or be accepted through
the legacy loader by coercing labels.
