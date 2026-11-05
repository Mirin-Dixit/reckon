"""P1 offline controls and actual SDK-to-HTTP wiring; no external requests."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from app.api.dependencies import RuntimeService
from app.api.main import create_app
from app.api.models import GenerationRequest as ApiGenerationRequest
from app.generation.config import OpenAIProviderConfig
from app.generation.contracts import (
    GenerationRequest,
    ProviderError,
    ProviderErrorKind,
    TokenUsage,
)
from app.generation.pipeline import _combined_usage
from app.generation.providers.openai_responses import OpenAIResponsesProvider
from app.ingestion.schema import Document
from fastapi.testclient import TestClient
from test_api_hardening import AdversarialSDK, adversarial_application
from test_openai_provider import FakeClient, response


@pytest.mark.parametrize(
    "values",
    [
        {"RECKON_MAX_OUTPUT_TOKENS": "0"},
        {"RECKON_MAX_OUTPUT_TOKENS": "32769"},
        {"RECKON_MAX_OUTPUT_TOKENS": ""},
        {"RECKON_TIMEOUT_SECONDS": "121"},
        {"RECKON_MAX_PROVIDER_REQUESTS": "-1"},
        {"RECKON_MAX_PROVIDER_REQUESTS": "101"},
        {"RECKON_RETRY_COUNT": "6"},
    ],
)
def test_invalid_runtime_controls_fail_closed(values):
    with pytest.raises(ValueError):
        OpenAIProviderConfig.from_env(values)


def test_default_output_limit_and_server_ceiling():
    config = OpenAIProviderConfig.from_env({})
    assert config.max_output_tokens == 1024
    assert config.max_provider_requests == 4
    runtime = RuntimeService([], object(), config)
    assert (
        runtime.resolve_generation(ApiGenerationRequest())["max_output_tokens"] == 1024
    )
    with pytest.raises(ProviderError):
        runtime.resolve_generation(ApiGenerationRequest(max_output_tokens=1025))
    sdk = FakeClient([response("ok")])
    provider = OpenAIResponsesProvider(config, client=sdk)
    provider.generate(GenerationRequest("trusted", "question", "mock"))
    assert sdk.responses.calls[0]["max_output_tokens"] == 1024


def test_retry_attempts_consume_budget_and_exhaustion_does_not_retry():
    sdk = FakeClient([TimeoutError("private"), TimeoutError("private")])
    provider = OpenAIResponsesProvider(
        OpenAIProviderConfig(retry_count=5, max_provider_requests=2),
        client=sdk,
        sleep_fn=lambda _: None,
    )
    with pytest.raises(ProviderError) as error:
        provider.generate(GenerationRequest("trusted", "question", "mock"))
    assert error.value.kind is ProviderErrorKind.RATE_LIMIT
    assert not error.value.retryable
    assert len(sdk.responses.calls) == 2


def test_concurrent_calls_cannot_exceed_budget():
    class SDK:
        responses = None

        def __init__(self):
            self.responses = self
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            return response("ok")

    sdk = SDK()
    provider = OpenAIResponsesProvider(
        OpenAIProviderConfig(max_provider_requests=2),
        client=sdk,
    )

    def generate(_):
        try:
            provider.generate(GenerationRequest("trusted", "question", "mock"))
            return True
        except ProviderError:
            return False

    with ThreadPoolExecutor(max_workers=8) as workers:
        assert sum(workers.map(generate, range(12))) == 2
    assert sdk.calls == 2


@pytest.mark.parametrize(
    "policy,expected,calls",
    [
        ({"name": "always_answer"}, "ANSWER", 1),
        ({"name": "prompt_abstention"}, "ANSWER", 2),
        ({"name": "threshold", "score_type": "bm25", "threshold": -1}, "ANSWER", 1),
    ],
)
def test_all_bm25_policy_paths_use_bounded_generation(
    monkeypatch, policy, expected, calls
):
    sdk = AdversarialSDK("ANSWER")
    with TestClient(adversarial_application(monkeypatch, sdk)) as client:
        reply = client.post(
            "/api/v1/query",
            json={
                "question": "procurement approval",
                "policy": policy,
            },
        )
        assert reply.status_code == 200, reply.text
        assert reply.json()["decision"] == expected
        assert len(sdk.calls) == calls
        assert all(call["max_output_tokens"] == 1024 for call in sdk.calls)
        assert all(call["store"] is False and "tools" not in call for call in sdk.calls)


def test_rate_limit_through_http_is_failure_not_abstention(monkeypatch):
    class RateLimitError(Exception):
        pass

    class RateLimitedSDK(AdversarialSDK):
        def create(self, **kwargs):
            raise RateLimitError("private credential must never escape")

    with TestClient(adversarial_application(monkeypatch, RateLimitedSDK())) as client:
        reply = client.post(
            "/api/v1/query",
            json={
                "question": "procurement approval",
                "policy": {"name": "always_answer"},
            },
        )
    assert reply.status_code == 502
    assert reply.json()["error"]["execution_status"] == "failed"
    assert "ABSTAIN" not in reply.text
    assert "private credential" not in reply.text


def test_prompt_answer_accounts_for_both_successful_provider_calls(monkeypatch):
    class MeteredSDK(AdversarialSDK):
        def create(self, **kwargs):
            result = super().create(**kwargs)
            from types import SimpleNamespace

            result.usage = SimpleNamespace(
                input_tokens=90, output_tokens=30, total_tokens=120,
            )
            return result

    sdk = MeteredSDK("ANSWER")
    with TestClient(adversarial_application(monkeypatch, sdk)) as client:
        reply = client.post("/api/v1/query", json={
            "question": "procurement approval",
            "policy": {"name": "prompt_abstention"},
        })
    assert reply.status_code == 200
    assert len(sdk.calls) == 2
    assert reply.json()["token_usage"] == {
        "input_tokens": 180, "output_tokens": 60, "total_tokens": 240,
    }
    assert _combined_usage(
        TokenUsage(input_tokens=10), TokenUsage(output_tokens=5),
    ) == TokenUsage()


def test_exhausted_budget_through_http_is_failure(monkeypatch):
    sdk = AdversarialSDK("ANSWER")
    monkeypatch.setenv("RECKON_MAX_PROVIDER_REQUESTS", "1")
    with TestClient(adversarial_application(monkeypatch, sdk)) as client:
        reply = client.post("/api/v1/query", json={
            "question": "procurement approval",
            "policy": {"name": "prompt_abstention"},
        })
    assert reply.status_code == 502
    assert reply.json()["error"]["execution_status"] == "failed"
    assert "ABSTAIN" not in reply.text
    assert len(sdk.calls) == 1


def test_installed_sdk_via_loopback_openai_endpoint(monkeypatch):
    """Exercise SDK parameter serialization and response parsing without OpenAI I/O."""
    openai = pytest.importorskip("openai")
    real_openai = openai.OpenAI
    calls = []
    text = "Procurement requires written approval."

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(request)
            evidence = json.loads(request["input"])["evidence"][0]
            payload = {
                "answer": text,
                "citations": [
                    {
                        "claim": text,
                        "evidence_id": evidence["evidence_id"],
                        "quote": text,
                    }
                ],
                "unsupported_premises": [],
                "contradictions": [],
            }
            body = json.dumps(
                {
                    "id": "resp-offline",
                    "object": "response",
                    "created_at": 0,
                    "status": "completed",
                    "model": "offline-sdk-model",
                    "output": [
                        {
                            "id": "msg-offline",
                            "type": "message",
                            "role": "assistant",
                            "status": "completed",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(payload),
                                    "annotations": [],
                                }
                            ],
                        }
                    ],
                    "usage": {
                        "input_tokens": 90,
                        "output_tokens": 30,
                        "total_tokens": 120,
                    },
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("x-request-id", "req-offline")
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        monkeypatch.setattr(
            openai,
            "OpenAI",
            lambda **kwargs: real_openai(
                **kwargs,
                base_url=f"http://127.0.0.1:{server.server_port}/v1",
            ),
        )
        monkeypatch.setenv("RECKON_TEST_KEY", "offline-only-canary")
        config = OpenAIProviderConfig(
            model="offline-sdk-model",
            api_key_env_var="RECKON_TEST_KEY",
            retry_count=0,
        )
        provider = OpenAIResponsesProvider(config)
        runtime = RuntimeService(
            [
                Document("offline", "Procurement", "https://example.test/policy", text),
            ],
            provider,
            config,
        )
        with TestClient(create_app(runtime_factory=lambda: runtime)) as client:
            reply = client.post(
                "/api/v1/query",
                json={
                    "question": "What approval does Procurement require?",
                    "policy": {"name": "always_answer"},
                },
            )
            assert reply.status_code == 200, reply.text
            observed = reply.json()
            assert observed["decision"] == "ANSWER"
            assert observed["citations"][0]["quote"] == text
            assert observed["provider"]["request_id"] == "req-offline"
            assert observed["provider"]["model"] == "offline-sdk-model"
            assert observed["token_usage"]["total_tokens"] == 120
            assert "offline-only-canary" not in reply.text
        assert len(calls) == 1
        assert calls[0]["text"]["format"]["strict"] is True
        assert calls[0]["max_output_tokens"] == 1024
        assert calls[0]["store"] is False and "tools" not in calls[0]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        assert not worker.is_alive()
