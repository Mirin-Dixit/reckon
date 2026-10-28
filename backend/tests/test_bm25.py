"""Tests for the Okapi BM25 retrieval index and ranking functions."""

import math
from pathlib import Path

import pytest
from app.ingestion.chunking import Chunk, chunk_documents, find_containing_chunks
from app.ingestion.loader import load_dataset
from app.retrieval.bm25 import BM25Index, ScoredChunk, bm25_search, tokenize


def test_tokenize_preserves_identifiers():
    """Verify that tokenization handles lowercase, punctuation, and underscores."""
    text = "@functools.lru_cache(maxsize=128, typed=False) # comment"
    tokens = tokenize(text)
    assert tokens == [
        "functools",
        "lru_cache",
        "maxsize",
        "128",
        "typed",
        "false",
        "comment",
    ]


def test_hand_calculated_tf_scaling():
    """Verify BM25 score against exact manual calculation for repeated terms."""
    # Two chunks of equal length (2 tokens each): avgdl = 2.0
    # Chunk A: "python cache" (f=1)
    # Chunk B: "python python" (f=2)
    c_a = Chunk("ca", "doc_a", 0, 0, 12, "python cache")
    c_b = Chunk("cb", "doc_b", 0, 0, 13, "python python")
    index = BM25Index([c_a, c_b], k1=1.5, b=0.75)

    # N = 2, df("python") = 2
    # IDF = ln(1 + (2 - 2 + 0.5) / (2 + 0.5)) = ln(1 + 0.5/2.5) = ln(1.2)
    expected_idf = math.log(1.2)
    assert index.idf("python") == pytest.approx(expected_idf, rel=1e-6)

    # Chunk A: f=1, doc_len=2, avgdl=2. len_norm = 1.0 - 0.75 + 0.75*(2/2) = 1.0
    # TF_comp_A = 1 * (2.5) / (1 + 1.5 * 1.0) = 2.5 / 2.5 = 1.0
    expected_score_a = expected_idf * 1.0

    # Chunk B: f=2, doc_len=2, avgdl=2. len_norm = 1.0
    # TF_comp_B = 2 * (2.5) / (2 + 1.5 * 1.0) = 5.0 / 3.5 = 10/7
    expected_score_b = expected_idf * (5.0 / 3.5)

    results = index.search("python", top_k=5)
    assert len(results) == 2

    # Higher frequency must rank first with diminishing return
    assert results[0].chunk.chunk_id == "cb"
    assert results[0].score == pytest.approx(expected_score_b, rel=1e-5)

    assert results[1].chunk.chunk_id == "ca"
    assert results[1].score == pytest.approx(expected_score_a, rel=1e-5)


def test_hand_calculated_document_length_normalization():
    """Verify that shorter documents are favored when term frequency is identical."""
    # Chunk Short: 1 token ("cache")
    # Chunk Long: 5 tokens ("cache python code test file")
    c_short = Chunk("c_s", "doc_s", 0, 0, 5, "cache")
    c_long = Chunk("c_l", "doc_l", 0, 0, 26, "cache python code test file")
    index = BM25Index([c_short, c_long], k1=1.5, b=0.75)

    results = index.search("cache", top_k=5)
    assert len(results) == 2
    # Concise chunk must receive a higher score than the verbose chunk
    assert results[0].chunk.chunk_id == "c_s"
    assert results[1].chunk.chunk_id == "c_l"
    assert results[0].score > results[1].score


def test_non_negative_idf_guarantee():
    """Verify that IDF remains non-negative even when terms appear in all documents."""
    chunks = [
        Chunk("c1", "d1", 0, 0, 4, "test"),
        Chunk("c2", "d2", 0, 0, 4, "test"),
        Chunk("c3", "d3", 0, 0, 4, "test"),
    ]
    index = BM25Index(chunks)
    # Term appears in 3 out of 3 documents (df = N)
    idf_val = index.idf("test")
    # Traditional Okapi without +1 yields log((0 + 0.5)/(3 + 0.5)) < 0.
    # Our formula ln(1 + ...) guarantees idf > 0.
    assert idf_val > 0.0


def test_deterministic_tie_breaking():
    """Verify that ties are broken deterministically by doc_id ASC then index ASC."""
    c1 = Chunk("cz_0", "doc_z", 0, 0, 5, "match")
    c2 = Chunk("ca_1", "doc_a", 1, 0, 5, "match")
    c3 = Chunk("ca_0", "doc_a", 0, 0, 5, "match")

    results = bm25_search("match", [c1, c2, c3], top_k=5)
    assert len(results) == 3

    # All three have identical scores
    assert results[0].score == results[1].score == results[2].score

    # Expected order: doc_a index 0, doc_a index 1, doc_z index 0
    assert [r.chunk.chunk_id for r in results] == ["ca_0", "ca_1", "cz_0"]


