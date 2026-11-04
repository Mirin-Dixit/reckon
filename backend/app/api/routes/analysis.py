"""Read-only synthetic analysis, with no runtime/store initialization or inference."""

import threading
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.errors import ApiProblem
from app.api.routes.experiment_jobs import local_access
from app.db.analysis_reader import read_analysis_jobs
from app.evaluation.matched_analysis import AnalysisReport, analyze_matched
from app.evaluation.risk_coverage import from_p4_job

router = APIRouter()
_capacity = threading.BoundedSemaphore(1)


def analysis_capacity():
    """Bound CPU/memory concurrency; cancellation never implies backend work stopped."""
    if not _capacity.acquire(blocking=False):
        raise ApiProblem(
            503, "analysis_busy", "Another analysis is running. Try later."
        )
    try:
        yield
    finally:
        _capacity.release()


@router.get(
    "/experiments/{job_id}/analysis",
    response_model=AnalysisReport,
    dependencies=[Depends(local_access), Depends(analysis_capacity)],
)
def analyze_experiment(
    job_id: UUID,
    request: Request,
    response: Response,
    compare: Annotated[list[UUID] | None, Query(max_length=7)] = None,
    resamples: Annotated[int, Query(ge=2, le=5000)] = 2000,
    seed: Annotated[int, Query(ge=-(2**31), le=2**31 - 1)] = 0,
    lexical_proxy: bool = False,
    threshold_only: bool = False,
) -> AnalysisReport:
    """Compare complete saved synthetic cohorts only; no threshold trial execution."""
    response.headers["Cache-Control"] = "no-store"
    ids = (str(job_id), *(str(i) for i in compare or []))
    if len(ids) != len(set(ids)):
        raise ApiProblem(
            422, "invalid_analysis_selection", "Select distinct experiments."
        )
    try:
        jobs = read_analysis_jobs(Path(request.app.state.experiment_store_path), ids)
    except KeyError:
        raise ApiProblem(404, "experiment_not_found", "Experiment not found.") from None
    except ValueError:
        raise ApiProblem(
            422, "invalid_analysis_record", "Saved results cannot be analyzed."
        ) from None
    except Exception:
        raise ApiProblem(
            503,
            "analysis_storage_unavailable",
            "Read-only experiment storage is unavailable.",
        ) from None
    try:
        cohorts = []
        for job in jobs:
            if job.get("status") not in ("done", "partial", "failed"):
                raise ValueError("Experiment is not terminal")
            record = job.get("result")
            if not isinstance(record, dict) or record.get("stopped_early"):
                raise ValueError("Missing or interrupted result")
            allowed = {
                f"synthetic_{record.get('benchmark_split')}_0{i}" for i in range(1, 5)
            }
            if not set(record.get("selected_question_ids", [])) <= allowed:
                raise ValueError("Only P4 synthetic question IDs are supported")
            policies = [
                p
                for p in record.get("policy_configurations", [])
                if not threshold_only or p["name"] == "threshold"
            ]
            if not policies:
                raise ValueError("No selected policies in saved experiment")
            for policy in policies:
                cohorts.append(
                    from_p4_job(job, policy["name"], lexical_proxy=lexical_proxy)
                )
        return analyze_matched(cohorts, resamples=resamples, seed=seed)
    except (ValueError, KeyError, TypeError):
        raise ApiProblem(
            422,
            "incompatible_analysis",
            "Complete matched synthetic cohorts and compatible provenance "
            "are required.",
        ) from None
