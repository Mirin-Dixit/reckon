"""Tests for dataset schema, serialization, and validation rules."""

import pytest
from app.ingestion import (
    Document,
    EvidenceSpan,
    Question,
    UnanswerableCategory,
    ValidationError,
    validate_documents,
    validate_questions,
)


def test_valid_document_roundtrip():
    """Verify Document serialization and deserialization."""
    doc_data = {
        "id": "doc_functools_cache",
        "title": "functools — Higher-order functions",
        "source_url": "https://docs.python.org/3/library/functools.html",
        "text": "cache(user_function) is a simple, lightweight wrapper for lru_cache.",
    }
    doc = Document.from_dict(doc_data)
    assert doc.id == "doc_functools_cache"
    assert doc.to_dict() == doc_data


def test_document_validation_failures():
    """Verify Document field validation checks."""
    # Missing required field
    with pytest.raises(ValidationError, match="missing required fields"):
        Document.from_dict({"id": "doc_1", "title": "T", "text": "Content"})

    # Non-string field
    with pytest.raises(ValidationError, match="must be a string"):
        Document(
            id="doc_1", title=123, source_url="https://example.com", text="T"  # type: ignore
        )

    # Empty string field
    with pytest.raises(ValidationError, match="cannot be empty"):
        Document(id="doc_1", title="  ", source_url="https://example.com", text="T")

    # Non-dict input
    with pytest.raises(ValidationError, match="must be a dict"):
        Document.from_dict(["not", "a", "dict"])  # type: ignore


def test_valid_evidence_span_roundtrip():
    """Verify EvidenceSpan serialization and deserialization."""
    span_data = {
        "doc_id": "doc_functools_cache",
        "start_char": 0,
        "end_char": 20,
        "text": "cache(user_function)",
    }
    span = EvidenceSpan.from_dict(span_data)
    assert span.start_char == 0
    assert span.end_char == 20
    assert span.to_dict() == span_data


def test_evidence_span_validation_failures():
    """Verify offset and boundary checks on EvidenceSpan."""
    # start_char >= end_char
    with pytest.raises(ValidationError, match="must be less than end_char"):
        EvidenceSpan(doc_id="d1", start_char=10, end_char=10, text="a")

    # Negative start_char
    with pytest.raises(ValidationError, match="must be >= 0"):
        EvidenceSpan(doc_id="d1", start_char=-1, end_char=5, text="a")

    # Non-integer offsets (strict typing rejects bool and float)
    with pytest.raises(ValidationError, match="must be integers"):
        EvidenceSpan(doc_id="d1", start_char=True, end_char=5, text="a")  # type: ignore

    with pytest.raises(ValidationError, match="must be integers"):
        EvidenceSpan(doc_id="d1", start_char=0, end_char=5.5, text="a")  # type: ignore


def test_valid_answerable_question():
    """Verify serialization and structure of a valid answerable question."""
    q_data = {
        "id": "q_001",
        "question": "What does cache() wrap?",
        "is_answerable": True,
        "question_type": "factoid",
        "expected_answer": "It wraps lru_cache(maxsize=None).",
        "absence_note": None,
        "unanswerable_category": None,
        "evidence_spans": [
            {
                "doc_id": "doc_1",
                "start_char": 5,
                "end_char": 14,
                "text": "lru_cache",
            }
        ],
    }
    question = Question.from_dict(q_data)
    assert question.is_answerable is True
    assert len(question.evidence_spans) == 1
    assert question.to_dict() == q_data


def test_valid_unanswerable_question_categories():
    """Verify that all three allowed unanswerable categories are accepted."""
    for category in UnanswerableCategory:
        q_data = {
            "id": f"q_un_{category.value}",
            "question": "Does urllib support max_retries?",
            "is_answerable": False,
            "question_type": "factoid",
            "expected_answer": None,
            "absence_note": "urllib.request does not feature max_retries parameter.",
            "unanswerable_category": category.value,
            "evidence_spans": [],
        }
        question = Question.from_dict(q_data)
        assert question.is_answerable is False
        assert question.unanswerable_category == category.value
        assert question.to_dict() == q_data


def test_strict_boolean_validation():
    """Verify that boolean answerability is strictly enforced."""
    base_data = {
        "id": "q_bool_test",
        "question": "Question text",
        "question_type": "factoid",
        "expected_answer": "Answer",
        "absence_note": None,
        "unanswerable_category": None,
        "evidence_spans": [
            {"doc_id": "d1", "start_char": 0, "end_char": 1, "text": "x"}
        ],
    }

    for invalid_bool in ("true", "false", 1, 0, None):
        with pytest.raises(ValidationError, match="must be a boolean"):
            Question.from_dict({**base_data, "is_answerable": invalid_bool})


