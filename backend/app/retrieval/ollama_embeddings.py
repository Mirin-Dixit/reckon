"""Bounded local Ollama Embedder implementation; no downloads or fallback."""

from __future__ import annotations

import hashlib
import json
import math
import re
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

from app.generation.config import validate_ollama_url
from app.generation.contracts import ProviderError, ProviderErrorKind
from app.generation.providers.ollama import JsonTransport, LocalHttpTransport
from app.retrieval.dense import validate_vector
from app.retrieval.resources import RAM_RESERVE_BYTES, available_ram_bytes


@dataclass(frozen=True)
class EmbeddingIdentity:
    """Exact weights and input transformation used to produce cached vectors."""

    model: str
    digest: str
    dimensions: int
    preprocessing: str = "verbatim-v1"
    context_size: int = 256
    server_version: str = "unknown"
    execution: str = "ollama-cpu-f16-v1"

    def __post_init__(self) -> None:
        if not isinstance(self.digest, str) or not re.fullmatch(
            r"[0-9a-f]{64}", self.digest,
        ):
            raise ValueError("Embedding identity requires a SHA-256 model digest")
        if type(self.dimensions) is not int or not 1 <= self.dimensions <= 1024:
            raise ValueError("Invalid embedding dimensions")
        if type(self.context_size) is not int or not 1 <= self.context_size <= 8192:
            raise ValueError("Invalid embedding context")
        if any(not isinstance(s, str) or not s.strip() for s in (
            self.model, self.preprocessing, self.server_version, self.execution,
        )):
            raise ValueError("Embedding identity fields must be non-empty strings")


def checked_vectors(value: object, count: int, dimensions: int) -> list[list[float]]:
    """Validate count, shape, finite values and safe nonzero magnitude."""
    if not isinstance(value, list) or len(value) != count:
        raise ValueError("Embedding count does not match inputs")
    result = []
    for vector in value:
        validate_vector(vector, expected_dim=dimensions)
        if any(abs(v) > 1_000_000 for v in vector):
            raise ValueError("Embedding magnitude is unsafe")
        if not 1e-12 <= math.hypot(*vector) <= 1_000_000:
            raise ValueError("Embedding must have a finite nonzero norm")
        result.append([float(v) for v in vector])
    return result


