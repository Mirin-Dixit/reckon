"""Focused regression tests for targeted RAG reliability fixes."""

import json
import pytest
from app.generation.config import OllamaProviderConfig
from app.generation.contracts import (
    EvidenceContext,
    ExecutionStatus,
    GenerationRequest,
    GenerationResponse,
    ModelSettings,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
    StructuredOutputSpec,
)
from app.generation.answering import ProviderAnswerGenerator
from app.generation.pipeline import _execution_status
from app.generation.providers.ollama import LocalHttpTransport, OllamaProvider
from app.retrieval.runtime import RetrievalFailure


class FakeOllamaTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, method, path, payload, timeout):
        self.calls.append((method, path, payload))
        if path == "/api/tags":
            return {
                "models": [
                    {
                        "name": "qwen3:4b",
                        "size": 2_500_000_000,
                        "digest": "a" * 64,
                        "details": {"quantization_level": "Q4_K_M"},
                    }
                ]
            }
        if path == "/api/show":
            return {"model_info": {"general.architecture": "qwen3"}}
        if path == "/api/version":
            return {"version": "test-v1"}
        assert path == "/api/chat"
        return {
            "model": payload["model"],
            "done": True,
            "done_reason": "stop",
            "message": {
                "role": "assistant",
                "content": json.dumps({"ok": True}),
            },
            "prompt_eval_count": 40,
            "eval_count": 10,
            "total_duration": 5_000_000,
        }


def make_request():
    return GenerationRequest(
        system_instruction="Follow evidence strictly.",
        user_content="Question",
        model="qwen3:4b",
        settings=ModelSettings(max_output_tokens=64),
        structured_output=StructuredOutputSpec(
            "test_spec",
            {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
                "additionalProperties": False,
            },
        ),
    )


def test_ollama_metadata_is_cached_and_think_is_explicit():
    transport = FakeOllamaTransport()
    provider = OllamaProvider(OllamaProviderConfig(), transport=transport)

    assert provider.available("qwen3:4b") is True
    initial_tag_calls = sum(1 for _, path, _ in transport.calls if path == "/api/tags")
    initial_show_calls = sum(1 for _, path, _ in transport.calls if path == "/api/show")
    assert initial_tag_calls == 1
    assert initial_show_calls == 1

    # Second call (generate) must reuse the cached metadata and template allowance
    result = provider.generate(make_request())
    assert result.structured_content == {"ok": True}

    tag_calls_after = sum(1 for _, path, _ in transport.calls if path == "/api/tags")
    show_calls_after = sum(1 for _, path, _ in transport.calls if path == "/api/show")
    assert tag_calls_after == 1, "Metadata /api/tags should be cached"
    assert show_calls_after == 1, "Metadata /api/show should be cached"

    # Verify think: False is explicitly present in the generation payload
    chat_calls = [p for _, path, p in transport.calls if path == "/api/chat"]
    assert len(chat_calls) == 1
    assert chat_calls[0].get("think") is False


def test_local_transport_non_positive_timeout_raises_timeout_error():
    transport = LocalHttpTransport("http://127.0.0.1:11434")
    with pytest.raises(ProviderError) as exc_info:
        transport("POST", "/api/chat", {}, timeout=0.0)
    assert exc_info.value.kind == ProviderErrorKind.TIMEOUT

    with pytest.raises(ProviderError) as exc_info_neg:
        transport("POST", "/api/chat", {}, timeout=-1.5)
    assert exc_info_neg.value.kind == ProviderErrorKind.TIMEOUT


def test_pipeline_execution_status_classifies_timeouts_accurately():
    timeout_failure = RetrievalFailure("embedding_timeout", 504, "timed_out")
    assert _execution_status(timeout_failure) == ExecutionStatus.TIMED_OUT

    generic_failure = RetrievalFailure("other_error", 502, "failed")
    assert _execution_status(generic_failure) == ExecutionStatus.FAILED

    assert _execution_status(TimeoutError("socket deadline")) == ExecutionStatus.TIMED_OUT


def test_uncited_answer_populates_unsupported_premises():
    class MockUncitedProvider:
        def generate(self, req):
            content = json.dumps({
                "answer": "Parametric Python definition.",
                "citations": [],
                "unsupported_premises": [],
                "contradictions": [],
            })
            return GenerationResponse(
                content=content,
                structured_content=json.loads(content),
                metadata=ProviderMetadata("mock", req.model),
                status=ExecutionStatus.SUCCEEDED,
            )

    generator = ProviderAnswerGenerator(MockUncitedProvider(), "qwen3:4b")
    text = "Unrelated travel text."
    context = EvidenceContext(
        chunk_id="chunk1", document_id="doc1", text=text,
        start_char=0, end_char=len(text), title="Travel", source_url="https://test",
        version="v1", source_date="2026-01-01", domain="travel",
    )
    res = generator.generate("What is Python?", (context,))
    assert res.citations == ()
    assert "Answer contains no grounded citations in retrieved evidence." in res.unsupported_premises
