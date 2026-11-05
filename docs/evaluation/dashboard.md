# Evaluation Dashboard foundation (P5.1)

Open `http://127.0.0.1:3000/evaluation` after starting the local frontend and
backend with the existing setup commands. The Evaluation Results navigation item
opens this dashboard; Experiments retains submission, observation inspection and
existing JSON exports. Dashboard reporting/export enhancements belong to P5.2.

## Read-only integration

The dashboard lists saved experiments, selects a persisted result snapshot and
requests existing R1 analysis. It never submits experiments or invokes models.

- `GET /api/v1/analysis/experiments?limit=20&offset=0`: bounded metadata history.
- `GET /api/v1/analysis/experiments/{id}`: selected saved result.
- `GET /api/v1/experiments/{id}/analysis`: existing R1 analysis, with its existing
  bounded bootstrap, comparison, judgment and threshold-only options.

The first two routes are necessary because the P4 history/results dependencies
initialize a writable worker with interrupted-job recovery. Dashboard reads use
R1's SQLite `mode=ro`, `query_only` transaction instead, without initializing the
store or runtime. They use the same configured experiment database, enforce local
access and synthetic Train/Dev identities, and send `Cache-Control: no-store`.
An absent database produces empty history without creating a file. Unsupported
WAL databases, corrupt/oversized records and unavailable storage fail explicitly;
they are never repaired or silently replaced. P4's rollback-journal store remains
unchanged. Trusted arbitrary Python callbacks are not sandboxed.

## Research interpretation

All currently supported results are synthetic development fixtures, not empirical
performance evidence. Unknown judgments are the default; opting into synthetic
lexical exact-match proxy judgments does not establish semantic correctness.
Both end-to-end coverage A/N and successful-execution coverage A/(A+B+C) retain
their R1 definitions. Execution failures, missing observations, incomplete
judgments, undefined risk and unavailable uncertainty remain distinct.

The dashboard reuses the R1 plot and intervals. It shows operating points without
joining unrelated policies; native threshold curves show only their recorded
coverage domain. Partial area is never presented as full AURC or extrapolated.
Small samples and undefined bootstrap replicates retain backend disclosures.

Comparison candidates on the current history page are screened by saved metadata
only. They are provisional until the R1 endpoint validates full matched cohorts,
evidence, generation provenance and compatible policy configurations. Different
splits, fingerprints, retrieval settings or repeated controls are not silently
compared. Threshold-only mode can exclude repeated controls in native trials.
Refreshing, switching experiments or changing settings clears stale analysis.
Cancelling stops browser waiting; it does not claim server computation stopped.

## Manual acceptance

1. Open Evaluation Results at desktop and 390px width. Check table scrolling,
   readable history, visible focus and the mobile workspace menu.
2. Select an existing synthetic experiment; verify saved ID, split, counts,
   settings, seed and fingerprints against Experiments. Refresh and paginate.
3. Analyze with unknown judgments, then explicit lexical proxy opt-in. Inspect
   both coverage definitions, undefined risk, sample sizes and disclosures.
4. Where saved threshold trials exist, use threshold-only comparisons. Confirm
   incompatible candidates explain their disabled state and R1 rejects any
   remaining provenance mismatch. Inspect partial domains/undefined AURC.
5. Cancel or change selection during loading; old reports must not reappear.
   Stop the backend and refresh: show a safe error, not empty success or raw
   exception text. Restart and retry without creating a new experiment.
6. Confirm no dashboard action starts inference, changes a freeze or requests
   held-out Test data. Existing exports remain accessible from Experiments.
