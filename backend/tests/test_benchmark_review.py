"""Offline review-gate fixtures, never production benchmark questions."""

import ast
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.evaluation.benchmark_review import (
    HumanDecision,
    ReviewItem,
    SourceRecord,
    acceptance_issues,
    canonical_digest,
    validate_source_isolation,
    validate_source_snapshot,
)
from app.ingestion.schema import Document
from pydantic import ValidationError

NOW = datetime(2026, 11, 3, tzinfo=UTC)
BASE_CANDIDATE = {
    "id": "fixture-only",
    "author_id": "candidate-author",
    "category": "attribute_near_miss",
    "expected_decision": "ABSTAIN",
    "is_compound": False,
    "ambiguity_type": None,
    "question": "Offline fixture, not a benchmark question",
}
CANDIDATE = canonical_digest(BASE_CANDIDATE)
CORPUS = canonical_digest({"fixture": "test corpus revision"})
CHECKS = ["source", "split", "answerability", "evidence", "negative_absence"]
RAW = "A😀e\u0301\r\n".encode()
TEXT = "A😀e\u0301\n"


def source(**updates):
    return SourceRecord.model_validate(
        {
            "schema_version": "ragbench.source.v2",
            "source_id": "source-a",
            "document_id": "doc-a",
            "cluster_id": "cluster-a",
            "split": "train",
            "source_url": "https://docs.python.org/3.11/library/functools.html",
            "python_version": "3.11.18",
            "snapshot_revision": "a" * 40,
            "snapshot_path": "Doc/library/functools.rst",
            "retrieved_at_utc": NOW,
            "raw_sha256": hashlib.sha256(RAW).hexdigest(),
            "text_sha256": hashlib.sha256(TEXT.encode()).hexdigest(),
            "extraction_version": "rst-identity-lf-v1",
            "license_id": "PSF-2.0",
            "code_license": "PSF-2.0 OR 0BSD",
            "copyright_notice": "PSF notice",
            **updates,
        }
    )


def review(reviewer="reviewer-a", **updates):
    return {
        "reviewer_id": reviewer,
        "actor_kind": "human",
        "candidate_sha256": CANDIDATE,
        "corpus_sha256": CORPUS,
        "reviewed_at_utc": NOW,
        "verdict": "accept",
        "checks": CHECKS,
        "rationale": "Source and full corpus checked independently.",
        "independent_first_pass": True,
        **updates,
    }


def item(**updates):
    current = {
        **BASE_CANDIDATE,
        **{k: v for k, v in updates.items() if k in BASE_CANDIDATE},
    }
    digest = canonical_digest(current)
    updates.setdefault("candidate_sha256", digest)
    if "reviews" in updates:
        updates["reviews"] = [
            {**r, "candidate_sha256": digest}
            if r["candidate_sha256"] == CANDIDATE
            else r
            for r in updates["reviews"]
        ]
    return ReviewItem.model_validate(
        {
            "schema_version": "ragbench.review.v2",
            "candidate_id": "fixture-only",
            "candidate_sha256": CANDIDATE,
            "corpus_sha256": CORPUS,
            "author_id": "candidate-author",
            "category": "attribute_near_miss",
            "expected_decision": "ABSTAIN",
            "is_compound": False,
            "ambiguity_type": None,
            "reviews": [
                review(candidate_sha256=digest),
                review("reviewer-b", candidate_sha256=digest),
            ],
            "adjudication": None,
            **updates,
        }
    )


def issues(record):
    candidate = {
        **BASE_CANDIDATE,
        **{
            key: getattr(record, key)
            for key in [
                "author_id",
                "category",
                "expected_decision",
                "is_compound",
                "ambiguity_type",
            ]
        },
    }
    return acceptance_issues(record, candidate=candidate, corpus_sha256=CORPUS)


def test_source_hashes_bind_raw_and_exact_unicode_document_text():
    document = Document(
        "doc-a", "Fixture", source().source_url, TEXT, version="3.11.18"
    )
    validate_source_snapshot(source(), RAW, document)
    for raw, doc in [
        (b"changed", document),
        (
            RAW,
            Document(
                "doc-a",
                "Fixture",
                source().source_url,
                "A😀é",
                version="3.11.18",
            ),
        ),
    ]:
        with pytest.raises(ValueError, match="hash mismatch"):
            validate_source_snapshot(source(), raw, doc)


