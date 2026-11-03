"""Offline regression tests for the Stage 3G independent audit findings."""

import hashlib
import json
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
import uvicorn
from app.api.dependencies import (
    DOCUMENTS_PATH,
    QUESTIONS_PATH,
    ApiSettings,
    RuntimeManager,
    RuntimeService,
    _LazyOpenAIProvider,
)
from app.api.main import create_app
from app.evaluation.metrics import paired_policy_comparison
from app.evaluation.runner import EvaluationRunner
from app.generation.config import OpenAIProviderConfig
from app.generation.contracts import (
    Decision,
    ProviderError,
    ProviderErrorKind,
    TokenUsage,
)
from app.generation.pipeline import DecisionSelection, FixedDecisionPolicy
from app.generation.providers.openai_responses import OpenAIResponsesProvider
from app.ingestion.loader import load_dataset
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException
from test_api import FakeRuntime, make_result
from test_openai_provider import FakeClient, response


def test_documented_uvicorn_startup_serves_health_without_provider_calls():
    version = subprocess.run(
        [sys.executable, "-m", "uvicorn", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert "uvicorn" in version.stdout.lower()
    server = uvicorn.Server(
        uvicorn.Config("app.api.main:app", host="127.0.0.1", port=0, log_level="error")
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        worker = threading.Thread(
            target=server.run, kwargs={"sockets": [listener]}, daemon=True
        )
        worker.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and worker.is_alive():
                assert time.monotonic() < deadline, "Server did not start"
                time.sleep(0.01)
            assert server.started
            with urlopen(f"http://127.0.0.1:{port}/api/v1/health", timeout=5) as reply:
                body = json.load(reply)
                assert reply.status == 200
                assert body["runtime_initialized"] is True
                assert body["provider_connection_tested"] is False
        finally:
            server.should_exit = True
            worker.join(timeout=10)
            assert not worker.is_alive()


def test_local_frontend_cors_configuration_is_exact():
    settings = ApiSettings.from_env(
        {"RAGBENCH_CORS_ORIGINS": "http://127.0.0.1:3000,http://127.0.0.1:3001"}
    )
    assert settings.cors_origins == (
        "http://127.0.0.1:3000", "http://127.0.0.1:3001"
    )
    assert ApiSettings.from_env({}).cors_origins == ()
    with pytest.raises(ValueError, match="Wildcard CORS"):
        ApiSettings.from_env({"RAGBENCH_CORS_ORIGINS": "http://127.0.0.1:3001,*"})


def test_local_frontend_cors_over_real_loopback_http():
    origin = "http://127.0.0.1:3001"
    application = create_app(
        settings=ApiSettings.from_env({"RAGBENCH_CORS_ORIGINS": origin}),
        runtime_factory=FakeRuntime,
    )

    @application.get("/cors-test-error")
    def unexpected():
        raise RuntimeError("PRIVATE_CORS_ERROR_SENTINEL")

    server = uvicorn.Server(uvicorn.Config(application, log_level="error"))
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        base = f"http://127.0.0.1:{listener.getsockname()[1]}"
        worker = threading.Thread(
            target=server.run, kwargs={"sockets": [listener]}, daemon=True
        )
        worker.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and worker.is_alive():
                assert time.monotonic() < deadline, "Server did not start"
                time.sleep(0.01)
            assert server.started
            for requested_origin, allowed in (
                (origin, True), ("https://unexpected.example", False),
                ("http://127.0.0.1:30010", False),
            ):
                request = Request(
                    base + "/api/v1/health", headers={"Origin": requested_origin}
                )
                with urlopen(request, timeout=5) as reply:
                    assert reply.status == 200
                    assert json.load(reply)["provider_connection_tested"] is False
                    assert reply.headers.get("Access-Control-Allow-Origin") == (
                        origin if allowed else None
                    )
                    assert reply.headers.get("Access-Control-Allow-Credentials") is None
            preflight = Request(
                base + "/api/v1/health", method="OPTIONS",
                headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
            )
            with urlopen(preflight, timeout=5) as reply:
                assert reply.headers["Access-Control-Allow-Origin"] == origin
            denied_preflight = Request(
                base + "/api/v1/health", method="OPTIONS",
                headers={
                    "Origin": "https://unexpected.example",
                    "Access-Control-Request-Method": "GET",
                },
            )
            with pytest.raises(HTTPError) as denied:
                urlopen(denied_preflight, timeout=5)
            with denied.value as reply:
                assert reply.code == 400
                assert reply.headers.get("Access-Control-Allow-Origin") is None
                assert reply.headers.get("Access-Control-Allow-Credentials") is None
            error_request = Request(
                base + "/cors-test-error", headers={"Origin": origin}
            )
            with pytest.raises(HTTPError) as captured:
                urlopen(error_request, timeout=5)
            with captured.value as reply:
                assert reply.code == 500
                assert reply.headers["Access-Control-Allow-Origin"] == origin
                body = reply.read().decode()
                assert json.loads(body)["error"]["code"] == "internal_error"
                assert "PRIVATE_CORS_ERROR_SENTINEL" not in body
        finally:
            server.should_exit = True
            worker.join(timeout=10)
            assert not worker.is_alive()


def recorded_experiment(config, *, overrides=None):
    documents, _ = load_dataset(DOCUMENTS_PATH, QUESTIONS_PATH)
    sdk = FakeClient(
        [
            response(
                json.dumps(
                    {
                        "answer": "Mock answer.",
                        "citations": [],
                        "unsupported_premises": [],
                        "contradictions": [],
                    }
                ),
                model="audit-model",
            )
        ]
    )
    provider = OpenAIResponsesProvider(config, client=sdk)
    runtime = RuntimeService(documents, provider, config)
    application = create_app(runtime_factory=lambda: runtime)
    reply = TestClient(application).post(
        "/api/v1/evaluations",
        json={
            "split": "test",
            "policies": [{"name": "threshold", "score_type": "bm25", "threshold": 0}],
            "generation": overrides or {},
            "random_seed": 17,
        },
    )
    assert reply.status_code == 200, reply.text
    record = application.state.experiment_registry.get(reply.json()["experiment_id"])
    assert record.runs[0].observed.execution_status.value == "succeeded"
    return record, sdk


def test_effective_defaults_are_identical_in_execution_and_provenance():
    config = OpenAIProviderConfig(
        model="audit-model",
        temperature=0.2,
        max_output_tokens=999,
        timeout_seconds=75,
        retry_count=4,
    )
    record, sdk = recorded_experiment(config)
    effective = record.generation_configuration
    assert effective["temperature"] == sdk.responses.calls[0]["temperature"] == 0.2
    assert effective["max_output_tokens"] == sdk.responses.calls[0]["max_output_tokens"]
    assert effective["timeout_seconds"] == sdk.option_calls[0]["timeout"] == 75
    assert effective["retry_count"] == config.retry_count == 4
    assert effective["sdk_retry_count"] == sdk.option_calls[0]["max_retries"] == 0
    assert effective["seed_applied"] is False
    assert record.retrieval_configuration["chunking"]["size"] == 500
    assert record.retrieval_configuration["index"] == {
        "k1": 1.5,
        "b": 0.75,
        "tokenizer": "unicode-word-v1",
    }
    explicit, sdk = recorded_experiment(
        config,
        overrides={"temperature": 0, "timeout_seconds": 30, "max_output_tokens": 40},
    )
    assert sdk.option_calls[0]["timeout"] == 30
    assert explicit.generation_configuration["temperature"] == 0


def test_different_effective_defaults_are_rejected_by_paired_comparison():
    config = OpenAIProviderConfig(model="audit-model", temperature=0.2)
    left, _ = recorded_experiment(config)
    for changed in (
        replace(config, temperature=0.8),
        replace(config, retry_count=4),
        replace(config, timeout_seconds=75),
        replace(config, max_output_tokens=900),
    ):
        right, _ = recorded_experiment(changed)
        comparison = paired_policy_comparison(left, "threshold", right, "threshold")
        assert comparison["status"] == "incompatible"
        assert (
            "incompatible generation_configuration"
            in comparison["incompatibility_reasons"]
        )


def test_query_preserves_observed_safety_and_execution_metadata_safely():
    secret = "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789"
    observed = replace(
        make_result(Decision.ANSWER),
        unsupported_premises=("No approval was granted.", secret),
        surfaced_contradictions=("The two limits disagree.",),
        prompt_version="api-v1",
        latency_ms=12.5,
        token_usage=TokenUsage(input_tokens=20, output_tokens=5, total_tokens=25),
    )
    app_client = TestClient(create_app(runtime_factory=lambda: FakeRuntime(observed)))
    reply = app_client.post(
        "/api/v1/query", json={"question": "Q?", "policy": {"name": "always_answer"}}
    )
    assert reply.status_code == 200
    body = reply.json()
    assert body["unsupported_premises"] == [
        "No approval was granted.",
        "<redacted-credential>",
    ]
    assert body["surfaced_contradictions"] == ["The two limits disagree."]
    assert body["prompt_version"] == "api-v1"
    assert body["latency_ms"] == 12.5
    assert body["token_usage"]["total_tokens"] == 25
    assert secret not in reply.text


@pytest.mark.parametrize("headers", [{}, {"Content-Length": "1"}])
def test_actual_byte_limit_rejects_streamed_body_before_runtime(headers):
    calls = []
    application = create_app(
        settings=ApiSettings(max_request_bytes=128),
        runtime_factory=lambda: calls.append("runtime") or FakeRuntime(),
    )
    payload = json.dumps({"question": "Q?", "policy": {"name": "always_answer"}})
    reply = TestClient(application).post(
        "/api/v1/query",
        content=iter([b" " * 100, payload.encode()]),
        headers={"Content-Type": "application/json", **headers},
    )
    assert reply.status_code == 413
    assert reply.json()["error"]["code"] == "request_too_large"
    assert calls == []


def test_body_limit_allows_exact_boundary_and_rejects_invalid_length():
    payload = json.dumps({"question": "Q?", "policy": {"name": "always_answer"}})
    c = TestClient(
        create_app(
            settings=ApiSettings(max_request_bytes=len(payload)),
            runtime_factory=lambda: FakeRuntime(),
        )
    )
    assert (
        c.post(
            "/api/v1/query",
            content=iter([payload.encode()]),
            headers={"Content-Type": "application/json"},
        ).status_code
        == 200
    )
    for length in ("-1", "invalid", "9" * 5000):
        reply = c.post(
            "/api/v1/query", content=b"{}", headers={"Content-Length": length}
        )
        assert reply.status_code == (413 if length.isdigit() else 400)


def test_openapi_matches_error_envelopes_and_nested_response_types():
    application = create_app(runtime_factory=lambda: FakeRuntime())

    @application.get("/internal-error")
    def internal_error():
        raise HTTPException(418, "private credentials and path")

    c = TestClient(application)
    schema = c.get("/api/v1/openapi.json").json()
    responses = schema["paths"]["/api/v1/query"]["post"]["responses"]
    for status in (400, 404, 405, 413, 422, 500, 502, 503, 504):
        assert responses[str(status)]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponse"
        }
    models = schema["components"]["schemas"]
    for field in ("citations", "retrieved_evidence"):
        assert "$ref" in models["QueryResponse"]["properties"][field]["items"]
    assert models["EvaluationResults"]["properties"]["experiment"] == {
        "$ref": "#/components/schemas/ExperimentResponse"
    }
    for reply in (
        c.get("/missing"),
        c.get("/api/v1/query"),
        c.post("/api/v1/query", json={}),
        c.get("/internal-error"),
    ):
        assert set(reply.json()) == {"error"}
        assert set(reply.json()["error"]) == {"code", "message", "execution_status"}
        assert "private" not in reply.text


@pytest.mark.parametrize("field", ["experiment_id", "run_id"])
def test_correlation_ids_reject_credentials_and_accept_uuid(field):
    c = TestClient(create_app(runtime_factory=lambda: FakeRuntime()))
    payload = {"question": "Q?", "policy": {"name": "always_answer"}}
    for unsafe in ("sk-proj-abcdefghijklmnopqrstuvwxyz0123456789", "Bearer secret", ""):
        reply = c.post("/api/v1/query", json={**payload, field: unsafe})
        assert reply.status_code == 422
        assert unsafe not in reply.text if unsafe else True
    identifier = str(uuid4())
    reply = c.post("/api/v1/query", json={**payload, field: identifier})
    assert reply.status_code == 200
    assert reply.json()[field] == identifier


def test_lazy_provider_initializes_once_under_simultaneous_requests(monkeypatch):
    created = []
    closed = []

    def factory(config):
        created.append(config)
        return SimpleNamespace(
            generate=lambda request: request, close=lambda: closed.append(1)
        )

    monkeypatch.setattr("app.api.dependencies.OpenAIResponsesProvider", factory)
    provider = _LazyOpenAIProvider(OpenAIProviderConfig())
    ready = threading.Barrier(8)

    def generate(index):
        ready.wait(timeout=5)
        return provider.generate(index)

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(generate, range(8))) == list(range(8))
    assert len(created) == 1
    provider.close()
    provider.close()
    assert closed == [1]
    with pytest.raises(ProviderError):
        provider.generate("closed")


def test_provider_shutdown_waits_for_active_call_and_closes_client(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    closed = []

    def generate(request):
        entered.set()
        assert release.wait(5)
        return request

    monkeypatch.setattr(
        "app.api.dependencies.OpenAIResponsesProvider",
        lambda config: SimpleNamespace(
            generate=generate, close=lambda: closed.append(1)
        ),
    )
    provider = _LazyOpenAIProvider(OpenAIProviderConfig())
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = pool.submit(provider.generate, "result")
        assert entered.wait(5)
        shutdown = pool.submit(provider.close)
        try:
            with provider._condition:
                assert provider._condition.wait_for(lambda: provider._closed, timeout=5)
            assert not shutdown.done()
            assert not closed
            with pytest.raises(ProviderError):
                provider.generate("late call")
        finally:
            release.set()
        assert active.result(timeout=5) == "result"
        shutdown.result(timeout=5)
    assert closed == [1]


def test_runtime_failure_recovers_after_cooldown_without_public_reset(caplog):
    now, calls = [0.0], []
    runtime = FakeRuntime()

    def factory():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("private credential and path")
        return runtime

    manager = RuntimeManager(factory, clock=lambda: now[0])
    assert manager.get() is None
    assert manager.get() is None
    assert len(calls) == 1
    now[0] = 1.1
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(lambda _: manager.get(), range(8))) == [runtime] * 8
    assert len(calls) == 2
    assert "private credential" not in caplog.text
    manager.close()
    assert manager.get() is None


def test_lifespan_closes_runtime_and_adapter_client_once():
    closed = []
    sdk = SimpleNamespace(close=lambda: closed.append(1))
    provider = OpenAIResponsesProvider(OpenAIProviderConfig(), client=sdk)
    runtime = RuntimeService([], provider, OpenAIProviderConfig())
    application = create_app(runtime_factory=lambda: runtime)
    with TestClient(application) as c:
        assert c.get("/api/v1/health").status_code == 200
    assert closed == [1]
    application.state.runtime_manager.close()
    assert closed == [1]


def test_evaluation_uses_runner_documents_instead_of_cached_runtime_snapshot():
    documents, _ = load_dataset(DOCUMENTS_PATH, QUESTIONS_PATH)
    fresh = replace(documents[0], title="Runner snapshot title")
    runtime = RuntimeService([], object(), OpenAIProviderConfig())
    from app.api.models import GenerationRequest, RetrievalRequest

    generation = runtime.resolve_generation(GenerationRequest())
    pipeline = runtime.evaluation_pipeline_factory(
        FixedDecisionPolicy(DecisionSelection(Decision.ANSWER)),
        {fresh.id: fresh},
        runtime.retrieval_configuration(RetrievalRequest()),
        generation,
        None,
    )
    # Retrieval/context inspection does not call the deliberately absent provider.
    matches = pipeline.retriever.search(fresh.text[:150])
    assert matches
    evidence = pipeline._to_context(matches[0], 1)
    assert evidence.title == "Runner snapshot title"
    assert evidence.document_id == fresh.id
    assert not runtime.documents


def test_dataset_fingerprints_match_captured_bytes_even_when_files_change(
    tmp_path, monkeypatch
):
    documents, questions = tmp_path / "documents.jsonl", tmp_path / "questions.jsonl"
    doc_payload = Path(DOCUMENTS_PATH).read_bytes()
    question_payload = Path(QUESTIONS_PATH).read_bytes()
    documents.write_bytes(doc_payload)
    questions.write_bytes(question_payload)
    original_read = Path.read_bytes
    reads = []

    def changing_read(path):
        payload = original_read(path)
        if path in (documents, questions):
            reads.append(path)
            path.write_bytes(b"invalid later content")
        return payload

    monkeypatch.setattr(Path, "read_bytes", changing_read)
    runner = EvaluationRunner(documents, questions)
    assert reads == [documents, questions]
    assert len(runner._documents) == 17
    assert len(runner._questions) == 54
    assert runner._dataset_fingerprint == {
        "documents_sha256": hashlib.sha256(doc_payload).hexdigest(),
        "questions_sha256": hashlib.sha256(question_payload).hexdigest(),
    }


class AdversarialSDK:
    """Exercise the real adapter and pipeline without importing an SDK client."""

    def __init__(self, mode="ANSWER"):
        self.responses = self
        self.mode = mode
        self.calls = []
        self.closed = False

    def with_options(self, **options):
        return self

    def close(self):
        self.closed = True

    def create(self, **parameters):
        self.calls.append(parameters)
        if self.mode == "timeout":
            raise TimeoutError("server-only-credential-do-not-leak")
        if self.mode == "refusal":
            return response(
                "",
                output=[
                    SimpleNamespace(
                        content=[
                            SimpleNamespace(
                                type="refusal", refusal="private provider refusal"
                            )
                        ]
                    )
                ],
            )
        if self.mode == "incomplete":
            return response("private incomplete text", status="incomplete")
        if self.mode == "malformed":
            return response("not JSON; server-only-credential-do-not-leak")
        evidence = json.loads(parameters["input"])["evidence"]
        if parameters["text"]["format"]["name"] == "rag_decision":
            payload = {
                "decision": self.mode,
                "reason": "Mock policy reasoning.",
                "reason_code": "other",
                "supporting_evidence_ids": [evidence[0]["evidence_id"]]
                if self.mode == "ANSWER"
                else [],
                "clarification_question": "Which limit?"
                if self.mode == "CLARIFY"
                else None,
            }
        else:
            first = evidence[0]
            quote = first["text"][:10]
            payload = {
                "answer": "A mock grounded answer.",
                "citations": [
                    {
                        "claim": "A cited claim.",
                        "evidence_id": "not-supplied"
                        if self.mode == "invalid_citation"
                        else first["evidence_id"],
                        "quote": quote,
                        "start_char": first["start_char"],
                        "end_char": first["start_char"] + len(quote),
                    }
                ],
                "unsupported_premises": ["No approval established."],
                "contradictions": ["Mock conflict observation."],
            }
        return response(json.dumps(payload), model="audit-model")


def adversarial_application(monkeypatch, sdk):
    monkeypatch.setenv("RAGBENCH_PROVIDER", "openai")
    monkeypatch.setenv("RAGBENCH_MODEL", "audit-model")
    monkeypatch.setenv("RAGBENCH_API_KEY_ENV", "RAGBENCH_TEST_KEY")
    monkeypatch.setenv("RAGBENCH_TEST_KEY", "server-only-credential-do-not-leak")
    monkeypatch.setenv("RAGBENCH_RETRY_COUNT", "0")
    monkeypatch.setattr("app.api.dependencies.openai_sdk_available", lambda: True)
    monkeypatch.setattr(
        "app.api.dependencies.OpenAIResponsesProvider",
        lambda config: OpenAIResponsesProvider(config, client=sdk),
    )
    return create_app()


@pytest.mark.parametrize("decision", ["ANSWER", "ABSTAIN", "CLARIFY"])
def test_real_http_policy_and_provider_path_preserves_decisions_and_citations(
    monkeypatch, decision
):
    sdk = AdversarialSDK(decision)
    with TestClient(adversarial_application(monkeypatch, sdk)) as c:
        reply = c.post(
            "/api/v1/query",
            json={
                "question": "procurement limits",
                "policy": {"name": "prompt_abstention"},
            },
        )
        assert reply.status_code == 200, reply.text
        body = reply.json()
        assert body["decision"] == decision
        assert body["execution_status"] == "succeeded"
        if decision == "ANSWER":
            citation = body["citations"][0]
            evidence = next(
                item
                for item in body["retrieved_evidence"]
                if item["chunk_id"] == citation["evidence_id"]
            )
            start = citation["start_char"] - evidence["start_char"]
            assert (
                evidence["text"][start : start + len(citation["quote"])]
                == citation["quote"]
            )
            assert body["unsupported_premises"] == ["No approval established."]
            assert body["surfaced_contradictions"] == ["Mock conflict observation."]
        for parameters in sdk.calls:
            assert "tools" not in parameters
            assert parameters["store"] is False
            assert "untrusted" in parameters["instructions"]
            assert set(json.loads(parameters["input"])) == {"question", "evidence"}
    assert sdk.closed


@pytest.mark.parametrize(
    ("mode", "status", "execution"),
    [
        ("timeout", 504, "timed_out"),
        ("refusal", 502, "refused"),
        ("incomplete", 502, "incomplete"),
        ("malformed", 502, "failed"),
        ("invalid_citation", 502, "failed"),
    ],
)
def test_adversarial_provider_failures_never_become_abstentions_or_leak_details(
    monkeypatch, caplog, mode, status, execution
):
    sdk = AdversarialSDK(mode)
    with TestClient(adversarial_application(monkeypatch, sdk)) as c:
        reply = c.post(
            "/api/v1/query",
            json={
                "question": "procurement limits",
                "policy": {"name": "always_answer"},
            },
        )
        assert reply.status_code == status
        assert reply.json()["error"]["execution_status"] == execution
        assert "decision" not in reply.json()
        assert "server-only-credential" not in reply.text + caplog.text
        assert "private provider refusal" not in reply.text + caplog.text


def test_runtime_gold_sentinels_only_appear_in_explicit_evaluation_results(monkeypatch):
    sdk = AdversarialSDK()
    application = adversarial_application(monkeypatch, sdk)
    runtime = application.state.runtime_manager.get()
    runner = runtime.evaluation_runner()
    question = next(
        q for q in runner._questions if q.is_answerable and q.split == "train"
    )
    runner._questions = (
        replace(
            question,
            expected_answer="GOLD_ANSWER_SENTINEL",
            expected_safe_behavior="GOLD_BEHAVIOR_SENTINEL",
        ),
    )
    monkeypatch.setattr(runtime, "evaluation_runner", lambda: runner)
    with TestClient(application) as c:
        started = c.post(
            "/api/v1/evaluations",
            json={
                "split": "train",
                "question_ids": [question.id],
                "policies": [{"name": "prompt_abstention"}],
            },
        )
        assert started.status_code == 200, started.text
        experiment = started.json()["experiment_id"]
        metadata = c.get(f"/api/v1/evaluations/{experiment}")
        assert "GOLD_" not in started.text + metadata.text + json.dumps(sdk.calls)
        results = c.get(f"/api/v1/evaluations/{experiment}/results")
        assert results.status_code == 200, results.text
        assert (
            results.json()["experiment"]["runs"][0]["gold"]["expected_answer"]
            == "GOLD_ANSWER_SENTINEL"
        )


def test_unexpected_errors_do_not_escape_to_server_tracebacks_and_keep_cors(caplog):
    application = create_app(settings=ApiSettings(cors_origins=("https://ui.example",)))

    @application.get("/unexpected")
    def unexpected():
        raise RuntimeError("server-only-credential-and-private-path")

    # Default TestClient rethrows errors escaping ServerErrorMiddleware; this must not.
    c = TestClient(application)
    reply = c.get("/unexpected", headers={"Origin": "https://ui.example"})
    assert reply.status_code == 500
    assert reply.json()["error"]["code"] == "internal_error"
    assert reply.headers["access-control-allow-origin"] == "https://ui.example"
    assert "server-only-credential" not in reply.text + caplog.text
    assert "Traceback" not in caplog.text
    assert c.get("/api/v1/query").headers["allow"] == "POST"


def test_response_validation_errors_hide_values_from_clients_and_server_logs(caplog):
    from app.api.models import QueryResponse

    application = create_app()

    @application.get("/invalid-response", response_model=QueryResponse)
    def invalid_response():
        return {"answer": "server-only-credential-and-private-path"}

    reply = TestClient(application).get("/invalid-response")
    assert reply.status_code == 500
    assert "server-only-credential" not in reply.text + caplog.text
    assert "Traceback" not in caplog.text


@pytest.mark.parametrize("method", ["dense", "hybrid"])
def test_unsupported_retrieval_never_falls_back_to_bm25(monkeypatch, method):
    sdk = AdversarialSDK()
    with TestClient(adversarial_application(monkeypatch, sdk)) as c:
        reply = c.post(
            "/api/v1/query",
            json={
                "question": "Q?",
                "retrieval": {"method": method},
                "policy": {"name": "always_answer"},
            },
        )
        assert reply.status_code == 422
        assert not sdk.calls


def test_empty_retrieval_abstains_without_calling_provider_and_long_question_rejected(
    monkeypatch,
):
    sdk = AdversarialSDK()
    with TestClient(adversarial_application(monkeypatch, sdk)) as c:
        payload = {
            "question": "zzzz_no_corpus_term_92fa623",
            "policy": {"name": "threshold", "score_type": "bm25", "threshold": 0.1},
        }
        reply = c.post("/api/v1/query", json=payload)
        assert reply.status_code == 200
        assert reply.json()["decision"] == "ABSTAIN"
        assert reply.json()["retrieved_evidence"] == []
        assert not sdk.calls
        reply = c.post("/api/v1/query", json={**payload, "question": "x" * 8001})
        assert reply.status_code == 422
        assert not sdk.calls


def test_lazy_provider_construction_failure_can_recover_without_client_leak(
    monkeypatch,
):
    attempts, closed = [], []

    def factory(config):
        attempts.append(1)
        if len(attempts) == 1:
            raise ProviderError(
                ProviderErrorKind.CONFIGURATION, "Missing configuration"
            )
        return SimpleNamespace(
            generate=lambda value: value, close=lambda: closed.append(1)
        )

    monkeypatch.setattr("app.api.dependencies.OpenAIResponsesProvider", factory)
    provider = _LazyOpenAIProvider(OpenAIProviderConfig())
    with pytest.raises(ProviderError):
        provider.generate("first")
    assert provider.generate("second") == "second"
    assert len(attempts) == 2
    provider.close()
    assert closed == [1]
