"""Observed ranking/self-assessment signals, never calibrated probabilities."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, fields
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from app.generation.contracts import EvidenceContext


class ScoreKind(StrEnum):
    BM25 = "bm25"
    DENSE_COSINE = "dense_cosine"
    HYBRID_RRF = "hybrid_rrf"
    SELF_ASSESSMENT = "prompt_self_assessment"


class ScoreSource(StrEnum):
    RETRIEVAL = "retrieval"
    MODEL = "model_self_report"


class ScoreRole(StrEnum):
    OBSERVATIONAL = "observational"
    THRESHOLD_INPUT = "threshold_input"
    SELF_ASSESSMENT = "self_assessment"


@dataclass(frozen=True)
class ScoreSignal:
    kind: ScoreKind
    value: float | None
    source: ScoreSource
    retrieval_method: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    role: ScoreRole = ScoreRole.OBSERVATIONAL
    threshold: float | None = None
    threshold_direction: str | None = None
    unavailable_reason: str | None = None
    availability: Literal["available", "unavailable"] = field(init=False)
    lower_bound: float = field(init=False)
    upper_bound: float | None = field(init=False)
    direction: Literal["higher_is_more_support", "higher_is_more_relevant"] = field(
        init=False, default="higher_is_more_support",
    )
    calibration: Literal["uncalibrated"] = field(init=False, default="uncalibrated")
    schema_version: Literal["ragbench.score.v1"] = field(
        init=False, default="ragbench.score.v1",
    )

    def __post_init__(self) -> None:
        if (not isinstance(self.kind, ScoreKind)
                or not isinstance(self.source, ScoreSource)):
            raise ValueError("Invalid score kind/source")
        if not isinstance(self.role, ScoreRole):
            raise ValueError("Invalid score role")
        expected = (ScoreSource.MODEL if self.kind is ScoreKind.SELF_ASSESSMENT
                    else ScoreSource.RETRIEVAL)
        if self.source is not expected:
            raise ValueError("Score source does not match its kind")
        if self.kind is not ScoreKind.SELF_ASSESSMENT:
            if self.retrieval_method != self.kind.value:
                raise ValueError("Score family/method mismatch")
            object.__setattr__(self, "direction", "higher_is_more_relevant")
        elif self.retrieval_method is not None:
            raise ValueError("Model self-assessment is independent of retrieval method")
        if not isinstance(self.parameters, dict):
            raise ValueError("Score parameters must be an object")
        json.dumps(self.parameters, allow_nan=False)
        if (self.kind is ScoreKind.SELF_ASSESSMENT) != (
            self.role is ScoreRole.SELF_ASSESSMENT
        ):
            raise ValueError("Score role does not match its source")
        lower, upper = 0.0, None
        if self.kind is ScoreKind.DENSE_COSINE:
            lower, upper = -1.0, 1.0
        elif self.kind is ScoreKind.SELF_ASSESSMENT:
            upper = 1.0
        elif self.kind is ScoreKind.HYBRID_RRF:
            k, lists = self.parameters.get("rrf_k"), self.parameters.get("rank_lists")
            if k is not None or lists is not None:
                if type(k) is not int or k <= 0 or type(lists) is not int or lists < 0:
                    raise ValueError("RRF requires effective k and rank lists")
                upper = lists / (k + 1)
            elif self.value is not None:
                raise ValueError("RRF score needs bound provenance")
        for value in (self.value, self.threshold):
            if value is not None and (isinstance(value, bool)
                    or not isinstance(value, (float, int)) or not math.isfinite(value)):
                raise ValueError("Score and threshold must be finite numbers or null")
        if self.value is not None and (
            self.value < lower or (upper is not None and self.value > upper)
        ):
            raise ValueError("Score is outside its declared range")
        if self.role is ScoreRole.THRESHOLD_INPUT:
            if self.threshold is None or self.threshold_direction not in {
                "at_least", "at_most",
            }:
                raise ValueError("Threshold input requires threshold and comparison")
        elif self.threshold is not None or self.threshold_direction is not None:
            raise ValueError("Only threshold inputs carry a threshold")
        if self.value is None:
            if (not isinstance(self.unavailable_reason, str)
                    or not self.unavailable_reason.strip()):
                raise ValueError("Unavailable scores require a reason")
        elif self.unavailable_reason is not None:
            raise ValueError("Available score cannot have an unavailable reason")
        object.__setattr__(self, "availability", "unavailable" if self.value is None
                           else "available")
        object.__setattr__(self, "lower_bound", lower)
        object.__setattr__(self, "upper_bound", upper)


def retrieval_signal(
    evidence: tuple[EvidenceContext, ...], *, method: str | None = None,
    parameters: dict | None = None, role: ScoreRole = ScoreRole.OBSERVATIONAL,
    threshold: float | None = None, threshold_direction: str | None = None,
) -> ScoreSignal | None:
    """Maximum returned score; missing inputs stay unavailable, not zero."""
    method = method or (evidence[0].retrieval_method if evidence else None)
    if method not in {"bm25", "dense_cosine", "hybrid_rrf"}:
        return None  # Legacy/custom retrievers have no invented score family.
    parameters = dict(parameters or (
        evidence[0].score.parameters if evidence and evidence[0].score else {}
    ))
    parameters.setdefault("score_aggregation", "max")
    reason = None
    values = [e.retrieval_score for e in evidence]
    if not values or any(v is None for v in values):
        reason = "no_results" if not values else "missing_chunk_score"
    if method == "hybrid_rrf" and not {"rrf_k", "rank_lists"} <= parameters.keys():
        reason = "missing_fusion_provenance"
    value = None if reason else max(values)
    return ScoreSignal(ScoreKind(method), value, ScoreSource.RETRIEVAL, method,
                       parameters, role, threshold, threshold_direction, reason)


def score_from_dict(value: dict) -> ScoreSignal:
    """Validate archived score fields, including derived range and provenance."""
    if (not isinstance(value, dict)
            or set(value) != {f.name for f in fields(ScoreSignal)}):
        raise ValueError("Invalid serialized score fields")
    arguments = {f.name: value[f.name] for f in fields(ScoreSignal) if f.init}
    arguments.update(kind=ScoreKind(value["kind"]), source=ScoreSource(value["source"]),
                     role=ScoreRole(value["role"]))
    result = ScoreSignal(**arguments)
    if any(isinstance(value[name], bool) for name in ("lower_bound", "upper_bound")):
        raise ValueError("Score bounds must be numbers, not booleans")
    if any(value[f.name] != getattr(result, f.name) for f in fields(ScoreSignal)
           if not f.init):
        raise ValueError("Serialized score range or provenance is inconsistent")
    return result
