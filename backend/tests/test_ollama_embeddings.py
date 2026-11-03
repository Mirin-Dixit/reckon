"""P2 Batch 1: mocked embedding transport only; no installed model required."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
from app.generation.contracts import ProviderError, ProviderErrorKind
from app.generation.providers.ollama import LocalHttpTransport
from app.retrieval.dense import Embedder
from app.retrieval.ollama_embeddings import EmbeddingIdentity, OllamaEmbedder
from app.retrieval.resources import RAM_RESERVE_BYTES


class Transport:
    def __init__(self):
        self.calls = []
        self.tag = {"name": "all-minilm:22m", "size": 46_000_000,
                    "digest": "a" * 64}
        self.shown = {"capabilities": ["embedding"], "model_info": {
            "general.architecture": "bert", "bert.embedding_length": 384,
        }}
        self.mutate = lambda reply: reply

    def __call__(self, method, path, payload, timeout):
        assert 0 < timeout <= 120
        self.calls.append((method, path, deepcopy(payload)))
        if path == "/api/tags":
            return {"models": [self.tag]}
        if path == "/api/show":
            return self.shown
        if path == "/api/version":
            return {"version": "offline"}
        assert path == "/api/embed"
        return self.mutate({"model": "all-minilm:22m", "embeddings": [
            [float(len(t)), *([0.0] * 383)] for t in payload["input"]
        ]})


def embedder(transport=None, **kwargs):
    return OllamaEmbedder(
        transport=transport or Transport(),
        memory_reader=kwargs.pop("memory_reader", lambda: 4 * 1024**3), **kwargs,
    )


def test_protocol_batching_preserves_order_text_and_local_options():
    transport = Transport()
    model = embedder(transport)
    assert isinstance(model, Embedder)
    texts = ["  original text  "] + ["x" * i for i in range(1, 17)]
    vectors = model.embed_texts(texts)
    assert [v[0] for v in vectors] == [len(t) for t in texts]
    calls = [p for _, path, p in transport.calls if path == "/api/embed"]
    assert [len(p["input"]) for p in calls] == [8, 8, 1]
    assert [t for p in calls for t in p["input"]] == texts
    assert all(p["truncate"] is False and p["keep_alive"] == 0 for p in calls)
    assert all(p["options"] == {"num_ctx": 256, "num_gpu": 0} for p in calls)
    assert model.attempts == 3
    assert model.embed_query("q")[0] == 1


def test_identity_and_empty_inputs_do_not_infer():
    transport = Transport()
    model = embedder(transport)
    assert model.embed_texts([]) == [] and not transport.calls
    assert model.identity().digest == "a" * 64
    assert len(model.identity_fingerprint()) == 64
    assert model.attempts == 0
    assert not any(path == "/api/embed" for _, path, _ in transport.calls)


@pytest.mark.parametrize("value", [None, "text", [""], [" "], [False],
                                  ["x" * 8193], ["q"] * 257])
def test_invalid_inputs_never_call_transport(value):
    transport = Transport()
    with pytest.raises(ValueError):
        embedder(transport).embed_texts(value)
    assert not transport.calls


@pytest.mark.parametrize("kwargs", [
    {"model": "all-minilm:latest"}, {"model": "remote/model:tag"},
    {"base_url": "https://ollama.com"}, {"base_url": "http://localhost:11434"},
    {"base_url": "http://0.0.0.0:11434"},
    {"base_url": "http://user:secret@127.0.0.1"},
    {"timeout_seconds": 0}, {"timeout_seconds": float("nan")},
    {"timeout_seconds": 121}, {"max_requests": True}, {"max_requests": -1},
])
def test_configuration_rejects_unsafe_values(kwargs):
    with pytest.raises(ValueError):
        embedder(**kwargs)


@pytest.mark.parametrize("field", ["remote_host", "remote_model"])
@pytest.mark.parametrize("location", ["tag", "shown"])
def test_remote_aliases_never_infer(field, location):
    transport = Transport()
    getattr(transport, location)[field] = "remote"
    with pytest.raises(ProviderError):
        embedder(transport).embed_query("q")
    assert not any(path == "/api/embed" for _, path, _ in transport.calls)
    if location == "tag":
        assert [p for _, p, _ in transport.calls] == ["/api/tags"]


@pytest.mark.parametrize("bad", [None, [], [[0.0] * 384], [[True] * 384],
                               [[1.0] * 383], [[float("nan")] * 384],
                               [[float("inf")] * 384], [[1e308] * 384],
                               [[1e-300] * 384], [[1.0] * 384] * 2])
def test_invalid_vectors_are_rejected_without_retry(bad):
    transport = Transport()
    transport.mutate = lambda reply: {**reply, "embeddings": bad}
    model = embedder(transport)
    with pytest.raises(ProviderError):
        model.embed_query("q")
    assert model.attempts == 1


@pytest.mark.parametrize("change", ["size", "digest", "architecture", "capability"])
def test_missing_or_wrong_local_weights_fail_before_embedding(change):
    transport = Transport()
    if change == "size":
        transport.tag["size"] = 0
    elif change == "digest":
        transport.tag["digest"] = None
    elif change == "architecture":
        transport.shown["model_info"]["general.architecture"] = "qwen3"
    else:
        transport.shown["capabilities"] = []
    with pytest.raises(ProviderError):
        embedder(transport).embed_query("q")
    assert not any(path == "/api/embed" for _, path, _ in transport.calls)


def test_mutable_tag_changes_are_rejected():
    transport = Transport()
    model = embedder(transport)
    model.identity()
    transport.tag["digest"] = "b" * 64
    with pytest.raises(ProviderError):
        model.embed_query("q")
    assert model.attempts == 0


def test_model_change_during_embedding_is_rejected():
    transport = Transport()

    def mutate(reply):
        transport.tag["digest"] = "b" * 64
        return reply

    transport.mutate = mutate
    with pytest.raises(ProviderError):
        embedder(transport).embed_query("q")


@pytest.mark.parametrize("low_after", [0, 2, 3])
def test_ram_reserve_before_and_after_batches(low_after):
    transport = Transport()
    readings = iter([4 * 1024**3] * low_after + [RAM_RESERVE_BYTES - 1] * 10)
    model = embedder(transport, memory_reader=lambda: next(readings))
    with pytest.raises(ProviderError):
        model.embed_texts(["q"] * 9)
    assert model.attempts <= 1


def test_failed_attempt_consumes_budget_and_does_not_retry():
    transport = Transport()

    def fail(reply):
        raise ProviderError(ProviderErrorKind.TIMEOUT, "safe timeout")

    transport.mutate = fail
    model = embedder(transport, max_requests=1)
    with pytest.raises(ProviderError):
        model.embed_query("q")
    with pytest.raises(ProviderError):
        model.embed_query("q")
    assert model.attempts == 1


def test_concurrent_calls_share_budget_and_release_lock_after_failure():
    transport = Transport()
    active = []

    def slow(reply):
        active.append(threading.get_ident())
        assert len(active) == 1
        time.sleep(.01)
        active.pop()
        return reply

    transport.mutate = slow
    model = embedder(transport, max_requests=2)

    def run(_):
        try:
            model.embed_query("q")
            return 1
        except ProviderError:
            return 0

    with ThreadPoolExecutor(max_workers=4) as workers:
        assert sum(workers.map(run, range(4))) == 2
    assert model.attempts == 2


def test_identity_requires_valid_dimension_and_digest():
    with pytest.raises(ValueError):
        EmbeddingIdentity("m", "a" * 64, True)
    with pytest.raises(ValueError):
        EmbeddingIdentity("m", "invalid", 384)


def test_preflight_reserves_additional_encoder_headroom():
    transport = Transport()
    model = embedder(transport, memory_reader=lambda: RAM_RESERVE_BYTES + 1)
    with pytest.raises(ProviderError):
        model.embed_query("q")
    assert model.attempts == 0


def test_missing_model_and_duplicate_inventory_never_infer():
    for records in ([], [Transport().tag, Transport().tag]):
        def inventory(method, path, payload, timeout):
            assert path == "/api/tags"
            return {"models": records}

        model = embedder(inventory)
        with pytest.raises(ProviderError):
            model.embed_query("q")
        assert model.attempts == 0


def test_large_escaped_payload_is_bounded_before_embedding():
    transport = Transport()
    with pytest.raises(ProviderError):
        embedder(transport).embed_texts(["\u03c0" * 4096] * 8)
    assert not any(path == "/api/embed" for _, path, _ in transport.calls)


@pytest.mark.parametrize("status,body,content_type", [
    (200, b'{"model":"all-minilm:22m","embeddings":[[1,2]]}',
     "application/json"),
    (302, b"", "application/json"),
    (200, b"{" , "application/json"),
    (200, b"{}", "text/html"),
    (200, b" " * 1_048_577, "application/json"),
    (404, b"{}", "application/json"),
], ids=["valid", "redirect", "malformed", "content-type", "oversized", "missing"])
def test_actual_transport_bounds_cleanup_without_network(
    monkeypatch, status, body, content_type,
):
    connections = []

    class Response:
        def __init__(self):
            self.status = status

        def getheader(self, name, default=None):
            return content_type if name == "Content-Type" else default

        def read(self, size):
            assert size == 1_048_577
            return body[:size]

    class Connection:
        def __init__(self, host, port, timeout):
            assert host == "127.0.0.1" and port == 11434
            connections.append(self)
            self.closed = False

        def request(self, method, path, body, headers):
            assert path == "/api/embed"
            assert "Authorization" not in headers and "Cookie" not in headers
            assert json_body(body)["truncate"] is False

        def getresponse(self):
            return Response()

        def close(self):
            self.closed = True

    def json_body(body):
        import json

        return json.loads(body)

    monkeypatch.setattr("http.client.HTTPConnection", Connection)
    transport = LocalHttpTransport("http://127.0.0.1:11434")
    payload = {"model": "all-minilm:22m", "input": ["q"], "truncate": False}
    if status == 200 and content_type == "application/json" and body.startswith(
        b'{"model"',
    ):
        assert transport("POST", "/api/embed", payload, 2)["embeddings"] == [[1, 2]]
    else:
        with pytest.raises(ProviderError):
            transport("POST", "/api/embed", payload, 2)
    assert len(connections) == 1 and connections[0].closed
