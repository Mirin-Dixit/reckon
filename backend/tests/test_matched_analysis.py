"""Numerical and matched-unit bootstrap regression tests; no model calls."""

import json
from uuid import uuid4

import pytest
from app.api.experiment_models import ExperimentRequest
from app.evaluation.matched_analysis import AnalysisReport, analyze_matched
from app.evaluation.risk_coverage import Cohort, Observation, canonical
from app.evaluation.threshold_sweep import run_synthetic_sweep
from app.generation.contracts import Decision, ExecutionStatus

H = "a" * 64


def cohort(policy="always_answer", decisions=("ANSWER", "ANSWER"), losses=(0, 1)):
    return Cohort(
        split="dev",
        policy_name=policy,
        expected_ids=tuple(f"q{i}" for i in range(len(decisions))),
        observations=tuple(
            Observation(
                question_id=f"q{i}",
                run_id=str(uuid4()),
                status=ExecutionStatus.SUCCEEDED
                if decision
                else ExecutionStatus.FAILED,
                decision=Decision(decision) if decision else None,
                loss=losses[i],
                gold_sha256=H,
                output_sha256=H,
                evidence_sha256=H,
            )
            for i, decision in enumerate(decisions)
        ),
        source_record_sha256=H,
        source_experiment_id=str(uuid4()),
        loss_basis="synthetic_lexical_proxy",
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
                policy=dict(name=policy, parameters={}),
                seed=0,
                software=dict(version="test"),
            )
        ),
    )


def test_seeded_paired_bootstrap_exact_metrics_and_zero_paired_differences():
    a, b = cohort(), cohort("prompt_abstention")
    report = analyze_matched((a, b), resamples=2000, seed=21)
    assert analyze_matched((a, b), resamples=2000, seed=21) == report
    risk = report.rows[0].uncertainty["selective_risk"]
    assert risk.estimate == 0.5 and (risk.lower, risk.upper) == (0, 1)
    assert risk.valid_replicates == 2000 and risk.undefined_replicates == 0
    delta = report.comparisons[0].uncertainty["selective_risk"]
    assert delta.estimate == delta.lower == delta.upper == 0
    assert delta.degenerate
    assert report.matched_questions == report.resampling_units == 2
    assert AnalysisReport.model_validate_json(report.model_dump_json()) == report


def test_alignment_is_by_question_id_not_observation_order():
    a, b = cohort(), cohort("prompt_abstention")
    b = b.model_copy(
        update={
            "expected_ids": tuple(reversed(b.expected_ids)),
            "observations": tuple(reversed(b.observations)),
        }
    )
    report = analyze_matched((a, b), resamples=30)
    assert report.comparisons[0].uncertainty["selective_risk"].upper == 0


def test_failures_stay_failures_and_both_denominators_retained():
    a = cohort(
        decisions=("ANSWER", "ABSTAIN", "CLARIFY", None), losses=(0, None, None, None)
    )
    point = analyze_matched((a,), resamples=50).rows[0]
    assert point.end_to_end_coverage.value == 0.25
    assert point.successful_execution_coverage.value == 1 / 3
    assert point.failure_rate.value == 0.25
    assert point.uncertainty["selective_risk"].undefined_replicates > 0
    assert point.uncertainty["selective_risk"].lower is None


def test_unknown_judgments_and_zero_answer_not_correct_answers():
    a = cohort(losses=(0, None))
    report = analyze_matched((a,), resamples=50)
    assert report.rows[0].selective_risk is None
    assert report.rows[0].risk_bounds == (0, 0.5)
    assert report.rows[0].uncertainty["selective_risk"].lower is None
    b = cohort(decisions=("ABSTAIN", "CLARIFY"), losses=(None, None))
    assert analyze_matched((b,), resamples=20).rows[0].selective_risk is None


def test_risk_comparison_withheld_at_different_coverage():
    a = cohort()
    b = cohort("prompt_abstention", ("ANSWER", "ABSTAIN"), (0, None))
    report = analyze_matched((a, b), resamples=30)
    comparison = report.comparisons[0]
    assert comparison.risk_unavailable_reason == "coverage_domains_differ"
    assert comparison.uncertainty["selective_risk"].estimate is None
    assert comparison.uncertainty["end_to_end_coverage"].estimate == 0.5


def test_whole_family_resampling_and_single_unit_disclosure():
    a = cohort(decisions=("ANSWER",) * 4, losses=(0, 0, 1, 1))
    families = dict(q0="first", q1="first", q2="second", q3="second")
    report = analyze_matched((a,), resamples=100, families=families)
    assert report.matched_questions == 4 and report.resampling_units == 2
    assert report.cluster_sizes == (2, 2)
    assert report.grouping == "declared_question_family"
    assert report.family_map_sha256
    report = analyze_matched(
        (a,), resamples=20, families=dict.fromkeys(a.expected_ids, "one")
    )
    assert report.resampling_units == 1
    assert (
        report.rows[0].uncertainty["selective_risk"].unavailable_reason
        == "insufficient_resampling_units"
    )


