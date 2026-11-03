"""P2 Batch 2 HTTP integration with fake local embedding and generation only."""

import json
from dataclasses import replace

import pytest
from app.api.dependencies import RuntimeService, model_settings
from app.api.main import create_app
from app.api.models import QueryRequest, RetrievalRequest
from app.evaluation.runner import EvaluationRunner
from app.generation.config import OllamaProviderConfig
from app.generation.contracts import (
    GenerationResponse,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
)
from app.ingestion.schema import Document
from app.retrieval.bm25 import BM25Index
from app.retrieval.cache import DenseIndexCache
from app.retrieval.ollama_embeddings import OllamaEmbedder
from app.retrieval.runtime import RetrievalFailure, RetrievalRuntime
from fastapi.testclient import TestClient
from test_ollama_embeddings import Transport

SCORES = {"bm25": "bm25", "dense": "dense_cosine", "hybrid": "hybrid_rrf"}
TEXT = "Approval requires manager approval."


class Provider:
    def __init__(self):
        self.calls = []

    def available(self, model):
        return True

    def generate(self, request):
        self.calls.append(request)
        evidence = json.loads(request.user_content)["evidence"][0]
        if "decision" in request.structured_output.schema["properties"]:
            payload = {"decision": "ANSWER", "reason": "Supported.",
                       "reason_code": "other", "clarification_question": None,
                       "self_assessment": 0.75,
                       "supporting_evidence_ids": [evidence["evidence_id"]]}
        else:
            payload = {"answer": evidence["text"], "citations": [{
                "claim": evidence["text"], "quote": evidence["text"],
                "evidence_id": evidence["evidence_id"],
            }], "unsupported_premises": [], "contradictions": []}
        return GenerationResponse(json.dumps(payload), ProviderMetadata(
            "mock", request.model,
        ), structured_content=payload)


@pytest.fixture
def environment(tmp_path):
    transport = Transport()
    provider = Provider()
    embedder = OllamaEmbedder(transport=transport,
                             memory_reader=lambda: 4 * 1024**3)
    cache = DenseIndexCache(tmp_path / "cache",
                            memory_reader=lambda: 4 * 1024**3)
    runtime = RuntimeService(
        [Document("doc", "Approval", "https://example.test", TEXT)],
        provider, OllamaProviderConfig(model="offline:model"),
        retrieval_runtime=RetrievalRuntime(embedder=embedder, cache=cache),
    )
    app = create_app(runtime_factory=lambda: runtime)
    return runtime, app, transport, provider


def request(method, policy="always_answer", **retrieval):
    p = {"name": policy}
    if policy == "threshold":
        p.update(score_type=SCORES[method], threshold=-1)
    return {"question": "What approval is required?",
            "retrieval": {"method": method, "top_k": 1, **retrieval}, "policy": p}


@pytest.mark.parametrize("method", SCORES)
@pytest.mark.parametrize("policy", ["always_answer", "prompt_abstention", "threshold"])
def test_all_nine_query_combinations(environment, method, policy):
    runtime, app, transport, provider = environment
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=request(method, policy))
    assert reply.status_code == 200, reply.text
    body = reply.json()
    assert body["decision"] == "ANSWER"
    assert body["execution_status"] == "succeeded"
    assert body["retrieved_evidence"][0]["retrieval_method"] == SCORES[method]
    assert body["citations"][0]["start_char"] == 0
    assert body["citations"][0]["end_char"] == len(TEXT)
    assert body["citations"][0]["quote"] == TEXT
    assert len(provider.calls) == (2 if policy == "prompt_abstention" else 1)
    if method == "bm25":
        assert not transport.calls
    else:
        assert any(path == "/api/embed" for _, path, _ in transport.calls)
    assert runtime.documents["doc"].text == TEXT


@pytest.mark.parametrize("method", SCORES)
@pytest.mark.parametrize("policy", ["always_answer", "prompt_abstention", "threshold"])
def test_all_nine_evaluation_combinations_use_snapshot(environment, tmp_path,
                                                     method, policy):
    runtime, app, _, _ = environment
    # Intentionally different from runtime documents, with the same document ID.
    text = "Snapshot manager approval is required."
    docs = tmp_path / "documents.jsonl"
    questions = tmp_path / "questions.jsonl"
    docs.write_text(json.dumps(Document(
        "doc", "Snapshot", "https://example.test", text,
    ).to_dict()) + "\n", encoding="utf-8")
    questions.write_text(json.dumps({
        "id": "train_fixture", "question": "What approval is required?",
        "split": "train", "is_answerable": True, "question_type": "factual",
        "absence_note": None, "unanswerable_category": None,
        "expected_answer": text, "evidence_spans": [{
            "doc_id": "doc", "start_char": 0, "end_char": len(text), "text": text,
        }],
    }) + "\n", encoding="utf-8")
    runtime.evaluation_runner = lambda: EvaluationRunner(docs, questions)
    payload = request(method, policy)
    with TestClient(app) as client:
        reply = client.post("/api/v1/evaluations", json={
            "split": "train", "retrieval": payload["retrieval"],
            "policies": [payload["policy"]],
        })
        assert reply.status_code == 200, reply.text
        assert reply.json()["status"] == "completed"
        record = app.state.experiment_registry.get(reply.json()["experiment_id"])
        assert record.runs[0].observed.answer == text
        assert record.policy_configurations[0]["parameters"]["provider"] == "ollama"
        if method != "bm25":
            assert record.retrieval_configuration["embedding"]["digest"] == "a" * 64


