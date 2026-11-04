"""Bounded, in-memory synthetic experiments; no P4 jobs or persistence writes."""

from __future__ import annotations

import json
import math
import sys
from typing import Literal

from app.api.experiment_models import ExperimentRequest
from app.evaluation.risk_coverage import (
    AnalysisModel,
    Area,
    OperatingPoint,
    from_experiment,
    operating_point,
    right_step_area,
)
from app.evaluation.runner import EvaluationRunner
from app.evaluation.synthetic_runtime import (
    FIXTURES,
    GENERATION,
    pipeline_factory,
    policy_configs,
    source_fingerprint,
)


class ThresholdSweep(AnalysisModel):
    schema_version: Literal["ragbench.threshold-sweep.v1"] = (
        "ragbench.threshold-sweep.v1"
    )
    notice: Literal["Synthetic development only; no empirical claims."] = (
        "Synthetic development only; no empirical claims."
    )
    thresholds: tuple[float, ...]
    exhaustive: bool
    points: tuple[OperatingPoint, ...]
    area: Area
    discovery_executions: int
    trial_executions: int


def threshold_grid(scores: tuple[float, ...], direction: str) -> tuple[float, ...]:
    """Whole tied groups, native inclusive comparator, and reject-all boundary."""
    if direction not in ("at_least", "at_most"):
        raise ValueError("Unknown threshold direction")
    if any(type(s) not in (int, float) or not math.isfinite(s) for s in scores):
        raise ValueError("Scores must be finite numbers")
    values = sorted(set(scores), reverse=direction == "at_least")
    if not values:
        return ()
    boundary = math.nextafter(
        values[0], math.inf if direction == "at_least" else -math.inf
    )
    if not math.isfinite(boundary):
        raise ValueError("No finite reject-all threshold")
    return (boundary, *map(float, values))


def run_synthetic_sweep(
    request: ExperimentRequest,
    *,
    thresholds: tuple[float, ...] | None = None,
) -> ThresholdSweep:
    """Execute all selected fixture questions at each threshold, without callbacks.

    Uses P4's server-owned fixture paths and native policy/retrieval implementations.
    Trusted arbitrary Python code is not sandboxed; this is not a plugin interface.
    """
    # Revalidate rather than trusting a model constructed without validation.
    request = ExperimentRequest.model_validate(request.model_dump())
    if len(request.policies) != 1 or request.policies[0].name != "threshold":
        raise ValueError("A sweep requires exactly one threshold policy")
    if request.fail_fast:
        raise ValueError("Sweep must execute the whole fixed population")
    if thresholds is not None and (
        not 1 <= len(thresholds) <= 128
        or len(set(thresholds)) != len(thresholds)
        or any(type(t) not in (int, float) or not math.isfinite(t) for t in thresholds)
    ):
        raise ValueError("Threshold grid must contain 1..128 distinct finite numbers")
    retrieval = request.retrieval.model_dump()
    retrieval.update(chunk_size=500, chunk_overlap=50, k1=1.5, b=0.75)
    if request.retrieval.method == "hybrid":
        retrieval.update(
            rank_lists=2,
            candidate_k=request.retrieval.candidate_k or 50,
            rrf_k=request.retrieval.rrf_k or 60,
        )
    generation = {**GENERATION, "source_sha256": source_fingerprint()}
    runner = EvaluationRunner(
        FIXTURES / "documents.jsonl", FIXTURES / "questions.jsonl"
    )
    spec = request.policies[0]

    def trial(threshold: float) -> OperatingPoint:
        config = request.model_dump()
        config["policies"][0]["threshold"] = threshold
        configured = ExperimentRequest.model_validate(config)
        record = runner.run(
            split=request.split,
            question_ids=request.question_ids,
            policies=policy_configs(configured),
            pipeline_factory=pipeline_factory,
            retrieval_configuration=retrieval,
            generation_configuration=generation,
            random_seed=request.random_seed,
        )
        return operating_point(from_experiment(record, "threshold", lexical_proxy=True))

    # Discovery retrieves every question; it is not an answered-only ranking.
    discovery_threshold = (
        sys.float_info.max if spec.direction == "at_least" else -sys.float_info.max
    )
    discovery = trial(discovery_threshold)
    values = []
    for row in discovery.cohort.observations:
        signals = [
            json.loads(s)
            for s in row.scores
            if json.loads(s)["kind"] == spec.score_type
        ]
        if len(signals) > 1:
            raise ValueError("Ambiguous threshold score")
        if signals and signals[0]["value"] is not None:
            values.append(signals[0]["value"])
    complete_grid = threshold_grid(tuple(values), spec.direction)
    chosen = (
        (complete_grid or (discovery_threshold,))
        if thresholds is None
        else tuple(map(float, thresholds))
    )
    chosen = tuple(sorted(chosen, reverse=spec.direction == "at_least"))

    def signatures(grid):
        return {
            tuple(s >= t if spec.direction == "at_least" else s <= t for s in values)
            for t in grid
        }

    exhaustive = signatures(chosen) >= signatures(complete_grid)
    points = tuple(trial(t) for t in chosen)

    # Score values, including unavailable values, must stay stable at every trial.
    def stable_scores(point):
        return {
            row.question_id: tuple(
                (s["kind"], s["value"], s["parameters"], s["availability"])
                for raw in row.scores
                if (s := json.loads(raw))["source"] == "retrieval"
            )
            for row in point.cohort.observations
        }

    for point in points:
        if stable_scores(point) != stable_scores(discovery):
            raise ValueError("Retrieval scores changed during deterministic sweep")
    return ThresholdSweep(
        thresholds=chosen,
        exhaustive=exhaustive,
        points=points,
        area=right_step_area(points, exhaustive=exhaustive),
        discovery_executions=len(discovery.cohort.expected_ids),
        trial_executions=sum(len(p.cohort.expected_ids) for p in points),
    )