class OllamaEmbedder:
    """Approved MiniLM only, CPU batches, zero retries, one call at a time.

    Injected transports and memory callbacks are trusted Python, not sandboxed.
    RAM checks are snapshots, not an OS memory reservation or continuous monitor.
    """

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "all-minilm:22m",
        timeout_seconds: float = 60,
        max_requests: int = 256,
        transport: JsonTransport | None = None,
        memory_reader: Callable[[], int] = available_ram_bytes,
    ) -> None:
        validate_ollama_url(base_url)
        if model != "all-minilm:22m":
            raise ValueError("Only the approved all-minilm:22m model is supported")
        if (isinstance(timeout_seconds, bool) or not math.isfinite(timeout_seconds)
                or not 0 < timeout_seconds <= 120):
            raise ValueError("Invalid embedding timeout")
        if type(max_requests) is not int or not 0 <= max_requests <= 1024:
            raise ValueError("Invalid embedding request budget")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_requests = max_requests
        self._transport = transport or LocalHttpTransport(base_url)
        self._memory = memory_reader
        self._lock = threading.Lock()
        self._attempts = 0
        self._identity: EmbeddingIdentity | None = None

    @property
    def attempts(self) -> int:
        return self._attempts

    def identity(self) -> EmbeddingIdentity:
        """Inspect local inventory only; pin identity and reject weight changes."""
        with self._lock:
            return self._inspect(time.monotonic() + self.timeout_seconds)

    def _inspect(self, deadline: float) -> EmbeddingIdentity:
        def read(method, path, body=None):
            return self._transport(method, path, body, self._remaining(deadline))

        items = read("GET", "/api/tags").get("models")
        if not isinstance(items, list):
            raise ValueError("Invalid local model inventory")
        matches = [x for x in items if isinstance(x, dict)
                   and x.get("name", x.get("model")) == self.model]
        if len(matches) != 1:
            raise ValueError("Approved embedding model is not uniquely installed")
        item = matches[0]
        self._local_weights(item)
        shown = read("POST", "/api/show", {"model": self.model})
        if shown.get("remote_host") or shown.get("remote_model"):
            raise ValueError("Remote embedding aliases are forbidden")
        info = shown.get("model_info")
        if (not isinstance(info, dict) or info.get("general.architecture") != "bert"
                or info.get("bert.embedding_length") != 384):
            raise ValueError("Unexpected embedding architecture or dimensions")
        capabilities = shown.get("capabilities")
        if not isinstance(capabilities, list) or "embedding" not in capabilities:
            raise ValueError("Model does not advertise embedding capability")
        version = read("GET", "/api/version").get("version")
        identity = EmbeddingIdentity(
            self.model, item.get("digest"), 384,
            server_version=version if isinstance(version, str) else "unknown",
        )
        if self._identity is not None and identity != self._identity:
            raise ValueError("Embedding model changed; construct a new embedder")
        self._identity = identity
        return identity

    @staticmethod
    def _local_weights(item: dict) -> None:
        if (item.get("remote_host") or item.get("remote_model")
                or type(item.get("size")) is not int or item["size"] <= 0):
            raise ValueError("Local embedding weights are required")

    @staticmethod
    def _remaining(deadline: float) -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProviderError(ProviderErrorKind.TIMEOUT, "Local embeddings timed out")
        return remaining

    def _check_memory(self, *, before_inference: bool = False) -> None:
        available = self._memory()
        # A conservative initial allowance for the small CPU encoder. Actual
        # memory is checked again after each batch; this is not a hard OS limit.
        minimum = RAM_RESERVE_BYTES + (512 * 1024**2 if before_inference else 0)
        if type(available) is not int or available < minimum:
            raise ValueError("Embedding RAM safety reserve is unavailable")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed at most 256 verbatim inputs in batches of eight; never truncate."""
        if not isinstance(texts, list) or len(texts) > 256:
            raise ValueError("Embedding inputs exceed the bounded collection size")
        if any(not isinstance(t, str) or not t.strip() or len(t.encode('utf-8')) > 8192
               for t in texts):
            raise ValueError("Embedding inputs must be nonempty bounded strings")
        if not texts:
            return []
        deadline = time.monotonic() + self.timeout_seconds
        if not self._lock.acquire(timeout=self.timeout_seconds):
            raise ProviderError(ProviderErrorKind.TIMEOUT, "Embedding slot timed out")
        try:
            self._check_memory()
            identity = self._inspect(deadline)
            vectors = []
            for start in range(0, len(texts), 8):
                batch = texts[start:start + 8]
                payload = {
                    "model": self.model, "input": batch, "truncate": False,
                    "options": {"num_ctx": 256, "num_gpu": 0}, "keep_alive": 0,
                }
                if len(json.dumps(payload).encode()) > 65_536:
                    raise ValueError("Embedding request exceeds byte limit")
                self._check_memory(before_inference=True)
                if self._attempts >= self.max_requests:
                    raise ValueError("Embedding attempt budget exhausted")
                self._attempts += 1
                reply = self._transport(
                    "POST", "/api/embed", payload, self._remaining(deadline),
                )
                self._check_memory()
                if reply.get("model") != self.model or "error" in reply:
                    raise ValueError("Invalid embedding response")
                vectors.extend(checked_vectors(
                    reply.get("embeddings"), len(batch), identity.dimensions,
                ))
            if self._inspect(deadline) != identity:
                raise ValueError("Embedding identity changed during execution")
            return vectors
        except (ValueError, TypeError, OverflowError) as error:
            raise ProviderError(
                ProviderErrorKind.MALFORMED_RESPONSE,
                "Local embedding validation failed", provider="ollama",
            ) from error
        finally:
            self._lock.release()

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]

    def identity_fingerprint(self) -> str:
        """Stable diagnostic identity; no machine paths or corpus labels."""
        data = json.dumps(asdict(self.identity()), sort_keys=True).encode()
        return hashlib.sha256(data).hexdigest()
