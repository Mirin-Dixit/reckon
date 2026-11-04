"""Offline P4 execution, durability, isolation and failure regression tests."""

import hashlib
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from app.api.experiment_models import (
    DevFreeze,
    ExperimentRequest,
    JobList,
    JobResults,
    JobSummary,
)
from app.api.main import create_app
from app.db.experiments import ExperimentStore, QueueFull, StoreConflict
from app.evaluation.experiment_jobs import ExperimentJobs
from app.evaluation.serialization import experiment_from_json
from app.evaluation.synthetic_runtime import GENERATION
from fastapi.testclient import TestClient


def request(method="bm25", split="dev", **overrides):
    return ExperimentRequest.model_validate(dict(
        split=split, retrieval={"method": method, "top_k": 3},
        policies=[{"name": "always_answer"}, {"name": "prompt_abstention"},
                  {"name": "threshold", "threshold": 0, "score_type": {
                      "bm25": "bm25", "dense": "dense_cosine", "hybrid": "hybrid_rrf",
                  }[method]}], **overrides,
    ))


@pytest.fixture
def service(tmp_path):
    jobs = ExperimentJobs(tmp_path / "jobs.sqlite", start_worker=False)
    yield jobs
    jobs.close()


def execute(service, spec=None):
    job = service.submit(spec or request())
    claimed = service.store.claim()
    assert claimed["id"] == job["id"]
    service._execute(claimed)
    return service.store.get(job["id"])


@pytest.mark.parametrize("method", ["bm25", "dense", "hybrid"])
def test_all_policies_reproducible_and_no_external_provider(
    service, monkeypatch, method
):
    import socket

    def forbidden(*args, **kwargs):
        pytest.fail("Synthetic execution attempted network access")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    first = execute(service, request(method))
    second = execute(service, request(method))
    assert first["status"] == second["status"] == "done"
    assert first["empirical_evaluation"] is False
    assert first["observed_run_count"] == first["expected_run_count"] == 12
    assert first["configuration"]["split"] == "dev"
    a = [r["observed"] for r in first["observations"]]
    b = [r["observed"] for r in second["observations"]]
    assert a == b
    assert {r["decision"] for r in a} == {"ANSWER", "ABSTAIN", "CLARIFY"}
    assert all(r["token_usage"] is None and r["latency_ms"] is None for r in a)
    record = experiment_from_json(json.dumps(first["result"]))
    assert record["generation_configuration"]["external_calls"] is False
    assert record["generation_configuration"]["model"] == GENERATION["model"]
    assert record["dataset_fingerprint"] == first["dataset_fingerprint"]
    JobResults.model_validate(first)


def test_bounded_queue_concurrent_submissions(service):
    def submit(_):
        try:
            return service.submit(request())["id"]
        except QueueFull:
            return None

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(submit, range(12)))
    assert sum(r is not None for r in results) == 5
    assert len(service.store.list()) == 5
    assert len(set(filter(None, results))) == 5


def test_single_owner_prevents_false_restart_recovery(service):
    job = service.submit(request())
    with pytest.raises(OSError):
        ExperimentStore(service.store.path)
    assert service.store.get(job["id"])["status"] == "queued"


@pytest.mark.parametrize("observe", [False, True])
def test_restart_marks_pending_interrupted_without_reexecution(tmp_path, observe):
    path = tmp_path / "jobs.sqlite"
    first = ExperimentJobs(path, start_worker=False)
    job = first.submit(request())
    queued = first.submit(request())
    claimed = first.store.claim()
    if observe:
        original = first.store.observe

        def interrupt(job_id, run):
            original(job_id, run)
            raise RuntimeError("process interruption")

        first.store.observe = interrupt
        with pytest.raises(RuntimeError):
            first._execute(claimed)
    first.close()
    second = ExperimentJobs(path, start_worker=False)
    try:
        saved = second.store.get(job["id"])
        assert saved["status"] == ("partial" if observe else "failed")
        assert saved["error"] == "process_interrupted"
        assert saved["observed_run_count"] == int(observe)
        assert saved["result"] is None
        assert second.store.get(queued["id"])["status"] == "failed"
        assert second.store.claim() is None
    finally:
        second.close()


@pytest.mark.parametrize("fail_fast", [False, True])
def test_failures_are_not_abstentions_and_cannot_freeze(service, fail_fast):
    job = execute(service, request(split="train", fail_fast=fail_fast))
    assert job["status"] == "partial"
    errors = [r for r in job["observations"] if r["error"]]
    assert errors and all(r["observed"]["decision"] is None for r in errors)
    assert job["observed_run_count"] == (4 if fail_fast else 12)
    with pytest.raises(StoreConflict):
        service.store.freeze(job["id"])


def test_dev_freeze_is_idempotent_immutable_and_hash_bound(service):
    job = execute(service)
    frozen = service.store.freeze(job["id"])
    assert frozen == service.store.freeze(job["id"])
    assert frozen["empirical_evaluation"] is False
    manifest = {k: v for k, v in frozen.items() if k not in ("sha256", "created_at")}
    serialized = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    assert hashlib.sha256(serialized).hexdigest() == frozen["sha256"]
    execute(service, request(random_seed=17))
    assert service.store.freeze(job["id"]) == frozen
    assert frozen["configuration"]["split"] == "dev"
    assert (
        frozen["generation_configuration"]["source_sha256"]
        == job["runtime_source_sha256"]
    )


