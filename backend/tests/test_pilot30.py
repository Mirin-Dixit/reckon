"""Pilot release fixtures are synthetic; no real human reviews are created here."""

import ast
import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.evaluation.benchmark_queue import Submission, _template, required_checks
from app.evaluation.benchmark_review import (
    HumanDecision,
    canonical_digest,
)
from app.evaluation.benchmark_v2 import load_v2_candidates, validate_v2_dataset
from app.evaluation.pilot30 import (
    EXPOSED_IDS,
    PARENT_ROOT,
    PILOT_ID,
    PILOT_ROOT,
    RELEASE_CHECKS,
    STRATA,
    agreement,
    create_pilot,
    pilot_ledger,
    select_candidates,
    selection_inputs,
    validate_pilot,
    validate_pilot_submission,
)
from app.evaluation.review_app import create_review_app
from fastapi.testclient import TestClient


def write_ledger(root, items):
    (root / "review_ledger.jsonl").write_text(
        "".join(item.model_dump_json() + "\n" for item in items.values()),
        encoding="utf-8",
        newline="\n",
    )


@pytest.fixture
def pilot(tmp_path):
    root = tmp_path / "pilot"
    shutil.copytree(PILOT_ROOT, root)
    return root


def fixture_decision(q, reviewer):
    notes = dict(
        rationale="SYNTHETIC fixture rationale; not a real human decision",
        first_pass_decision=q.expected_decision,
        first_pass_category=q.category,
        first_pass_findings="SYNTHETIC fixture findings; not a real human review",
        corpus_search_notes="SYNTHETIC searches; not actual human searches",
        evidence_records=[
            dict(**s.model_dump(), finding="SYNTHETIC span check")
            for s in q.evidence_spans + q.diagnostic_spans
        ],
    )
    return HumanDecision(
        reviewer_id=reviewer,
        actor_kind="human",
        independent_first_pass=True,
        candidate_sha256=canonical_digest(q.model_dump(mode="json")),
        corpus_sha256=q.corpus_sha256,
        reviewed_at_utc=datetime(2026, 11, 3, tzinfo=UTC),
        verdict="accept",
        checks=required_checks(q),
        rationale=json.dumps(notes),
    )


def fill_fixture_reviews(root):
    _, _, selected = selection_inputs()
    items = pilot_ledger(root)
    for q in selected:
        items[q.id] = items[q.id].model_copy(
            update={
                "reviews": [
                    fixture_decision(q, "fixture-rater-a"),
                    fixture_decision(q, "fixture-rater-b"),
                ]
            }
        )
    write_ledger(root, items)
    return items


def fixture_release(root):
    payload = dict(
        schema_version="ragbench.pilot-release.v1",
        pilot_id=PILOT_ID,
        actor_kind="human",
        reviewer_id="fixture-coordinator-only",
        approved_at_utc="2026-11-04T00:00:00Z",
        approval="explicit_pilot_freeze_approval",
        protocol_sha256=canonical_digest(
            json.loads((root / "protocol.json").read_text())
        ),
        selection_sha256=canonical_digest(
            json.loads((root / "selection.json").read_text())
        ),
        review_ledger_sha256=hashlib.sha256(
            (root / "review_ledger.jsonl").read_bytes()
        ).hexdigest(),
        checks=list(RELEASE_CHECKS),
        rationale="SYNTHETIC approval in tmp_path only",
    )
    (root / "release_approval.json").write_text(json.dumps(payload), encoding="utf-8")


def test_exact_reproducible_composition_anchors_and_exclusions():
    qs = load_v2_candidates(PARENT_ROOT)
    chosen, excluded = select_candidates(qs)
    reverse, reverse_excluded = select_candidates(list(reversed(qs)))
    assert [q.id for q in chosen] == [q.id for q in reverse]
    assert excluded == reverse_excluded
    assert len(chosen) == len({q.id for q in chosen}) == 30
    assert set(EXPOSED_IDS) <= set(excluded)
    assert not set(excluded) & {q.id for q in chosen}
    assert "py311v2_test_001" in excluded  # Entire exposed anchor family.
    for split in ("dev", "test"):
        group = [q for q in chosen if q.split == split]
        assert Counter(q.category for q in group) == {
            "answerable": 9,
            **{c: 1 for c in STRATA},
        }
        assert all(set(q.near_miss_parent_ids) <= {r.id for r in group} for q in group)
        assert {q.cluster_id for q in group if q.is_answerable} == {
            q.cluster_id for q in qs if q.split == split
        }
    dev_topics = {q.cluster_id for q in chosen if q.split == "dev"}
    test_topics = {q.cluster_id for q in chosen if q.split == "test"}
    assert not dev_topics & test_topics


