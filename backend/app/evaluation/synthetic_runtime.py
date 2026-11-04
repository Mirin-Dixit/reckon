"""Deterministic fictional runtime. No network, model, or gold-label access."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from app.api.experiment_models import ExperimentRequest
from app.evaluation.runner import PolicyRunConfig
from app.generation.contracts import (
    ClaimCitation,
    EvidenceAssessment,
    GenerationResponse,
    ProviderMetadata,
)
from app.generation.pipeline import (
    GeneratedAnswer,
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
from app.ingestion.chunking import chunk_documents
from app.retrieval.bm25 import BM25Index
from app.retrieval.dense import DenseIndex
from app.retrieval.hybrid import HybridIndex

FIXTURES = Path(__file__).resolve().parents[3] / "data/fixtures/p4_synthetic_v1"
GENERATION = {
    "provider": "synthetic",
    "model": "fixture-rules.v1",
    "embedding": "sha256-token-buckets.v1",
    "external_calls": False,
}


def source_fingerprint() -> str:
    """Bind uncommitted runtime code as well as the recorded Git revision."""
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for source in sorted(root.rglob("*.py")):
        digest.update(source.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(source.read_bytes()).digest())
    return digest.hexdigest()


class FixtureEmbedder:
    """Token hash buckets exercise vector retrieval; no learned semantics."""

    def embed_query(self, query: str) -> list[float]:
        vector = [0.0] * 32
        for word in re.findall(r"\w+", query.lower()):
            vector[hashlib.sha256(word.encode()).digest()[0] % 32] += 1.0
        return vector

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]


class FixtureProvider:
    """Structured rule responses exercise the existing prompt policy parser."""

    def generate(self, request) -> GenerationResponse:
        data = json.loads(request.user_content)
        question = data["question"]
        evidence = data["evidence"]
        decision, reason = "ANSWER", "other"
        if "unknown" in question.lower() or not evidence:
            decision, reason = "ABSTAIN", "insufficient_evidence"
        elif "which limit" in question.lower():
            decision, reason = "CLARIFY", "ambiguous_intent"
        return GenerationResponse(
            content="",
            metadata=ProviderMetadata("synthetic", "fixture-rules.v1"),
            structured_content=dict(
                decision=decision,
                reason="Synthetic rule response.",
                reason_code=reason,
                supporting_evidence_ids=(
                    [evidence[0]["evidence_id"]] if decision == "ANSWER" else []
                ),
                clarification_question=(
                    "Do you mean the red or blue limit?"
                    if decision == "CLARIFY"
                    else None
                ),
                self_assessment=None,
            ),
        )


class FixtureGenerator:
    def generate(self, question, evidence) -> GeneratedAnswer:
        if not evidence:
            raise ValueError("Fixture has no evidence")
        item = evidence[0]
        return GeneratedAnswer(
            answer=item.text,
            citations=(
                ClaimCitation(
                    item.text, item.chunk_id, item.text, item.start_char, item.end_char
                ),
            ),
            provider=ProviderMetadata("synthetic", "fixture-rules.v1"),
        )


class FixtureRetriever:
    def __init__(self, retriever, candidate_k=None) -> None:
        self.retriever = retriever
        self.candidate_k = candidate_k

    def search(self, query: str, top_k: int = 5):
        if "simulate failure" in query.lower():
            raise RuntimeError("Deliberate synthetic execution failure")
        if isinstance(self.retriever, HybridIndex):
            return self.retriever.search(
                query, top_k=top_k, candidate_k=self.candidate_k
            )
        return self.retriever.search(query, top_k=top_k)

    def score_parameters(self, query, chunks, top_k):
        describe = getattr(self.retriever, "score_parameters", None)
        return describe(query, chunks, top_k) if callable(describe) else {}


def policy_configs(request: ExperimentRequest) -> list[PolicyRunConfig]:
    configs = []
    for spec in request.policies:
        if spec.name == "always_answer":
            policy = AlwaysAnswerPolicy()
        elif spec.name == "prompt_abstention":
            policy = PromptAbstentionPolicy(FixtureProvider(), "fixture-rules.v1")
        else:
            policy = ThresholdAbstentionPolicy(
                ThresholdScoreType(spec.score_type),
                spec.threshold,
                ThresholdDirection(spec.direction),
                MissingScoreDecision(spec.missing_score_decision),
            )
        params = spec.model_dump(exclude={"name"}, exclude_none=True)
        params.update(model="fixture-rules.v1", provider="synthetic")
        configs.append(PolicyRunConfig(spec.name, policy, params))
    return configs


def pipeline_factory(policy, documents, retrieval, generation, seed) -> RagPipeline:
    """Only runtime inputs enter here; references stay in EvaluationRunner."""
    chunks = chunk_documents(list(documents.values()), 500, 50)
    bm25 = BM25Index(chunks)
    method = retrieval["method"]
    index = bm25
    if method != "bm25":
        dense = DenseIndex(chunks, FixtureEmbedder())
        index = (
            dense
            if method == "dense"
            else HybridIndex(
                bm25,
                dense,
                retrieval.get("rrf_k") or 60,
            )
        )
    return RagPipeline(
        retriever=FixtureRetriever(index, retrieval.get("candidate_k")),
        documents=dict(documents),
        assessor=MockEvidenceAssessor(EvidenceAssessment()),
        policy=policy,
        generator=FixtureGenerator(),
        config=PipelineConfig(
            top_k=retrieval["top_k"],
            retrieval_method={
                "bm25": "bm25",
                "dense": "dense_cosine",
                "hybrid": "hybrid_rrf",
            }[method],
            prompt_version="synthetic-fixture.v1",
            retrieval_parameters=retrieval,
        ),
    )
