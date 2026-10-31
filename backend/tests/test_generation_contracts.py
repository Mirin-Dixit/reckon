"""Tests for provider-neutral generation and evaluation contracts."""

import pytest
from app.generation.contracts import (
    ClaimCitation,
    Decision,
    DecisionReason,
    EvidenceAssessment,
    EvidenceContext,
    ExecutionStatus,
    GenerationRequest,
    GenerationResponse,
    ModelSettings,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
    ReasonCode,
    Relevance,
    RetrievalMetadata,
    RunResult,
    StructuredOutputSpec,
    Sufficiency,
    TokenUsage,
    validate_citations,
)


def evidence() -> EvidenceContext:
    return EvidenceContext(
        chunk_id="doc1_c0",
        document_id="doc1",
        text="Orders ship within five days.",
        start_char=100,
        end_char=129,
        title="Shipping policy",
        source_url="https://example.test/shipping",
        version="v2",
        source_date="2026-01-01",
        domain="shipping",
        retrieval_rank=1,
        retrieval_score=0.75,
        retrieval_method="hybrid_rrf",
    )


def test_decision_enum_has_exactly_three_values_and_rejects_invalid():
    assert {decision.value for decision in Decision} == {"ANSWER", "ABSTAIN", "CLARIFY"}
    with pytest.raises(ValueError):
        Decision("UNKNOWN")


def test_provider_neutral_request_and_response():
    request = GenerationRequest(
        system_instruction="Use evidence only.",
        user_content="When do orders ship?",
        model="model-x",
        settings=ModelSettings(temperature=0.0, seed=17, timeout_seconds=5),
        structured_output=StructuredOutputSpec(
            "response", {"type": "object", "properties": {"answer": {"type": "string"}}}
        ),
    )
    response = GenerationResponse(
        content='{"answer":"Within five days."}',
        structured_content={"answer": "Within five days."},
        metadata=ProviderMetadata(provider="mock", model=request.model),
        latency_ms=10.5,
        token_usage=TokenUsage(input_tokens=20, output_tokens=4, total_tokens=24),
    )
    assert request.settings.seed == 17
    assert request.structured_output is not None
    assert response.metadata.provider == "mock"


def test_evidence_context_metadata_offsets_and_invalid_ranges():
    item = evidence()
    assert item.title == "Shipping policy"
    assert item.end_char - item.start_char == len(item.text)
    with pytest.raises(ValueError, match="offset range must equal"):
        EvidenceContext(
            chunk_id="c",
            document_id="d",
            text="abc",
            start_char=0,
            end_char=4,
        )
    with pytest.raises(ValueError, match="positive integer"):
        EvidenceContext(
            chunk_id="c", document_id="d", text="abc", start_char=0, end_char=3,
            retrieval_rank=0,
        )


def test_assessment_keeps_relevance_and_sufficiency_separate():
    assessment = EvidenceAssessment(
        relevance=Relevance.RELEVANT,
        sufficiency=Sufficiency.PARTIAL,
        supporting_evidence_ids=("doc1_c0",),
        missing_premises=("Destination is not specified.",),
        contradictions=("One source says five days; another says seven days.",),
        unsupported_assumptions=("That the estimate guarantees delivery.",),
    )
    assert assessment.relevance is Relevance.RELEVANT
    assert assessment.sufficiency is Sufficiency.PARTIAL
    assert assessment.missing_premises
    assert assessment.contradictions


def test_citation_must_resolve_to_supplied_evidence_and_exact_quote():
    item = evidence()
    citation = ClaimCitation(
        claim="Orders ship within five days.",
        evidence_id=item.chunk_id,
        quote="ship within five days",
        start_char=107,
        end_char=128,
    )
    validate_citations([citation], [item])
    with pytest.raises(ValueError, match="unsupplied evidence"):
        validate_citations([ClaimCitation("claim", "missing", "x", 0, 1)], [item])
    bad_quote = ClaimCitation("claim", item.chunk_id, "wrong", 100, 105)
    with pytest.raises(ValueError, match="does not match"):
        validate_citations([bad_quote], [item])


def test_run_result_serializes_observed_fields_without_benchmark_expectations():
    item = evidence()
    result = RunResult(
        decision=Decision.ANSWER,
        answer="Orders ship within five days.",
        evidence_assessment=EvidenceAssessment(
            relevance=Relevance.RELEVANT,
            sufficiency=Sufficiency.SUFFICIENT,
            supporting_evidence_ids=(item.chunk_id,),
        ),
        execution_status=ExecutionStatus.SUCCEEDED,
        citations=(
            ClaimCitation("Orders ship within five days.", item.chunk_id,
                          "Orders ship within five days.", 100, 129),
        ),
        retrieval=RetrievalMetadata("hybrid_rrf", 5, (item,)),
        provider=ProviderMetadata("mock", "mock-model"),
        prompt_version="grounded-v1",
        observed_safe_behavior=True,
    )
    serialized = result.to_dict()
    assert serialized["decision"] == "ANSWER"
    assert serialized["execution_status"] == "succeeded"
    assert serialized["observed_safe_behavior"] is True
    assert "expected_safe_behavior" not in serialized
    assert "expected_answer" not in serialized


def test_expected_and_observed_safety_are_not_conflated():
    result = RunResult(
        decision=Decision.ABSTAIN,
        abstention_reason=DecisionReason(
            ReasonCode.INSUFFICIENT_EVIDENCE, "No support."
        ),
        evidence_assessment=EvidenceAssessment(sufficiency=Sufficiency.INSUFFICIENT),
        execution_status=ExecutionStatus.SUCCEEDED,
        observed_safe_behavior=True,
    )
    assert result.observed_safe_behavior is True
    assert not hasattr(result, "expected_safe_behavior")


def test_execution_failure_is_not_an_intentional_abstention():
    with pytest.raises(ValueError, match="must not carry a user decision"):
        RunResult(
            decision=Decision.ABSTAIN,
            abstention_reason=DecisionReason(ReasonCode.OTHER, "Provider failed."),
            evidence_assessment=EvidenceAssessment(),
            execution_status=ExecutionStatus.FAILED,
        )
    failed = RunResult(
        decision=None,
        evidence_assessment=EvidenceAssessment(),
        execution_status=ExecutionStatus.FAILED,
    )
    assert failed.decision is None
    error = ProviderError(ProviderErrorKind.TIMEOUT, "Timed out", retryable=True)
    assert error.kind is ProviderErrorKind.TIMEOUT
