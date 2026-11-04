"""R1 accounting, strict adapters, undefined states and hand-calculated area."""

import copy
import json
from pathlib import Path

import pytest
from app.evaluation.risk_coverage import (
    Cohort,
    Observation,
    canonical,
    from_experiment,
    from_p4_job,
    operating_point,
    right_step_area,
)
from app.generation.contracts import Decision, ExecutionStatus
from pydantic import ValidationError

H = "a" * 64


def cohort(decisions, losses=None, *, expected=None, threshold=0.0):
    losses = losses if losses is not None else [None] * len(decisions)
    rows = tuple(
        Observation(
            question_id=f"q{i}",
            run_id=f"run{i}",
            status=ExecutionStatus.SUCCEEDED if d else ExecutionStatus.FAILED,
            decision=Decision(d) if d else None,
            loss=losses[i],
            gold_sha256=H,
            output_sha256=H,
            evidence_sha256=H,
        )
        for i, d in enumerate(decisions)
    )
    return Cohort(
        split="dev",
        policy_name="threshold",
        expected_ids=tuple(f"q{i}" for i in range(expected or len(rows))),
        observations=rows,
        source_record_sha256=H,
        source_experiment_id="00000000-0000-0000-0000-000000000001",
        provenance_json=canonical(
            dict(
                dataset=dict(documents_sha256=H, questions_sha256=H),
                retrieval=dict(method="bm25", top_k=3),
                generation=dict(
                    provider="synthetic",
                    model="fixture-rules.v1",
                    external_calls=False,
                    source_sha256=H,
                ),
                policy=dict(
                    name="threshold",
                    parameters=dict(threshold=threshold, score_type="bm25"),
                ),
                seed=0,
                software=dict(python="3.13"),
            )
        ),
        loss_basis="synthetic_lexical_proxy",
    )


def test_both_coverage_denominators_and_missing():
    point = operating_point(
        cohort(
            ["ANSWER", "ABSTAIN", "CLARIFY", None], [1, None, None, None], expected=5
        )
    )
    assert point.end_to_end_coverage.value == 1 / 5
    assert point.successful_execution_coverage.value == 1 / 3
    assert point.failure_rate.value == point.missing_rate.value == 1 / 5
    assert point.failures == ("q3",) and point.missing == ("q4",)
    assert point.selective_risk == 1
    assert point.judgment_completeness.value == 1


@pytest.mark.parametrize("decisions", [[], ["ABSTAIN"], ["CLARIFY"], [None]])
def test_no_answers_risk_is_undefined(decisions):
    point = operating_point(cohort(decisions))
    assert point.selective_risk is None
    assert point.risk_bounds is None
    assert point.undefined_reason == "zero_answers"
    assert point.judgment_completeness.value is None
    if not decisions:
        assert point.end_to_end_coverage.value is None


def test_unknown_judgments_not_zero_loss():
    point = operating_point(cohort(["ANSWER"] * 3, [0, 1, None]))
    assert point.selective_risk is None
    assert point.risk_bounds == (1 / 3, 2 / 3)
    assert point.judgment_completeness.value == 2 / 3
    assert right_step_area((point,), exhaustive=True).undefined_reason == (
        "unknown_answer_judgments"
    )


def hand_points():
    # Native >= thresholds on .9,.8,.8,.1; losses 0,1,0,1.
    return tuple(
        operating_point(cohort(ds, ls, threshold=t))
        for t, ds, ls in [
            (1.0, ["ABSTAIN"] * 4, [None] * 4),
            (0.9, ["ANSWER", "ABSTAIN", "ABSTAIN", "ABSTAIN"], [0, None, None, None]),
            (0.8, ["ANSWER", "ANSWER", "ANSWER", "ABSTAIN"], [0, 1, 0, None]),
            (0.1, ["ANSWER"] * 4, [0, 1, 0, 1]),
        ]
    )


def test_hand_calculated_seven_over_twenty_four():
    points = hand_points()
    assert [p.end_to_end_coverage.value for p in points] == [0, 0.25, 0.75, 1]
    area = right_step_area(points, exhaustive=True)
    assert area.full_aurc == pytest.approx(7 / 24)
    assert area.partial_aurc is None
    assert area.coverage_bounds == (0.0, 1.0)
    assert points[0].selective_risk is None


def test_partial_area_not_extrapolated_or_renormalized():
    area = right_step_area(hand_points()[:3], exhaustive=True)
    assert area.full_aurc is None
    assert area.partial_aurc == pytest.approx(1 / 6)
    assert area.coverage_bounds == (0.0, 0.75)
    area = right_step_area(hand_points()[1:], exhaustive=True)
    assert area.full_aurc is None
    assert area.coverage_bounds == (0.25, 1.0)
    assert area.partial_aurc == pytest.approx(7 / 24)


def test_sparse_grid_not_called_aurc():
    area = right_step_area(hand_points()[::3], exhaustive=False)
    assert area.full_aurc is area.partial_aurc is None
    assert area.undefined_reason == "incomplete_threshold_grid"


def test_missing_runs_invalidates_area():
    point = operating_point(cohort(["ANSWER"], [0], expected=2))
    assert right_step_area((point,), exhaustive=True).undefined_reason == (
        "missing_observations"
    )


@pytest.mark.parametrize("change", ["gold_sha256", "evidence_sha256", "output_sha256"])
def test_sweep_drift_rejected(change):
    points = list(hand_points())
    row = points[-1].cohort.observations[0].model_dump()
    row[change] = "b" * 64
    data = points[-1].cohort.model_dump()
    data["observations"] = (Observation(**row), *points[-1].cohort.observations[1:])
    points[-1] = operating_point(Cohort(**data))
    with pytest.raises(ValueError, match="changed"):
        right_step_area(tuple(points), exhaustive=True)


