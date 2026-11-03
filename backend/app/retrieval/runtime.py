"""Snapshot-specific index reuse for the local API; no gold-data loading."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from app.generation.contracts import ProviderError, ProviderErrorKind
from app.ingestion.chunking import chunk_documents
from app.ingestion.schema import Document
from app.retrieval.bm25 import BM25Index, ScoredChunk
from app.retrieval.cache import DenseIndexCache, IdentifiedEmbedder
from app.retrieval.hybrid import HybridIndex
from app.retrieval.ollama_embeddings import OllamaEmbedder


class RetrievalFailure(Exception):
    """Safe, public retrieval setup error, separate from intentional abstention."""

    def __init__(self, code: str, status: int = 503,
                 execution_status: str = "failed"):
        super().__init__(code)
        self.code = code
        self.status = status
        self.execution_status = execution_status


class HybridRetriever:
    """Bind candidate depth without changing the existing RRF implementation."""

    def __init__(self, index: HybridIndex, candidate_k: int | None):
        self.index = index
        self.candidate_k = candidate_k

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        return self.index.search(query, top_k=top_k, candidate_k=self.candidate_k)

    def score_parameters(self, query: str, results: list[ScoredChunk],
                         top_k: int) -> dict:
        # DenseIndex returns a candidate for every chunk on a nonempty query.
        # Inspect lexical participation without another embedding call; ranking
        # and fusion still execute only through the unchanged HybridIndex.
        lexical = bool(self.index.bm25_index.search(query, top_k=1))
        return {"rrf_k": self.index.rrf_k,
                "rank_lists": int(lexical) + int(bool(results)),
                "configured_rank_lists": 2,
                "effective_candidate_k": self.candidate_k or max(
                    len(self.index.chunks), 50, 3 * top_k,
                )}


class RetrievalRuntime:
    """Bounded per-runtime LRU; dense vectors persist through Batch 1's cache.

    Model/cache settings are server-only. Default BM25 never contacts Ollama.
    Injected Python embedders remain trusted callbacks, not sandboxed code.
    """

    def __init__(self, *, embedder: IdentifiedEmbedder | None = None,
                 cache: DenseIndexCache | None = None):
        self.embedder = embedder
        self.cache = cache
        self._indexes = OrderedDict()
        self._lock = threading.RLock()

    def embedding_configuration(self) -> dict:
        try:
            with self._lock:
                if self.embedder is None:
                    model = os.environ.get("RAGBENCH_EMBEDDING_MODEL")
                    if model is None:
                        raise RetrievalFailure("embedding_not_configured")
                    try:
                        self.embedder = OllamaEmbedder(
                            model=model,
                            base_url=os.environ.get(
                                "RAGBENCH_OLLAMA_URL", "http://127.0.0.1:11434",
                            ),
                        )
                    except (ValueError, TypeError):
                        raise RetrievalFailure(
                            "invalid_embedding_configuration",
                        ) from None
                return asdict(self.embedder.identity())
        except RetrievalFailure:
            raise
        except ProviderError as error:
            code = ("embedding_timeout" if error.kind is ProviderErrorKind.TIMEOUT
                    else "embedding_unavailable")
            raise RetrievalFailure(
                code, 504 if error.kind is ProviderErrorKind.TIMEOUT else 503,
                "timed_out" if error.kind is ProviderErrorKind.TIMEOUT else "failed",
            ) from None
        except (ValueError, TypeError):
            raise RetrievalFailure("embedding_unavailable") from None
        except (OSError, MemoryError, RuntimeError):
            raise RetrievalFailure("retrieval_resource_failure") from None

    def get(self, documents: Mapping[str, Document], config: Mapping):
        """Use exactly supplied documents, including evaluator-provided snapshots."""
        method = config.get("method")
        if method not in {"bm25", "dense", "hybrid"}:
            raise RetrievalFailure("invalid_retrieval_configuration", 422)
        try:
            if method != "bm25":
                if config.get("embedding") != self.embedding_configuration():
                    raise RetrievalFailure("embedding_identity_mismatch", 422)
            fingerprint = hashlib.sha256(json.dumps(
                [doc.to_dict() for doc in documents.values()],
                sort_keys=True, ensure_ascii=False, allow_nan=False,
            ).encode()).hexdigest()
            key = hashlib.sha256(json.dumps(
                [fingerprint, dict(config)], sort_keys=True, allow_nan=False,
            ).encode()).hexdigest()
            with self._lock:
                if method != "bm25":
                    if self.cache is None:
                        self.cache = DenseIndexCache(Path(os.environ.get(
                            "RAGBENCH_DENSE_CACHE_DIR", ".ragbench-cache/dense",
                        )))
                    try:
                        self.cache._check_memory()
                    except (ValueError, RuntimeError):
                        raise RetrievalFailure("retrieval_resource_failure") from None
                if method == "hybrid":
                    candidate = config.get("candidate_k")
                    rrf = config.get("rrf_k")
                    if (type(rrf) is not int or not 1 <= rrf <= 1000
                            or (candidate is not None and (
                                type(candidate) is not int
                                or not config["top_k"] <= candidate <= 256))):
                        raise RetrievalFailure("invalid_retrieval_configuration", 422)
                if key in self._indexes:
                    self._indexes.move_to_end(key)
                    return self._indexes[key]
                chunks = chunk_documents(
                    list(documents.values()), chunk_size=config["chunking"]["size"],
                    chunk_overlap=config["chunking"]["overlap"],
                )
                if method == "bm25":
                    index = BM25Index(chunks, k1=config["index"]["k1"],
                                      b=config["index"]["b"])
                else:
                    cached = self.cache.get_or_build(
                        chunks, self.embedder, snapshot_fingerprint=fingerprint,
                        chunking=config["chunking"],
                    )
                    dense = cached.index
                    if method == "dense":
                        index = dense
                    else:
                        bm25 = BM25Index(chunks, k1=config["index"]["k1"],
                                         b=config["index"]["b"])
                        index = HybridRetriever(
                            HybridIndex(bm25, dense, rrf_k=config["rrf_k"]),
                            config["candidate_k"],
                        )
                index.provenance = {"documents_fingerprint": fingerprint}
                if method != "bm25":
                    index.provenance.update(
                        cache_key=cached.cache_key,
                        vector_fingerprint=cached.vector_fingerprint,
                    )
                self._indexes[key] = index
                while len(self._indexes) > 8:
                    self._indexes.popitem(last=False)
                return index
        except RetrievalFailure:
            raise
        except ProviderError as error:
            raise RetrievalFailure(
                "embedding_timeout" if error.kind is ProviderErrorKind.TIMEOUT
                else "embedding_execution_failure",
                504 if error.kind is ProviderErrorKind.TIMEOUT else 503,
                "timed_out" if error.kind is ProviderErrorKind.TIMEOUT else "failed",
            ) from None
        except (OSError, MemoryError, RuntimeError):
            raise RetrievalFailure("retrieval_resource_failure") from None
        except (ValueError, KeyError, TypeError):
            raise RetrievalFailure("invalid_retrieval_configuration", 422) from None
