"""In-process, injectable RAG orchestration for deterministic experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.generation.contracts import (
    ClaimCitation,
    Decision,
    DecisionReason,
    EvidenceAssessment,
    EvidenceContext,
    ExecutionStatus,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
    RetrievalMetadata,
    RunResult,
    TokenUsage,
    validate_citations,
)
from app.ingestion.chunking import Chunk
from app.ingestion.schema import Document
from app.retrieval.bm25 import ScoredChunk


class Retriever(Protocol):
    """Structural interface satisfied by BM25Index and HybridIndex."""

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Return ranked chunks paired with retrieval scores."""
        ...


class EvidenceAssessor(Protocol):
    """Assess evidence independently of retrieval ranking."""

    def assess(
        self, question: str, evidence: tuple[EvidenceContext, ...]
    ) -> EvidenceAssessment:
        """Return an evidence assessment; no benchmark labels are supplied."""
        ...


@dataclass(frozen=True)
class DecisionSelection:
    """A policy's outcome and the user-facing details required by that outcome."""

    decision: Decision
    reason: DecisionReason | None = None
    clarification_question: str | None = None
    policy_name: str = "fixed"
    policy_parameters: dict[str, object] | None = None
    provider: ProviderMetadata | None = None
    latency_ms: float | None = None
    token_usage: TokenUsage | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.decision, Decision):
            raise ValueError("decision must be a Decision value")
        if self.decision is Decision.ABSTAIN and self.reason is None:
            raise ValueError("ABSTAIN requires a decision reason")
        if self.decision is Decision.CLARIFY and not self.clarification_question:
            raise ValueError("CLARIFY requires a specific clarification question")
        if self.decision is Decision.ANSWER and self.clarification_question is not None:
            raise ValueError(
                "ANSWER cannot include clarification details"
            )
        if not self.policy_name.strip():
            raise ValueError("policy_name must be non-empty")


class DecisionPolicy(Protocol):
    """Select an outcome without binding orchestration to a particular policy."""

    def decide(
        self,
        question: str,
        assessment: EvidenceAssessment,
        evidence: tuple[EvidenceContext, ...],
    ) -> DecisionSelection:
        """Return one deterministic or learned decision selection."""
        ...


@dataclass(frozen=True)
class GeneratedAnswer:
    """Mock generator output with citations attached to its claims."""

    answer: str
    citations: tuple[ClaimCitation, ...]
    unsupported_premises: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    provider: ProviderMetadata | None = None
    latency_ms: float | None = None
    token_usage: TokenUsage | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.answer, str) or not self.answer.strip():
            raise ValueError("answer must be a non-empty string")


class AnswerGenerator(Protocol):
    """Generate only when the decision policy selects ANSWER."""

    def generate(
        self, question: str, evidence: tuple[EvidenceContext, ...]
    ) -> GeneratedAnswer:
        """Return a grounded answer and claim citations."""
        ...


@dataclass(frozen=True)
class PipelineConfig:
    top_k: int = 5
    retrieval_method: str = "custom"
    prompt_version: str = "mock-v1"

    def __post_init__(self) -> None:
        if type(self.top_k) is not int or self.top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if not self.retrieval_method.strip():
            raise ValueError("retrieval_method must be non-empty")
        if not self.prompt_version.strip():
            raise ValueError("prompt_version must be non-empty")


class MockEvidenceAssessor:
    """Return configured assessments deterministically; not model intelligence."""

    def __init__(
        self,
        assessment: EvidenceAssessment | dict[str, EvidenceAssessment],
        default: EvidenceAssessment | None = None,
    ) -> None:
        self._assessment = assessment
        self._default = default
        self.calls: list[tuple[str, tuple[EvidenceContext, ...]]] = []

    def assess(
        self, question: str, evidence: tuple[EvidenceContext, ...]
    ) -> EvidenceAssessment:
        self.calls.append((question, evidence))
        if isinstance(self._assessment, EvidenceAssessment):
            return self._assessment
        result = self._assessment.get(question, self._default)
        if result is None:
            raise KeyError(f"No mock assessment configured for question: {question}")
        return result


class FixedDecisionPolicy:
    """Deterministic test policy returning a preconfigured outcome."""

    def __init__(self, selection: DecisionSelection) -> None:
        self.selection = selection
        self.calls = 0

    def decide(
        self,
        question: str,
        assessment: EvidenceAssessment,
        evidence: tuple[EvidenceContext, ...],
    ) -> DecisionSelection:
        self.calls += 1
        return self.selection


class MockAnswerGenerator:
    """Return configured answer content and expose supplied evidence for tests."""

    def __init__(self, generated: GeneratedAnswer) -> None:
        self.generated = generated
        self.calls: list[tuple[str, tuple[EvidenceContext, ...]]] = []

    def generate(
        self, question: str, evidence: tuple[EvidenceContext, ...]
    ) -> GeneratedAnswer:
        self.calls.append((question, evidence))
        return self.generated


