"""Provider-neutral contracts for grounded generation and evaluation runs.

These models deliberately contain observed runtime data only. Benchmark labels and
expected answers remain in the benchmark schema and must not be passed to providers.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import StrEnum
from typing import Any, Protocol, TypeAlias


class Decision(StrEnum):
    """The three user-facing outcomes supported by the RAG system."""

    ANSWER = "ANSWER"
    ABSTAIN = "ABSTAIN"
    CLARIFY = "CLARIFY"


class Relevance(StrEnum):
    """How closely retrieved evidence relates to the request."""

    RELEVANT = "relevant"
    PARTIALLY_RELEVANT = "partially_relevant"
    IRRELEVANT = "irrelevant"
    NOT_ASSESSED = "not_assessed"


class Sufficiency(StrEnum):
    """Whether the evidence establishes the facts needed to respond."""

    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"
    CONTRADICTORY = "contradictory"
    NOT_ASSESSED = "not_assessed"


class ExecutionStatus(StrEnum):
    """Execution outcome, distinct from an intentional ABSTAIN decision."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    REFUSED = "refused"
    INCOMPLETE = "incomplete"


class ProviderErrorKind(StrEnum):
    """Provider-neutral categories for adapter-normalized failures."""

    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    INVALID_REQUEST = "invalid_request"
    RATE_LIMIT = "rate_limit"
    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    REFUSAL = "refusal"
    INCOMPLETE = "incomplete"
    MALFORMED_RESPONSE = "malformed_response"
    UNKNOWN = "unknown"


def _non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _finite_or_none(value: float | None, name: str) -> None:
    if value is not None and (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite number or None")


@dataclass(frozen=True)
class ModelSettings:
    """Provider-independent settings; unsupported options are adapter-defined."""

    temperature: float | None = None
    seed: int | None = None
    max_output_tokens: int | None = None
    timeout_seconds: float = 30.0
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _finite_or_none(self.temperature, "temperature")
        if self.temperature is not None and self.temperature < 0:
            raise ValueError("temperature must be non-negative")
        if self.seed is not None and (type(self.seed) is not int):
            raise ValueError("seed must be an integer or None")
        if self.max_output_tokens is not None and (
            type(self.max_output_tokens) is not int or self.max_output_tokens <= 0
        ):
            raise ValueError("max_output_tokens must be a positive integer or None")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive finite number")


@dataclass(frozen=True)
class StructuredOutputSpec:
    """Named JSON Schema requirement passed through without provider SDK types."""

    name: str
    schema: dict[str, Any]
    strict: bool = True

    def __post_init__(self) -> None:
        _non_empty(self.name, "name")
        if not isinstance(self.schema, dict) or not self.schema:
            raise ValueError("schema must be a non-empty JSON Schema object")


@dataclass(frozen=True)
class GenerationRequest:
    """Input for one model generation call."""

    system_instruction: str
    user_content: str
    model: str
    settings: ModelSettings = field(default_factory=ModelSettings)
    structured_output: StructuredOutputSpec | None = None

    def __post_init__(self) -> None:
        _non_empty(self.system_instruction, "system_instruction")
        _non_empty(self.user_content, "user_content")
        _non_empty(self.model, "model")


@dataclass(frozen=True)
class ProviderMetadata:
    """Non-secret provider/model metadata returned by an adapter."""

    provider: str
    model: str
    request_id: str | None = None
    api_version: str | None = None

    def __post_init__(self) -> None:
        _non_empty(self.provider, "provider")
        _non_empty(self.model, "model")


@dataclass(frozen=True)
class TokenUsage:
    """Token counts when the provider reports them."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a non-negative integer or None")


@dataclass(frozen=True)
class GenerationResponse:
    """Provider-neutral text/structured response and execution metadata."""

    content: str
    metadata: ProviderMetadata
    status: ExecutionStatus = ExecutionStatus.SUCCEEDED
    structured_content: dict[str, Any] | None = None
    latency_ms: float | None = None
    token_usage: TokenUsage | None = None
    finish_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise ValueError("content must be a string")
        if not isinstance(self.metadata, ProviderMetadata):
            raise ValueError("metadata must be ProviderMetadata")
        if not isinstance(self.status, ExecutionStatus):
            raise ValueError("status must be an ExecutionStatus")
        if self.structured_content is not None and not isinstance(
            self.structured_content, dict
        ):
            raise ValueError("structured_content must be a dict or None")
        _finite_or_none(self.latency_ms, "latency_ms")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")


class LLMProvider(Protocol):
    """Provider-independent sync interface; adapters own network and retry details."""

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response or raise a normalized ProviderError."""
        ...


@dataclass(frozen=True)
class ProviderError(Exception):
    """Normalized provider failure, with no SDK-specific exception dependency."""

    kind: ProviderErrorKind
    message: str
    retryable: bool = False
    provider: str | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProviderErrorKind):
            raise ValueError("kind must be a ProviderErrorKind")
        _non_empty(self.message, "message")


