"""Read-only SQLite and local API, without store recovery or inference."""

import hashlib
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from app.api.main import create_app
from app.db.analysis_reader import MAX_PAYLOAD_BYTES, read_analysis_jobs
from app.evaluation.matched_analysis import AnalysisReport
from fastapi.testclient import TestClient


@pytest.fixture
def saved(tmp_path):
    job = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "frontend/tests/fixture_job_result.json"
        ).read_text()
    )
    path = tmp_path / "jobs.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        db.execute(
            "CREATE TABLE freezes (job_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        db.execute("INSERT INTO jobs VALUES (?,?)", (job["id"], json.dumps(job)))
        db.execute(
            "INSERT INTO freezes VALUES (?,?)", (job["id"], '{"sha256":"unchanged"}')
        )
    return path, job


def test_analysis_is_read_only_and_never_initializes_runtime_or_store(
    saved, monkeypatch
):
    path, job = saved
    from app.db.experiments import ExperimentStore

    def forbidden(*a, **kw):
        raise AssertionError("No runtime/store initialization")

    monkeypatch.setattr(ExperimentStore, "__init__", forbidden)
    from app.evaluation import synthetic_runtime, threshold_sweep

    monkeypatch.setattr(synthetic_runtime, "pipeline_factory", forbidden)
    monkeypatch.setattr(threshold_sweep, "run_synthetic_sweep", forbidden)
    app = create_app(experiment_store_path=path, runtime_factory=forbidden)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/experiments/{job['id']}/analysis?lexical_proxy=true"
        )
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        report = AnalysisReport.model_validate_json(response.content)
        assert report.resamples == 2000 and report.matched_questions == 1
        assert report.resampling_units == 1
        assert not hasattr(app.state, "experiment_jobs")
        text = response.text
        for prohibited in (
            "expected_answer",
            "expected_safe_behavior",
            "evidence_spans",
            "reference_answer",
        ):
            assert prohibited not in text
        assert report.empirical_evaluation is False
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert not path.with_suffix(".lock").exists()


def test_ro_uri_enforced_and_missing_database_not_created(tmp_path, saved, monkeypatch):
    path, job = saved
    native = sqlite3.connect

    def check(database_uri, **kwargs):
        assert database_uri.endswith("?mode=ro") and kwargs["uri"] is True
        db = native(database_uri, **kwargs)
        with pytest.raises(sqlite3.OperationalError):
            db.execute("DELETE FROM jobs")
        db.rollback()
        return db

    monkeypatch.setattr(sqlite3, "connect", check)
    assert read_analysis_jobs(path, (job["id"],))[0] == job
    missing = tmp_path / "not-created.sqlite"
    with pytest.raises(FileNotFoundError):
        read_analysis_jobs(missing, (job["id"],))
    assert not missing.exists()


@pytest.mark.parametrize(
    "suffix",
    [
        "?resamples=1",
        "?resamples=5001",
        "?seed=2147483648",
        "?compare=bad",
        "?lexical_proxy=not-bool",
    ],
)
def test_invalid_api_parameters(saved, suffix):
    path, job = saved
    with TestClient(create_app(experiment_store_path=path)) as client:
        assert (
            client.get(f"/api/v1/experiments/{job['id']}/analysis{suffix}").status_code
            == 422
        )


def test_external_origins_missing_ids_duplicates_and_mutation_methods(saved):
    path, job = saved
    with TestClient(create_app(experiment_store_path=path)) as client:
        url = f"/api/v1/experiments/{job['id']}/analysis"
        assert (
            client.get(url, headers={"Origin": "https://evil.example"}).status_code
            == 403
        )
        assert client.post(url, json={}).status_code == 405
        assert client.get(url + f"?compare={job['id']}").status_code == 422
        assert client.get(url + f"?compare={uuid4()}").status_code == 404


