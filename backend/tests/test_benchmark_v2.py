"""Candidate structure checks only: no Test inference or human-review simulation."""

import ast
import hashlib
import itertools
import json
import re
import shutil
from collections import Counter
from pathlib import Path

import pytest
from app.evaluation.benchmark_review import ReviewItem, canonical_digest
from app.evaluation.benchmark_v2 import (
    CandidateRecord,
    ExactSpan,
    load_v2_candidates,
    second_review_sample,
    validate_v2_dataset,
)
from app.ingestion.loader import load_dataset, load_documents_from_jsonl
from pydantic import ValidationError

ROOT = Path("data/benchmark_v2/python311_3_11_9")


@pytest.fixture
def candidate():
    return load_v2_candidates(ROOT)[0].model_dump(mode="json")


def test_complete_candidate_inventory_and_unreviewed_gate():
    result = validate_v2_dataset(ROOT)
    assert result["documents"] == 34
    assert result["candidates"] == 160
    assert result["splits"] == {"train": 96, "dev": 24, "test": 40}
    assert result["categories"] == {
        "answerable": 96,
        "off_topic": 8,
        "temporal_near_miss": 16,
        "entity_near_miss": 12,
        "attribute_near_miss": 12,
        "false_premise": 8,
        "ambiguous_question": 8,
    }
    assert result["human_review_eligible"] == 0
    with pytest.raises(ValueError, match="Human verification incomplete"):
        validate_v2_dataset(ROOT, require_human_acceptance=True)


@pytest.mark.parametrize(
    "split,answers,negatives",
    [
        ("train", 58, 38),
        ("dev", 14, 10),
        ("test", 24, 16),
    ],
)
def test_split_answerability_counts(split, answers, negatives):
    counts = Counter(
        q.is_answerable for q in load_v2_candidates(ROOT) if q.split == split
    )
    assert counts == {True: answers, False: negatives}


@pytest.mark.parametrize(
    "update",
    [
        {"schema_version": "ragbench.question.v1"},
        {"dataset_version": "python311-latest"},
        {"status": "accepted"},
        {"verification_status": "human_verified"},
        {"author_id": "human"},
        {"split": "validation"},
        {"is_answerable": 1},
        {"category": "invented"},
        {"category": "false_premise"},
        {"expected_decision": "ABSTAIN"},
        {"expected_answer": None},
        {"question": " "},
        {"evidence_spans": []},
        {"source_document_ids": []},
        {"near_miss_parent_ids": ["a", "a"]},
        {"is_compound": True},
        {"question_type": "compound", "is_compound": True},
        {"ambiguity_type": "qualified_answer"},
        {"ambiguity_interpretations": ["unrequested", "alternatives"]},
        {"compound_required_spans": ["missing"]},
        {"compound_missing_premises": ["A required fact is missing"]},
        {"expected_safe_behavior": " "},
        {"corpus_sha256": "bad hash"},
        {"unrecognized_field": "must reject"},
    ],
)
def test_candidate_rejects_invalid_annotations(candidate, update):
    with pytest.raises(ValidationError):
        CandidateRecord.model_validate({**candidate, **update})


@pytest.mark.parametrize(
    "category",
    [
        "temporal_near_miss",
        "entity_near_miss",
        "attribute_near_miss",
        "false_premise",
    ],
)
def test_near_miss_requires_answerable_anchor(category):
    q = next(q for q in load_v2_candidates(ROOT) if q.category == category)
    with pytest.raises(ValidationError, match="requires an anchor"):
        CandidateRecord.model_validate({**q.model_dump(), "near_miss_parent_ids": []})


@pytest.mark.parametrize(
    "update",
    [
        {"id": "wrong"},
        {"start_char": True},
        {"end_char": 99},
        {"start_char": -1},
        {"text": ""},
    ],
)
def test_invalid_exact_coordinates(update):
    payload = dict(
        id="fixture_s1_4",
        doc_id="fixture",
        start_char=1,
        end_char=4,
        text="\U0001f600e\u0301",
    )
    with pytest.raises(ValueError):
        ExactSpan.model_validate({**payload, **update})


def test_unicode_codepoints_not_utf16_or_bytes():
    span = ExactSpan(
        id="fixture_s1_4",
        doc_id="fixture",
        start_char=1,
        end_char=4,
        text="\U0001f600e\u0301",
    )
    assert ("A\U0001f600e\u0301Z"[span.start_char : span.end_char]) == span.text
    assert ExactSpan.model_validate_json(span.model_dump_json()) == span


