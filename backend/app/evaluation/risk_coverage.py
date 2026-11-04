"""Derived R1 analysis only. Never mutates P4 records or judges semantics."""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.evaluation.metrics import _exact_match
from app.evaluation.results import ExperimentRecord
from app.evaluation.serialization import experiment_from_json
from app.generation.contracts import Decision, ExecutionStatus
from app.generation.scores import score_from_dict

SCHEMA_VERSION = "ragbench.risk-coverage.v1"
NOTICE = "Synthetic development analysis; lexical proxy is not semantic correctness."


def canonical(value: object) -> str:
    """Take a finite, detached JSON snapshot, suitable for hashing and comparison."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class AnalysisModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, allow_inf_nan=False
    )


class Observation(AnalysisModel):
    question_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    status: ExecutionStatus
    decision: Decision | None
    error_kind: str | None = None
    loss: Literal[0, 1] | None = None
    gold_sha256: str
    output_sha256: str
    evidence_sha256: str
    scores: tuple[str, ...] = ()

    @field_validator("loss", mode="before")
    @classmethod
    def validate_loss(cls, value):
        if value is not None and (type(value) is not int or value not in (0, 1)):
            raise ValueError("Loss must be an integer 0, 1 or null")
        return value

    @model_validator(mode="after")
    def validate_observation(self):
        if (self.status is ExecutionStatus.SUCCEEDED) != (self.decision is not None):
            raise ValueError("Execution failure must not have a decision")
        if self.decision is not Decision.ANSWER and self.loss is not None:
            raise ValueError("Only answers have a selective loss")
        for value in (self.gold_sha256, self.output_sha256, self.evidence_sha256):
            _hash(value)
        for score in self.scores:
            score_from_dict(json.loads(score))
        return self


def _hash(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("Expected a lowercase SHA-256 fingerprint")


class Cohort(AnalysisModel):
    schema_version: Literal["ragbench.risk-coverage.v1"] = SCHEMA_VERSION
    notice: Literal[
        "Synthetic development analysis; lexical proxy is not semantic correctness."
    ] = NOTICE
    split: Literal["train", "dev"]
    policy_name: Literal["always_answer", "threshold", "prompt_abstention"]
    expected_ids: tuple[str, ...]
    observations: tuple[Observation, ...]
    source_record_sha256: str
    source_experiment_id: str
    provenance_json: str
    loss_basis: Literal["unknown", "synthetic_lexical_proxy"] = "unknown"

    @model_validator(mode="after")
    def validate_cohort(self):
        _hash(self.source_record_sha256)
        uuid.UUID(self.source_experiment_id)
        if len(set(self.expected_ids)) != len(self.expected_ids) or any(
            not q.strip() for q in self.expected_ids
        ):
            raise ValueError("Expected question IDs must be nonempty and unique")
        ids = [o.question_id for o in self.observations]
        runs = [o.run_id for o in self.observations]
        if len(set(ids)) != len(ids) or len(set(runs)) != len(runs):
            raise ValueError("Duplicate observations are not independent samples")
        if not set(ids) <= set(self.expected_ids):
            raise ValueError("Observation outside the fixed cohort")
        provenance = json.loads(self.provenance_json)
        canonical(provenance)
        if set(provenance) != {
            "dataset",
            "retrieval",
            "generation",
            "policy",
            "seed",
            "software",
        }:
            raise ValueError("Incomplete analysis provenance")
        if any(
            not isinstance(provenance[k], dict)
            for k in ("dataset", "retrieval", "generation", "policy", "software")
        ):
            raise ValueError("Provenance sections must be objects")
        for key in ("documents_sha256", "questions_sha256"):
            _hash(provenance["dataset"].get(key, ""))
        generation = provenance["generation"]
        if (
            generation.get("provider") != "synthetic"
            or generation.get("model") != "fixture-rules.v1"
            or generation.get("external_calls") is not False
        ):
            raise ValueError("R1.1 accepts synthetic-only provenance")
        _hash(generation.get("source_sha256", ""))
        if provenance["policy"].get("name") != self.policy_name:
            raise ValueError("Policy identity conflicts with provenance")
        parameters = provenance["policy"].get("parameters")
        if not isinstance(parameters, dict):
            raise ValueError("Missing effective policy parameters")
        from app.api.models import PolicyRequest, RetrievalRequest

        policy = PolicyRequest.model_validate(
            {
                "name": self.policy_name,
                **{
                    k: v
                    for k, v in parameters.items()
                    if k in PolicyRequest.model_fields and k != "name" and v is not None
                },
            }
        )
        retrieval = provenance["retrieval"]
        parsed_retrieval = RetrievalRequest.model_validate(
            {
                k: v
                for k, v in retrieval.items()
                if k not in ("chunk_size", "chunk_overlap", "k1", "b", "rank_lists")
            }
        )
        if self.policy_name == "threshold" and (
            policy.score_type != parsed_retrieval.score_type
        ):
            raise ValueError("Threshold score and retrieval method disagree")
        if type(provenance["seed"]) is not int:
            raise ValueError("Synthetic analysis requires an explicit integer seed")
        method = provenance["retrieval"].get("method")
        kinds = {"bm25": "bm25", "dense": "dense_cosine", "hybrid": "hybrid_rrf"}
        if method not in kinds or not provenance["software"]:
            raise ValueError("Missing retrieval/software provenance")
        for row in self.observations:
            if self.loss_basis == "unknown" and row.loss is not None:
                raise ValueError("Unknown judgments cannot contain inferred losses")
            for serialized in row.scores:
                score = score_from_dict(json.loads(serialized))
                if (
                    score.source.value == "retrieval"
                    and score.kind.value != kinds[method]
                ):
                    raise ValueError("Score method conflicts with cohort provenance")
                if score.source.value == "retrieval" and any(
                    score.parameters[key] != retrieval[key]
                    for key in score.parameters.keys() & retrieval.keys()
                ):
                    raise ValueError(
                        "Score parameters conflict with retrieval provenance"
                    )
        return self


def from_experiment(
    record: ExperimentRecord | dict,
    policy_name: str,
    *,
    lexical_proxy: bool = False,
) -> Cohort:
    """Copy one policy's evaluator-side records; never pass gold into runtime."""
    from app.api.models import ExperimentResponse

    data = record.to_dict() if isinstance(record, ExperimentRecord) else record
    ExperimentResponse.model_validate(data)
    data = experiment_from_json(canonical(data))
    configs = [p for p in data["policy_configurations"] if p["name"] == policy_name]
    if len(configs) != 1:
        raise ValueError("Exactly one declared policy is required")
    declared = {p["name"] for p in data["policy_configurations"]}
    if len(declared) != len(data["policy_configurations"]) or any(
        r["policy_name"] not in declared for r in data["runs"]
    ):
        raise ValueError("Undeclared or duplicated policy")
    gold_by_id = {}
    for row in data["runs"]:
        digest = fingerprint(row["gold"])
        if (
            row["question_id"] in gold_by_id
            and gold_by_id[row["question_id"]] != digest
        ):
            raise ValueError("Gold annotations differ across policies")
        gold_by_id[row["question_id"]] = digest
    observations = []
    for row in data["runs"]:
        if row["policy_name"] != policy_name:
            continue
        result, gold = row["observed"], row["gold"]
        decision = Decision(result["decision"]) if result["decision"] else None
        required_body = {
            Decision.ANSWER: "answer",
            Decision.CLARIFY: "clarification_question",
        }.get(decision)
        if required_body and (
            not isinstance(result.get(required_body), str)
            or not result[required_body].strip()
        ):
            raise ValueError(
                "Successful decision is missing its required response body"
            )
        if decision is Decision.ABSTAIN and result.get("abstention_reason") is None:
            raise ValueError("Successful abstention is missing its structured reason")
        if policy_name == "threshold" and decision is not None:
            params = configs[0]["parameters"]
            signals = [
                score_from_dict(s)
                for s in result.get("scores", [])
                if s.get("role") == "threshold_input"
            ]
            if len(signals) != 1:
                raise ValueError("Successful threshold observation needs one score")
            signal = signals[0]
            if (signal.kind.value, signal.threshold, signal.threshold_direction) != (
                params.get("score_type"),
                params.get("threshold"),
                params.get("direction", "at_least"),
            ):
                raise ValueError("Observed threshold provenance disagrees with policy")
            expected = params.get("missing_score_decision", "ABSTAIN")
            if signal.value is not None:
                passed = (
                    signal.value >= signal.threshold
                    if signal.threshold_direction == "at_least"
                    else signal.value <= signal.threshold
                )
                expected = "ANSWER" if passed else "ABSTAIN"
            if decision.value != expected:
                raise ValueError("Observed decision disagrees with native comparator")
        loss = None
        if lexical_proxy and decision is Decision.ANSWER:
            if (
                not isinstance(result.get("answer"), str)
                or not result["answer"].strip()
            ):
                raise ValueError("Answer observation has no answer text")
            loss = int(
                not gold["is_answerable"]
                or not _exact_match(result["answer"], gold["expected_answer"])
            )
        if (result["execution_status"] == "succeeded") == (
            row.get("error") is not None
        ):
            raise ValueError("Recorded error conflicts with execution status")
        observations.append(
            Observation(
                question_id=row["question_id"],
                run_id=row["run_id"],
                status=ExecutionStatus(result["execution_status"]),
                decision=decision,
                error_kind=(row.get("error") or {}).get("kind"),
                loss=loss,
                gold_sha256=fingerprint(gold),
                output_sha256=fingerprint(
                    {
                        k: result.get(k)
                        for k in (
                            "answer",
                            "citations",
                            "clarification_question",
                            "abstention_reason",
                        )
                    }
                ),
                evidence_sha256=fingerprint(
                    (result.get("retrieval") or {}).get("evidence")
                ),
                scores=tuple(canonical(s) for s in result.get("scores", [])),
            )
        )
    return Cohort(
        split=data["benchmark_split"],
        policy_name=policy_name,
        expected_ids=tuple(data["selected_question_ids"]),
        observations=tuple(observations),
        source_record_sha256=fingerprint(data),
        source_experiment_id=data["experiment_id"],
        provenance_json=canonical(
            dict(
                dataset=data["dataset_fingerprint"],
                retrieval=data["retrieval_configuration"],
                generation=data["generation_configuration"],
                policy=configs[0],
                seed=data["random_seed"],
                software=data["software_metadata"],
            )
        ),
        loss_basis="synthetic_lexical_proxy" if lexical_proxy else "unknown",
    )