def test_creation_does_not_copy_or_change_parent_data(tmp_path):
    before = {
        p: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in PARENT_ROOT.rglob("*")
        if p.is_file()
    }
    output = tmp_path / "new-pilot"
    result = create_pilot(output)
    assert result["human_reviews"] == 0
    assert result["empirical_evaluation_allowed"] is False
    assert result["synthetic_infrastructure_allowed"] is True
    assert not (output / "documents.jsonl").exists()
    assert all(not item.reviews for item in pilot_ledger(output).values())
    assert all(
        hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in before.items()
    )
    with pytest.raises(ValueError, match="not be overwritten"):
        create_pilot(output)
    with pytest.raises(ValueError, match="separate"):
        create_pilot(PARENT_ROOT / "forbidden-pilot-output")


def test_pilot_and_full_gates_stay_closed_while_fixtures_are_allowed():
    result = validate_pilot()
    assert result["candidates"] == 30
    assert result["required_reviews"] == 60
    assert result["human_reviews"] == 0
    assert result["agreement"] is None
    assert result["full_benchmark_accepted"] is False
    assert result["synthetic_infrastructure_allowed"] is True
    with pytest.raises(ValueError, match="Pilot not accepted"):
        validate_pilot(require_acceptance=True)
    with pytest.raises(ValueError, match="Human verification incomplete"):
        validate_v2_dataset(PARENT_ROOT, require_human_acceptance=True)


@pytest.mark.parametrize("filename", ["protocol.json", "selection.json"])
def test_tampered_protocol_or_selection_is_rejected(pilot, filename):
    data = json.loads((pilot / filename).read_text())
    if filename == "protocol.json":
        data["required_reviews"] = 1
    else:
        data["records"][0]["split"] = "train"
    (pilot / filename).write_text(json.dumps(data))
    with pytest.raises(ValueError, match="protocol|selection"):
        validate_pilot(pilot)


def test_sixty_reviews_still_need_explicit_release_and_human_audits(pilot):
    fill_fixture_reviews(pilot)
    result = validate_pilot(pilot)
    assert result["human_reviews"] == 60
    assert result["agreement"]["answerability"]["kappa"] == 1
    assert result["empirical_evaluation_allowed"] is False
    fixture_release(pilot)
    result = validate_pilot(pilot, require_acceptance=True)
    assert result["empirical_evaluation_allowed"] is True
    assert result["full_benchmark_accepted"] is False
    assert validate_pilot()["human_reviews"] == 0  # Actual pilot is untouched.


def test_one_review_per_ordinary_answer_is_not_enough_and_approval_binds_log(pilot):
    items = fill_fixture_reviews(pilot)
    fixture_release(pilot)
    ordinary = next(
        item
        for item in items.values()
        if item.category == "answerable"
        and not item.is_compound
        and item.ambiguity_type is None
    )
    items[ordinary.candidate_id] = ordinary.model_copy(
        update={
            "reviews": ordinary.reviews[:1],
        }
    )
    write_ledger(pilot, items)
    result = validate_pilot(pilot)
    assert result["human_reviews"] == 59
    assert result["empirical_evaluation_allowed"] is False
    assert any("two distinct" in s for s in result["blockers"])
    assert any("approval" in s for s in result["blockers"])


def test_cannot_forge_actor_assistance_or_duplicate_rater(pilot):
    items = fill_fixture_reviews(pilot)
    first = next(iter(items))
    item = items[first]
    items[first] = item.model_copy(
        update={"reviews": [item.reviews[0], item.reviews[0]]}
    )
    write_ledger(pilot, items)
    assert validate_pilot(pilot)["empirical_evaluation_allowed"] is False
    # Invalid independent attestation is rejected by the original review schema.
    text = (pilot / "review_ledger.jsonl").read_text()
    (pilot / "review_ledger.jsonl").write_text(
        text.replace(
            '"independent_first_pass":true', '"independent_first_pass":false', 1
        )
    )
    with pytest.raises(ValueError):
        validate_pilot(pilot)


def test_same_two_raters_and_exact_evidence_are_required(pilot):
    items = fill_fixture_reviews(pilot)
    first = next(iter(items))
    review = items[first].reviews[1]
    notes = json.loads(review.rationale)
    notes["evidence_records"][0]["text"] = "not the source text"
    modified = review.model_copy(
        update={
            "reviewer_id": "fixture-different-rater",
            "rationale": json.dumps(notes),
        }
    )
    items[first] = items[first].model_copy(
        update={
            "reviews": [items[first].reviews[0], modified],
        }
    )
    write_ledger(pilot, items)
    result = validate_pilot(pilot)
    assert result["empirical_evaluation_allowed"] is False
    assert any("annotation/evidence" in s for s in result["blockers"])
    assert any("same two" in s for s in result["blockers"])


def test_agreement_is_annotation_based_and_undefined_is_honest():
    assert agreement([True, True, False, False], [True, False, True, False]) == {
        "n": 4,
        "raw_agreement": 0.5,
        "kappa": 0.0,
    }
    assert agreement([True, False], [True, False])["kappa"] == 1
    assert agreement([True, True], [True, True])["kappa"] is None
    assert agreement([], [True])["raw_agreement"] is None