@pytest.mark.parametrize("families", [{}, {"q0": "one"}, {"q0": "", "q1": "x"}])
def test_invalid_families_rejected(families):
    with pytest.raises(ValueError, match="Family"):
        analyze_matched((cohort(),), families=families)


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "dataset",
        "method",
        "gold",
        "evidence",
        "seed",
        "loss_basis",
    ],
)
def test_incompatible_or_duplicate_cohorts_rejected(change):
    a, b = cohort(), cohort("prompt_abstention")
    if change == "duplicate":
        b = a
    elif change == "missing":
        b = b.model_copy(update={"observations": b.observations[:1]})
    elif change in ("dataset", "method", "seed"):
        provenance = json.loads(b.provenance_json)
        if change == "dataset":
            provenance["dataset"]["questions_sha256"] = "b" * 64
        elif change == "method":
            provenance["retrieval"]["method"] = "dense"
        else:
            provenance["seed"] = 1
        b = b.model_copy(update={"provenance_json": canonical(provenance)})
    elif change == "loss_basis":
        b = b.model_copy(
            update={
                "loss_basis": "unknown",
                "observations": tuple(
                    r.model_copy(update={"loss": None}) for r in b.observations
                ),
            }
        )
    else:
        row = b.observations[0].model_copy(update={f"{change}_sha256": "b" * 64})
        b = b.model_copy(update={"observations": (row, b.observations[1])})
    with pytest.raises(ValueError):
        analyze_matched((a, b), resamples=20)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(resamples=1),
        dict(resamples=5001),
        dict(resamples=True),
        dict(seed=True),
        dict(seed=2**31),
    ],
)
def test_bootstrap_budgets(kwargs):
    with pytest.raises(ValueError):
        analyze_matched((cohort(),), **kwargs)


def test_aurc_uses_genuine_saved_trials_and_bootstraps_joint_questions():
    request = ExperimentRequest.model_validate(
        dict(
            split="dev",
            retrieval=dict(method="bm25", top_k=3),
            policies=[dict(name="threshold", score_type="bm25", threshold=0.0)],
        )
    )
    sweep = run_synthetic_sweep(request)
    report = analyze_matched(tuple(p.cohort for p in sweep.points), resamples=50)
    assert len(report.curves) == 1
    assert report.curves[0].area == sweep.area
    assert report.curves[0].uncertainty.valid_replicates == 50
    assert report.curves[0].area.full_aurc is not None
    sparse = analyze_matched(
        (sweep.points[0].cohort, sweep.points[-1].cohort), resamples=20
    )
    assert sparse.curves[0].area.undefined_reason == "incomplete_threshold_grid"
    assert sparse.curves[0].uncertainty.estimate is None


def test_aurc_comparison_requires_compatible_native_curves_and_domains():
    trials = []
    expected = []
    for direction in ("at_least", "at_most"):
        request = ExperimentRequest.model_validate(
            dict(
                split="dev",
                retrieval=dict(method="bm25", top_k=3),
                policies=[
                    dict(
                        name="threshold",
                        score_type="bm25",
                        threshold=0.0,
                        direction=direction,
                    )
                ],
            )
        )
        sweep = run_synthetic_sweep(request)
        trials.extend(p.cohort for p in sweep.points)
        expected.append(sweep.area.full_aurc)
    report = analyze_matched(tuple(trials), resamples=50)
    assert len(report.curve_comparisons) == 1
    by_id = {curve.id: curve for curve in report.curves}
    pair = report.curve_comparisons[0]
    assert pair.uncertainty.estimate == pytest.approx(
        by_id[pair.left].area.full_aurc - by_id[pair.right].area.full_aurc
    )
    assert pair.uncertainty.undefined_replicates == 0
    assert sorted(c.area.full_aurc for c in report.curves) == sorted(expected)
    without_reject_all = tuple(
        c
        for c in trials
        if c.source_experiment_id != sweep.points[0].cohort.source_experiment_id
    )
    unmatched_domains = analyze_matched(without_reject_all, resamples=20)
    pair = unmatched_domains.curve_comparisons[0]
    assert pair.uncertainty.estimate is None
    assert pair.uncertainty.unavailable_reason == "coverage_domains_differ"


def test_partial_curve_bootstrap_withholds_varying_coverage_domains():
    request = ExperimentRequest.model_validate(
        dict(
            split="train",
            retrieval=dict(method="bm25", top_k=3),
            policies=[dict(name="threshold", score_type="bm25", threshold=0.0)],
        )
    )
    sweep = run_synthetic_sweep(request)
    report = analyze_matched(tuple(p.cohort for p in sweep.points), resamples=50)
    curve = report.curves[0]
    assert curve.area.full_aurc is None
    assert curve.area.partial_aurc is not None
    assert curve.area.coverage_bounds == (0, 0.75)
    assert curve.uncertainty.undefined_replicates > 0
    assert curve.uncertainty.lower is None


def test_conflicting_source_snapshots_and_duplicate_observations_rejected():
    a, b = cohort(), cohort("prompt_abstention")
    b = b.model_copy(
        update={
            "source_experiment_id": a.source_experiment_id,
            "source_record_sha256": "b" * 64,
        }
    )
    with pytest.raises(ValueError, match="Conflicting"):
        analyze_matched((a, b), resamples=20)
    a = a.model_copy(update={"observations": (a.observations[0],) * 2})
    with pytest.raises(ValueError, match="Duplicate"):
        analyze_matched((a,), resamples=20)


def test_same_run_identity_cannot_be_reused_as_another_policy_sample():
    a, b = cohort(), cohort("prompt_abstention")
    b = b.model_copy(
        update={
            "observations": tuple(
                row.model_copy(update={"run_id": a.observations[i].run_id})
                for i, row in enumerate(b.observations)
            )
        }
    )
    with pytest.raises(ValueError, match="Duplicate run identities"):
        analyze_matched((a, b), resamples=20)
