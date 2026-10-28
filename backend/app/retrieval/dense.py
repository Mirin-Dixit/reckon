"""Dense retrieval: embeddings, vector normalization, and cosine similarity ranking."""

import math
from typing import Protocol, runtime_checkable

from app.ingestion.chunking import Chunk
from app.retrieval.bm25 import ScoredChunk


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding providers converting text into dense float vectors."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a sequence of texts into a sequence of dense float vectors."""
        ...

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string into a dense float vector."""
        ...


def validate_vector(
    vec: list[float],
    expected_dim: int | None = None,
    label: str = "Vector",
) -> None:
    """Validate that a vector is non-empty, finite, and matches expected_dim.

    Raises ValueError if vec is empty, contains non-numeric or non-finite values,
    or fails to match expected_dim.
    """
    if not isinstance(vec, (list, tuple)) or len(vec) == 0:
        raise ValueError(f"{label} must be a non-empty sequence of numbers")

    for i, val in enumerate(vec):
        if (
            isinstance(val, bool)
            or not isinstance(val, (float, int))
            or not math.isfinite(val)
        ):
            raise ValueError(
                f"{label} contains invalid non-finite element at index {i}: {val!r}"
            )

    if expected_dim is not None and len(vec) != expected_dim:
        raise ValueError(
            f"{label} dimension mismatch: expected {expected_dim}, got {len(vec)}"
        )


def normalize_vector(vec: list[float]) -> list[float]:
    """Return L2-normalized vector.

    If vector norm is zero (all elements 0.0), returns a zero vector without error.
    """
    validate_vector(vec)
    squared_sum = sum(x * x for x in vec)
    norm = math.sqrt(squared_sum)
    if norm == 0.0:
        return [0.0] * len(vec)
    return [x / norm for x in vec]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    If either vector has norm 0.0, returns 0.0.
    Vectors must have identical dimensions and contain finite numbers.
    """
    validate_vector(v1, label="First vector")
    validate_vector(v2, expected_dim=len(v1), label="Second vector")

    norm1 = math.sqrt(sum(x * x for x in v1))
    norm2 = math.sqrt(sum(y * y for y in v2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    dot_product = sum(x * y for x, y in zip(v1, v2))
    sim = dot_product / (norm1 * norm2)
    return max(-1.0, min(1.0, sim))


class DenseIndex:
    """In-memory dense retrieval index using cosine similarity over embeddings."""

    def __init__(
        self,
        chunks: list[Chunk],
        embedder: Embedder,
        chunk_embeddings: list[list[float]] | None = None,
    ) -> None:
        """Build a DenseIndex over chunks using embedder or precomputed embeddings."""
        self.chunks: list[Chunk] = list(chunks)
        self.embedder: Embedder = embedder
        self._dim: int = 0
        self._normalized_embeddings: list[list[float]] = []

        if not self.chunks:
            return

        if chunk_embeddings is None:
            chunk_embeddings = self.embedder.embed_texts([c.text for c in self.chunks])

        if len(chunk_embeddings) != len(self.chunks):
            raise ValueError(
                f"Embedder returned {len(chunk_embeddings)} embeddings for "
                f"{len(self.chunks)} chunks"
            )

        self._dim = len(chunk_embeddings[0])
        for vec in chunk_embeddings:
            validate_vector(vec, expected_dim=self._dim, label="Chunk vector")
            self._normalized_embeddings.append(normalize_vector(vec))

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Rank chunks against query using cosine similarity.

        Scores represent geometric vector similarities in range [-1.0, 1.0],
        not calibrated probabilities of answerability.
        """
        if type(top_k) is not int or top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k!r}")

        if not self.chunks:
            return []

        if not query or not query.strip():
            return []

        query_vec = self.embedder.embed_query(query)
        validate_vector(query_vec, expected_dim=self._dim, label="Query vector")
        query_norm = normalize_vector(query_vec)

        scored_candidates: list[ScoredChunk] = []
        for chunk, chunk_norm in zip(self.chunks, self._normalized_embeddings):
            score = sum(q * d for q, d in zip(query_norm, chunk_norm))
            score = max(-1.0, min(1.0, score))
            scored_candidates.append(ScoredChunk(chunk=chunk, score=score))

        # Deterministic sort: score DESC, doc_id ASC, index ASC
        scored_candidates.sort(
            key=lambda sc: (-sc.score, sc.chunk.doc_id, sc.chunk.index)
        )

        return scored_candidates[:top_k]


def dense_search(
    query: str,
    chunks: list[Chunk],
    embedder: Embedder,
    top_k: int = 5,
    chunk_embeddings: list[list[float]] | None = None,
) -> list[ScoredChunk]:
    """Helper to build an index and search chunks in a single call."""
    if type(top_k) is not int or top_k <= 0:
        raise ValueError(f"top_k must be a positive integer, got {top_k!r}")

    if not chunks:
        return []

    index = DenseIndex(chunks, embedder, chunk_embeddings=chunk_embeddings)
    return index.search(query, top_k=top_k)
