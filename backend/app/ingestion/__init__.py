"""Ingestion package: schemas and dataset validation."""

from .schema import (
    Document,
    EvidenceSpan,
    Question,
    UnanswerableCategory,
    ValidationError,
    validate_documents,
    validate_questions,
)

__all__ = [
    "Document",
    "EvidenceSpan",
    "Question",
    "UnanswerableCategory",
    "ValidationError",
    "validate_documents",
    "validate_questions",
]
