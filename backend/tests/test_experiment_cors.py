"""Real loopback browser preflight regression; synthetic fixtures only."""

import json
import socket
import threading
import time
from contextlib import contextmanager
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
import uvicorn
from app.api.dependencies import ApiSettings
from app.api.main import create_app

ORIGIN = "http://127.0.0.1:3000"
PAYLOAD = {
    "profile": "p4-synthetic.v1",
    "split": "train",
    "question_ids": ["synthetic_train_01"],
    "retrieval": {"method": "bm25", "top_k": 3},
    "policies": [{"name": "always_answer"}],
}


@contextmanager
def local_server(tmp_path, *, configured=True):
    def no_query_runtime():
        raise AssertionError("Synthetic experiments must not initialize live inference")

    app = create_app(
        settings=ApiSettings.from_env(
            {"RECKON_CORS_ORIGINS": ORIGIN} if configured else {}
        ),
        runtime_factory=no_query_runtime,
        experiment_store_path=tmp_path / "cors.sqlite",
    )
    server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        base = f"http://127.0.0.1:{listener.getsockname()[1]}"
        worker = threading.Thread(target=server.run, kwargs={"sockets": [listener]},
                                  daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and worker.is_alive():
                assert time.monotonic() < deadline
                time.sleep(.01)
            assert server.started
            yield base, app
        finally:
            server.should_exit = True
            worker.join(timeout=10)
            assert not worker.is_alive()


def http(base, method, *, origin=ORIGIN, body=None, **headers):
    try:
        reply = urlopen(Request(
            base + "/api/v1/experiments", method=method,
            headers={**({"Origin": origin} if origin is not None else {}), **headers},
            data=json.dumps(body).encode() if body is not None else None,
        ), timeout=10)
    except HTTPError as error:
        reply = error
    with reply:
        return reply.status, reply.headers, reply.read().decode()


def test_missing_cors_configuration_reproduces_405(tmp_path):
    with local_server(tmp_path, configured=False) as (base, _):
        assert http(base, "GET", origin=None)[0] == 200
        status, headers, body = http(base, "OPTIONS", **{
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert status == 405
        assert headers.get("Access-Control-Allow-Origin") is None
        assert json.loads(body)["error"]["code"] == "method_not_allowed"


def test_configured_experiment_preflight_post_and_history(tmp_path):
    with local_server(tmp_path) as (base, _):
        status, headers, _ = http(base, "OPTIONS", **{
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert status == 200
        assert headers["Access-Control-Allow-Origin"] == ORIGIN
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert headers.get("Access-Control-Allow-Credentials") is None
        status, headers, body = http(base, "POST", body=PAYLOAD,
                                     **{"Content-Type": "application/json"})
        assert status == 202, body
        assert headers["Access-Control-Allow-Origin"] == ORIGIN
        assert headers.get("Access-Control-Allow-Credentials") is None
        job = json.loads(body)
        assert job["empirical_evaluation"] is False
        status, headers, body = http(base, "GET")
        assert status == 200
        assert headers["Access-Control-Allow-Origin"] == ORIGIN
        assert job["id"] in {row["id"] for row in json.loads(body)["jobs"]}
        status, headers, body = http(base, "POST", body={**PAYLOAD, "split": "test"},
                                     **{"Content-Type": "application/json"})
        assert status == 422
        assert headers["Access-Control-Allow-Origin"] == ORIGIN
        assert json.loads(body)["error"]["code"] == "invalid_request"


@pytest.mark.parametrize("origin", [
    "https://unexpected.example", "http://127.0.0.1:3001",
    "http://127.0.0.1.evil.example:3000",
])
def test_unauthorized_origin_cannot_preflight_or_submit(tmp_path, origin):
    with local_server(tmp_path) as (base, app):
        status, headers, _ = http(base, "OPTIONS", origin=origin, **{
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert status == 400
        assert headers.get("Access-Control-Allow-Origin") is None
        assert headers.get("Access-Control-Allow-Credentials") is None
        status, headers, body = http(base, "POST", origin=origin, body=PAYLOAD,
                                     **{"Content-Type": "application/json"})
        assert status == 403, body
        assert headers.get("Access-Control-Allow-Origin") is None
        assert json.loads(body)["error"]["code"] == "local_only"
        assert getattr(app.state, "experiment_jobs", None) is None
