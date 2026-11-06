# Python 3.11.9 benchmark v2 candidates

**Not a human-verified benchmark. Not frozen. Not enabled for evaluation.**
Version: `python311-3.11.9-candidates.1`. All 160 machine-authored records have
`status=candidate` and `verification_status=machine_checked_human_pending`.
There are zero human reviews and zero human-review-eligible records.
The existing 54-question mixed-domain pilot is unchanged.

B2 Batch 3 provides a [human-review queue](human_review/README.md), with blind
first-pass packets, separate proposed annotations, exact source passages and blank
decision forms. See the [coordinator workflow](../../../docs/benchmark/human_review_workflow.md)
before sharing material with reviewers. There are still zero completed human
reviews; review-packet fingerprints do not constitute a benchmark freeze.

## Inventory

| Category | Train | Dev | Test | Total |
|---|---:|---:|---:|---:|
| Answerable | 58 | 14 | 24 | 96 |
| Off-topic | 5 | 1 | 2 | 8 |
| Temporal near-miss | 10 | 2 | 4 | 16 |
| Entity near-miss | 7 | 2 | 3 | 12 |
| Attribute near-miss | 7 | 2 | 3 | 12 |
| False premise | 5 | 1 | 2 | 8 |
| Clarification | 4 | 2 | 2 | 8 |
| Total | 96 | 24 | 40 | 160 |

Four answerable records carry qualified-answer ambiguity; together with eight
clarifications, this is 12 ambiguous candidates (7.5%). Six records are compound:
four answerable, two missing a required performance premise. These are candidate
annotations, subject to revision rather than quota-driven acceptance.

The 34 source pages belong to 11 provisional topic clusters. Train owns
containers, iterators/functions, data model, filesystem and dates/time; Dev owns
numeric and serialization; Test owns concurrency, networking, database and process
control. Page/cluster ownership and all near-miss parent links stay within splits.
There are no shared 12-token sequences across splits in selected evidence or
diagnostic spans. This lexical check is not a semantic leakage guarantee.
All 34 pages are captured; 33 currently supply selected spans (`collections.abc`
is contextual corpus material without a selected span).

## Authentic source snapshot

The source is CPython **v3.11.9**, resolved through the official GitHub tag API:

- Annotated tag object: `7cd4a91608030a5a404220c0beb1f307de84af26`.
- Immutable commit: `de54cf5be371a6f5e2e9f208c38def5f81d3ef02`.
- Raw URL pattern:
  `https://raw.githubusercontent.com/python/cpython/de54cf5be371a6f5e2e9f208c38def5f81d3ef02/Doc/library/<module>.rst`.
- Reader-facing URLs: `https://docs.python.org/3.11/library/<module>.html`.
  These URLs can move with patch releases; the captured commit is authoritative.
- Canonical source manifest SHA-256:
  `688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c`.

`sources_manifest.json` records each actual UTC capture time, raw/text hashes,
snapshot path, version, provenance, license and provisional split ownership.
The 34 library files contain 1,387,935 raw bytes in total; bundled license files
are additional. `documents.jsonl` retains complete RST text, converting only CRLF
or lone CR to LF. No summaries or synthetic documentation have been substituted.
RST roles, examples and markup remain part of the exact offset coordinate space.
Offsets are zero-based Unicode code points, half-open, not bytes or UTF-16 units.

The original proposed inventory discussed the then-current moving documentation;
the captured dataset deliberately pins a reproducible 3.11.9 release instead.
It does not establish behavior in Python 3.13. Temporal candidates change only the
requested version of their positive anchor, not the API or requested attribute.

Licenses: Python Software Foundation License Agreement (`PSF-2.0`);
documentation code examples additionally `PSF-2.0 OR 0BSD`. Original notices are
retained in `sources/LICENSE`, `sources/license.rst` and the captured pages.
License reference: <https://docs.python.org/3.11/license.html>.
Third-party attributions inside upstream pages still require release review.
Upstream whitespace is preserved; do not reformat captured sources.
Local `.gitattributes` prevents checkout newline conversion of hashed artifacts.

