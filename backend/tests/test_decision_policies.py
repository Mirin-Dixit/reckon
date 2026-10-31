"""Offline tests for the three Stage 3D decision baselines."""

import json

import pytest
from app.generation.contracts import (
    Decision,
    EvidenceAssessment,
    EvidenceContext,
    ExecutionStatus,
    GenerationResponse,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
    ReasonCode,
    Relevance,
    Sufficiency,
)
from app.generation.pipeline import (
    GeneratedAnswer,
    MockAnswerGenerator,
    MockEvidenceAssessor,
    PipelineConfig,
    RagPipeline,
)
from app.generation.policies import (
    AlwaysAnswerPolicy,
    MissingScoreDecision,
    PromptAbstentionPolicy,
    ThresholdAbstentionPolicy,
    ThresholdDirection,
    ThresholdScoreType,
)
from app.ingestion.chunking import Chunk
from app.ingestion.schema import Document
from app.retrieval.bm25 import ScoredChunk


class MockProvider:
    def __init__(self, payload=None, error: Exception | None = None, status=None):
        self.payload = payload
        self.error = error
        self.status = status or ExecutionStatus.SUCCEEDED
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return GenerationResponse(
            content=json.dumps(self.payload) if self.payload is not None else "",
            structured_content=self.payload,
            metadata=ProviderMetadata("mock", request.model, request_id="req-1"),
            status=self.status,
            latency_ms=12.0,
        )


def policy_payload(
    decision="ANSWER",
    support_ids=("chunk-1",),
    clarification=None,
    reason="The evidence supports this decision.",
    reason_code="other",
):
    return {
        "decision": decision,
        "reason": reason,
        "reason_code": reason_code,
        "supporting_evidence_ids": list(support_ids),
        "clarification_question": clarification,
    }


def context(
    score: float | None = 0.7,
    method: str = "bm25",
    chunk_id: str = "chunk-1",
    text: str = "Policy evidence.",
    start: int = 10,
) -> EvidenceContext:
    return EvidenceContext(
        chunk_id=chunk_id,
        document_id="doc-1",
        text=text,
        title="Policy",
        source_url="https://example.test/policy",
        start_char=start,
        end_char=start + len(text),
        retrieval_rank=1,
        retrieval_score=score,
        retrieval_method=method,
    )


def assessment(sufficiency=Sufficiency.SUFFICIENT):
    return EvidenceAssessment(
        relevance=Relevance.RELEVANT,
        sufficiency=sufficiency,
        supporting_evidence_ids=("chunk-1",),
        contradictions=("Two values conflict.",)
        if sufficiency is Sufficiency.CONTRADICTORY
        else (),
        missing_premises=("A required date is missing.",)
        if sufficiency is Sufficiency.PARTIAL
        else (),
    )


class StaticRetriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.calls = []

    def search(self, query: str, top_k: int = 5):
        self.calls.append((query, top_k))
        return self.chunks[:top_k]


class RecordingPolicy:
    def __init__(self, policy):
        self.policy = policy
        self.inputs = []

    def decide(self, question, evidence_assessment, evidence):
        self.inputs.append((question, evidence_assessment, evidence))
        return self.policy.decide(question, evidence_assessment, evidence)


def pipeline_for(policy):
    text = "The account renews annually."
    doc = Document(
        id="doc-1",
        title="Policy",
        source_url="https://example.test/policy",
        text=text,
    )
    chunk = Chunk("chunk-1", doc.id, 0, 0, len(text), text)
    return RagPipeline(
        retriever=StaticRetriever([ScoredChunk(chunk, 0.7)]),
        documents={doc.id: doc},
        assessor=MockEvidenceAssessor(assessment()),
        policy=policy,
        generator=MockAnswerGenerator(GeneratedAnswer("Annual renewal.", ())),
        config=PipelineConfig(top_k=3, retrieval_method="bm25"),
    )


