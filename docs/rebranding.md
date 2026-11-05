# Reckon identity and compatibility

Reckon | Evidence-Aware RAG Evaluation & Selective Prediction Platform

An evidence-aware RAG evaluation workbench that studies when retrieval-augmented
generation systems should answer, abstain, or request clarification.

## Stable compatibility boundaries

Visible identity, packages, new Docker images/projects and setup commands use
Reckon. The generic Python `app` package remains unchanged. `RECKON_*` settings
win over fallback `RAGBENCH_*` aliases, including when explicitly empty.
Next configuration accepts both `NEXT_PUBLIC_RECKON_API_BASE_URL` and its old
`NEXT_PUBLIC_RAGBENCH_API_BASE_URL` fallback, and both standalone flags.
The health reader accepts `RAGBench Studio` from older servers but displays Reckon.
No provider credentials are exposed to the browser.

Versioned `ragbench.*` schema/report/cache identifiers remain contracts, not
active branding. Readers and writers retain their versions; no historical rewrite
or schema migration is needed. Datasets, source URLs, exact offsets, manifests,
review submissions, integrity files and the `ragbench-pilot30-v1` selection seed
remain unchanged. `.ragbench-cache` remains the native state directory to preserve
saved experiments, vectors and reviewer drafts. Old generated metadata, logs,
virtual environments, build output and Git commits are not rewritten.

## Existing Docker state: explicit compatibility mapping

The accepted store is in external volume `ragbench-p6-check_state`. Never copy,
recreate or remove it. Stop its old owner before starting Reckon. From the root:

```powershell
docker compose -p ragbench-p6-check stop -t 45
docker compose -p reckon -f compose.yaml -f compose.legacy-state.yaml config --quiet
docker compose -p reckon -f compose.yaml -f compose.legacy-state.yaml build backend
docker compose -p reckon -f compose.yaml -f compose.legacy-state.yaml build frontend
docker compose -p reckon -f compose.yaml -f compose.legacy-state.yaml build gateway
docker compose -p reckon -f compose.yaml -f compose.legacy-state.yaml up -d --wait --no-build
```

Keep BOTH `-f` arguments and project `reckon` for all subsequent commands on this
migrated installation. The external declaration fails safely if the volume is
missing, rather than silently creating empty state. The old stopped containers
and original volume remain. Never start two owners. Fresh installations can omit
the override and use new `reckon_state` storage. Gateway-only localhost exposure,
private application networking and exact-origin checks are unchanged. No model
inference is required to verify saved results and report compatibility.

## Repository and workspace names

The real URL remains https://github.com/Mirin-Dixit/RAGbench . Do not substitute a
fictional URL. A later rename requires owner action under GitHub Settings > General
> Repository name. After it succeeds, deliberately update origin and docs; this
rebrand does neither automatically.

Do not rename the open Windows repository root. Later: stop its Docker containers
without removing volumes, close editors/terminals using the folder, rename it in
Explorer, reopen the workspace, check origin/HEAD and recreate the SAME Compose
project using the external-volume override from the new root. Preserve Git history
and uncommitted work; do not clone over or replace the existing directory.
