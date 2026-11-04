"""Loopback-only synthetic experiment workspace endpoints."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.errors import ApiProblem
from app.api.experiment_models import (
    DevFreeze,
    ExperimentRequest,
    JobList,
    JobResults,
    JobSummary,
)
from app.db.experiments import QueueFull, StoreConflict
from app.evaluation.experiment_jobs import ExperimentJobs

router = APIRouter()
_initialization_lock = threading.Lock()
DEFAULT_STORE = (
    Path(__file__).resolve().parents[4]
    / ".ragbench-cache/experiments/experiments.sqlite3"
)


def local_access(request: Request) -> None:
    """Reject remote clients, DNS rebinding and cross-origin browser writes."""
    testing = request.client is not None and request.client.host == "testclient"
    allowed = {"127.0.0.1", "localhost", "::1"}
    if not testing and (
        request.client is None
        or request.client.host not in allowed
        or request.url.hostname not in allowed
    ):
        raise ApiProblem(403, "local_only", "Experiments require loopback access.")
    origin = request.headers.get("origin")
    if origin:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in ("http", "https")
            or parsed.hostname not in allowed
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or (
                origin not in request.app.state.settings.cors_origins
                and origin != f"{request.url.scheme}://{request.url.netloc}"
            )
        ):
            raise ApiProblem(403, "local_only", "Use the local frontend origin.")


def jobs(request: Request, _: None = Depends(local_access)) -> ExperimentJobs:
    with _initialization_lock:
        service = getattr(request.app.state, "experiment_jobs", None)
        if service is None:
            try:
                service = ExperimentJobs(request.app.state.experiment_store_path)
            except (OSError, sqlite3.Error, ValueError):
                raise ApiProblem(
                    503,
                    "experiment_storage_unavailable",
                    "Experiment storage is unavailable or in use.",
                ) from None
            request.app.state.experiment_jobs = service
    if service.unavailable:
        raise ApiProblem(
            503,
            "experiment_worker_unavailable",
            "Worker stopped; restart the backend to recover jobs.",
        )
    return service


def storage_error() -> ApiProblem:
    return ApiProblem(
        503,
        "experiment_storage_unavailable",
        "Experiment storage is unavailable; no success is confirmed.",
    )


def summary(job: dict) -> dict:
    return {k: v for k, v in job.items() if k not in ("observations", "result")}


@router.post("/experiments", status_code=202, response_model=JobSummary)
def start(body: ExperimentRequest, service: ExperimentJobs = Depends(jobs)) -> dict:
    try:
        return summary(service.submit(body))
    except QueueFull:
        raise ApiProblem(
            429,
            "experiment_queue_full",
            "Queue is full (one active, four waiting). Try later.",
        ) from None
    except ValueError:
        raise ApiProblem(
            422,
            "invalid_fixture_selection",
            "Select questions from the requested fixture split.",
        ) from None
    except (OSError, sqlite3.Error):
        raise storage_error() from None


@router.get("/experiments", response_model=JobList)
def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
    service: ExperimentJobs = Depends(jobs),
) -> dict:
    try:
        return {"jobs": [summary(j) for j in service.store.list(limit, offset)]}
    except (OSError, sqlite3.Error):
        raise storage_error() from None


def require_job(service: ExperimentJobs, job_id: UUID) -> dict:
    try:
        job = service.store.get(str(job_id))
    except (OSError, sqlite3.Error):
        raise storage_error() from None
    if job is None:
        raise ApiProblem(404, "experiment_not_found", "Experiment not found.")
    return job


@router.get("/experiments/{job_id}", response_model=JobSummary)
def get_job(job_id: UUID, service: ExperimentJobs = Depends(jobs)) -> dict:
    return summary(require_job(service, job_id))


@router.get("/experiments/{job_id}/results", response_model=JobResults)
def results(job_id: UUID, service: ExperimentJobs = Depends(jobs)) -> dict:
    # Explicit evaluator-only endpoint; gold is never in status/list responses.
    return require_job(service, job_id)


@router.post("/experiments/{job_id}/freeze", response_model=DevFreeze)
def freeze(job_id: UUID, service: ExperimentJobs = Depends(jobs)) -> dict:
    try:
        return service.store.freeze(str(job_id))
    except KeyError:
        raise ApiProblem(404, "experiment_not_found", "Experiment not found.") from None
    except StoreConflict:
        raise ApiProblem(
            409,
            "invalid_dev_freeze",
            "Freeze requires a fully successful synthetic Dev job.",
        ) from None
    except (OSError, sqlite3.Error):
        raise storage_error() from None