def test_always_answer_ignores_insufficient_or_contradictory_assessment():
    policy = AlwaysAnswerPolicy()
    result = policy.decide("question", assessment(Sufficiency.INSUFFICIENT), ())
    assert result.decision is Decision.ANSWER
    assert result.policy_name == "always_answer"
    assert "evidence" in result.reason.explanation
    contradictory = policy.decide(
        "question", assessment(Sufficiency.CONTRADICTORY), ()
    )
    assert contradictory.decision is Decision.ANSWER


def test_prompt_policy_requires_structured_output_and_validates_answer_ids():
    provider = MockProvider(policy_payload())
    policy = PromptAbstentionPolicy(provider, model="mock-model")
    supplied = context()
    selection = policy.decide("When?", assessment(), (supplied,))
    request = provider.requests[0]
    serialized_user = json.loads(request.user_content)
    assert serialized_user["question"] == "When?"
    assert serialized_user["evidence"][0]["evidence_id"] == supplied.chunk_id
    assert "expected_answer" not in request.user_content
    assert request.structured_output is not None
    assert request.structured_output.strict is True
    assert selection.decision is Decision.ANSWER
    assert selection.reason.explanation == "The evidence supports this decision."
    assert selection.policy_name == "prompt_based_abstention"
    assert selection.provider.provider == "mock"


@pytest.mark.parametrize(
    "payload",
    [
        {**policy_payload(), "decision": "MAYBE"},
        {key: value for key, value in policy_payload().items() if key != "reason"},
        policy_payload(support_ids=("not-supplied",)),
        policy_payload(support_ids=()),
        policy_payload(decision="CLARIFY", support_ids=(), clarification=None),
        {**policy_payload(), "unexpected": "field"},
    ],
)
def test_prompt_policy_rejects_invalid_structured_output(payload):
    provider = MockProvider(payload)
    policy = PromptAbstentionPolicy(provider, "mock-model")
    with pytest.raises(ValueError):
        policy.decide("question", assessment(), (context(),))


@pytest.mark.parametrize(
    ("decision", "clarification", "reason_code"),
    [
        ("ABSTAIN", None, "insufficient_evidence"),
        ("CLARIFY", "Which renewal do you mean?", "ambiguous_intent"),
    ],
)
def test_prompt_policy_supports_abstain_and_clarify(
    decision, clarification, reason_code
):
    payload = policy_payload(
        decision=decision,
        support_ids=(),
        clarification=clarification,
        reason_code=reason_code,
    )
    selected = PromptAbstentionPolicy(MockProvider(payload), "mock").decide(
        "Question?", assessment(), (context(),)
    )
    assert selected.decision.value == decision
    if decision == "CLARIFY":
        assert selected.clarification_question == clarification
    else:
        assert selected.reason.code is ReasonCode.INSUFFICIENT_EVIDENCE


def test_prompt_provider_timeout_and_failure_are_not_abstentions():
    provider = MockProvider(error=ProviderError(ProviderErrorKind.TIMEOUT, "late"))
    with pytest.raises(ProviderError):
        PromptAbstentionPolicy(provider, "mock").decide(
            "Question?", assessment(), (context(),)
        )
    failed_response_provider = MockProvider(
        policy_payload(), status=ExecutionStatus.TIMED_OUT
    )
    with pytest.raises(ProviderError):
        PromptAbstentionPolicy(failed_response_provider, "mock").decide(
            "Question?", assessment(), (context(),)
        )


@pytest.mark.parametrize(
    ("score", "threshold", "direction", "expected"),
    [
        (0.5, 0.5, ThresholdDirection.AT_LEAST, Decision.ANSWER),
        (0.49, 0.5, ThresholdDirection.AT_LEAST, Decision.ABSTAIN),
        (0.5, 0.5, ThresholdDirection.AT_MOST, Decision.ANSWER),
        (0.51, 0.5, ThresholdDirection.AT_MOST, Decision.ABSTAIN),
    ],
)
def test_threshold_boundary_and_direction(score, threshold, direction, expected):
    policy = ThresholdAbstentionPolicy(
        ThresholdScoreType.BM25, threshold, direction
    )
    selection = policy.decide("Q", assessment(), (context(score),))
    assert selection.decision is expected
    assert selection.policy_parameters["observed_aggregate_score"] == score
    assert selection.policy_parameters["threshold"] == threshold
    assert selection.policy_parameters["aggregation"] == "max"


