"""P2 Batch 3: deterministic score contracts, policy semantics and provenance."""

import json
from dataclasses import asdict, replace

import pytest
import test_retrieval_http as http
from app.api.models import QueryResponse, ScoreResponse
from app.evaluation.serialization import experiment_from_json, experiment_to_json
from app.generation.contracts import (
    Decision,
    ExecutionStatus,
    ProviderError,
    ProviderErrorKind,
)
from app.generation.pipeline import PipelineConfig
from app.generation.policies import (
    AlwaysAnswerPolicy,
    MissingScoreDecision,
    PromptAbstentionPolicy,
    ThresholdAbstentionPolicy,
    ThresholdDirection,
    ThresholdScoreType,
)
from app.generation.scores import (
    ScoreKind,
    ScoreRole,
    ScoreSignal,
    ScoreSource,
    retrieval_signal,
    score_from_dict,
)
from fastapi.testclient import TestClient
from test_decision_policies import (
    MockProvider,
    assessment,
    context,
    pipeline_for,
    policy_payload,
)

environment = http.environment


def signal(kind="bm25", value=0.7, **kwargs):
    source = ScoreSource.MODEL if kind == "prompt_self_assessment" else (
        ScoreSource.RETRIEVAL
    )
    if source is ScoreSource.MODEL:
        kwargs.setdefault("role", ScoreRole.SELF_ASSESSMENT)
    return ScoreSignal(ScoreKind(kind), value, source,
                       None if source is ScoreSource.MODEL else kind, **kwargs)


@pytest.mark.parametrize("kind,value,parameters,lower,upper", [
    ("bm25", 0, {}, 0, None), ("bm25", 1e12, {}, 0, None),
    ("dense_cosine", -1, {}, -1, 1), ("dense_cosine", 1, {}, -1, 1),
    ("hybrid_rrf", .25, {"rrf_k": 7, "rank_lists": 2}, 0, .25),
    ("hybrid_rrf", .125, {"rrf_k": 7, "rank_lists": 1}, 0, .125),
    ("prompt_self_assessment", 0, {}, 0, 1),
    ("prompt_self_assessment", 1, {}, 0, 1),
])
def test_valid_ranges_and_json_roundtrip(kind, value, parameters, lower, upper):
    original = signal(kind, value, parameters=parameters)
    assert original.lower_bound == lower and original.upper_bound == upper
    assert original.calibration == "uncalibrated"
    assert original.availability == "available"
    payload = json.loads(json.dumps(asdict(original)))
    assert score_from_dict(payload) == original
    assert ScoreResponse.model_validate(payload).model_dump(mode="json") == payload


@pytest.mark.parametrize("kind,value,parameters", [
    ("bm25", -.001, {}), ("bm25", True, {}), ("bm25", float("nan"), {}),
    ("dense_cosine", 1.001, {}), ("dense_cosine", -1.001, {}),
    ("hybrid_rrf", .251, {"rrf_k": 7, "rank_lists": 2}),
    ("hybrid_rrf", .1, {}),
    ("hybrid_rrf", .1, {"rrf_k": True, "rank_lists": 2}),
    ("hybrid_rrf", .1, {"rrf_k": 60, "rank_lists": -1}),
    ("prompt_self_assessment", 1.001, {}),
    ("prompt_self_assessment", -.001, {}),
    ("prompt_self_assessment", "0.7", {}),
    ("prompt_self_assessment", float("inf"), {}),
])
def test_invalid_scores_rejected(kind, value, parameters):
    with pytest.raises(ValueError):
        signal(kind, value, parameters=parameters)


@pytest.mark.parametrize("kind", list(ScoreKind))
def test_missing_is_explicitly_unavailable_not_zero(kind):
    s = signal(kind.value, None, unavailable_reason="not_reported")
    assert s.value is None and s.availability == "unavailable"
    assert score_from_dict(json.loads(json.dumps(asdict(s)))) == s
    with pytest.raises(ValueError):
        signal(kind.value, None)