@dataclass(frozen=True)
class EvidenceContext:
    """Retrieved chunk with document metadata and original-document coordinates."""

    chunk_id: str
    document_id: str
    text: str
    start_char: int
    end_char: int
    title: str | None = None
    source_url: str | None = None
    version: str | None = None
    source_date: str | None = None
    domain: str | None = None
    retrieval_rank: int | None = None
    retrieval_score: float | None = None
    retrieval_method: str | None = None
    contains_injection: bool = False

    def __post_init__(self) -> None:
        for value, name in (
            (self.chunk_id, "chunk_id"),
            (self.document_id, "document_id"),
        ):
            _non_empty(value, name)
        if not isinstance(self.text, str) or not self.text:
            raise ValueError("text must be a non-empty string")
        if type(self.start_char) is not int or self.start_char < 0:
            raise ValueError("start_char must be a non-negative integer")
        if type(self.end_char) is not int or self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        if self.end_char - self.start_char != len(self.text):
            raise ValueError("offset range must equal the evidence text length")
        if self.retrieval_rank is not None and (
            type(self.retrieval_rank) is not int or self.retrieval_rank <= 0
        ):
            raise ValueError("retrieval_rank must be a positive integer or None")
        _finite_or_none(self.retrieval_score, "retrieval_score")
        if self.retrieval_method is not None:
            _non_empty(self.retrieval_method, "retrieval_method")


@dataclass(frozen=True)
class EvidenceAssessment:
    """Separate relevance and sufficiency plus explicit evidence limitations."""

    relevance: Relevance = Relevance.NOT_ASSESSED
    sufficiency: Sufficiency = Sufficiency.NOT_ASSESSED
    supporting_evidence_ids: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    missing_premises: tuple[str, ...] = ()
    unsupported_assumptions: tuple[str, ...] = ()
    ambiguity_requiring_clarification: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.relevance, Relevance):
            raise ValueError("relevance must be a Relevance value")
        if not isinstance(self.sufficiency, Sufficiency):
            raise ValueError("sufficiency must be a Sufficiency value")
        for evidence_id in self.supporting_evidence_ids:
            _non_empty(evidence_id, "supporting evidence ID")
        for name in ("contradictions", "missing_premises", "unsupported_assumptions"):
            for item in getattr(self, name):
                _non_empty(item, name)