class RagPipeline:
    """Connect existing retrieval to injectable assessment, policy, and generation."""

    def __init__(
        self,
        retriever: Retriever,
        documents: dict[str, Document],
        assessor: EvidenceAssessor,
        policy: DecisionPolicy,
        generator: AnswerGenerator,
        config: PipelineConfig | None = None,
    ) -> None:
        self.retriever = retriever
        self.documents = dict(documents)
        self.assessor = assessor
        self.policy = policy
        self.generator = generator
        self.config = config or PipelineConfig()

    def run(self, question: str) -> RunResult:
        """Run one user question; benchmark Question objects are never accepted."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")

        assessment = EvidenceAssessment()
        retrieval: RetrievalMetadata | None = None
        try:
            scored_chunks = self.retriever.search(
                question, top_k=self.config.top_k
            )
            contexts = tuple(
                self._to_context(scored, rank)
                for rank, scored in enumerate(scored_chunks, start=1)
            )
            retrieval = RetrievalMetadata(
                method=self.config.retrieval_method,
                top_k=self.config.top_k,
                evidence=contexts,
            )
            assessment = self.assessor.assess(question, contexts)
            selection = self.policy.decide(question, assessment, contexts)

            if selection.decision is Decision.ABSTAIN:
                return RunResult(
                    decision=Decision.ABSTAIN,
                    abstention_reason=selection.reason,
                    decision_reason=selection.reason,
                    evidence_assessment=assessment,
                    execution_status=ExecutionStatus.SUCCEEDED,
                    retrieval=retrieval,
                    policy_name=selection.policy_name,
                    policy_parameters=selection.policy_parameters or {},
                    provider=selection.provider,
                    latency_ms=selection.latency_ms,
                    token_usage=selection.token_usage,
                    prompt_version=self.config.prompt_version,
                )
            if selection.decision is Decision.CLARIFY:
                return RunResult(
                    decision=Decision.CLARIFY,
                    clarification_question=selection.clarification_question,
                    decision_reason=selection.reason,
                    evidence_assessment=assessment,
                    execution_status=ExecutionStatus.SUCCEEDED,
                    retrieval=retrieval,
                    policy_name=selection.policy_name,
                    policy_parameters=selection.policy_parameters or {},
                    provider=selection.provider,
                    latency_ms=selection.latency_ms,
                    token_usage=selection.token_usage,
                    prompt_version=self.config.prompt_version,
                )

            generated = self.generator.generate(question, contexts)
            validate_citations(generated.citations, contexts)
            return RunResult(
                decision=Decision.ANSWER,
                answer=generated.answer,
                unsupported_premises=generated.unsupported_premises,
                surfaced_contradictions=generated.contradictions,
                citations=generated.citations,
                decision_reason=selection.reason,
                evidence_assessment=assessment,
                execution_status=ExecutionStatus.SUCCEEDED,
                retrieval=retrieval,
                policy_name=selection.policy_name,
                policy_parameters=selection.policy_parameters or {},
                provider=generated.provider or selection.provider
                or ProviderMetadata(provider="mock", model="mock"),
                latency_ms=(
                    generated.latency_ms
                    if generated.latency_ms is not None
                    else selection.latency_ms
                ),
                token_usage=_combined_usage(
                    selection.token_usage, generated.token_usage
                ),
                prompt_version=self.config.prompt_version,
            )
        except Exception as error:
            status = _execution_status(error)
            return RunResult(
                decision=None,
                evidence_assessment=assessment,
                execution_status=status,
                retrieval=retrieval,
                policy_name=type(self.policy).__name__,
                prompt_version=self.config.prompt_version,
            )

    def _to_context(self, scored: ScoredChunk, rank: int) -> EvidenceContext:
        chunk: Chunk = scored.chunk
        document = self.documents.get(chunk.doc_id)
        if document is None:
            raise ValueError(
                f"No document metadata for retrieved chunk: {chunk.doc_id}"
            )
        if chunk.end_char > len(document.text):
            raise ValueError(f"Chunk offsets exceed document text: {chunk.chunk_id}")
        if document.text[chunk.start_char : chunk.end_char] != chunk.text:
            raise ValueError(
                f"Chunk text does not match document offsets: {chunk.chunk_id}"
            )
        overlaps_injection = any(
            chunk.start_char < end and start < chunk.end_char
            for start, end in document.injection_spans
        )
        return EvidenceContext(
            chunk_id=chunk.chunk_id,
            document_id=document.id,
            text=chunk.text,
            title=document.title,
            source_url=document.source_url,
            version=document.version,
            source_date=document.source_date,
            domain=document.domain,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            retrieval_rank=rank,
            retrieval_score=float(scored.score),
            retrieval_method=self.config.retrieval_method,
            contains_injection=document.contains_injection or overlaps_injection,
        )


def _combined_usage(
    first: TokenUsage | None, second: TokenUsage | None
) -> TokenUsage | None:
    """Combine reported decision and answer usage; never invent missing counts."""
    if first is None:
        return second
    if second is None:
        return first

    def total(name: str) -> int | None:
        left, right = getattr(first, name), getattr(second, name)
        return left + right if left is not None and right is not None else None

    return TokenUsage(
        input_tokens=total("input_tokens"),
        output_tokens=total("output_tokens"),
        total_tokens=total("total_tokens"),
    )


def _execution_status(error: Exception) -> ExecutionStatus:
    if isinstance(error, ProviderError):
        return {
            ProviderErrorKind.TIMEOUT: ExecutionStatus.TIMED_OUT,
            ProviderErrorKind.REFUSAL: ExecutionStatus.REFUSED,
            ProviderErrorKind.INCOMPLETE: ExecutionStatus.INCOMPLETE,
        }.get(error.kind, ExecutionStatus.FAILED)
    return ExecutionStatus.FAILED
