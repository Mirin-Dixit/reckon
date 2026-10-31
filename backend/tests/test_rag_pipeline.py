"""Deterministic end-to-end tests for in-process RAG orchestration."""

import pytest
from app.generation.contracts import (
    ClaimCitation,
    Decision,
    DecisionReason,
    EvidenceAssessment,
    ExecutionStatus,
    ProviderError,
    ProviderErrorKind,
    ReasonCode,
    Relevance,
    Sufficiency,
)
from app.generation.pipeline import (
    DecisionSelection,
    FixedDecisionPolicy,
    GeneratedAnswer,
    MockAnswerGenerator,
    MockEvidenceAssessor,
    PipelineConfig,
    RagPipeline,
)
from app.ingestion.chunking import Chunk
from app.ingestion.schema import Document
from app.retrieval.bm25 import BM25Index, ScoredChunk
from app.retrieval.hybrid import HybridIndex

TEXT = "The service is active. Renewal happens yearly."


class FixedEmbedder:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        return [1.0, 0.0]


class StaticRetriever:
    def __init__(self, results: list[ScoredChunk]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        self.calls.append((query, top_k))
        return self.results[:top_k]


def setup_pipeline(
    decision: Decision,
    assessment: EvidenceAssessment | None = None,
    retriever=None,
    citations: tuple[ClaimCitation, ...] | None = None,
    retrieval_method: str = "bm25",
):
    document = Document(
        id="doc1",
        title="Service terms",
        source_url="https://example.test/terms",
        text=TEXT,
        version="v3",
        source_date="2026-05-01",
        domain="service",
        contains_injection=True,
        injection_spans=((0, 10),),
    )
    chunk = Chunk("doc1_c0", "doc1", 0, 0, len(TEXT), TEXT)
    active_retriever = retriever or StaticRetriever([ScoredChunk(chunk, 0.42)])
    selected_citations = citations
    if selected_citations is None:
        selected_citations = (
            ClaimCitation("The service is active.", chunk.chunk_id, TEXT[:23], 0, 23),
        )
    generator = MockAnswerGenerator(
        GeneratedAnswer("The service is active.", selected_citations)
    )
    actual_assessment = assessment or EvidenceAssessment(
        relevance=Relevance.RELEVANT,
        sufficiency=Sufficiency.SUFFICIENT,
        supporting_evidence_ids=(chunk.chunk_id,),
    )
    assessor = MockEvidenceAssessor(actual_assessment)
    policy = FixedDecisionPolicy(
        DecisionSelection(
            decision,
            reason=(
                None
                if decision is not Decision.ABSTAIN
                else DecisionReason(
                    ReasonCode.INSUFFICIENT_EVIDENCE, "Not supported."
                )
            ),
            clarification_question=(
                "Which meaning do you intend?"
                if decision is Decision.CLARIFY
                else None
            ),
        )
    )
    pipeline = RagPipeline(
        active_retriever,
        {document.id: document},
        assessor,
        policy,
        generator,
        PipelineConfig(
            top_k=2,
            retrieval_method=retrieval_method,
            prompt_version="mock-test-v1",
        ),
    )
    return pipeline, document, chunk, active_retriever, assessor, policy, generator


def test_bm25_integration_constructs_traceable_context_and_offsets():
    document = Document(
        id="doc1", title="Service terms", source_url="https://example.test/terms",
        text=TEXT, version="v3", source_date="2026-05-01", domain="service",
    )
    chunks = [Chunk("doc1_c0", document.id, 0, 0, len(TEXT), TEXT)]
    pipeline, _, _, retriever, _, _, _ = setup_pipeline(
        Decision.ANSWER, retriever=BM25Index(chunks)
    )
    result = pipeline.run("service active")
    assert result.decision is Decision.ANSWER
    context = result.retrieval.evidence[0]
    assert context.text == document.text[context.start_char : context.end_char]
    assert context.title == document.title
    assert context.source_url == document.source_url
    assert context.version == document.version
    assert context.source_date == document.source_date
    assert context.domain == document.domain
    assert context.retrieval_rank == 1
    assert context.retrieval_score > 0
    assert context.retrieval_method == "bm25"
    assert retriever.search("service active", top_k=2)


def test_hybrid_retrieval_integrates_without_retrieval_changes():
    document = Document(
        id="doc1", title="Service terms", source_url="https://example.test/terms",
        text=TEXT,
    )
    chunk = Chunk("doc1_c0", document.id, 0, 0, len(TEXT), TEXT)
    hybrid = HybridIndex.from_chunks([chunk], FixedEmbedder())
    pipeline, _, _, _, _, _, _ = setup_pipeline(
        Decision.ANSWER, retriever=hybrid, retrieval_method="hybrid_rrf"
    )
    result = pipeline.run("service active")
    assert result.decision is Decision.ANSWER
    assert result.retrieval.method == "hybrid_rrf"
    assert result.retrieval.evidence[0].retrieval_score > 0


def test_all_three_decisions_and_generation_only_for_answer():
    answer, *_answer_components = setup_pipeline(Decision.ANSWER)
    answer_result = answer.run("Is service active?")
    assert answer_result.decision is Decision.ANSWER
    assert answer_result.answer == "The service is active."
    assert len(answer_result.citations) == 1
    assert len(_answer_components[-1].calls) == 1

    abstain, *abstain_components = setup_pipeline(Decision.ABSTAIN)
    abstain_result = abstain.run("What is not in evidence?")
    assert abstain_result.decision is Decision.ABSTAIN
    assert abstain_result.abstention_reason is not None
    assert abstain_components[-1].calls == []

    clarify, *clarify_components = setup_pipeline(Decision.CLARIFY)
    clarify_result = clarify.run("Which one?")
    assert clarify_result.decision is Decision.CLARIFY
    assert clarify_result.clarification_question == "Which meaning do you intend?"
    assert clarify_components[-1].calls == []


@pytest.mark.parametrize(
    ("sufficiency", "assessment_updates"),
    [
        (Sufficiency.SUFFICIENT, {}),
        (Sufficiency.PARTIAL, {"missing_premises": ("Start date is absent.",)}),
        (Sufficiency.INSUFFICIENT, {"missing_premises": ("No renewal term.",)}),
        (
            Sufficiency.CONTRADICTORY,
            {"contradictions": ("Sources give different terms.",)},
        ),
    ],
)
def test_assessment_outcomes_preserved(sufficiency, assessment_updates):
    assessment = EvidenceAssessment(
        relevance=Relevance.RELEVANT,
        sufficiency=sufficiency,
        **assessment_updates,
    )
    pipeline, *_ = setup_pipeline(Decision.ABSTAIN, assessment)
    result = pipeline.run("What is the term?")
    assert result.evidence_assessment.sufficiency is sufficiency
    assert result.evidence_assessment.missing_premises or sufficiency not in (
        Sufficiency.PARTIAL,
        Sufficiency.INSUFFICIENT,
    )
    assert result.evidence_assessment.contradictions or (
        sufficiency is not Sufficiency.CONTRADICTORY
    )


def test_clarification_assessment_and_missing_premises_are_retained():
    assessment = EvidenceAssessment(
        relevance=Relevance.RELEVANT,
        sufficiency=Sufficiency.PARTIAL,
        missing_premises=("The user did not identify which renewal.",),
        ambiguity_requiring_clarification="Renewal can refer to two terms.",
    )
    pipeline, *_ = setup_pipeline(Decision.CLARIFY, assessment)
    result = pipeline.run("What is the renewal?")
    assert result.decision is Decision.CLARIFY
    assert result.evidence_assessment.ambiguity_requiring_clarification
    assert result.evidence_assessment.missing_premises


@pytest.mark.parametrize(
    "citation",
    [
        ClaimCitation("claim", "unknown", "abc", 0, 3),
        ClaimCitation("claim", "doc1_c0", "wrong", 0, 5),
        ClaimCitation("claim", "doc1_c0", "yearly", 100, 106),
    ],
)
def test_invalid_generator_citations_become_execution_failures(citation):
    pipeline, *_ = setup_pipeline(Decision.ANSWER, citations=(citation,))
    result = pipeline.run("Question")
    assert result.decision is None
    assert result.execution_status is ExecutionStatus.FAILED


def test_empty_retrieval_can_abstain_without_inference_from_score():
    assessment = EvidenceAssessment(
        relevance=Relevance.NOT_ASSESSED,
        sufficiency=Sufficiency.INSUFFICIENT,
        missing_premises=("No retrieved evidence.",),
    )
    pipeline, _, _, _, _, _, generator = setup_pipeline(
        Decision.ABSTAIN,
        assessment,
        retriever=StaticRetriever([]),
    )
    result = pipeline.run("Question with no matches")
    assert result.decision is Decision.ABSTAIN
    assert result.retrieval.evidence == ()
    assert generator.calls == []


def test_injection_metadata_survives_and_is_visible_to_assessor():
    pipeline, _, _, _, assessor, _, _ = setup_pipeline(Decision.ABSTAIN)
    result = pipeline.run("Question")
    context = result.retrieval.evidence[0]
    assert context.contains_injection is True
    assert assessor.calls[0][1][0].contains_injection is True


def test_execution_errors_are_separate_and_return_no_decision():
    class BrokenRetriever:
        def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
            raise ProviderError(ProviderErrorKind.TIMEOUT, "timed out")

    pipeline, _, _, _, _, _, generator = setup_pipeline(
        Decision.ANSWER, retriever=BrokenRetriever()
    )
    result = pipeline.run("Question")
    assert result.decision is None
    assert result.execution_status is ExecutionStatus.TIMED_OUT
    assert generator.calls == []


def test_runtime_accepts_question_text_not_benchmark_ground_truth_record():
    pipeline, *_ = setup_pipeline(Decision.ABSTAIN)
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        pipeline.run(object())  # type: ignore[arg-type]


def test_offset_mismatch_is_rejected_before_assessment():
    document = Document(
        id="doc1", title="Service terms", source_url="https://example.test/terms",
        text=TEXT,
    )
    wrong_chunk = Chunk("doc1_c0", document.id, 0, 1, len(TEXT), TEXT)
    pipeline, _, _, _, assessor, _, _ = setup_pipeline(
        Decision.ABSTAIN,
        retriever=StaticRetriever([ScoredChunk(wrong_chunk, 0.5)]),
    )
    result = pipeline.run("Question")
    assert result.decision is None
    assert result.execution_status is ExecutionStatus.FAILED
    assert assessor.calls == []