@pytest.mark.parametrize("retrieval", [
    {"method": "other"}, {"method": "dense", "rrf_k": 60},
    {"method": "bm25", "candidate_k": 10},
    {"method": "hybrid", "candidate_k": 0},
    {"method": "hybrid", "candidate_k": 257},
    {"method": "hybrid", "top_k": 3, "candidate_k": 2},
    {"method": "hybrid", "rrf_k": True},
    {"method": "hybrid", "rrf_k": 1001},
    {"method": "hybrid", "rrf_k": 0},
    {"method": "dense", "model": "remote:cloud"},
    {"method": "hybrid", "candidate_k": 2.5},
])
def test_invalid_http_parameters_fail_before_any_embedding(environment, retrieval):
    _, app, transport, provider = environment
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json={
            **request("bm25"), "retrieval": retrieval,
        })
        assert reply.status_code == 422
    assert not transport.calls and not provider.calls


@pytest.mark.parametrize("method", ["dense", "hybrid"])
def test_threshold_requires_correct_score_family(environment, method):
    _, app, transport, _ = environment
    payload = request(method, "threshold")
    payload["policy"]["score_type"] = "bm25"
    with TestClient(app) as client:
        assert client.post("/api/v1/query", json=payload).status_code == 422
        assert client.post("/api/v1/evaluations", json={
            "split": "train", "retrieval": payload["retrieval"],
            "policies": [payload["policy"]],
        }).status_code == 422
    assert not transport.calls


def pipeline(runtime, method="dense", **retrieval):
    body = QueryRequest.model_validate(request(method, **retrieval))
    generation = runtime.resolve_generation(body.generation)
    settings = model_settings(generation)
    return runtime.make_pipeline(
        runtime.make_policy(body.policy, generation["model"], settings),
        method=method, top_k=1, model=generation["model"], settings=settings,
        retrieval_configuration=runtime.retrieval_configuration(body.retrieval),
    )


def test_indexes_reused_and_fusion_settings_bound(environment):
    runtime, _, transport, _ = environment
    a, b = pipeline(runtime), pipeline(runtime)
    assert a.retriever is b.retriever
    assert len([c for c in transport.calls if c[1] == "/api/embed"]) == 1
    hybrid = pipeline(runtime, "hybrid", candidate_k=1, rrf_k=7)
    assert hybrid.retriever.candidate_k == 1
    assert hybrid.retriever.index.rrf_k == 7
    assert len([c for c in transport.calls if c[1] == "/api/embed"]) == 1
    assert pipeline(runtime, "hybrid", candidate_k=1, rrf_k=7).retriever is (
        hybrid.retriever
    )


def test_bm25_defaults_and_ranking_unchanged(environment):
    runtime, _, transport, _ = environment
    config = runtime.retrieval_configuration(RetrievalRequest())
    assert config == RuntimeService.retrieval_configuration_values(5)
    p = pipeline(runtime, "bm25")
    assert p.retriever.search("approval") == (
        BM25Index(runtime.chunks).search("approval")
    )
    assert not transport.calls


def test_runtime_snapshot_and_identity_mismatch_are_rejected(environment):
    runtime, _, _, _ = environment
    p = pipeline(runtime)
    config = runtime.retrieval_configuration(RetrievalRequest(method="dense", top_k=1))
    fresh = replace(runtime.documents["doc"], text="A changed document snapshot.")
    index = runtime.retrieval_runtime.get({fresh.id: fresh}, config)
    assert index is not p.retriever
    assert index.chunks[0].text == fresh.text
    broken = {**config, "embedding": {**config["embedding"], "digest": "b" * 64}}
    with pytest.raises(RetrievalFailure, match="identity_mismatch"):
        runtime.retrieval_runtime.get(runtime.documents, broken)


