"""Hybrid retrieval combining BM25 and Dense rankings via Reciprocal Rank Fusion."""

from collections import defaultdict

from app.ingestion.chunking import Chunk
from app.retrieval.bm25 import BM25Index, ScoredChunk
from app.retrieval.dense import DenseIndex, Embedder


def reciprocal_rank_fusion(
    rankings: list[list[ScoredChunk]],
    k: int = 60,
    top_k: int = 5,
) -> list[ScoredChunk]:
    """Fuse multiple ranked lists of ScoredChunks using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_score(chunk) = sum(1.0 / (k + rank))
    where rank is the 1-based rank position of the chunk's first occurrence in each
    ranking. Duplicate chunk IDs within an individual ranking are deduplicated,
    counting only their best (first) rank.

    Results are sorted deterministically: score DESC, doc_id ASC, chunk index ASC.
    """
    if type(k) is not int or k <= 0:
        raise ValueError(f"k must be a positive integer, got {k!r}")
    if type(top_k) is not int or top_k <= 0:
        raise ValueError(f"top_k must be a positive integer, got {top_k!r}")

    if not rankings:
        return []

    chunk_scores: dict[str, float] = defaultdict(float)
    chunk_objects: dict[str, Chunk] = {}

    for ranking in rankings:
        seen_in_ranking: set[str] = set()
        for rank, scored_chunk in enumerate(ranking, start=1):
            cid = scored_chunk.chunk.chunk_id
            if cid in seen_in_ranking:
                continue
            seen_in_ranking.add(cid)
            chunk_scores[cid] += 1.0 / (k + rank)
            if cid not in chunk_objects:
                chunk_objects[cid] = scored_chunk.chunk

    fused_candidates = [
        ScoredChunk(chunk=chunk_objects[cid], score=score)
        for cid, score in chunk_scores.items()
    ]

    # Deterministic sort: score DESC, doc_id ASC, index ASC
    fused_candidates.sort(
        key=lambda sc: (-sc.score, sc.chunk.doc_id, sc.chunk.index)
    )

    return fused_candidates[:top_k]


class HybridIndex:
    """Hybrid retrieval index combining BM25 and Dense retrieval via RRF."""

    def __init__(
        self,
        bm25_index: BM25Index,
        dense_index: DenseIndex,
        rrf_k: int = 60,
    ) -> None:
        """Initialize hybrid index from compatible BM25Index and DenseIndex.

        Both indices must be constructed over the exact same chunk sequence.
        """
        if not isinstance(bm25_index, BM25Index):
            t_name = type(bm25_index).__name__
            raise ValueError(f"Expected BM25Index instance, got {t_name}")
        if not isinstance(dense_index, DenseIndex):
            t_name = type(dense_index).__name__
            raise ValueError(f"Expected DenseIndex instance, got {t_name}")
        if type(rrf_k) is not int or rrf_k <= 0:
            raise ValueError(f"rrf_k must be a positive integer, got {rrf_k!r}")

        if len(bm25_index.chunks) != len(dense_index.chunks):
            raise ValueError(
                f"Incompatible chunk collections: BM25 has {len(bm25_index.chunks)} "
                f"chunks, but Dense has {len(dense_index.chunks)} chunks"
            )

        for i, (c_bm25, c_dense) in enumerate(
            zip(bm25_index.chunks, dense_index.chunks)
        ):
            if c_bm25 != c_dense:
                raise ValueError(
                    f"Incompatible chunk at index {i}: BM25 chunk '{c_bm25.chunk_id}' "
                    f"does not match Dense chunk '{c_dense.chunk_id}'"
                )

        self.bm25_index: BM25Index = bm25_index
        self.dense_index: DenseIndex = dense_index
        self.rrf_k: int = rrf_k
        self.chunks: list[Chunk] = bm25_index.chunks

    @classmethod
    def from_chunks(
        cls,
        chunks: list[Chunk],
        embedder: Embedder,
        chunk_embeddings: list[list[float]] | None = None,
        k1: float = 1.5,
        b: float = 0.75,
        rrf_k: int = 60,
    ) -> "HybridIndex":
        """Build BM25 and Dense indices over the same chunks and initialize
        HybridIndex.
        """
        bm25_index = BM25Index(chunks, k1=k1, b=b)
        dense_index = DenseIndex(
            chunks, embedder, chunk_embeddings=chunk_embeddings
        )
        return cls(bm25_index, dense_index, rrf_k=rrf_k)

    def search(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int | None = None,
    ) -> list[ScoredChunk]:
        """Retrieve candidates from BM25 and Dense indices and fuse via RRF."""
        if type(top_k) is not int or top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k!r}")

        if candidate_k is not None:
            if type(candidate_k) is not int or candidate_k <= 0:
                raise ValueError(
                    f"candidate_k must be a positive integer, got {candidate_k!r}"
                )

        if not self.chunks:
            return []

        if not query or not query.strip():
            return []

        eff_candidate_k = (
            candidate_k
            if candidate_k is not None
            else max(top_k * 3, 50, len(self.chunks))
        )

        bm25_results = self.bm25_index.search(query, top_k=eff_candidate_k)
        dense_results = self.dense_index.search(query, top_k=eff_candidate_k)

        return reciprocal_rank_fusion(
            [bm25_results, dense_results],
            k=self.rrf_k,
            top_k=top_k,
        )


def hybrid_search(
    query: str,
    chunks: list[Chunk],
    embedder: Embedder,
    top_k: int = 5,
    rrf_k: int = 60,
    candidate_k: int | None = None,
    chunk_embeddings: list[list[float]] | None = None,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[ScoredChunk]:
    """Helper to build a HybridIndex and search chunks in a single call."""
    if type(top_k) is not int or top_k <= 0:
        raise ValueError(f"top_k must be a positive integer, got {top_k!r}")

    if candidate_k is not None:
        if type(candidate_k) is not int or candidate_k <= 0:
            raise ValueError(
                f"candidate_k must be a positive integer, got {candidate_k!r}"
            )

    if type(rrf_k) is not int or rrf_k <= 0:
        raise ValueError(f"rrf_k must be a positive integer, got {rrf_k!r}")

    if not chunks:
        return []

    if not query or not query.strip():
        return []

    index = HybridIndex.from_chunks(
        chunks=chunks,
        embedder=embedder,
        chunk_embeddings=chunk_embeddings,
        k1=k1,
        b=b,
        rrf_k=rrf_k,
    )
    return index.search(query, top_k=top_k, candidate_k=candidate_k)
