"""Offline regression for the genuine P2 decision/reason inconsistency."""

import copy
import json

import pytest
import test_retrieval_http as http
from app.api.dependencies import PROMPT_VERSION
from app.generation.contracts import (
    ClaimCitation,
    Decision,
    ExecutionStatus,
    ReasonCode,
)
from app.generation.pipeline import GeneratedAnswer, MockAnswerGenerator
from app.generation.policies import PromptAbstentionPolicy
from fastapi.testclient import TestClient
from test_decision_policies import (
    MockProvider,
    assessment,
    context,
    pipeline_for,
    policy_payload,
)

environment = http.environment

ALLOWED = {
    "ANSWER": {"other"},
    "ABSTAIN": {"insufficient_evidence", "conflicting_evidence",
                "unsupported_premise", "out_of_scope", "other"},
    "CLARIFY": {"ambiguous_intent", "other"},
}


def payload_for(decision, reason, self_assessment=None):
    return {**policy_payload(
        decision=decision, reason_code=reason,
        support_ids=("chunk-1",) if decision == "ANSWER" else (),
        clarification="Which item do you mean?" if decision == "CLARIFY" else None,
    ), "self_assessment": self_assessment}


@pytest.mark.parametrize("decision", list(Decision))
@pytest.mark.parametrize("reason", list(ReasonCode))
@pytest.mark.parametrize("self_assessment", [None, .9])
def test_complete_decision_reason_matrix(decision, reason, self_assessment):
    payload = payload_for(decision.value, reason.value, self_assessment)
    original = copy.deepcopy(payload)
    policy = PromptAbstentionPolicy(MockProvider(payload), "mock")
    if reason.value in ALLOWED[decision.value]:
        selection = policy.decide("q", assessment(), (context(),))
        assert selection.decision is decision
        assert selection.reason.code is reason
        assert selection.scores[-1].value == self_assessment
        assert selection.scores[-1].availability == (
            "unavailable" if self_assessment is None else "available"
        )
    else:
        with pytest.raises(ValueError, match="inconsistent"):
            policy.decide("q", assessment(), (context(),))
    assert payload == original  # Rejection never silently remaps model output.


@pytest.mark.parametrize("retrieval", ["bm25", "dense", "hybrid"])
def test_recorded_live_answer_ambiguity_pair_is_rejected(retrieval):
    # Frozen fields from all three genuine prompt-policy responses. This fixture
    # does not rewrite the originals or depend on a machine-local artifact path.
    observed = {
        "decision": "ANSWER",
        "reason": (
            "The evidence shows that in Python 3.11, an aware current UTC datetime "
            "object can be obtained by calling datetime.now(timezone.utc). "
            "The documentation explicitly states this method."
        ),
        "reason_code": "ambiguous_intent",
        "supporting_evidence_ids": ["doc_py311_datetime_c0000"],
        "clarification_question": None,
        "self_assessment": .9,
    }
    before = copy.deepcopy(observed)
    policy = PromptAbstentionPolicy(MockProvider(observed), "qwen3:4b-q4_K_M")
    evidence = context(chunk_id="doc_py311_datetime_c0000",
                       method=http.SCORES[retrieval])
    with pytest.raises(ValueError, match="inconsistent"):
        policy.decide(
            "How can an aware current UTC datetime object be obtained in Python 3.11?",
            assessment(), (evidence,),
        )
    assert observed == before


@pytest.mark.parametrize("method", http.SCORES)
@pytest.mark.parametrize("decision,reason", [
    ("ANSWER", "ambiguous_intent"), ("ABSTAIN", "ambiguous_intent"),
    ("CLARIFY", "insufficient_evidence"),
])
def test_invalid_cross_decision_output_is_http_failure(environment, method,
                                                     decision, reason):
    runtime, app, _, _ = environment

    class BadReasonProvider(http.Provider):
        def generate(self, request):
            result = super().generate(request)
            payload = result.structured_content
            # Reuse supplied evidence IDs; only the reason pairing is invalid.
            payload.update(decision=decision, reason_code=reason,
                           self_assessment=None,
                           clarification_question="Which item?"
                           if decision == "CLARIFY" else None)
            return result

    provider = BadReasonProvider()
    runtime.provider = provider
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=http.request(
            method, "prompt_abstention",
        ))
    assert reply.status_code == 502
    assert reply.json()["error"]["execution_status"] == "failed"
    assert "decision" not in reply.json()
    assert len(provider.calls) == 1  # No answer generation after rejected selection.


def test_valid_abstention_null_score_is_success_not_failure():
    policy = PromptAbstentionPolicy(MockProvider(payload_for(
        "ABSTAIN", "insufficient_evidence",
    )), "mock")
    result = pipeline_for(policy).run("q")
    assert result.execution_status is ExecutionStatus.SUCCEEDED
    assert result.decision is Decision.ABSTAIN and result.answer is None
    assert result.scores[-1].value is None


def test_rejected_answer_pair_is_failure_not_abstention():
    policy = PromptAbstentionPolicy(MockProvider(payload_for(
        "ANSWER", "ambiguous_intent",
    )), "mock")
    result = pipeline_for(policy).run("q")
    assert result.execution_status is ExecutionStatus.FAILED
    assert result.decision is None and result.abstention_reason is None
    assert result.answer is None and result.citations == ()


def test_valid_answer_preserves_citations_and_null_self_assessment():
    policy = PromptAbstentionPolicy(
        MockProvider(payload_for("ANSWER", "other")), "mock",
    )
    pipeline = pipeline_for(policy)
    text = pipeline.documents["doc-1"].text
    pipeline.generator = MockAnswerGenerator(GeneratedAnswer(
        text, (ClaimCitation(text, "chunk-1", text, 0, len(text)),),
    ))
    result = pipeline.run("q")
    assert result.execution_status is ExecutionStatus.SUCCEEDED
    assert result.decision is Decision.ANSWER
    assert result.citations and result.scores[-1].value is None


def test_prompt_and_schema_describe_same_rules_and_version():
    provider = MockProvider(payload_for("ANSWER", "other"))
    policy = PromptAbstentionPolicy(provider, "mock")
    result = policy.decide("q", assessment(), (context(),))
    request = provider.requests[0]
    assert policy.PROMPT_VERSION == "prompt-decision-v3"
    assert PROMPT_VERSION == "api-v4"
    assert result.scores[-1].parameters["prompt_version"] == policy.PROMPT_VERSION
    assert "untrusted data" in request.system_instruction
    assert "ANSWER: other;" in request.system_instruction
    assert set(json.loads(request.user_content)) == {"question", "evidence"}
    reason_schema = request.structured_output.schema["properties"]["reason_code"]
    assert set(reason_schema["enum"]) == {reason.value for reason in ReasonCode}
    for decision, reasons in ALLOWED.items():
        rule = f"{decision}: {', '.join(sorted(reasons))}"
        assert rule in request.system_instruction
    assert "decision" in reason_schema["description"]
