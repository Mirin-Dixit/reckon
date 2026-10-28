"""Tests for dense retrieval, vector normalization, and cosine similarity ranking."""

import math
from pathlib import Path

import pytest
from app.ingestion.chunking import Chunk, chunk_documents
from app.ingestion.loader import load_dataset
from app.retrieval.bm25 import ScoredChunk
from app.retrieval.dense import (
    DenseIndex,
    cosine_similarity,
    dense_search,
    normalize_vector,
)


class MockEmbedder:
    """Configurable mock embedder for offline unit tests."""

    def __init__(
        self,
        text_embeddings: dict[str, list[float]] | None = None,
        query_embeddings: dict[str, list[float]] | None = None,
        default_vector: list[float] | None = None,
    ) -> None:
        self.text_embeddings: dict[str, list[float]] = text_embeddings or {}
        self.query_embeddings: dict[str, list[float]] = query_embeddings or {}
        self.default_vector: list[float] = default_vector or [0.1, 0.2]
        self.embed_texts_calls: int = 0
        self.embed_query_calls: int = 0

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.embed_texts_calls += 1
        return [self.text_embeddings.get(t, list(self.default_vector)) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        self.embed_query_calls += 1
        return self.query_embeddings.get(query, list(self.default_vector))


class TokenHashEmbedder:
    """Deterministic, offline pseudo-embedder for smoke-testing without model weights.

    NOTE: This generates fixed synthetic pseudo-embeddings to verify pipeline mechanics;
    it makes no claim of semantic language understanding.
    """

    def __init__(self, dim: int = 16) -> None:
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        if not tokens:
            return vec
        for i, token in enumerate(tokens):
            bucket = sum(ord(c) for c in token) % self.dim
            vec[bucket] += 1.0 / (i + 1.0)
        return vec

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed(query)


def test_hand_calculated_normalization():
    """Verify vector normalization on known hand-calculated vectors."""
    # 3-4-5 right triangle: [3.0, 4.0] -> norm 5.0 -> [0.6, 0.8]
    assert normalize_vector([3.0, 4.0]) == pytest.approx([0.6, 0.8])
    # Negative coordinates
    assert normalize_vector([-6.0, 8.0]) == pytest.approx([-0.6, 0.8])
    # Unit vector remains unchanged
    assert normalize_vector([1.0, 0.0]) == pytest.approx([1.0, 0.0])


def test_hand_calculated_cosine_similarity():
    """Verify cosine similarity against known geometric angles."""
    # Identical direction: angle 0 deg -> sim 1.0
    assert cosine_similarity([1.0, 2.0], [2.0, 4.0]) == pytest.approx(1.0)

    # Orthogonal vectors: angle 90 deg -> sim 0.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    # Opposite vectors: angle 180 deg -> sim -1.0
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    # 45 degree angle: [1.0, 0.0] and [1.0, 1.0] -> 1 / sqrt(2)
    expected_45 = 1.0 / math.sqrt(2.0)
    assert cosine_similarity([1.0, 0.0], [1.0, 1.0]) == pytest.approx(expected_45)


def test_zero_vector_handling():
    """Verify safe zero-vector handling in normalization, similarity, and ranking."""
    # Normalizing zero vector returns a zero vector without ZeroDivisionError
    assert normalize_vector([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]

    # Cosine similarity involving zero vectors returns 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([1.0, 2.0], [0.0, 0.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0

    # Index with a zero-vector chunk
    embedder = MockEmbedder(
        text_embeddings={"zero": [0.0, 0.0], "non_zero": [1.0, 0.0]},
        query_embeddings={"q": [1.0, 0.0], "q_zero": [0.0, 0.0]},
    )
    c_zero = Chunk("c0", "d1", 0, 0, 4, "zero")
    c_norm = Chunk("c1", "d1", 1, 4, 12, "non_zero")

    # Search with non-zero query: zero chunk receives score 0.0
    res = dense_search("q", [c_zero, c_norm], embedder, top_k=2)
    assert len(res) == 2
    assert res[0].chunk.chunk_id == "c1"
    assert res[0].score == pytest.approx(1.0)
    assert res[1].chunk.chunk_id == "c0"
    assert res[1].score == pytest.approx(0.0)

    # Search with zero-vector query: all chunks safely receive 0.0
    res_zero = dense_search("q_zero", [c_zero, c_norm], embedder, top_k=2)
    assert len(res_zero) == 2
    assert res_zero[0].score == pytest.approx(0.0)
    assert res_zero[1].score == pytest.approx(0.0)


def test_vector_validation_errors():
    """Verify rejections of empty, non-finite, non-numeric, and invalid vectors."""
    # Empty vector
    with pytest.raises(ValueError, match="must be a non-empty sequence"):
        normalize_vector([])

    # NaN and infinity
    with pytest.raises(ValueError, match="invalid non-finite element at index 1"):
        normalize_vector([1.0, float("nan")])

    with pytest.raises(ValueError, match="invalid non-finite element at index 0"):
        normalize_vector([float("inf"), 2.0])

    with pytest.raises(ValueError, match="invalid non-finite element at index 0"):
        normalize_vector([float("-inf"), 2.0])

    # Boolean and string elements
    with pytest.raises(ValueError, match="invalid non-finite element at index 1"):
        normalize_vector([1.0, True])  # type: ignore

    with pytest.raises(ValueError, match="invalid non-finite element at index 0"):
        normalize_vector(["not_a_number", 1.0])  # type: ignore

    # Dimension mismatch in cosine_similarity
    with pytest.raises(ValueError, match="dimension mismatch: expected 2, got 3"):
        cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])


