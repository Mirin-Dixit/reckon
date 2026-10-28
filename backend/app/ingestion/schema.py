"""Data schema and validation for documents, questions, and evidence spans."""

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ValidationError(ValueError):
    """Raised when a dataset record fails schema validation."""


class UnanswerableCategory(StrEnum):
    """Allowed reason categories for unanswerable evaluation questions."""

    OFF_TOPIC = "off-topic"
    TEMPORAL_NEAR_MISS = "temporal_near_miss"
    ENTITY_ATTRIBUTE_NEAR_MISS = "entity_attribute_near_miss"


@dataclass(frozen=True)
class Document:
    """A document in the evaluation corpus."""

    id: str
    title: str
    source_url: str
    text: str

    def __post_init__(self) -> None:
        """Validate field types and contents upon initialization."""
        for field_name in ("id", "title", "source_url", "text"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                t_name = type(value).__name__
                raise ValidationError(
                    f"Document '{field_name}' must be a string, got {t_name}"
                )
            if not value.strip():
                raise ValidationError(f"Document '{field_name}' cannot be empty")

    def to_dict(self) -> dict[str, str]:
        """Serialize the document to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":
        """Deserialize and validate a document from a dictionary."""
        if not isinstance(data, dict):
            raise ValidationError(
                f"Document record must be a dict, got {type(data).__name__}"
            )
        required_fields = {"id", "title", "source_url", "text"}
        missing = required_fields - data.keys()
        if missing:
            raise ValidationError(
                f"Document missing required fields: {sorted(missing)}"
            )
        return cls(
            id=data["id"],
            title=data["title"],
            source_url=data["source_url"],
            text=data["text"],
        )


@dataclass(frozen=True)
class EvidenceSpan:
    """A character-level span in a document providing evidence for a question."""

    doc_id: str
    start_char: int
    end_char: int
    text: str

    def __post_init__(self) -> None:
        """Validate span offsets and contents upon initialization."""
        if not isinstance(self.doc_id, str) or not self.doc_id.strip():
            raise ValidationError("EvidenceSpan 'doc_id' must be a non-empty string")
        if not isinstance(self.text, str) or len(self.text) == 0:
            raise ValidationError("EvidenceSpan 'text' must be a non-empty string")

        # Explicitly check exact int type so booleans are rejected
        if type(self.start_char) is not int or type(self.end_char) is not int:
            raise ValidationError("EvidenceSpan offsets must be integers")

        if self.start_char < 0:
            raise ValidationError(
                f"EvidenceSpan 'start_char' must be >= 0, got {self.start_char}"
            )
        if self.start_char >= self.end_char:
            raise ValidationError(
                f"EvidenceSpan start_char ({self.start_char}) must be less than "
                f"end_char ({self.end_char})"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the evidence span to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceSpan":
        """Deserialize and validate an evidence span from a dictionary."""
        if not isinstance(data, dict):
            raise ValidationError(
                f"EvidenceSpan must be a dict, got {type(data).__name__}"
            )
        required_fields = {"doc_id", "start_char", "end_char", "text"}
        missing = required_fields - data.keys()
        if missing:
            raise ValidationError(
                f"EvidenceSpan missing required fields: {sorted(missing)}"
            )
        return cls(
            doc_id=data["doc_id"],
            start_char=data["start_char"],
            end_char=data["end_char"],
            text=data["text"],
        )


@dataclass(frozen=True)
class Question:
    """An evaluation question targeting the corpus."""

    id: str
    question: str
    is_answerable: bool
    question_type: str
    expected_answer: str | None = None
    absence_note: str | None = None
    unanswerable_category: str | None = None
    evidence_spans: tuple[EvidenceSpan, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate question fields and answerability consistency."""
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValidationError("Question 'id' must be a non-empty string")
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValidationError("Question 'question' must be a non-empty string")
        if not isinstance(self.question_type, str) or not self.question_type.strip():
            raise ValidationError("Question 'question_type' must be a non-empty string")

        # Strict boolean validation (reject "true", 1, 0, etc.)
        if type(self.is_answerable) is not bool:
            t_name = type(self.is_answerable).__name__
            raise ValidationError(
                f"Question 'is_answerable' must be a boolean, got {t_name}"
            )

        if self.is_answerable:
            if (
                not isinstance(self.expected_answer, str)
                or not self.expected_answer.strip()
            ):
                raise ValidationError(
                    "Answerable question must have a non-empty 'expected_answer'"
                )
            if self.absence_note is not None:
                raise ValidationError(
                    "Answerable question must have 'absence_note' set to None"
                )
            if self.unanswerable_category is not None:
                raise ValidationError(
                    "Answerable question must have 'unanswerable_category' set to None"
                )
            if len(self.evidence_spans) == 0:
                raise ValidationError(
                    "Answerable question must contain at least one evidence span"
                )
        else:
            if self.expected_answer is not None:
                raise ValidationError(
                    "Unanswerable question must have 'expected_answer' set to None"
                )
            if not isinstance(self.absence_note, str) or not self.absence_note.strip():
                raise ValidationError(
                    "Unanswerable question must have a non-empty 'absence_note'"
                )

            valid_categories = {c.value for c in UnanswerableCategory}
            if self.unanswerable_category not in valid_categories:
                raise ValidationError(
                    f"Unanswerable question has invalid category "
                    f"'{self.unanswerable_category}'. "
                    f"Must be one of: {sorted(valid_categories)}"
                )
            if len(self.evidence_spans) > 0:
                raise ValidationError(
                    "Unanswerable question must not have evidence spans"
                )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the question to a dictionary."""
        return {
            "id": self.id,
            "question": self.question,
            "is_answerable": self.is_answerable,
            "question_type": self.question_type,
            "expected_answer": self.expected_answer,
            "absence_note": self.absence_note,
            "unanswerable_category": self.unanswerable_category,
            "evidence_spans": [span.to_dict() for span in self.evidence_spans],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Question":
        """Deserialize and validate a question from a dictionary."""
        if not isinstance(data, dict):
            raise ValidationError(
                f"Question record must be a dict, got {type(data).__name__}"
            )
        required_fields = {
            "id",
            "question",
            "is_answerable",
            "question_type",
            "expected_answer",
            "absence_note",
            "unanswerable_category",
            "evidence_spans",
        }
        missing = required_fields - data.keys()
        if missing:
            raise ValidationError(
                f"Question missing required fields: {sorted(missing)}"
            )

        raw_spans = data.get("evidence_spans")
        if not isinstance(raw_spans, list):
            t_name = type(raw_spans).__name__
            raise ValidationError(
                f"Question 'evidence_spans' must be a list, got {t_name}"
            )

        parsed_spans = tuple(
            EvidenceSpan.from_dict(span) if isinstance(span, dict) else span
            for span in raw_spans
        )

        return cls(
            id=data["id"],
            question=data["question"],
            is_answerable=data["is_answerable"],
            question_type=data["question_type"],
            expected_answer=data.get("expected_answer"),
            absence_note=data.get("absence_note"),
            unanswerable_category=data.get("unanswerable_category"),
            evidence_spans=parsed_spans,
        )


def validate_documents(documents: list[Document]) -> None:
    """Validate a collection of documents for uniqueness and consistency."""
    seen_ids: set[str] = set()
    for doc in documents:
        if not isinstance(doc, Document):
            raise ValidationError(
                f"Expected Document instance, got {type(doc).__name__}"
            )
        if doc.id in seen_ids:
            raise ValidationError(f"Duplicate document ID detected: '{doc.id}'")
        seen_ids.add(doc.id)


def validate_questions(
    questions: list[Question],
    documents_by_id: dict[str, Document] | None = None,
) -> None:
    """Validate questions for uniqueness and referential integrity against documents."""
    seen_ids: set[str] = set()
    for q in questions:
        if not isinstance(q, Question):
            raise ValidationError(f"Expected Question instance, got {type(q).__name__}")
        if q.id in seen_ids:
            raise ValidationError(f"Duplicate question ID detected: '{q.id}'")
        seen_ids.add(q.id)

        if documents_by_id is not None:
            for span in q.evidence_spans:
                if span.doc_id not in documents_by_id:
                    raise ValidationError(
                        f"Question '{q.id}' references unknown "
                        f"document ID '{span.doc_id}'"
                    )
                doc = documents_by_id[span.doc_id]
                if span.end_char > len(doc.text):
                    raise ValidationError(
                        f"Question '{q.id}' span offset end_char ({span.end_char}) "
                        f"exceeds document '{doc.id}' text length ({len(doc.text)})"
                    )
                actual_slice = doc.text[span.start_char : span.end_char]
                if actual_slice != span.text:
                    raise ValidationError(
                        f"Question '{q.id}' span text mismatch in document '{doc.id}'. "
                        f"Expected {span.text!r}, found {actual_slice!r}"
                    )
