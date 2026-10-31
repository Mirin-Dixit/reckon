"""JSON serialization and schema-version checks for experiment records."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from app.evaluation.results import EXPERIMENT_SCHEMA_VERSION, ExperimentRecord
from app.generation.contracts import Decision, ExecutionStatus
from app.ingestion.schema import ALLOWED_SPLITS


def to_primitive(value: Any) -> Any:
    """Recursively convert dataclasses, enums, and containers to JSON values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: to_primitive(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_primitive(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Cannot serialize value of type {type(value).__name__}")


def experiment_to_json(experiment: ExperimentRecord, *, indent: int | None = 2) -> str:
    """Serialize an experiment deterministically, with stable key ordering."""
    return json.dumps(
        sanitize_serialized(experiment.to_dict()),
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
        allow_nan=False,
    )


def experiment_from_json(payload: str) -> dict[str, Any]:
    """Parse and validate the top-level versioned experiment structure."""
    try:
        record = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError("Experiment JSON is malformed") from error
    if not isinstance(record, dict):
        raise ValueError("Experiment record must be a JSON object")
    if record.get("schema_version") != EXPERIMENT_SCHEMA_VERSION:
        raise ValueError("Unsupported experiment schema version")
    if record.get("benchmark_split") not in ALLOWED_SPLITS:
        raise ValueError("Invalid benchmark_split")
    required = {
        "experiment_id",
        "created_at_utc",
        "benchmark_split",
        "selected_question_ids",
        "dataset_fingerprint",
        "retrieval_configuration",
        "policy_configurations",
        "generation_configuration",
        "random_seed",
        "software_metadata",
        "environment_metadata",
        "runs",
    }
    missing = required - record.keys()
    if missing:
        raise ValueError(f"Experiment record missing fields: {sorted(missing)}")
    for field in (
        "dataset_fingerprint",
        "retrieval_configuration",
        "generation_configuration",
        "software_metadata",
        "environment_metadata",
    ):
        if not isinstance(record[field], dict):
            raise ValueError(f"{field} must be an object")
    if not isinstance(record["policy_configurations"], list):
        raise ValueError("policy_configurations must be an array")
    if any(not isinstance(item, dict) for item in record["policy_configurations"]):
        raise ValueError("policy_configurations entries must be objects")
    if not isinstance(record.get("stopped_early", False), bool):
        raise ValueError("stopped_early must be a boolean")
    if not isinstance(record.get("comparison_warnings", []), list):
        raise ValueError("comparison_warnings must be an array")
    if not isinstance(record.get("metrics", {}), dict):
        raise ValueError("metrics must be an object")
    if record["random_seed"] is not None and type(record["random_seed"]) is not int:
        raise ValueError("random_seed must be an integer or null")
    if (
        not isinstance(record["experiment_id"], str)
        or not record["experiment_id"].strip()
    ):
        raise ValueError("Experiment ID must be a non-empty string")
    try:
        uuid.UUID(record["experiment_id"])
    except (ValueError, AttributeError) as error:
        raise ValueError("Experiment ID must be a UUID") from error
    timestamp = record["created_at_utc"]
    if not isinstance(timestamp, str):
        raise ValueError("created_at_utc must be a string")
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("created_at_utc must be ISO-8601") from error
    if (
        parsed_timestamp.tzinfo is None
        or parsed_timestamp.utcoffset().total_seconds() != 0
    ):
        raise ValueError("created_at_utc must use UTC")
    selected = record["selected_question_ids"]
    if not isinstance(selected, list) or any(
        not isinstance(item, str) or not item for item in selected
    ):
        raise ValueError("selected_question_ids must be an array of non-empty strings")
    if len(selected) != len(set(selected)):
        raise ValueError("selected_question_ids must be unique")
    runs = record["runs"]
    if not isinstance(runs, list):
        raise ValueError("runs must be an array")
    run_ids = set()
    policy_questions = set()
    for run in runs:
        if not isinstance(run, dict) or not {
            "run_id",
            "question_id",
            "policy_name",
            "observed",
            "gold",
        }.issubset(run):
            raise ValueError(
                "Each run must contain run_id, question_id, policy_name, "
                "observed, and gold"
            )
        for field in ("run_id", "question_id", "policy_name"):
            if not isinstance(run[field], str) or not run[field]:
                raise ValueError(f"run {field} must be a non-empty string")
        try:
            uuid.UUID(run["run_id"])
        except ValueError as error:
            raise ValueError("run_id must be a UUID") from error
        if run["run_id"] in run_ids:
            raise ValueError("run IDs must be unique")
        run_ids.add(run["run_id"])
        if run["question_id"] not in selected:
            raise ValueError("run question_id must be in selected_question_ids")
        key = (run["policy_name"], run["question_id"])
        if key in policy_questions:
            raise ValueError("duplicate question runs per policy are not allowed")
        policy_questions.add(key)
        if not isinstance(run["observed"], dict) or not isinstance(run["gold"], dict):
            raise ValueError("run observed and gold must be objects")
        observed = run["observed"]
        if not {"decision", "execution_status", "evidence_assessment"}.issubset(
            observed
        ):
            raise ValueError("observed result is missing required fields")
        gold = run["gold"]
        if not {
            "question_id",
            "split",
            "is_answerable",
            "expected_answer",
            "expected_safe_behavior",
            "unanswerable_category",
            "ambiguity_type",
            "domain",
            "question_type",
            "evidence_spans",
        }.issubset(gold):
            raise ValueError("gold labels are missing required fields")
        if (
            gold["question_id"] != run["question_id"]
            or gold["split"] != record["benchmark_split"]
        ):
            raise ValueError("gold identity/split must match its run and experiment")
        if not isinstance(gold["is_answerable"], bool) or not isinstance(
            gold["evidence_spans"], list
        ):
            raise ValueError("gold answerability or evidence_spans has invalid type")
        if any(
            not isinstance(span, dict)
            or not {"doc_id", "start_char", "end_char", "text"}.issubset(span)
            for span in gold["evidence_spans"]
        ):
            raise ValueError("evidence_spans entries have invalid structure")
        if not isinstance(observed["evidence_assessment"], dict):
            raise ValueError("evidence_assessment must be an object")
        if not isinstance(observed.get("citations"), list):
            raise ValueError("observed citations must be an array")
        if observed.get("retrieval") is not None and not isinstance(
            observed["retrieval"], dict
        ):
            raise ValueError("retrieval metadata must be an object or null")
        if not isinstance(observed["execution_status"], str):
            raise ValueError("execution_status must be a string")
        if observed["decision"] is not None and not isinstance(
            observed["decision"], str
        ):
            raise ValueError("decision must be a string or null")
        if observed["execution_status"] not in {item.value for item in ExecutionStatus}:
            raise ValueError("execution_status is invalid")
        if observed["decision"] is not None and observed["decision"] not in {
            item.value for item in Decision
        }:
            raise ValueError("decision is invalid")
        if (observed["execution_status"] == ExecutionStatus.SUCCEEDED.value) != (
            observed["decision"] is not None
        ):
            raise ValueError("decision and execution_status are inconsistent")
        if gold["is_answerable"] and not isinstance(gold.get("expected_answer"), str):
            raise ValueError("answerable gold labels require expected_answer")
        if not gold["is_answerable"] and gold.get("expected_answer") is not None:
            raise ValueError("unanswerable gold labels cannot have expected_answer")
    return record


def sanitize_serialized(value: Any, key: str = "") -> Any:
    """Redact secret-keyed values and recognizable credential strings only."""
    normalized = "".join(
        character for character in key.casefold() if character.isalnum()
    )
    secret_key = any(
        marker in normalized
        for marker in (
            "apikey",
            "apitoken",
            "accesstoken",
            "refreshtoken",
            "secret",
            "password",
            "credential",
            "authorization",
            "bearer",
        )
    ) or normalized in {"key", "token"}
    if secret_key and not normalized.endswith("envvar"):
        return "<redacted>"
    if isinstance(value, dict):
        return {k: sanitize_serialized(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_serialized(item) for item in value]
    if isinstance(value, str):
        patterns = (
            r"(?i)\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
            r"(?i)\bgh[pousr]_[A-Za-z0-9]{20,}\b",
            r"(?i)\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
            r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}=*",
        )
        for pattern in patterns:
            value = re.sub(pattern, "<redacted-credential>", value)
    return value


def write_experiment_json(
    experiment: ExperimentRecord, path: str | Path, *, indent: int | None = 2
) -> None:
    """Write one complete experiment record as UTF-8 JSON."""
    Path(path).write_text(
        experiment_to_json(experiment, indent=indent), encoding="utf-8"
    )


def read_experiment_json(path: str | Path) -> dict[str, Any]:
    """Read and version-check a UTF-8 experiment JSON file."""
    return experiment_from_json(Path(path).read_text(encoding="utf-8"))
