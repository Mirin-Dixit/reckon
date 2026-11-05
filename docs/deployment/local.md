# P6 local engineering and deployment

The required deployment is local and synthetic-only, with zero paid inference.
No authentication or public hosting is claimed. Do not expose this stack through
a public proxy, tunnel, wildcard bind or router port-forward. Query, legacy
evaluation and experiment/analysis APIs enforce loopback peers and exact browser
origins. Health is public but does not prove a provider connection or model quality.

## Native startup and recovery (existing supported inference path)

From the repository root, using the existing environments:

```powershell
$env:RAGBENCH_CORS_ORIGINS = 'http://127.0.0.1:3000,http://127.0.0.1:3001'
$env:RAGBENCH_REQUEST_BODY_TIMEOUT_SECONDS = '15'
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers --no-access-log --timeout-graceful-shutdown 30
```

In the frontend terminal:

```powershell
Set-Location frontend
$env:NEXT_PUBLIC_RAGBENCH_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd run build
npm.cmd run start
```

Existing Ollama setup remains optional and local-only. Follow the accepted API
reference for the exact installed models, cloud-disabled Ollama server, zero
retries, provider-attempt budget, 8192 context and 1024 output cap. No P6 check
authorizes inference or downloads. Preserve at least 1.5 GiB available RAM after
any model load; stop inference if that reserve cannot be maintained.

Use Ctrl+C for graceful shutdown. Keep one Uvicorn worker: the durable queue owns
a process lock, and its one-active/four-waiting limits are not a distributed queue.
On restart, P4 worker initialization records interrupted queued/running work as
failures according to its existing recovery semantics. It never fabricates
completed results. Dashboard/analysis GETs do not initialize or recover workers.
Only start recovery against a backed-up store that you intend to operate.

`RAGBENCH_EXPERIMENT_STORE_PATH` optionally selects an absolute, trusted server-side
SQLite path. It is never accepted from HTTP. Leaving it unset preserves the native
store location. A missing store yields empty dashboard history without creating a
database; only the experiment worker provisions storage. Do not point verification
at protected records for mutating requests. Missing results are 404; corrupt,
oversized, unsupported-WAL or inaccessible snapshots fail safely, without repair.
Never delete a lock/database to force startup, run two owners, copy a live SQLite
file without a consistent backup, or change journal mode to bypass a read-only gate.

Request bodies are capped at 1 MiB and a cumulative 15-second receive deadline,
including chunked requests. Deadline expiry returns a safe 408 envelope before
runtime initialization. The trusted timeout setting accepts only (0,60] seconds.
Existing provider/embedding timeouts, cache limits and analysis concurrency remain
unchanged. Cancellation stops waiting; it does not promise backend inference or
CPU work was terminated.

## Docker: local synthetic workbench

Requires an existing Docker Engine with Compose v2 and enough disk/RAM for builds.
On Windows, use Linux containers (an open-source Engine/Compose installation in
WSL2 is an option; no Docker Desktop subscription is required by this project).
No Docker installation is performed by this
milestone. Check headroom before building; the runtime limits total 1792 MiB plus
Docker/OS overhead. Keep the 1.5 GiB host reserve. Build-time usage is separate.

`compose.yaml` uses JSON syntax, a valid YAML subset, so offline contract tests can
parse it with the Python standard library. Four non-root, read-only services are used.
Backend, frontend and the private `app-proxy` share the backend network namespace
on an internal application network. The private relay reaches Next and FastAPI
through loopback, preserving peer checks. The separate Nginx `gateway` joins the
private network and a dedicated ingress network; only it publishes
`127.0.0.1:3000:8080`. No backend/frontend ports are published. Only the gateway
has an external route; it uses fixed private upstreams, strips forwarded identity,
cookies and authorization, and rejects unknown hosts. Application processes retain
no external route. Origins are preserved for exact-origin validation.

