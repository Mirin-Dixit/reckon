"""Bounded SELECT-only snapshots. Does not construct ExperimentStore or recover jobs."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from uuid import UUID

MAX_PAYLOAD_BYTES = 2 * 1024 * 1024


def read_analysis_jobs(path: Path, job_ids: tuple[str, ...]) -> tuple[dict, ...]:
    """Read up to eight saved jobs in one read transaction; never create a database."""
    if not 1 <= len(job_ids) <= 8 or len(set(job_ids)) != len(job_ids):
        raise ValueError("Select 1..8 distinct experiments")
    for job_id in job_ids:
        if str(UUID(job_id)) != job_id:
            raise ValueError("Invalid experiment identity")
    if not path.is_file():
        raise FileNotFoundError("Experiment database unavailable")
    # P4 uses rollback journals. Refuse WAL instead of ignoring uncheckpointed
    # data with immutable=1 or allowing SQLite to create shared-memory sidecars.
    with path.open("rb") as source:
        header = source.read(100)
    if len(header) < 100 or header[18:20] != b"\x01\x01":
        raise ValueError("Analysis requires the P4 rollback-journal database format")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1)
    try:
        db.execute("PRAGMA query_only=ON")
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_PAYLOAD_BYTES * 2)
        deadline = time.monotonic() + 2
        db.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        db.execute("BEGIN")
        results = []
        for job_id in job_ids:
            row = db.execute(
                "SELECT CASE WHEN length(CAST(payload AS BLOB)) <= ? "
                "THEN payload ELSE NULL END FROM jobs WHERE id=?",
                (MAX_PAYLOAD_BYTES, job_id),
            ).fetchone()
            if row is None:
                raise KeyError(job_id)
            if row[0] is None:
                raise ValueError("Stored result exceeds analysis limit")
            job = json.loads(row[0])
            if not isinstance(job, dict) or job.get("id") != job_id:
                raise ValueError("Invalid saved experiment")
            results.append(job)
        return tuple(results)
    finally:
        db.close()  # rolls back the read transaction; no recovery/checkpoint writes
