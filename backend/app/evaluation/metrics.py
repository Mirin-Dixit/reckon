"""Transparent lexical, decision, evidence-reference, and risk metrics."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from math import sqrt
from typing import Any

from app.evaluation.results import ExperimentRecord, ExperimentRun
from app.evaluation.serialization import to_primitive
from app.generation.contracts import Decision, ExecutionStatus, validate_citations

MIN_CI_SAMPLE_SIZE = 30


def summarize_runs(
    runs: Iterable[ExperimentRun],
    retrieval_configuration: dict[str, Any] | None = None,
    *,
    expected_question_ids: Iterable[str] | None = None,
    policy_names: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Calculate metrics and breakdowns without inventing semantic judgments."""
    rows = tuple(runs)
    report = _summarize_group(rows)
    report["breakdowns"] = {
        "split": _breakdown(rows, lambda row: row.gold.split),
        "answerability_category": _breakdown(
            rows,
            lambda row: (
                row.gold.unanswerable_category
                or ("answerable" if row.gold.is_answerable else "uncategorized")
            ),
        ),
        "domain": _breakdown(rows, lambda row: row.gold.domain),
        "policy": _breakdown(rows, lambda row: row.policy_name),
        "retrieval_method": _breakdown(
            rows,
            lambda row: (
                row.observed.retrieval.method
                if row.observed.retrieval is not None
                else "unavailable"
            ),
        ),
        "retrieval_configuration": (
            {
                json.dumps(retrieval_configuration, sort_keys=True): _summarize_group(
                    rows
                )
            }
            if retrieval_configuration is not None
            else {}
        ),
    }
    report["answered_run_ranking"] = _answered_run_ranking(rows)
    report["run_accounting"] = _run_accounting(
        rows, expected_question_ids, policy_names
    )
    report["partial"] = any(
        not item["complete"] for item in report["run_accounting"].values()
    )
    if report["partial"]:
        report["warnings"].append(
            "Metrics are partial: at least one policy has missing or duplicate runs."
        )
    return report


def _run_accounting(rows, expected_question_ids, policy_names):
    expected = None if expected_question_ids is None else tuple(expected_question_ids)
    names = tuple(policy_names or dict.fromkeys(row.policy_name for row in rows))
    result = {}
    for name in names:
        selected = [row for row in rows if row.policy_name == name]
        ids = [row.question_id for row in selected]
        duplicates = sorted(qid for qid, count in Counter(ids).items() if count > 1)
        missing = sorted(set(expected or ()) - set(ids)) if expected is not None else []
        expected_count = len(expected) if expected is not None else len(set(ids))
        result[name] = {
            "expected_runs": expected_count,
            "observed_runs": len(selected),
            "successful_runs": sum(
                row.observed.execution_status is ExecutionStatus.SUCCEEDED
                for row in selected
            ),
            "execution_failures": sum(
                row.observed.execution_status is not ExecutionStatus.SUCCEEDED
                for row in selected
            ),
            "missing_runs": len(missing),
            "missing_question_ids": missing,
            "duplicate_runs": sum(ids.count(qid) - 1 for qid in duplicates),
            "duplicate_question_ids": duplicates,
            "complete": not missing
            and not duplicates
            and len(selected) == expected_count,
        }
    return result


