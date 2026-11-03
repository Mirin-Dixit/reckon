# RAGBench implementation roadmap

The finished product is defined by the local `TARGET_SPEC.md`; this roadmap
orders implementation and acceptance work without redefining that target.
Track functional application milestones separately from the weighted S1-S13
target scorecard. Neither a passing unit suite nor an earlier report alone
establishes milestone completion.

## Pre-flight evidence

Fresh pre-P1 validation: 258 backend tests and 78 frontend tests passed; Ruff,
ESLint, TypeScript and the production build passed. Pytest emitted one
Starlette/httpx deprecation warning. These results establish a baseline, not
live model quality, browser acceptance or statistical generalization.

The frozen mixed-domain pilot contains 17 documents and 54 questions: 50 Train,
3 Dev and 1 Test. It does not satisfy the future Python 3.11 benchmark scope.
The separate sample fixture has 5 documents and 10 questions defaulting to Dev.
Neither is sufficient for a reported held-out research evaluation.

The ordinary runtime currently loads validated documents only; evaluation
loads and fingerprints documents and questions together. Existing isolation
tests passed in this baseline. P1 must preserve and reverify this boundary,
not reintroduce gold loading. Trusted arbitrary Python callbacks are not
sandboxed by this architectural boundary.

OpenAI readiness inspection found no installed SDK, configured model or
credential in the current process. No live provider calls were made.
Retrieval scores are not calibrated answerability probabilities; the current
answered-run ranking diagnostic is not a true threshold sweep.

## Current constraint update - zero spending

The user's zero-spending instruction supersedes the earlier OpenAI-first and
paid-cloud execution plans below. P1 uses local Ollama and an approved open-weight
model. OpenAI remains optional inactive adapter code. Installations and model
downloads require explicit approval; no paid APIs, credits or hosting are allowed.
Later embeddings and judging must also run locally with reviewed licenses.
Demonstration/deployment uses existing hardware; no paid cloud service is planned.
Historical pre-flight findings above remain historical, not current readiness.

## Pass 1 - Functional, research-backed RAGBench

### P1 - Live BM25 + local Ollama

- [x] Correct or reverify strict evaluator-only gold-label loading.
- [x] Configure the provider safely, including explicit model, timeout,
  bounded retries and output-token limits; keep credentials server-side.
- [x] Execute real BM25-backed answer generation through the actual versioned
  query HTTP route, after authorized local installation/model download; no paid calls.
- [x] Preserve execution failure versus intentional abstention and record
  effective settings, model/provider metadata, token usage and provenance.

Gate: isolation/provider/API regression tests pass; a documented real HTTP
answer cites supplied evidence, and failure paths remain distinguishable.
Do not claim live generation from mocked success.

Accepted 3 November 2026 for local BM25 integration only: Ollama 0.40.14,
`qwen3:4b-q4_K_M`, context 8192, top-k 3, output 1024, thinking disabled,
zero retries, concurrency 1, loopback and cloud disabled. Three genuine Train
HTTP requests returned 200: always-answer and threshold tau=0 on `q_pilot_020`
returned ANSWER; prompt-abstention on `q_batch2_011` returned ABSTAIN.
One adapter used 3/4 provider attempts; spending was ₹0. Exact citation offsets
and manual semantic support were verified. Backend validation: 380 tests passed,
Ruff and diff checks passed. Earlier validation failures and the memory-blocked
attempt remain documented in the API reference. No Test inference occurred;
this is not benchmark-wide reliability or generalization evidence.

### P2 - Retrieval + Confidence

- [x] Expose working dense and hybrid retrieval over HTTP.
- [x] Use real embeddings rather than mock-only semantic retrieval.
- [x] Return confidence/evidence scores from all three policies, explicitly
  identifying source, range, direction and calibration status.
- [x] Preserve distinctions among BM25, dense cosine, hybrid RRF and any
  model-reported confidence; do not equate relevance with sufficiency.

Gate: retrieval/score serialization tests and real HTTP checks cover all
retrieval-policy combinations, missing scores and provider failures.

P2 Batches 1-4 are accepted following offline and bounded genuine Train
verification. Local Ollama `all-minilm:22m` (384-dimensional F16) has digest
`1b226e2802dbb772b5fc32a58f103ca1804ef7501331012de126ab22f67475ef`.
Dense/hybrid HTTP retrieval reuses snapshot-specific indexes and the persistent
vector cache; typed scores remain explicitly uncalibrated and preserve provenance.

The initial live batch completed all nine retrieval/policy combinations, the
unsupported logo-color abstention, and a deliberate high-threshold evaluation:
10 query POSTs, one evaluation, 12 embedding calls and 13 generation attempts.
Three prompt ANSWER results had inconsistent ambiguity reason codes. Offline
remediation added 52 regression cases and explicit reason rules. The first
one-attempt targeted rerun validated ANSWER/other but returned HTTP 502 because
answer generation needed another call. The final fresh two-attempt rerun returned
HTTP 200 / succeeded / ANSWER / other with validated citation offsets and manual
semantic support under `api-v4` / `prompt-decision-v3`.

