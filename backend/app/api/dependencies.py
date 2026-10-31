"""Application settings, runtime construction, and process-local registry."""

from __future__ import annotations

import importlib.util
import logging
import os
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import Request

from app.api.errors import ApiProblem
from app.evaluation.runner import EvaluationRunner
from app.generation.answering import ProviderAnswerGenerator
from app.generation.config import OpenAIProviderConfig
from app.generation.contracts import (
    EvidenceAssessment,
    GenerationRequest,
    GenerationResponse,
    LLMProvider,
    ModelSettings,
    ProviderError,
    ProviderErrorKind,
    RunResult,
)
from app.generation.pipeline import (
    DecisionPolicy,
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
from app.generation.providers.openai_responses import OpenAIResponsesProvider
from app.ingestion.chunking import chunk_documents
from app.ingestion.loader import load_dataset
from app.ingestion.schema import Document
from app.retrieval.bm25 import BM25Index

if TYPE_CHECKING:
    from app.api.models import (
        GenerationRequest as ApiGenerationRequest,
    )
    from app.api.models import (
        PolicyRequest,
        QueryRequest,
        RetrievalRequest,
    )

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS_PATH = PROJECT_ROOT / "data" / "benchmark" / "documents.jsonl"
QUESTIONS_PATH = PROJECT_ROOT / "data" / "benchmark" / "questions.jsonl"
logger = logging.getLogger(__name__)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BM25_K1 = 1.5
BM25_B = 0.75
PROMPT_VERSION = "api-v1"


def openai_sdk_available() -> bool:
    return importlib.util.find_spec("openai") is not None


@dataclass(frozen=True)
class ApiSettings:
    cors_origins: tuple[str, ...] = ()
    environment: str = "development"
    max_request_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        if self.max_request_bytes <= 0:
            raise ValueError("max_request_bytes must be positive")
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not allowed")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> ApiSettings:
        values = os.environ if environ is None else environ
        origins = tuple(
            origin.strip()
            for origin in values.get("RAGBENCH_CORS_ORIGINS", "").split(",")
            if origin.strip()
        )
        if "*" in origins:
            raise ValueError("Wildcard CORS origins are not allowed")
        return cls(
            cors_origins=origins,
            environment=values.get("RAGBENCH_ENV", "development").strip().lower(),
        )


class RuntimeService:
    """Build existing retrieval/generation components from fixed server data."""

    def __init__(
        self,
        documents: list[Document],
        provider: LLMProvider,
        provider_config: OpenAIProviderConfig,
    ) -> None:
        self.documents = {document.id: document for document in documents}
        self.chunks = chunk_documents(
            documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        self.provider = provider
        self.provider_config = provider_config

    @classmethod
    def from_environment(cls) -> RuntimeService:
        documents, _ = load_dataset(DOCUMENTS_PATH, QUESTIONS_PATH)
        provider_config = OpenAIProviderConfig.from_env()
        provider = _LazyOpenAIProvider(provider_config)
        return cls(documents, provider, provider_config)

    def close(self) -> None:
        close = getattr(self.provider, "close", None)
        if callable(close):
            close()

    @property
    def generation_configured(self) -> bool:
        return self.can_generate(None)

    def make_policy(
        self, policy_request: PolicyRequest, model: str | None, settings: ModelSettings
    ) -> DecisionPolicy:
        if policy_request.name == "always_answer":
            return AlwaysAnswerPolicy()
        if policy_request.name == "prompt_abstention":
            return PromptAbstentionPolicy(
                self.provider,
                _require_model(model),
                settings,
            )
        return ThresholdAbstentionPolicy(
            score_type=ThresholdScoreType(policy_request.score_type),
            threshold=policy_request.threshold,
            direction=ThresholdDirection(policy_request.direction),
            missing_score_decision=MissingScoreDecision(
                policy_request.missing_score_decision
            ),
        )

    def make_pipeline(
        self,
        policy: DecisionPolicy,
        *,
        method: str,
        top_k: int,
        model: str | None,
        settings: ModelSettings,
        documents: Mapping[str, Document] | None = None,
        retrieval_configuration: Mapping[str, Any] | None = None,
    ) -> RagPipeline:
        if method != "bm25":
            raise ValueError("Only BM25 retrieval is configured for the API runtime")
        generator = _LazyAnswerGenerator(self.provider, model, settings)
        source_documents = self.documents if documents is None else documents
        config = retrieval_configuration or self.retrieval_configuration_values(top_k)
        chunks = chunk_documents(
            list(source_documents.values()),
            chunk_size=config["chunking"]["size"],
            chunk_overlap=config["chunking"]["overlap"],
        )
        return RagPipeline(
            retriever=BM25Index(
                chunks, k1=config["index"]["k1"], b=config["index"]["b"]
            ),
            documents=source_documents,
            assessor=_NeutralEvidenceAssessor(),
            policy=policy,
            generator=generator,
            config=PipelineConfig(
                top_k=top_k,
                retrieval_method="bm25",
                prompt_version=PROMPT_VERSION,
            ),
        )

    def execute_query(self, request: QueryRequest) -> RunResult:
        effective = self.resolve_generation(request.generation)
        settings = model_settings(effective)
        model = effective["model"]
        policy = self.make_policy(request.policy, model, settings)
        pipeline = self.make_pipeline(
            policy,
            method=request.retrieval.method,
            top_k=request.retrieval.top_k,
            model=model,
            settings=settings,
            retrieval_configuration=self.retrieval_configuration(request.retrieval),
        )
        return pipeline.run(request.question)

    def resolve_model(self, requested_model: str | None) -> str | None:
        configured_model = self.provider_config.model
        if configured_model and requested_model and configured_model != requested_model:
            raise ProviderError(
                ProviderErrorKind.CONFIGURATION,
                "The request model conflicts with the server-configured model.",
            )
        return configured_model or requested_model

    def resolve_generation(self, generation: ApiGenerationRequest) -> dict[str, Any]:
        """Resolve request overrides once, before execution and provenance recording."""
        config = self.provider_config
        return {
            "provider": config.provider,
            "model": self.resolve_model(generation.model),
            "temperature": (
                generation.temperature
                if generation.temperature is not None
                else config.temperature
            ),
            "max_output_tokens": (
                generation.max_output_tokens
                if generation.max_output_tokens is not None
                else config.max_output_tokens
            ),
            "timeout_seconds": (
                generation.timeout_seconds
                if generation.timeout_seconds is not None
                else config.timeout_seconds
            ),
            "retry_count": config.retry_count,
            "sdk_retry_count": 0,
            "store": False,
            "prompt_version": PROMPT_VERSION,
            "seed_applied": False,
        }

    @staticmethod
    def retrieval_configuration_values(top_k: int) -> dict[str, Any]:
        return {
            "method": "bm25",
            "top_k": top_k,
            "chunking": {
                "algorithm": "character-v1",
                "size": CHUNK_SIZE,
                "overlap": CHUNK_OVERLAP,
            },
            "index": {"k1": BM25_K1, "b": BM25_B, "tokenizer": "unicode-word-v1"},
        }

    def retrieval_configuration(self, retrieval: RetrievalRequest) -> dict[str, Any]:
        return self.retrieval_configuration_values(retrieval.top_k)

    def can_generate(self, requested_model: str | None) -> bool:
        try:
            model = self.resolve_model(requested_model)
        except ProviderError:
            return False
        return (
            bool(model)
            and bool(os.environ.get(self.provider_config.api_key_env_var))
            and openai_sdk_available()
        )

    def evaluation_pipeline_factory(
        self,
        policy: DecisionPolicy,
        documents: Mapping[str, Document],
        retrieval_configuration: Mapping[str, Any],
        generation_configuration: Mapping[str, Any],
        seed: int | None,
    ) -> RagPipeline:
        del seed
        if generation_configuration["retry_count"] != self.provider_config.retry_count:
            raise ValueError("Generation retry configuration does not match runtime")
        settings = model_settings(generation_configuration)
        return self.make_pipeline(
            policy,
            method=retrieval_configuration.get("method", "bm25"),
            top_k=retrieval_configuration.get("top_k", 5),
            model=generation_configuration.get("model") or self.provider_config.model,
            settings=settings,
            documents=documents,
            retrieval_configuration=retrieval_configuration,
        )

    def evaluation_runner(self) -> EvaluationRunner:
        return EvaluationRunner(DOCUMENTS_PATH, QUESTIONS_PATH)


class _NeutralEvidenceAssessor:
    """The API does not invent an evidence assessment absent a configured assessor."""

    def assess(self, question, evidence):
        del question, evidence
        return EvidenceAssessment()


class _LazyOpenAIProvider:
    """Own one SDK adapter; drain active calls before closing it at shutdown."""

    def __init__(self, config: OpenAIProviderConfig) -> None:
        self.config = config
        self._provider = None
        self._condition = threading.Condition()
        self._active = 0
        self._closed = False

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        with self._condition:
            if self._closed:
                raise ProviderError(
                    ProviderErrorKind.CONFIGURATION, "The provider runtime is closed."
                )
            if self._provider is None:
                self._provider = OpenAIResponsesProvider(self.config)
            provider = self._provider
            self._active += 1
        try:
            return provider.generate(request)
        finally:
            with self._condition:
                self._active -= 1
                self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            self._condition.notify_all()
            while self._active:
                self._condition.wait()
            provider, self._provider = self._provider, None
        if provider is not None:
            provider.close()


class _LazyAnswerGenerator:
    def __init__(
        self, provider: LLMProvider, model: str | None, settings: ModelSettings
    ):
        self.provider = provider
        self.model = model
        self.settings = settings

    def generate(self, question, evidence):
        generator = ProviderAnswerGenerator(
            self.provider,
            _require_model(self.model),
            self.settings,
        )
        return generator.generate(question, evidence)


class RuntimeManager:
    """Serialize initialization; retry failed construction after a short cooldown."""

    def __init__(
        self,
        factory: Callable[[], RuntimeService] | None = None,
        *,
        retry_delay_seconds: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.factory = factory or RuntimeService.from_environment
        self._lock = threading.Lock()
        self._runtime = None
        self._retry_at = 0.0
        self._retry_delay = retry_delay_seconds
        self._clock = clock
        self._closed = False

    def get(self) -> RuntimeService | None:
        with self._lock:
            if self._closed:
                return None
            if self._runtime is not None:
                return self._runtime
            if self._clock() < self._retry_at:
                return None
            try:
                self._runtime = self.factory()
            except Exception as error:
                logger.warning(
                    "Runtime initialization failed (%s)", type(error).__name__
                )
                self._retry_at = self._clock() + self._retry_delay
            return self._runtime

    def close(self) -> None:
        with self._lock:
            self._closed = True
            runtime, self._runtime = self._runtime, None
        close = getattr(runtime, "close", None)
        if callable(close):
            try:
                close()
            except Exception as error:
                logger.warning("Runtime shutdown failed (%s)", type(error).__name__)

    @property
    def initialized(self) -> bool:
        return self.get() is not None


class ExperimentRegistry:
    """Single-process in-memory registry; contents disappear on restart."""

    def __init__(self):
        self._records = {}
        self._lock = threading.RLock()

    def add(self, record):
        with self._lock:
            self._records[record.experiment_id] = record

    def get(self, experiment_id: str):
        with self._lock:
            return self._records.get(experiment_id)


def model_settings(configuration: Mapping[str, Any]) -> ModelSettings:
    return ModelSettings(
        temperature=configuration["temperature"],
        max_output_tokens=configuration["max_output_tokens"],
        timeout_seconds=configuration["timeout_seconds"],
    )


def _require_model(model: str | None) -> str:
    if not model:
        raise ProviderError(
            ProviderErrorKind.CONFIGURATION,
            "A model must be configured with RAGBENCH_MODEL or the request.",
        )
    return model


def get_runtime_service(request: Request) -> RuntimeService:
    runtime = request.app.state.runtime_manager.get()
    if runtime is None:
        raise ApiProblem(
            503,
            "runtime_unavailable",
            "The configured runtime could not be initialized.",
        )
    return runtime