@pytest.mark.parametrize("kind,value,params", [
    ("bm25", .7, {}), ("dense_cosine", -.5, {}),
    ("hybrid_rrf", .02, {"rrf_k": 60, "rank_lists": 2}),
])
@pytest.mark.parametrize("direction", list(ThresholdDirection))
def test_exact_threshold_boundary_and_reported_comparison(
    kind, value, params, direction,
):
    evidence = (replace(context(value, kind), score=signal(kind, value,
                                                       parameters=params)),)
    policy = ThresholdAbstentionPolicy(ThresholdScoreType(kind), value, direction)
    selected = policy.decide("q", assessment(), evidence)
    assert selected.decision is Decision.ANSWER
    observed = selected.scores[0]
    assert observed.value == observed.threshold == value
    assert observed.threshold_direction == direction.value
    assert observed.role is ScoreRole.THRESHOLD_INPUT
    fail_value = (value - 1e-5 if direction is ThresholdDirection.AT_LEAST
                  else value + 1e-5)
    changed = replace(evidence[0], retrieval_score=fail_value,
                      score=signal(kind, fail_value, parameters=params))
    assert policy.decide("q", assessment(), (changed,)).decision is Decision.ABSTAIN


def test_observational_score_does_not_change_always_answer():
    for value in (0, None):
        selection = AlwaysAnswerPolicy().decide("q", assessment(), (context(value),))
        assert selection.decision is Decision.ANSWER
        assert selection.scores[0].role is ScoreRole.OBSERVATIONAL
        assert selection.scores[0].value == value


@pytest.mark.parametrize("decision,value", [("ANSWER", 0), ("ABSTAIN", 1),
                                            ("CLARIFY", 1), ("ANSWER", None)])
def test_self_assessment_never_overrides_selected_decision(decision, value):
    payload = policy_payload(decision, clarification="Which item?"
                             if decision == "CLARIFY" else None)
    payload["self_assessment"] = value
    provider = MockProvider(payload)
    selection = PromptAbstentionPolicy(provider, "mock").decide(
        "q", assessment(), (context(),),
    )
    assert selection.decision.value == decision
    observed = selection.scores[-1]
    assert observed.value == value and observed.calibration == "uncalibrated"
    assert observed.parameters["prompt_version"] == "prompt-decision-v3"
    assert "must not override" in provider.requests[0].system_instruction


@pytest.mark.parametrize("value", [True, "0.7", -1, 1.1, float("nan"),
                                  float("inf"), {}, []])
def test_invalid_model_self_assessments_are_execution_failures(value):
    payload = {**policy_payload(), "self_assessment": value}
    pipeline = pipeline_for(PromptAbstentionPolicy(MockProvider(payload), "mock"))
    result = pipeline.run("q")
    assert result.execution_status is ExecutionStatus.FAILED
    assert result.decision is None
    assert not any(s.kind is ScoreKind.SELF_ASSESSMENT for s in result.scores)


def test_missing_model_field_is_not_silently_defaulted():
    payload = policy_payload()
    del payload["self_assessment"]
    with pytest.raises(ValueError):
        PromptAbstentionPolicy(MockProvider(payload), "mock").decide(
            "q", assessment(), (context(),),
        )


def test_missing_chunk_score_preserves_threshold_action_and_null_value():
    policy = ThresholdAbstentionPolicy(ThresholdScoreType.BM25, .5)
    result = policy.decide("q", assessment(), (context(.7), context(None)))
    assert result.decision is Decision.ABSTAIN
    assert result.scores[0].value is None
    assert result.scores[0].unavailable_reason == "missing_chunk_score"


def test_empty_pipeline_reports_unavailable_score_without_claiming_absence():
    pipeline = pipeline_for(ThresholdAbstentionPolicy(ThresholdScoreType.BM25, .5))
    pipeline.retriever.chunks = []
    pipeline.config = PipelineConfig(retrieval_method="bm25")
    result = pipeline.run("q")
    assert result.decision is Decision.ABSTAIN
    assert result.scores[0].value is None
    assert result.scores[0].parameters == result.retrieval.parameters


@pytest.mark.parametrize("method", http.SCORES)
@pytest.mark.parametrize("policy", ["always_answer", "prompt_abstention", "threshold"])
def test_http_scores_and_provenance_all_nine(environment, method, policy):
    _, app, _, _ = environment
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=http.request(method, policy))
    assert reply.status_code == 200, reply.text
    body = reply.json()
    score = body["scores"][0]
    assert score["retrieval_method"] == http.SCORES[method]
    assert len(score["parameters"]["documents_fingerprint"]) == 64
    assert body["retrieved_evidence"][0]["score"]["value"] == score["value"]
    assert score["calibration"] == "uncalibrated"
    assert body["evidence_assessment"]["sufficiency"] == "not_assessed"
    if method != "bm25":
        assert score["parameters"]["embedding"]["digest"] == "a" * 64
        assert len(score["parameters"]["vector_fingerprint"]) == 64
    if policy == "threshold":
        assert score["role"] == "threshold_input" and score["threshold"] == -1
        assert score["value"] == body["policy_parameters"]["observed_aggregate_score"]
    elif policy == "prompt_abstention":
        assert body["scores"][1]["kind"] == "prompt_self_assessment"
        assert body["prompt_version"] == "api-v4"
    if method == "hybrid":
        assert score["upper_bound"] == 2 / 61
        assert score["parameters"]["effective_candidate_k"] == 50