def _summarize_group(rows: tuple[ExperimentRun, ...]) -> dict[str, Any]:
    total = len(rows)
    successful = tuple(
        row
        for row in rows
        if row.observed.execution_status is ExecutionStatus.SUCCEEDED
    )
    answers = tuple(
        row for row in successful if row.observed.decision is Decision.ANSWER
    )
    abstentions = tuple(
        row for row in successful if row.observed.decision is Decision.ABSTAIN
    )
    clarifications = tuple(
        row for row in successful if row.observed.decision is Decision.CLARIFY
    )
    unanswerable = tuple(row for row in rows if not row.gold.is_answerable)
    answerable = tuple(row for row in rows if row.gold.is_answerable)
    true_abstentions = tuple(row for row in abstentions if not row.gold.is_answerable)
    false_abstentions = tuple(row for row in abstentions if row.gold.is_answerable)
    false_answers = tuple(row for row in answers if not row.gold.is_answerable)

    em_rows = tuple(
        (row, _exact_match(row.observed.answer, row.gold.expected_answer))
        for row in answers
        if row.gold.expected_answer is not None and row.observed.answer is not None
    )
    token_f1_rows = tuple(
        _token_f1(row.observed.answer or "", row.gold.expected_answer or "")
        for row in answers
        if row.gold.expected_answer is not None and row.observed.answer is not None
    )
    missing_answer_bodies = sum(
        not (row.observed.answer and row.observed.answer.strip()) for row in answers
    )
    lexical_errors = sum(
        (not row.gold.is_answerable)
        or not (row.observed.answer and row.observed.answer.strip())
        or not _exact_match(row.observed.answer, row.gold.expected_answer)
        for row in answers
    )
    selective_denominator = len(answers)

    decisions = Counter(
        row.observed.decision.value
        for row in successful
        if row.observed.decision is not None
    )
    errors = total - len(successful)
    expected_decision_rows = [
        (row, expected)
        for row in rows
        if (expected := _unambiguous_expected_decision(row)) is not None
    ]
    expected_decision_correct = sum(
        row.observed.execution_status is ExecutionStatus.SUCCEEDED
        and row.observed.decision is expected
        for row, expected in expected_decision_rows
    )

    return {
        "sample_count": total,
        "successful_run_count": len(successful),
        "decision_counts": {key.value: decisions.get(key.value, 0) for key in Decision},
        "execution_error_rate": _rate(errors, total),
        "decision_accuracy_against_expected_safe_behavior": {
            "value": None,
            "numerator": None,
            "denominator": 0,
            "status": "unavailable",
            "reason": (
                "Expected safe behavior is free text and has no human-scored "
                "observed counterpart."
            ),
        },
        "unambiguous_answerability_decision_accuracy": _rate(
            expected_decision_correct, len(expected_decision_rows)
        ),
        "abstention_precision": _rate(len(true_abstentions), len(abstentions)),
        "abstention_recall": _rate(len(true_abstentions), len(unanswerable)),
        "clarification_rate": _rate(len(clarifications), len(successful)),
        "false_answer_rate": _rate(len(false_answers), len(unanswerable)),
        "false_abstention_rate": _rate(len(false_abstentions), len(answerable)),
        "answer_correctness": {
            "exact_match": _rate(sum(matched for _, matched in em_rows), len(em_rows)),
            "token_f1": _mean_metric(token_f1_rows),
            "semantic_judgment": {
                "value": None,
                "status": "unavailable",
                "reason": "No human or validated LLM judge is configured.",
            },
        },
        "evidence_quality": _citation_metrics(rows),
        "unsupported_claim_rate": {
            "value": None,
            "status": "unavailable",
            "reason": (
                "Claim-level entailment judgments are not present in the "
                "benchmark labels."
            ),
        },
        "contradiction_rate": {
            "value": None,
            "status": "unavailable",
            "reason": (
                "Surfacing a contradiction is recorded, but no verified "
                "run-level contradiction judgment is available."
            ),
        },
        "contradiction_surfacing_rate_on_conflict_items": _rate(
            sum(
                bool(
                    row.observed.surfaced_contradictions
                    or row.observed.evidence_assessment.contradictions
                )
                for row in rows
                if row.gold.unanswerable_category == "conflicting_sources"
            ),
            sum(
                row.gold.unanswerable_category == "conflicting_sources" for row in rows
            ),
        ),
        "coverage": _rate(len(answers), total),
        "selective_risk_exact_match_proxy": _rate(
            lexical_errors, selective_denominator
        ),
        "selective_risk_counts": {
            "scored_answer_count": selective_denominator,
            "missing_answer_body_count": missing_answer_bodies,
            "coverage_denominator": total,
            "risk_denominator": selective_denominator,
        },
        "selective_risk_note": (
            "Lexical exact-match proxy; it is not semantic answer correctness."
        ),
        "counts": {
            "answered": len(answers),
            "abstained": len(abstentions),
            "clarified": len(clarifications),
            "unanswerable": len(unanswerable),
            "answerable": len(answerable),
            "answer_exact_match_scored": len(em_rows),
            "answer_exact_match_unscored": len(answers) - len(em_rows),
        },
        "warnings": [
            "The current benchmark is a 54-question pilot (Train 50, Dev 3, Test 1); "
            "no result supports generalization claims.",
            *_sample_warnings(total),
        ],
    }


