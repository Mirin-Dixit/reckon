"""Genuine native-policy synthetic sweeps, not post-hoc answered rankings."""

import json
import math
import socket

import pytest
from app.api.experiment_models import ExperimentRequest
from app.evaluation.threshold_sweep import (
    ThresholdSweep,
    run_synthetic_sweep,
    threshold_grid,
)


def request(method="bm25", direction="at_least", missing="ABSTAIN", split="dev"):
    return ExperimentRequest.model_validate(
        dict(
            split=split,
            retrieval=dict(method=method, top_k=3),
            policies=[
                dict(
                    name="threshold",
                    threshold=0.0,
                    direction=direction,
                    score_type={
                        "bm25": "bm25",
                        "dense": "dense_cosine",
                        "hybrid": "hybrid_rrf",
                    }[method],
                    missing_score_decision=missing,
                )
            ],
        )
    )


@pytest.mark.parametrize("direction", ["at_least", "at_most"])
def test_ties_inclusive_boundaries(direction):
    grid = threshold_grid((0.9, 0.8, 0.8, 0.1), direction)
    if direction == "at_least":
        assert grid == (math.nextafter(0.9, math.inf), 0.9, 0.8, 0.1)
    else:
        assert grid == (math.nextafter(0.1, -math.inf), 0.1, 0.8, 0.9)


@pytest.mark.parametrize("scores", [(float("nan"),), (float("inf"),), (True,)])
def test_nonfinite_scores(scores):
    with pytest.raises(ValueError):
        threshold_grid(scores, "at_least")


@pytest.mark.parametrize("method", ["bm25", "dense", "hybrid"])
@pytest.mark.parametrize("direction", ["at_least", "at_most"])
def test_real_synthetic_sweep_all_questions_each_threshold(
    monkeypatch, method, direction
):
    def forbidden(*args, **kwargs):
        raise AssertionError("No external calls or SQLite access allowed")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    import sqlite3

    monkeypatch.setattr(sqlite3, "connect", forbidden)
    from app.evaluation import threshold_sweep as module

    native = module.pipeline_factory
    calls = []

    def factory(policy, documents, retrieval, generation, seed):
        pipeline = native(policy, documents, retrieval, generation, seed)
        original = pipeline.run

        def run(question):
            assert isinstance(question, str)  # gold objects never enter runtime
            calls.append(question)
            return original(question)

        pipeline.run = run
        return pipeline

    monkeypatch.setattr(module, "pipeline_factory", factory)
    result = run_synthetic_sweep(request(method, direction))
    assert result.exhaustive
    assert result.discovery_executions == 4
    assert result.trial_executions == 4 * len(result.thresholds)
    assert len(calls) == result.discovery_executions + result.trial_executions
    assert all(len(p.cohort.observations) == 4 for p in result.points)
    assert result.points[0].end_to_end_coverage.value == 0
    assert result.points[-1].end_to_end_coverage.value == 1
    assert result.area.full_aurc is not None
    assert ThresholdSweep.model_validate_json(result.model_dump_json()) == result
    again = run_synthetic_sweep(request(method, direction))
    assert again.thresholds == result.thresholds
    assert again.area == result.area
    assert [p.selective_risk for p in again.points] == [
        p.selective_risk for p in result.points
    ]
    for point, threshold in zip(result.points, result.thresholds, strict=True):
        for row in point.cohort.observations:
            score = next(
                json.loads(s)
                for s in row.scores
                if json.loads(s)["role"] == "threshold_input"
            )
            assert score["threshold"] == threshold
            assert score["threshold_direction"] == direction
            passed = (
                score["value"] >= threshold
                if direction == "at_least"
                else score["value"] <= threshold
            )
            assert row.decision.value == ("ANSWER" if passed else "ABSTAIN")


def test_recorded_failure_limits_attainable_coverage():
    result = run_synthetic_sweep(request(split="train"))
    assert all(len(p.failures) == 1 for p in result.points)
    assert result.points[-1].end_to_end_coverage.value == 0.75
    assert result.points[-1].successful_execution_coverage.value == 1
    assert result.area.full_aurc is None
    assert result.area.partial_aurc is not None
    assert result.area.coverage_bounds == (0.0, 0.75)


def test_sparse_explicit_grid_not_full_aurc():
    result = run_synthetic_sweep(request(), thresholds=(100.0, 0.0))
    assert not result.exhaustive
    assert result.area.full_aurc is result.area.partial_aurc is None


@pytest.mark.parametrize(
    "thresholds",
    [(), (0.0, 0.0), (float("nan"),), (True,), tuple(float(i) for i in range(129))],
)
def test_invalid_grid_rejected_before_execution(thresholds):
    with pytest.raises(ValueError, match="grid"):
        run_synthetic_sweep(request(), thresholds=thresholds)


def test_no_fail_fast_or_other_policy():
    req = request().model_dump()
    req["fail_fast"] = True
    with pytest.raises(ValueError, match="whole fixed"):
        run_synthetic_sweep(ExperimentRequest.model_validate(req))
    req["fail_fast"] = False
    req["policies"] = [dict(name="always_answer")]
    with pytest.raises(ValueError, match="exactly one"):
        run_synthetic_sweep(ExperimentRequest.model_validate(req))


@pytest.mark.parametrize("missing", ["ANSWER", "ABSTAIN"])
def test_missing_scores_preserve_native_configured_action(monkeypatch, missing):
    from types import SimpleNamespace

    from app.evaluation.synthetic_runtime import FixtureRetriever

    original = FixtureRetriever.search

    def unscored(self, query, top_k=5):
        return [
            SimpleNamespace(chunk=s.chunk, score=None)
            for s in original(self, query, top_k)
        ]

    monkeypatch.setattr(FixtureRetriever, "search", unscored)
    result = run_synthetic_sweep(request(missing=missing))
    assert result.exhaustive
    assert len(result.points) == 1  # only one attainable operating point
    point = result.points[0]
    assert all(o.decision.value == missing for o in point.cohort.observations)
    for row in point.cohort.observations:
        score = json.loads(row.scores[0])
        assert score["value"] is None
        assert score["availability"] == "unavailable"
    assert result.area.full_aurc is result.area.partial_aurc is None
    assert result.area.undefined_reason == "no_positive_coverage_interval"


def test_threshold_dependent_generation_failure_does_not_become_abstention(monkeypatch):
    from app.evaluation.synthetic_runtime import FixtureGenerator

    def fail(self, question, evidence):
        raise RuntimeError("Synthetic generator failed")

    monkeypatch.setattr(FixtureGenerator, "generate", fail)
    result = run_synthetic_sweep(request())
    assert result.points[0].failures == ()
    assert len(result.points[-1].failures) == 4
    assert result.points[-1].answers == ()
    assert result.points[-1].abstentions == ()
    assert result.area.undefined_reason == "threshold_dependent_execution_failures"