def from_p4_job(job: dict, policy_name: str, *, lexical_proxy: bool = False) -> Cohort:
    """Validate the saved public P4 envelope, including duplicated snapshots."""
    from app.api.experiment_models import JobResults

    JobResults.model_validate(job)
    data = json.loads(canonical(job))
    record = data["result"]
    if record is None:
        raise ValueError(
            "No completed result snapshot; cannot infer missing observations"
        )
    config = data["configuration"]
    if (
        config.get("profile") != "p4-synthetic.v1"
        or config.get("split") != record["benchmark_split"]
        or config.get("question_ids") != record["selected_question_ids"]
        or config.get("retrieval") != record["retrieval_configuration"]
        or config.get("random_seed") != record["random_seed"]
        or data["id"] != record["experiment_id"]
        or data["dataset_fingerprint"] != record["dataset_fingerprint"]
        or data["runtime_source_sha256"]
        != record["generation_configuration"].get("source_sha256")
        or data["observations"] != record["runs"]
        or data["observed_run_count"] != len(record["runs"])
        or data["expected_run_count"]
        != len(record["selected_question_ids"]) * len(record["policy_configurations"])
    ):
        raise ValueError("P4 envelope and saved record provenance disagree")
    configured = config.get("policies", [])
    actual = record["policy_configurations"]
    if len(configured) != len(actual) or any(
        p["name"] != a["name"]
        or any(
            a["parameters"].get(k) != v
            for k, v in p.items()
            if k != "name" and v is not None
        )
        for p, a in zip(configured, actual, strict=True)
    ):
        raise ValueError("P4 policy snapshots disagree")
    return from_experiment(record, policy_name, lexical_proxy=lexical_proxy)


