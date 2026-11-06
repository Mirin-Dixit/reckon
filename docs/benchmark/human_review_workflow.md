# B2 Batch 3: human review queue and blocked freeze

> **Scope update, 4 November 2026:** This workflow and its 250-review gate continue
> to apply unchanged to the full 160-question benchmark. The separately approved
> [pilot30 protocol](pilot30_protocol.md) uses 30 selected candidates and 60 genuine
> independent reviews. Launch this same interface with `--pilot` for its three
> packets and separate draft storage. Neither pilot selection nor its acceptance
> completes original B2.3. P4/R1/P5 infrastructure may proceed on labeled synthetic
> fixtures before pilot acceptance; empirical pilot use remains gated.

The [review queue](../../data/benchmark_v2/python311_3_11_9/human_review/README.md)
contains 160 candidates in 16 packets of ten. It is prepared for real human
review; it does not record completed human verification.

The minimum is **250 reviews**: 72 negative/clarification/qualified/compound
candidates require two, the agreed 18-record ordinary sample also requires two,
and the remaining 70 require one. Priority is hard cases, sampled second reviews,
then remaining ordinary answers. A/B are empty assignment slots, not identities.

## Coordinator and independent reviewers

1. The coordinator uses `human_review/queue.json` to assign distinct humans.
   Do not send the master queue, coordinator README, annotation packets or other
   reviewers' decisions during the blind first pass: their ordering/metadata can
   reveal proposed labels. Send **only `batch-NN/blind.md`, blank forms and the full
   pinned source corpus**. Preserve relative paths when distributing packets.
   This workflow relies on honest attestations, not a sandbox or access-control UI.
2. Each reviewer independently reads the complete relevant documentation and
   records an initial decision/category and findings before viewing proposed labels.
   For negatives, search all 34 pages and examples. Never infer corpus-wide absence
   from a retrieval result or a question's proposed category.
3. After those findings are saved, provide `annotations.md`: proposed labels,
   reference answer, safe behavior, missing premises, exact source text, Unicode
   `[start,end)` offsets, source/span IDs, pinned files and official reader URLs.
   Verify every reference claim, both ambiguity branches and compound premises.
4. Fill `reviewer-A.json` or a separate `reviewer-B.json` copy with the actual
   human identifier, actual UTC timestamp, first-pass attestation/judgments,
   required checks, exact evidence with a finding, search notes and rationale.
   `submission_schema.json` describes every field. Blank/null forms are deliberately
   invalid, and no identities, dates or verdicts have been filled automatically.
5. Select `accept`, `revise`, `reject` or `reclassify`. Accept requires explicit
   verification of all proposed spans. Revise/reclassify must supply an annotation
   patch in `proposed_changes`; reclassify must change category consistently with
   answerability, decision and evidence. It maps to the existing ledger's `revise`
   verdict. The original action and proposed new candidate are preserved in the
   validation receipt, without changing the current annotation.

From the repository root, validate a filled form without applying it:

```powershell
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe -m app.evaluation.benchmark_queue check-submission data/benchmark_v2/python311_3_11_9 PATH_TO_FILLED_FORM.json
```

The command rejects stale candidate/corpus hashes, author self-review, duplicate
reviewers, incomplete checks, invalid attestations and nonexact evidence. It emits
`validated_not_imported` receipts. It does not append reviews, apply proposals,
rewrite integrity metadata or certify human identity. Trusted arbitrary Python
code and direct file access are not sandboxed.

An actual receipt must be reviewed and imported into the existing hash-bound
ledger during curation. Preserve the original submission. The ledger's rationale
retains structured first-pass judgments, source checks and search notes. Applying
a proposed edit creates a new candidate revision/hash and invalidates earlier
reviews; source/split changes also require corpus-manifest revision and renewed
overlap checks. Recompute the integrity inventory only for an intentional,
reviewed update, not to conceal an unexpected mismatch.

## Duplicate and leakage alarms

The reproducible screen uses version-neutral TF-IDF cosine (>=0.72), token Jaccard
(>=0.65), explicit lexical equivalences and exact answer-evidence reuse. These are
curation alarms, not model scores or trained/calibrated decision thresholds.
It compares all candidate pairs and questions in the original pilot/sample.
No model or embedding inference is involved.

The current screen flags **28 pairs**: 16 declared temporal near-miss relationships
and 12 possible within-split redundancies (including reused answer passages).
It raises zero cross-split or historical-exposure alarms at these thresholds.
This does **not** establish semantic independence: lexical methods can miss
paraphrases and flag legitimate different questions. Independent reviewers must
also inspect unflagged pairs and the provisional source-overlap graph.