@pytest.mark.parametrize(
    "change",
    [
        {"approved_at_utc": "2020-01-01T00:00:00Z"},
        {"checks": []},
        {"selection_sha256": "a" * 64},
    ],
)
def test_release_approval_cannot_skip_or_predate_human_gates(pilot, change):
    fill_fixture_reviews(pilot)
    fixture_release(pilot)
    path = pilot / "release_approval.json"
    payload = json.loads(path.read_text())
    path.write_text(json.dumps({**payload, **change}))
    assert validate_pilot(pilot)["empirical_evaluation_allowed"] is False
    with pytest.raises(ValueError, match="Pilot not accepted"):
        validate_pilot(pilot, require_acceptance=True)


def test_pilot_ui_reuses_sources_and_separates_profiles_and_reviewers(tmp_path):
    drafts = tmp_path / "drafts"

    def client(pilot=None, reviewer="fixture-ui-only"):
        c = TestClient(
            create_review_app(
                reviewer=reviewer,
                drafts=drafts,
                pilot=pilot,
            ),
            base_url="http://127.0.0.1:8010",
            client=("127.0.0.1", 50000),
        )
        c.headers["X-Review-Token"] = c.get("/api/session").json()["token"]
        return c

    a = client(PILOT_ROOT)
    full = client()
    b = client(PILOT_ROOT, "fixture-second-ui-only")
    assert a.get("/api/session").json()["profile"] == PILOT_ID
    assert a.get("/api/session").json()["packets"] == [1, 2, 3]
    assert len(a.get("/api/session").json()["sources"]) == 34
    assert full.get("/api/session").json()["packets"] == list(range(1, 17))
    assert a.get("/api/packets/4").status_code == 404
    first = a.get("/api/packets/1").json()["records"][0]
    qid = first["submission"]["candidate_id"]
    assert "annotation" not in first
    response = a.put(
        "/api/packets/1/first-pass/" + qid,
        json=dict(
            revision=0,
            basis="assisted",
            first_pass_decision="ABSTAIN",
            first_pass_category="attribute_near_miss",
            first_pass_findings="SYNTHETIC interface note, not a real judgment",
            corpus_search_notes="SYNTHETIC searches",
            evidence_records=[],
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json()["records"][0]["submission"]["independent_first_pass"] is None
    assert b.get("/api/packets/1").json()["first_pass_saved"] == 0
    assert full.get("/api/packets/1").json()["first_pass_saved"] == 0
    assert client(PILOT_ROOT).get("/api/packets/1").json()["first_pass_saved"] == 1
    assert a.post("/api/packets/1/reveal", json={"revision": 1}).status_code == 409
    exports = sum((a.get(f"/api/packets/{n}/export").json() for n in [1, 2, 3]), [])
    expected = json.loads((PILOT_ROOT / "selection.json").read_text())["records"]
    assert {r["candidate_id"] for r in exports} == {r["candidate_id"] for r in expected}
    assert not set(EXPOSED_IDS) & {r["candidate_id"] for r in exports}


def test_pilot_submission_membership_and_duplicates(pilot):
    _, _, selected = selection_inputs()
    q = selected[0]
    review = fixture_decision(q, "fixture-rater-a")
    notes = json.loads(review.rationale)
    payload = {
        **_template(q),
        **review.model_dump(
            mode="json",
            exclude={
                "actor_kind",
                "verdict",
                "rationale",
            },
        ),
        **notes,
        "action": "accept",
    }
    parsed = Submission.model_validate_json(json.dumps(payload))
    receipt = validate_pilot_submission(pilot, parsed)
    assert receipt["status"] == "validated_not_imported"
    assert receipt["pilot_id"] == PILOT_ID
    assert all(not r.reviews for r in pilot_ledger(pilot).values())
    fill_fixture_reviews(pilot)
    with pytest.raises(ValueError, match="Duplicate pilot reviewer"):
        validate_pilot_submission(pilot, parsed)
    other = next(q for q in load_v2_candidates(PARENT_ROOT) if q.id == EXPOSED_IDS[0])
    with pytest.raises(ValueError, match="outside"):
        validate_pilot_submission(
            pilot, parsed.model_copy(update={"candidate_id": other.id})
        )


def test_pilot_module_is_not_imported_by_inference():
    paths = [Path("backend/app/evaluation/runner.py")]
    for folder in ["api", "retrieval", "generation"]:
        paths.extend((Path("backend/app") / folder).rglob("*.py"))
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text("utf-8-sig"))):
            if isinstance(node, ast.ImportFrom):
                assert "pilot30" not in (node.module or "").split("."), path
            elif isinstance(node, ast.Import):
                assert all("pilot30" not in a.name.split(".") for a in node.names), path
