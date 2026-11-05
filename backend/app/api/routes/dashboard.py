"""Read-only P5 metadata/results; never constructs a worker or recovers jobs."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.errors import ApiProblem
from app.api.experiment_models import JobList, JobResults, JobSummary
from app.api.routes.experiment_jobs import local_access
from app.db.analysis_reader import read_analysis_history, read_analysis_jobs
from app.evaluation.serialization import sanitize_serialized

router = APIRouter(dependencies=[Depends(local_access)])


def _synthetic(job: dict) -> None:
    config = job.get("configuration", {})
    ids = config.get("question_ids")
    allowed = {f"synthetic_{config.get('split')}_0{i}" for i in range(1, 5)}
    if (
        config.get("profile") != "p4-synthetic.v1"
        or config.get("split") not in ("train", "dev")
        or not isinstance(ids, list)
        or not ids
        or not set(ids) <= allowed
        or len(ids) != len(set(ids))
        or job.get("empirical_evaluation") is not False
    ):
        raise ValueError("Only saved P4 synthetic records are available")
    UUID(job["id"])


def _invalid() -> ApiProblem:
    return ApiProblem(
        422, "invalid_saved_evaluation", "Saved synthetic evaluation data is invalid."
    )


@router.get("/analysis/experiments", response_model=JobList)
def history(
    request: Request,
    response: Response,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0, le=100000),
) -> JobList:
    response.headers["Cache-Control"] = "no-store"
    try:
        jobs = read_analysis_history(
            Path(request.app.state.experiment_store_path), limit, offset
        )
        for job in jobs:
            _synthetic(job)
        return JobList(
            jobs=[JobSummary.model_validate(sanitize_serialized(job)) for job in jobs]
        )
    except (ValueError, TypeError, KeyError):
        raise _invalid() from None
    except Exception:
        raise ApiProblem(
            503,
            "evaluation_storage_unavailable",
            "Read-only evaluation storage is unavailable.",
        ) from None


@router.get("/analysis/experiments/{job_id}", response_model=JobResults)
def saved_results(job_id: UUID, request: Request, response: Response) -> JobResults:
    response.headers["Cache-Control"] = "no-store"
    try:
        job = read_analysis_jobs(
            Path(request.app.state.experiment_store_path), (str(job_id),)
        )[0]
        _synthetic(job)
        record = job.get("result")
        if record is not None:
            split = job["configuration"]["split"]
            if (
                record.get("benchmark_split") != split
                or record.get("selected_question_ids")
                != job["configuration"]["question_ids"]
                or record.get("runs") != job.get("observations")
            ):
                raise ValueError("Saved snapshot mismatch")
        allowed = set(job["configuration"]["question_ids"])
        for row in job.get("observations", []):
            if (
                row.get("question_id") not in allowed
                or row.get("gold", {}).get("split") != job["configuration"]["split"]
            ):
                raise ValueError("Synthetic observation identity mismatch")
        return JobResults.model_validate(sanitize_serialized(job))
    except (KeyError, FileNotFoundError):
        raise ApiProblem(
            404, "experiment_not_found", "Saved experiment not found."
        ) from None
    except (ValueError, TypeError):
        raise _invalid() from None
    except Exception:
        raise ApiProblem(
            503,
            "evaluation_storage_unavailable",
            "Read-only evaluation storage is unavailable.",
        ) from None
