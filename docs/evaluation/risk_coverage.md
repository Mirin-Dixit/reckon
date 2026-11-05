# R1 synthetic risk-coverage analysis

R1 has three checkpoints: R1.1 statistical engine; R1.2 matched comparisons,
uncertainty, read-only API and minimal visualization/export; R1.3 regression,
manual acceptance and an approved Git checkpoint. The local synthetic-only R1
scope has completed automated acceptance and received final manual browser
acceptance from the project owner. Empirical evaluation, held-out Test completion
and production readiness are not established.

## Data boundary and contracts

`app.evaluation.risk_coverage` defines frozen, versioned analysis contracts
(`ragbench.risk-coverage.v1`). `from_experiment` validates an existing P4 experiment
and selects exactly one declared policy. `from_p4_job` additionally checks the
saved job's configuration, dataset/runtime fingerprints, IDs, counts and duplicated
observation snapshots against its result. Inputs are copied, never modified.
Source experiment/run IDs and a SHA-256 of the serialized source record retain
traceability. Configuration snapshots are canonical finite JSON strings; typed
score validation reuses the existing score contracts.

R1.1 accepts only synthetic Train/Dev records with explicit seed, dataset hashes,
synthetic generation identity and runtime source fingerprint. Historical records
are bound to their recorded source, not falsely required to match today's code.
Incomplete records retain their selected population; duplicate policy/question
observations, foreign IDs and contradictory provenance are rejected. No SQLite
connection, job submission, freeze creation or mutation of a P4 record is needed.

Gold is consumed only by this evaluator-side adapter after execution. It never
enters retrieval, generation or policy inputs. Arbitrary trusted Python callbacks
and monkeypatches are not sandboxed; these functions are not a security boundary
against code already executing inside the process.

## Operating points

For **one policy** on a fixed set of N distinct selected question IDs:

| Symbol | Meaning |
| --- | --- |
| A | Successful ANSWER |
| B | Successful ABSTAIN |
| C | Successful CLARIFY |
| E | Recorded execution failure, including timeout/refusal/incomplete |
| M | Missing observation |

`N = A+B+C+E+M`. Primary **end-to-end coverage** is `A/N`.
**Successful-execution coverage** is `A/(A+B+C)`, retaining the denominator in
TARGET_SPEC section 7.3. Both include explicit numerator and denominator and are
null at zero denominator. ABSTAIN and CLARIFY are uncovered, distinct outcomes.
Failures and missing observations are never classified as abstentions.
Failure and missing rates use N; both retain the corresponding question IDs.

Selective risk is incorrect answers / A, defined only when A > 0 and all A
answers have judgments. Judgment completeness is known answer judgments / A.
With U unknown judgments and K known errors, risk is null and its identification
bounds are `[K/A, (K+U)/A]`. These are not confidence intervals. With A=0,
risk, judgment completeness and risk bounds are null, even if N>0.
Missing observations prevent curve-area calculation; their absence never creates
a zero-risk result. Known risk on the observed answers can still be reported.

Adapters default to unknown judgments. An explicit `lexical_proxy=True` computes
the existing normalized exact-match proxy (including loss=1 for answering a
negative fixture). Its name and notice remain **synthetic lexical proxy, not
verified semantic correctness**. No human judgments are invented. All analysis
here is non-empirical development evidence, not research performance.

## Genuine threshold sweeps

`app.evaluation.threshold_sweep.run_synthetic_sweep` accepts a validated existing
P4 `ExperimentRequest` with exactly one threshold policy and fail-fast disabled.
It uses only the server-owned fictional fixtures, deterministic fixture runtime,
native BM25/cosine/RRF indexes and native threshold policy. It never uses a real
embedding/model provider, stored P4 job or answered-only ranking diagnostic.

A discovery execution retrieves **every** selected question. Every subsequent
threshold re-executes that same population, including previously abstained or
failed questions. Inclusive `>=` and `<=` comparators and the configured
missing-score action are preserved. Equal scores enter together. Available
scores are never imputed for unavailable values. Automatic grids contain every
distinct score and a finite `nextafter` reject-all boundary; an all-unscored
population has one attainable point under its configured missing-score action.
Explicit grids are bounded to 128 distinct finite thresholds. They must cover
every native acceptance partition before area is reported. A sparse grid is
reported as incomplete, not silently interpolated into an exact AURC.

The entire bounded fixture population (at most ten questions through the P4
request contract) is rerun per point. Reports include discovery/trial execution
counts. Numerical outputs are deterministic; experiment UUIDs and UTC timestamps
are fresh, so source-record fingerprints are not expected to be identical across
separate runs. Provenance is checked within each sweep. Evidence, scores, gold,
cohort, seed, runtime and configuration must remain stable; overlapping answers
must retain the same output and loss. Answered sets must be nested in sweep order.

