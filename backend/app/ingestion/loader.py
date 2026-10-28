"""Utilities for loading and validating dataset records from JSONL files."""

import json
from pathlib import Path

from app.ingestion.schema import (
    Document,
    Question,
    ValidationError,
    validate_documents,
    validate_questions,
)


def load_documents_from_jsonl(file_path: str | Path) -> list[Document]:
    """Load and validate Document records from a JSONL file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Documents file not found: {path}")

    documents: list[Document] = []
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as err:
                raise ValidationError(
                    f"Invalid JSON on line {line_num} in {path.name}: {err}"
                ) from err
            documents.append(Document.from_dict(data))

    validate_documents(documents)
    return documents


def load_questions_from_jsonl(file_path: str | Path) -> list[Question]:
    """Load Question records from a JSONL file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Questions file not found: {path}")

    questions: list[Question] = []
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as err:
                raise ValidationError(
                    f"Invalid JSON on line {line_num} in {path.name}: {err}"
                ) from err
            questions.append(Question.from_dict(data))

    return questions


def load_dataset(
    documents_path: str | Path,
    questions_path: str | Path,
) -> tuple[list[Document], list[Question]]:
    """Load and cross-validate documents and questions from JSONL files."""
    documents = load_documents_from_jsonl(documents_path)
    questions = load_questions_from_jsonl(questions_path)

    documents_by_id = {doc.id: doc for doc in documents}
    validate_questions(questions, documents_by_id=documents_by_id)

    return documents, questions
