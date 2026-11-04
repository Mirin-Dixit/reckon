"""Question-paired, synthetic-only analysis of saved observations, without inference."""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Literal

from app.evaluation.risk_coverage import (
    AnalysisModel,
    Area,
    Cohort,
    Fraction,
    Observation,
    canonical,
    fingerprint,
    operating_point,
    right_step_area,
)
from app.generation.contracts import Decision, ExecutionStatus

Metric = Literal[
    "end_to_end_coverage",
    "successful_execution_coverage",
    "selective_risk",
    "failure_rate",
]
METRICS: tuple[Metric, ...] = (
    "end_to_end_coverage",
    "successful_execution_coverage",
    "selective_risk",
    "failure_rate",
)


class Interval(AnalysisModel):
    estimate: float | None
    lower: float | None
    upper: float | None
    valid_replicates: int
    undefined_replicates: int
    degenerate: bool
    unavailable_reason: str | None


class PointSummary(AnalysisModel):
    id: str
    policy: Literal["always_answer", "threshold", "prompt_abstention"]
    experiment_id: str
    source_record_sha256: str
    threshold: float | None
    direction: Literal["at_least", "at_most"] | None
    end_to_end_coverage: Fraction
    successful_execution_coverage: Fraction
    failure_rate: Fraction
    missing_rate: Fraction
    judgment_completeness: Fraction
    selective_risk: float | None
    risk_bounds: tuple[float, float] | None
    undefined_reason: str | None
    uncertainty: dict[Metric, Interval]


class PointComparison(AnalysisModel):
    left: str
    right: str
    difference: Literal["left_minus_right"] = "left_minus_right"
    uncertainty: dict[Metric, Interval]
    risk_unavailable_reason: str | None


class CurvePoint(AnalysisModel):
    row_id: str
    coverage: float
    risk: float | None


class CurveSummary(AnalysisModel):
    id: str
    points: tuple[CurvePoint, ...]
    area: Area
    uncertainty: Interval


class CurveComparison(AnalysisModel):
    left: str
    right: str
    difference: Literal["left_minus_right"] = "left_minus_right"
    uncertainty: Interval


class AnalysisReport(AnalysisModel):
    schema_version: Literal["ragbench.matched-analysis.v1"] = (
        "ragbench.matched-analysis.v1"
    )
    empirical_evaluation: Literal[False] = False
    notice: Literal[
        "Synthetic development only; lexical proxy is not semantic correctness."
    ] = "Synthetic development only; lexical proxy is not semantic correctness."
    split: Literal["train", "dev"]
    retrieval_method: Literal["bm25", "dense", "hybrid"]
    provenance_sha256: str
    question_ids: tuple[str, ...]
    matched_questions: int
    resampling_units: int
    cluster_sizes: tuple[int, ...]
    grouping: Literal["question", "declared_question_family"]
    family_map_sha256: str | None
    seed: int
    resamples: int
    interval_method: Literal["paired_percentile_95"] = "paired_percentile_95"
    loss_basis: Literal["unknown", "synthetic_lexical_proxy"]
    rows: tuple[PointSummary, ...]
    comparisons: tuple[PointComparison, ...]
    curves: tuple[CurveSummary, ...]
    curve_comparisons: tuple[CurveComparison, ...]
    limitations: tuple[str, ...]


def _base(cohort: Cohort) -> dict:
    provenance = json.loads(cohort.provenance_json)
    provenance.pop("policy")
    return provenance


