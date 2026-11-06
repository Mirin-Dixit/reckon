"""Synthetic review submissions are fixtures, never recorded human reviews."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.evaluation.benchmark_queue import (
    Submission,
    _fence,
    build_queue,
    leakage_report,
    required_checks,
    review_status,
    validate_submission,
)
from app.evaluation.benchmark_review import ReviewItem, canonical_digest
from app.evaluation.benchmark_v2 import load_v2_candidates
from pydantic import ValidationError

ROOT = Path("data/benchmark_v2/python311_3_11_9")


@pytest.fixture
def fixture_submission():
    q = load_v2_candidates(ROOT)[0]
    payload = dict(
        schema_version="ragbench.review-submission.v1",
        candidate_id=q.id,
        candidate_sha256=canonical_digest(q.model_dump(mode="json")),
        corpus_sha256=q.corpus_sha256,
        reviewer_id="fixture-only-reviewer",
        reviewed_at_utc=datetime(2026, 11, 3, tzinfo=UTC),
        independent_first_pass=True,
        first_pass_decision=q.expected_decision,
        first_pass_category=q.category,
        first_pass_findings="Synthetic test findings",
        action="accept",
        checks=required_checks(q),
        rationale="Synthetic test rationale",
        corpus_search_notes="Synthetic test search notes",
        evidence_records=[
            {**s.model_dump(), "finding": "Synthetic span check"}
            for s in q.evidence_spans
        ],
        proposed_changes=None,
    )
    return payload


def test_packets_are_bound_prioritized_and_do_not_record_reviews(tmp_path):
    before = (ROOT / "review_ledger.jsonl").read_bytes()
    output = tmp_path / "packets"
    result = build_queue(ROOT, output, repository=Path("."))
    assert result["candidates"] == 160
    assert result["required_review_records"] == 250
    assert result["human_reviews"] == result["accepted_candidates"] == 0
    assert result["missing_review_records"] == 250
    assert result["agreement"] is None
    assert result["unresolved_verdict_disagreements"] == 0
    assert result["freeze_status"].startswith("blocked")
    assert len(list(output.glob("batch-*"))) == 16
    assert sum(r["required_reviews"] == 2 for r in result["queue"]) == 90
    assert all(r["required_reviews"] == 2 for r in result["queue"][:90])
    assert len(list(output.glob("batch-*/reviewer-*.json"))) == 25
    for form in output.glob("batch-*/reviewer-*.json"):
        for row in json.loads(form.read_text(encoding="utf-8")):
            assert row["reviewer_id"] is row["action"] is None
            assert row["independent_first_pass"] is None
            with pytest.raises(ValidationError):
                Submission.model_validate(row)
    for packet in output.glob("batch-*/blind.md"):
        text = packet.read_text(encoding="utf-8")
        assert "expected_answer" not in text
        assert "expected_decision" not in text
        assert "evidence_spans" not in text
    assert "expected_answer" in (output / "batch-01/annotations.md").read_text(
        encoding="utf-8"
    )
    assert (ROOT / "review_ledger.jsonl").read_bytes() == before
    hashes = json.loads((output / "packet_hashes.json").read_text())
    for name, digest in hashes["files"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    with pytest.raises(ValueError, match="will not be overwritten"):
        build_queue(ROOT, output, repository=Path("."))


def test_lexical_screen_flags_cross_split_and_historical_exposure():
    a = load_v2_candidates(ROOT)[0]
    b = a.model_copy(
        update={
            "id": "fixture-b",
            "split": "test",
            "question": a.question.replace("3.11", "3.13"),
        }
    )
    old = dict(
        id="fixture-history", dataset="sample", split="unspecified", question=a.question
    )
    result = leakage_report([a, b], [old])
    assert result == leakage_report([a, b], [old])
    assert result["counts"]["cross_split_possible_paraphrase"] == 1
    assert result["counts"]["historical_exposure"] == 2
    assert all(p["status"] == "pending_human_pair_review" for p in result["pairs"])
    assert "not_semantic" in result["status"]


def test_answer_support_reuse_flags_different_question_wording():
    a = load_v2_candidates(ROOT)[0]
    b = a.model_copy(update={"id": "fixture-b", "question": "Explain this operation."})
    report = leakage_report([a, b], [])
    assert report["pairs"][0]["shared_answer_evidence_ids"] == [a.evidence_spans[0].id]


def test_fences_cannot_be_closed_by_source_text():
    value = "````\n<script>source, not HTML</script>\n`````"
    fenced = _fence(value)
    assert fenced.startswith("``````text\n")
    assert fenced.endswith("\n``````\n")


def test_valid_fixture_receipt_is_read_only(fixture_submission):
    before = (ROOT / "review_ledger.jsonl").read_bytes()
    receipt = validate_submission(ROOT, Submission.model_validate(fixture_submission))
    assert receipt["status"] == "validated_not_imported"
    assert receipt["ledger_review"]["verdict"] == "accept"
    assert receipt["proposed_candidate"] is None
    assert json.loads(receipt["ledger_review"]["rationale"])["evidence_records"]
    assert (ROOT / "review_ledger.jsonl").read_bytes() == before


@pytest.mark.parametrize(
    "update",
    [
        {"reviewer_id": None},
        {"reviewer_id": " "},
        {"reviewed_at_utc": datetime(2026, 11, 3)},
        {"independent_first_pass": 1},
        {"independent_first_pass": False},
        {"action": None},
        {"action": "automatic_accept"},
        {"first_pass_findings": " "},
        {"rationale": " "},
        {"first_pass_decision": "CLARIFY"},
    ],
)
def test_blank_or_invalid_human_attestations_are_rejected(fixture_submission, update):
    with pytest.raises(ValidationError):
        Submission.model_validate({**fixture_submission, **update})


@pytest.mark.parametrize(
    "update, message",
    [
        ({"candidate_sha256": "a" * 64}, "stale or unknown"),
        ({"corpus_sha256": "a" * 64}, "stale or unknown"),
        ({"candidate_id": "unknown"}, "stale or unknown"),
        ({"reviewer_id": "codex"}, "self-review"),
        ({"checks": []}, "checklist incomplete"),
        ({"evidence_records": []}, "recorded exact source evidence"),
        ({"action": "revise", "proposed_changes": None}, "requires annotation changes"),
        (
            {"action": "revise", "proposed_changes": {"id": "changed"}},
            "protected identity",
        ),
        ({"action": "accept", "proposed_changes": {"question": "Changed"}}, "hidden"),
        (
            {"action": "reclassify", "proposed_changes": {"question": "Changed"}},
            "different proposed category",
        ),
    ],
)
def test_invalid_intake_does_not_bypass_review(fixture_submission, update, message):
    submission = Submission.model_validate({**fixture_submission, **update})
    with pytest.raises(ValueError, match=message):
        validate_submission(ROOT, submission)


def test_nonexact_review_evidence_is_rejected(fixture_submission):
    fixture_submission["evidence_records"][0]["text"] = (
        "X" + fixture_submission["evidence_records"][0]["text"][1:]
    )
    with pytest.raises(ValueError, match="not an exact"):
        validate_submission(ROOT, Submission.model_validate(fixture_submission))


@pytest.mark.parametrize(
    "action,verdict",
    [
        ("reject", "reject"),
        ("revise", "revise"),
        ("reclassify", "revise"),
    ],
)
def test_actions_preserve_existing_ledger_verdicts(fixture_submission, action, verdict):
    fixture_submission["action"] = action
    if action == "revise":
        fixture_submission["proposed_changes"] = {
            "notes": "Synthetic proposed correction"
        }
    elif action == "reclassify":
        span = load_v2_candidates(ROOT)[0].evidence_spans[0].model_dump()
        fixture_submission["proposed_changes"] = dict(
            category="off_topic",
            is_answerable=False,
            expected_decision="ABSTAIN",
            expected_answer=None,
            evidence_spans=[],
            diagnostic_spans=[span],
            absence_note="Synthetic fixture only, not a real candidate correction",
        )
    receipt = validate_submission(ROOT, Submission.model_validate(fixture_submission))
    assert receipt["ledger_review"]["verdict"] == verdict
    assert receipt["action"] == action
    if action != "reject":
        assert receipt["proposed_candidate"]["candidate_revision"] == 2
        assert receipt["proposed_candidate"]["status"] == "candidate"


def test_no_human_counts_or_agreement_are_invented():
    candidates = load_v2_candidates(ROOT)
    ledger = {
        r.candidate_id: r
        for r in (
            ReviewItem.model_validate_json(line)
            for line in (ROOT / "review_ledger.jsonl").read_text().splitlines()
        )
    }
    status = review_status(candidates, ledger)
    assert status["human_reviews"] == status["accepted_candidates"] == 0
    assert status["agreement"] is None
