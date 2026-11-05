"""Local transport boundaries, bounded uploads and side-effect-free configuration."""

import asyncio
import json

import pytest
from app.api.dependencies import ApiSettings
from app.api.main import create_app
from app.api.middleware import RequestBodyLimitMiddleware
from fastapi.testclient import TestClient


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), 61])
def test_invalid_body_deadline_is_rejected(value):
    with pytest.raises(ValueError, match="deadline"):
        ApiSettings(request_body_timeout_seconds=value)


@pytest.mark.parametrize("trickle", [False, True])
def test_stalled_or_trickling_upload_is_bounded_before_runtime(trickle):
    async def run():
        messages = []

        async def forbidden(scope, receive, send):
            raise AssertionError("Runtime must not receive incomplete request")

        async def receive():
            await asyncio.sleep(0.01 if trickle else 10)
            return {"type": "http.request", "body": b"x", "more_body": True}

        async def send(message):
            messages.append(message)

        app = RequestBodyLimitMiddleware(forbidden, 1024, timeout_seconds=0.03)
        await asyncio.wait_for(
            app({"type": "http", "headers": []}, receive, send), timeout=1
        )
        assert messages[0]["status"] == 408
        assert (b"connection", b"close") in messages[0]["headers"]
        assert json.loads(messages[1]["body"])["error"]["code"] == (
            "request_body_timeout"
        )

    asyncio.run(run())


@pytest.mark.parametrize(
    "route,method",
    [
        ("/query", "POST"),
        ("/evaluations", "POST"),
        ("/evaluations/unknown/results", "GET"),
    ],
)
@pytest.mark.parametrize("remote", [False, True])
def test_legacy_routes_reject_foreign_origins_and_remote_clients(route, method, remote):
    def forbidden():
        raise AssertionError("No runtime initialization")

    app = create_app(runtime_factory=forbidden)
    client_address = ("198.51.100.2", 1234) if remote else ("testclient", 50000)
    with TestClient(app, client=client_address) as client:
        response = client.request(
            method,
            "/api/v1" + route,
            headers={} if remote else {"Origin": "https://evil.example"},
            json={"question": "hello"} if method == "POST" else None,
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "local_only"


def test_environment_storage_path_does_not_initialize_or_create_store(
    tmp_path, monkeypatch
):
    path = tmp_path / "new-state" / "jobs.sqlite"
    monkeypatch.setenv("RECKON_EXPERIMENT_STORE_PATH", str(path))
    app = create_app()
    assert app.state.experiment_store_path == path
    with TestClient(app) as client:
        assert client.get("/api/v1/analysis/experiments").json() == {"jobs": []}
        assert (
            "408"
            in client.get("/api/v1/openapi.json").json()["paths"]["/api/v1/query"][
                "post"
            ]["responses"]
        )
    assert not path.parent.exists()
    monkeypatch.setenv("RECKON_EXPERIMENT_STORE_PATH", "relative.sqlite")
    with pytest.raises(ValueError, match="absolute"):
        create_app()