def validate_matched(cohorts: Sequence[Cohort]) -> tuple[Cohort, ...]:
    """Align by question ID; never intersect silently or pool policy replicates."""
    if not 1 <= len(cohorts) <= 24:
        raise ValueError("Analysis accepts 1..24 policy configurations")
    first = cohorts[0]
    ids = tuple(sorted(first.expected_ids))
    if not 1 <= len(ids) <= 10:
        raise ValueError("Analysis requires 1..10 matched synthetic questions")
    signatures = set()
    sources = {}
    run_ids = set()
    result = []
    reference = {r.question_id: r for r in first.observations}
    for cohort in cohorts:
        # Revalidate inputs rather than trusting model_copy/model_construct.
        cohort = Cohort.model_validate(cohort.model_dump())
        point = operating_point(cohort)
        current_runs = {row.run_id for row in cohort.observations}
        if run_ids & current_runs:
            raise ValueError("Duplicate run identities across policy cohorts")
        run_ids.update(current_runs)
        if (
            cohort.source_experiment_id in sources
            and sources[cohort.source_experiment_id] != cohort.source_record_sha256
        ):
            raise ValueError("Conflicting snapshots for the same experiment")
        sources[cohort.source_experiment_id] = cohort.source_record_sha256
        if point.missing or set(cohort.expected_ids) != set(ids):
            raise ValueError("Incomplete or unmatched question cohort")
        if (cohort.split, cohort.loss_basis, _base(cohort)) != (
            first.split,
            first.loss_basis,
            _base(first),
        ):
            raise ValueError("Incompatible experiment provenance")
        policy = json.loads(cohort.provenance_json)["policy"]
        signature = canonical(policy)
        if signature in signatures:
            raise ValueError(
                "Duplicate policy configuration; repeated runs are not samples"
            )
        signatures.add(signature)
        rows = {r.question_id: r for r in cohort.observations}
        for qid in ids:
            a, b = reference[qid], rows[qid]
            if (a.gold_sha256, a.evidence_sha256, _scores(a)) != (
                b.gold_sha256,
                b.evidence_sha256,
                _scores(b),
            ):
                raise ValueError(
                    "Question gold/evidence/retrieval differs across policies"
                )
        result.append(
            cohort.model_copy(
                update={
                    "expected_ids": ids,
                    "observations": tuple(rows[qid] for qid in ids),
                }
            )
        )
    return tuple(result)


def _scores(row: Observation) -> str:
    return canonical(
        sorted(
            [
                {k: s[k] for k in ("kind", "value", "parameters", "availability")}
                for raw in row.scores
                if (s := json.loads(raw))["source"] == "retrieval"
            ],
            key=lambda s: s["kind"],
        )
    )


def _metrics(rows: tuple[Observation, ...], weights: tuple[int, ...]) -> dict:
    n = sum(weights)
    a = sum(
        w
        for row, w in zip(rows, weights, strict=True)
        if row.decision is Decision.ANSWER
    )
    e = sum(
        w
        for row, w in zip(rows, weights, strict=True)
        if row.status is not ExecutionStatus.SUCCEEDED
    )
    known = sum(
        w
        for row, w in zip(rows, weights, strict=True)
        if row.decision is Decision.ANSWER and row.loss is not None
    )
    errors = sum(
        w * row.loss
        for row, w in zip(rows, weights, strict=True)
        if row.decision is Decision.ANSWER and row.loss is not None
    )
    return dict(
        end_to_end_coverage=a / n,
        successful_execution_coverage=a / (n - e) if n > e else None,
        selective_risk=errors / a if a and known == a else None,
        failure_rate=e / n,
    )