Use `leakage_report.json` and `pair_adjudication_templates.json`. Every template
is pending and binds the pair to its report hash and corpus hash. Record actual
reviewer/date, exact evidence, rationale and a disposition such as:

- distinct questions with legitimate shared evidence;
- intentional version/entity/attribute pair retained in one split;
- duplicate requiring revision/replacement;
- cross-split overlap requiring regrouping and renewed review;
- uncertain, requiring an independent adjudicator.

These are proposed disposition labels, not recorded findings. No pair has been
automatically cleared or reclassified. Do not move related questions across splits
to satisfy a numerical quota. No candidate or split assignment changed in Batch 3.

## Final acceptance and freeze gates

The existing validator checks source snapshots, artifact hashes, exact spans,
source/topic ownership, parent links, candidate/ledger bindings and review counts.
It currently passes structural validation and fails human acceptance:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.benchmark_v2 data/benchmark_v2/python311_3_11_9
.\.venv\Scripts\python.exe -m app.evaluation.benchmark_v2 data/benchmark_v2/python311_3_11_9 --require-human-acceptance
```

The second command must fail until required current, independent human approvals
exist. It is not a complete release certification: reviewers must also resolve
pair/source-overlap and licensing issues, validate corpus-wide negative labels,
compute pre-adjudication agreement from independent annotation judgments and meet
the documented kappa >=0.70 gate. Accept/reject verdict agreement is not a substitute
for annotation agreement. Report undefined kappa honestly.

Only after all these gates pass may the coordinator request explicit Test-freeze
approval and record immutable release membership/hashes. Review-packet hashes are
input identities, not a frozen benchmark. There is no automatic freeze command.

Current state: **0 human reviews, 0 accepted candidates, no observed human
disagreements to adjudicate, agreement unavailable, 28 pending machine-screened
pair reviews, Test unfrozen**. Independent human reviewers are the blocker.

Queue generation is deterministic and refuses to overwrite an existing directory:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.benchmark_queue build data/benchmark_v2/python311_3_11_9 NEW_REVIEW_OUTPUT_DIRECTORY
```

Keep filled forms outside regenerated output. No runtime contract, pilot data,
model inference, Test evaluation or experiment-selection behavior changes here.

## Local browser interface

Run the separate curation service from the repository root using existing installed
FastAPI/Uvicorn dependencies. No installation, inference or paid service is needed:

```powershell
Set-Location -LiteralPath 'C:\Users\Mirin Dixit\OneDrive\Desktop\ragbench'
$env:PYTHONPATH = 'backend'
$reviewerId = Read-Host 'Your real reviewer identifier (no spaces)'
.\.venv\Scripts\python.exe -m app.evaluation.review_app --reviewer $reviewerId --port 8010
```

Open `http://127.0.0.1:8010`. Use the same reviewer identifier after restarting to
resume. Each real reviewer uses their own identifier and process, preferably on
their own computer. On a shared machine, stop the prior reviewer's process with
Ctrl+C before starting the next, or use a different local port. The HTTP API cannot
select another reviewer or enumerate their files. This is workflow separation,
not authentication or protection against a person with filesystem access. Never
publish, reverse-proxy or tunnel this service. It is separate from the inference API.

1. Choose a packet. Decision/category choices start empty and come from the existing
   schema. Read the exact blind question; source searches are literal and cover all
   34 pinned documents. Search results show source names and line numbers. The full
   document viewer preserves the source text and identifies Python 3.11.9; compare
   this with the version actually requested by the question.
2. Write findings and notes about actual searches/readings. Indicate whether your
   judgment was independent or assisted/exposed. Neither is selected by default.
   An independent attestation is recorded only on your explicit save with that
   choice. Assistance cannot later be promoted to independence in this workspace.
3. Select a passage in the full source viewer, describe what you verified, and
   choose **Add selected passage**. The service constructs exact Unicode offsets,
   text and span ID from the pinned document. This does not infer semantic support.
   Passages are retained only when you save the question. Use Tab/Shift+Tab for form
   controls and Previous/Next for questions. Navigation warns about unsaved edits.
4. Save each first-pass judgment. After all ten are saved, explicitly reveal the
   packet's proposed annotations. The server locks the first-pass fields before
   returning annotations, including to direct API requests. No other reviewer's
   findings or verdicts are displayed. Revealing one packet does not reveal others.