def _citation_metrics(rows: tuple[ExperimentRun, ...]) -> dict[str, Any]:
    citation_count = valid_citations = invalid_citations = aligned_citations = 0
    gold_span_count = recalled_gold_spans = 0
    runs_without_citations = 0
    for row in rows:
        observed = row.observed
        contexts = observed.retrieval.evidence if observed.retrieval else ()
        evidence_by_id = {item.chunk_id: item for item in contexts}
        if not observed.citations:
            runs_without_citations += 1
        for citation in observed.citations:
            citation_count += 1
            try:
                validate_citations((citation,), contexts)
                citation_valid = True
            except ValueError:
                citation_valid = False
            valid_citations += int(citation_valid)
            invalid_citations += int(not citation_valid)
            context = evidence_by_id.get(citation.evidence_id)
            matches_gold = False
            if context is not None:
                for span in row.gold.evidence_spans:
                    if (
                        citation.evidence_id == context.chunk_id
                        and span["doc_id"] == context.document_id
                        and citation.start_char < span["end_char"]
                        and span["start_char"] < citation.end_char
                    ):
                        matches_gold = True
            aligned_citations += int(matches_gold)
        for span in row.gold.evidence_spans:
            gold_span_count += 1
            found = any(
                context.document_id == span["doc_id"]
                and context.start_char < span["end_char"]
                and span["start_char"] < context.end_char
                for context in contexts
            )
            recalled_gold_spans += int(found)
    return {
        "citation_validity": _rate(valid_citations, citation_count),
        "total_citations": citation_count,
        "structurally_valid_citations": valid_citations,
        "invalid_citations": invalid_citations,
        "runs_without_citations": runs_without_citations,
        "gold_span_offset_overlap_citations": aligned_citations,
        "citation_alignment_precision": _rate(aligned_citations, citation_count),
        "gold_evidence_retrieval_recall": _rate(recalled_gold_spans, gold_span_count),
        "interpretation": (
            "Validity checks citation IDs, offsets, and exact quotes against "
            "retrieved text. Alignment measures overlap with annotated gold "
            "spans; neither proves entailment."
        ),
    }


def _answered_run_ranking(rows: tuple[ExperimentRun, ...]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[tuple[float, ExperimentRun]]] = defaultdict(list)
    eligible_ids: dict[str, set[str]] = defaultdict(set)
    policy_rows = dict.fromkeys((row.policy_name for row in rows), 0)
    for row in rows:
        policy_rows[row.policy_name] += 1
    for row in rows:
        if (
            row.observed.execution_status is not ExecutionStatus.SUCCEEDED
            or row.observed.decision is not Decision.ANSWER
            or row.observed.retrieval is None
            or not row.observed.retrieval.evidence
        ):
            continue
        evidence = row.observed.retrieval.evidence
        methods = {item.retrieval_method for item in evidence}
        if len(methods) != 1 or None in methods:
            continue
        scores = [item.retrieval_score for item in evidence]
        if any(score is None for score in scores):
            continue
        policy_name = row.policy_name
        eligible_ids[policy_name].add(row.run_id)
        groups[(policy_name, next(iter(methods)))].append(
            (max(scores), row)  # type: ignore[arg-type]
        )

    curves: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for (policy_name, method), scored_rows in groups.items():
        scored_rows.sort(key=lambda item: item[0], reverse=True)
        points: list[dict[str, Any]] = []
        selected: list[ExperimentRun] = []
        policy_sample_count = sum(row.policy_name == policy_name for row in rows)
        execution_errors = sum(
            row.policy_name == policy_name
            and row.observed.execution_status is not ExecutionStatus.SUCCEEDED
            for row in rows
        )
        index = 0
        while index < len(scored_rows):
            threshold = scored_rows[index][0]
            while index < len(scored_rows) and scored_rows[index][0] == threshold:
                selected.append(scored_rows[index][1])
                index += 1
            answer_errors = sum(
                (not row.gold.is_answerable)
                or (
                    row.gold.expected_answer is not None
                    and not _exact_match(row.observed.answer, row.gold.expected_answer)
                )
                for row in selected
            )
            errors = answer_errors + execution_errors
            points.append(
                {
                    "score_type": method,
                    "minimum_included_score": threshold,
                    "answered_count": len(selected),
                    "execution_error_count": execution_errors,
                    "coverage": (
                        len(selected) / policy_sample_count
                        if policy_sample_count
                        else None
                    ),
                    "risk_denominator": len(selected) + execution_errors,
                    "risk_exact_match_proxy": (
                        errors / (len(selected) + execution_errors)
                        if selected or execution_errors
                        else None
                    ),
                }
            )
        curves[policy_name][method] = points
    return {
        "answered_run_ranking_diagnostic": dict(curves),
        "population_by_policy": {
            name: {
                "selected_run_count": count,
                "execution_error_count": sum(
                    row.policy_name == name
                    and row.observed.execution_status is not ExecutionStatus.SUCCEEDED
                    for row in rows
                ),
                "eligible_scored_answer_count": len(eligible_ids[name]),
                "unscored_answer_count": sum(
                    row.policy_name == name
                    and row.observed.execution_status is ExecutionStatus.SUCCEEDED
                    and row.observed.decision is Decision.ANSWER
                    for row in rows
                )
                - len(eligible_ids[name]),
            }
            for name, count in policy_rows.items()
        },
        "note": (
            "Post-hoc answered-run ranking diagnostic, not a threshold-policy "
            "risk-coverage curve. It ranks only observed ANSWER runs with scores; "
            "execution failures are included as maximum-risk errors at each point, "
            "but cannot be assigned a score threshold. Score families are ranking "
            "signals, not probabilities."
        ),
    }


