"""Split-aware experiment execution with a hard runtime/gold data boundary."""

from __future__ import annotations

import copy
import platform
import subprocess
import sys
import tomllib
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from app.evaluation.metrics import summarize_runs
from app.evaluation.results import (
    EXPERIMENT_SCHEMA_VERSION,
    ErrorDetails,
    ExperimentRecord,
    ExperimentRun,
    GoldLabels,
)
from app.evaluation.serialization import to_primitive, write_experiment_json
from app.generation.contracts import (
    EvidenceAssessment,
    ExecutionStatus,
    ProviderError,
    RunResult,
)
from app.generation.pipeline import DecisionPolicy, RagPipeline
from app.ingestion.loader import load_dataset_snapshot
from app.ingestion.schema import ALLOWED_SPLITS, Document, Question


class ErrorHandlingMode(StrEnum):
    CONTINUE = "continue"
    FAIL_FAST = "fail_fast"


@dataclass(frozen=True)
class PolicyRunConfig:
    """A policy instance and secret-free parameters recorded for an experiment."""

    name: str
    policy: DecisionPolicy
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("policy configuration name must be non-empty")


PipelineFactory = Callable[
    [
        DecisionPolicy,
        Mapping[str, Document],
        Mapping[str, Any],
        Mapping[str, Any],
        int | None,
    ],
    RagPipeline,
]