def _quantile(values: list[float], q: float) -> float:
    position = (len(values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def _interval(estimate, samples, units, reason=None) -> Interval:
    valid = sorted(v for v in samples if v is not None)
    undefined = len(samples) - len(valid)
    degenerate = bool(valid) and len(set(valid)) == 1
    unavailable = (reason if estimate is None else None) or (
        "undefined_estimate"
        if estimate is None
        else "insufficient_resampling_units"
        if units < 2
        else "undefined_replicates"
        if undefined
        else None
    )
    return Interval(
        estimate=estimate,
        lower=_quantile(valid, 0.025) if unavailable is None else None,
        upper=_quantile(valid, 0.975) if unavailable is None else None,
        valid_replicates=len(valid),
        undefined_replicates=undefined,
        degenerate=degenerate,
        unavailable_reason=unavailable,
    )


def _difference(a, b):
    return a - b if a is not None and b is not None else None


def _curve_area(points, weights, area):
    if area.undefined_reason is not None:
        return None, None
    metrics = [_metrics(p.cohort.observations, weights) for p in points]
    if any(m["end_to_end_coverage"] and m["selective_risk"] is None for m in metrics):
        return None, None
    low, high = metrics[0]["end_to_end_coverage"], metrics[-1]["end_to_end_coverage"]
    if high <= low:
        return None, (low, high)
    value = sum(
        (b["end_to_end_coverage"] - a["end_to_end_coverage"]) * b["selective_risk"]
        for a, b in zip(metrics, metrics[1:])
        if b["end_to_end_coverage"] > a["end_to_end_coverage"]
    )
    return value, (low, high)


def _curves(cohorts):
    groups = defaultdict(list)
    for index, cohort in enumerate(cohorts):
        if cohort.policy_name != "threshold":
            continue
        config = json.loads(cohort.provenance_json)["policy"]
        config["parameters"].pop("threshold")
        groups[canonical(config)].append(index)
    curves = []
    for key, indexes in sorted(groups.items()):
        direction = json.loads(key)["parameters"].get("direction", "at_least")
        indexes.sort(
            key=lambda i: json.loads(cohorts[i].provenance_json)["policy"][
                "parameters"
            ]["threshold"],
            reverse=direction == "at_least",
        )
        points = tuple(operating_point(cohorts[i]) for i in indexes)
        scores = [
            json.loads(s)["value"]
            for row in cohorts[indexes[0]].observations
            for s in row.scores
            if json.loads(s)["source"] == "retrieval"
            and json.loads(s)["value"] is not None
        ]

        def signatures(thresholds):
            return {
                tuple(s >= t if direction == "at_least" else s <= t for s in scores)
                for t in thresholds
            }

        thresholds = [
            json.loads(cohorts[i].provenance_json)["policy"]["parameters"]["threshold"]
            for i in indexes
        ]
        from app.evaluation.threshold_sweep import threshold_grid

        exhaustive = signatures(thresholds) >= signatures(
            threshold_grid(tuple(scores), direction)
        )
        area = right_step_area(points, exhaustive=exhaustive)
        curves.append((fingerprint(json.loads(key))[:16], indexes, points, area))
    return curves


def analyze_matched(
    cohorts: Sequence[Cohort],
    *,
    resamples: int = 2000,
    seed: int = 0,
    families: Mapping[str, str] | None = None,
) -> AnalysisReport:
    """Paired question/whole-family percentile bootstrap, never observation bootstrap.

    Family declarations must cover the entire cohort and come from trusted analysis
    metadata, not labels inferred by this function. No family labels exist in P4.
    """
    if type(resamples) is not int or not 2 <= resamples <= 5000:
        raise ValueError("Resamples must be an integer in 2..5000")
    if type(seed) is not int or not -(2**31) <= seed < 2**31:
        raise ValueError("Seed must be a signed 32-bit integer")
    cohorts = validate_matched(cohorts)
    ids = cohorts[0].expected_ids
    if families is not None and (
        set(families) != set(ids)
        or any(not isinstance(v, str) or not v.strip() for v in families.values())
    ):
        raise ValueError(
            "Family declarations must cover every matched question exactly"
        )
    units = defaultdict(list)
    for i, qid in enumerate(ids):
        units[families[qid] if families is not None else qid].append(i)
    groups = [units[k] for k in sorted(units)]
    rng = random.Random(seed)
    draws = []
    for _ in range(resamples):
        counts = Counter(i for _ in groups for i in groups[rng.randrange(len(groups))])
        draws.append(tuple(counts[i] for i in range(len(ids))))
    base_weights = (1,) * len(ids)
    estimates = [_metrics(c.observations, base_weights) for c in cohorts]
    samples = [[_metrics(c.observations, w) for w in draws] for c in cohorts]
    row_ids = [f"{c.source_experiment_id}:{c.policy_name}" for c in cohorts]
    points = [operating_point(c) for c in cohorts]
    summaries = []
    for i, (cohort, point) in enumerate(zip(cohorts, points, strict=True)):
        params = json.loads(cohort.provenance_json)["policy"]["parameters"]
        summaries.append(
            PointSummary(
                id=row_ids[i],
                policy=cohort.policy_name,
                experiment_id=cohort.source_experiment_id,
                source_record_sha256=cohort.source_record_sha256,
                threshold=params.get("threshold"),
                direction=params.get("direction")
                if cohort.policy_name == "threshold"
                else None,
                **{
                    k: getattr(point, k)
                    for k in (
                        "end_to_end_coverage",
                        "successful_execution_coverage",
                        "failure_rate",
                        "missing_rate",
                        "judgment_completeness",
                        "selective_risk",
                        "risk_bounds",
                        "undefined_reason",
                    )
                },
                uncertainty={
                    m: _interval(
                        estimates[i][m], [s[m] for s in samples[i]], len(groups)
                    )
                    for m in METRICS
                },
            )
        )
    comparisons = []
    for a, b in itertools.combinations(range(len(cohorts)), 2):
        compatible_risk = (
            estimates[a]["end_to_end_coverage"] == estimates[b]["end_to_end_coverage"]
        )
        intervals = {}
        for metric in METRICS:
            estimate = _difference(estimates[a][metric], estimates[b][metric])
            values = [
                _difference(x[metric], y[metric])
                if metric != "selective_risk"
                or x["end_to_end_coverage"] == y["end_to_end_coverage"]
                else None
                for x, y in zip(samples[a], samples[b], strict=True)
            ]
            if metric == "selective_risk" and not compatible_risk:
                estimate, values = None, [None] * resamples
            intervals[metric] = _interval(
                estimate,
                values,
                len(groups),
                "coverage_domains_differ"
                if metric == "selective_risk" and not compatible_risk
                else None,
            )
        comparisons.append(
            PointComparison(
                left=row_ids[a],
                right=row_ids[b],
                uncertainty=intervals,
                risk_unavailable_reason=(
                    "coverage_domains_differ"
                    if not compatible_risk
                    else "undefined_risk"
                    if estimates[a]["selective_risk"] is None
                    or estimates[b]["selective_risk"] is None
                    else None
                ),
            )
        )
    curves = _curves(cohorts)
    curve_results, curve_samples = [], []
    for curve_id, indexes, trial_points, area in curves:
        values = [_curve_area(trial_points, w, area) for w in draws]
        curve_samples.append(values)
        estimate = area.full_aurc if area.full_aurc is not None else area.partial_aurc
        # Do not combine areas on varying bootstrap coverage domains.
        same_domain = [
            v if domain == area.coverage_bounds else None for v, domain in values
        ]
        curve_results.append(
            CurveSummary(
                id=curve_id,
                points=tuple(
                    CurvePoint(
                        row_id=row_ids[i],
                        coverage=p.end_to_end_coverage.value,
                        risk=p.selective_risk,
                    )
                    for i, p in zip(indexes, trial_points, strict=True)
                ),
                area=area,
                uncertainty=_interval(
                    estimate, same_domain, len(groups), area.undefined_reason
                ),
            )
        )
    curve_comparisons = []
    for a, b in itertools.combinations(range(len(curves)), 2):
        x, y = curve_results[a], curve_results[b]
        same = x.area.coverage_bounds == y.area.coverage_bounds
        estimate = (
            _difference(x.uncertainty.estimate, y.uncertainty.estimate)
            if same
            else None
        )
        values = [
            _difference(u, v) if ud == vd == x.area.coverage_bounds and same else None
            for (u, ud), (v, vd) in zip(curve_samples[a], curve_samples[b], strict=True)
        ]
        curve_comparisons.append(
            CurveComparison(
                left=x.id,
                right=y.id,
                uncertainty=_interval(
                    estimate,
                    values,
                    len(groups),
                    "coverage_domains_differ" if not same else None,
                ),
            )
        )
    return AnalysisReport(
        split=cohorts[0].split,
        retrieval_method=_base(cohorts[0])["retrieval"]["method"],
        provenance_sha256=fingerprint(_base(cohorts[0])),
        question_ids=ids,
        matched_questions=len(ids),
        resampling_units=len(groups),
        cluster_sizes=tuple(map(len, groups)),
        grouping="declared_question_family" if families is not None else "question",
        family_map_sha256=fingerprint(dict(families)) if families is not None else None,
        seed=seed,
        resamples=resamples,
        loss_basis=cohorts[0].loss_basis,
        rows=tuple(summaries),
        comparisons=tuple(comparisons),
        curves=tuple(curve_results),
        curve_comparisons=tuple(curve_comparisons),
        limitations=(
            "Synthetic development only; no semantic correctness or generalization "
            "claim.",
            "Small samples and dependent questions limit bootstrap interpretation; "
            "no significance claim.",
            "Intervals withheld for any undefined replicate or fewer than two "
            "resampling units.",
            "Degenerate intervals do not establish certainty; repeated policy "
            "observations are paired.",
            "Risk differences require equal coverage; selected answer subsets "
            "may still differ.",
            "AURC uses saved genuine threshold trials only; no inference or "
            "threshold-scale comparison.",
            "No declared P4 question families; question independence is an assumption."
            if families is None
            else "Whole declared families are resampled jointly; "
            "cluster sizes may differ.",
        ),
    )