def test_answerable_question_consistency():
    """Verify that answerable questions require expected_answer and evidence."""
    # Missing evidence spans
    with pytest.raises(ValidationError, match="at least one evidence span"):
        Question(
            id="q_ans_1",
            question="Q",
            is_answerable=True,
            question_type="factoid",
            expected_answer="Ans",
            evidence_spans=(),
        )

    # Missing expected answer
    with pytest.raises(ValidationError, match="non-empty 'expected_answer'"):
        Question(
            id="q_ans_2",
            question="Q",
            is_answerable=True,
            question_type="factoid",
            expected_answer=None,
            evidence_spans=(EvidenceSpan("d1", 0, 1, "a"),),
        )

    # Erroneous absence_note provided
    with pytest.raises(ValidationError, match="'absence_note' set to None"):
        Question(
            id="q_ans_3",
            question="Q",
            is_answerable=True,
            question_type="factoid",
            expected_answer="Ans",
            absence_note="Unexpected note",
            evidence_spans=(EvidenceSpan("d1", 0, 1, "a"),),
        )


def test_unanswerable_question_consistency():
    """Verify that unanswerable questions require absence_note and valid category."""
    # Evidence spans present
    with pytest.raises(ValidationError, match="must not have evidence spans"):
        Question(
            id="q_un_1",
            question="Q",
            is_answerable=False,
            question_type="factoid",
            absence_note="Note",
            unanswerable_category="off-topic",
            evidence_spans=(EvidenceSpan("d1", 0, 1, "a"),),
        )

    # Missing absence note
    with pytest.raises(ValidationError, match="non-empty 'absence_note'"):
        Question(
            id="q_un_2",
            question="Q",
            is_answerable=False,
            question_type="factoid",
            absence_note=None,
            unanswerable_category="off-topic",
        )

    # Invalid category
    with pytest.raises(ValidationError, match="invalid category 'arbitrary_reason'"):
        Question(
            id="q_un_3",
            question="Q",
            is_answerable=False,
            question_type="factoid",
            absence_note="Note",
            unanswerable_category="arbitrary_reason",
        )

    # Expected answer erroneously present
    with pytest.raises(ValidationError, match="'expected_answer' set to None"):
        Question(
            id="q_un_4",
            question="Q",
            is_answerable=False,
            question_type="factoid",
            expected_answer="Unexpected answer",
            absence_note="Note",
            unanswerable_category="off-topic",
        )


def test_validate_documents_uniqueness():
    """Verify document ID uniqueness enforcement."""
    docs = [
        Document("d1", "Title 1", "https://example.com/1", "Text 1"),
        Document("d2", "Title 2", "https://example.com/2", "Text 2"),
    ]
    validate_documents(docs)  # Should succeed

    duplicate_docs = [
        Document("d1", "Title 1", "https://example.com/1", "Text 1"),
        Document("d1", "Title 2", "https://example.com/2", "Text 2"),
    ]
    with pytest.raises(ValidationError, match="Duplicate document ID detected: 'd1'"):
        validate_documents(duplicate_docs)


def test_validate_questions_uniqueness():
    """Verify question ID uniqueness enforcement."""
    span = EvidenceSpan("d1", 0, 4, "Text")
    q1 = Question(
        "q1", "Q1", True, "factoid", expected_answer="A1", evidence_spans=(span,)
    )
    q2 = Question(
        "q1", "Q2", True, "factoid", expected_answer="A2", evidence_spans=(span,)
    )
    with pytest.raises(ValidationError, match="Duplicate question ID detected: 'q1'"):
        validate_questions([q1, q2])


def test_evidence_span_exact_slice_validation():
    """Verify that evidence spans are checked against exact document text slices."""
    doc_text = "The quick brown fox jumps over the lazy dog."
    doc = Document("doc_fox", "Fox Story", "https://example.com/fox", doc_text)
    docs_by_id = {"doc_fox": doc}

    # Valid span: doc_text[4:9] is "quick"
    valid_span = EvidenceSpan("doc_fox", 4, 9, "quick")
    valid_q = Question(
        "q_valid",
        "Find animal attribute",
        True,
        "factoid",
        expected_answer="quick",
        evidence_spans=(valid_span,),
    )
    validate_questions([valid_q], documents_by_id=docs_by_id)

    # Mismatched slice text
    bad_text_span = EvidenceSpan("doc_fox", 4, 9, "brown")
    bad_text_q = Question(
        "q_bad_slice",
        "Find animal attribute",
        True,
        "factoid",
        expected_answer="brown",
        evidence_spans=(bad_text_span,),
    )
    with pytest.raises(ValidationError, match="span text mismatch"):
        validate_questions([bad_text_q], documents_by_id=docs_by_id)

    # Span offset exceeding document text length
    overflow_span = EvidenceSpan("doc_fox", 0, len(doc_text) + 10, "overflow")
    overflow_q = Question(
        "q_overflow",
        "Q",
        True,
        "factoid",
        expected_answer="overflow",
        evidence_spans=(overflow_span,),
    )
    with pytest.raises(ValidationError, match="exceeds document 'doc_fox' text length"):
        validate_questions([overflow_q], documents_by_id=docs_by_id)

    # Unknown document ID reference
    unknown_doc_span = EvidenceSpan("doc_nonexistent", 0, 4, "test")
    unknown_doc_q = Question(
        "q_unknown",
        "Q",
        True,
        "factoid",
        expected_answer="test",
        evidence_spans=(unknown_doc_span,),
    )
    with pytest.raises(ValidationError, match="references unknown document ID"):
        validate_questions([unknown_doc_q], documents_by_id=docs_by_id)