Validation: 649 backend tests, Ruff, dataset/hash and diff checks passed.
No Test inference, paid calls or benchmark edits occurred; spending was INR 0.
Historical failures and raw captures are preserved. This accepts local integration,
not benchmark-wide retrieval quality, calibration or generalization. See the API
reference for recorded budgets, caveats and final targeted results. P3 implementation
is complete through Batch 3 offline checks; manual browser acceptance is pending.

### P3 - Query Lab

- [ ] Build working query controls against the live backend.
- [ ] Display real answers, abstentions, clarification, execution failures,
  evidence and citations safely.
- [ ] Complete manual browser acceptance checks.

Gate: automated UI/API tests and desktop/mobile keyboard/browser checks cover
loading, success, malformed responses, connection failures and cancellation.

The original acceptance checkboxes remain open until manual acceptance.
Batch 3 verifies all nine retrieval/policy combinations through the actual FastAPI
ASGI route and real retrieval/pipeline implementations with deterministic fake
embedding/generation transports. This is offline integration evidence, not live
model verification. ANSWER, ABSTAIN, CLARIFY and execution failure are tested
independently. No P3 live inference was authorized or performed. Browser automation
was unavailable (browser host/native connection unavailable); desktop/mobile,
keyboard focus and screen-reader acceptance remain manual gates. See the
[manual checklist](../frontend/README.md#p3-final-manual-acceptance).

### B2 - Benchmark v2 (parallel workstream)

Begin immediately alongside P1; its placement here is not a serial dependency
on P3.

- [ ] Audit existing questions, evidence, source provenance and near-miss pairs.
- [ ] Establish Python 3.11 source scope and topic clusters; keep related
  near-miss questions in the same held-out group.
- [ ] Reach at least 100 verified questions, including at least 30 held-out Test.
- [ ] Human-review evidence and annotations.
- [ ] Freeze Test assignments and the dataset fingerprint before reported Test
  experiments, documenting every intentional annotation/split change.

Gate: loader and exact-offset checks pass, source/topic leakage is reviewed,
review decisions are recorded, and the immutable Test freeze is approved.

### P4 - Experiment Runner

- [ ] Run experiments through the UI, starting with Train/Dev.
- [ ] Record effective retrieval, policy and generation configurations,
  dataset fingerprints, seeds and software/provider provenance.
- [ ] Select and freeze thresholds using Dev only.

Gate: experiment round-trip and matched-question comparison tests pass;
HTTP/UI acceptance demonstrates reproducible Train/Dev runs without gold leakage.

### R1 - Selective-Prediction Evaluation

This roadmap's R1 label denotes future selective-prediction work. The earlier
milestone also called R1 concerned gold-data isolation; it is a separate scope.

- [ ] Implement genuine threshold-sweep risk-coverage analysis and AURC.
- [ ] Keep execution failures separate and define consistent denominators,
  score direction, ties and zero-coverage behavior.
- [ ] Run the frozen Test configuration once for the reported evaluation,
  only after B2 freeze; record failures honestly.
- [ ] Never substitute the existing answered-run ranking diagnostic for a
  genuine threshold-policy curve.

Gate: hand-calculated metric fixtures and sweep tests pass; Train/Dev HTTP
experiments establish the pipeline before the approved frozen Test run.

### P5-P6 - Dashboard and End-to-End Validation

- [ ] Display actual experiment results, policy comparisons and risk-coverage.
- [ ] Verify complete query/evaluation workflows.
- [ ] Test browser behavior, accessibility, mobile layouts and error states.

Gate: dashboard values reconcile with recorded runs; automated end-to-end and
manual browser acceptance checks pass. No fabricated results or polish-only
completion claims.

## Pass 2 - Full Target Specification

Complete the remaining S1-S13 requirements against their original acceptance
criteria, including:

- [ ] Full benchmark target of at least 150 questions.
- [ ] Validated semantic correctness judge and human agreement analysis.
- [ ] Bootstrap confidence intervals and statistical paired comparisons.
- [ ] Persistent experiment storage and asynchronous jobs.
- [ ] Authentication, rate limiting and spend caps.
- [ ] Docker Compose and cloud HTTPS deployment.
- [ ] GitHub Actions.
- [ ] Final research report and showcase.

Gate each increment with the corresponding specification evidence, automated
tests and appropriate HTTP/UI checks. Local prototype readiness is not public
deployment readiness. Recompute weighted target progress from verified
criteria independently of Pass 1 functional progress.

## Non-negotiable rules

1. The Test split is never used until B2 is frozen.
2. R1's reported Test run cannot start before B2 is frozen.
3. Prompts and thresholds are tuned using Train/Dev only.
4. No fabricated model results or dashboard metrics.
5. Gold labels never reach the runtime inference path.
6. Execution failures never count as abstentions.
7. Every feature requires automated tests and an appropriate HTTP/UI
   acceptance check.
8. Research correctness takes priority over frontend polish.
9. Never silently change benchmark annotations or split assignments.
10. Maintain separate progress tracking for the functional application and
    the weighted S1-S13 target specification.

The pre-flight loader inventory and baseline validation are inspection checks,
not Test inference experiments or tuning. Future research execution must obey
the freeze rules above. P1 and P2 are accepted within their explicitly documented local integration scopes.