def test_all_offsets_and_review_bindings_are_exact():
    docs = {d.id: d for d in load_documents_from_jsonl(ROOT / "documents.jsonl")}
    candidates = {q.id: q for q in load_v2_candidates(ROOT)}
    for q in candidates.values():
        assert CandidateRecord.model_validate_json(q.model_dump_json()) == q
        for span in [*q.evidence_spans, *q.diagnostic_spans]:
            assert docs[span.doc_id].text[span.start_char : span.end_char] == span.text
    for line in (ROOT / "review_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        item = ReviewItem.model_validate_json(line)
        assert item.candidate_sha256 == canonical_digest(
            candidates[item.candidate_id].model_dump(mode="json")
        )
        assert item.reviews == [] and item.adjudication is None


def test_negatives_have_no_fabricated_gold_spans_and_clarification_is_explicit():
    for q in load_v2_candidates(ROOT):
        if not q.is_answerable:
            assert q.expected_answer is None and q.evidence_spans == []
            assert q.absence_note
        if q.expected_decision == "CLARIFY":
            assert "Ask which" in q.expected_safe_behavior
            assert q.ambiguity_type == "clarification_required"
            assert len(q.diagnostic_spans) >= 2


def test_related_parents_stay_in_the_same_split_and_cluster():
    qs = {q.id: q for q in load_v2_candidates(ROOT)}
    for q in qs.values():
        for parent in q.near_miss_parent_ids:
            assert qs[parent].is_answerable
            assert (qs[parent].split, qs[parent].cluster_id) == (q.split, q.cluster_id)


def test_temporal_pairs_change_only_the_requested_python_version():
    qs = {q.id: q for q in load_v2_candidates(ROOT)}
    for q in qs.values():
        if q.category == "temporal_near_miss":
            parent = qs[q.near_miss_parent_ids[0]]
            assert (
                q.question.replace("Python 3.13", "Python 3.11", 1) == parent.question
            )


def test_no_exact_twelve_token_evidence_overlap_across_splits():
    # A lexical alarm, not proof that semantic paraphrases are absent.
    qs = load_v2_candidates(ROOT)
    shingles = {}
    for q in qs:
        shingles[q.id] = set()
        for span in q.evidence_spans + q.diagnostic_spans:
            words = re.findall(r"\w+", span.text.casefold())
            shingles[q.id].update(
                tuple(words[i : i + 12]) for i in range(len(words) - 11)
            )
    for a, b in itertools.combinations(qs, 2):
        if a.split != b.split:
            assert not shingles[a.id] & shingles[b.id], (a.id, b.id)


def test_review_sample_is_reproducible_and_excludes_hard_cases():
    qs = load_v2_candidates(ROOT)
    ids = second_review_sample(qs)
    assert len(ids) == 18
    assert second_review_sample(list(reversed(qs))) == ids
    assert all(
        q.is_answerable and not q.is_compound and q.ambiguity_type is None
        for q in qs
        if q.id in ids
    )


@pytest.fixture
def copied(tmp_path):
    target = tmp_path / "dataset"
    shutil.copytree(ROOT, target)
    return target


@pytest.mark.parametrize(
    "relative",
    [
        "sources/collections.rst",
        "sources/LICENSE",
        "documents.jsonl",
        "candidates/train.jsonl",
        "review_ledger.jsonl",
        "review_plan.json",
    ],
)
def test_artifact_tampering_is_rejected(copied, relative):
    path = copied / relative
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Artifact integrity mismatch"):
        validate_v2_dataset(copied)


def test_wrong_split_file_is_rejected(copied):
    source = copied / "candidates/train.jsonl"
    lines = source.read_text(encoding="utf-8").splitlines()
    source.write_text(
        json.dumps({**json.loads(lines[0]), "split": "test"}) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="differs from its file"):
        load_v2_candidates(copied)


@pytest.mark.parametrize(
    "defect,error",
    [
        ("offset", "does not match captured"),
        ("parent", "Invalid/cross-split near-miss parent"),
        ("duplicate", "Duplicate normalized"),
        ("corpus", "stale corpus"),
        ("ownership", "Cross-split/topic"),
        ("ledger", "not bound to the current"),
    ],
)
def test_rehashed_content_still_requires_consistent_annotations(copied, defect, error):
    path = copied / "candidates/train.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if defect == "offset":
        # Keep the same length and valid ID; only comparison with source detects it.
        rows[0]["evidence_spans"][0]["text"] = (
            "X" + rows[0]["evidence_spans"][0]["text"][1:]
        )
    elif defect == "parent":
        rows[-1]["near_miss_parent_ids"] = ["py311v2_test_001"]
    elif defect == "duplicate":
        rows[1]["question"] = rows[0]["question"]
    elif defect == "corpus":
        rows[0]["corpus_sha256"] = "a" * 64
    elif defect == "ownership":
        rows[0]["source_document_ids"] = ["py3119.sqlite3"]
    else:
        rows[0]["question"] += " Please explain."
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    integrity_path = copied / "integrity.json"
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    integrity["files"]["candidates/train.jsonl"] = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
    integrity_path.write_text(json.dumps(integrity), encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        validate_v2_dataset(copied)


def test_legacy_pilot_unchanged_and_still_loads():
    expected = {
        "documents.jsonl": (
            "39b035542deb580bf1bd5c192511f362d39b89b3dcd82990ee1554b24225b7c3"
        ),
        "questions.jsonl": (
            "b1df4b578978cc6d3c4e352d8a38563b3615f6263c9d2cbbf144e26cc1703f5c"
        ),
    }
    for name, digest in expected.items():
        assert (
            hashlib.sha256(
                (Path("data/benchmark") / name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            == digest
        )
    documents, questions = load_dataset(
        "data/benchmark/documents.jsonl", "data/benchmark/questions.jsonl"
    )
    assert len(documents) == 17
    assert len(questions) == 54


def test_candidate_gold_modules_are_not_imported_by_runtime():
    forbidden = {
        "benchmark_v2",
        "benchmark_review",
        "benchmark_queue",
        "CandidateRecord",
        "load_v2_candidates",
        "validate_v2_dataset",
    }
    paths = [
        p
        for folder in ("api", "retrieval", "generation")
        for p in (Path("backend/app") / folder).rglob("*.py")
    ]
    paths.append(Path("backend/app/evaluation/runner.py"))
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            if isinstance(node, ast.ImportFrom):
                assert not forbidden & set((node.module or "").split(".")), path
                assert not forbidden & {alias.name for alias in node.names}, path
            if isinstance(node, ast.Import):
                assert all(
                    not forbidden & set(a.name.split(".")) for a in node.names
                ), path


def test_unreviewed_candidates_are_not_accepted_by_legacy_loader():
    with pytest.raises(ValueError):
        load_dataset(ROOT / "documents.jsonl", ROOT / "candidates/train.jsonl")