def test_non_nested_answers_rejected():
    with pytest.raises(ValueError, match="Non-nested"):
        right_step_area(tuple(reversed(hand_points())), exhaustive=True)


def test_incompatible_provenance_rejected():
    a, b = hand_points()[:2]
    data = b.cohort.model_dump()
    prov = json.loads(data["provenance_json"])
    prov["seed"] = 1
    data["provenance_json"] = canonical(prov)
    with pytest.raises(ValueError, match="Incompatible"):
        right_step_area((a, operating_point(Cohort(**data))), exhaustive=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_ids", ("q0", "q0")),
        ("expected_ids", ("other",)),
        ("split", "test"),
        ("source_record_sha256", "not-a-hash"),
        ("schema_version", "future"),
    ],
)
def test_invalid_cohorts(field, value):
    data = cohort(["ANSWER"], [0]).model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        Cohort(**data)


def test_duplicate_and_inconsistent_observations_rejected():
    data = cohort(["ANSWER"], [0]).model_dump()
    row = data["observations"][0]
    data["observations"] = (row, row)
    with pytest.raises(ValidationError, match="Duplicate"):
        Cohort(**data)
    row["status"] = ExecutionStatus.FAILED
    with pytest.raises(ValidationError, match="failure"):
        Observation(**row)


@pytest.fixture
def job():
    return json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "frontend/tests/fixture_job_result.json"
        ).read_text()
    )


def test_real_p4_saved_response_adapter_round_trip_without_mutation(job):
    original = copy.deepcopy(job)
    selected = from_p4_job(job, "always_answer")
    assert selected.loss_basis == "unknown"
    assert operating_point(selected).selective_risk is None
    proxy = from_p4_job(job, "always_answer", lexical_proxy=True)
    assert proxy.loss_basis == "synthetic_lexical_proxy"
    assert "not semantic" in proxy.notice
    assert Cohort.model_validate_json(proxy.model_dump_json()) == proxy
    assert job == original


@pytest.mark.parametrize(
    "change",
    [
        "dataset",
        "runtime",
        "observations",
        "expected",
        "retrieval",
        "policy",
        "ids",
    ],
)
def test_p4_envelope_mismatch_rejected(job, change):
    if change == "dataset":
        job["dataset_fingerprint"]["documents_sha256"] = H
    elif change == "runtime":
        job["runtime_source_sha256"] = H
    elif change == "observations":
        job["observations"] = []
    elif change == "expected":
        job["expected_run_count"] = 4
    elif change == "retrieval":
        job["configuration"]["retrieval"]["top_k"] = 9
    elif change == "policy":
        job["configuration"]["policies"][2]["threshold"] = 9.0
    else:
        job["configuration"]["question_ids"] = ["other"]
    with pytest.raises(ValueError):
        from_p4_job(job, "always_answer")


def test_missing_result_and_policy_rejected(job):
    with pytest.raises(ValueError, match="declared policy"):
        from_p4_job(job, "absent")
    job["result"] = None
    with pytest.raises(ValueError, match="No completed"):
        from_p4_job(job, "always_answer")


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "foreign",
        "gold",
        "unknown_policy",
        "failure_decision",
        "blank_answer",
        "missing_hash",
        "remote",
        "nan",
        "observed_threshold",
    ],
)
def test_invalid_saved_records_rejected(job, change):
    record = job["result"]
    if change == "duplicate":
        record["runs"].append(copy.deepcopy(record["runs"][0]))
    elif change == "foreign":
        record["runs"][0]["question_id"] = "foreign"
    elif change == "gold":
        record["runs"][1]["gold"]["domain"] = "changed"
    elif change == "unknown_policy":
        record["runs"][0]["policy_name"] = "unknown"
    elif change == "failure_decision":
        record["runs"][0]["observed"]["execution_status"] = "failed"
    elif change == "blank_answer":
        record["runs"][0]["observed"]["answer"] = " "
    elif change == "missing_hash":
        del record["dataset_fingerprint"]["documents_sha256"]
    elif change == "remote":
        record["generation_configuration"]["provider"] = "openai"
    elif change == "nan":
        record["retrieval_configuration"]["k1"] = float("nan")
    else:
        record["runs"][2]["observed"]["scores"][0]["threshold"] = 99.0
    policy = "threshold" if change == "observed_threshold" else "always_answer"
    with pytest.raises(ValueError):
        from_experiment(record, policy)


def test_record_fingerprint_and_unknown_judgments_are_explicit(job):
    from app.evaluation.risk_coverage import fingerprint

    selected = from_p4_job(job, "always_answer")
    assert selected.source_record_sha256 == fingerprint(job["result"])
    assert selected.source_experiment_id == job["id"]
    assert all(o.loss is None for o in selected.observations)


def test_score_parameter_drift_rejected(job):
    record = job["result"]
    record["runs"][0]["observed"]["scores"][0]["parameters"]["k1"] = 2.0
    with pytest.raises(ValueError, match="parameters conflict"):
        from_experiment(record, "always_answer")


def test_area_rejects_tampered_operating_point():
    points = list(hand_points())
    data = points[-1].model_dump()
    data["selective_risk"] = 0.0
    points[-1] = type(points[-1])(**data)
    with pytest.raises(ValueError, match="disagree"):
        right_step_area(tuple(points), exhaustive=True)


@pytest.mark.parametrize("loss", [True, 0.5, float("nan"), -1, 2])
def test_loss_not_coerced(loss):
    data = cohort(["ANSWER"], [0]).observations[0].model_dump()
    data["loss"] = loss
    with pytest.raises(ValueError, match="Loss"):
        Observation(**data)