5. Compare the proposals against complete sources. Personally complete each
   required check, add verified spans with findings, select your action, and record
   its rationale. Revision/reclassification proposals use the existing annotation
   patch contract; they never change the candidate automatically. The actual UTC
   annotation-save event supplies `reviewed_at_utc`; it is not a claimed prior review.
6. **Validate packet** runs the existing `Submission` and `validate_submission`
   checks. **Export JSON draft** downloads the existing submission format. Complete
   independent submissions can produce `validated_not_imported` receipts; assisted
   or incomplete drafts remain blocked. Exporting a draft does not make it valid.
   Use the existing CLI on the downloaded file as a separate check:

   ```powershell
   .\.venv\Scripts\python.exe -m app.evaluation.benchmark_queue check-submission data/benchmark_v2/python311_3_11_9 PATH_TO_EXPORTED_REVIEW.json
   ```

The page distinguishes saved first-pass entries, saved annotation reviews and
validated-not-imported submissions. None counts as an imported ledger review or
accepted benchmark candidate. There is no automatic ledger import, agreement
calculation or freeze action. The 250 independent-review requirement is unchanged.

### Draft storage and recovery

Browser workspaces are saved server-side at
`.ragbench-cache/human-review/browser/<SHA256-of-reviewer-id>/batch-NN.json`.
These are internal draft envelopes holding unchanged submission-shaped records
and UI phase/revision metadata; exports omit the envelope. They never overwrite
the generated `human_review/` templates or existing manual working copies. The
reviewer ID is hashed for safe path construction, not for identity verification.
Back up this ignored directory yourself if the drafts need long-term retention.

Writes use a temporary file and atomic replacement. Stale tabs and competing
writers are rejected rather than silently overwriting work. A failed save retains
the previous file and leaves your browser text available to copy or retry. A
malformed or hash-stale draft is refused without replacement. Keep a backup before
manual recovery. If a crashed process leaves `.write-lock`, stop every review
service using that reviewer directory before inspecting/removing that stale lock;
do not remove a lock from an active writer.

### Existing Q1/Q2 discrepancy — no automatic reconciliation

At implementation inspection, `py311v2_test_027` (Q1) has four first-pass fields
in `human_review/batch-01/reviewer-A.json`, which is a generated template. Its
packet fingerprint therefore differs from the original. Q2,
`py311v2_train_064`, has assisted notes in
`.ragbench-cache/human-review/batch-01-A/reviewer-A.json`. Both independence
attestations are null. Neither file has been restored, merged or rewritten by
the interface implementation; the benchmark ledger still records zero reviews.

Reconcile only with explicit approval: first back up both files, compare records
by candidate ID and hashes, then copy only the approved Q1 fields into the existing
working copy without replacing Q2 or unrelated fields. Record the AI assistance
and keep independence null. Restoring the generated template requires separate
approval and verification against its original packet fingerprint; do not rewrite
that fingerprint to legitimize an accidental edit.

The page's optional **Import as assisted notes** reads an explicitly selected JSON
file into an empty browser packet, copies only complete first-pass fields and
always leaves independence null. It does not reconcile either original file or
import final actions, identities, timestamps or independent attestations. Export
or back up drafts before further manual reconciliation. Imported assisted notes
cannot satisfy independent-review acceptance.

### Verification and manual acceptance

Automated checks, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_review_app.py backend/tests/test_benchmark_queue.py backend/tests/test_benchmark_review.py backend/tests/test_benchmark_v2.py backend/tests/test_gold_isolation.py
node --test backend/tests/review_ui.test.mjs
.\.venv\Scripts\python.exe -m ruff check backend
```

The Node tests use a minimal DOM/transport harness; they are not browser or
accessibility acceptance. Before accepting this interface, a human should:

- Launch locally; confirm Packet 1 matches `blind.md` and no labels are preselected.
- Search/open sources, check requested versus pinned version, and select a passage.
- Save a genuine first pass; restart with the same ID and verify it resumes.
- Try a second real reviewer ID and verify the first reviewer's work is absent.
- Verify early reveal is disabled; after all ten genuine first passes, reveal and
  verify the first-pass fields are locked. Do not invent judgments to test this.
- Complete an annotation review and run page/CLI validation on its export. Confirm
  assisted notes remain ineligible and nothing enters the ledger automatically.
- Check keyboard focus, narrow-screen reading, unsaved-change warnings and errors.

Manual acceptance of the interface is separate from acceptance of B2.3 or the
benchmark. Test remains unfrozen until all genuine independent-review/release gates
pass and the immutable freeze receives explicit approval.
