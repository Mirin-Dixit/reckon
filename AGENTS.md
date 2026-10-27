
# Project Instructions

## General
- Read the relevant documentation before implementing a feature.
- Keep changes focused on the current milestone.
- Do not claim that a feature works without testing it.
- Do not invent benchmark results or test outcomes.
- Prefer clear, maintainable code over unnecessary abstraction.

## Backend
- Keep application code under `backend/app/`.
- Keep automated tests under `backend/tests/`.
- Separate API routes, ingestion, retrieval, generation, evaluation,
  database access, and shared configuration.
- Use type hints for public functions.
- Handle invalid input and expected failures explicitly.

## Testing and Quality
- Add or update tests for behaviour changes.
- Run pytest after implementing backend functionality.
- Run Ruff to check Python code.
- Fix errors rather than suppressing warnings without justification.

## Git
- Never commit secrets, `.env` files, virtual environments, or generated caches.
- Make focused commits with descriptive messages.
- Inspect `git diff` before committing.
- Do not rewrite or discard existing work without permission.

## Collaboration
- Explain significant design decisions.
- Ask before adding major dependencies or changing the agreed architecture.
- Keep the README accurate to the implementation.