@pytest.mark.parametrize(
    "change", ["test", "incomplete", "pending", "secret", "oversized", "corrupt"]
)
def test_invalid_records_are_safe_errors_without_recovery(saved, change):
    path, job = saved
    if change == "test":
        job["configuration"]["split"] = "test"
    elif change == "incomplete":
        job["result"]["runs"].pop()
    elif change == "pending":
        job["status"] = "running"
    elif change == "secret":
        job["result"]["generation_configuration"]["provider"] = (
            "sk-FAKE_INTERNAL_SECRET"
        )
    elif change == "oversized":
        job["extra"] = "x" * MAX_PAYLOAD_BYTES
    payload = (
        "invalid JSON sk-FAKE_INTERNAL_SECRET"
        if change == "corrupt"
        else json.dumps(job)
    )
    with sqlite3.connect(path) as db:
        db.execute("UPDATE jobs SET payload=?", (payload,))
    before = path.read_bytes()
    with TestClient(create_app(experiment_store_path=path)) as client:
        response = client.get(f"/api/v1/experiments/{job['id']}/analysis")
        assert response.status_code == 422
        assert "sk-FAKE_INTERNAL_SECRET" not in response.text
        assert set(response.json()) == {"error"}
    assert before == path.read_bytes()


def test_limits_remote_clients_and_busy_analysis(saved):
    from app.api.routes.analysis import _capacity

    path, job = saved
    app = create_app(experiment_store_path=path)
    url = f"/api/v1/experiments/{job['id']}/analysis"
    with TestClient(app, client=("203.0.113.1", 1234)) as client:
        assert client.get(url).status_code == 403
    with TestClient(app) as client:
        assert (
            client.get(
                url + "?" + "&".join(f"compare={uuid4()}" for _ in range(8))
            ).status_code
            == 422
        )
        assert _capacity.acquire(blocking=False)
        try:
            assert client.get(url).status_code == 503
        finally:
            _capacity.release()


def test_wal_format_rejected_without_sidecars_or_stale_immutable_reads(saved):
    path, job = saved
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
    before = {p.name: p.read_bytes() for p in path.parent.iterdir() if p.is_file()}
    with pytest.raises(ValueError, match="rollback-journal"):
        read_analysis_jobs(path, (job["id"],))
    assert before == {
        p.name: p.read_bytes() for p in path.parent.iterdir() if p.is_file()
    }


def test_analysis_does_not_load_gold_files_and_openapi_schema_matches_frontend(
    saved, monkeypatch
):
    from app.ingestion import loader

    def forbidden(*a, **kw):
        raise AssertionError("Analysis may not load datasets")

    monkeypatch.setattr(loader, "load_dataset_snapshot", forbidden)
    path, job = saved
    with TestClient(create_app(experiment_store_path=path)) as client:
        assert (
            client.get(f"/api/v1/experiments/{job['id']}/analysis").status_code == 200
        )
        spec = client.get("/api/v1/openapi.json").json()
        assert spec["paths"]["/api/v1/experiments/{job_id}/analysis"]["get"][
            "responses"
        ]["200"]
    schema = Path(__file__).resolve().parents[2] / "frontend/lib/analysis-schema.json"
    assert json.loads(schema.read_text()) == AnalysisReport.model_json_schema()


def test_explicit_threshold_only_selection_avoids_pooling_repeated_controls(saved):
    import copy

    path, first = saved
    second = copy.deepcopy(first)
    second["id"] = str(uuid4())
    second["result"]["experiment_id"] = second["id"]
    second["configuration"]["policies"][2]["threshold"] = -1.0
    second["result"]["policy_configurations"][2]["parameters"]["threshold"] = -1.0
    for row in second["observations"]:
        row["run_id"] = str(uuid4())
        if row["policy_name"] == "threshold":
            row["observed"]["scores"][0]["threshold"] = -1.0
            row["observed"]["policy_parameters"]["threshold"] = -1.0
    second["result"]["runs"] = copy.deepcopy(second["observations"])
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO jobs VALUES (?,?)", (second["id"], json.dumps(second)))
    before = path.read_bytes()
    with TestClient(create_app(experiment_store_path=path)) as client:
        url = (
            f"/api/v1/experiments/{first['id']}/analysis"
            f"?compare={second['id']}&resamples=20"
        )
        assert client.get(url).status_code == 422  # duplicated control configurations
        response = client.get(url + "&threshold_only=true&lexical_proxy=true")
        assert response.status_code == 200
        report = response.json()
        assert len(report["rows"]) == 2
        assert all(row["policy"] == "threshold" for row in report["rows"])
        assert report["matched_questions"] == 1
    assert path.read_bytes() == before
