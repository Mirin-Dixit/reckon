"""Tests for hybrid retrieval combining BM25 and Dense ranking via RRF."""

from pathlib import Path

import pytest
from app.ingestion.chunking import Chunk, chunk_documents
from app.ingestion.loader import load_dataset
from app.retrieval.bm25 import BM25Index, ScoredChunk
from app.retrieval.dense import DenseIndex
from app.retrieval.hybrid import (
    HybridIndex,
    hybrid_search,
    reciprocal_rank_fusion,
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


def test_hand_calculated_rrf_math():
    """Verify RRF formula against exact hand calculation.

    Retriever 1: [ca (rank 1), cb (rank 2)]
    Retriever 2: [cb (rank 1), cc (rank 2)]
    k = 60
    Expected scores:
        ca: 1 / (60 + 1) = 1/61 ~= 0.01639344
        cb: 1 / (60 + 2) + 1 / (60 + 1) = 1/62 + 1/61 ~= 0.03252248
        cc: 1 / (60 + 2) = 1/62 ~= 0.01612903
    """
    ca = Chunk("ca", "doc_a", 0, 0, 10, "text a")
    cb = Chunk("cb", "doc_b", 0, 0, 10, "text b")
    cc = Chunk("cc", "doc_c", 0, 0, 10, "text c")

    r1 = [ScoredChunk(ca, 10.0), ScoredChunk(cb, 5.0)]
    r2 = [ScoredChunk(cb, 0.9), ScoredChunk(cc, 0.4)]

    results = reciprocal_rank_fusion([r1, r2], k=60, top_k=5)
    assert len(results) == 3

    # Ranking: cb ranks #1 (consensus), ca ranks #2, cc ranks #3
    assert results[0].chunk.chunk_id == "cb"
    assert results[0].score == pytest.approx(1.0 / 62.0 + 1.0 / 61.0)

    assert results[1].chunk.chunk_id == "ca"
    assert results[1].score == pytest.approx(1.0 / 61.0)

    assert results[2].chunk.chunk_id == "cc"
    assert results[2].score == pytest.approx(1.0 / 62.0)


def test_deterministic_tie_breaking():
    """Verify that ties in RRF score break by doc_id ASC then chunk index ASC."""
    c1 = Chunk("cz_0", "doc_z", 0, 0, 5, "match")
    c2 = Chunk("ca_1", "doc_a", 1, 0, 5, "match")
    c3 = Chunk("ca_0", "doc_a", 0, 0, 5, "match")

    # Three separate single-chunk rankings of rank 1
    # Each chunk gets score 1 / (60 + 1) = 1/61
    r1 = [ScoredChunk(c1, 1.0)]
    r2 = [ScoredChunk(c2, 1.0)]
    r3 = [ScoredChunk(c3, 1.0)]

    results = reciprocal_rank_fusion([r1, r2, r3], k=60, top_k=5)
    assert len(results) == 3
    assert results[0].score == results[1].score == results[2].score
    assert [r.chunk.chunk_id for r in results] == ["ca_0", "ca_1", "cz_0"]


def test_duplicate_chunk_ids_in_single_ranking():
    """Verify duplicate chunk IDs in a ranking only count their first occurrence."""
    ca = Chunk("ca", "doc_a", 0, 0, 5, "text a")
    cb = Chunk("cb", "doc_b", 0, 0, 5, "text b")

    # ca appears at rank 1 and rank 3 in the same ranking
    ranking_with_dupes = [
        ScoredChunk(ca, 10.0),  # rank 1
        ScoredChunk(cb, 5.0),  # rank 2
        ScoredChunk(ca, 2.0),  # rank 3 (should be ignored for ca)
    ]

    results = reciprocal_rank_fusion([ranking_with_dupes], k=60, top_k=5)
    assert len(results) == 2
    assert results[0].chunk.chunk_id == "ca"
    # Score must be 1 / (60 + 1), not 1/61 + 1/63
    assert results[0].score == pytest.approx(1.0 / 61.0)

    assert results[1].chunk.chunk_id == "cb"
    assert results[1].score == pytest.approx(1.0 / 62.0)


def test_disjoint_and_asymmetric_rankings():
    """Verify fusion with disjoint chunk lists and empty retriever lists."""
    ca = Chunk("ca", "doc_a", 0, 0, 5, "text a")
    cb = Chunk("cb", "doc_b", 0, 0, 5, "text b")
    cc = Chunk("cc", "doc_c", 0, 0, 5, "text c")
    cd = Chunk("cd", "doc_d", 0, 0, 5, "text d")

    # 1. Disjoint results: retriever 1 has {ca, cb}, retriever 2 has {cc, cd}
    r1 = [ScoredChunk(ca, 1.0), ScoredChunk(cb, 0.5)]
    r2 = [ScoredChunk(cc, 1.0), ScoredChunk(cd, 0.5)]
    fused_disjoint = reciprocal_rank_fusion([r1, r2], k=60, top_k=10)
    assert len(fused_disjoint) == 4
    assert {r.chunk.chunk_id for r in fused_disjoint} == {"ca", "cb", "cc", "cd"}

    # 2. Asymmetric empty retriever: retriever 1 has {ca, cb}, retriever 2 is empty []
    fused_asymmetric = reciprocal_rank_fusion([r1, []], k=60, top_k=5)
    assert len(fused_asymmetric) == 2
    assert fused_asymmetric[0].chunk.chunk_id == "ca"
    assert fused_asymmetric[0].score == pytest.approx(1.0 / 61.0)
    assert fused_asymmetric[1].chunk.chunk_id == "cb"
    assert fused_asymmetric[1].score == pytest.approx(1.0 / 62.0)

    # 3. Both retrievers empty
    assert reciprocal_rank_fusion([[], []], k=60, top_k=5) == []
    assert reciprocal_rank_fusion([], k=60, top_k=5) == []


def test_parameter_validation_including_booleans():
    """Verify strict validation for top_k, candidate_k, and k, rejecting booleans."""
    chunk = Chunk("c1", "d1", 0, 0, 5, "text")
    r1 = [ScoredChunk(chunk, 1.0)]

    # Validate k in reciprocal_rank_fusion
    for invalid_k in [0, -1, True, False, 1.5, "60"]:
        with pytest.raises(ValueError, match="k must be a positive integer"):
            reciprocal_rank_fusion([r1], k=invalid_k)  # type: ignore

    # Validate top_k in reciprocal_rank_fusion
    for invalid_top_k in [0, -1, True, False, 1.5, "5"]:
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            reciprocal_rank_fusion([r1], top_k=invalid_top_k)  # type: ignore

    # Validate top_k and candidate_k in HybridIndex.search
    embedder = MockEmbedder(default_vector=[1.0, 0.0])
    index = HybridIndex.from_chunks([chunk], embedder)

    for invalid_val in [0, -1, True, False, 1.5, "5"]:
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            index.search("query", top_k=invalid_val)  # type: ignore

        with pytest.raises(ValueError, match="candidate_k must be a positive integer"):
            index.search("query", top_k=5, candidate_k=invalid_val)  # type: ignore

        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            hybrid_search("query", [chunk], embedder, top_k=invalid_val)  # type: ignore

        with pytest.raises(ValueError, match="candidate_k must be a positive integer"):
            hybrid_search(
                "query", [chunk], embedder, top_k=5, candidate_k=invalid_val  # type: ignore
            )

        with pytest.raises(ValueError, match="rrf_k must be a positive integer"):
            hybrid_search(
                "query", [chunk], embedder, top_k=5, rrf_k=invalid_val  # type: ignore
            )


def test_incompatible_underlying_corpora():
    """Verify HybridIndex rejects BM25 and Dense indices with mismatching chunks."""
    c1 = Chunk("c1", "doc_a", 0, 0, 5, "text 1")
    c2 = Chunk("c2", "doc_a", 1, 5, 10, "text 2")
    c3 = Chunk("c3", "doc_b", 0, 0, 5, "different")

    embedder = MockEmbedder(default_vector=[1.0, 0.0])

    # 1. Chunk count mismatch (2 chunks in BM25 vs 1 chunk in Dense)
    bm25_idx = BM25Index([c1, c2])
    dense_idx = DenseIndex([c1], embedder)
    with pytest.raises(
        ValueError, match="Incompatible chunk collections: BM25 has 2 chunks"
    ):
        HybridIndex(bm25_idx, dense_idx)

    # 2. Chunk attribute mismatch at same position
    dense_mismatch = DenseIndex([c1, c3], embedder)
    with pytest.raises(
        ValueError, match="Incompatible chunk at index 1: BM25 chunk 'c2'"
    ):
        HybridIndex(bm25_idx, dense_mismatch)


def test_empty_query_and_empty_corpus_skip_embedder():
    """Verify empty corpus and empty queries return [] without invoking embedder."""
    spy = MockEmbedder(default_vector=[1.0, 0.0])
    chunk = Chunk("c1", "d1", 0, 0, 5, "sample text")

    # 1. Empty corpus via HybridIndex
    empty_idx = HybridIndex.from_chunks([], spy)
    assert spy.embed_texts_calls == 0
    assert empty_idx.search("query") == []
    assert spy.embed_query_calls == 0

    # 2. Empty corpus via hybrid_search helper
    assert hybrid_search("query", [], spy) == []
    assert spy.embed_texts_calls == 0
    assert spy.embed_query_calls == 0

    # 3. Populated index with empty and whitespace queries
    pop_idx = HybridIndex.from_chunks([chunk], spy)
    assert spy.embed_texts_calls == 1  # 1 call during indexing

    assert pop_idx.search("") == []
    assert pop_idx.search("   ") == []
    assert pop_idx.search("\t\n") == []
    assert spy.embed_query_calls == 0  # Query embedder must NOT be called!

    # 4. hybrid_search helper with empty query
    assert hybrid_search("", [chunk], spy) == []
    assert hybrid_search("   ", [chunk], spy) == []


def test_sample_dataset_integration_smoke_test():
    """Verify HybridIndex integrates with sample dataset loader and chunker.

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
    hybrid_index = HybridIndex.from_chunks(chunks, embedder, rrf_k=60)

    answerable_q = next(q for q in questions if q.is_answerable)
    results = hybrid_index.search(answerable_q.question, top_k=3)

    assert len(results) == 3
    for scored in results:
        assert isinstance(scored, ScoredChunk)
        assert isinstance(scored.chunk, Chunk)
        assert scored.score > 0.0
        assert scored.score <= (2.0 / 61.0)  # Maximum possible RRF score for rank 1 + 1