def test_embedder_output_count_mismatch():
    """Verify ValueError when embedder returns unexpected count of embeddings."""

    class MismatchedEmbedder:

        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0]]  # Returns 1 vector for 2 chunks

        def embed_query(self, query: str) -> list[float]:
            return [1.0, 0.0]

    chunks = [
        Chunk("c1", "d1", 0, 0, 5, "text1"),
        Chunk("c2", "d1", 1, 5, 10, "text2"),
    ]
    with pytest.raises(
        ValueError, match="Embedder returned 1 embeddings for 2 chunks"
    ):
        DenseIndex(chunks, MismatchedEmbedder())


def test_chunk_vector_dimension_mismatch_in_corpus():
    """Verify ValueError when corpus chunks have inconsistent embedding dimensions."""
    chunks = [
        Chunk("c1", "d1", 0, 0, 5, "text1"),
        Chunk("c2", "d1", 1, 5, 10, "text2"),
    ]
    inconsistent_embeddings = [[1.0, 0.0, 0.0], [1.0, 0.0]]
    embedder = MockEmbedder()
    with pytest.raises(
        ValueError, match="Chunk vector dimension mismatch: expected 3, got 2"
    ):
        DenseIndex(chunks, embedder, chunk_embeddings=inconsistent_embeddings)


def test_query_dimension_mismatch():
    """Verify ValueError when query embedding dimension does not match index."""
    embedder = MockEmbedder(
        text_embeddings={"text1": [1.0, 0.0, 0.0]},
        query_embeddings={"q": [1.0, 0.0]},  # dim 2 vs index dim 3
    )
    chunk = Chunk("c1", "d1", 0, 0, 5, "text1")
    index = DenseIndex([chunk], embedder)

    with pytest.raises(
        ValueError, match="Query vector dimension mismatch: expected 3, got 2"
    ):
        index.search("q")


def test_deterministic_tie_breaking():
    """Verify identical scores break ties by doc_id ASC then chunk index ASC."""
    # All chunks produce identical embedding [1.0, 0.0]
    embedder = MockEmbedder(default_vector=[1.0, 0.0])
    c1 = Chunk("cz_0", "doc_z", 0, 0, 5, "match")
    c2 = Chunk("ca_1", "doc_a", 1, 0, 5, "match")
    c3 = Chunk("ca_0", "doc_a", 0, 0, 5, "match")

    results = dense_search("match", [c1, c2, c3], embedder, top_k=5)
    assert len(results) == 3
    assert results[0].score == results[1].score == results[2].score
    assert [r.chunk.chunk_id for r in results] == ["ca_0", "ca_1", "cz_0"]


