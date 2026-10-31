"""Utilities for loading and validating dataset records from JSONL files."""

import hashlib
import io
import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TypeVar

from app.ingestion.schema import (
    Document,
    Question,
    ValidationError,
    validate_documents,
    validate_questions,
)

Record = TypeVar("Record")


def _read_payload(path: Path, label: str) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(f"{label} file not found: {path}")
    return path.read_bytes()


def _parse_records(
    lines: Iterable[str], name: str, constructor: Callable[..., Record]
) -> list[Record]:
    records = []
    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError(
                f"Invalid JSON on line {line_num} in {name}: {error}"
            ) from error
        records.append(constructor(data))
    return records


def load_documents_from_jsonl(file_path: str | Path) -> list[Document]:
    """Load and validate Document records from a JSONL file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Documents file not found: {path}")
    with path.open("r", encoding="utf-8") as source:
        documents = _parse_records(source, path.name, Document.from_dict)
    validate_documents(documents)
    return documents


def load_questions_from_jsonl(file_path: str | Path) -> list[Question]:
    """Load Question records from a JSONL file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Questions file not found: {path}")
    with path.open("r", encoding="utf-8") as source:
        return _parse_records(source, path.name, Question.from_dict)


def load_dataset_snapshot(
    documents_path: str | Path,
    questions_path: str | Path,
) -> tuple[list[Document], list[Question], dict[str, str]]:
    """Validate and fingerprint the exact captured bytes used for an experiment."""
    doc_path, question_path = Path(documents_path), Path(questions_path)
    doc_bytes = _read_payload(doc_path, "Documents")
    question_bytes = _read_payload(question_path, "Questions")
    # Match text-file newlines without splitting Unicode separators inside JSON.
    documents = _parse_records(
        io.StringIO(doc_bytes.decode("utf-8"), newline=None),
        doc_path.name,
        Document.from_dict,
    )
    questions = _parse_records(
        io.StringIO(question_bytes.decode("utf-8"), newline=None),
        question_path.name,
        Question.from_dict,
    )
    validate_documents(documents)
    validate_questions(questions, documents_by_id={doc.id: doc for doc in documents})
    return (
        documents,
        questions,
        {
            "documents_sha256": hashlib.sha256(doc_bytes).hexdigest(),
            "questions_sha256": hashlib.sha256(question_bytes).hexdigest(),
        },
    )


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