def test_edge_cases_empty_and_no_match():
    """Verify handling of empty queries, empty corpora, and queries with no matches."""
    chunk = Chunk("c1", "d1", 0, 0, 10, "some text")

    # Empty query string or punctuation only
    assert bm25_search("", [chunk]) == []
    assert bm25_search("   ", [chunk]) == []
    assert bm25_search("!@#$%", [chunk]) == []

    # Empty corpus
    assert bm25_search("text", []) == []

    # Query with no matching terms in corpus
    assert bm25_search("nonexistent", [chunk]) == []


def test_all_empty_token_corpus_returns_empty():
    """Verify searching a corpus of only punctuation/whitespace chunks returns []."""
    empty_chunks = [
        Chunk("c1", "d1", 0, 0, 5, "   "),
        Chunk("c2", "d1", 1, 5, 15, "!@#$%^&*()"),
        Chunk("c3", "d2", 0, 0, 4, "\n\t  "),
    ]
    index = BM25Index(empty_chunks)
    assert index._avgdl == 0.0
    assert index.search("python") == []
    assert bm25_search("python", empty_chunks) == []


def test_invalid_parameters():
    """Verify parameter validations on index constructor and search method."""
    chunk = Chunk("c1", "d1", 0, 0, 5, "text")

    # Invalid k1 (< 0)
    with pytest.raises(ValueError, match="k1 must be a non-negative number"):
        BM25Index([chunk], k1=-0.1)

    # Invalid b (< 0 or > 1)
    with pytest.raises(ValueError, match="b must be a number in range"):
        BM25Index([chunk], b=-0.1)

    with pytest.raises(ValueError, match="b must be a number in range"):
        BM25Index([chunk], b=1.1)

    index = BM25Index([chunk])

    # Invalid top_k (<= 0 or non-int)
    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        index.search("text", top_k=0)

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        index.search("text", top_k=-2)

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        index.search("text", top_k=True)  # type: ignore


def test_scored_chunk_metadata_preservation():
    """Verify that ScoredChunk preserves the complete parent Chunk metadata."""
    original_chunk = Chunk(
        chunk_id="doc_x_c0002",
        doc_id="doc_x",
        index=2,
        start_char=100,
        end_char=150,
        text="Target keyword passage.",
    )
    results = bm25_search("keyword", [original_chunk], top_k=1)
    assert len(results) == 1

    scored = results[0]
    assert isinstance(scored, ScoredChunk)
    assert scored.chunk is original_chunk
    assert scored.chunk.chunk_id == "doc_x_c0002"
    assert scored.chunk.doc_id == "doc_x"
    assert scored.chunk.index == 2
    assert scored.chunk.start_char == 100
    assert scored.chunk.end_char == 150
    assert scored.chunk.text == "Target keyword passage."
    assert scored.score > 0.0


def test_dataset_integration_answerable_evidence_coverage():
    """Verify that BM25 retrieves gold evidence chunks for sample answerable queries."""
    documents, questions = load_dataset(
        Path("data/sample/documents.jsonl"),
        Path("data/sample/questions.jsonl"),
    )
    chunks = chunk_documents(documents, chunk_size=300, chunk_overlap=80)
    index = BM25Index(chunks)

    answerable_count = 0
    failing_queries: list[str] = []

    for q in questions:
        if q.is_answerable:
            answerable_count += 1
            # Retrieve top-3 chunks
            retrieved = index.search(q.question, top_k=3)
            retrieved_ids = {r.chunk.chunk_id for r in retrieved}

            # Find gold evidence chunk IDs
            gold_chunk_ids: set[str] = set()
            for span in q.evidence_spans:
                gold_chunks = find_containing_chunks(span, chunks)
                gold_chunk_ids.update(c.chunk_id for c in gold_chunks)

            # Check if any gold evidence chunk is in the retrieved top-k
            if not retrieved_ids.intersection(gold_chunk_ids):
                failing_queries.append(q.id)

    assert answerable_count == 7
    assert (
        not failing_queries
    ), f"BM25 failed to retrieve evidence for questions: {failing_queries}"


def test_unanswerable_query_behavior():
    """Verify retrieval behavior on unanswerable questions.

    A query with zero corpus terms (like Google Guava) returns empty results,
    while near-miss queries containing corpus terms (like itertools) retrieve
    lexically related chunks without answering the question.
    """
    documents, _ = load_dataset(
        Path("data/sample/documents.jsonl"),
        Path("data/sample/questions.jsonl"),
    )
    chunks = chunk_documents(documents, chunk_size=300, chunk_overlap=80)
    index = BM25Index(chunks)

    # 1. Non-matching query: zero tokens exist in the corpus -> returns []
    guava_results = index.search("Google Guava CacheBuilder expiration", top_k=3)
    assert guava_results == []

    # 2. Near-miss query: contains "itertools", so BM25 retrieves related chunks
    # even though itertools.batched is absent. This proves BM25 alone does not
    # imply answerability.
    batched_results = index.search(
        "How do you use itertools.batched in Python 3.11?", top_k=3
    )
    assert len(batched_results) > 0
    assert any(r.chunk.doc_id == "doc_itertools_islice" for r in batched_results)
