# RAGBench Studio frontend

The Workbench provides read-only System Status. `/query-lab` submits individual
questions to `POST /api/v1/query` and displays retrieved evidence, exact citation
highlights, decisions, score provenance and execution metadata.

`/experiments` provides the completed P4 synthetic-only Experiment Runner:
Train/Dev fixture jobs, persistent history and saved results, observations,
configuration/provenance, JSON export and immutable completed-Dev configuration
receipts. Experiment execution uses deterministic fixtures with no model calls.
Empirical evaluation, benchmark human acceptance and held-out testing remain
separately gated; a synthetic Dev freeze does not satisfy those gates.

The Workbench has a near-black hero with a wide green particle mesh. The research
workflow and decision notation sit below it, followed by real System Status
controls. Health fields and the conceptual sketch use closed disclosures.
Experiments is an active workspace; Evaluation Results remains planned and
non-interactive. The System Status link jumps to the working panel. Empirical
benchmark gold labels and review records are not requested by these workspaces.

## Requirements

- Node.js >=20.9.0 (validated with Node 24.18.0) and npm.
- Existing Python backend environment; Python >=3.11.
- Existing Next.js/React/TypeScript dependencies pinned by `package-lock.json`.

No frontend dependencies were added. Tests use TypeScript, Node's built-in test
runner, and React's server renderer. They mock backend responses. One negative
configuration test invokes the Next build entry point and expects it to reject
an unsafe URL before compilation.

## Local startup (Windows PowerShell)

Run the backend in one terminal, from the repository root. Initial backend setup,
if needed, is `python -m pip install -e ".[server,dev]"` using the project virtual
environment. The OpenAI extra and credentials are unnecessary for System Status.

```powershell
$env:RAGBENCH_CORS_ORIGINS = "http://127.0.0.1:3000,http://127.0.0.1:3001"
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In a second terminal, starting at the repository root:

```powershell
Set-Location frontend
npm.cmd ci
$env:NEXT_PUBLIC_RAGBENCH_API_BASE_URL = "http://127.0.0.1:8000"
npm.cmd run dev
```

Open `http://127.0.0.1:3000`. `npm.cmd` avoids the Windows PowerShell execution
policy restriction on `npm.ps1`; other shells can use `npm`.
Both development and production-start scripts explicitly bind to `127.0.0.1`.
For the current port-3001 workspace, use `npm.cmd run dev -- --port 3001` and open
`http://127.0.0.1:3001`. The backend command above explicitly permits both local
ports. Set the CORS variable in the backend terminal **before** starting Uvicorn;
restart that process after changing it. Changing the frontend variable does not
update the running backend allowlist.
For `/experiments`, the browser sends an OPTIONS preflight before the JSON POST.
If OPTIONS returns 405, stop and restart the backend with the CORS variable above
in that same terminal. Expect preflight 200 with the exact frontend origin and
POST 202; an HTTP 200 history GET alone does not verify CORS for submissions.
Use the same frontend origin in the browser and backend CORS settings. If using
`http://localhost:3000`, explicitly add that exact origin to
`RAGBENCH_CORS_ORIGINS`; it differs from `127.0.0.1`.

The backend defaults to port 8000. The only public frontend variable is
`NEXT_PUBLIC_RAGBENCH_API_BASE_URL`, defaulting to `http://127.0.0.1:8000` when
unset. It must be an HTTP(S) loopback origin (`127.0.0.1`, `localhost`, or `[::1]`)
without credentials, path, query, or fragment. Do not include `/api/v1`; the client
appends the endpoint path. Invalid configuration fails safely at startup/build
and is also checked before requests. Restart dev or rebuild after changing it:
Next.js inlines public configuration into the browser bundle.

Never put keys, passwords, tokens, or provider configuration in a `NEXT_PUBLIC_`
variable, frontend `.env` file, URL, request, or browser storage. Provider keys
belong exclusively in the backend process. Only the local backend origin is
public configuration; it is not a secret. No frontend proxy or new backend route
has been introduced.

## Verification

From `frontend/`:

```powershell
npm.cmd test
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

The build uses locally hosted fonts and assets, so it needs no external font
fetch. Dependencies must already be installed for offline verification. Compiled
test files live in ignored `.test-build/`; TypeScript/lint checks exclude them.
Tests cover configured, unconfigured, degraded, unreachable and malformed
responses, error envelopes, cancellation, request/body-read timeouts, response
size limits, credential-bearing configuration, and safely rendered status states.
Static React rendering tests do not replace browser interaction/accessibility QA.

To smoke-check the production build locally, stop the dev server, then run:

```powershell
npm.cmd run start
```

## Architecture and behavior

- `lib/configuration.ts`: shared loopback-origin validation before public values
  are bundled and before browser requests.
- `lib/api.ts`: typed health/error contracts, runtime payload validation, safe
  public failures, and bounded shared JSON transport with injectable fetch.
- `lib/query-api.ts` / `query-contracts.ts` / `query-schema.json`: typed query
  requests, nested response validation and query-only backend contract snapshot.
- `lib/query-lab.ts`: form validation and single-flight request lifecycle.
- `components/query-lab.tsx`: accessible query controls and basic observed output.
- `lib/system-status.ts`: maps client results to explicit loading/ready/error states.
- `components/system-status.tsx`: mounts the health check, offers manual refresh,
  cancels obsolete requests and ignores stale results.
- `components/status-view.tsx`: pure, testable status table and accessible messages.
- `components/workbench-shell.tsx`: research context, planned workflow, interpretation,
  and local/request boundaries around the working status panel.
- `components/workbench-navigation.tsx`: desktop navigation and a mobile disclosure;
  planned workspaces have no link or keyboard action.

The Workbench uses a near-black background (#090D0C), charcoal-green surfaces
(#131B18), near-white text (#EAEDE7), and a bold Plex Sans hero. Three independently
phased, twisting particle ribbons cross the hero behind and beside the heading.
Green is reserved for accents and the wave. The planned workflow precedes the
real System Status operation; the health fields expand beneath its live result. Decision
notation and a closed conceptual-sketch disclosure remain secondary; none of the
visuals represent experiment output or evidence measurements.

Design tokens live in `app/tokens.css` and map to Tailwind v4's theme. Latin font
assets in `app/fonts/` load through `next/font/local` with swap, preload, and
adjusted fallbacks. Source Serif 4 remains available with optical sizing and real
italics; IBM Plex Sans provides variable weight for the primary interface. Plex
Mono is restricted to identifiers, values, step indices, and technical labels.
Font redistribution licenses accompany the assets. There are no runtime font
requests, new dependencies, or external animation services.

### Continuous particle wave

`components/particle-wave.tsx` binds browser lifecycle APIs to the reusable
Canvas 2D renderer in `lib/particle-wave.ts`. Three travelling harmonic surfaces with rotating cross-sections drive
fine dots, ribbon strands, and sparse cross-connections continuously through elapsed time, without a
finite timeline or a visible loop reset. This is not a PNG, video, or GIF.

The renderer maintains at most one requestAnimationFrame callback. It pauses
when the document is hidden or the component leaves the viewport, resets the
frame clock on resume, and removes all listeners/observers and releases the
canvas backing buffer on unmount. Reduced-motion preference draws a static wave
and schedules no animation frames; preference changes are respected live.

DPR is capped at 1.5 (1 on low-core devices). Initial density scales down for
mobile/narrow screens and low-core devices; sustained slow rendering reduces
mesh density further. Backing-buffer dimensions are bounded. Rendering targets
the browser frame cadence on capable hardware; 60 FPS is a target, not a measured
guarantee. Actual visual quality, GPU use, and device performance need browser QA.

Unit tests exercise continuously changing geometry, ongoing frame scheduling,
visibility/offscreen suspension, reduced motion, resize/DPR bounds, adaptive
quality, no-Canvas fallback, and idempotent teardown using an injected host.
Responsive CSS keeps technical text at its own size rather than scaling SVG text.
Browser checks at 1440x900 and 390 px remain unverified when browser access fails.

The check runs on page mount and manual refresh, with no polling or automatic
retries. GET requests omit credentials, refuse redirects, disable caching, send
no body, and have a five-second deadline including body reads. Responses are
limited to 16 KiB. Health payloads must match the inspected contract: known
application identity, plain numeric semantic version, correct boolean fields,
`ok`/`degraded`, and `provider_connection_tested: false`. Unknown fields and
inconsistent readiness states are rejected. A future backend contract change
may require updating the parser and tests together.

Backend error messages, raw exception text and response bodies are never shown
or logged. The UI uses fixed failure messages. Backend-sourced text uses React
text rendering, with no HTML or external-link interpretation.

`ok` means runtime availability, not answer quality. Generation configuration
is reported separately; it does not verify credentials or connectivity. A
`degraded` response still means the backend answered HTTP but its runtime failed
to initialize. Network/CORS errors cannot be distinguished by the browser and
share actionable guidance. Execution/configuration failures are not abstentions.

The API has no authentication. CORS does not provide access control. Keep this
prototype local; public deployment requires a separate security design.

## Query Lab (P3 Batch 1)

Open `http://127.0.0.1:3000/query-lab` (or port 3001 when configured above).
No query is sent on page load. Enter a corpus question and submit explicitly.
BM25, dense and hybrid retrieval work with always-answer, threshold and
prompt-abstention. Defaults: BM25, top-k 3, prompt-abstention. Hybrid defaults
RRF k to 60; blank candidate k uses the backend automatic value. Threshold
uses the matching score family, `at_least`, and ABSTAIN on missing scores.
The default threshold 0 is an operating point, not a calibrated recommendation.
It resets when retrieval changes. Thresholds outside a score range are allowed
for deliberate always/never-answer experiments, as in the backend contract.