def test_threshold_uses_max_and_preserves_contradictions_and_partial_assessment():
    policy = ThresholdAbstentionPolicy(ThresholdScoreType.BM25, 0.6)
    contexts = (context(0.2), context(0.8, chunk_id="chunk-2"))
    selection = policy.decide(
        "Q", assessment(Sufficiency.CONTRADICTORY), contexts
    )
    assert selection.decision is Decision.ANSWER
    assert selection.policy_parameters["observed_aggregate_score"] == 0.8
    assert assessment(Sufficiency.PARTIAL).missing_premises
    assert assessment(Sufficiency.CONTRADICTORY).contradictions


@pytest.mark.parametrize("evidence", [(), (context(None),)])
def test_threshold_handles_empty_and_missing_scores_explicitly(evidence):
    abstain = ThresholdAbstentionPolicy(ThresholdScoreType.BM25, 0.5)
    selection = abstain.decide("Q", assessment(), evidence)
    assert selection.decision is Decision.ABSTAIN
    assert selection.policy_parameters["observed_aggregate_score"] is None
    assert selection.policy_parameters["missing_score_decision"] == "ABSTAIN"
    answer = ThresholdAbstentionPolicy(
        ThresholdScoreType.BM25,
        0.5,
        missing_score_decision=MissingScoreDecision.ANSWER,
    ).decide("Q", assessment(), evidence)
    assert answer.decision is Decision.ANSWER


def test_threshold_rejects_mixed_score_family_and_does_not_call_score_confidence():
    policy = ThresholdAbstentionPolicy(ThresholdScoreType.BM25, 0.5)
    with pytest.raises(ValueError, match="cannot use other retrieval methods"):
        policy.decide("Q", assessment(), (context(0.8, method="hybrid_rrf"),))


def test_pipeline_records_policy_name_parameters_and_prompt_provider_metadata():
    provider = MockProvider(policy_payload())
    prompt_policy = PromptAbstentionPolicy(provider, "mock-model")
    result = pipeline_for(prompt_policy).run("Is this annual?")
    assert result.decision is Decision.ANSWER
    assert result.policy_name == "prompt_based_abstention"
    assert result.policy_parameters["model"] == "mock-model"
    assert result.provider.provider == "mock"
    assert result.latency_ms == 12.0

    threshold_result = pipeline_for(
        ThresholdAbstentionPolicy(ThresholdScoreType.BM25, 0.6)
    ).run("Is this annual?")
    assert threshold_result.policy_name == "threshold_based_abstention"
    assert threshold_result.policy_parameters[
        "observed_aggregate_score"
    ] == pytest.approx(0.7)


def test_all_policies_receive_identical_question_assessment_and_evidence():
    policies = [
        AlwaysAnswerPolicy(),
        PromptAbstentionPolicy(MockProvider(policy_payload()), "mock"),
        ThresholdAbstentionPolicy(ThresholdScoreType.BM25, 0.6),
    ]
    recorders = [RecordingPolicy(policy) for policy in policies]
    results = [pipeline_for(policy).run("same user question") for policy in recorders]
    inputs = [recorder.inputs[0] for recorder in recorders]
    assert all(item[0] == "same user question" for item in inputs)
    assert inputs[0][1] == inputs[1][1] == inputs[2][1]
    assert inputs[0][2] == inputs[1][2] == inputs[2][2]
    assert {result.policy_name for result in results} == {
        "always_answer",
        "prompt_based_abstention",
        "threshold_based_abstention",
    }


def test_prompt_timeout_in_pipeline_has_no_decision_and_is_not_abstention():
    policy = PromptAbstentionPolicy(
        MockProvider(error=ProviderError(ProviderErrorKind.TIMEOUT, "late")), "mock"
    )
    result = pipeline_for(policy).run("Question")
    assert result.decision is None
    assert result.execution_status is ExecutionStatus.TIMED_OUT
    assert result.abstention_reason is None
