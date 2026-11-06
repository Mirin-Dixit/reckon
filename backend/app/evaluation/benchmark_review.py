"""Offline v2 review gates. Never imported by query/retrieval/generation code.

Human identities and independent review are attestations, not authenticated proof.
This module neither loads questions nor exports accepted runtime datasets.
"""

import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ingestion.schema import Document

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(min_length=1, pattern=r"^\S+$")]
Split = Literal["train", "dev", "test"]
Category = Literal[
    "answerable",
    "off_topic",
    "temporal_near_miss",
    "entity_near_miss",
    "attribute_near_miss",
    "false_premise",
    "ambiguous_question",
]
Check = Literal[
    "source",
    "split",
    "answerability",
    "evidence",
    "reference_answer",
    "negative_absence",
    "ambiguity",
    "compound",
]


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class SourceRecord(StrictRecord):
    schema_version: Literal["ragbench.source.v2"]
    source_id: Identifier
    document_id: Identifier
    cluster_id: Identifier
    split: Split
    source_url: str
    python_version: Annotated[str, Field(pattern=r"^3\.11\.\d+$")]
    snapshot_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    snapshot_path: Annotated[str, Field(pattern=r"^Doc/library/[A-Za-z0-9_.-]+\.rst$")]
    retrieved_at_utc: datetime
    raw_sha256: Digest
    text_sha256: Digest
    extraction_version: Literal["rst-identity-lf-v1"]
    license_id: Literal["PSF-2.0"]
    code_license: Literal["PSF-2.0 OR 0BSD"]
    copyright_notice: Annotated[str, Field(min_length=1)]

    @field_validator("copyright_notice")
    @classmethod
    def nonblank_notice(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Copyright notice cannot be blank")
        return value

    @field_validator("source_url")
    @classmethod
    def official_url(cls, value: str) -> str:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or url.netloc != "docs.python.org"
            or not re.fullmatch(r"/3\.11/library/[A-Za-z0-9_.-]+\.html", url.path)
            or url.query
            or any(ord(char) < 32 for char in value)
        ):
            raise ValueError("Expected an official Python 3.11 library URL")
        return value

    @field_validator("retrieved_at_utc")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        if value.utcoffset() != timedelta(0):
            raise ValueError("Capture timestamp must be timezone-aware UTC")
        return value


def validate_source_snapshot(
    source: SourceRecord,
    raw: bytes,
    document: Document,
) -> None:
    """Check captured bytes and the exact text used for future span coordinates."""
    if (
        hashlib.sha256(raw).hexdigest() != source.raw_sha256
        or hashlib.sha256(document.text.encode("utf-8")).hexdigest()
        != source.text_sha256
    ):
        raise ValueError("Source snapshot hash mismatch")
    if raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n") != (document.text):
        raise ValueError("Document text does not match declared extraction")
    if (
        document.id != source.document_id
        or document.source_url != source.source_url
        or document.version != source.python_version
        or document.contains_injection
    ):
        raise ValueError("Source/document provenance mismatch")


def validate_source_isolation(
    sources: list[SourceRecord],
    overlap_links: list[tuple[str, str]],
) -> None:
    """Reject known shared topics/pages/content or linked evidence across splits.

    Overlap detection itself requires human review; this checks the declared graph.
    """
    by_doc = {source.document_id: source for source in sources}
    if len(by_doc) != len(sources) or len({s.source_id for s in sources}) != len(
        sources
    ):
        raise ValueError("Duplicate source or document identity")
    owners: dict[tuple[str, str], str] = {}
    for source in sources:
        keys = [
            ("cluster", source.cluster_id),
            ("page", source.source_url.split("#")[0]),
            ("text", source.text_sha256),
            ("raw", source.raw_sha256),
        ]
        for key in keys:
            if key in owners and owners[key] != source.split:
                raise ValueError("Cross-split source/topic/content overlap")
            owners[key] = source.split
    for left, right in overlap_links:
        if left not in by_doc or right not in by_doc:
            raise ValueError("Overlap link references an unknown document")
        if by_doc[left].split != by_doc[right].split:
            raise ValueError("Cross-split evidence/near-miss link")