@pytest.mark.parametrize(
    "changes",
    [
        {"source_url": "https://docs.python.org/3.12/library/functools.html"},
        {"source_url": "https://user:pass@docs.python.org/3.11/library/a.html"},
        {"source_url": "https://docs.python.org/3.11/library/a.html?token=x"},
        {"source_url": "http://docs.python.org/3.11/library/a.html"},
        {"python_version": "3.11"},
        {"snapshot_revision": "main"},
        {"raw_sha256": "placeholder"},
        {"retrieved_at_utc": datetime(2026, 11, 3)},
        {"extra_gold": "forbidden"},
        {"copyright_notice": " "},
        {"snapshot_path": "../../private.rst"},
        {"source_url": "https://docs.python.org/3.11/library/../../3.12/x.html"},
    ],
)
def test_invalid_provenance_is_rejected(changes):
    with pytest.raises(ValidationError):
        source(**changes)


def test_source_json_roundtrip_and_document_binding():
    original = source()
    assert SourceRecord.model_validate_json(original.model_dump_json()) == original
    with pytest.raises(ValueError, match="provenance mismatch"):
        validate_source_snapshot(
            original,
            RAW,
            Document(
                "wrong-id",
                "Fixture",
                original.source_url,
                TEXT,
                version="3.11.18",
            ),
        )


def second_source(**updates):
    return source(
        source_id="source-b",
        document_id="doc-b",
        cluster_id="cluster-b",
        source_url="https://docs.python.org/3.11/library/decimal.html",
        raw_sha256="b" * 64,
        text_sha256="c" * 64,
        **updates,
    )


def test_isolation_accepts_distinct_sources_and_same_split_overlap():
    validate_source_isolation([source(), second_source()], [("doc-a", "doc-b")])
    validate_source_isolation([source(), second_source(split="test")], [])


@pytest.mark.parametrize(
    "field", ["cluster_id", "source_url", "text_sha256", "raw_sha256"]
)
def test_shared_source_identity_or_content_cannot_cross_splits(field):
    data = second_source(split="test").model_dump()
    data[field] = getattr(source(), field)
    with pytest.raises(ValueError, match="Cross-split"):
        validate_source_isolation([source(), SourceRecord.model_validate(data)], [])


@pytest.mark.parametrize("links", [[("doc-a", "doc-b")], [("doc-a", "unknown")]])
def test_overlap_graph_rejects_cross_split_and_unknown_links(links):
    with pytest.raises(ValueError):
        validate_source_isolation([source(), second_source(split="test")], links)


def test_duplicate_source_and_document_ids_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_source_isolation([source(), source()], [])


def test_negative_requires_two_distinct_non_author_human_reviews():
    assert issues(item()) == ()
    for reviews in [
        [],
        [review()],
        [review(), review()],
        [review(), review("candidate-author")],
    ]:
        assert issues(item(reviews=reviews))


@pytest.mark.parametrize(
    "changes",
    [
        {"actor_kind": "model"},
        {"independent_first_pass": False},
        {"independent_first_pass": 1},
        {"rationale": " "},
        {"reviewed_at_utc": NOW.replace(tzinfo=None)},
        {"checks": ["made_up"]},
        {"accepted": True},
    ],
)
def test_unverifiable_or_malformed_review_declarations_rejected(changes):
    with pytest.raises(ValidationError):
        HumanDecision.model_validate(review(**changes))


def test_stale_candidate_corpus_review_and_incomplete_checks_block_acceptance():
    assert "stale candidate or corpus" in issues(item(candidate_sha256="f" * 64))
    assert "stale review" in issues(
        item(reviews=[review(corpus_sha256="f" * 64), review("reviewer-b")])
    )
    assert "incomplete review checklist" in issues(
        item(
            reviews=[review(checks=[]), review("reviewer-b")],
        )
    )