class Fraction(AnalysisModel):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    value: float | None = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_fraction(self):
        expected = self.numerator / self.denominator if self.denominator else None
        if self.numerator > self.denominator or self.value != expected:
            raise ValueError("Fraction must preserve its numerator and denominator")
        return self


def fraction(numerator: int, denominator: int) -> Fraction:
    return Fraction(
        numerator=numerator,
        denominator=denominator,
        value=numerator / denominator if denominator else None,
    )


class OperatingPoint(AnalysisModel):
    schema_version: Literal["ragbench.risk-coverage.v1"] = SCHEMA_VERSION
    cohort: Cohort
    answers: tuple[str, ...]
    abstentions: tuple[str, ...]
    clarifications: tuple[str, ...]
    failures: tuple[str, ...]
    missing: tuple[str, ...]
    end_to_end_coverage: Fraction
    successful_execution_coverage: Fraction
    failure_rate: Fraction
    missing_rate: Fraction
    judgment_completeness: Fraction
    selective_risk: float | None
    risk_bounds: tuple[float, float] | None
    undefined_reason: str | None


def operating_point(cohort: Cohort) -> OperatingPoint:
    """Fixed N is selected IDs, never observed runs or pooled policy replicates."""
    groups = {
        d: tuple(o.question_id for o in cohort.observations if o.decision is d)
        for d in Decision
    }
    answers = groups[Decision.ANSWER]
    failures = tuple(
        o.question_id
        for o in cohort.observations
        if o.status is not ExecutionStatus.SUCCEEDED
    )
    seen = {o.question_id for o in cohort.observations}
    missing = tuple(q for q in cohort.expected_ids if q not in seen)
    losses = [o.loss for o in cohort.observations if o.decision is Decision.ANSWER]
    known = [loss for loss in losses if loss is not None]
    n, a = len(cohort.expected_ids), len(answers)
    complete = a > 0 and len(known) == a
    errors = sum(known)
    return OperatingPoint(
        cohort=cohort,
        answers=answers,
        abstentions=groups[Decision.ABSTAIN],
        clarifications=groups[Decision.CLARIFY],
        failures=failures,
        missing=missing,
        end_to_end_coverage=fraction(a, n),
        successful_execution_coverage=fraction(
            a, len(cohort.observations) - len(failures)
        ),
        failure_rate=fraction(len(failures), n),
        missing_rate=fraction(len(missing), n),
        judgment_completeness=fraction(len(known), a),
        selective_risk=errors / a if complete else None,
        risk_bounds=(errors / a, (errors + a - len(known)) / a) if a else None,
        undefined_reason=None
        if complete
        else ("zero_answers" if not a else "unknown_answer_judgments"),
    )