def canonical_digest(payload: object) -> str:
    """Hash complete JSON annotations/review sets without newline/whitespace drift."""
    data = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class HumanAttestation(StrictRecord):
    reviewer_id: Identifier
    actor_kind: Literal["human"]
    candidate_sha256: Digest
    corpus_sha256: Digest
    reviewed_at_utc: datetime
    verdict: Literal["accept", "revise", "reject"]
    checks: list[Check]
    rationale: Annotated[str, Field(min_length=1)]

    _utc = field_validator("reviewed_at_utc")(SourceRecord.utc.__func__)

    @field_validator("rationale")
    @classmethod
    def meaningful(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Review rationale cannot be blank")
        return value


class HumanDecision(HumanAttestation):
    independent_first_pass: Literal[True]

    @field_validator("independent_first_pass", mode="before")
    @classmethod
    def explicit_boolean(cls, value: object) -> object:
        if type(value) is not bool:
            raise ValueError("Independent review requires an explicit boolean")
        return value


class Adjudication(HumanAttestation):
    review_set_sha256: Digest


class ReviewItem(StrictRecord):
    schema_version: Literal["ragbench.review.v2"]
    candidate_id: Identifier
    candidate_sha256: Digest
    corpus_sha256: Digest
    author_id: Identifier
    category: Category
    expected_decision: Literal["ANSWER", "ABSTAIN", "CLARIFY"]
    is_compound: bool
    ambiguity_type: Literal["qualified_answer", "clarification_required"] | None
    reviews: list[HumanDecision]
    adjudication: Adjudication | None

    @model_validator(mode="after")
    def consistent_label(self) -> Self:
        expected = (
            "ANSWER"
            if self.category == "answerable"
            else "CLARIFY"
            if self.category == "ambiguous_question"
            else "ABSTAIN"
        )
        if self.expected_decision != expected:
            raise ValueError("Category/expected decision mismatch")
        if (self.category == "ambiguous_question") != (
            self.ambiguity_type == "clarification_required"
        ):
            raise ValueError("Clarification requires explicit ambiguity annotation")
        if self.ambiguity_type == "qualified_answer" and expected != "ANSWER":
            raise ValueError("Qualified answers must remain answerable")
        return self


def acceptance_issues(
    item: ReviewItem,
    *,
    candidate: dict[str, object],
    corpus_sha256: str,
) -> tuple[str, ...]:
    """Return deterministic blockers, not a machine-generated human acceptance.

    Hash complete candidate content and bind review metadata to that content.
    The caller supplies the independently computed captured corpus manifest hash.
    """
    issues = []
    candidate_sha256 = canonical_digest(candidate)
    for field, key in [
        ("candidate_id", "id"),
        ("author_id", "author_id"),
        ("category", "category"),
        ("expected_decision", "expected_decision"),
        ("is_compound", "is_compound"),
        ("ambiguity_type", "ambiguity_type"),
    ]:
        if key not in candidate or candidate[key] != getattr(item, field):
            issues.append("review metadata differs from current candidate")
    if item.candidate_sha256 != candidate_sha256 or item.corpus_sha256 != corpus_sha256:
        issues.append("stale candidate or corpus")
    required = {"source", "split", "answerability", "evidence"}
    required.add(
        "reference_answer"
        if item.expected_decision == "ANSWER"
        else "negative_absence"
        if item.expected_decision == "ABSTAIN"
        else "ambiguity"
    )
    if item.ambiguity_type:
        required.add("ambiguity")
    if item.is_compound:
        required.add("compound")
    minimum = (
        2
        if (item.category != "answerable" or item.is_compound or item.ambiguity_type)
        else 1
    )
    reviewers = [review.reviewer_id for review in item.reviews]
    if len(set(reviewers)) < minimum:
        issues.append("insufficient independent human reviews")
    if len(set(reviewers)) != len(reviewers) or item.author_id in reviewers:
        issues.append("duplicate reviewer or author self-review")
    for review in [*item.reviews, *([item.adjudication] if item.adjudication else [])]:
        if (
            review.candidate_sha256 != candidate_sha256
            or review.corpus_sha256 != corpus_sha256
        ):
            issues.append("stale review")
        if not required <= set(review.checks):
            issues.append("incomplete review checklist")
    adjudication = item.adjudication
    if adjudication:
        if adjudication.reviewer_id in [item.author_id, *reviewers]:
            issues.append("adjudicator is not independent")
        if adjudication.review_set_sha256 != canonical_digest(
            [r.model_dump(mode="json") for r in item.reviews]
        ):
            issues.append("stale adjudication review set")
        if adjudication.verdict != "accept":
            issues.append("adjudication did not accept")
    elif any(review.verdict != "accept" for review in item.reviews):
        issues.append("non-accepting review requires adjudication or revision")
    return tuple(issues)
