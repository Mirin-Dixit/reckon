# python311-pilot30.v1 — selected, unaccepted

This separately versioned exploratory pilot references 30 unchanged candidates
from the full Python 3.11.9 benchmark. It duplicates neither questions nor source
documents. All 34 original pinned documents remain the evidence corpus.

- Dev: 15 (9 answerable, one each of five negative categories, one clarification).
- Held-out: 15 with the same proposed composition. No original split reassignment.
- Review requirement: the same two independent humans each review all 30, minimum
  60 submissions; independent adjudication where required.
- Current status: zero pilot reviews, no agreement result, no release approval,
  no empirical evaluation. Selection quotas are not verified annotations.

`protocol.json` freezes the method, exclusions, parent hashes and pilot gates.
`selection.json` records exact IDs, canonical candidate hashes, original splits,
three packet assignments and deterministic overlap alarms. These coordinator
files reveal proposed labels; keep them away from blind first-pass reviewers.
`review_ledger.jsonl` uses the existing review schema and starts empty of reviews.
There is no automatic import or release approval. Changes require an explicit
versioned revision; do not overwrite parent records or silently reseed selection.

The complete [protocol](../../../docs/benchmark/pilot30_protocol.md) explains
selection, human acceptance, exploratory limitations and launch commands.
The browser interface is reused with `--pilot`; it saves reviewer drafts in a
separate ignored namespace. It does not change the original 16 review packets.

The full 160-question benchmark remains unaccepted, with its original 250-review
requirement and unfrozen Test. The older 54-question mixed-domain pilot remains a
different dataset. Q1/Q2's existing assisted notes retain their provenance and
do not count as independent pilot reviews.

P4/R1/P5 development with clearly labeled synthetic fixtures is permitted before
pilot human acceptance. Empirical pilot runs require acceptance plus separate
inference authorization. Tune only on Dev, then freeze configuration before the
15-question held-out evaluation. Pilot results must report counts/uncertainty and
remain exploratory. Runtime experiment integration is future P4 work.