class EvaluationRunner:
    """Run policy comparisons while keeping ``Question`` gold outside the pipeline."""

    def __init__(
        self,
        documents_path: str | Path,
        questions_path: str | Path,
    ) -> None:
        documents, questions, fingerprint = load_dataset_snapshot(
            documents_path, questions_path
        )
        self._documents = MappingProxyType({doc.id: doc for doc in documents})
        self._questions = tuple(questions)
        self._dataset_fingerprint = fingerprint

    def run(
        self,
        *,
        split: str,
        policies: Sequence[PolicyRunConfig],
        pipeline_factory: PipelineFactory,
        retrieval_configuration: Mapping[str, Any],
        generation_configuration: Mapping[str, Any],
        random_seed: int | None = None,
        question_ids: Sequence[str] | None = None,
        error_mode: ErrorHandlingMode = ErrorHandlingMode.CONTINUE,
        output_path: str | Path | None = None,
        experiment_id: str | None = None,
        on_observation: Callable[[ExperimentRun], None] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> ExperimentRecord:
        """Run each selected question for each policy using only question text.

        The pipeline factory receives documents and sanitized runtime configurations,
        never Question instances, reference answers, annotations, or gold spans.
        The evaluator attaches gold labels only after each run has completed.
        """
        if split not in ALLOWED_SPLITS:
            raise ValueError(f"split must be one of {sorted(ALLOWED_SPLITS)}")
        if not isinstance(error_mode, ErrorHandlingMode):
            raise ValueError("error_mode must be an ErrorHandlingMode")
        if random_seed is not None and type(random_seed) is not int:
            raise ValueError("random_seed must be an integer or None")
        policy_names = [item.name for item in policies]
        if len(policy_names) != len(set(policy_names)):
            raise ValueError("policy configuration names must be unique")

        split_questions = [item for item in self._questions if item.split == split]
        if question_ids is None:
            selected = split_questions
        else:
            if len(question_ids) != len(set(question_ids)):
                raise ValueError("question_ids must not contain duplicates")
            by_id = {item.id: item for item in split_questions}
            unknown = set(question_ids) - by_id.keys()
            if unknown:
                raise ValueError(
                    f"Question IDs are not in split {split}: {sorted(unknown)}"
                )
            selected_ids = set(question_ids)
            selected = [item for item in split_questions if item.id in selected_ids]

        retrieval_config = _sanitize(to_primitive(dict(retrieval_configuration)))
        generation_config = _sanitize(to_primitive(dict(generation_configuration)))
        runs: list[ExperimentRun] = []
        warnings: list[str] = []
        evidence_by_question: dict[str, Any] = {}
        stopped_early = False
        stop_after_failure = False

        for policy_config in policies:
            if should_stop is not None and should_stop():
                stopped_early = True
                break
            if not selected:
                continue
            try:
                pipeline = pipeline_factory(
                    policy_config.policy,
                    self._documents,
                    copy.deepcopy(retrieval_config),
                    copy.deepcopy(generation_config),
                    random_seed,
                )
            except Exception as error:
                for question in selected:
                    record = self._failed_run(
                        question,
                        policy_config.name,
                        error,
                    )
                    runs.append(record)
                    if on_observation is not None:
                        on_observation(record)
                    if error_mode is ErrorHandlingMode.FAIL_FAST:
                        stopped_early = True
                        stop_after_failure = True
                        break
                if stop_after_failure:
                    break
                continue

            for question in selected:
                if should_stop is not None and should_stop():
                    stopped_early = True
                    break
                try:
                    observed = pipeline.run(question.question)
                    error_details = _error_from_result(observed)
                except Exception as error:
                    observed = RunResult(
                        decision=None,
                        evidence_assessment=EvidenceAssessment(),
                        execution_status=ExecutionStatus.FAILED,
                    )
                    error_details = _safe_error(error)
                record = ExperimentRun(
                    run_id=str(uuid.uuid4()),
                    question_id=question.id,
                    policy_name=policy_config.name,
                    observed=observed,
                    error=error_details,
                    gold=GoldLabels.from_question(question),
                )
                runs.append(record)
                if on_observation is not None:
                    on_observation(record)
                if observed.retrieval is not None:
                    evidence = to_primitive(observed.retrieval.evidence)
                    previous = evidence_by_question.setdefault(question.id, evidence)
                    if previous != evidence:
                        warning = (
                            f"Retrieved evidence differs across policies for "
                            f"question {question.id}; paired comparison is invalid."
                        )
                        if warning not in warnings:
                            warnings.append(warning)
                if (
                    error_details is not None
                    and error_mode is ErrorHandlingMode.FAIL_FAST
                ):
                    stopped_early = True
                    stop_after_failure = True
                    break
            if stop_after_failure:
                break

        record = ExperimentRecord(
            experiment_id=experiment_id or str(uuid.uuid4()),
            schema_version=EXPERIMENT_SCHEMA_VERSION,
            created_at_utc=_utc_now(),
            benchmark_split=split,
            selected_question_ids=tuple(item.id for item in selected),
            dataset_fingerprint=self._dataset_fingerprint,
            retrieval_configuration=retrieval_config,
            policy_configurations=tuple(
                {
                    "name": item.name,
                    "parameters": _sanitize(to_primitive(dict(item.parameters))),
                }
                for item in policies
            ),
            generation_configuration=generation_config,
            random_seed=random_seed,
            software_metadata=_software_metadata(),
            environment_metadata={
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
            },
            runs=tuple(runs),
            stopped_early=stopped_early,
            comparison_warnings=tuple(warnings),
            metrics=summarize_runs(
                runs,
                retrieval_config,
                expected_question_ids=[item.id for item in selected],
                policy_names=policy_names,
            ),
        )
        if output_path is not None:
            write_experiment_json(record, output_path)
        return record

    @staticmethod
    def _failed_run(
        question: Question,
        policy_name: str,
        error: Exception,
    ) -> ExperimentRun:
        return ExperimentRun(
            run_id=str(uuid.uuid4()),
            question_id=question.id,
            policy_name=policy_name,
            observed=RunResult(
                decision=None,
                evidence_assessment=EvidenceAssessment(),
                execution_status=ExecutionStatus.FAILED,
                policy_name=policy_name,
            ),
            error=_safe_error(error),
            gold=GoldLabels.from_question(question),
        )


def _safe_error(error: Exception) -> ErrorDetails:
    if isinstance(error, ProviderError):
        return ErrorDetails(
            kind=error.kind.value,
            message=f"Provider execution failed ({error.kind.value}).",
            retryable=error.retryable,
        )
    return ErrorDetails(
        kind=type(error).__name__,
        message="Pipeline execution failed; raw exception text was omitted.",
    )


def _error_from_result(result: RunResult) -> ErrorDetails | None:
    if result.execution_status is ExecutionStatus.SUCCEEDED:
        return None
    return ErrorDetails(
        kind=result.execution_status.value,
        message=f"Run ended with execution status {result.execution_status.value}.",
    )


def _sanitize(value: Any, key: str = "") -> Any:
    # Normalize punctuation/case so apiKey, API_KEY, OPENAI_API_KEY, etc. map
    # to the same secret-bearing key vocabulary.
    normalized_key = "".join(
        character for character in key.casefold() if character.isalnum()
    )
    secret_key = any(
        marker in normalized_key
        for marker in (
            "apikey",
            "apitoken",
            "accesstoken",
            "refreshtoken",
            "password",
            "secret",
            "credential",
            "authorization",
            "bearer",
        )
    ) and not normalized_key.endswith("envvar")
    secret_key = secret_key or normalized_key in {"key", "token"}
    if secret_key:
        return "<redacted>"
    if isinstance(value, dict):
        return {str(k): _sanitize(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _software_metadata() -> dict[str, Any]:
    project_version = "unknown"
    try:
        with Path("pyproject.toml").open("rb") as source:
            project_version = tomllib.load(source)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        pass
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        revision = None
    try:
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.strip()
        )
    except (OSError, subprocess.SubprocessError):
        dirty = None
    return {
        "project_version": project_version,
        "git_revision": revision,
        "working_tree_dirty": dirty,
    }
