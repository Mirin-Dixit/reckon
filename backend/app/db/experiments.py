"""Transactional durable queue. A process lock protects restart recovery."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.api.experiment_models import SYNTHETIC_NOTICE


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class QueueFull(Exception):
    """The bounded durable queue is full."""


class StoreConflict(Exception):
    """An operation is invalid for the persisted job state."""


class ExperimentStore:
    """One owning service, short transactions, no shared SQLite connections."""

    def __init__(self, path: Path, capacity: int = 5) -> None:
        self.path = path
        self.capacity = capacity
        path.parent.mkdir(parents=True, exist_ok=True)
        self._owner = path.with_suffix(".lock").open("a+b")
        try:
            self._owner.seek(0)
            if os.name == "nt":
                import msvcrt

                if self._owner.read(1) == b"":
                    self._owner.write(b"0")
                    self._owner.flush()
                self._owner.seek(0)
                msvcrt.locking(self._owner.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._owner.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.connection() as db:
                db.executescript("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY, payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS freezes (
                        job_id TEXT PRIMARY KEY REFERENCES jobs(id),
                        payload TEXT NOT NULL
                    );
                """)
                for row in db.execute("SELECT id,payload FROM jobs").fetchall():
                    job = json.loads(row[1])
                    if job["status"] in ("queued", "running"):
                        job.update(
                            status="partial" if job["observations"] else "failed",
                            error="process_interrupted",
                            updated_at=utc_now(),
                        )
                        self._put(db, job)
        except BaseException:
            self._owner.close()
            raise

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=3)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def close(self) -> None:
        self._owner.close()

    @staticmethod
    def _put(db: sqlite3.Connection, job: dict[str, Any]) -> None:
        db.execute(
            "UPDATE jobs SET payload=? WHERE id=?",
            (json.dumps(job, allow_nan=False), job["id"]),
        )

    def submit(
        self, config: dict, fingerprint: dict, expected: int, source_sha256: str
    ) -> dict:
        with self.connection() as db:
            jobs = [
                json.loads(row[0]) for row in db.execute("SELECT payload FROM jobs")
            ]
            if sum(j["status"] in ("queued", "running") for j in jobs) >= (
                self.capacity
            ):
                raise QueueFull
            now = utc_now()
            job = dict(
                schema_version="ragbench.experiment-job.v1",
                id=str(uuid.uuid4()),
                status="queued",
                created_at=now,
                updated_at=now,
                notice=SYNTHETIC_NOTICE,
                empirical_evaluation=False,
                configuration=config,
                runtime_source_sha256=source_sha256,
                dataset_fingerprint=fingerprint,
                expected_run_count=expected,
                observed_run_count=0,
                observations=[],
                result=None,
                error=None,
            )
            db.execute(
                "INSERT INTO jobs VALUES (?,?)",
                (job["id"], json.dumps(job, allow_nan=False)),
            )
            return job

    def get(self, job_id: str) -> dict | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT payload FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
            return json.loads(row[0]) if row else None

    def list(self, limit: int = 50, offset: int = 0) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT payload FROM jobs ORDER BY rowid DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [json.loads(row[0]) for row in rows]

    def claim(self) -> dict | None:
        with self.connection() as db:
            for row in db.execute("SELECT payload FROM jobs ORDER BY rowid"):
                job = json.loads(row[0])
                if job["status"] == "queued":
                    job.update(status="running", updated_at=utc_now())
                    self._put(db, job)
                    return job
        return None

    def observe(self, job_id: str, observation: dict) -> None:
        with self.connection() as db:
            job = json.loads(
                db.execute("SELECT payload FROM jobs WHERE id=?", (job_id,)).fetchone()[
                    0
                ]
            )
            if job["status"] != "running":
                raise StoreConflict("Job is not running")
            key = (observation["question_id"], observation["policy_name"])
            if any(
                (r["question_id"], r["policy_name"]) == key for r in job["observations"]
            ):
                raise StoreConflict("Duplicate observation")
            job["observations"].append(observation)
            job["observed_run_count"] = len(job["observations"])
            if job["observed_run_count"] > job["expected_run_count"]:
                raise StoreConflict("Too many observations")
            job["updated_at"] = utc_now()
            self._put(db, job)

    def finish(self, job_id: str, result: dict | None, error: str | None) -> None:
        with self.connection() as db:
            job = json.loads(
                db.execute("SELECT payload FROM jobs WHERE id=?", (job_id,)).fetchone()[
                    0
                ]
            )
            if job["status"] != "running":
                raise StoreConflict("Job is not running")
            if result is not None:
                if (
                    result["experiment_id"] != job_id
                    or result["runs"] != job["observations"]
                    or result["dataset_fingerprint"] != job["dataset_fingerprint"]
                    or result["selected_question_ids"]
                    != job["configuration"]["question_ids"]
                    or result["benchmark_split"] != job["configuration"]["split"]
                    or result["random_seed"] != job["configuration"]["random_seed"]
                    or result["retrieval_configuration"]
                    != job["configuration"]["retrieval"]
                    or result["generation_configuration"]["source_sha256"]
                    != job["runtime_source_sha256"]
                ):
                    raise StoreConflict("Result does not match persisted observations")
            complete = (
                result is not None
                and not result["stopped_early"]
                and len(job["observations"]) == job["expected_run_count"]
            )
            failures = sum(r["error"] is not None for r in job["observations"])
            status = (
                "done"
                if complete and not failures and not error
                else ("partial" if job["observations"] else "failed")
            )
            job.update(status=status, result=result, error=error, updated_at=utc_now())
            self._put(db, job)

    def freeze(self, job_id: str) -> dict:
        with self.connection() as db:
            row = db.execute(
                "SELECT payload FROM freezes WHERE job_id=?", (job_id,)
            ).fetchone()
            if row:
                return json.loads(row[0])
            row = db.execute(
                "SELECT payload FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
            if row is None:
                raise KeyError(job_id)
            job = json.loads(row[0])
            if job["status"] != "done" or job["configuration"]["split"] != "dev":
                raise StoreConflict("Freeze requires a completed Dev job")
            manifest = dict(
                schema_version="ragbench.dev-freeze.v1",
                job_id=job_id,
                empirical_evaluation=False,
                notice=SYNTHETIC_NOTICE,
                configuration=job["configuration"],
                dataset_fingerprint=job["dataset_fingerprint"],
                software_metadata=job["result"]["software_metadata"],
                generation_configuration=job["result"]["generation_configuration"],
            )
            digest = hashlib.sha256(
                json.dumps(
                    manifest,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode()
            ).hexdigest()
            manifest.update(sha256=digest, created_at=utc_now())
            db.execute(
                "INSERT INTO freezes VALUES (?,?)", (job_id, json.dumps(manifest))
            )
            return manifest
