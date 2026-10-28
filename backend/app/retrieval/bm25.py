"""Okapi BM25 ranking over Document Chunk collections."""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from app.ingestion.chunking import Chunk


@dataclass(frozen=True)
class ScoredChunk:
    """A retrieved Chunk paired with its BM25 relevance score."""

    chunk: Chunk
    score: float

    def __post_init__(self) -> None:
        """Validate scored chunk attributes."""
        if not isinstance(self.chunk, Chunk):
            t_name = type(self.chunk).__name__
            raise ValueError(f"Expected Chunk instance, got {t_name}")
        if type(self.score) not in (float, int):
            t_name = type(self.score).__name__
            raise ValueError(f"Score must be a float or int, got {t_name}")


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens, preserving underscores."""
    return re.findall(r"\w+", text.lower())


class BM25Index:
    """In-memory Okapi BM25 index over a collection of Chunk objects."""

    def __init__(
        self,
        chunks: list[Chunk],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        """Initialize and build the BM25 index from a list of chunks."""
        if type(k1) not in (float, int) or k1 < 0:
            raise ValueError(f"k1 must be a non-negative number, got {k1!r}")
        if type(b) not in (float, int) or not (0.0 <= b <= 1.0):
            raise ValueError(f"b must be a number in range [0.0, 1.0], got {b!r}")

        self.chunks: list[Chunk] = list(chunks)
        self.k1: float = float(k1)
        self.b: float = float(b)

        self._num_chunks: int = len(self.chunks)
        self._doc_lens: list[int] = []
        self._tf: list[Counter[str]] = []
        self._df: dict[str, int] = defaultdict(int)

        for chunk in self.chunks:
            tokens = tokenize(chunk.text)
            self._doc_lens.append(len(tokens))
            term_counts = Counter(tokens)
            self._tf.append(term_counts)
            for term in term_counts:
                self._df[term] += 1

        if self._num_chunks > 0:
            self._avgdl: float = sum(self._doc_lens) / self._num_chunks
        else:
            self._avgdl = 0.0

    def idf(self, term: str) -> float:
        """Compute non-negative Lucene/Okapi inverse document frequency for a term."""
        doc_freq = self._df.get(term, 0)
        # The +1 inside the logarithm guarantees that IDF is always >= 0.0
        return math.log(1.0 + (self._num_chunks - doc_freq + 0.5) / (doc_freq + 0.5))

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Rank chunks against the query.

        Returns the top-k matches with score strictly greater than 0.0.
        """
        if type(top_k) is not int or top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k!r}")

        if self._num_chunks == 0 or self._avgdl == 0.0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scored_candidates: list[ScoredChunk] = []

        for i, chunk in enumerate(self.chunks):
            doc_len = self._doc_lens[i]
            tf_counter = self._tf[i]
            score = 0.0

            # Length normalization denominator factor
            len_norm = 1.0 - self.b + self.b * (doc_len / self._avgdl)

            for term in query_tokens:
                if term in tf_counter:
                    freq = tf_counter[term]
                    idf_weight = self.idf(term)
                    tf_component = (freq * (self.k1 + 1.0)) / (
                        freq + self.k1 * len_norm
                    )
                    score += idf_weight * tf_component

            if score > 0.0:
                scored_candidates.append(ScoredChunk(chunk=chunk, score=score))

        # Deterministic sort: score DESC, doc_id ASC, index ASC
        scored_candidates.sort(
            key=lambda sc: (-sc.score, sc.chunk.doc_id, sc.chunk.index)
        )

        return scored_candidates[:top_k]


def bm25_search(
    query: str,
    chunks: list[Chunk],
    top_k: int = 5,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[ScoredChunk]:
    """Helper to build an index and search chunks in a single call."""
    index = BM25Index(chunks, k1=k1, b=b)
    return index.search(query, top_k=top_k)
