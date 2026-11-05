"""Dashboard reads persisted synthetic snapshots without worker side effects."""

import hashlib
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from app.api.experiment_models import JobResults
from app.api.main import create_app
from app.db.analysis_reader import read_analysis_history
from app.db.experiments import ExperimentStore
from fastapi.testclient import TestClient


@pytest.fixture
def saved_dashboard(tmp_path, monkeypatch):
    job = json.loads(
        (
            Path(__file__).parents[2] / "frontend/tests/fixture_job_result.json"
        ).read_text(encoding="utf-8")
    )
    path = tmp_path / "jobs.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY, payload TEXT)")
        db.execute("CREATE TABLE freezes (job_id TEXT PRIMARY KEY, payload TEXT)")
        db.execute("INSERT INTO jobs VALUES (?,?)", (job["id"], json.dumps(job)))
        db.execute("INSERT INTO freezes VALUES (?,?)", (job["id"], "unchanged"))

    def forbidden(*args, **kwargs):
        raise AssertionError("Dashboard must not initialize runtime or store")

    monkeypatch.setattr(ExperimentStore, "__init__", forbidden)
    app = create_app(experiment_store_path=path, runtime_factory=forbidden)
    return path, job, app


def test_history_and_results_are_select_only(saved_dashboard):
    path, job, app = saved_dashboard
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with TestClient(app) as client:
        history = client.get("/api/v1/analysis/experiments?limit=20&offset=0")
        assert history.status_code == 200
        assert history.headers["cache-control"] == "no-store"
        summary = history.json()["jobs"][0]
        assert summary["id"] == job["id"]
        assert "observations" not in summary and "result" not in summary
        assert "expected_answer" not in history.text
        result = client.get(f"/api/v1/analysis/experiments/{job['id']}")
        assert result.status_code == 200
        assert result.json() == JobResults.model_validate(job).model_dump(mode="json")
        assert result.headers["cache-control"] == "no-store"
        assert client.get("/api/v1/analysis/experiments?offset=1").json() == {
            "jobs": []
        }
        assert not hasattr(app.state, "experiment_jobs")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert sorted(p.name for p in path.parent.iterdir()) == [path.name]


def test_unprovisioned_store_is_empty_not_created(tmp_path):
    path = tmp_path / "absent" / "db.sqlite"
    with TestClient(create_app(experiment_store_path=path)) as client:
        response = client.get("/api/v1/analysis/experiments")
        assert response.status_code == 200 and response.json() == {"jobs": []}
    assert not path.parent.exists()


def test_interrupted_job_is_not_recovered(saved_dashboard):
    path, job, app = saved_dashboard
    job.update(status="running", observations=[], result=None, observed_run_count=0)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE jobs SET payload=?", (json.dumps(job),))
    before = path.read_bytes()
    with TestClient(app) as client:
        assert (
            client.get("/api/v1/analysis/experiments").json()["jobs"][0]["status"]
            == "running"
        )
        response = client.get(f"/api/v1/analysis/experiments/{job['id']}")
        assert response.status_code == 200 and response.json()["result"] is None
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "suffix", ["?limit=0", "?limit=51", "?offset=-1", "?offset=100001"]
)
def test_history_bounds(saved_dashboard, suffix):
    _, _, app = saved_dashboard
    with TestClient(app) as client:
        assert client.get("/api/v1/analysis/experiments" + suffix).status_code == 422


@pytest.mark.parametrize("origin", ["https://evil.example", "http://localhost:9999"])
def test_external_origin_rejected(saved_dashboard, origin):
    _, job, app = saved_dashboard
    with TestClient(app) as client:
        for route in ("", f"/{job['id']}"):
            response = client.get(
                "/api/v1/analysis/experiments" + route, headers={"Origin": origin}
            )
            assert response.status_code == 403
            assert response.headers.get("access-control-allow-origin") != origin


@pytest.mark.parametrize("change", ["test", "empirical", "ids", "snapshot", "gold"])
def test_invalid_saved_identity_is_not_exposed(saved_dashboard, change):
    path, job, app = saved_dashboard
    if change == "test":
        job["configuration"]["split"] = "test"
    elif change == "empirical":
        job["empirical_evaluation"] = True
    elif change == "ids":
        job["configuration"]["question_ids"] = ["q_secret_test"]
    elif change == "snapshot":
        job["result"]["selected_question_ids"] = ["synthetic_dev_04"]
    else:
        job["observations"][0]["gold"]["split"] = "test"
    with sqlite3.connect(path) as db:
        db.execute("UPDATE jobs SET payload=?", (json.dumps(job),))
    with TestClient(app) as client:
        response = client.get(f"/api/v1/analysis/experiments/{job['id']}")
        assert response.status_code == 422
        assert "q_secret_test" not in response.text
        assert "Traceback" not in response.text


def test_missing_corrupt_and_wal_records_fail_safely(saved_dashboard):
    path, _, app = saved_dashboard
    with TestClient(app) as client:
        assert client.get(f"/api/v1/analysis/experiments/{uuid4()}").status_code == 404
        assert client.get("/api/v1/analysis/experiments/not-uuid").status_code == 422
        with sqlite3.connect(path) as db:
            db.execute("UPDATE jobs SET payload='not-json'")
        response = client.get("/api/v1/analysis/experiments")
        assert response.status_code == 503
        assert "not-json" not in response.text
        with sqlite3.connect(path) as db:
            db.execute("PRAGMA journal_mode=WAL")
        before = path.read_bytes()
        assert client.get("/api/v1/analysis/experiments").status_code == 422
        assert path.read_bytes() == before


def test_saved_metadata_credentials_are_redacted_without_rewriting(saved_dashboard):
    path, job, app = saved_dashboard
    job["configuration"]["api_key"] = "never-expose-this-value"
    with sqlite3.connect(path) as db:
        db.execute("UPDATE jobs SET payload=?", (json.dumps(job),))
    before = path.read_bytes()
    with TestClient(app) as client:
        for suffix in ("", f"/{job['id']}"):
            response = client.get("/api/v1/analysis/experiments" + suffix)
            assert response.status_code == 200
            assert "never-expose-this-value" not in response.text
            assert "<redacted>" in response.text
    assert path.read_bytes() == before


@pytest.mark.parametrize("limit,offset", [(True, 0), (1, True), (0, 0), (1, -1)])
def test_direct_reader_bounds(tmp_path, limit, offset):
    with pytest.raises(ValueError):
        read_analysis_history(tmp_path / "missing", limit, offset)