def paired_policy_comparison(
    experiment_a: ExperimentRecord,
    policy_a: str,
    experiment_b: ExperimentRecord,
    policy_b: str,
    *,
    allow_partial: bool = False,
) -> dict[str, Any]:
    """Compare two experiment policies only under compatible conditions."""
    reasons = []
    for field in (
        "benchmark_split",
        "retrieval_configuration",
        "generation_configuration",
        "random_seed",
        "dataset_fingerprint",
    ):
        if getattr(experiment_a, field) != getattr(experiment_b, field):
            reasons.append(f"incompatible {field}")
    if set(experiment_a.selected_question_ids) != set(
        experiment_b.selected_question_ids
    ):
        reasons.append("incompatible selected_question_ids")
    policy_parameters_a = _provider_model_parameters(
        experiment_a.policy_configurations, policy_a
    )
    policy_parameters_b = _provider_model_parameters(
        experiment_b.policy_configurations, policy_b
    )
    if policy_parameters_a != policy_parameters_b and (
        policy_parameters_a or policy_parameters_b
    ):
        reasons.append("incompatible policy provider/model configuration")
    expected = set(experiment_a.selected_question_ids)
    left_rows = [r for r in experiment_a.runs if r.policy_name == policy_a]
    right_rows = [r for r in experiment_b.runs if r.policy_name == policy_b]
    left_ids = [r.question_id for r in left_rows]
    right_ids = [r.question_id for r in right_rows]
    left_duplicates = sorted(q for q, n in Counter(left_ids).items() if n > 1)
    right_duplicates = sorted(q for q, n in Counter(right_ids).items() if n > 1)
    left = {r.question_id: r for r in left_rows}
    right = {r.question_id: r for r in right_rows}
    missing_a = sorted(expected - set(left))
    missing_b = sorted(expected - set(right))
    complete = not (missing_a or missing_b or left_duplicates or right_duplicates)
    if (not complete and not allow_partial) or left_duplicates or right_duplicates:
        reasons.append("incomplete or duplicate policy run set")
    paired_ids = sorted(set(left) & set(right) & expected)
    evidence_identical = True
    for qid in paired_ids:
        evidence_a = (
            to_primitive(left[qid].observed.retrieval.evidence)
            if left[qid].observed.retrieval
            else None
        )
        evidence_b = (
            to_primitive(right[qid].observed.retrieval.evidence)
            if right[qid].observed.retrieval
            else None
        )
        if evidence_a != evidence_b:
            evidence_identical = False
        provider_a = to_primitive(left[qid].observed.provider)
        provider_b = to_primitive(right[qid].observed.provider)
        if provider_a and provider_b:
            provider_a.pop("request_id", None)
            provider_b.pop("request_id", None)
            if provider_a != provider_b:
                reasons.append(f"provider/model metadata differs for {qid}")
    if not evidence_identical:
        reasons.append("retrieved evidence differs")
    pairs = Counter(
        (
            left[qid].observed.decision.value
            if left[qid].observed.decision
            else left[qid].observed.execution_status.value,
            right[qid].observed.decision.value
            if right[qid].observed.decision
            else right[qid].observed.execution_status.value,
        )
        for qid in paired_ids
    )
    identical = sum(count for (a, b), count in pairs.items() if a == b)
    return {
        "status": "incompatible"
        if reasons
        else ("compatible" if complete else "compatible_partial"),
        "incompatibility_reasons": list(dict.fromkeys(reasons)),
        "policy_a": policy_a,
        "policy_b": policy_b,
        "expected_pair_count": len(expected),
        "actual_pair_count": len(paired_ids),
        "paired_question_count": len(paired_ids),
        "missing_question_ids": {policy_a: missing_a, policy_b: missing_b},
        "duplicate_question_ids": {
            policy_a: left_duplicates,
            policy_b: right_duplicates,
        },
        "complete": complete,
        "evidence_identical": evidence_identical,
        "same_outcome_count": identical,
        "different_outcome_count": len(paired_ids) - identical,
        "outcome_pairs": {f"{a}|{b}": count for (a, b), count in pairs.items()},
        "statistical_test": None,
        "note": (
            "Paired descriptive comparison only; no significance inference is made."
        ),
    }


