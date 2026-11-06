# Human review queue — pending

160 candidates; 90 need independent dual review and 70 need one review (250 minimum reviews). A/B denote blank assignment slots, not reviewer identities.

Work in packet order, ten candidates per packet: negatives/clarifications, then hard answerable cases, then the agreed ordinary second-review sample, then remaining answers. Each reviewer keeps a separate copy. Read blind.md and derive findings from the pinned corpus before opening annotations.md. Never view the other reviewer's completed form.

Fill actual identity, UTC date, independent-first-pass attestation, initial decision/category, findings, checks, rationale, searches and exact evidence in reviewer-A/B.json. Null/blank forms are deliberately invalid submissions and do not count as reviews.

Actions: accept, revise, reject or reclassify. Reclassification maps to the existing revise verdict and must include proposed_changes with a different category and consistent labels. Revise requires proposed changes too. No proposal is applied automatically. All edits require a new candidate revision/hash and renewed review.

Validate filled forms from the repository root with PYTHONPATH=backend:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.benchmark_queue check-submission data/benchmark_v2/python311_3_11_9 PATH_TO_FILLED_FORM.json
```

The command is read-only. It returns validated ledger-review/proposal receipts for curation, does not append reviews or change integrity hashes, and cannot authenticate humans. Preserve originals; actual receipt import and candidate changes require a reviewed curation step.

leakage_report.json contains lexical alarms, not semantic judgments. Inspect every flagged pair, including historical pilot/sample exposure and expected version-near-miss pairs. Record pair disposition/evidence/rationale separately for adjudication; no alarm is cleared automatically. Inspect unflagged paraphrases too.

No agreement score can be reported yet. After reviews, compute pre-adjudication agreement from independent annotation judgments, not accept/reject verdicts. Require the documented kappa gate, resolve all pair/licensing issues and obtain explicit Test-freeze approval. This directory's fingerprints identify review inputs; they are not a benchmark freeze.
