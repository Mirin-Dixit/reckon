"""Real loopback HTTP; disposable synthetic storage and mocked model transports."""

import json
import os
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / "backend"), str(root / "backend/tests")]
import uvicorn  # noqa: E402
from app.api.dependencies import ApiSettings  # noqa: E402
from app.api.main import create_app  # noqa: E402
from test_retrieval_http import environment  # noqa: E402
from test_retrieval_http import request as query_request  # noqa: E402


@contextmanager
def server(app):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    service = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="error",
            ws="none",
        )
    )
    thread = threading.Thread(target=service.run, daemon=True)
    thread.start()
    try:
        for _ in range(200):
            if service.started:
                break
            if not thread.is_alive():
                raise RuntimeError("Test server exited")
            time.sleep(0.05)
        else:
            raise RuntimeError("Test server startup timed out")
        yield f"http://127.0.0.1:{port}"
    finally:
        service.should_exit = True
        thread.join(timeout=10)
        if thread.is_alive():
            raise RuntimeError("Test server did not stop")


packets = {}


def http(
    base,
    name,
    path,
    body=None,
    method=None,
    origin="http://127.0.0.1:3000",
    headers=None,
):
    supplied = {"Origin": origin, **(headers or {})}
    if body is not None:
        supplied["Content-Type"] = "application/json"
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers=supplied,
    )
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read()
        packet = dict(
            status=response.status,
            cors=response.headers.get("Access-Control-Allow-Origin"),
            body=json.loads(raw) if raw.startswith(b"{") else None,
        )
    packets[name] = packet
    return packet


def wait_job(base, job_id):
    for _ in range(150):
        data = http(base, "poll", f"/api/v1/experiments/{job_id}/results")["body"]
        if data["status"] not in ("queued", "running"):
            return data
        time.sleep(0.05)
    raise RuntimeError("Synthetic job did not finish")


with tempfile.TemporaryDirectory(
    prefix="wui-", dir=os.environ.get("TEMP")
) as temporary:
    scratch = Path(temporary)
    runtime, _, transport, provider = environment.__wrapped__(scratch)
    settings = ApiSettings(cors_origins=("http://127.0.0.1:3000",))
    app = create_app(
        settings=settings,
        runtime_factory=lambda: runtime,
        experiment_store_path=scratch / "synthetic.sqlite",
    )
    with server(app) as base:
        http(base, "health", "/api/v1/health")
        http(
            base,
            "preflight",
            "/api/v1/experiments",
            method="OPTIONS",
            headers={
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        http(
            base,
            "external",
            "/api/v1/experiments",
            body={},
            origin="https://evil.example",
        )
        for method in ("bm25", "dense", "hybrid"):
            for policy in ("always_answer", "threshold", "prompt_abstention"):
                http(
                    base,
                    f"query-{method}-{policy}",
                    "/api/v1/query",
                    query_request(method, policy),
                )
        http(
            base,
            "invalid-query",
            "/api/v1/query",
            dict(question="", policy=dict(name="always_answer")),
        )
        body = dict(
            split="dev",
            retrieval=dict(method="bm25", top_k=3),
            policies=[
                dict(name="always_answer"),
                dict(name="prompt_abstention"),
                dict(name="threshold", threshold=0, score_type="bm25"),
            ],
        )
        started = http(base, "start", "/api/v1/experiments", body)["body"]
        job_id = started["id"]
        packets["completed"] = dict(status=200, body=wait_job(base, job_id))
        http(base, "history", "/api/v1/experiments?limit=50&offset=0")
        http(base, "metadata", f"/api/v1/experiments/{job_id}")
        http(base, "freeze", f"/api/v1/experiments/{job_id}/freeze", {})
        http(base, "freeze-again", f"/api/v1/experiments/{job_id}/freeze", {})
        http(
            base,
            "analysis",
            f"/api/v1/experiments/{job_id}/analysis?lexical_proxy=true",
        )
        http(
            base,
            "analysis-again",
            f"/api/v1/experiments/{job_id}/analysis?lexical_proxy=true",
        )
        http(
            base,
            "analysis-threshold",
            f"/api/v1/experiments/{job_id}/analysis?threshold_only=true&lexical_proxy=true",
        )
        http(
            base,
            "analysis-invalid",
            f"/api/v1/experiments/{job_id}/analysis?resamples=5001",
        )
        body.update(split="train", question_ids=["synthetic_train_04"])
        failed = http(base, "start-failure", "/api/v1/experiments", body)["body"]["id"]
        packets["failed"] = dict(status=200, body=wait_job(base, failed))
        http(base, "failed-freeze", f"/api/v1/experiments/{failed}/freeze", {})
        packets.pop("poll", None)
    packets["runtime"] = dict(
        status=200,
        body=dict(
            provider="mock",
            embedding_transport="mock",
            external_inference=False,
            generation_calls=len(provider.calls),
            embedding_calls=len(transport.calls),
        ),
    )
json.dump(packets, sys.stdout)
