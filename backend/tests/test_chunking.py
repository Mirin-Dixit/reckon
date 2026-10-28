"""Tests for deterministic fixed-size character chunking and span mapping."""

from pathlib import Path

import pytest
from app.ingestion.chunking import (
    Chunk,
    chunk_document,
    chunk_documents,
    find_containing_chunks,
)
from app.ingestion.loader import load_dataset
from app.ingestion.schema import Document, EvidenceSpan


def test_exact_chunk_boundaries_and_slices():
    """Verify exact character slicing and indexing on a deterministic document."""
    doc = Document(
        id="doc_test",
        title="Test Document",
        source_url="https://example.com/test",
        text="ABCDEFGHIJ",  # length 10
    )
    chunks = chunk_document(doc, chunk_size=6, chunk_overlap=2)

    # Step is 6 - 2 = 4
    # Chunk 0: [0:6] -> "ABCDEF"
    # Chunk 1: [4:10] -> "EFGHIJ" (reaches end, loop terminates)
    assert len(chunks) == 2

    assert chunks[0].chunk_id == "doc_test_c0000"
    assert chunks[0].doc_id == "doc_test"
    assert chunks[0].index == 0
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 6
    assert chunks[0].text == "ABCDEF"

    assert chunks[1].chunk_id == "doc_test_c0001"
    assert chunks[1].doc_id == "doc_test"
    assert chunks[1].index == 1
    assert chunks[1].start_char == 4
    assert chunks[1].end_char == 10
    assert chunks[1].text == "EFGHIJ"

    for c in chunks:
        assert c.text == doc.text[c.start_char : c.end_char]


def test_stop_when_end_reached_no_trailing_chunks():
    """Verify that chunking terminates immediately when end is reached."""
    # Length 10 with chunk_size 6, overlap 2:
    # Chunk 1 ends at 10. Next start would be 8, but end is already 10.
    doc10 = Document("d10", "D10", "https://example.com", "0123456789")
    chunks10 = chunk_document(doc10, chunk_size=6, chunk_overlap=2)
    assert len(chunks10) == 2
    assert chunks10[-1].end_char == 10

    # Length 12 with chunk_size 6, overlap 2 (step 4):
    # [0:6], [4:10], [8:12] -> exactly 3 chunks
    doc12 = Document("d12", "D12", "https://example.com", "0123456789AB")
    chunks12 = chunk_document(doc12, chunk_size=6, chunk_overlap=2)
    assert len(chunks12) == 3
    assert [(c.start_char, c.end_char) for c in chunks12] == [
        (0, 6),
        (4, 10),
        (8, 12),
    ]

    # Length 15 with chunk_size 6, overlap 2 (step 4):
    # [0:6], [4:10], [8:14], [12:15] -> exactly 4 chunks
    doc15 = Document("d15", "D15", "https://example.com", "0123456789ABCDE")
    chunks15 = chunk_document(doc15, chunk_size=6, chunk_overlap=2)
    assert len(chunks15) == 4
    assert [(c.start_char, c.end_char) for c in chunks15] == [
        (0, 6),
        (4, 10),
        (8, 14),
        (12, 15),
    ]


def test_document_shorter_or_equal_to_chunk_size():
    """Verify documents smaller than or equal to chunk_size produce exactly 1 chunk."""
    doc_short = Document("ds", "Short", "https://example.com", "Hello")
    chunks = chunk_document(doc_short, chunk_size=10, chunk_overlap=3)
    assert len(chunks) == 1
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 5
    assert chunks[0].text == "Hello"

    doc_exact = Document("de", "Exact", "https://example.com", "1234567890")
    chunks_exact = chunk_document(doc_exact, chunk_size=10, chunk_overlap=2)
    assert len(chunks_exact) == 1
    assert chunks_exact[0].start_char == 0
    assert chunks_exact[0].end_char == 10
    assert chunks_exact[0].text == "1234567890"


def test_overlap_consistency():
    """Verify that adjacent chunks overlap by the specified character count."""
    doc = Document("d", "D", "https://example.com", "A" * 100)
    chunk_size = 25
    chunk_overlap = 10
    chunks = chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for i in range(len(chunks) - 1):
        c1 = chunks[i]
        c2 = chunks[i + 1]
        assert c2.start_char == c1.start_char + (chunk_size - chunk_overlap)
        overlap = c1.end_char - c2.start_char
        assert overlap == chunk_overlap


def test_invalid_parameters():
    """Verify that invalid chunk sizes and overlaps raise ValueError."""
    doc = Document("d", "D", "https://example.com", "Text")

    # Invalid chunk_size
    with pytest.raises(ValueError, match="chunk_size must be a positive integer"):
        chunk_document(doc, chunk_size=0, chunk_overlap=0)

    with pytest.raises(ValueError, match="chunk_size must be a positive integer"):
        chunk_document(doc, chunk_size=-5, chunk_overlap=0)

    with pytest.raises(ValueError, match="chunk_size must be a positive integer"):
        chunk_document(doc, chunk_size=True, chunk_overlap=0)  # type: ignore

    # Invalid chunk_overlap
    with pytest.raises(ValueError, match="chunk_overlap must be a non-negative"):
        chunk_document(doc, chunk_size=10, chunk_overlap=-1)

    # Overlap >= chunk_size
    with pytest.raises(ValueError, match="must be strictly less than"):
        chunk_document(doc, chunk_size=10, chunk_overlap=10)

    with pytest.raises(ValueError, match="must be strictly less than"):
        chunk_document(doc, chunk_size=10, chunk_overlap=15)