Use the accepted local backend configuration from the root README/API reference:
`RAGBENCH_PROVIDER=ollama`, `RAGBENCH_MODEL=qwen3:4b-q4_K_M`, local Ollama with
cloud disabled. Dense/hybrid additionally require installed `all-minilm:22m`.
Keep the existing 1.5 GiB RAM reserve and concurrency-one limits. No model is
downloaded or configured by the frontend. Do not enable paid providers.
Provider settings, keys and generation overrides are never sent by this form.
The unauthenticated backend must remain loopback-only; CORS is not authentication.

The query client validates a query-only snapshot of the actual backend schemas,
including nested response types, decision/reason pairing and score provenance.
It caps JSON reads at 1 MiB and waits at most 270 seconds, covering the two bounded
120-second provider phases plus overhead. Health retains its 16 KiB / 5-second
limits. Both requests omit credentials, reject redirects and release their streams.
No automatic retries, local storage, external evidence links or HTML rendering
are used. Backend error messages are discarded in favor of fixed safe messages.
Cancelling or timing out stops browser waiting; it cannot guarantee cancellation
of synchronous backend inference or reclaim its shared provider-attempt budget.
Execution failures never appear as intentional ABSTAIN results.

Validation (no inference):

```powershell
# Repository root: exact schema drift + nine request combinations
.\.venv\Scripts\python.exe frontend/tests/check_query_contract.py
# frontend directory
npm.cmd test
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

Node tests use mocked transport, session lifecycle tests and server-rendered views.
They do not replace manual desktop/mobile, keyboard and browser acceptance checks.
Evidence/citation visualization validates returned source coordinates; exact quote
matches and citation counts do not prove semantic grounding. Scores remain uncalibrated and are not answerability probabilities.


## Query Lab evidence and decisions (P3 Batch 2)

The observed response contains the actual decision/reason code and explanation,
separate relevance/sufficiency assessments, missing premises, unsupported
assumptions and contradictions. ANSWER, intentional ABSTAIN and CLARIFY use
text labels and distinct rule treatments; execution errors remain separate.

The evidence ledger displays every returned chunk with document/chunk IDs,
metadata, rank and source coordinates. URLs remain inert text. Source passages
are untrusted data, including any flagged injection content. Claim citations link
to focusable passages. Highlighting uses only validated original-document
half-open offsets `[start, end)` in Unicode code points, matching Python indexing.
It does not search for quotes, normalize text or convert offsets to UTF-16 units.
Duplicate chunk IDs, mismatched text lengths, out-of-range spans and nonmatching
quotes reject the response as malformed. Overlapping spans share highlights
without duplicating source text. Validation checks the returned chunk, not the
full document on disk, and does not establish semantic support.

Score tables preserve the supplied family, source, role, effective parameters,
range, direction, availability and uncalibrated status. Threshold inputs show the
actual score and comparison; null stays unavailable and zero stays zero. Missing
RRF bound provenance is labeled unavailable, not unbounded. Prompt self-assessment
never overrides a decision. Empty retrieval does not imply corpus-wide absence.

Execution details display only supplied model/provider, prompt version, latency
and token fields. There is no fabricated per-stage timing or missing-token estimate.
Use keyboard-accessible disclosures and horizontally scrollable score tables on
narrow screens. The evidence interface adds no animation and inherits reduced-motion
and focus styles. Automated tests remain deterministic and offline; real-model and
manual browser acceptance require separate review.

Focused evidence tests, after `npm.cmd test` compiles them:

```powershell
node --test .test-build/tests/evidence-ledger.test.js
```


## P3 final manual acceptance

P3 Batch 3 adds an offline integration bridge that sends frontend-built requests
through the actual FastAPI ASGI route and real retrieval/pipeline code, using
existing fake embedding/generation transports and synthetic documents only.
All nine combinations are checked along with independent decision/error cases,
response parsing, citation rendering, and rejection of benchmark-only fields.
`npm.cmd test` now needs the existing root `.venv` backend test environment as
well as frontend dependencies; it makes no real model or embedding calls.

Focus moves to Cancel while a request is active, to the observed-response heading
on completion/failure/cancellation, and to the validation message on invalid
submission. Decision headings keep their heading semantics inside a live region.
An unsuccessful execution inside an HTTP 200 payload is rejected as malformed;
it does not fabricate a 502 status. Genuine backend 502/504 errors remain failures,
not intentional abstentions. No unrelated cleanup or backend changes were needed.

Browser QA was attempted but unavailable: browser access host and native pipe
could not connect. The following remain **unverified** and require manual review:

1. At 1440x900 and 390px, verify navigation, form, evidence ledger and scrollable
   score tables remain readable without page-wide horizontal overflow.
2. Use Tab/Shift+Tab and Enter/Space: navigate to Query Lab, trigger empty-input
   validation, use every select, operate disclosures and follow citation anchors.
   Verify visible focus reaches validation, Cancel, response heading and passages.
3. With an explicitly approved local request or a separate test-only mocked backend,
   inspect ANSWER, ABSTAIN, CLARIFY, execution failure, empty evidence and null scores.
   Do not initiate real inference merely to complete this checklist without approval.
4. Check loading, cancellation, stale completion, timeout and network failure.
   Cancellation must say that backend inference may continue. No automatic retry.
5. Check screen-reader announcements, table headers/captions and heading order;
   enable reduced motion and verify focus and all controls remain usable.
6. Check real browser CORS/configuration against the local backend without making
   an unapproved model call. Inspect for hydration warnings or browser errors.

Gold data is not fetched by the frontend or loaded by ordinary query runtime
initialization. Benchmark-only request fields are rejected before execution.
Free-text input cannot prevent a user manually pasting a known benchmark question
or reference answer; this interface must not be described as a content sandbox.
These checks do not establish model quality, semantic grounding or public-deployment
security. The API remains an unauthenticated, loopback-only local prototype.


Final offline validation for P3: 197 frontend tests and 649 backend tests passed,
with TypeScript, ESLint, production build, Ruff and schema/dataset checks passing.
The browser checks above were not performed. Dataset working-file SHA-256 hashes
match the accepted P2 baseline. The questions file uses CRLF locally and LF in
Git; its clean-filtered Git blob identity is unchanged.

## P4 synthetic experiment results

At `/experiments`, each history entry has a **View saved results** button.
Results appear inline in **Selected experiment**, below the form/history area;
selecting a row moves keyboard focus and scrolls to that panel without animation.
Selecting the same row again reloads its results. Loading, empty and failed reads
have explicit messages, and **Retry loading results** does not submit another job.

The panel shows saved status/counts, observations, decisions, recorded errors,
configuration, dataset/runtime fingerprints and supplied provider/software
provenance. **Export synthetic result JSON** downloads the selected saved record.
**Freeze this Dev configuration** is enabled only for a completed synthetic Dev
job while no mutation is pending. A successful matching receipt exposes **Export
freeze JSON**. Train, running, partial and failed jobs cannot be frozen here.
This fixture freeze neither accepts a benchmark nor authorizes held-out evaluation.

Manual retest:

1. Select an existing `dev / done / 12/12` row. Verify the panel is reached and
   contains 12 observations, provenance and both result controls.
2. Select that same row twice, then a different row. Verify results reload and the
   displayed/exported experiment ID matches the selected entry each time.
3. Use Tab and Enter to select history and operate disclosures and controls.
4. Export JSON; compare its ID/counts with the panel. Freeze an eligible synthetic
   Dev configuration and verify its receipt/export. Confirm ineligible controls
   remain disabled. This action is synthetic-only and makes no model calls.
5. Test empty history and a failed results GET. Verify explicit feedback and a
   working read-only retry, without silently showing another experiment's data.
