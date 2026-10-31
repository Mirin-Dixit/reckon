"""Ingestion package: schemas and dataset validation."""

from .schema import (
    ALLOWED_AMBIGUITY_TYPES,
    ALLOWED_SPLITS,
    Document,
    EvidenceSpan,
    Question,
    UnanswerableCategory,
    ValidationError,
    validate_documents,
    validate_questions,
)

__all__ = [
    "ALLOWED_AMBIGUITY_TYPES",
    "ALLOWED_SPLITS",
    "Document",
    "EvidenceSpan",
    "Question",
    "UnanswerableCategory",
    "ValidationError",
    "validate_documents",
    "validate_questions",
]