def test_retaining_zero_and_negative_scores():
    """Verify that zero and negative similarities are retained and ranked correctly."""
    embedder = MockEmbedder(
        text_embeddings={
            "parallel": [1.0, 0.0],
            "orthogonal": [0.0, 1.0],
            "obtuse": [-0.6, 0.8],
            "opposite": [-1.0, 0.0],
        },
        query_embeddings={"q": [1.0, 0.0]},
    )
    chunks = [
        Chunk("c_opp", "d1", 3, 0, 8, "opposite"),
        Chunk("c_obt", "d1", 2, 0, 6, "obtuse"),
        Chunk("c_orth", "d1", 1, 0, 10, "orthogonal"),
        Chunk("c_par", "d1", 0, 0, 8, "parallel"),
    ]

    results = dense_search("q", chunks, embedder, top_k=4)
    assert len(results) == 4
    # Highest to lowest score, retaining non-positive scores without filtering
    assert results[0].chunk.chunk_id == "c_par"
    assert results[0].score == pytest.approx(1.0)
    assert results[1].chunk.chunk_id == "c_orth"
    assert results[1].score == pytest.approx(0.0)
    assert results[2].chunk.chunk_id == "c_obt"
    assert results[2].score == pytest.approx(-0.6)
    assert results[3].chunk.chunk_id == "c_opp"
    assert results[3].score == pytest.approx(-1.0)


def test_empty_query_and_empty_corpus_skip_embedder():
    """Verify empty corpus and empty queries return [] without calling embedder."""
    spy = MockEmbedder()
    chunk = Chunk("c1", "d1", 0, 0, 5, "text")

    # 1. Empty corpus via DenseIndex
    empty_index = DenseIndex([], spy)
    assert spy.embed_texts_calls == 0
    assert empty_index.search("hello") == []
    assert spy.embed_query_calls == 0

    # 2. Empty corpus via dense_search helper
    assert dense_search("hello", [], spy) == []
    assert spy.embed_texts_calls == 0
    assert spy.embed_query_calls == 0

    # 3. Empty and whitespace-only queries on populated index
    index = DenseIndex([chunk], spy)
    assert spy.embed_texts_calls == 1  # 1 call during indexing

    assert index.search("") == []
    assert index.search("   ") == []
    assert index.search("\t\n") == []
    assert spy.embed_query_calls == 0  # Query embedder must NOT be called!


def test_invalid_top_k_parameter():
    """Verify strict validation of top_k on search and dense_search."""
    chunk = Chunk("c1", "d1", 0, 0, 5, "text")
    embedder = MockEmbedder(default_vector=[1.0, 0.0])
    index = DenseIndex([chunk], embedder)

    for invalid_k in [0, -1, -5, True, 1.5, "3"]:
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            index.search("query", top_k=invalid_k)  # type: ignore

        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            dense_search("query", [chunk], embedder, top_k=invalid_k)  # type: ignore

    # top_k must be validated before early returns for empty corpus or query
    for invalid_k in [0, -1, True]:
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            dense_search("query", [], embedder, top_k=invalid_k)  # type: ignore

        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            index.search("", top_k=invalid_k)  # type: ignore


def test_sample_dataset_integration_smoke_test():
    """Verify DenseIndex integrates with sample dataset loader and chunker.

    NOTE: This integration smoke test uses a deterministic synthetic mock embedder
    to verify pipeline mechanics and contract compliance without downloading
    external models. It does not measure semantic retrieval quality.
    """
    documents, questions = load_dataset(
        Path("data/sample/documents.jsonl"),
        Path("data/sample/questions.jsonl"),
    )
    chunks = chunk_documents(documents, chunk_size=300, chunk_overlap=80)
    # Dynamically verify chunk count from the current pipeline
    assert len(chunks) == 10

    embedder = TokenHashEmbedder(dim=16)
    index = DenseIndex(chunks, embedder)

    answerable_q = next(q for q in questions if q.is_answerable)
    results = index.search(answerable_q.question, top_k=3)

    assert len(results) == 3
    for scored in results:
        assert isinstance(scored, ScoredChunk)
        assert isinstance(scored.chunk, Chunk)
        assert -1.0 <= scored.score <= 1.0
        assert math.isfinite(scored.score)
