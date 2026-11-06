"""Synthetic UI submissions are test fixtures, never genuine recorded reviews."""

import ast
import hashlib
import json
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest
from app.evaluation import review_app
from app.evaluation.benchmark_queue import (
    Submission,
    required_checks,
    validate_submission,
)
from app.evaluation.benchmark_v2 import load_v2_candidates, validate_v2_dataset
from app.evaluation.review_app import DATASET, ReviewStore, create_review_app
from fastapi.testclient import TestClient


def client_for(drafts, reviewer="fixture-only-reviewer"):
    client = TestClient(
        create_review_app(reviewer=reviewer, drafts=drafts),
        base_url="http://127.0.0.1:8010",
        client=("127.0.0.1", 51000),
    )
    session = client.get("/api/session").json()
    client.headers["X-Review-Token"] = session["token"]
    return client


@pytest.fixture
def client(tmp_path):
    return client_for(tmp_path / "drafts")


def first_payload(record, revision=0, basis="independent"):
    # Read candidate gold solely to construct a deterministic synthetic fixture.
    q = next(
        q
        for q in load_v2_candidates(DATASET)
        if q.id == record["submission"]["candidate_id"]
    )
    return dict(
        revision=revision,
        basis=basis,
        first_pass_decision=q.expected_decision,
        first_pass_category=q.category,
        first_pass_findings="Synthetic fixture findings, not a human judgment.",
        corpus_search_notes="Synthetic fixture search notes, not human work.",
        evidence_records=[],
    )


def fill_first_pass(client, basis="independent"):
    state = client.get("/api/packets/1").json()
    for record in state["records"]:
        response = client.put(
            "/api/packets/1/first-pass/" + record["submission"]["candidate_id"],
            json=first_payload(record, state["revision"], basis),
        )
        assert response.status_code == 200, response.text
        state = response.json()
    response = client.post(
        "/api/packets/1/reveal", json={"revision": state["revision"]}
    )
    assert response.status_code == 200, response.text
    return response.json()


def final_payload(record, revision):
    q = next(
        q
        for q in load_v2_candidates(DATASET)
        if q.id == record["submission"]["candidate_id"]
    )
    return dict(
        revision=revision,
        action="accept",
        checks=required_checks(q),
        rationale="Synthetic fixture rationale, not a real acceptance.",
        evidence_records=[
            dict(**s.model_dump(), finding="Synthetic span check")
            for s in q.evidence_spans + q.diagnostic_spans
        ],
        proposed_changes=None,
    )


def test_blind_questions_sources_schema_and_shared_styling(client):
    session = client.get("/api/session").json()
    assert session["packets"] == list(range(1, 17))
    assert len(session["sources"]) == 34
    assert session["schema"] == Submission.model_json_schema()
    for batch in session["packets"]:
        state = client.get(f"/api/packets/{batch}").json()
        blind = (DATASET / f"human_review/batch-{batch:02}/blind.md").read_text(
            encoding="utf-8"
        )
        questions = re.findall(r"```text\n(.*?)\n```", blind, re.DOTALL)
        assert [r["question"] for r in state["records"]] == questions
        assert all("annotation" not in r for r in state["records"])
        assert all(
            r["submission"]["first_pass_category"] is None for r in state["records"]
        )
    for doc in session["sources"]:
        source = client.get("/api/sources/" + doc["id"])
        assert source.status_code == 200
        assert source.json()["version"] == "3.11.9"
        text = source.json()["text"].encode()
        assert hashlib.sha256(text).hexdigest() == source.json()["sha256"]
    tokens = client.get("/assets/tokens.css")
    assert tokens.content == Path("frontend/app/tokens.css").read_bytes()
    index = client.get("/")
    assert 'id="decision" required' in index.text
    assert 'id="annotation-panel" hidden' in index.text
    assert "frame-ancestors 'none'" in index.headers["content-security-policy"]
    assert index.headers["cache-control"] == "no-store"
    assert client.get("/assets/review.js").status_code == 200
    assert client.get("/assets/review.css").status_code == 200


