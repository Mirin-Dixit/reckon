"""Strict, fixture-only P4 job contracts."""

from typing import Literal

from pydantic import Field, JsonValue

from app.api.models import (
    EvaluationRequest,
    ExperimentResponse,
    ExperimentRunResponse,
    StrictModel,
)

SYNTHETIC_NOTICE = "Synthetic fixture — development only; no empirical claims."


class ExperimentRequest(EvaluationRequest):
    """Server-owned fixtures only; no file paths or provider overrides."""

    profile: Literal["p4-synthetic.v1"] = "p4-synthetic.v1"
    split: Literal["train", "dev"] = "train"
    random_seed: int = Field(default=0, strict=True)
    question_ids: list[str] | None = Field(default=None, max_length=10)
    generation: None = None


class JobSummary(StrictModel):
    schema_version: Literal["ragbench.experiment-job.v1"]
    id: str
    status: Literal["queued", "running", "done", "partial", "failed"]
    created_at: str
    updated_at: str
    notice: Literal["Synthetic fixture — development only; no empirical claims."]
    empirical_evaluation: Literal[False]
    configuration: dict[str, JsonValue]
    dataset_fingerprint: dict[str, str]
    runtime_source_sha256: str
    expected_run_count: int = Field(ge=1, le=40)
    observed_run_count: int = Field(ge=0, le=40)
    error: str | None


class JobResults(JobSummary):
    observations: list[ExperimentRunResponse]
    result: ExperimentResponse | None


class JobList(StrictModel):
    jobs: list[JobSummary]


class DevFreeze(StrictModel):
    schema_version: Literal["ragbench.dev-freeze.v1"]
    job_id: str
    empirical_evaluation: Literal[False]
    notice: Literal["Synthetic fixture — development only; no empirical claims."]
    configuration: dict[str, JsonValue]
    dataset_fingerprint: dict[str, str]
    software_metadata: dict[str, JsonValue]
    generation_configuration: dict[str, JsonValue]
    sha256: str
    created_at: str