## Right-step AURC and partial domains

For attainable points ordered by increasing end-to-end coverage, integrate
`sum((coverage[j]-coverage[j-1]) * risk[j])`. Tied coverage adds no area.
The zero-answer endpoint has undefined risk; no risk=0 origin is fabricated.
The first positive point supplies the right-step height from an observed zero
endpoint. Non-monotone risk is retained, never smoothed.

`full_aurc` is available only for an exhaustive, judged, complete sweep spanning
`[0,1]`. Otherwise an exhaustive curve with a positive interval reports
`partial_aurc` **and its actual coverage bounds**, without extrapolation or
renormalization. Stable failures can cap coverage below 1; missing-score ANSWER
can impose a floor above 0. A single point or an all-zero-answer curve has no
positive interval and no area. Unknown answer judgments, missing observations,
sparse grids and threshold-dependent failures have explicit undefined reasons.
Incompatible provenance or non-nested/different answers are rejected.
`right_step_area` is a low-level helper: the caller must certify exhaustive native
threshold boundaries; the supported sweep runner performs that certification.

Hand fixture: scores `.9,.8,.8,.1`, losses `0,1,0,1`. Attainable coverage/risk:
`(0,null), (1/4,0), (3/4,1/3), (1,1/2)`.
Right-step area: `(1/2)*(1/3)+(1/4)*(1/2) = 7/24`.

## Validation and limits

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_risk_coverage.py backend/tests/test_threshold_sweep.py -q --basetemp "$env:TEMP\reckon-r1"
.\.venv\Scripts\python.exe -m ruff check backend
git diff --check
```

Tests block network and SQLite access for synthetic integration, exercise native
threshold comparators/directions/ties, and check accounting, unknown/missing data,
partial areas, serialization and provenance drift. Existing P4 schemas, records,
SQLite databases, freeze receipts, benchmarks and review files remain untouched.
R1.1 introduced no API, frontend or uncertainty estimates. The separate R1.2
extension below adds these without changing the R1.1 contracts or formulas.
Held-out and empirical evaluation remain unavailable.

## R1.2 matched comparisons and uncertainty

`app.evaluation.matched_analysis` validates complete, identical question sets by
ID, not order, for 1–24 policy configurations and at most ten fixture questions.
Split, dataset, seed, retrieval settings, generation identity, software/runtime
provenance, question gold fingerprints and retrieved evidence/scores must match.
Only policy configuration may differ. Duplicated policy configurations, repeated
question observations, missing questions and conflicting snapshots are rejected;
there is no silent intersection or pooling. Failures are valid recorded outcomes,
not missing observations or abstentions. Reports contain source experiment IDs,
record fingerprints and a compatibility fingerprint, never gold answers/spans.

Operating-point differences are left minus right on the matched population.
Both named coverage definitions and failure rates are compared. Conditional risk
differences are withheld unless end-to-end coverage is equal and both risks are
defined. Equal coverage does not imply identical answered subsets; this limitation
is disclosed. Raw thresholds from different score families are never compared:
different retrieval configurations fail compatibility validation.

The deterministic paired bootstrap defaults to 2,000 resamples, seed 0, with a
2–5,000 resample limit and a signed 32-bit seed. One draw resamples question IDs
jointly across **all** policies and all saved threshold trials. Multiplicities are
weights, not fictitious new observations. The estimator recalculates both coverage
ratios, risk and failure rates for every draw. With declared complete question-family
metadata, whole families are sampled with replacement and every member is retained;
unequal-size families can produce varying replicate population sizes. No automatic
semantic clustering is claimed. P4 has no declared family field, so the API uses
question-level resampling and discloses its independence assumption. The engine's
trusted `families` argument supports future explicit declarations without changing
P4 storage. It requires exactly one nonempty family assignment per question.

Reports give matched question count, resampling-unit count (questions or families),
cluster sizes, seed, requested resamples and valid/undefined replicate counts per
metric and difference. These are observable sample-unit counts, not a claim that
the statistical effective sample size or independence is known. Percentile intervals
use linear interpolation at 2.5% and 97.5%. Intervals are withheld if the estimate
is undefined, **any** replicate is undefined, or fewer than two resampling units
exist. This avoids silently conditioning on successful replicates. A constant
bootstrap distribution is flagged as degenerate; a zero-width interval is not
evidence of certainty. Small synthetic samples cannot support significance,
calibration, generalization or empirical correctness claims.

### Saved threshold curves and area comparisons

The read-only analysis path never reruns retrieval, generation or synthetic
experiments. It groups saved native threshold trials that differ only in threshold,
checks every native acceptance partition including the reject-all boundary, then
uses R1.1 right-step integration. Every trial must cover all selected questions.
Answered-only ranking is never used. A single saved point or a sparse set of
thresholds cannot become a full curve. Without saved complete trials, the UI shows
operating points and explicitly unavailable AURC.

Curves must retain stable scores/evidence, nested answers, identical repeated
answer outputs/losses, compatible provenance and stable failures. Curve bootstrap
resamples the same questions jointly across the saved trials and reintegrates
the resulting step curve. Area uncertainty is withheld when any draw has no
positive interval or a different coverage domain. Area differences require
compatible full/partial domains, identical populations and metric/loss definitions;
undefined or incompatible area comparisons stay undefined. No partial area is
renormalized or compared as if it were full AURC.

## Read-only API and results interface

```text
GET /api/v1/experiments/{job_id}/analysis
  ?resamples=2000&seed=0&lexical_proxy=true
  &compare={additional_saved_job_id}
