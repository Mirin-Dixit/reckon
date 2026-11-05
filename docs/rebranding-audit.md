# Reckon rebrand inventory

Independent final search uses case-insensitive `rag[\s_-]*bench` plus optional
Studio separators, over tracked and relevant untracked text, dotfiles and names.
No accidental active branding (category A) remains in the reviewed source set.
B = compatibility identifier; C = preserved research/history/provenance;
D = generated/ignored/external artifact. This inventory lists exact retained
source locations; line numbers refer to the rebrand working tree.

| File | Lines | Class | Why retained |
|---|---|---|---|
| `.b2_author.py` | 156, 315 | C | Immutable research/provenance or historical authoring artifact |
| `.gitignore` | 15 | B | Wire/schema/storage/legacy-reader compatibility |
| `README.md` | 104, 117, 353 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/api/experiment_models.py` | 28, 53 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/api/models.py` | 179, 363 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/api/routes/experiment_jobs.py` | 28 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/configuration.py` | 8, 11, 12 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/db/experiments.py` | 112, 234 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/benchmark_queue.py` | 218, 308, 434, 524, 547 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/benchmark_review.py` | 47, 196 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/benchmark_v2.py` | 48, 141, 208, 227, 256 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/matched_analysis.py` | 97, 98 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/pilot30.py` | 43, 140, 173, 253 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/results.py` | 13 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/review_app.py` | 45, 237, 299 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/risk_coverage.py` | 20, 77, 386, 445 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/evaluation/threshold_sweep.py` | 30, 31 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/generation/scores.py` | 51, 52 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/retrieval/cache.py` | 21 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/app/retrieval/runtime.py` | 125 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/tests/test_benchmark_queue.py` | 29 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/tests/test_benchmark_review.py` | 41, 93 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/tests/test_benchmark_v2.py` | 69 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/tests/test_deployment_contracts.py` | 67 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/tests/test_pilot30.py` | 95 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/tests/test_rebranding.py` | 17, 26, 30, 52 | B | Wire/schema/storage/legacy-reader compatibility |
| `backend/tests/test_review_app.py` | 260 | B | Wire/schema/storage/legacy-reader compatibility |
| `compose.legacy-state.yaml` | 5 | B | Wire/schema/storage/legacy-reader compatibility |
| `data/benchmark/sources_manifest.json` | 100, 113, 152, 165, 177, 178, 190, 191, 203, 204, 216, 217, 229, 230 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/README.md` | 78, 84 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-01/annotations.md` | 12, 77, 145, 210, 277, 344, 408, 473, 540, 607 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-01/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-01/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-02/annotations.md` | 12, 79, 145, 216, 281, 346, 412, 479, 545, 613 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-02/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-02/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-03/annotations.md` | 12, 77, 145, 213, 301, 369, 437, 505, 573, 661 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-03/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-03/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-04/annotations.md` | 12, 79, 146, 210, 274, 338, 403, 471, 538, 625 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-04/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-04/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-05/annotations.md` | 12, 76, 142, 210, 277, 344, 410, 477, 545, 611 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-05/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-05/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-06/annotations.md` | 12, 77, 169, 233, 298, 380, 445, 512, 581, 663 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-06/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-06/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-07/annotations.md` | 12, 78, 154, 220, 304, 384, 470, 556, 634, 715 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-07/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-07/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-08/annotations.md` | 12, 92, 172, 238, 303, 366, 429, 495, 558, 622 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-08/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-08/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-09/annotations.md` | 12, 74, 137, 199, 268, 333, 396, 460, 522, 589 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-09/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-09/reviewer-B.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-10/annotations.md` | 12, 75, 138, 201, 267, 333, 399, 464, 526, 588 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-10/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-11/annotations.md` | 12, 77, 142, 206, 270, 335, 399, 468, 535, 598 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-11/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-12/annotations.md` | 12, 75, 139, 204, 267, 331, 397, 461, 525, 590 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-12/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-13/annotations.md` | 12, 75, 139, 201, 264, 330, 394, 459, 524, 586 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-13/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-14/annotations.md` | 12, 76, 139, 205, 271, 333, 396, 462, 528, 601 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-14/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-15/annotations.md` | 12, 74, 139, 203, 266, 329, 396, 465, 532, 595 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-15/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-16/annotations.md` | 12, 76, 139, 202, 266, 331, 398, 462, 536, 613 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/batch-16/reviewer-A.json` | 3, 21, 39, 57, 75, 93, 111, 129, 147, 165 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/leakage_report.json` | 2 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/packet_hashes.json` | 2 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/queue.json` | 2 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/human_review/submission_schema.json` | 54 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/integrity.json` | 2 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/review_plan.json` | 2 | C | Immutable research/provenance or historical authoring artifact |
| `data/benchmark_v2/python311_3_11_9/sources_manifest.json` | 2, 10, 28, 46, 64, 82, 100, 118, 136, 154, 172, 190, 208, 226, 244, 262, 280, 298, 316, 334, 352, 370, 388, 406, 424, 442, 460, 478, 496, 514, 532, 550, 568, 586, 604 | C | Immutable research/provenance or historical authoring artifact |
| `data/pilot30/python311_3_11_9_v1/protocol.json` | 2, 5 | C | Immutable research/provenance or historical authoring artifact |
| `data/pilot30/python311_3_11_9_v1/selection.json` | 2, 188 | C | Immutable research/provenance or historical authoring artifact |
| `docs/api/api_reference.md` | 87, 113, 151 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/benchmark/human_review_workflow.md` | 194, 215 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/benchmark/human_review_workflow.md` | 139 | C | Existing repository, original deployment or workspace history |
| `docs/benchmark/pilot30_protocol.md` | 33, 39, 81, 162 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/benchmark/python311_v2_plan.md` | 25, 122, 127, 191, 199, 253 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/evaluation/dashboard.md` | 69 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/evaluation/evaluation_protocol.md` | 30 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/evaluation/risk_coverage.md` | 13, 201 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/rebranding.md` | 12, 14, 15, 18, 21, 22, 28 | B | Wire/schema/storage/legacy-reader compatibility |
| `docs/rebranding.md` | 32, 50 | C | Existing repository, original deployment or workspace history |
| `frontend/lib/analysis-api.ts` | 23, 29 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/lib/analysis-schema.json` | 7, 8, 484, 485 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/lib/api.ts` | 71 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/lib/evaluation-report.ts` | 37 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/lib/experiment-api.ts` | 7, 27 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/lib/experiment-schema.json` | 9, 375, 1331, 1484, 1606, 1728 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/lib/query-contracts.ts` | 17 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/lib/query-schema.json` | 867 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/next.config.ts` | 5, 9 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/tests/api.test.ts` | 254 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/tests/evaluation-dashboard.test.tsx` | 194 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/tests/evidence-ledger.test.tsx` | 21 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/tests/experiment-runner.test.tsx` | 210, 365, 392 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/tests/fixture_analysis.json` | 2, 400 | B | Saved versioned synthetic compatibility fixture |
| `frontend/tests/fixture_analysis_curve.json` | 2, 627 | B | Saved versioned synthetic compatibility fixture |
| `frontend/tests/fixture_job_result.json` | 2, 140, 181, 224, 338, 379, 422, 443, 555, 596, 639, 668, 817, 858, 901, 1015, 1056, 1099, 1120, 1232, 1273, 1316 | B | Saved versioned synthetic compatibility fixture |
| `frontend/tests/query-lab.test.tsx` | 123 | B | Wire/schema/storage/legacy-reader compatibility |
| `frontend/tests/risk-analysis.test.tsx` | 179 | B | Wire/schema/storage/legacy-reader compatibility |

## External/generated boundaries (D)

- `.git/`: original 21 commits, remote URL and historical identities; never rewritten.
- `.ragbench-cache/`: existing databases, inference caches and reviewer drafts.
- `backend/ragbench_studio.egg-info/` and `.venv/`: installed/generated metadata.
- `frontend/.next/`, `frontend/.test-build/`, `node_modules/`, old pytest temp
  directories, logs and `tmp/`: generated or pre-existing temporary artifacts.
- Old Docker containers/images/networks are retained stopped or cached; the
  existing data volume is explicitly mapped, not renamed or removed.
- The open repository root and actual GitHub repository remain named historically.

The R-shaped vector favicon is already appropriate for Reckon and is unchanged.
No file/directory rename is required: application modules use generic names.
No datasets, fixtures containing saved records, or review decisions are rewritten.

## Exact changed/new files

- `README.md`
- `backend/Dockerfile`
- `backend/app/__init__.py`
- `backend/app/api/__init__.py`
- `backend/app/api/dependencies.py`
- `backend/app/api/main.py`
- `backend/app/api/routes/health.py`
- `backend/app/configuration.py`
- `backend/app/evaluation/review_ui/index.html`
- `backend/app/generation/config.py`
- `backend/app/retrieval/runtime.py`
- `backend/tests/test_api.py`
- `backend/tests/test_api_hardening.py`
- `backend/tests/test_deployment_contracts.py`
- `backend/tests/test_experiment_cors.py`
- `backend/tests/test_gold_isolation.py`
- `backend/tests/test_ollama_provider.py`
- `backend/tests/test_openai_provider.py`
- `backend/tests/test_p1_runtime.py`
- `backend/tests/test_p6_security.py`
- `backend/tests/test_rebranding.py`
- `backend/tests/test_retrieval_http.py`
- `backend/tests/test_review_app.py`
- `compose.legacy-state.yaml`
- `compose.yaml`
- `deploy/gateway.Dockerfile`
- `docs/ROADMAP.md`
- `docs/TARGET_SPEC.md`
- `docs/api/api_reference.md`
- `docs/benchmark/annotation_guide.md`
- `docs/benchmark/benchmark_spec.md`
- `docs/benchmark/pilot_plan.md`
- `docs/deployment/aws-readiness.md`
- `docs/deployment/local.md`
- `docs/evaluation/evaluation_protocol.md`
- `docs/evaluation/risk_coverage.md`
- `docs/rebranding-audit.md`
- `docs/rebranding.md`
- `frontend/Dockerfile`
- `frontend/README.md`
- `frontend/app/evaluation/page.tsx`
- `frontend/app/experiments/page.tsx`
- `frontend/app/layout.tsx`
- `frontend/app/query-lab/page.tsx`
- `frontend/components/evaluation-dashboard.tsx`
- `frontend/components/experiment-runner.tsx`
- `frontend/components/query-lab.tsx`
- `frontend/components/risk-analysis.tsx`
- `frontend/components/system-status.tsx`
- `frontend/components/workbench-shell.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/query-api.ts`
- `frontend/next.config.ts`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/tests/api.test.ts`
- `frontend/tests/status-view.test.tsx`
- `pyproject.toml`

## Executed verification

- Before edits: 1,001 backend tests and 328 frontend tests passed.
- After edits: 1,009 backend tests and 329 frontend tests passed.
- Final focused rebrand/deployment checks: 13 passed. Ruff, TypeScript,
  ESLint and diff whitespace checks passed.
- All three Docker images built sequentially; frontend production build passed.
  Four Reckon containers are healthy; only gateway publishes 127.0.0.1:3000.
- HTTP 200 for all four workspaces with Reckon titles, health and OpenAPI.
  Existing exact-origin and Host rejection checks passed.
- Original external volume reused; SQLite SHA-256 remains
  `6fac4e082e544513df05872691417adf35ff4c5a3cf47788bba112fa2f6b4d37`.
  Saved 3-observation experiment, analysis, Dev freeze and exported report remain
  identical to pre-rebrand records; no experiment/freeze writes were issued.
- All 124 protected-file hashes match. No inference, commits, remote changes,
  database/volume deletion, AWS activity or paid services.
- New visual browser QA was not performed; HTTP markup, automated rendering and
  integration tests are verified. The existing R vector favicon is retained.
- The build reports the pre-existing eight moderate development-tooling npm
  advisories. No dependency versions were upgraded.