def test_chunk_dataclass_validation_and_serialization():
    """Verify Chunk post-init validation and dictionary roundtrip."""
    chunk = Chunk(
        chunk_id="doc_1_c0000",
        doc_id="doc_1",
        index=0,
        start_char=10,
        end_char=25,
        text="Sample passage.",
    )
    assert chunk.to_dict()["chunk_id"] == "doc_1_c0000"
    assert Chunk.from_dict(chunk.to_dict()) == chunk

    # Invalid end <= start
    with pytest.raises(ValueError, match="must be strictly greater than"):
        Chunk("c1", "d1", 0, 10, 10, "text")

    # Negative start
    with pytest.raises(ValueError, match="must be a non-negative integer"):
        Chunk("c1", "d1", 0, -1, 5, "text")


def test_find_containing_chunks():
    """Verify evidence span full containment mapping."""
    doc = Document("d1", "Title", "https://example.com", "ABCDEFGHIJ")
    chunks = chunk_document(doc, chunk_size=6, chunk_overlap=2)
    # chunks: [0:6] ("ABCDEF"), [4:10] ("EFGHIJ")

    # Span 1: "BCD" (offsets 1..4) -> fully inside Chunk 0 only
    span1 = EvidenceSpan("d1", 1, 4, "BCD")
    containing1 = find_containing_chunks(span1, chunks)
    assert [c.index for c in containing1] == [0]

    # Span 2: "EF" (offsets 4..6) -> inside overlap, fully in both Chunk 0 and 1
    span2 = EvidenceSpan("d1", 4, 6, "EF")
    containing2 = find_containing_chunks(span2, chunks)
    assert [c.index for c in containing2] == [0, 1]

    # Span 3: "DEFGH" (offsets 3..8) -> crosses boundary, neither fully contains it
    span3 = EvidenceSpan("d1", 3, 8, "DEFGH")
    assert find_containing_chunks(span3, chunks) == []

    # Span 4: different doc_id -> returns []
    span4 = EvidenceSpan("d_other", 1, 4, "BCD")
    assert find_containing_chunks(span4, chunks) == []


def test_chunk_documents_batch():
    """Verify batch chunking over multiple documents."""
    docs = [
        Document("d1", "Title 1", "https://example.com/1", "0123456789"),
        Document("d2", "Title 2", "https://example.com/2", "ABCDEFGHIJ"),
    ]
    chunks = chunk_documents(docs, chunk_size=6, chunk_overlap=2)
    assert len(chunks) == 4
    assert [c.doc_id for c in chunks] == ["d1", "d1", "d2", "d2"]
    assert [c.chunk_id for c in chunks] == [
        "d1_c0000",
        "d1_c0001",
        "d2_c0000",
        "d2_c0001",
    ]


def test_sample_dataset_chunking_containment():
    """Verify evidence containment on the sample corpus under agreed chunk settings."""
    documents, questions = load_dataset(
        Path("data/sample/documents.jsonl"),
        Path("data/sample/questions.jsonl"),
    )
    # Using agreed settings: chunk_size=300, chunk_overlap=80
    chunks = chunk_documents(documents, chunk_size=300, chunk_overlap=80)

    answerable_count = 0
    for q in questions:
        if q.is_answerable:
            answerable_count += 1
            for span in q.evidence_spans:
                containing = find_containing_chunks(span, chunks)
                assert (
                    len(containing) >= 1
                ), f"Question {q.id} lacks a fully containing chunk for span: {span}"
                for chunk in containing:
                    assert span.text in chunk.text

    assert (
        answerable_count == 7
    ), f"Expected exactly 7 answerable questions checked, got {answerable_count}"


def test_sample_dataset_boundary_crossing_behavior():
    """Verify that a tighter window demonstrates expected boundary-crossing behavior."""
    documents, questions = load_dataset(
        Path("data/sample/documents.jsonl"),
        Path("data/sample/questions.jsonl"),
    )
    # With chunk_size=350 and overlap=100, q_dataclass_frozen (237..366) crosses
    # the chunk boundary: Chunk 0 ends at 350 (< 366), Chunk 1 starts at 250 (> 237).
    chunks = chunk_documents(documents, chunk_size=350, chunk_overlap=100)
    q_frozen = next(q for q in questions if q.id == "q_dataclass_frozen")
    span = q_frozen.evidence_spans[0]

    # No single chunk fully contains it
    assert find_containing_chunks(span, chunks) == []
