# RAGBench Studio frontend - Stage 4A

This local workbench foundation provides System Status only. It calls the existing
`GET /api/v1/health` endpoint; it does not send questions, run evaluations, access
benchmark labels, or make provider calls. Query Lab, Experiment Runner, analytics,
and deployment remain outside this batch.

The Workbench has a near-black hero with a wide green particle mesh. The planned
workflow and decision notation sit below it, followed by real System Status
controls. Health fields and the conceptual sketch use closed disclosures. Planned workspaces are non-interactive
text, not placeholder routes. The System Status link jumps to the working panel.

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
  public failures, and a health-only client with injectable fetch for tests.
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
