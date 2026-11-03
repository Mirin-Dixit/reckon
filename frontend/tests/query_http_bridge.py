"""Test-only ASGI bridge: actual FastAPI routes, existing deterministic runtime double.

No sockets, benchmark loading or real embedding/generation calls.
JSON packets on stdin/stdout.
"""

import json
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / "backend"), str(root / "backend/tests")]
from app.generation.contracts import Decision, ExecutionStatus  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from test_api import FakeRuntime, client, make_result  # noqa: E402
from test_retrieval_http import environment  # noqa: E402

packets = []
for index, case in enumerate(json.load(sys.stdin)):
    scratch = tempfile.TemporaryDirectory(dir=root / "frontend/.test-build")
    provider = None
    status = (
        ExecutionStatus.FAILED
        if case["outcome"] == "EXECUTION_FAILURE"
        else ExecutionStatus.SUCCEEDED
    )
    runtime = FakeRuntime(
        make_result(
            Decision.ABSTAIN
            if status is ExecutionStatus.FAILED
            else Decision(case["outcome"]),
            status=status,
        )
    )
    if index < 9:
        runtime, app, _, provider = environment.__wrapped__(Path(scratch.name))
    else:
        app = None
    observed = []
    original = runtime.execute_query

    def execute(request):
        observed.append(request.model_dump(mode="json"))
        return original(request)

    runtime.execute_query = execute
    with TestClient(app) if app is not None else client(runtime) as http:
        response = http.post("/api/v1/query", json=case["request"])
        packets.append(
            {
                "status": response.status_code,
                "body": response.json(),
                "observed": observed,
                "prompts": [json.loads(call.user_content) for call in provider.calls]
                if provider
                else [],
            }
        )
    scratch.cleanup()
json.dump(packets, sys.stdout)