def test_disagreement_requires_third_human_adjudication_bound_to_review_set():
    reviews = [review(), review("reviewer-b", verdict="reject")]
    assert issues(item(reviews=reviews))
    adjudication = review("adjudicator")
    adjudication.pop("independent_first_pass")
    adjudication["review_set_sha256"] = canonical_digest(
        [HumanDecision.model_validate(r).model_dump(mode="json") for r in reviews]
    )
    assert issues(item(reviews=reviews, adjudication=adjudication)) == ()
    for change in [
        {"review_set_sha256": "0" * 64},
        {"reviewer_id": "reviewer-a"},
        {"verdict": "reject"},
    ]:
        assert issues(item(reviews=reviews, adjudication={**adjudication, **change}))


def test_qualified_and_compound_answers_require_dual_review_and_extra_checks():
    base = {
        "category": "answerable",
        "expected_decision": "ANSWER",
        "reviews": [review(checks=[*CHECKS, "reference_answer"])],
    }
    assert issues(item(**base)) == ()
    for changes in [{"is_compound": True}, {"ambiguity_type": "qualified_answer"}]:
        assert issues(item(**{**base, **changes}))
    checks = [*CHECKS, "reference_answer", "compound", "ambiguity"]
    assert (
        issues(
            item(
                **{
                    **base,
                    "is_compound": True,
                    "ambiguity_type": "qualified_answer",
                    "reviews": [
                        review(checks=checks),
                        review("reviewer-b", checks=checks),
                    ],
                }
            )
        )
        == ()
    )


def test_clarification_and_false_premise_are_explicit_not_silently_mapped():
    assert issues(item(category="false_premise")) == ()
    record = item(
        category="ambiguous_question",
        expected_decision="CLARIFY",
        ambiguity_type="clarification_required",
        reviews=[
            review(checks=[*CHECKS, "ambiguity"]),
            review("reviewer-b", checks=[*CHECKS, "ambiguity"]),
        ],
    )
    assert issues(record) == ()
    with pytest.raises(ValidationError):
        item(category="false_premise", expected_decision="ANSWER")
    with pytest.raises(ValidationError):
        item(category="ambiguous_question")


def test_fingerprints_are_canonical_and_invalidate_unicode_or_label_edits():
    assert canonical_digest({"a": 1, "b": 2}) == canonical_digest({"b": 2, "a": 1})
    assert canonical_digest({"text": "e\u0301"}) != canonical_digest({"text": "é"})
    with pytest.raises(ValueError):
        canonical_digest({"score": float("nan")})
    original = item()
    assert ReviewItem.model_validate_json(original.model_dump_json()) == original


def test_rehashed_fabricated_extraction_is_rejected():
    fabricated = "Unrelated text"
    declared = source(text_sha256=hashlib.sha256(fabricated.encode()).hexdigest())
    with pytest.raises(ValueError, match="declared extraction"):
        validate_source_snapshot(
            declared,
            RAW,
            Document(
                "doc-a",
                "Fixture",
                declared.source_url,
                fabricated,
                version="3.11.18",
            ),
        )


def test_review_module_is_not_imported_by_runtime_or_evaluation_runner():
    paths = [
        path
        for folder in ["api", "generation", "retrieval"]
        for path in (Path("backend/app") / folder).rglob("*.py")
    ]
    paths.append(Path("backend/app/evaluation/runner.py"))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert "benchmark_review" not in (node.module or ""), path
                assert all(a.name != "benchmark_review" for a in node.names), path
            elif isinstance(node, ast.Import):
                assert all("benchmark_review" not in a.name for a in node.names), path


def test_review_metadata_cannot_be_changed_to_bypass_author_or_dual_review_rules():
    original = item()
    altered = original.model_copy(update={"author_id": "different-author"})
    assert "review metadata differs from current candidate" in acceptance_issues(
        altered,
        candidate=BASE_CANDIDATE,
        corpus_sha256=CORPUS,
    )
    changed = {**BASE_CANDIDATE, "question": "Changed annotation text"}
    assert "stale candidate or corpus" in acceptance_issues(
        original,
        candidate=changed,
        corpus_sha256=CORPUS,
    )
