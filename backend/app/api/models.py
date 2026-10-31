"""Validated public request and response models."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.generation.contracts import (
    Decision,
    ExecutionStatus,
    ReasonCode,
    Relevance,
    Sufficiency,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RetrievalRequest(StrictModel):
    method: Literal["bm25"] = "bm25"
    top_k: int = Field(default=5, ge=1, le=20)


class PolicyRequest(StrictModel):
    name: Literal["always_answer", "prompt_abstention", "threshold"]
    score_type: Literal["bm25", "dense_cosine", "hybrid_rrf"] | None = None
    threshold: float | None = Field(default=None, allow_inf_nan=False)
    direction: Literal["at_least", "at_most"] = "at_least"
    missing_score_decision: Literal["ABSTAIN", "ANSWER"] = "ABSTAIN"

    @model_validator(mode="after")
    def validate_policy_fields(self):
        if self.name == "threshold":
            if self.threshold is None or self.score_type is None:
                raise ValueError("threshold policy requires score_type and threshold")
        elif self.threshold is not None or self.score_type is not None:
            raise ValueError(
                "score_type and threshold are only valid for threshold policy"
            )
        return self


class GenerationRequest(StrictModel):
    model: str | None = Field(default=None, min_length=1, max_length=200)
    temperature: float | None = Field(default=None, ge=0, le=2, allow_inf_nan=False)
    max_output_tokens: int | None = Field(default=None, ge=1, le=32768)
    timeout_seconds: float | None = Field(
        default=None, gt=0, le=120, allow_inf_nan=False
    )


CorrelationId = Annotated[
    str,
    Field(
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
    ),
]


class QueryRequest(StrictModel):
    question: str = Field(min_length=1, max_length=8000)
    retrieval: RetrievalRequest = Field(default_factory=RetrievalRequest)
    policy: PolicyRequest
    generation: GenerationRequest = Field(default_factory=GenerationRequest)
    experiment_id: CorrelationId | None = None
    run_id: CorrelationId | None = None

    @model_validator(mode="after")
    def validate_score_method(self):
        if (
            self.policy.name == "threshold"
            and self.policy.score_type != self.retrieval.method
        ):
            raise ValueError("threshold score_type must match retrieval method")
        return self


class EvaluationRequest(StrictModel):
    split: Literal["train", "dev", "test"]
    question_ids: list[str] | None = Field(default=None, max_length=100)
    policies: list[PolicyRequest] = Field(min_length=1, max_length=4)
    retrieval: RetrievalRequest = Field(default_factory=RetrievalRequest)
    generation: GenerationRequest = Field(default_factory=GenerationRequest)
    random_seed: int | None = None
    fail_fast: bool = False

    @model_validator(mode="after")
    def unique_policy_names(self):
        names = [policy.name for policy in self.policies]
        if len(names) != len(set(names)):
            raise ValueError("policy names must be unique")
        if self.question_ids is not None and len(self.question_ids) != len(
            set(self.question_ids)
        ):
            raise ValueError("question_ids must not contain duplicates")
        for policy in self.policies:
            if (
                policy.name == "threshold"
                and policy.score_type != self.retrieval.method
            ):
                raise ValueError("threshold score_type must match retrieval method")
        return self


class ErrorBody(BaseModel):
    code: str
    message: str
    execution_status: ExecutionStatus | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    application: str
    api_version: str
    runtime_initialized: bool
    generation_configured: bool
    provider_connection_tested: Literal[False] = False


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReasonResponse(PublicModel):
    code: ReasonCode
    explanation: str


class CitationResponse(PublicModel):
    claim: str
    evidence_id: str
    quote: str
    start_char: int
    end_char: int


class EvidenceResponse(PublicModel):
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


class AssessmentResponse(PublicModel):
    relevance: Relevance
    sufficiency: Sufficiency
    supporting_evidence_ids: list[str]
    contradictions: list[str]
    missing_premises: list[str]
    unsupported_assumptions: list[str]
    ambiguity_requiring_clarification: str | None


class ProviderResponse(PublicModel):
    provider: str
    model: str
    request_id: str | None = None
    api_version: str | None = None


class UsageResponse(PublicModel):
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


class SettingsResponse(PublicModel):
    temperature: float | None
    seed: int | None
    max_output_tokens: int | None
    timeout_seconds: float


class PolicyParameters(PublicModel):
    model: str | None = None
    provider: str | None = None
    settings: SettingsResponse | None = None
    score_type: str | None = None
    threshold: float | None = None
    direction: str | None = None
    aggregation: str | None = None
    observed_aggregate_score: float | None = None
    missing_score_decision: str | None = None


class QueryResponse(PublicModel):
    experiment_id: str | None
    run_id: str | None
    decision: Decision
    answer: str | None
    clarification_question: str | None
    decision_reason: ReasonResponse | None
    citations: list[CitationResponse]
    retrieved_evidence: list[EvidenceResponse]
    evidence_assessment: AssessmentResponse
    policy_name: str | None
    policy_parameters: PolicyParameters
    provider: ProviderResponse | None
    execution_status: ExecutionStatus
    unsupported_premises: list[str]
    surfaced_contradictions: list[str]
    prompt_version: str | None
    latency_ms: float | None
    token_usage: UsageResponse | None


class EvaluationAccepted(BaseModel):
    experiment_id: str
    status: Literal["completed", "partial"]
    split: str
    selected_question_count: int
    observed_run_count: int


class EvaluationMetadata(BaseModel):
    experiment_id: str
    status: Literal["completed", "partial"]
    split: str
    selected_question_ids: list[str]
    policy_names: list[str]
    observed_run_count: int
    stopped_early: bool


class RetrievalResponse(PublicModel):
    method: str
    top_k: int
    evidence: list[EvidenceResponse]
    parameters: dict[str, JsonValue]


class ObservedResultResponse(PublicModel):
    decision: Decision | None
    evidence_assessment: AssessmentResponse
    execution_status: ExecutionStatus
    answer: str | None
    unsupported_premises: list[str]
    surfaced_contradictions: list[str]
    clarification_question: str | None
    abstention_reason: ReasonResponse | None
    decision_reason: ReasonResponse | None
    citations: list[CitationResponse]
    policy_name: str | None
    policy_parameters: PolicyParameters
    retrieval: RetrievalResponse | None
    provider: ProviderResponse | None
    prompt_version: str | None
    latency_ms: float | None
    token_usage: UsageResponse | None
    observed_safe_behavior: bool | None


class GoldSpanResponse(PublicModel):
    doc_id: str
    start_char: int
    end_char: int
    text: str
    id: str


class GoldResponse(PublicModel):
    question_id: str
    split: Literal["train", "dev", "test"]
    is_answerable: bool
    expected_answer: str | None
    expected_safe_behavior: str | None
    unanswerable_category: str | None
    ambiguity_type: str | None
    domain: str | None
    question_type: str | None
    evidence_spans: list[GoldSpanResponse]


class RunErrorResponse(PublicModel):
    kind: str
    message: str
    retryable: bool | None


class ExperimentRunResponse(PublicModel):
    run_id: str
    question_id: str
    policy_name: str
    observed: ObservedResultResponse
    gold: GoldResponse
    error: RunErrorResponse | None


class PolicyConfigurationResponse(PublicModel):
    name: str
    parameters: PolicyParameters


class ExperimentResponse(PublicModel):
    schema_version: Literal["ragbench.experiment.v2"]
    experiment_id: str
    created_at_utc: str
    benchmark_split: Literal["train", "dev", "test"]
    selected_question_ids: list[str]
    dataset_fingerprint: dict[str, str]
    retrieval_configuration: dict[str, JsonValue]
    policy_configurations: list[PolicyConfigurationResponse]
    generation_configuration: dict[str, JsonValue]
    random_seed: int | None
    software_metadata: dict[str, JsonValue]
    environment_metadata: dict[str, JsonValue]
    runs: list[ExperimentRunResponse]
    stopped_early: bool
    comparison_warnings: list[str]
    metrics: dict[str, JsonValue]


class EvaluationResults(PublicModel):
    experiment: ExperimentResponse
