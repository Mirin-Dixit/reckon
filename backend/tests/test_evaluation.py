"""Tests for split-aware evaluation, leakage prevention, and metrics."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.evaluation.metrics import paired_policy_comparison, summarize_runs
from app.evaluation.results import (
    EXPERIMENT_SCHEMA_VERSION,
    ExperimentRecord,
    ExperimentRun,
    GoldLabels,
)
from app.evaluation.runner import (
    ErrorHandlingMode,
    EvaluationRunner,
    PolicyRunConfig,
)
from app.evaluation.serialization import experiment_from_json, experiment_to_json
from app.generation.contracts import (
    ClaimCitation,
    Decision,
    DecisionReason,
    EvidenceAssessment,
    EvidenceContext,
    ExecutionStatus,
    ProviderMetadata,
    ReasonCode,
    RetrievalMetadata,
    RunResult,
)
from app.generation.pipeline import (
    DecisionSelection,
    GeneratedAnswer,
    MockAnswerGenerator,
    MockEvidenceAssessor,
    PipelineConfig,
    RagPipeline,
)
from app.ingestion.schema import Document

BENCHMARK = Path("data/benchmark")


class EmptyRetriever:
    def search(self, query: str, top_k: int = 5):
        return []


class CaptureAbstainPolicy:
    def __init__(self, name):
        self.name = name
        self.calls = []

    def decide(self, question, assessment, evidence):
        self.calls.append((question, assessment, evidence))
        return DecisionSelection(
            Decision.ABSTAIN,
            DecisionReason(ReasonCode.INSUFFICIENT_EVIDENCE, "No retrieved evidence."),
            policy_name=self.name,
            policy_parameters={"mode": "deterministic"},
        )


def make_factory(observations):
    def factory(policy, documents, retrieval_config, generation_config, seed):
        observations.append(
            {
                "policy": policy,
                "documents": documents,
                "retrieval": retrieval_config,
                "generation": generation_config,
                "seed": seed,
            }
        )
        assert all(isinstance(doc, Document) for doc in documents.values())
        assert all(not hasattr(doc, "expected_answer") for doc in documents.values())
        return RagPipeline(
            retriever=EmptyRetriever(),
            documents=dict(documents),
            assessor=MockEvidenceAssessor(EvidenceAssessment()),
            policy=policy,
            generator=MockAnswerGenerator(GeneratedAnswer("Unused answer.", ())),
            config=PipelineConfig(
                top_k=retrieval_config["top_k"], retrieval_method="bm25"
            ),
        )

    return factory


def runner() -> EvaluationRunner:
    return EvaluationRunner(
        BENCHMARK / "documents.jsonl", BENCHMARK / "questions.jsonl"
    )


def test_split_filtering_multi_policy_run_and_runtime_gold_separation():
    evaluator = runner()
    question_id = next(q.id for q in evaluator._questions if q.split == "train")
    policies = [
        PolicyRunConfig("policy_a", CaptureAbstainPolicy("policy_a"), {"mode": "a"}),
        PolicyRunConfig("policy_b", CaptureAbstainPolicy("policy_b"), {"mode": "b"}),
    ]
    calls = []
    experiment = evaluator.run(
        split="train",
        policies=policies,
        pipeline_factory=make_factory(calls),
        retrieval_configuration={"method": "bm25", "top_k": 5},
        generation_configuration={
            "provider": "mock",
            "model": "offline",
            "api_key": "do-not-record-this",
        },
        random_seed=13,
        question_ids=[question_id],
    )
    assert experiment.selected_question_ids == (question_id,)
    assert len(experiment.runs) == 2
    assert len({run.run_id for run in experiment.runs}) == 2
    assert all(run.question_id == question_id for run in experiment.runs)
    assert len(calls) == 2
    assert all(call["seed"] == 13 for call in calls)
    assert calls[0]["retrieval"] == calls[1]["retrieval"]
    assert calls[0]["generation"] == calls[1]["generation"]
    assert calls[0]["generation"]["api_key"] == "<redacted>"
    for configured_policy, run in zip(policies, experiment.runs):
        runtime_calls = configured_policy.policy.calls
        assert runtime_calls
        runtime_question, _, _ = runtime_calls[0]
        assert isinstance(runtime_question, str)
        assert runtime_question == evaluator._questions[0].question
        assert run.gold.expected_answer == evaluator._questions[0].expected_answer
        assert run.observed.decision is Decision.ABSTAIN
    assert experiment.schema_version == EXPERIMENT_SCHEMA_VERSION
    assert experiment.created_at_utc.endswith("Z")
    assert len(experiment.dataset_fingerprint["documents_sha256"]) == 64
    assert len(experiment.dataset_fingerprint["questions_sha256"]) == 64
    assert "do-not-record-this" not in experiment_to_json(experiment)


def test_question_filter_rejects_ids_outside_selected_split():
    with pytest.raises(ValueError, match="not in split dev"):
        runner().run(
            split="dev",
            policies=[],
            pipeline_factory=make_factory([]),
            retrieval_configuration={},
            generation_configuration={},
            question_ids=["q_pilot_001"],
        )


def test_redacted_configuration_is_what_runtime_factory_receives():
    evaluator = runner()
    qid = next(q.id for q in evaluator._questions if q.split == "train")
    received = []
    experiment = evaluator.run(
        split="train",
        policies=[PolicyRunConfig("p", CaptureAbstainPolicy("p"), {})],
        pipeline_factory=make_factory(received),
        retrieval_configuration={"method": "bm25", "top_k": 2},
        generation_configuration={
            "nested": [{"apiKey": "secret-a", "clientSecret": "secret-b"}],
            "OPENAI_API_KEY": "secret-c",
            "api_key_env_var": "OPENAI_API_KEY",
        },
        question_ids=[qid],
    )
    runtime_config = received[0]["generation"]
    assert runtime_config["nested"][0] == {
        "apiKey": "<redacted>",
        "clientSecret": "<redacted>",
    }
    assert runtime_config["OPENAI_API_KEY"] == "<redacted>"
    assert runtime_config["api_key_env_var"] == "OPENAI_API_KEY"
    assert "secret-a" not in experiment.to_dict().__repr__()


def test_empty_selection_is_a_valid_record_with_zero_runs():
    experiment = runner().run(
        split="test",
        policies=[],
        pipeline_factory=make_factory([]),
        retrieval_configuration={},
        generation_configuration={},
        question_ids=[],
    )
    assert experiment.selected_question_ids == ()
    assert experiment.runs == ()
    assert experiment.metrics["sample_count"] == 0
    assert experiment.metrics["coverage"]["value"] is None
    assert experiment.metrics["warnings"]


def test_empty_split_loads_as_zero_runs(tmp_path):
    question_rows = [
        json.loads(line)
        for line in (BENCHMARK / "questions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    train_only = [item for item in question_rows if item["split"] == "train"]
    question_path = tmp_path / "train_only_questions.jsonl"
    question_path.write_text(
        "\n".join(json.dumps(item) for item in train_only) + "\n",
        encoding="utf-8",
    )
    evaluator = EvaluationRunner(BENCHMARK / "documents.jsonl", question_path)
    factories_called = []
    experiment = evaluator.run(
        split="dev",
        policies=[PolicyRunConfig("p", CaptureAbstainPolicy("p"), {})],
        pipeline_factory=lambda *args: factories_called.append(args),
        retrieval_configuration={"method": "bm25", "top_k": 2},
        generation_configuration={"provider": "mock"},
    )
    assert experiment.selected_question_ids == ()
    assert experiment.runs == ()
    assert factories_called == []


class FailingPipeline:
    def __init__(self):
        self.calls = 0

    def run(self, question):
        self.calls += 1
        raise RuntimeError("token=secret-value")


def test_continue_on_error_and_fail_fast_modes_keep_errors_out_of_decisions():
    evaluator = runner()
    ids = [q.id for q in evaluator._questions if q.split == "train"][:2]

    def factory(*_args):
        return FailingPipeline()

    def execute(mode):
        return evaluator.run(
            split="train",
            policies=[PolicyRunConfig("p", CaptureAbstainPolicy("p"), {})],
            pipeline_factory=factory,
            retrieval_configuration={},
            generation_configuration={},
            question_ids=ids,
            error_mode=mode,
        )

    continued = execute(ErrorHandlingMode.CONTINUE)
    assert len(continued.runs) == 2
    assert not continued.stopped_early
    assert all(run.observed.decision is None for run in continued.runs)
    assert all(run.error.kind == "RuntimeError" for run in continued.runs)
    assert all("secret-value" not in run.error.message for run in continued.runs)

    stopped = execute(ErrorHandlingMode.FAIL_FAST)
    assert len(stopped.runs) == 1
    assert stopped.stopped_early
    assert stopped.selected_question_ids == tuple(ids)
    assert stopped.metrics["partial"] is True
    assert stopped.metrics["run_accounting"]["p"]["expected_runs"] == 2
    assert stopped.metrics["run_accounting"]["p"]["observed_runs"] == 1
    assert stopped.metrics["run_accounting"]["p"]["missing_question_ids"] == [ids[1]]


def test_experiment_json_round_trip_version_and_credential_redaction():
    calls = []
    experiment = runner().run(
        split="train",
        policies=[
            PolicyRunConfig("p", CaptureAbstainPolicy("p"), {"api_key": "secret-token"})
        ],
        pipeline_factory=make_factory(calls),
        retrieval_configuration={"method": "bm25", "top_k": 4},
        generation_configuration={
            "provider": "openai",
            "api_key": "secret-token",
            "apiKey": "camel-secret",
            "API_KEY": "upper-secret",
            "client_secret": "client-secret",
            "clientSecret": "camel-client-secret",
            "authorization": "Bearer auth-secret",
            "access_token": "access-secret",
            "refresh_token": "refresh-secret",
            "OPENAI_API_KEY": "openai-env-secret",
            "nested": [{"clientSecret": "nested-secret"}],
            "api_key_env_var": "OPENAI_API_KEY",
        },
        question_ids=[],
    )
    serialized = experiment_to_json(experiment)
    loaded = experiment_from_json(serialized)
    assert loaded == json.loads(serialized)
    assert loaded["schema_version"] == EXPERIMENT_SCHEMA_VERSION
    assert "secret-token" not in serialized
    assert loaded["generation_configuration"]["api_key"] == "<redacted>"
    assert loaded["generation_configuration"]["api_key_env_var"] == "OPENAI_API_KEY"
    for key in (
        "apiKey",
        "API_KEY",
        "client_secret",
        "clientSecret",
        "authorization",
        "access_token",
        "refresh_token",
        "OPENAI_API_KEY",
    ):
        assert loaded["generation_configuration"][key] == "<redacted>"
    assert (
        loaded["generation_configuration"]["nested"][0]["clientSecret"] == "<redacted>"
    )
    assert loaded["runs"] == []
    with pytest.raises(ValueError, match="Unsupported experiment schema"):
        experiment_from_json(serialized.replace(EXPERIMENT_SCHEMA_VERSION, "future.v2"))


def test_experiment_metrics_are_grouped_by_full_retrieval_configuration():
    experiment = runner().run(
        split="train",
        policies=[PolicyRunConfig("p", CaptureAbstainPolicy("p"), {})],
        pipeline_factory=make_factory([]),
        retrieval_configuration={"method": "bm25", "top_k": 3, "k1": 1.4},
        generation_configuration={"provider": "mock"},
        question_ids=[],
    )
    key = json.dumps(experiment.retrieval_configuration, sort_keys=True)
    assert key in experiment.metrics["breakdowns"]["retrieval_configuration"]


def gold(
    question_id,
    *,
    answerable=True,
    answer="Alpha",
    split="train",
    safe=None,
    category=None,
    ambiguity=None,
    evidence_spans=(),
):
    return GoldLabels(
        question_id=question_id,
        split=split,
        is_answerable=answerable,
        expected_answer=answer if answerable else None,
        expected_safe_behavior=safe,
        unanswerable_category=category,
        ambiguity_type=ambiguity,
        domain="demo",
        question_type="factoid",
        evidence_spans=tuple(evidence_spans),
    )


def run_record(
    question_id,
    decision,
    labels,
    *,
    answer=None,
    policy="p",
    score=None,
    provider=None,
):
    reason = (
        DecisionReason(ReasonCode.INSUFFICIENT_EVIDENCE, "No answer.")
        if decision is Decision.ABSTAIN
        else None
    )
    evidence = (
        (
            EvidenceContext(
                "c-1",
                "d-1",
                "Alpha evidence.",
                0,
                len("Alpha evidence."),
                retrieval_rank=1,
                retrieval_score=score,
                retrieval_method="bm25",
            ),
        )
        if score is not None
        else ()
    )
    result = RunResult(
        decision=decision,
        answer=answer,
        abstention_reason=reason,
        evidence_assessment=EvidenceAssessment(),
        execution_status=ExecutionStatus.SUCCEEDED,
        clarification_question="Which meaning do you intend?"
        if decision is Decision.CLARIFY
        else None,
        policy_name=policy,
        provider=provider,
        retrieval=RetrievalMetadata("bm25", 1, evidence) if score is not None else None,
    )
    return ExperimentRun(str(uuid.uuid4()), question_id, policy, result, labels)


def test_gold_labels_reject_missing_or_invalid_reference_answers():
    with pytest.raises(ValueError, match="require expected_answer"):
        gold("bad", answerable=True, answer=None)
    with pytest.raises(ValueError, match="cannot have expected_answer"):
        GoldLabels(
            "bad",
            "train",
            False,
            "unexpected",
            None,
            None,
            None,
            "demo",
            "factoid",
            (),
        )
    with pytest.raises(ValueError, match="is_answerable must be a boolean"):
        GoldLabels("bad", "train", 1, "answer", None, None, None, "demo", "factoid", ())


def test_metrics_denominators_zero_handling_tiny_warnings_and_unavailable_judgments():
    rows = (
        run_record("a", Decision.ANSWER, gold("a"), answer="alpha!"),
        run_record(
            "b",
            Decision.ABSTAIN,
            gold("b", answerable=False, category="off-topic"),
        ),
        run_record(
            "c",
            Decision.ANSWER,
            gold("c", answerable=False, category="off-topic"),
            answer="Unsupported answer",
        ),
    )
    metrics = summarize_runs(rows)
    assert metrics["decision_counts"] == {"ANSWER": 2, "ABSTAIN": 1, "CLARIFY": 0}
    assert metrics["abstention_precision"]["numerator"] == 1
    assert metrics["abstention_recall"]["denominator"] == 2
    assert metrics["answer_correctness"]["exact_match"]["numerator"] == 1
    assert metrics["false_answer_rate"]["value"] == 0.5
    assert (
        metrics["decision_accuracy_against_expected_safe_behavior"]["status"]
        == "unavailable"
    )
    assert metrics["evidence_quality"]["citation_validity"]["value"] is None
    assert metrics["warnings"]
    empty = summarize_runs(())
    assert empty["execution_error_rate"]["value"] is None
    assert empty["coverage"]["denominator"] == 0


def test_tiny_sample_has_no_wilson_interval_and_answered_ranking_groups():
    items = tuple(
        run_record(
            str(i),
            Decision.ANSWER,
            gold(str(i), answerable=(i == 0), answer="Alpha"),
            answer="Alpha" if i == 0 else "Wrong",
            score=1.0 - i * 0.1,
        )
        for i in range(3)
    )
    metrics = summarize_runs(items)
    assert metrics["coverage"]["ci95_wilson"] is None
    curve = metrics["answered_run_ranking"]["answered_run_ranking_diagnostic"]["p"][
        "bm25"
    ]
    assert len(curve) == 3
    assert curve[0]["coverage"] == pytest.approx(1 / 3)
    assert curve[-1]["coverage"] == 1.0
    assert "not a threshold-policy" in metrics["answered_run_ranking"]["note"]


def _experiment(
    rows,
    selected_ids,
    *,
    retrieval=None,
    generation=None,
    seed=11,
    policy_configurations=(),
):
    return ExperimentRecord(
        experiment_id=str(uuid.uuid4()),
        schema_version=EXPERIMENT_SCHEMA_VERSION,
        created_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        benchmark_split="train",
        selected_question_ids=tuple(selected_ids),
        dataset_fingerprint={"documents_sha256": "d", "questions_sha256": "q"},
        retrieval_configuration=retrieval or {"method": "bm25"},
        policy_configurations=tuple(policy_configurations),
        generation_configuration=generation or {"provider": "mock"},
        random_seed=seed,
        software_metadata={},
        environment_metadata={},
        runs=tuple(rows),
    )


def test_paired_comparison_aligns_by_question_and_rejects_missing_pairs():
    records = (
        run_record("q1", Decision.ANSWER, gold("q1"), answer="Alpha", policy="a"),
        run_record("q2", Decision.ABSTAIN, gold("q2"), policy="a"),
        run_record("q1", Decision.ABSTAIN, gold("q1"), policy="b"),
        run_record("q2", Decision.ABSTAIN, gold("q2"), policy="b"),
    )
    left = _experiment(records[:2], ["q1", "q2"])
    right = _experiment(records[2:], ["q1", "q2"])
    paired = paired_policy_comparison(left, "a", right, "b")
    assert paired["status"] == "compatible"
    assert paired["expected_pair_count"] == paired["actual_pair_count"] == 2
    assert paired["different_outcome_count"] == 1
    incomplete = _experiment(records[2:3], ["q1", "q2"])
    result = paired_policy_comparison(left, "a", incomplete, "b")
    assert result["status"] == "incompatible"
    assert result["missing_question_ids"]["b"] == ["q2"]
    partial = paired_policy_comparison(left, "a", incomplete, "b", allow_partial=True)
    assert partial["status"] == "compatible_partial"
    assert not partial["complete"]
    assert partial["expected_pair_count"] == 2
    assert partial["actual_pair_count"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("benchmark_split", "dev"),
        ("selected_question_ids", ("different",)),
        ("retrieval_configuration", {"method": "dense"}),
        ("generation_configuration", {"provider": "other"}),
        ("random_seed", 12),
        ("dataset_fingerprint", {"documents_sha256": "other", "questions_sha256": "q"}),
    ],
)
def test_paired_comparison_rejects_incompatible_experiment_conditions(field, value):
    a = run_record("q1", Decision.ABSTAIN, gold("q1"), policy="a")
    b = run_record("q1", Decision.ABSTAIN, gold("q1"), policy="b")
    left = _experiment([a], ["q1"])
    right = _experiment([b], ["q1"])
    object.__setattr__(right, field, value)
    result = paired_policy_comparison(left, "a", right, "b")
    assert result["status"] == "incompatible"
    assert result["incompatibility_reasons"]


def test_paired_comparison_rejects_evidence_mismatch_and_reports_duplicates():
    a = run_record(
        "q1", Decision.ANSWER, gold("q1"), answer="Alpha", policy="a", score=1.0
    )
    b = run_record(
        "q1", Decision.ANSWER, gold("q1"), answer="Alpha", policy="b", score=0.5
    )
    result = paired_policy_comparison(
        _experiment([a], ["q1"]), "a", _experiment([b], ["q1"]), "b"
    )
    assert result["status"] == "incompatible"
    assert not result["evidence_identical"]
    duplicate = _experiment([b], ["q1"])
    object.__setattr__(duplicate, "runs", (b, b))
    result = paired_policy_comparison(_experiment([a], ["q1"]), "a", duplicate, "b")
    assert result["duplicate_question_ids"]["b"] == ["q1"]


def test_paired_comparison_rejects_provider_model_mismatch():
    a = run_record(
        "q1",
        Decision.ABSTAIN,
        gold("q1"),
        policy="a",
        provider=ProviderMetadata("provider-a", "model-a"),
    )
    b = run_record(
        "q1",
        Decision.ABSTAIN,
        gold("q1"),
        policy="b",
        provider=ProviderMetadata("provider-b", "model-b"),
    )
    result = paired_policy_comparison(
        _experiment([a], ["q1"]), "a", _experiment([b], ["q1"]), "b"
    )
    assert result["status"] == "incompatible"
    assert any(
        "provider/model" in reason for reason in result["incompatibility_reasons"]
    )

    left = _experiment(
        [a],
        ["q1"],
        policy_configurations=(
            {"name": "a", "parameters": {"provider": "provider-a", "model": "model-a"}},
        ),
    )
    right = _experiment(
        [b],
        ["q1"],
        policy_configurations=(
            {"name": "b", "parameters": {"provider": "provider-b", "model": "model-b"}},
        ),
    )
    result = paired_policy_comparison(left, "a", right, "b")
    assert any(
        "policy provider/model" in reason
        for reason in result["incompatibility_reasons"]
    )


def test_answered_ranking_diagnostic_counts_errors_as_maximum_risk():
    answer = run_record("a", Decision.ANSWER, gold("a"), answer="Alpha", score=0.8)
    failed_result = RunResult(None, EvidenceAssessment(), ExecutionStatus.FAILED)
    failed = ExperimentRun("failed", "b", "p", failed_result, gold("b"))
    abstain = run_record("c", Decision.ABSTAIN, gold("c"), policy="p")
    metrics = summarize_runs((answer, failed, abstain))
    points = metrics["answered_run_ranking"]["answered_run_ranking_diagnostic"]["p"][
        "bm25"
    ]
    assert points[0]["answered_count"] == 1
    assert points[0]["execution_error_count"] == 1
    assert points[0]["risk_denominator"] == 2
    assert points[0]["risk_exact_match_proxy"] == pytest.approx(0.5)


def test_zero_answers_and_no_score_produce_no_ranking_points_and_null_risk():
    rows = (
        run_record("a", Decision.ABSTAIN, gold("a")),
        run_record("b", Decision.CLARIFY, gold("b")),
        ExperimentRun(
            "e",
            "c",
            "p",
            RunResult(None, EvidenceAssessment(), ExecutionStatus.FAILED),
            gold("c"),
        ),
    )
    metrics = summarize_runs(rows)
    assert metrics["coverage"]["value"] == 0
    assert metrics["selective_risk_exact_match_proxy"]["value"] is None
    assert metrics["answered_run_ranking"]["answered_run_ranking_diagnostic"] == {}
    assert (
        metrics["answered_run_ranking"]["population_by_policy"]["p"][
            "unscored_answer_count"
        ]
        == 0
    )


def test_unscored_answer_is_reported_outside_the_answered_ranking_diagnostic():
    row = run_record("q", Decision.ANSWER, gold("q"), answer="Alpha")
    diagnostic = summarize_runs((row,))["answered_run_ranking"]
    assert diagnostic["answered_run_ranking_diagnostic"] == {}
    assert diagnostic["population_by_policy"]["p"]["unscored_answer_count"] == 1


def test_tied_scores_form_one_ranking_point():
    rows = tuple(
        run_record(str(i), Decision.ANSWER, gold(str(i)), answer="Alpha", score=0.5)
        for i in range(2)
    )
    points = summarize_runs(rows)["answered_run_ranking"][
        "answered_run_ranking_diagnostic"
    ]["p"]["bm25"]
    assert len(points) == 1
    assert points[0]["answered_count"] == 2


def test_citations_are_counted_individually_and_alignment_uses_citation_offsets():
    context = EvidenceContext(
        "c-1",
        "d-1",
        "Alpha evidence text",
        0,
        19,
        retrieval_rank=1,
        retrieval_score=0.2,
        retrieval_method="bm25",
    )
    labels = gold(
        "q",
        evidence_spans=(
            {"doc_id": "d-1", "start_char": 0, "end_char": 5, "text": "Alpha"},
        ),
    )
    result = RunResult(
        Decision.ANSWER,
        EvidenceAssessment(),
        ExecutionStatus.SUCCEEDED,
        answer="Alpha is stated.",
        citations=(ClaimCitation("Alpha", "c-1", "Alpha", 0, 5),),
        retrieval=RetrievalMetadata("bm25", 1, (context,)),
    )
    # Simulate a corrupted archived result after the normal contract boundary.
    object.__setattr__(
        result,
        "citations",
        (
            ClaimCitation("Alpha", "c-1", "Alpha", 0, 5),
            ClaimCitation("Other", "missing", "Other", 10, 15),
        ),
    )
    row = ExperimentRun("r", "q", "p", result, labels)
    metrics = summarize_runs((row,))["evidence_quality"]
    assert metrics["total_citations"] == 2
    assert metrics["structurally_valid_citations"] == 1
    assert metrics["invalid_citations"] == 1
    assert metrics["gold_span_offset_overlap_citations"] == 1
    assert metrics["citation_alignment_precision"]["value"] == 0.5

    outside = RunResult(
        Decision.ANSWER,
        EvidenceAssessment(),
        ExecutionStatus.SUCCEEDED,
        answer="Text.",
        citations=(ClaimCitation("evidence", "c-1", "evidence", 6, 14),),
        retrieval=RetrievalMetadata("bm25", 1, (context,)),
    )
    outside_metrics = summarize_runs((ExperimentRun("r2", "q", "p", outside, labels),))[
        "evidence_quality"
    ]
    assert outside_metrics["structurally_valid_citations"] == 1
    assert outside_metrics["gold_span_offset_overlap_citations"] == 0


def test_no_citations_reports_run_count_separately():
    row = run_record("q", Decision.ANSWER, gold("q"), answer="Alpha")
    metrics = summarize_runs((row,))["evidence_quality"]
    assert metrics["total_citations"] == 0
    assert metrics["runs_without_citations"] == 1
    assert metrics["citation_validity"]["value"] is None


def test_missing_answer_body_is_counted_as_high_risk_and_still_covered():
    row = run_record("q", Decision.ANSWER, gold("q"), answer="Alpha")
    object.__setattr__(row.observed, "answer", None)
    metrics = summarize_runs((row,))
    assert metrics["coverage"]["value"] == 1.0
    assert metrics["selective_risk_exact_match_proxy"]["numerator"] == 1
    assert metrics["selective_risk_exact_match_proxy"]["denominator"] == 1
    assert metrics["selective_risk_counts"]["missing_answer_body_count"] == 1
    assert metrics["counts"]["answer_exact_match_unscored"] == 1


def test_final_json_redacts_recognizable_credentials_without_rewriting_normal_answer():
    row = run_record("q", Decision.ANSWER, gold("q"), answer="Ordinary answer")
    object.__setattr__(
        row.observed,
        "answer",
        "Ordinary answer sk-proj-abcdefghijklmnopqrstuvwxyz0123456789",
    )
    serialized = experiment_to_json(_experiment((row,), ["q"]))
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789" not in serialized
    assert "Ordinary answer" in serialized


def test_serialization_rejects_duplicate_run_ids_and_malformed_nested_run():
    row = run_record("q", Decision.ABSTAIN, gold("q"))
    object.__setattr__(row, "run_id", str(uuid.uuid4()))
    experiment = _experiment((row,), ["q"])
    payload = json.loads(experiment_to_json(experiment))
    payload["runs"][0]["run_id"] = "not-a-uuid"
    with pytest.raises(ValueError, match="run_id must be a UUID"):
        experiment_from_json(json.dumps(payload))
    payload = json.loads(experiment_to_json(experiment))
    payload["runs"][0]["observed"] = {}
    with pytest.raises(ValueError, match="observed result"):
        experiment_from_json(json.dumps(payload))

    other = run_record("q", Decision.ABSTAIN, gold("q"), policy="other")
    object.__setattr__(other, "run_id", str(uuid.uuid4()))
    multi = _experiment((row, other), ["q"])
    payload = json.loads(experiment_to_json(multi))
    payload["runs"][1]["run_id"] = payload["runs"][0]["run_id"]
    with pytest.raises(ValueError, match="run IDs must be unique"):
        experiment_from_json(json.dumps(payload))


def test_partial_experiment_round_trips_and_non_utc_timestamp_is_rejected():
    row = run_record("q", Decision.ABSTAIN, gold("q"))
    experiment = _experiment((row,), ["q", "missing"])
    assert experiment_from_json(experiment_to_json(experiment))["runs"]
    payload = json.loads(experiment_to_json(experiment))
    payload["created_at_utc"] = "2026-10-30T12:00:00+02:00"
    with pytest.raises(ValueError, match="must use UTC"):
        experiment_from_json(json.dumps(payload))


def test_confidence_intervals_only_appear_at_minimum_denominator():
    from app.evaluation.metrics import _rate

    assert _rate(2, 3)["ci95_wilson"] is None
    assert _rate(20, 30)["ci95_wilson"] is not None


def test_experiment_warns_if_policy_runs_retrieve_different_evidence():
    evaluator = runner()
    question_id = next(q.id for q in evaluator._questions if q.split == "train")

    class DifferentEvidencePipeline:
        def __init__(self, policy_name):
            self.policy_name = policy_name

        def run(self, question):
            snippet = "retrieved text"
            evidence = EvidenceContext(
                f"chunk-{self.policy_name}",
                "doc-py311-datetime",
                snippet,
                0,
                len(snippet),
                retrieval_rank=1,
                retrieval_score=0.2,
                retrieval_method="bm25",
            )
            return RunResult(
                Decision.ABSTAIN,
                EvidenceAssessment(),
                ExecutionStatus.SUCCEEDED,
                abstention_reason=DecisionReason(
                    ReasonCode.INSUFFICIENT_EVIDENCE, "Not enough."
                ),
                retrieval=RetrievalMetadata("bm25", 1, (evidence,)),
                policy_name=self.policy_name,
            )

    experiment = evaluator.run(
        split="train",
        policies=[
            PolicyRunConfig("a", CaptureAbstainPolicy("a"), {}),
            PolicyRunConfig("b", CaptureAbstainPolicy("b"), {}),
        ],
        pipeline_factory=lambda policy, *_args: DifferentEvidencePipeline(policy.name),
        retrieval_configuration={"method": "bm25", "top_k": 1},
        generation_configuration={"provider": "mock"},
        question_ids=[question_id],
    )
    assert experiment.comparison_warnings
    assert question_id in experiment.comparison_warnings[0]