def test_save_resume_and_stale_tab_cannot_overwrite(tmp_path):
    drafts = tmp_path / "drafts"
    client = client_for(drafts)
    record = client.get("/api/packets/1").json()["records"][0]
    url = "/api/packets/1/first-pass/" + record["submission"]["candidate_id"]
    payload = first_payload(record)
    response = client.put(url, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["first_pass_saved"] == 1
    assert client.put(url, json=payload).status_code == 409
    # A newly created app, as after process restart, loads the durable draft.
    reopened = client_for(drafts)
    resumed = reopened.get("/api/packets/1").json()
    assert resumed["revision"] == 1
    assert (
        resumed["records"][0]["submission"]["first_pass_findings"]
        == (payload["first_pass_findings"])
    )
    assert reopened.get("/api/packets/2").json()["first_pass_saved"] == 0


def test_reviewers_cannot_select_or_view_each_others_drafts(tmp_path):
    drafts = tmp_path / "drafts"
    a = client_for(drafts, "fixture-A")
    b = client_for(drafts, "fixture-B")
    record = a.get("/api/packets/1").json()["records"][0]
    assert (
        a.put(
            "/api/packets/1/first-pass/" + record["submission"]["candidate_id"],
            json=first_payload(record),
        ).status_code
        == 200
    )
    assert b.get("/api/packets/1").json()["first_pass_saved"] == 0
    assert b.get("/api/reviewers/fixture-A").status_code == 404
    body = first_payload(record)
    body["reviewer_id"] = "fixture-A"
    assert (
        b.put(
            "/api/packets/1/first-pass/" + record["submission"]["candidate_id"],
            json=body,
        ).status_code
        == 422
    )
    assert b.get("/api/session").json()["reviewer_id"] == "fixture-B"


def test_reveal_requires_whole_packet_and_locks_first_pass(client):
    assert client.post("/api/packets/1/reveal", json={"revision": 0}).status_code == 409
    record = client.get("/api/packets/1").json()["records"][0]
    assert (
        client.put(
            "/api/packets/1/annotation/" + record["submission"]["candidate_id"],
            json=final_payload(record, 0),
        ).status_code
        == 409
    )
    state = fill_first_pass(client)
    assert all("annotation" in r for r in state["records"])
    assert client.get("/api/packets/2").json()["revealed"] is False
    assert (
        client.put(
            "/api/packets/1/first-pass/" + record["submission"]["candidate_id"],
            json=first_payload(record, state["revision"]),
        ).status_code
        == 409
    )


def test_completed_export_passes_existing_validator_but_never_imports(client, tmp_path):
    immutable = {p: p.read_bytes() for p in DATASET.rglob("*") if p.is_file()}
    state = fill_first_pass(client)
    for record in state["records"]:
        response = client.put(
            "/api/packets/1/annotation/" + record["submission"]["candidate_id"],
            json=final_payload(record, state["revision"]),
        )
        assert response.status_code == 200, response.text
        state = response.json()
    assert state["validated_not_imported"] == 10
    checked = client.post(
        "/api/packets/1/validate", json={"revision": state["revision"]}
    )
    assert checked.json()["status"] == "validated_not_imported"
    exported = client.get("/api/packets/1/export")
    for record in exported.json():
        parsed = Submission.model_validate_json(json.dumps(record))
        assert (
            validate_submission(DATASET, parsed)["status"] == "validated_not_imported"
        )
    form = tmp_path / "synthetic-fixture-only.json"
    form.write_bytes(exported.content)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.evaluation.benchmark_queue",
            "check-submission",
            str(DATASET),
            str(form),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert len(json.loads(result.stdout)) == 10
    with pytest.raises(ValueError, match="Human verification incomplete"):
        validate_v2_dataset(DATASET, require_human_acceptance=True)
    assert all(p.read_bytes() == content for p, content in immutable.items())


def test_assisted_cannot_be_promoted_or_exported_as_independent(client):
    state = fill_first_pass(client, basis="assisted")
    record = state["records"][0]
    response = client.put(
        "/api/packets/1/annotation/" + record["submission"]["candidate_id"],
        json=final_payload(record, state["revision"]),
    )
    assert response.status_code == 200
    assert response.json()["records"][0]["validation"]["status"] == (
        "assisted_not_eligible"
    )
    exported = client.get("/api/packets/1/export").json()
    assert all(r["independent_first_pass"] is None for r in exported)
    assert response.json()["validated_not_imported"] == 0


def test_imported_q1_q2_notes_keep_assistance_and_originals(tmp_path):
    client = client_for(tmp_path / "drafts")
    files = [
        DATASET / "human_review/batch-01/reviewer-A.json",
        Path(".ragbench-cache/human-review/batch-01-A/reviewer-A.json"),
    ]
    before = {p: p.read_bytes() for p in files}
    # Combine nonempty first-pass entries only in a synthetic HTTP upload;
    # this never reconciles or writes either actual reviewer file.
    records = [
        r
        for p in files
        for r in json.loads(p.read_text("utf-8"))
        if r["first_pass_findings"]
    ]
    response = client.post(
        "/api/packets/1/import-notes",
        json={
            "revision": 0,
            "records": records,
        },
    )
    assert response.status_code == 200, response.text
    state = response.json()
    for original in records:
        saved = next(
            r
            for r in state["records"]
            if r["submission"]["candidate_id"] == original["candidate_id"]
        )
        assert (
            saved["submission"]["first_pass_findings"]
            == original["first_pass_findings"]
        )
        assert saved["assisted"] is True
        assert saved["submission"]["independent_first_pass"] is None
        url = "/api/packets/1/first-pass/" + original["candidate_id"]
        assert (
            client.put(url, json=first_payload(saved, state["revision"])).status_code
            == 409
        )
    assert all(p.read_bytes() == content for p, content in before.items())


@pytest.mark.parametrize(
    "update",
    [
        {"basis": None},
        {"first_pass_decision": "AUTO"},
        {"first_pass_findings": " "},
        {"first_pass_category": "unknown"},
        {"first_pass_category": "answerable", "first_pass_decision": "CLARIFY"},
        {"independent_first_pass": True},
        {"revision": True},
    ],
)
def test_invalid_first_pass_never_saves(client, update):
    record = client.get("/api/packets/1").json()["records"][0]
    response = client.put(
        "/api/packets/1/first-pass/" + record["submission"]["candidate_id"],
        json={**first_payload(record), **update},
    )
    assert response.status_code == 422
    assert client.get("/api/packets/1").json()["first_pass_saved"] == 0


def test_unicode_evidence_and_full_corpus_search(client):
    session = client.get("/api/session").json()
    # Locate real non-ASCII text in the pinned corpus without modifying it.
    for doc in session["sources"]:
        text = client.get("/api/sources/" + doc["id"]).json()["text"]
        start = next((i for i, c in enumerate(text) if ord(c) > 127), None)
        if start is not None:
            break
    assert start is not None
    response = client.post(
        "/api/evidence",
        json=dict(
            doc_id=doc["id"],
            start_char=start,
            end_char=start + 5,
            finding="Synthetic exact Unicode check",
        ),
    )
    assert response.status_code == 200
    assert response.json()["text"] == text[start : start + 5]
    assert response.json()["id"] == f"{doc['id']}_s{start}_{start + 5}"
    assert (
        client.post(
            "/api/evidence",
            json=dict(
                doc_id=doc["id"],
                start_char=0,
                end_char=99999999,
                finding="fixture",
            ),
        ).status_code
        == 422
    )
    result = client.get("/api/search", params={"q": "create_task"}).json()
    assert result["documents_searched"] == 34
    assert any(r["doc_id"] == "py3119.asyncio-task" for r in result["matches"])
    assert all(r["line"] > 0 for r in result["matches"])


def test_corrupt_state_and_failed_replace_preserve_previous_save(tmp_path, monkeypatch):
    drafts = tmp_path / "drafts"
    client = client_for(drafts)
    record = client.get("/api/packets/1").json()["records"][0]
    url = "/api/packets/1/first-pass/" + record["submission"]["candidate_id"]
    assert client.put(url, json=first_payload(record)).status_code == 200
    path = next(drafts.glob("*/batch-01.json"))
    before = path.read_bytes()

    def fail_replace(*args):
        raise OSError("fixture-only sensitive filesystem path")

    with monkeypatch.context() as patch:
        patch.setattr(review_app.os, "replace", fail_replace)
        response = client.put(url, json=first_payload(record, 1))
        assert response.status_code == 503
        assert "sensitive filesystem" not in response.text
    assert path.read_bytes() == before
    assert not list(path.parent.glob("*.tmp"))
    assert not (path.parent / ".write-lock").exists()
    path.write_text("{broken", encoding="utf-8")
    assert client.get("/api/packets/1").status_code == 409
    assert client.put(url, json=first_payload(record, 1)).status_code == 409
    assert path.read_text() == "{broken"


def test_second_process_lock_prevents_overwrite(tmp_path):
    drafts = tmp_path / "drafts"
    client = client_for(drafts)
    store = ReviewStore(DATASET, drafts, "fixture-only-reviewer")
    record = client.get("/api/packets/1").json()["records"][0]
    with store.transaction():
        response = client.put(
            "/api/packets/1/first-pass/" + record["submission"]["candidate_id"],
            json=first_payload(record),
        )
        assert response.status_code == 409
    assert client.get("/api/packets/1").json()["first_pass_saved"] == 0


def test_local_boundary_paths_and_request_limit(client):
    assert (
        client.get("/api/session", headers={"Host": "attacker.example"}).status_code
        == 403
    )
    assert (
        client.get(
            "/api/session", headers={"Origin": "https://attacker.example"}
        ).status_code
        == 403
    )
    assert (
        client.get("/api/session", headers={"Sec-Fetch-Site": "cross-site"}).status_code
        == 403
    )
    assert (
        client.post(
            "/api/packets/1/reveal",
            json={"revision": 0},
            headers={"X-Review-Token": "bad"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/packets/1/reveal",
            content="x" * (512 * 1024 + 1),
            headers={"Content-Type": "application/json"},
        ).status_code
        == 413
    )
    assert (
        client.post(
            "/api/packets/1/reveal",
            content="{broken",
            headers={"Content-Type": "application/json"},
        ).status_code
        == 422
    )
    assert client.get("/assets/secret.txt").status_code == 404
    assert client.get("/api/sources/unknown").status_code == 404
    assert client.get("/api/packets/17").status_code == 404
    assert client.get("/api/search", params={"q": ""}).status_code == 422
    with pytest.raises(ValueError, match="separate from benchmark"):
        ReviewStore(DATASET, DATASET / "drafts", "fixture")
    with pytest.raises(ValueError, match="author"):
        ReviewStore(DATASET, Path(".pytest_cache"), "codex")


def test_invalid_imports_and_final_override_do_not_change_drafts(client):
    record = client.get("/api/packets/1").json()["records"][0]
    original = record["submission"]
    for records in [
        [{**original, "candidate_id": ["bad"]}],
        [original, original],
        [{**original, "candidate_sha256": "a" * 64}],
        [{**original, "first_pass_findings": "Incomplete imported note"}],
    ]:
        response = client.post(
            "/api/packets/1/import-notes",
            json={
                "revision": 0,
                "records": records,
            },
        )
        assert response.status_code == 422, response.text
        assert client.get("/api/packets/1").json()["revision"] == 0
    body = final_payload(record, 0)
    body["independent_first_pass"] = True
    assert (
        client.put(
            "/api/packets/1/annotation/" + original["candidate_id"],
            json=body,
        ).status_code
        == 422
    )


def test_changed_inputs_block_saving_without_touching_draft(client, monkeypatch):
    record = client.get("/api/packets/1").json()["records"][0]

    def changed(*args, **kwargs):
        raise ValueError("Fixture-only simulated integrity drift")

    monkeypatch.setattr(review_app, "validate_v2_dataset", changed)
    response = client.put(
        "/api/packets/1/first-pass/" + record["submission"]["candidate_id"],
        json=first_payload(record),
    )
    assert response.status_code == 409
    assert client.get("/api/packets/1").json()["first_pass_saved"] == 0


def test_curation_app_stays_out_of_runtime_imports():
    files = [Path("backend/app/evaluation/runner.py")]
    for folder in ("api", "retrieval", "generation"):
        files.extend((Path("backend/app") / folder).rglob("*.py"))
    for path in files:
        for node in ast.walk(ast.parse(path.read_text("utf-8-sig"))):
            if isinstance(node, ast.ImportFrom):
                assert "review_app" not in (node.module or "").split("."), path
            elif isinstance(node, ast.Import):
                assert all("review_app" not in n.name.split(".") for n in node.names), (
                    path
                )


@pytest.mark.parametrize("pilot_profile", [False, True])
def test_documented_cli_serves_only_loopback_without_inference(tmp_path, pilot_profile):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    log_path = tmp_path / "startup.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "app.evaluation.review_app",
                "--reviewer",
                "fixture-startup-only",
                *(["--pilot"] if pilot_profile else []),
                "--port",
                str(port),
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 20
            while True:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                        html = response.read().decode()
                    break
                except OSError:
                    if process.poll() is not None or time.monotonic() >= deadline:
                        pytest.fail(log_path.read_text(encoding="utf-8"))
                    time.sleep(0.1)
            assert "Reckon" in html
            with urlopen(
                f"http://127.0.0.1:{port}/api/packets/1", timeout=3
            ) as response:
                packet = json.load(response)
            assert packet["first_pass_saved"] == 0
            assert len(packet["records"]) == 10
            assert "annotation" not in packet["records"][0]
            with urlopen(f"http://127.0.0.1:{port}/api/session", timeout=3) as response:
                session = json.load(response)
            assert len(session["packets"]) == (3 if pilot_profile else 16)
            assert session["profile"] == (
                "python311-pilot30.v1" if pilot_profile else "full-160"
            )
            assert f"http://127.0.0.1:{port}" in log_path.read_text("utf-8")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