```

Response version: `ragbench.matched-analysis.v1`. `compare` may repeat up to seven
times (eight distinct saved jobs total). `threshold_only=true` explicitly selects
only the threshold policy from each saved job; this permits curves from all-policy
P4 jobs without silently pooling repeated controls. The default compares all
policies and rejects duplicated configurations across jobs. UUIDs, limits and compatible
complete synthetic Train/Dev cohorts are validated. `lexical_proxy` defaults to
false: unknown judgments remain unknown. The UI explicitly opts into the labeled
synthetic lexical proxy. Only terminal jobs with complete snapshots are eligible;
early-stopped jobs are rejected. Failure observations remain failures. Only known
P4 synthetic IDs are accepted. No paths, providers, prompts, Test split, model
settings, arbitrary family maps or analysis-write operations are accepted.

`app.db.analysis_reader` opens the server-configured existing SQLite file with
`mode=ro`, sets `query_only`, and reads requested jobs in one transaction. It does
not initialize `ExperimentStore`, acquire its process lock, recover jobs, create a
database or touch freeze receipts. Payloads are capped at 2 MiB per job; SQL length,
busy timeout and progress deadline are bounded. P4 rollback-journal format is
required. WAL is explicitly rejected rather than ignoring uncheckpointed data
with `immutable=1` or risking shared-memory sidecar creation. Incompatible/corrupt
records return safe 422 errors, missing jobs 404, and unavailable storage or busy
analysis capacity 503. Only one analysis runs at a time. Local host/client and
exact-origin guards are reused; no wildcard CORS or public deployment permission
is added. Successful responses are `Cache-Control: no-store`.

The existing Experiment Results section now has an explicit Analyze control,
optional additional saved experiment IDs, accessible SVG axes and table values,
policy/difference tables, area bounds, uncertainty disclosures and JSON export.
The plot labels its primary axis **end-to-end coverage A/N**; the second coverage
definition remains separately named in the table. Only supported native threshold
series receive connecting step lines. Unknown risk is never drawn at zero.
Response schema snapshots and numerical consistency checks validate untrusted
payloads. Existing bounded byte reads, loopback URLs, timeouts, abort cleanup,
safe text rendering and credential omission are reused. Cancelling stops waiting
and invalidates stale updates; it does not claim backend computation stopped or
alter saved experiments. No new dependencies or model calls are needed.

R1.2 validation commands:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_matched_analysis.py backend/tests/test_analysis_api.py backend/tests/test_risk_coverage.py backend/tests/test_threshold_sweep.py backend/tests/test_experiment_jobs.py backend/tests/test_experiment_cors.py backend/tests/test_evaluation.py backend/tests/test_gold_isolation.py backend/tests/test_scores.py backend/tests/test_decision_policies.py -q --basetemp "$env:TEMP\reckon-r12"
.\.venv\Scripts\python.exe -m ruff check backend
git diff --check
cd frontend
npm.cmd test
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

## Accepted synthetic-only scope and historical validation

R1.3 automated acceptance previously recorded **962 passing backend tests** using
a short Windows TEMP basetemp. The latest comprehensive frontend refinement pass
recorded **272 passing frontend tests** and **179 passing relevant backend
API/integration tests**, plus successful TypeScript, ESLint, production build,
Ruff and diff checks. These counts are historical accepted results, not fresh
executions made by this documentation update.

Real loopback HTTP checks used mocked inference and disposable synthetic storage
for mutations. Read-only analysis of the existing saved P4 Dev experiment also
succeeded, with reproducible reports and unchanged SQLite/protected-file hashes.
The project owner subsequently accepted browser rendering and navigation and
inspected the analysis JSON export; this is user-reported manual acceptance, not
a claim that the agent performed those browser checks.

This acceptance covers local synthetic research infrastructure and frontend
integration only. Lexical proxy risk is not verified semantic correctness. No
empirical benchmark performance, held-out Test evaluation, benchmark acceptance,
calibration, statistical generalization or production readiness is claimed. P5
is outside this checkpoint. Local commits remain subject to the approved scope
and final staged-tree verification.
