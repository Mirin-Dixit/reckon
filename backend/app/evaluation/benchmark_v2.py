"""Offline candidate-only Python benchmark v2; not a runtime dataset adapter."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from app.evaluation.benchmark_review import (
    Category,
    Digest,
    Identifier,
    ReviewItem,
    SourceRecord,
    Split,
    StrictRecord,
    acceptance_issues,
    canonical_digest,
    validate_source_isolation,
    validate_source_snapshot,
)
from app.ingestion.loader import load_documents_from_jsonl
from app.ingestion.schema import EvidenceSpan

VERSION = "python311-3.11.9-candidates.1"


class ExactSpan(StrictRecord):
    id: Identifier
    doc_id: Identifier
    start_char: Annotated[int, Field(ge=0)]
    end_char: Annotated[int, Field(gt=0)]
    text: Annotated[str, Field(min_length=1)]

    @model_validator(mode="after")
    def exact_coordinates(self) -> Self:
        EvidenceSpan(self.doc_id, self.start_char, self.end_char, self.text, self.id)
        if self.end_char - self.start_char != len(self.text):
            raise ValueError("Span length differs from Unicode coordinates")
        return self


class CandidateRecord(StrictRecord):
    schema_version: Literal["ragbench.question.v2"]
    dataset_version: Literal["python311-3.11.9-candidates.1"]
    status: Literal["candidate"]
    verification_status: Literal["machine_checked_human_pending"]
    id: Identifier
    question: Annotated[str, Field(min_length=1, max_length=8000)]
    split: Split
    cluster_id: Identifier
    source_document_ids: list[Identifier]
    near_miss_parent_ids: list[Identifier]
    is_answerable: bool
    category: Category
    expected_decision: Literal["ANSWER", "ABSTAIN", "CLARIFY"]
    question_type: Literal["factoid", "procedural", "compound", "ambiguous"]
    is_compound: bool
    ambiguity_type: Literal["qualified_answer", "clarification_required"] | None
    ambiguity_interpretations: list[str]
    expected_answer: str | None
    expected_safe_behavior: Annotated[str, Field(min_length=1)]
    absence_note: str | None
    evidence_spans: list[ExactSpan]
    diagnostic_spans: list[ExactSpan]
    compound_required_spans: list[Identifier]
    compound_missing_premises: list[str]
    notes: Annotated[str, Field(min_length=1)]
    author_id: Literal["codex"]
    candidate_revision: Annotated[int, Field(ge=1)]
    corpus_sha256: Digest

    @model_validator(mode="after")
    def annotation_rules(self) -> Self:
        if not self.question.strip() or not self.expected_safe_behavior.strip():
            raise ValueError("Question and safe behavior must be nonblank")
        if self.is_answerable != (self.expected_decision == "ANSWER"):
            raise ValueError("Answerability/expected decision mismatch")
        if self.is_compound != (self.question_type == "compound"):
            raise ValueError("Compound tag/type mismatch")
        if not self.source_document_ids:
            raise ValueError("Explicit source/topic ownership is required")
        for values in (
            self.source_document_ids,
            self.near_miss_parent_ids,
            self.compound_required_spans,
        ):
            if len(values) != len(set(values)):
                raise ValueError("Duplicate references")
        spans = [*self.evidence_spans, *self.diagnostic_spans]
        if len({s.id for s in spans}) != len(spans):
            raise ValueError("Duplicate spans within candidate")
        if self.is_answerable:
            if not self.expected_answer or not self.expected_answer.strip():
                raise ValueError("Answerable reference answer required")
            if not self.evidence_spans or self.absence_note is not None:
                raise ValueError("Answerable evidence/absence mismatch")
            if self.compound_missing_premises:
                raise ValueError("Answerable candidate cannot have missing premises")
        elif self.expected_answer is not None or self.evidence_spans:
            raise ValueError("Negative candidate cannot pretend to have gold answers")
        elif not self.absence_note or not self.absence_note.strip():
            raise ValueError("Negative/clarification rationale required")
        if self.is_compound and self.is_answerable:
            if len(self.evidence_spans) < 2 or set(self.compound_required_spans) != {
                s.id for s in self.evidence_spans
            }:
                raise ValueError("Compound required spans must match exact evidence")
        elif self.compound_required_spans:
            raise ValueError("Unexpected compound span requirements")
        if self.ambiguity_type and len(self.ambiguity_interpretations) < 2:
            raise ValueError("Ambiguity needs two supported interpretations")
        if not self.ambiguity_type and self.ambiguity_interpretations:
            raise ValueError("Unexpected ambiguity interpretations")
        if self.ambiguity_type:
            if len(set(self.ambiguity_interpretations)) < 2 or any(
                not value.strip() for value in self.ambiguity_interpretations
            ):
                raise ValueError("Ambiguity interpretations must be distinct/nonblank")
            relevant = (
                self.evidence_spans if self.is_answerable else self.diagnostic_spans
            )
            if len(relevant) < 2:
                raise ValueError("Ambiguity requires evidence for both interpretations")
        if self.category == "ambiguous_question" and self.question_type != "ambiguous":
            raise ValueError("Clarification requires ambiguous question type")
        if self.category in {
            "temporal_near_miss",
            "entity_near_miss",
            "attribute_near_miss",
            "false_premise",
        }:
            if not self.near_miss_parent_ids:
                raise ValueError("Near-miss/unsupported premise requires an anchor")
        # Reuse the review contract's category/decision/ambiguity rules.
        ReviewItem(
            schema_version="ragbench.review.v2",
            candidate_id=self.id,
            candidate_sha256=canonical_digest(self.model_dump(mode="json")),
            corpus_sha256=self.corpus_sha256,
            author_id=self.author_id,
            category=self.category,
            expected_decision=self.expected_decision,
            is_compound=self.is_compound,
            ambiguity_type=self.ambiguity_type,
            reviews=[],
            adjudication=None,
        )
        return self


def _records(path: Path) -> list[str]:
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Offline dataset file exceeds 16 MiB bound")
    with path.open(encoding="utf-8") as stream:
        return [line for line in stream if line.strip()]


def load_v2_candidates(root: Path) -> list[CandidateRecord]:
    """Evaluator/curation-only gold loader. Never use for query initialization."""
    records = []
    for split in ("train", "dev", "test"):
        for line in _records(root / "candidates" / f"{split}.jsonl"):
            candidate = CandidateRecord.model_validate_json(line)
            if candidate.split != split:
                raise ValueError("Candidate split differs from its file")
            records.append(candidate)
    return records


def second_review_sample(candidates: list[CandidateRecord]) -> list[str]:
    """Deterministic 20% ordinary-answer sample; other hard cases already need two."""
    ordinary = [
        q.id
        for q in candidates
        if q.is_answerable and not q.is_compound and q.ambiguity_type is None
    ]
    ordered = sorted(
        ordinary,
        key=lambda value: hashlib.sha256(
            ("py311-v2-review-1:" + value).encode("utf-8")
        ).hexdigest(),
    )
    return ordered[: (len(ordered) + 4) // 5]


def validate_artifact_integrity(root: Path, manifest: dict) -> None:
    """Detect accidental release drift; unsigned hashes do not authenticate authors."""
    integrity = json.loads((root / "integrity.json").read_text(encoding="utf-8"))
    expected = {
        "documents.jsonl",
        "sources_manifest.json",
        "review_ledger.jsonl",
        "review_plan.json",
        "candidates/train.jsonl",
        "candidates/dev.jsonl",
        "candidates/test.jsonl",
    }
    expected.update(
        "sources/" + Path(s["snapshot_path"]).name for s in manifest["sources"]
    )
    expected.update("sources/" + name for name in manifest["license_files"])
    if (
        integrity.get("schema_version") != "ragbench.integrity.v2"
        or set(integrity.get("files", {})) != expected
    ):
        raise ValueError("Integrity inventory mismatch")
    for relative, digest in integrity["files"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Unsafe artifact path")
        if (
            path.stat().st_size > 16 * 1024 * 1024
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("Artifact integrity mismatch: " + relative)


def validate_v2_dataset(root: Path, *, require_human_acceptance: bool = False) -> dict:
    """Validate candidate structure/provenance, without claiming semantic review."""
    manifest = json.loads((root / "sources_manifest.json").read_text(encoding="utf-8"))
    if (
        manifest["schema_version"] != "ragbench.dataset.v2"
        or manifest["dataset_version"] != VERSION
        or manifest["release_status"] != "candidate_unreviewed"
    ):
        raise ValueError("Unexpected candidate manifest version/status")
    validate_artifact_integrity(root, manifest)
    sources = [
        SourceRecord.model_validate_json(json.dumps(s)) for s in manifest["sources"]
    ]
    links = [tuple(link) for link in manifest["overlap_links"]]
    validate_source_isolation(sources, links)
    documents = load_documents_from_jsonl(root / "documents.jsonl")
    by_doc = {doc.id: doc for doc in documents}
    if set(by_doc) != {s.document_id for s in sources}:
        raise ValueError("Source manifest/document inventory mismatch")
    for source in sources:
        if source.snapshot_revision != manifest["source_revision"]:
            raise ValueError("Mixed source commits")
        raw = (root / "sources" / Path(source.snapshot_path).name).read_bytes()
        validate_source_snapshot(source, raw, by_doc[source.document_id])
    for name, digest in manifest["license_files"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe license path")
        if hashlib.sha256((root / "sources" / name).read_bytes()).hexdigest() != digest:
            raise ValueError("License snapshot mismatch")
    candidates = load_v2_candidates(root)
    review_plan = json.loads((root / "review_plan.json").read_text(encoding="utf-8"))
    if review_plan.get(
        "schema_version"
    ) != "ragbench.review-plan.v2" or review_plan.get(
        "ordinary_second_review_ids"
    ) != second_review_sample(candidates):
        raise ValueError("Second-review sample differs from deterministic plan")
    by_id = {q.id: q for q in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("Duplicate candidate IDs")
    normalized = [
        re.sub(r"\W+", " ", q.question.casefold()).strip() for q in candidates
    ]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Duplicate normalized candidate questions")
    corpus_digest = canonical_digest(manifest)
    source_map = {s.document_id: s for s in sources}
    for q in candidates:
        if q.corpus_sha256 != corpus_digest:
            raise ValueError("Candidate bound to a stale corpus")
        for doc_id in q.source_document_ids:
            source = source_map.get(doc_id)
            if not source or (source.split, source.cluster_id) != (
                q.split,
                q.cluster_id,
            ):
                raise ValueError("Cross-split/topic candidate ownership")
        for span in [*q.evidence_spans, *q.diagnostic_spans]:
            if span.doc_id not in q.source_document_ids:
                raise ValueError("Span outside declared candidate source ownership")
            if by_doc[span.doc_id].text[span.start_char : span.end_char] != span.text:
                raise ValueError("Evidence text does not match captured source offsets")
        for parent in q.near_miss_parent_ids:
            anchor = by_id.get(parent)
            if (
                not anchor
                or not anchor.is_answerable
                or (anchor.split, anchor.cluster_id) != (q.split, q.cluster_id)
            ):
                raise ValueError("Invalid/cross-split near-miss parent")
    ledger = [
        ReviewItem.model_validate_json(line)
        for line in _records(root / "review_ledger.jsonl")
    ]
    if len(ledger) != len(candidates) or {r.candidate_id for r in ledger} != set(by_id):
        raise ValueError("Review ledger inventory mismatch")
    eligible = 0
    for review in ledger:
        candidate = by_id[review.candidate_id].model_dump(mode="json")
        if (
            review.candidate_sha256 != canonical_digest(candidate)
            or review.corpus_sha256 != corpus_digest
            or any(
                candidate[key] != getattr(review, field)
                for field, key in (
                    ("author_id", "author_id"),
                    ("category", "category"),
                    ("expected_decision", "expected_decision"),
                    ("is_compound", "is_compound"),
                    ("ambiguity_type", "ambiguity_type"),
                )
            )
        ):
            raise ValueError("Review ledger is not bound to the current candidate")
        blockers = acceptance_issues(
            review,
            candidate=candidate,
            corpus_sha256=corpus_digest,
        )
        eligible += not blockers
    if require_human_acceptance and eligible != len(candidates):
        raise ValueError("Human verification incomplete; dataset cannot be frozen")
    if require_human_acceptance:
        sampled = set(second_review_sample(candidates))
        if any(r.candidate_id in sampled and len(r.reviews) < 2 for r in ledger):
            raise ValueError("Independent second-review sample incomplete")
    counts = Counter(q.split for q in candidates)
    if counts != {"train": 96, "dev": 24, "test": 40}:
        raise ValueError("Candidate split target mismatch")
    if sum(q.is_answerable for q in candidates) != 96:
        raise ValueError("Candidate answerability target mismatch")
    return {
        "documents": len(documents),
        "candidates": len(candidates),
        "splits": dict(counts),
        "categories": dict(Counter(q.category for q in candidates)),
        "human_review_eligible": eligible,
        "corpus_sha256": corpus_digest,
        "status": "candidate_unreviewed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--require-human-acceptance", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            validate_v2_dataset(
                args.root,
                require_human_acceptance=args.require_human_acceptance,
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