class ReasonCode(StrEnum):
    """Machine-readable explanations for abstention and clarification outcomes."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    UNSUPPORTED_PREMISE = "unsupported_premise"
    AMBIGUOUS_INTENT = "ambiguous_intent"
    OUT_OF_SCOPE = "out_of_scope"
    OTHER = "other"


@dataclass(frozen=True)
class DecisionReason:
    code: ReasonCode
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, ReasonCode):
            raise ValueError("code must be a ReasonCode")
        _non_empty(self.explanation, "explanation")


@dataclass(frozen=True)
class ClaimCitation:
    """Citation attached to a claim and anchored to a supplied evidence context."""

    claim: str
    evidence_id: str
    quote: str
    start_char: int
    end_char: int

    def __post_init__(self) -> None:
        for value, name in (
            (self.claim, "claim"),
            (self.evidence_id, "evidence_id"),
            (self.quote, "quote"),
        ):
            _non_empty(value, name)
        if type(self.start_char) is not int or self.start_char < 0:
            raise ValueError("start_char must be a non-negative integer")
        if type(self.end_char) is not int or self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        if self.end_char - self.start_char != len(self.quote):
            raise ValueError("citation offsets must match quote length")


def validate_citations(
    citations: tuple[ClaimCitation, ...] | list[ClaimCitation],
    evidence: tuple[EvidenceContext, ...] | list[EvidenceContext],
) -> None:
    """Ensure citation IDs and original-document quotes resolve to supplied evidence."""
    by_id = {item.chunk_id: item for item in evidence}
    if len(by_id) != len(evidence):
        raise ValueError("evidence chunk IDs must be unique")
    for citation in citations:
        context = by_id.get(citation.evidence_id)
        if context is None:
            raise ValueError(
                f"citation references unsupplied evidence: {citation.evidence_id}"
            )
        relative_start = citation.start_char - context.start_char
        relative_end = citation.end_char - context.start_char
        if relative_start < 0 or relative_end > len(context.text):
            raise ValueError("citation offsets fall outside supplied evidence")
        if context.text[relative_start:relative_end] != citation.quote:
            raise ValueError("citation quote does not match supplied evidence text")


@dataclass(frozen=True)
class RetrievalMetadata:
    """Observed retrieval configuration and ranked evidence, not confidence."""

    method: str
    top_k: int
    evidence: tuple[EvidenceContext, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _non_empty(self.method, "method")
        if type(self.top_k) is not int or self.top_k <= 0:
            raise ValueError("top_k must be a positive integer")


@dataclass(frozen=True)
class RunResult:
    """Provider-neutral observed run output, separate from benchmark expectations."""

    decision: Decision | None
    evidence_assessment: EvidenceAssessment
    execution_status: ExecutionStatus
    answer: str | None = None
    unsupported_premises: tuple[str, ...] = ()
    surfaced_contradictions: tuple[str, ...] = ()
    clarification_question: str | None = None
    abstention_reason: DecisionReason | None = None
    decision_reason: DecisionReason | None = None
    citations: tuple[ClaimCitation, ...] = ()
    policy_name: str | None = None
    policy_parameters: dict[str, Any] = field(default_factory=dict)
    retrieval: RetrievalMetadata | None = None
    provider: ProviderMetadata | None = None
    prompt_version: str | None = None
    latency_ms: float | None = None
    token_usage: TokenUsage | None = None
    observed_safe_behavior: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_assessment, EvidenceAssessment):
            raise ValueError("evidence_assessment must be EvidenceAssessment")
        if not isinstance(self.execution_status, ExecutionStatus):
            raise ValueError("execution_status must be an ExecutionStatus")
        if self.execution_status is ExecutionStatus.SUCCEEDED and not isinstance(
            self.decision, Decision
        ):
            raise ValueError("successful execution requires a Decision value")
        if (
            self.execution_status is not ExecutionStatus.SUCCEEDED
            and self.decision is not None
        ):
            raise ValueError("execution failure/refusal must not carry a user decision")
        if self.decision is Decision.ANSWER and not self.answer:
            raise ValueError("ANSWER decision requires answer")
        if self.decision is Decision.CLARIFY and not self.clarification_question:
            raise ValueError("CLARIFY decision requires clarification_question")
        if self.decision is Decision.ABSTAIN and self.abstention_reason is None:
            raise ValueError("ABSTAIN decision requires abstention_reason")
        _finite_or_none(self.latency_ms, "latency_ms")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if self.retrieval is not None:
            validate_citations(self.citations, self.retrieval.evidence)

    def to_dict(self) -> dict[str, Any]:
        """Serialize enums and nested dataclasses into JSON-ready primitive values."""
        return _serialize(self)


def _serialize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    return value


ProviderResult: TypeAlias = GenerationResponse
