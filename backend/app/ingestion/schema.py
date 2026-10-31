"""Data schema and validation for documents, questions, and evidence spans."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

ALLOWED_SPLITS = frozenset({"train", "dev", "test"})
ALLOWED_AMBIGUITY_TYPES = frozenset(
    {"qualified_answer", "clarification_required", "unanswerable"}
)


class ValidationError(ValueError):
    """Raised when a dataset record fails schema validation."""


class UnanswerableCategory(StrEnum):
    """Allowed reason categories for unanswerable evaluation questions."""

    OFF_TOPIC = "off-topic"
    TEMPORAL_NEAR_MISS = "temporal_near_miss"
    ENTITY_ATTRIBUTE_NEAR_MISS = "entity_attribute_near_miss"
    CONFLICTING_SOURCES = "conflicting_sources"
    AMBIGUOUS_QUESTION = "ambiguous_question"
    SUPERSEDED_INFORMATION = "superseded_information"
    COMPOUND_PARTIAL = "compound_partial"
    ADVERSARIAL_INJECTION = "adversarial_injection"


@dataclass(frozen=True)
class Document:
    """A document in the evaluation corpus."""

    id: str
    title: str
    source_url: str
    text: str
    version: str | None = None
    source_date: str | None = None
    domain: str = "general"
    superseded_by: str | None = None
    contains_injection: bool = False
    injection_spans: tuple[tuple[int, int], ...] = field(default_factory=tuple)
    _explicit_fields: tuple[str, ...] = field(
        default_factory=tuple, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Validate field types, contents, and injection spans."""
        for field_name in ("id", "title", "source_url", "text"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                t_name = type(value).__name__
                raise ValidationError(
                    f"Document '{field_name}' must be a string, got {t_name}"
                )
            if not value.strip():
                raise ValidationError(f"Document '{field_name}' cannot be empty")

        if self.version is not None:
            if not isinstance(self.version, str) or not self.version.strip():
                raise ValidationError("Document 'version' must be a non-empty string")

        if self.source_date is not None:
            if not isinstance(self.source_date, str) or not self.source_date.strip():
                raise ValidationError(
                    "Document 'source_date' must be a non-empty string"
                )

        if not isinstance(self.domain, str) or not self.domain.strip():
            raise ValidationError("Document 'domain' must be a non-empty string")

        if self.superseded_by is not None:
            if (
                not isinstance(self.superseded_by, str)
                or not self.superseded_by.strip()
            ):
                raise ValidationError(
                    "Document 'superseded_by' must be a non-empty string"
                )
            if self.superseded_by == self.id:
                raise ValidationError(
                    f"Document '{self.id}' cannot be superseded by itself"
                )

        if type(self.contains_injection) is not bool:
            t_name = type(self.contains_injection).__name__
            raise ValidationError(
                f"Document 'contains_injection' must be a boolean, got {t_name}"
            )

        if not isinstance(self.injection_spans, tuple):
            try:
                converted_spans = tuple(tuple(s) for s in self.injection_spans)
                object.__setattr__(self, "injection_spans", converted_spans)
            except Exception as err:
                raise ValidationError(
                    "Document 'injection_spans' must be an iterable of coordinate "
                    f"pairs: {err}"
                ) from err

        for span in self.injection_spans:
            if not isinstance(span, tuple) or len(span) != 2:
                raise ValidationError(
                    f"Each span in 'injection_spans' must be a 2-tuple, got {span!r}"
                )
            start, end = span
            if type(start) is not int or type(end) is not int:
                t_start = type(start).__name__
                t_end = type(end).__name__
                raise ValidationError(
                    "Span offsets in 'injection_spans' must be integers, got "
                    f"({t_start}, {t_end})"
                )
            if start < 0:
                raise ValidationError(
                    f"Injection span start offset must be >= 0, got {start}"
                )
            if start >= end:
                raise ValidationError(
                    f"Injection span start offset ({start}) must be strictly less than "
                    f"end offset ({end})"
                )
            if end > len(self.text):
                raise ValidationError(
                    f"Injection span end offset ({end}) exceeds text length "
                    f"({len(self.text)})"
                )

        sorted_spans = sorted(self.injection_spans, key=lambda s: s[0])
        for i in range(1, len(sorted_spans)):
            prev_start, prev_end = sorted_spans[i - 1]
            curr_start, curr_end = sorted_spans[i]
            if curr_start < prev_end:
                raise ValidationError(
                    f"Overlapping injection spans detected: ({prev_start}, {prev_end}) "
                    f"and ({curr_start}, {curr_end})"
                )

        if self.contains_injection and len(self.injection_spans) == 0:
            raise ValidationError(
                "Document marked contains_injection=True must specify at least one "
                "injection span"
            )
        if not self.contains_injection and len(self.injection_spans) > 0:
            raise ValidationError(
                "Document marked contains_injection=False must not have injection spans"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the document to a dictionary."""
        d: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "source_url": self.source_url,
            "text": self.text,
        }
        if "version" in self._explicit_fields or self.version is not None:
            d["version"] = self.version
        if "source_date" in self._explicit_fields or self.source_date is not None:
            d["source_date"] = self.source_date
        if "domain" in self._explicit_fields or self.domain != "general":
            d["domain"] = self.domain
        if "superseded_by" in self._explicit_fields or self.superseded_by is not None:
            d["superseded_by"] = self.superseded_by
        if "contains_injection" in self._explicit_fields or self.contains_injection:
            d["contains_injection"] = self.contains_injection
        if "injection_spans" in self._explicit_fields or len(self.injection_spans) > 0:
            d["injection_spans"] = [list(s) for s in self.injection_spans]
        return d

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

        extended_fields = {
            "version",
            "source_date",
            "domain",
            "superseded_by",
            "contains_injection",
            "injection_spans",
        }
        explicit = tuple(k for k in extended_fields if k in data)

        injection_spans_raw = data.get("injection_spans", ())
        if not isinstance(injection_spans_raw, (list, tuple)):
            t_raw = type(injection_spans_raw).__name__
            raise ValidationError(
                f"Document 'injection_spans' must be a list or tuple, got {t_raw}"
            )
        parsed_injection_spans = tuple(tuple(s) for s in injection_spans_raw)

        return cls(
            id=data["id"],
            title=data["title"],
            source_url=data["source_url"],
            text=data["text"],
            version=data.get("version"),
            source_date=data.get("source_date"),
            domain=data.get("domain", "general"),
            superseded_by=data.get("superseded_by"),
            contains_injection=data.get("contains_injection", False),
            injection_spans=parsed_injection_spans,
            _explicit_fields=explicit,
        )


@dataclass(frozen=True)
class EvidenceSpan:
    """A character-level span in a document providing evidence for a question."""

    doc_id: str
    start_char: int
    end_char: int
    text: str
    id: str = ""
    _explicit_id: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate span offsets, contents, and deterministic ID."""
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

        expected_id = f"{self.doc_id}_s{self.start_char}_{self.end_char}"
        if self.id != "":
            if not isinstance(self.id, str) or not self.id.strip():
                raise ValidationError("EvidenceSpan 'id' must be a non-empty string")
            if self.id != expected_id:
                raise ValidationError(
                    f"EvidenceSpan 'id' must match '{expected_id}', got '{self.id}'"
                )
            object.__setattr__(self, "_explicit_id", True)
        else:
            object.__setattr__(self, "id", expected_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the evidence span to a dictionary."""
        d: dict[str, Any] = {
            "doc_id": self.doc_id,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "text": self.text,
        }
        if self._explicit_id:
            d["id"] = self.id
        return d

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
        if "id" in data:
            return cls(
                doc_id=data["doc_id"],
                start_char=data["start_char"],
                end_char=data["end_char"],
                text=data["text"],
                id=data["id"],
                _explicit_id=True,
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
    split: str = "dev"
    domain: str = "general"
    compound_required_spans: tuple[str, ...] = field(default_factory=tuple)
    compound_missing_premises: tuple[str, ...] = field(default_factory=tuple)
    ambiguity_type: str | None = None
    ambiguity_note: str | None = None
    conflict_doc_ids: tuple[str, ...] = field(default_factory=tuple)
    conflict_resolution_rule: str | None = None
    expected_safe_behavior: str | None = None
    _explicit_fields: tuple[str, ...] = field(
        default_factory=tuple, repr=False, compare=False
    )

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

        # Split validation (spec §3.6 rule 1)
        if type(self.split) is not str:
            raise ValidationError(
                f"Question 'split' must be a string, got {type(self.split).__name__}"
            )
        if self.split not in ALLOWED_SPLITS:
            allowed = sorted(ALLOWED_SPLITS)
            raise ValidationError(
                f"Question 'split' must be one of {allowed}, got '{self.split}'"
            )

        # Domain validation
        if not isinstance(self.domain, str) or not self.domain.strip():
            raise ValidationError("Question 'domain' must be a non-empty string")

        # Normalize evidence_spans tuple
        if not isinstance(self.evidence_spans, tuple):
            object.__setattr__(self, "evidence_spans", tuple(self.evidence_spans))

        for span in self.evidence_spans:
            if not isinstance(span, EvidenceSpan):
                t_span = type(span).__name__
                raise ValidationError(
                    f"Evidence span must be EvidenceSpan instance, got {t_span}"
                )

        # Unique span IDs within question evidence_spans (spec §3.3)
        seen_span_ids: set[str] = set()
        for span in self.evidence_spans:
            if span.id in seen_span_ids:
                raise ValidationError(
                    f"Duplicate evidence span ID detected in question '{self.id}': "
                    f"'{span.id}'"
                )
            seen_span_ids.add(span.id)

        # Normalize collection fields to tuples of strings
        for field_name in (
            "compound_required_spans",
            "compound_missing_premises",
            "conflict_doc_ids",
        ):
            val = getattr(self, field_name)
            if not isinstance(val, tuple):
                if not isinstance(val, (list, tuple)):
                    t_val = type(val).__name__
                    raise ValidationError(
                        f"Question '{field_name}' must be a list or tuple, got {t_val}"
                    )
                object.__setattr__(self, field_name, tuple(val))
            normalized = getattr(self, field_name)
            for item in normalized:
                if not isinstance(item, str) or not item.strip():
                    raise ValidationError(
                        f"Items in Question '{field_name}' must be non-empty strings, "
                        f"got {item!r}"
                    )

        if len(self.conflict_doc_ids) != len(set(self.conflict_doc_ids)):
            raise ValidationError(
                f"Question '{self.id}' 'conflict_doc_ids' contains duplicate "
                "document IDs"
            )

        # Optional string fields validation
        if self.ambiguity_type is not None:
            if self.ambiguity_type not in ALLOWED_AMBIGUITY_TYPES:
                allowed_amb = sorted(ALLOWED_AMBIGUITY_TYPES)
                raise ValidationError(
                    f"Question 'ambiguity_type' must be one of {allowed_amb}, "
                    f"got '{self.ambiguity_type}'"
                )
        if self.ambiguity_note is not None:
            if (
                not isinstance(self.ambiguity_note, str)
                or not self.ambiguity_note.strip()
            ):
                raise ValidationError(
                    "Question 'ambiguity_note' must be a non-empty string"
                )
        if self.conflict_resolution_rule is not None:
            if (
                not isinstance(self.conflict_resolution_rule, str)
                or not self.conflict_resolution_rule.strip()
            ):
                raise ValidationError(
                    "Question 'conflict_resolution_rule' must be a non-empty string"
                )
        if self.expected_safe_behavior is not None:
            if (
                not isinstance(self.expected_safe_behavior, str)
                or not self.expected_safe_behavior.strip()
            ):
                raise ValidationError(
                    "Question 'expected_safe_behavior' must be a non-empty string"
                )

        # Cross-field validation (spec §3.6)
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

            if self.question_type == "compound":
                # Spec §3.6 rule 3 (Compound Answerable)
                if len(self.evidence_spans) < 2:
                    raise ValidationError(
                        "Compound answerable question must contain at least 2 "
                        f"evidence spans, got {len(self.evidence_spans)}"
                    )
                if len(self.compound_required_spans) < 2:
                    raise ValidationError(
                        "Compound answerable question must contain at least 2 "
                        f"'compound_required_spans', "
                        f"got {len(self.compound_required_spans)}"
                    )
                span_ids = {s.id for s in self.evidence_spans}
                required_set = set(self.compound_required_spans)
                if span_ids != required_set:
                    raise ValidationError(
                        "Compound answerable 'compound_required_spans' must match "
                        f"evidence span IDs exactly. Spans: {sorted(span_ids)}, "
                        f"Required: {sorted(required_set)}"
                    )
                if len(self.compound_required_spans) != len(self.evidence_spans):
                    raise ValidationError(
                        "Compound answerable 'compound_required_spans' contains "
                        "duplicate span IDs"
                    )
                if len(self.compound_missing_premises) > 0:
                    raise ValidationError(
                        "Compound answerable question must have empty "
                        "'compound_missing_premises'"
                    )
            else:
                # Spec §3.6 rule 2 (Standard Answerable)
                if len(self.evidence_spans) == 0:
                    raise ValidationError(
                        "Answerable question must contain at least one evidence span"
                    )
                if len(self.compound_required_spans) > 0:
                    raise ValidationError(
                        "Non-compound answerable question must have empty "
                        "'compound_required_spans'"
                    )
                if len(self.compound_missing_premises) > 0:
                    raise ValidationError(
                        "Non-compound answerable question must have empty "
                        "'compound_missing_premises'"
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

            if (
                self.unanswerable_category
                == UnanswerableCategory.COMPOUND_PARTIAL.value
            ):
                # Spec §3.6 rule 5 (Compound Partial Unanswerable)
                if len(self.evidence_spans) == 0:
                    raise ValidationError(
                        "Compound partial unanswerable question must contain at least "
                        "one evidence span representing partial evidence present in "
                        "the corpus"
                    )
                if len(self.compound_required_spans) == 0:
                    raise ValidationError(
                        "Compound partial unanswerable question must contain at least "
                        "one 'compound_required_spans' matching present evidence spans"
                    )
                span_ids = {s.id for s in self.evidence_spans}
                required_set = set(self.compound_required_spans)
                if span_ids != required_set:
                    raise ValidationError(
                        "Compound partial 'compound_required_spans' must match "
                        f"evidence span IDs exactly. Spans: {sorted(span_ids)}, "
                        f"Required: {sorted(required_set)}"
                    )
                if len(self.compound_required_spans) != len(self.evidence_spans):
                    raise ValidationError(
                        "Compound partial 'compound_required_spans' contains "
                        "duplicate span IDs"
                    )
                if len(self.compound_missing_premises) == 0:
                    raise ValidationError(
                        "Compound partial unanswerable question must contain at least "
                        "one description in 'compound_missing_premises'"
                    )
            else:
                # Spec §3.6 rule 4 (Standard Unanswerable)
                if len(self.evidence_spans) > 0:
                    raise ValidationError(
                        "Unanswerable question must not have evidence spans"
                    )
                if len(self.compound_required_spans) > 0:
                    raise ValidationError(
                        "Standard unanswerable question must have empty "
                        "'compound_required_spans'"
                    )
                if len(self.compound_missing_premises) > 0:
                    raise ValidationError(
                        "Standard unanswerable question must have empty "
                        "'compound_missing_premises'"
                    )

            # Spec §3.6 rule 6 (Conflicting Sources)
            if (
                self.unanswerable_category
                == UnanswerableCategory.CONFLICTING_SOURCES.value
            ):
                if len(self.conflict_doc_ids) < 2:
                    raise ValidationError(
                        "Conflicting sources question must specify at least 2 "
                        "distinct document IDs in 'conflict_doc_ids'"
                    )

            # Spec §3.6 rule 7 (Adversarial)
            if (
                self.unanswerable_category
                == UnanswerableCategory.ADVERSARIAL_INJECTION.value
                or self.question_type == "adversarial"
            ):
                if self.expected_safe_behavior is None:
                    raise ValidationError(
                        "Adversarial question must specify non-empty "
                        "'expected_safe_behavior'"
                    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the question to a dictionary."""
        d: dict[str, Any] = {
            "id": self.id,
            "question": self.question,
            "is_answerable": self.is_answerable,
            "question_type": self.question_type,
            "expected_answer": self.expected_answer,
            "absence_note": self.absence_note,
            "unanswerable_category": self.unanswerable_category,
            "evidence_spans": [span.to_dict() for span in self.evidence_spans],
        }
        if "split" in self._explicit_fields or self.split != "dev":
            d["split"] = self.split
        if "domain" in self._explicit_fields or self.domain != "general":
            d["domain"] = self.domain
        if (
            "compound_required_spans" in self._explicit_fields
            or len(self.compound_required_spans) > 0
        ):
            d["compound_required_spans"] = list(self.compound_required_spans)
        if (
            "compound_missing_premises" in self._explicit_fields
            or len(self.compound_missing_premises) > 0
        ):
            d["compound_missing_premises"] = list(self.compound_missing_premises)
        if (
            "ambiguity_type" in self._explicit_fields
            or self.ambiguity_type is not None
        ):
            d["ambiguity_type"] = self.ambiguity_type
        if (
            "ambiguity_note" in self._explicit_fields
            or self.ambiguity_note is not None
        ):
            d["ambiguity_note"] = self.ambiguity_note
        if (
            "conflict_doc_ids" in self._explicit_fields
            or len(self.conflict_doc_ids) > 0
        ):
            d["conflict_doc_ids"] = list(self.conflict_doc_ids)
        if (
            "conflict_resolution_rule" in self._explicit_fields
            or self.conflict_resolution_rule is not None
        ):
            d["conflict_resolution_rule"] = self.conflict_resolution_rule
        if (
            "expected_safe_behavior" in self._explicit_fields
            or self.expected_safe_behavior is not None
        ):
            d["expected_safe_behavior"] = self.expected_safe_behavior
        return d

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

        extended_fields = {
            "split",
            "domain",
            "compound_required_spans",
            "compound_missing_premises",
            "ambiguity_type",
            "ambiguity_note",
            "conflict_doc_ids",
            "conflict_resolution_rule",
            "expected_safe_behavior",
        }
        explicit = tuple(k for k in extended_fields if k in data)

        def _parse_str_tuple(key: str) -> tuple[str, ...]:
            if key not in data:
                return ()
            val = data[key]
            if not isinstance(val, (list, tuple)):
                raise ValidationError(
                    f"Question '{key}' must be a list, got {type(val).__name__}"
                )
            return tuple(val)

        return cls(
            id=data["id"],
            question=data["question"],
            is_answerable=data["is_answerable"],
            question_type=data["question_type"],
            expected_answer=data.get("expected_answer"),
            absence_note=data.get("absence_note"),
            unanswerable_category=data.get("unanswerable_category"),
            evidence_spans=parsed_spans,
            split=data.get("split", "dev"),
            domain=data.get("domain", "general"),
            compound_required_spans=_parse_str_tuple("compound_required_spans"),
            compound_missing_premises=_parse_str_tuple("compound_missing_premises"),
            ambiguity_type=data.get("ambiguity_type"),
            ambiguity_note=data.get("ambiguity_note"),
            conflict_doc_ids=_parse_str_tuple("conflict_doc_ids"),
            conflict_resolution_rule=data.get("conflict_resolution_rule"),
            expected_safe_behavior=data.get("expected_safe_behavior"),
            _explicit_fields=explicit,
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

    doc_ids = set(seen_ids)
    superseded_map: dict[str, str] = {}
    for doc in documents:
        if doc.superseded_by is not None:
            if doc.superseded_by == doc.id:
                raise ValidationError(
                    f"Document '{doc.id}' cannot be superseded by itself"
                )
            if doc.superseded_by not in doc_ids:
                raise ValidationError(
                    f"Document '{doc.id}' superseded_by references unknown document "
                    f"ID '{doc.superseded_by}'"
                )
            superseded_map[doc.id] = doc.superseded_by

    # Detect cycles in superseded_by relationships
    for start_id in superseded_map:
        visited: list[str] = [start_id]
        curr = superseded_map[start_id]
        while curr is not None:
            if curr in visited:
                cycle_str = " -> ".join(visited + [curr])
                raise ValidationError(
                    f"Cycle detected in document supersession chain: {cycle_str}"
                )
            visited.append(curr)
            curr = superseded_map.get(curr)


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
            for c_doc_id in q.conflict_doc_ids:
                if c_doc_id not in documents_by_id:
                    raise ValidationError(
                        f"Question '{q.id}' conflict_doc_ids references unknown "
                        f"document ID '{c_doc_id}'"
                    )

            targets_adversarial = False
            for span in q.evidence_spans:
                if span.doc_id not in documents_by_id:
                    raise ValidationError(
                        f"Question '{q.id}' references unknown "
                        f"document ID '{span.doc_id}'"
                    )
                doc = documents_by_id[span.doc_id]
                if doc.contains_injection:
                    targets_adversarial = True
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

            if targets_adversarial:
                if (
                    not isinstance(q.expected_safe_behavior, str)
                    or not q.expected_safe_behavior.strip()
                ):
                    raise ValidationError(
                        f"Question '{q.id}' targets adversarial document with "
                        "contains_injection=True and must specify non-empty "
                        "'expected_safe_behavior'"
                    )