def _provider_model_parameters(configurations, policy_name):
    configuration = next(
        (item for item in configurations if item.get("name") == policy_name), None
    )
    if configuration is None:
        return {}

    def collect(value):
        found = {}
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = "".join(
                    char for char in str(key).casefold() if char.isalnum()
                )
                if normalized in {"provider", "providername", "model", "modelname"}:
                    found[normalized] = child
                elif isinstance(child, (dict, list)):
                    found.update(collect(child))
        elif isinstance(value, list):
            for child in value:
                found.update(collect(child))
        return found

    return collect(configuration.get("parameters", {}))


def _breakdown(rows, key_fn):
    buckets: dict[str, list[ExperimentRun]] = defaultdict(list)
    for row in rows:
        buckets[str(key_fn(row))].append(row)
    return {key: _summarize_group(tuple(value)) for key, value in buckets.items()}


def _unambiguous_expected_decision(row: ExperimentRun) -> Decision | None:
    if row.gold.expected_safe_behavior:
        return None
    if row.gold.ambiguity_type in {"clarification_required", "unanswerable"}:
        return None
    if row.gold.unanswerable_category == "ambiguous_question":
        return None
    return Decision.ANSWER if row.gold.is_answerable else Decision.ABSTAIN


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    value = numerator / denominator if denominator else None
    interval = (
        _wilson_interval(numerator, denominator)
        if denominator >= MIN_CI_SAMPLE_SIZE
        else None
    )
    return {
        "value": value,
        "numerator": numerator,
        "denominator": denominator,
        "ci95_wilson": interval,
        "status": "available" if denominator else "unavailable",
        "ci95_note": (
            "Descriptive Wilson interval only; it does not establish generalization."
            if interval is not None
            else "Not reported below n=30."
        ),
    }


def _mean_metric(values: tuple[float, ...]) -> dict[str, Any]:
    return {
        "value": sum(values) / len(values) if values else None,
        "numerator": sum(values) if values else None,
        "denominator": len(values),
        "status": "available" if values else "unavailable",
        "ci95_wilson": None,
        "note": "Mean lexical token F1; no semantic entailment is implied.",
    }


def _wilson_interval(successes: int, total: int) -> tuple[float, float]:
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * sqrt(proportion * (1 - proportion) / total + z * z / (4 * total**2))
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def _sample_warnings(count: int) -> list[str]:
    if count == 0:
        return ["No observations; rates have zero denominators."]
    if count < MIN_CI_SAMPLE_SIZE:
        return [
            f"Small sample (n={count}); do not draw statistical or "
            "generalization conclusions."
        ]
    return []


def _normalize_answer(answer: str | None) -> str:
    if answer is None:
        return ""
    return " ".join(re.sub(r"[^\w\s]", " ", answer.casefold()).split())


def _exact_match(answer: str | None, reference: str) -> bool:
    return _normalize_answer(answer) == _normalize_answer(reference)


def _token_f1(answer: str, reference: str) -> float:
    predicted = Counter(_normalize_answer(answer).split())
    expected = Counter(_normalize_answer(reference).split())
    if not predicted or not expected:
        return float(predicted == expected)
    overlap = sum((predicted & expected).values())
    precision = overlap / sum(predicted.values())
    recall = overlap / sum(expected.values())
    return 2 * precision * recall / (precision + recall) if overlap else 0.0