@pytest.mark.parametrize("failure", ["missing", "resource", "disk", "bad_vector"])
def test_retrieval_failures_are_explicit_and_never_fallback(environment, monkeypatch,
                                                          failure):
    runtime, app, transport, provider = environment
    if failure == "missing":
        transport.tag["name"] = "not-installed"
    elif failure == "resource":
        runtime.retrieval_runtime.cache._memory = lambda: 1
    elif failure == "disk":
        def fail(*args, **kwargs):
            raise OSError("private cache path secret")
        monkeypatch.setattr(runtime.retrieval_runtime.cache, "get_or_build", fail)
    else:
        transport.mutate = lambda reply: {**reply, "embeddings": [[False] * 384]}
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=request("dense"))
    assert reply.status_code == 503, reply.text
    assert reply.json()["error"]["execution_status"] == "failed"
    assert "decision" not in reply.json()
    assert "secret" not in reply.text and "private cache" not in reply.text
    assert not provider.calls


def test_query_embedding_failure_is_not_intentional_abstention(environment):
    runtime, app, transport, provider = environment
    pipeline(runtime)  # Build corpus vectors using the fake encoder.
    transport.mutate = lambda reply: {**reply, "embeddings": []}
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=request("dense", "threshold"))
    assert reply.status_code == 502
    assert reply.json()["error"]["code"] == "retrieval_execution_failure"
    assert not provider.calls


@pytest.mark.parametrize("method", ["dense", "hybrid"])
def test_high_threshold_abstains_without_generation(environment, method):
    _, app, _, provider = environment
    payload = request(method, "threshold")
    payload["policy"]["threshold"] = 1000
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=payload)
    assert reply.status_code == 200
    assert reply.json()["decision"] == "ABSTAIN"
    assert reply.json()["execution_status"] == "succeeded"
    assert not provider.calls


def test_default_pipeline_factory_selects_dense(environment):
    runtime, _, _, _ = environment
    body = QueryRequest.model_validate(request("dense"))
    settings = model_settings(runtime.resolve_generation(body.generation))
    result = runtime.make_pipeline(
        runtime.make_policy(body.policy, "offline:model", settings),
        method="dense", top_k=1, model="offline:model", settings=settings,
    )
    assert result.config.retrieval_method == "dense_cosine"


@pytest.mark.parametrize("rrf,candidate", [(0, 1), (True, 1), (60, 0), (60, 257)])
def test_direct_snapshot_configuration_validates_fusion(environment, rrf, candidate):
    runtime, _, _, _ = environment
    config = runtime.retrieval_configuration(RetrievalRequest(method="hybrid", top_k=1))
    config.update(rrf_k=rrf, candidate_k=candidate)
    with pytest.raises(RetrievalFailure):
        runtime.retrieval_runtime.get(runtime.documents, config)


def test_unavailable_configuration_has_safe_http_error(environment, monkeypatch):
    runtime, app, _, provider = environment
    runtime.retrieval_runtime = RetrievalRuntime()
    monkeypatch.setenv("RAGBENCH_EMBEDDING_MODEL", "remote:cloud")
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=request("dense"))
    assert reply.status_code == 503
    assert reply.json()["error"]["code"] == "invalid_embedding_configuration"
    assert not provider.calls


def test_query_embedding_timeout_preserves_timeout_status(environment):
    runtime, app, transport, provider = environment
    pipeline(runtime)

    def fail(reply):
        raise ProviderError(ProviderErrorKind.TIMEOUT, "private local details")

    transport.mutate = fail
    with TestClient(app) as client:
        reply = client.post("/api/v1/query", json=request("dense", "threshold"))
    assert reply.status_code == 504
    assert reply.json()["error"]["execution_status"] == "timed_out"
    assert reply.json()["error"]["code"] == "retrieval_timeout"
    assert "private" not in reply.text and not provider.calls


def test_new_runtime_reuses_persistent_cache(environment):
    runtime, _, transport, _ = environment
    pipeline(runtime)
    old = runtime.retrieval_runtime
    runtime.retrieval_runtime = RetrievalRuntime(embedder=old.embedder, cache=old.cache)
    pipeline(runtime)
    assert len([c for c in transport.calls if c[1] == "/api/embed"]) == 1


def test_runtime_index_lru_bounded(environment):
    runtime, _, _, _ = environment
    config = runtime.retrieval_configuration(RetrievalRequest(method="dense", top_k=1))
    for i in range(10):
        doc = replace(runtime.documents["doc"], text=f"Snapshot approval {i}.")
        runtime.retrieval_runtime.get({doc.id: doc}, config)
    assert len(runtime.retrieval_runtime._indexes) == 8


def test_unconfigured_evaluation_never_falls_back(environment, monkeypatch):
    runtime, app, _, provider = environment
    runtime.retrieval_runtime = RetrievalRuntime()
    monkeypatch.delenv("RAGBENCH_EMBEDDING_MODEL", raising=False)
    with TestClient(app) as client:
        reply = client.post("/api/v1/evaluations", json={
            "split": "train", "question_ids": ["q_pilot_020"],
            "retrieval": {"method": "dense", "top_k": 1},
            "policies": [{"name": "always_answer"}],
        })
    assert reply.status_code == 503
    assert reply.json()["error"]["code"] == "embedding_not_configured"
    assert not provider.calls