def test_hybrid_bound_counts_only_nonempty_rank_lists(environment):
    runtime, _, _, _ = environment
    pipeline = http.pipeline(runtime, "hybrid", rrf_k=7)
    result = pipeline.run("zzzz-unmatched")
    assert result.execution_status is ExecutionStatus.SUCCEEDED
    score = result.scores[0]
    assert score.parameters["rank_lists"] == 1
    assert score.upper_bound == 1 / 8 and score.value == 1 / 8


def test_experiment_roundtrip_and_legacy_observations(environment):
    _, app, _, _ = environment
    with TestClient(app) as client:
        reply = client.post("/api/v1/evaluations", json={
            "split": "train", "question_ids": ["q_pilot_020"],
            "policies": [{"name": "always_answer"}],
        })
        assert reply.status_code == 200
        identifier = reply.json()["experiment_id"]
        observed = client.get(f"/api/v1/evaluations/{identifier}/results")
        assert observed.status_code == 200, observed.text
        record = app.state.experiment_registry.get(identifier)
    payload = experiment_from_json(experiment_to_json(record))
    run = payload["runs"][0]["observed"]
    assert run["scores"] and run["retrieval"]["scores"]
    assert "is_answerable" not in json.dumps(run["scores"])
    # Every new nested location is validated, not only the top-level signal.
    for target in (run["scores"][0], run["retrieval"]["scores"][0],
                   run["retrieval"]["evidence"][0]["score"]):
        original = target["calibration"]
        target["calibration"] = "calibrated"
        with pytest.raises(ValueError):
            experiment_from_json(json.dumps(payload))
        target["calibration"] = original
    # New optional fields do not invalidate older v2 records.
    run.pop("scores")
    run["retrieval"].pop("scores")
    for evidence in run["retrieval"]["evidence"]:
        evidence.pop("score")
    assert experiment_from_json(json.dumps(payload))["schema_version"].endswith("v2")


@pytest.mark.parametrize("field,value", [("value", -1), ("calibration", "calibrated"),
                                        ("upper_bound", 1), ("availability", "missing"),
                                        ("lower_bound", False)])
def test_corrupt_serialized_scores_rejected(field, value):
    payload = asdict(signal())
    payload[field] = value
    with pytest.raises(ValueError):
        score_from_dict(payload)


def test_legacy_query_response_without_scores_remains_valid(environment):
    _, app, _, _ = environment
    with TestClient(app) as client:
        body = client.post("/api/v1/query", json=http.request("bm25")).json()
    body.pop("scores")
    body.pop("retrieval_parameters")
    for evidence in body["retrieved_evidence"]:
        evidence.pop("score")
    assert QueryResponse.model_validate(body).scores == []


def test_mixed_missing_signal_does_not_become_zero():
    observed = retrieval_signal((context(None),))
    assert observed.value is None and observed.availability == "unavailable"


def test_valid_scores_survive_downstream_failure_without_a_decision():
    policy = PromptAbstentionPolicy(MockProvider(policy_payload()), "mock")
    pipeline = pipeline_for(policy)

    class FailedGenerator:
        def generate(self, question, evidence):
            raise ProviderError(ProviderErrorKind.TIMEOUT, "offline timeout")

    pipeline.generator = FailedGenerator()
    result = pipeline.run("q")
    assert result.decision is None and result.answer is None
    assert result.execution_status is ExecutionStatus.TIMED_OUT
    assert result.scores[-1].kind is ScoreKind.SELF_ASSESSMENT
    assert result.scores[-1].value == .75


def test_missing_score_action_answer_is_preserved_with_unavailable_signal():
    policy = ThresholdAbstentionPolicy(
        ThresholdScoreType.BM25, .5, missing_score_decision=MissingScoreDecision.ANSWER,
    )
    result = policy.decide("q", assessment(), (context(None),))
    assert result.decision is Decision.ANSWER
    assert result.scores[0].value is None
    assert result.scores[0].availability == "unavailable"
