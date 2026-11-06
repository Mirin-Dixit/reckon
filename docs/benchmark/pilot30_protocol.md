# Python 3.11 pilot30 protocol v1

Scope change approved by the user on 4 November 2026. This is a separate,
exploratory validation track for the next application milestones. It does not
complete the original B2.3 gate or reduce the full benchmark's requirements.
Protocol ID: `python311-pilot30.v1`. Current state: **30 selected candidates,
zero pilot reviews, unaccepted, no pilot freeze, no empirical runs**.

## What is preserved

The full `data/benchmark_v2/python311_3_11_9/` tree, original candidate/source
hashes, 16 packets, annotations, ledger and 160-question/250-review acceptance
policy remain unchanged. Its Test split remains unfrozen. The older 54-question
mixed-domain pilot in `data/benchmark/` and sample fixtures are also unchanged.
The new pilot is a reference selection over the existing records, not regenerated
questions or a reduced source corpus. All 34 pinned Python 3.11.9 documents remain
the corpus against which positive support and negative absence must be checked.

## Deterministic selection and proposed composition

The executable contract is `app.evaluation.pilot30`, with immutable v1 settings in
`data/pilot30/python311_3_11_9_v1/protocol.json` and membership in `selection.json`.
These coordinator files contain proposed labels and must not be sent to blind
reviewers. The selection method uses no model outputs or correctness measurements.

1. Preserve original roles: Dev candidates supply the 15 development questions;
   original Test candidates supply the 15 held-out questions. No Train records.
2. Exclude the known AI-discussed IDs `py311v2_test_027`, `py311v2_train_064` and
   `py311v2_train_065`, then exclude their entire connected positive-anchor/child
   families. This produces 11 exclusions in the pinned parent version. The seed
   list is recorded, rather than silently changing with local browser files.
3. Within each original split, select one of each negative/clarification category
   by ascending SHA-256 of UTF-8 `ragbench-pilot30-v1:<candidate_id>`, then ID.
4. Include every selected record's positive anchors, including clarification
   anchors. Ensure an answerable representative of every eligible topic cluster,
   using the same rank where needed. Fill remaining answerable places to nine
   using that rank. If constraints cannot be met, fail; never silently resample.
5. Sort the selected records by SHA-256 of UTF-8
   `ragbench-pilot30-v1:review:<candidate_id>`, then ID, for three blind packets
   of ten. Packet order is not sorted by category or evaluation role.

| Proposed category | Dev | Held-out | Total |
|---|---:|---:|---:|
| Answerable | 9 | 9 | 18 |
| Off-topic | 1 | 1 | 2 |
| Temporal near-miss | 1 | 1 | 2 |
| Entity near-miss | 1 | 1 | 2 |
| Attribute near-miss | 1 | 1 | 2 |
| False premise | 1 | 1 | 2 |
| Clarification | 1 | 1 | 2 |
| Total | 15 | 15 | 30 |

Selected Dev topics are numeric and serialization; held-out topics are concurrency,
networking, database and process control. Counts are candidate-selection quotas,
not human-verified facts. A rejected/reclassified record blocks release pending an
explicitly documented protocol revision. Never force a label to preserve a quota,
change parent annotations, or replace a question because a model performs poorly.

The protocol binds the parent corpus, parent integrity inventory and historical
pilot/sample questions. Selection binds every candidate's full canonical annotation
hash, original split, protocol hash and deterministic leakage screen. Parent drift
or changed membership invalidates this version; do not repair hashes to conceal it.
The leakage screen is an alarm list, not semantic independence certification.

## Independent human verification and acceptance

The same two distinct real humans each review all 30 records: **60 first-pass
review submissions minimum**, plus an independent third adjudicator where needed.
The author cannot review their own candidates. Reviewers must derive first-pass
judgments without AI suggestions, proposed annotations, or another reviewer's work.
Seeing coordinator label metadata can disqualify a blind first pass for affected
questions. Local reviewer IDs are attestations, not verified human authentication.

Use the existing review interface and schema: save a whole packet's first pass,
explicitly reveal annotations, inspect exact passages/full documents, and record
checks, evidence, rationale and actions. Corpus-wide negative checks, version
boundaries, complete references, ambiguity branches, compound premises, historical
exposure, cross-split overlap and license notices all require actual human work.
Q1/Q2's old assisted notes remain unchanged and never count toward these 60 reviews.

The separate `review_ledger.jsonl` uses existing `ragbench.review.v2` records and
starts with empty review lists. Validated UI/CLI receipts are **not imported**.
Intentional curation must preserve original submissions and verify actual human
provenance before placing reviews in the pilot ledger. No automatic ledger import,
human identity creation or freeze command is provided.

The pilot gate requires:

- Exactly two distinct first-pass reviewers per record, the same pair across all
  30; valid actor/independence attestations and current hashes/checklists.
- Exact explained evidence and structured first-pass judgments from the existing
  submission validator. Accepting a proposed label cannot erase a divergent first
  pass. Non-accept verdicts require revision or current independent adjudication.
- Pre-adjudication answerability Cohen's kappa >=0.70 over all 30. Raw agreement,
  decision agreement and category agreement are reported too. Undefined kappa
  blocks acceptance; agreement of accept/reject verdicts is not a substitute.
- Human closure of source/reference semantics, corpus-wide negative checks,
  split/historical overlap, flagged duplicate pairs, licenses and the held-out
  protocol/exposure log.
- Explicit human pilot-freeze approval bound to protocol, selection and the exact
  review-ledger hash. The optional `release_approval.json` follows
  `pilot30.ReleaseAttestation`; it is not generated or approved by this implementation.

`validate --require-acceptance` is read-only. A passing result establishes recorded
release eligibility under these attestations, not authenticated humans or an
independent semantic proof. It cannot accept the full benchmark. Every intentional
selection/annotation/review change needs revalidation and renewed approval.

## Development and empirical-use boundary

**P4, R1 and P5 infrastructure development with clearly labeled synthetic fixtures
may proceed now. Neither 60 reviews nor pilot acceptance is a prerequisite for
writing/testing the runner, metric contracts, persistence, charts or UI.** This
scope implements the pilot protocol and interface profile, not those milestones.
Fixture outputs must not be presented as empirical results.

Empirical pilot evaluation is allowed only after the separate pilot gate passes,
with separately authorized local inference. Use only the 15 Dev questions for
prompt/configuration development or threshold selection. Freeze the operating
configuration before the 15-question held-out evaluation; no held-out tuning.
Evaluate held-out questions once per reported frozen configuration and retain
every attempt/failure in the exposure and provenance log.
Gold annotations stay in evaluator/curation code, never retrieval or prompts.
No pilot evaluator-to-runtime adapter is introduced here; P4 must enforce this
gate and record protocol/selection/corpus fingerprints when integrating it.

R1 empirical risk/AURC requires real predictions and human semantic correctness
judgments or a separately validated judge. Existing lexical metrics and the
answered-run ranking diagnostic cannot be relabeled as semantic risk or a true
threshold-policy curve. Declare denominators, failures, score direction, ties,
zero-coverage behavior and uncertainty methods before the reported held-out run.
P5 must identify fixture versus empirical mode and the dataset/experiment source.

All pilot findings are **exploratory**. Report Dev/held-out sample sizes, true
accepted class counts, raw numerators/denominators, unavailable measurements and
uncertainty with its method/limitations. Each held-out negative category and
clarification has n=1; subgroup differences cannot support strong conclusions.
Near-miss/anchor families and source topics are dependent: an IID question bootstrap
does not establish independence. Any grouped uncertainty estimate will itself be
fragile with so few groups. No statistical-conclusiveness or generalization claim.

Record all pilot-held-out IDs exposed by a final run. Their later reuse cannot be
described as a fresh untouched Test sample in a future full-benchmark study. The
full Test files and gate stay intact; future full evaluation needs an exposure
audit rather than an assertion that the original B2.3 gate passed.

## Local review and checks

From the repository root, with the existing environment:

```powershell
$env:PYTHONPATH = 'backend'
$reviewerId = Read-Host 'Your real reviewer identifier (no spaces)'
.\.venv\Scripts\python.exe -m app.evaluation.review_app --reviewer $reviewerId --pilot --port 8010
```

Stop any previous review process with Ctrl+C first, or choose a different local
port. Open `http://127.0.0.1:8010`. Confirm the `python311-pilot30.v1` profile and three
packets. Source search/evidence navigation and first-pass locking are unchanged.
The default command without `--pilot` still serves all 16 full-benchmark packets.
Pilot drafts are separate at
`.ragbench-cache/human-review/browser/python311-pilot30.v1/<first-16-selection-hash>/<reviewer-hash>/`.
The full selection hash is checked inside every saved workspace.
Reuse the same ID/profile to resume; use distinct real IDs for separate reviewers.

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.pilot30 validate
.\.venv\Scripts\python.exe -m app.evaluation.pilot30 validate --require-acceptance
.\.venv\Scripts\python.exe -m app.evaluation.pilot30 check-submission data/pilot30/python311_3_11_9_v1 PATH_TO_EXPORTED_REVIEW.json
```

The acceptance command currently must fail. `create` creates references and an
empty ledger only in a new directory and refuses overwrites; it never recreates
the original benchmark. Do not run it to reset reviews. Existing manual/template
Q1/Q2 reconciliation still requires the separately documented approval procedure.
