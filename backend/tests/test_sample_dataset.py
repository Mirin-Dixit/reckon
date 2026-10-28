"""Tests verifying the sample Python 3.11 dataset against the schema."""

from pathlib import Path

import pytest
from app.ingestion.loader import (
    load_dataset,
    load_documents_from_jsonl,
    load_questions_from_jsonl,
)
from app.ingestion.schema import UnanswerableCategory, ValidationError

DOCUMENTS_PATH = Path("data/sample/documents.jsonl")
QUESTIONS_PATH = Path("data/sample/questions.jsonl")


def test_load_sample_dataset_validity():
    """Verify that the sample dataset loads cleanly without validation errors."""
    assert DOCUMENTS_PATH.is_file(), f"Missing {DOCUMENTS_PATH}"
    assert QUESTIONS_PATH.is_file(), f"Missing {QUESTIONS_PATH}"

    documents, questions = load_dataset(DOCUMENTS_PATH, QUESTIONS_PATH)

    assert len(documents) == 5
    assert len(questions) == 10

    # Ensure all documents point to authoritative Python 3.11 URLs
    for doc in documents:
        assert doc.source_url.startswith("https://docs.python.org/3.11/")
        assert len(doc.text) > 0


def test_sample_question_distribution():
    """Verify the agreed 7-answerable and 3-unanswerable distribution."""
    _, questions = load_dataset(DOCUMENTS_PATH, QUESTIONS_PATH)

    answerable = [q for q in questions if q.is_answerable]
    unanswerable = [q for q in questions if not q.is_answerable]

    assert len(answerable) == 7
    assert len(unanswerable) == 3

    # Verify all three unanswerable categories are represented exactly once
    categories = {q.unanswerable_category for q in unanswerable}
    assert categories == {
        UnanswerableCategory.OFF_TOPIC.value,
        UnanswerableCategory.TEMPORAL_NEAR_MISS.value,
        UnanswerableCategory.ENTITY_ATTRIBUTE_NEAR_MISS.value,
    }


def test_evidence_spans_verbatim_slices():
    """Verify that every evidence span matches the exact document slice."""
    documents, questions = load_dataset(DOCUMENTS_PATH, QUESTIONS_PATH)
    docs_by_id = {doc.id: doc for doc in documents}

    for q in questions:
        if q.is_answerable:
            assert len(q.evidence_spans) >= 1
            for span in q.evidence_spans:
                doc = docs_by_id[span.doc_id]
                expected_slice = doc.text[span.start_char : span.end_char]
                assert span.text == expected_slice


def test_unanswerable_corpus_wide_absence():
    """Verify semantic absence and corpus-wide screening for unanswerable questions."""
    documents, questions = load_dataset(DOCUMENTS_PATH, QUESTIONS_PATH)
    all_text = " ".join(doc.text.lower() for doc in documents)

    unanswerable_by_id = {q.id: q for q in questions if not q.is_answerable}

    # 1. Off-topic: Google Guava
    q_guava = unanswerable_by_id["q_guava_cache"]
    assert "guava" in q_guava.absence_note.lower()
    assert "guava" not in all_text
    assert "cachebuilder" not in all_text

    # 2. Temporal near-miss: itertools.batched
    q_batched = unanswerable_by_id["q_itertools_batched"]
    assert "python 3.12" in q_batched.absence_note.lower()
    assert "python 3.11" in q_batched.absence_note.lower()
    assert "batched" not in all_text

    # 3. Entity/attribute near-miss: functools.lru_cache ttl
    q_ttl = unanswerable_by_id["q_lru_ttl"]
    assert "ttl" in q_ttl.absence_note.lower()
    assert "ttl" not in all_text
    assert "expiration" not in all_text


def test_loader_error_handling(tmp_path: Path):
    """Verify file not found and corrupted line handling in loader."""
    with pytest.raises(FileNotFoundError):
        load_documents_from_jsonl(tmp_path / "nonexistent.jsonl")

    corrupted_file = tmp_path / "bad.jsonl"
    corrupted_file.write_text("{not-valid-json\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="Invalid JSON"):
        load_documents_from_jsonl(corrupted_file)

    with pytest.raises(ValidationError, match="Invalid JSON"):
        load_questions_from_jsonl(corrupted_file)