def test_progress_survives_failed_finish_and_inconsistent_results_rejected(service):
    job = execute(service)
    with pytest.raises(StoreConflict):
        service.store.observe(job["id"], job["observations"][0])
    with pytest.raises(StoreConflict):
        service.store.finish(job["id"], job["result"], None)
    assert service.store.get(job["id"]) == job


def test_observation_storage_failure_not_reported_successful(service, monkeypatch):
    def failure(*args):
        raise sqlite3.OperationalError("private storage failure")

    monkeypatch.setattr(service.store, "observe", failure)
    job = service.submit(request())
    service.worker.start()
    for _ in range(150):
        saved = service.store.get(job["id"])
        if saved["status"] == "failed":
            break
        time.sleep(.02)
    assert saved["status"] == "failed"
    assert saved["error"] == "execution_failure"
    assert saved["result"] is None


def test_claim_failure_latches_worker_unavailable(service, monkeypatch):
    monkeypatch.setattr(service.store, "claim", lambda: (_ for _ in ()).throw(
        sqlite3.OperationalError("unavailable")))
    service.worker.start()
    service.worker.join(timeout=2)
    assert service.unavailable
    with pytest.raises(OSError):
        service.submit(request())


def wait_result(client, job_id):
    for _ in range(200):
        response = client.get(f"/api/v1/experiments/{job_id}/results")
        assert response.status_code == 200, response.text
        if response.json()["status"] not in ("queued", "running"):
            return response.json()
        time.sleep(.025)
    pytest.fail("Fixture job did not finish")


def test_http_workflow_persistence_and_no_gold_in_status(tmp_path):
    path = tmp_path / "api.sqlite"
    with TestClient(create_app(experiment_store_path=path)) as client:
        response = client.post("/api/v1/experiments", json=request().model_dump())
        assert response.status_code == 202, response.text
        job_id = response.json()["id"]
        saved = wait_result(client, job_id)
        assert saved["status"] == "done"
        status = client.get(f"/api/v1/experiments/{job_id}")
        assert "gold" not in status.text and "expected_answer" not in status.text
        assert client.post(f"/api/v1/experiments/{job_id}/freeze").status_code == 200
        assert client.get("/api/v1/experiments?limit=0").status_code == 422
    with TestClient(create_app(experiment_store_path=path)) as client:
        assert client.get(f"/api/v1/experiments/{job_id}/results").json() == saved
        assert client.get("/api/v1/experiments").json()["jobs"][0]["id"] == job_id


@pytest.mark.parametrize("changes", [
    {"split": "test"}, {"profile": "python311-pilot30.v1"},
    {"profile": "python311-v2"}, {"generation": {"model": "real-model"}},
    {"documents_path": "../../private"}, {"question_ids": ["py311v2_dev_001"]},
    {"question_ids": ["synthetic_train_01"]}, {"question_ids": []},
    {"question_ids": ["synthetic_dev_01", "synthetic_dev_01"]},
])
def test_api_rejects_real_data_overrides_and_split_leakage(tmp_path, changes):
    with TestClient(
        create_app(experiment_store_path=tmp_path / "api.sqlite")
    ) as client:
        payload = {**request().model_dump(), **changes}
        assert client.post("/api/v1/experiments", json=payload).status_code == 422


def test_legacy_empirical_route_denied_before_runtime_but_query_unchanged():
    calls = []
    def factory():
        calls.append(True)
        raise RuntimeError("No runtime initialized")

    with TestClient(create_app(runtime_factory=factory)) as client:
        response = client.post("/api/v1/evaluations", json={
            "split": "test", "policies": [{"name": "always_answer"}],
        })
        assert response.status_code == 403 and not calls
        # Query Lab still follows the existing runtime availability path.
        response = client.post("/api/v1/query", json={
            "question": "A question", "policy": {"name": "always_answer"},
        })
        assert response.status_code == 503 and calls


def test_local_access_and_safe_storage_error(tmp_path, monkeypatch):
    app = create_app(experiment_store_path=tmp_path / "api.sqlite")
    with TestClient(app) as client:
        evil = {"Origin": "https://evil.test"}
        assert client.get("/api/v1/experiments", headers=evil).status_code == 403
        assert client.get("/api/v1/experiments").status_code == 200
        def fail(*args):
            raise sqlite3.OperationalError("private path")
        monkeypatch.setattr(app.state.experiment_jobs.store, "list", fail)
        response = client.get("/api/v1/experiments")
        assert response.status_code == 503 and "private path" not in response.text


def test_schema_snapshot_matches_backend():
    snapshot = json.loads(Path("frontend/lib/experiment-schema.json").read_text())
    assert snapshot == {m.__name__: m.model_json_schema()
                        for m in (JobSummary, JobResults, JobList, DevFreeze)}
