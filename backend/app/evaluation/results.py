"""Versioned, JSON-compatible experiment and per-question result models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.generation.contracts import RunResult
from app.ingestion.schema import ALLOWED_SPLITS, Question

EXPERIMENT_SCHEMA_VERSION = "ragbench.experiment.v2"


@dataclass(frozen=True)
class GoldLabels:
    """Evaluator-only reference fields; never passed into runtime components."""

    question_id: str
    split: str
    is_answerable: bool
    expected_answer: str | None
    expected_safe_behavior: str | None
    unanswerable_category: str | None
    ambiguity_type: str | None
    domain: str
    question_type: str
    evidence_spans: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        if not self.question_id.strip():
            raise ValueError("question_id must be non-empty")
        if self.split not in ALLOWED_SPLITS:
            raise ValueError(f"invalid split: {self.split}")
        if type(self.is_answerable) is not bool:
            raise ValueError("is_answerable must be a boolean")
        if self.is_answerable and (
            not isinstance(self.expected_answer, str)
            or not self.expected_answer.strip()
        ):
            raise ValueError("answerable gold labels require expected_answer")
        if not self.is_answerable and self.expected_answer is not None:
            raise ValueError("unanswerable gold labels cannot have expected_answer")

    @classmethod
    def from_question(cls, question: Question) -> GoldLabels:
        """Copy benchmark labels after runtime execution, for scoring only."""
        return cls(
            question_id=question.id,
            split=question.split,
            is_answerable=question.is_answerable,
            expected_answer=question.expected_answer,
            expected_safe_behavior=question.expected_safe_behavior,
            unanswerable_category=question.unanswerable_category,
            ambiguity_type=question.ambiguity_type,
            domain=question.domain,
            question_type=question.question_type,
            evidence_spans=tuple(span.to_dict() for span in question.evidence_spans),
        )


@dataclass(frozen=True)
class ErrorDetails:
    """Sanitized execution error data; raw exception text is deliberately omitted."""

    kind: str
    message: str
    retryable: bool | None = None


@dataclass(frozen=True)
class ExperimentRun:
    """One policy/question observation plus a disjoint evaluator-only gold section."""

    run_id: str
    question_id: str
    policy_name: str
    observed: RunResult
    gold: GoldLabels
    error: ErrorDetails | None = None


@dataclass(frozen=True)
class ExperimentRecord:
    """Stable experiment envelope suitable for JSON archival and metric replay."""

    experiment_id: str
    schema_version: str
    created_at_utc: str
    benchmark_split: str
    selected_question_ids: tuple[str, ...]
    dataset_fingerprint: dict[str, str]
    retrieval_configuration: dict[str, Any]
    policy_configurations: tuple[dict[str, Any], ...]
    generation_configuration: dict[str, Any]
    random_seed: int | None
    software_metadata: dict[str, Any]
    environment_metadata: dict[str, Any]
    runs: tuple[ExperimentRun, ...]
    stopped_early: bool = False
    comparison_warnings: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema_version != EXPERIMENT_SCHEMA_VERSION:
            raise ValueError(f"unsupported schema version: {self.schema_version}")
        if self.benchmark_split not in ALLOWED_SPLITS:
            raise ValueError(f"invalid benchmark split: {self.benchmark_split}")
        if type(self.random_seed) not in (int, type(None)):
            raise ValueError("random_seed must be an integer or None")
        if not self.experiment_id.strip() or not self.created_at_utc.strip():
            raise ValueError("experiment_id and created_at_utc must be non-empty")
        try:
            uuid.UUID(self.experiment_id)
        except ValueError as error:
            raise ValueError("experiment_id must be a UUID") from error
        try:
            timestamp = datetime.fromisoformat(
                self.created_at_utc.replace("Z", "+00:00")
            )
        except ValueError as error:
            raise ValueError("created_at_utc must be an ISO-8601 timestamp") from error
        if timestamp.tzinfo is None or timestamp.utcoffset() != UTC.utcoffset(
            timestamp
        ):
            raise ValueError("created_at_utc must use UTC")
        if len(self.selected_question_ids) != len(set(self.selected_question_ids)):
            raise ValueError("selected_question_ids must be unique")
        run_ids = [run.run_id for run in self.runs]
        if any(not run_id.strip() for run_id in run_ids) or len(run_ids) != len(
            set(run_ids)
        ):
            raise ValueError("run IDs must be non-empty and unique")
        for run_id in run_ids:
            try:
                uuid.UUID(run_id)
            except ValueError as error:
                raise ValueError("run IDs must be UUIDs") from error
        selected = set(self.selected_question_ids)
        seen_policy_questions = set()
        for run in self.runs:
            if run.question_id not in selected:
                raise ValueError("run question_id must be in selected_question_ids")
            if (
                run.gold.question_id != run.question_id
                or run.gold.split != self.benchmark_split
            ):
                raise ValueError("run gold identity/split must match its experiment")
            key = (run.policy_name, run.question_id)
            if key in seen_policy_questions:
                raise ValueError("duplicate question runs per policy are not allowed")
            seen_policy_questions.add(key)

    def to_dict(self) -> dict[str, Any]:
        """Convert the complete experiment to JSON primitives."""
        from app.evaluation.serialization import sanitize_serialized, to_primitive

        return sanitize_serialized(to_primitive(self))