The original internal-only shared namespace declared a host port on backend, but
Engine 29.9.2 on Windows created no active host publication (`:0`). The split
Nginx ingress/private-relay configuration corrects that without changing API guards.
See the official [Compose service reference](https://docs.docker.com/reference/compose-file/services/)
and [Nginx proxy reference](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).

The default stack does **not** include an Ollama server or models. Synthetic
experiments, history, analysis and report exports work without inference. A live
Query Lab generation/embedding request will fail explicitly if the container-local
Ollama is unavailable. Host Ollama is not container loopback; no remote hostname
alias or cloud fallback is introduced. Use native startup for the accepted live
local-model path. Adding an inference sidecar requires a separate resource/model
review; do not change Ollama URL validation to reach a bridge address.

The named `state` volume is new Docker-owned storage, separate from the protected
native database. Only corpus documents and synthetic fixtures are read-only bind
mounts. Real benchmark questions, review files, models, databases and environment
files are excluded from image builds. Do not mount the native database writable.
Base images are pinned to official registry digests, server dependency versions
are locked, and frontend installation uses `npm ci` and its existing lockfile.
Only the Docker builder sets `RAGBENCH_STANDALONE=1`; native builds retain the
existing `next start` workflow. The Docker runner copies standalone output,
static assets and public files explicitly.
Digest pinning is reproducibility, not evidence of a vulnerability scan: deliberately
refresh and revalidate these pins before a future release. No image layers were
downloaded during this milestone's metadata checks.

From the repository root:

```powershell
docker --version
docker compose version
docker compose config --quiet
docker compose build
docker compose up -d --wait
docker compose ps
curl.exe --fail http://127.0.0.1:3000/api/v1/health
curl.exe --fail http://127.0.0.1:3000/evaluation
curl.exe --fail 'http://127.0.0.1:3000/api/v1/analysis/experiments?limit=20&offset=0'
```

Open exactly `http://127.0.0.1:3000`, not a LAN hostname. Select Synthetic Dev in
Experiments, run its deterministic fixture, view saved observations and run R1
analysis. Export the research report. These actions make no model calls and are
not empirical benchmark evidence. Stop/restart and verify that this Docker-owned
job and any eligible Dev freeze remain available. Do not repeat real-model calls.

```powershell
docker compose logs --tail 100 backend frontend app-proxy gateway
docker compose stop -t 45
docker compose up -d --wait
docker compose down
```

`down` retains named state; do not remove volumes. Namespace-sharing means backend
container replacement should recreate the complete stack, not just one dependent
container. Health checks gate startup and report liveness; they do not perform
inference. Backend 503 and proxy upstream errors are safe; frontend response-size,
timeout, cancellation and schema checks still apply.

For a consistent backup of **Docker-owned** state, while it exists:

```powershell
docker compose exec backend python -c "import sqlite3; s=sqlite3.connect('file:/state/experiments.sqlite3?mode=ro',uri=True); d=sqlite3.connect('/tmp/experiments-backup.sqlite3'); s.backup(d); d.close(); s.close()"
docker compose cp backend:/tmp/experiments-backup.sqlite3 ./experiments-backup.sqlite3
```

Keep backups outside Git. Restore only into a stopped, separately backed-up state
volume with correct UID 10001 ownership and explicit operator approval. No restore
or recovery command is run automatically by these instructions.

## Verification and limits

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp "$env:TEMP\rb-p6"
.\.venv\Scripts\python.exe -m ruff check backend frontend/tests/workspace_http_bridge.py
Set-Location frontend
npm.cmd test
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

Tests use mocked model transports and disposable state. Upload deadlines, remote
and foreign-origin rejection, safe errors, read-only history, restart recovery,
gold isolation and export correctness are covered. Dockerfile/Compose assertions
are static checks. If Docker is missing, Compose-engine parsing, Linux image builds,
Nginx syntax/runtime, networking, volume permissions and container restart/persistence
remain **NOT VERIFIED**. No cloud deployment or public security certification is
implied by local tests. Existing benchmark human acceptance and Test gates remain.

## Remaining Windows Docker verification, isolated from native records

Historical status: Docker was initially unavailable. Subsequent Windows verification
built the images and exercised localhost HTTP, synthetic results/analysis/export
and restart persistence. The user subsequently completed Windows Chrome acceptance; agent browser
automation remained unavailable. The original commands below remain the verification procedure.

Prerequisites: an existing Docker Desktop installation eligible under its license,
WSL2/Linux containers, hardware virtualization, sufficient free disk for image and
build caches (plan at least 20 GiB free), and RAM for Docker plus the host's 1.5 GiB
reserve. Consult the [Windows prerequisites](https://docs.docker.com/desktop/setup/install/windows-install/).
Do not install or change Windows features automatically. Stop only identified native
RAGBench servers using port 3000, or run the check later. No model server is needed.

Run from the repository root in PowerShell. `-p ragbench-p6-check` creates a separate
project/volume; it does not reuse the protected native SQLite database.

```powershell
docker --version
docker compose version
docker info --format '{{.OSType}}'
docker compose -p ragbench-p6-check config --quiet
docker compose -p ragbench-p6-check build
docker compose -p ragbench-p6-check up -d --wait
docker compose -p ragbench-p6-check ps
docker compose -p ragbench-p6-check port gateway 8080
$base = 'http://127.0.0.1:3000'
Invoke-RestMethod "$base/api/v1/health"
curl.exe --fail "$base/evaluation"
```

Expect Linux, healthy containers, the single `127.0.0.1:3000` publication and HTTP
200. Health does not verify Ollama; `provider_connection_tested` must remain false.
If a build fails, retain logs and stop: static checks did not establish that Linux
dependencies, Nginx or volume permissions work. Never repair failure by removing
the API guards, mounting native state, using root containers or publishing port 8000.

Create exactly one **synthetic** Dev job in the isolated Docker-owned store:

```powershell
$body = @{
  split = 'dev'; question_ids = @('synthetic_dev_01')
  retrieval = @{method='bm25'; top_k=3}
  policies = @(@{name='always_answer'}, @{name='prompt_abstention'},
               @{name='threshold'; threshold=0; score_type='bm25'})
} | ConvertTo-Json -Depth 6
$job = Invoke-RestMethod -Method Post "$base/api/v1/experiments" -ContentType 'application/json' -Body $body
for ($attempt=0; $attempt -lt 60; $attempt++) {
  $saved = Invoke-RestMethod "$base/api/v1/analysis/experiments/$($job.id)"
  if ($saved.status -in @('done','partial','failed')) { break }
  Start-Sleep -Seconds 1
}
if ($saved.status -ne 'done' -or $saved.observed_run_count -ne 3) { throw 'Record actual failure; do not retry or infer success' }
$analysis = Invoke-RestMethod "$base/api/v1/experiments/$($job.id)/analysis?lexical_proxy=true"
if ($analysis.empirical_evaluation -ne $false) { throw 'Unexpected evaluation profile' }
$freeze = Invoke-RestMethod -Method Post "$base/api/v1/experiments/$($job.id)/freeze" -ContentType 'application/json' -Body '{}'
docker compose -p ragbench-p6-check stop -t 45
docker compose -p ragbench-p6-check up -d --wait
$restored = Invoke-RestMethod "$base/api/v1/analysis/experiments/$($job.id)"
if ($restored.observed_run_count -ne 3) { throw 'Persistence failed' }
$sameFreeze = Invoke-RestMethod -Method Post "$base/api/v1/experiments/$($job.id)/freeze" -ContentType 'application/json' -Body '{}'
if ($sameFreeze.sha256 -ne $freeze.sha256) { throw 'Idempotent persisted receipt changed' }
docker compose -p ragbench-p6-check logs --tail 100 backend frontend app-proxy gateway
```

The receipt has POST-only access; the second POST checks its supported idempotent
behavior, not a nonexistent GET endpoint. No inference is involved. In Evaluation
Results, select this isolated job and export its research report; verify its ID,
source hashes, three policy rows and synthetic judgment basis. This is the remaining
container integration check, not a request to repeat accepted native browser QA.
Malformed JSON must return a safe 422, a foreign-origin query 403, a missing UUID
404, and backend/provider failures must never look like ABSTAIN. Never test paid
providers or use held-out questions to exercise errors.

| Command group | Meaning, changes, risks, verification and recovery |
|---|---|
| Version/info/config | Reads local tooling and parses configuration; changes no application data. Confirm Linux and successful exit. Start Desktop or fix the reported configuration if unavailable. |
| Build | Downloads pinned base images/dependencies and creates local images/caches; uses RAM/disk and Internet bandwidth, not paid inference. Success means all three builds finish. Inspect build logs on failure; do not delete protected files. |
| Up/ps/port | Starts local containers and provisions only the isolated named volume. Confirm health and loopback-only binding. `stop -t 45` stops services without erasing data. |
| Health/results/analysis GETs | Reads service state and performs bounded read-only R1 analysis. No inference or record recovery. Inspect actual status/body, not just connectivity. Stop on invalid data. |
| Synthetic POST/freeze | Writes only isolated synthetic records and a hash-bound receipt. Confirm saved counts and receipt SHA. A failed job remains a failure; no silent retry. |
| Stop/up | Tests retained state across shutdown. Confirm the same job and receipt. On failure, preserve the volume/logs for diagnosis. |
| Logs/export | Reads local logs or downloads a local JSON file; review for secrets/gold leakage. Access logs are disabled to avoid recording arbitrary URL query strings. Do not publish logs or reports automatically. |

Finish with `docker compose -p ragbench-p6-check down`. This stops/removes the
isolated containers/network, retaining its named volume for inspection. Do not
remove volumes or run broad pruning commands. These local commands allocate no
AWS resources; Internet access and Docker Desktop licensing are separate concerns.

## Ingress logging and runtime verification

Nginx access and error logs are suppressed because built-in error messages may
include unredacted request URIs. Diagnose through container health, process state
and safe HTTP error envelopes; do not enable raw request logging for sensitive
queries. Uvicorn access logging remains disabled. This trades proxy diagnostics
for request privacy in this unauthenticated local-only prototype.

Windows verification on 2026-11-05 confirmed sole gateway publication on
127.0.0.1:3000, four healthy services, HTTP 200 for all workspaces/health,
a three-observation synthetic Dev job, deterministic report JSON, and identical
saved results, analysis and Dev-freeze hash after restart. These are synthetic
engineering checks, not model-quality or empirical benchmark results. The
computer-use native pipe/browser host were unavailable to the agent. The user
subsequently accepted Windows Chrome verification of the Docker-hosted dashboard,
three saved observations and policy metrics for experiment
`99e8c74f-f8a8-40f2-aa14-c5392d4f8a36`, appropriate undefined risk/AURC for
unknown judgments, and a downloaded/validated research report with that experiment
ID. This is user-performed browser acceptance, not an agent browser-test claim.

The accepted local deployment has four healthy containers: backend, frontend,
private app-proxy and ingress gateway. The three built images cover these four
services because both Nginx services reuse the same image. Production-only npm
audit returned zero findings; the full audit identified eight moderate findings
in development tooling. No unreviewed dependency upgrades were applied. Public
hosting, image/OS-wide vulnerability certification, empirical evaluation and
container-local LLM inference remain outside this acceptance.