class Area(AnalysisModel):
    schema_version: Literal["ragbench.risk-coverage.v1"] = SCHEMA_VERSION
    axis: Literal["end_to_end_coverage"] = "end_to_end_coverage"
    rule: Literal["right_step"] = "right_step"
    full_aurc: float | None = None
    partial_aurc: float | None = None
    coverage_bounds: tuple[float, float] | None = None
    undefined_reason: str | None = None


def right_step_area(points: tuple[OperatingPoint, ...], *, exhaustive: bool) -> Area:
    """Ordered, genuine sweep points only; caller must certify score boundaries."""
    if not points:
        return Area(undefined_reason="no_points")
    first = points[0].cohort
    base = json.loads(first.provenance_json)
    base["policy"]["parameters"].pop("threshold", None)
    previous: OperatingPoint | None = None
    area = 0.0
    for point in points:
        cohort = point.cohort
        if point != operating_point(cohort):
            raise ValueError("Operating-point fields disagree with observations")
        provenance = json.loads(cohort.provenance_json)
        provenance["policy"]["parameters"].pop("threshold", None)
        if (cohort.expected_ids, cohort.split, cohort.loss_basis) != (
            first.expected_ids,
            first.split,
            first.loss_basis,
        ) or provenance != base:
            raise ValueError("Incompatible sweep cohort or provenance")
        if cohort.policy_name != "threshold":
            raise ValueError("AURC requires genuine threshold-policy trials")
        if point.missing:
            return Area(undefined_reason="missing_observations")
        if point.answers and point.selective_risk is None:
            return Area(undefined_reason="unknown_answer_judgments")
        if previous:
            old = {o.question_id: o for o in previous.cohort.observations}
            for row in cohort.observations:
                before = old[row.question_id]
                if (row.gold_sha256, row.evidence_sha256) != (
                    before.gold_sha256,
                    before.evidence_sha256,
                ):
                    raise ValueError("Evidence or gold changed during sweep")
                if row.question_id in set(previous.answers) & set(point.answers) and (
                    row.loss,
                    row.output_sha256,
                ) != (before.loss, before.output_sha256):
                    raise ValueError("Answer/loss changed during sweep")
            if not set(previous.answers) <= set(point.answers):
                raise ValueError("Non-nested answered sets")
            if previous.failures != point.failures:
                return Area(undefined_reason="threshold_dependent_execution_failures")
            left = previous.end_to_end_coverage.value
            right = point.end_to_end_coverage.value
            if left is not None and right is not None and right > left:
                area += (right - left) * point.selective_risk
        previous = point
    low = points[0].end_to_end_coverage.value
    high = points[-1].end_to_end_coverage.value
    if low is None or high is None or high == 0 or high == low:
        return Area(
            coverage_bounds=(low, high)
            if low is not None and high is not None
            else None,
            undefined_reason="no_positive_coverage_interval",
        )
    bounds = (low, high)
    if not exhaustive:
        return Area(
            coverage_bounds=bounds, undefined_reason="incomplete_threshold_grid"
        )
    if not math.isfinite(area):
        raise ValueError("Nonfinite area")
    return Area(
        coverage_bounds=bounds,
        full_aurc=area if bounds == (0, 1) else None,
        partial_aurc=area if bounds != (0, 1) else None,
    )