## Annotation and review files

- `candidates/{train,dev,test}.jsonl`: strict `ragbench.question.v2` records.
- `evidence_spans`: sufficient answer support proposed for answerable candidates.
- `diagnostic_spans`: actual nearby/counter-premise text for negatives and
  clarifications, never fabricated gold answers. Their presence does not prove
  corpus-wide absence.
- `near_miss_parent_ids`: positive anchors; related records remain in one split.
- `review_ledger.jsonl`: 160 `ragbench.review.v2` entries bound to the complete
  candidate and corpus hashes. Every `reviews` list is empty; adjudication is null.
- `review_plan.json`: pending gates and a reproducible 18-record (20% rounded up)
  second-review sample from 88 ordinary answerable records. All negatives,
  ambiguous and compound cases require two independent reviewers regardless.
- `integrity.json`: SHA-256 inventory of 43 data/source/review artifacts, excluding
  itself and explanatory files. Unsigned hashes detect drift, not hostile edits.

Typed validation lives in `app.evaluation.benchmark_v2`; the review and source
contracts live in `app.evaluation.benchmark_review`. Both are offline evaluator/
curation modules. They are not imported by query runtime or the evaluation runner.
The legacy ingestion schema, API, metrics and current dataset selection remain
unchanged. In particular, `false_premise` is not coerced into a legacy category.
An approved evaluator-only v2 adapter is still needed before future experiments.
No Test model runs or threshold selection have occurred for this dataset.

## Human verification required before acceptance

1. Derive an answer and exact supporting passages from the pinned documents
   before viewing the candidate annotation; record independent first-pass work.
2. Check each claim, API identity, patch/version, boundary case and reference
   answer. Quote matches establish coordinates, not logical entailment.
3. For every negative, search **all 34 documents**, including examples and alternate
   wording. Reject/reclassify if a grounded correction or complete answer is
   available. Future-version absence cannot be inferred from low retrieval scores.
4. Inspect entity substitutions and requested attributes. Resource-guarantee and
   third-party-API candidates may be too easy or confounded; revise rather than
   claiming they establish challenging near-miss coverage.
5. For false premises, separate the supported correction from the unavailable
   requested facts. A fully answerable "No" is not an abstention example.
6. For ambiguity, independently establish both plausible interpretations and why
   a clarification is needed. Qualified answers must support both branches.
7. For compound cases, identify every necessary premise and span; partial support
   must not become a complete answer.
8. Compare candidate paraphrases and answer-bearing content against all splits
   and the pilot/sample. In particular inspect process-control versus filesystem
   and networking versus serialization. The declared cross-page overlap graph is
   currently empty, not independently certified complete.
9. Two distinct humans must review hard cases and the recorded ordinary sample,
   neither the author. Revisions invalidate hashes/reviews. Resolve disagreements
   through a third independent adjudicator bound to the review log.
10. Record pre-adjudication agreement/kappa (historical gate >=0.70), resolve
    licensing/overlap issues, then obtain explicit immutable Test-freeze approval.
    No agreement statistics or human review outcomes are claimed yet.

Trusted arbitrary Python callbacks, reflection and direct file access are not
sandboxed by the architectural import tests. Review attestations do not
authenticate human identities. Operational access controls remain a separate concern.

## Reproducible offline checks

From the repository root (no model calls or downloads):

```powershell
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe -m app.evaluation.benchmark_v2 data/benchmark_v2/python311_3_11_9
.\.venv\Scripts\python.exe -m pytest backend/tests/test_benchmark_v2.py backend/tests/test_benchmark_review.py backend/tests/test_gold_isolation.py
.\.venv\Scripts\python.exe -m ruff check backend
git diff --check
```

Adding `--require-human-acceptance` to the validator currently **fails** with
`Human verification incomplete; dataset cannot be frozen`. This is intentional.
There is no automatic release/export action. Structural checks do not complete
the independent human verification or establish benchmark quality/generalization.
