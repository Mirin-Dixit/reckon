"""Deterministic fixed-size character chunking and evidence-span mapping."""

from dataclasses import asdict, dataclass
from typing import Any

from app.ingestion.schema import Document, EvidenceSpan


@dataclass(frozen=True)
class Chunk:
    """A deterministic character-slice chunk from a parent document."""

    chunk_id: str
    doc_id: str
    index: int
    start_char: int
    end_char: int
    text: str

    def __post_init__(self) -> None:
        """Validate chunk fields and character bounds."""
        if not isinstance(self.chunk_id, str) or not self.chunk_id.strip():
            raise ValueError("Chunk 'chunk_id' must be a non-empty string")
        if not isinstance(self.doc_id, str) or not self.doc_id.strip():
            raise ValueError("Chunk 'doc_id' must be a non-empty string")
        if type(self.index) is not int or self.index < 0:
            raise ValueError("Chunk 'index' must be a non-negative integer")
        if type(self.start_char) is not int or self.start_char < 0:
            raise ValueError("Chunk 'start_char' must be a non-negative integer")
        if type(self.end_char) is not int or self.end_char <= self.start_char:
            raise ValueError(
                f"Chunk 'end_char' ({self.end_char}) must be strictly greater than "
                f"'start_char' ({self.start_char})"
            )
        if not isinstance(self.text, str) or len(self.text) == 0:
            raise ValueError("Chunk 'text' must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the chunk to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chunk":
        """Deserialize a chunk from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(f"Chunk record must be a dict, got {type(data).__name__}")
        required_fields = {
            "chunk_id",
            "doc_id",
            "index",
            "start_char",
            "end_char",
            "text",
        }
        missing = required_fields - data.keys()
        if missing:
            raise ValueError(f"Chunk missing required fields: {sorted(missing)}")
        return cls(
            chunk_id=data["chunk_id"],
            doc_id=data["doc_id"],
            index=data["index"],
            start_char=data["start_char"],
            end_char=data["end_char"],
            text=data["text"],
        )


def chunk_document(
    document: Document,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Split a document into fixed-size character chunks with overlap.

    Stops generating chunks immediately once a chunk reaches the end of the
    document, avoiding unnecessary or duplicate trailing chunks.
    """
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError(f"chunk_size must be a positive integer, got {chunk_size!r}")
    if type(chunk_overlap) is not int or chunk_overlap < 0:
        raise ValueError(
            f"chunk_overlap must be a non-negative integer, got {chunk_overlap!r}"
        )
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be strictly less than "
            f"chunk_size ({chunk_size})"
        )

    text = document.text
    if len(text) == 0:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_slice = text[start:end]
        chunk_id = f"{document.id}_c{index:04d}"

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                doc_id=document.id,
                index=index,
                start_char=start,
                end_char=end,
                text=chunk_slice,
            )
        )

        # Stop immediately once the current chunk reaches the end of the text
        if end >= len(text):
            break

        start += step
        index += 1

    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Split a sequence of documents into chunks."""
    all_chunks: list[Chunk] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, chunk_size, chunk_overlap))
    return all_chunks


def find_containing_chunks(
    span: EvidenceSpan,
    chunks: list[Chunk],
) -> list[Chunk]:
    """Return all chunks from the same document that fully contain the span."""
    return [
        c
        for c in chunks
        if c.doc_id == span.doc_id
        and c.start_char <= span.start_char
        and c.end_char >= span.end_char
    ]
