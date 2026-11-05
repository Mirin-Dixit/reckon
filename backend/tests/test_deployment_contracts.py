"""Offline deployment contracts, not a substitute for Docker runtime testing."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_compose_is_local_nonroot_bounded_and_preserves_loopback_guards():
    # JSON is a YAML subset; no extra parser dependency is needed for these checks.
    config = json.loads((ROOT / "compose.yaml").read_text())
    services = config["services"]
    assert set(services) == {"backend", "frontend", "gateway", "app-proxy"}
    assert config["networks"]["local"]["internal"] is True
    assert services["gateway"]["ports"] == ["127.0.0.1:3000:8080"]
    assert services["backend"]["networks"] == ["local"]
    assert services["gateway"]["networks"] == ["ingress", "local"]
    assert services["gateway"].get("network_mode") is None
    for name, service in services.items():
        assert service["read_only"] and service["init"]
        assert service["cap_drop"] == ["ALL"]
        assert "no-new-privileges:true" in service["security_opt"]
        assert service["mem_limit"] and service["pids_limit"]
        dockerfile = (ROOT / service["build"]["dockerfile"]).read_text()
        assert re.search(r"^USER (node|10001:10001)$", dockerfile, re.M)
        assert "HEALTHCHECK" in dockerfile
        assert re.search(r"@sha256:[a-f0-9]{64}", dockerfile)
        if name in ("frontend", "app-proxy"):
            assert service["network_mode"] == "service:backend"
            assert "ports" not in service
    backend = services["backend"]
    assert backend["environment"]["RAGBENCH_PROVIDER"] == "ollama"
    assert backend["environment"]["RAGBENCH_RETRY_COUNT"] == "0"
    assert backend["environment"]["RAGBENCH_EXPERIMENT_STORE_PATH"].startswith(
        "/state/"
    )
    assert backend["volumes"][0] == "state:/state"
    assert '"--no-access-log"' in (ROOT / "backend/Dockerfile").read_text()
    assert "ports" not in backend
    assert all(mount.endswith(":ro") for mount in backend["volumes"][1:])
    assert not any("questions.jsonl" in mount for mount in backend["volumes"])


def test_build_context_and_runtime_lock_exclude_sensitive_and_unrelated_files():
    ignore = (ROOT / ".dockerignore").read_text()
    rules = [line for line in ignore.splitlines() if line and not line.startswith("#")]
    assert rules[0] == "**"
    for forbidden in ("**/.env*", "**/*.sqlite*", "**/.git", "**/node_modules"):
        assert forbidden in rules
    assert not any(line.startswith("!data") for line in rules)
    assert "backend/app/evaluation/review_ui" in rules
    locked = (ROOT / "deploy/requirements-server.lock").read_text()
    packages = [
        line for line in locked.splitlines() if line and not line.startswith("#")
    ]
    assert all(re.fullmatch(r"[a-z0-9-]+==[0-9.]+", line) for line in packages)
    assert not any("openai" in line or "pytest" in line for line in packages)
    frontend = (ROOT / "frontend/Dockerfile").read_text()
    assert "npm ci" in frontend and ".next/standalone" in frontend
    assert "NEXT_TELEMETRY_DISABLED=1" in frontend
    assert "RAGBENCH_STANDALONE=1" in frontend
    assert 'process.env.RAGBENCH_STANDALONE === "1"' in (
        ROOT / "frontend/next.config.ts"
    ).read_text()


def test_gateway_has_fixed_upstreams_no_forwarded_identity_and_safe_limits():
    gateway = (ROOT / "deploy/nginx.conf").read_text()
    assert "proxy_pass http://127.0.0.1:8000;" in gateway
    assert "proxy_pass http://127.0.0.1:3000;" in gateway
    assert "proxy_set_header Host $proxy_host;" in gateway
    assert 'proxy_set_header X-Forwarded-For "";' in gateway
    assert "server_name _; return 403;" in gateway
    assert "client_max_body_size 1m;" in gateway
    assert "client_body_timeout 15s;" in gateway
    assert "local_service_unavailable" in gateway
    assert "error_log /dev/null;" in gateway


def test_ingress_preserves_origin_and_only_uses_fixed_private_relay():
    edge = (ROOT / "deploy/ingress.conf").read_text()
    assert "proxy_pass http://backend:8080;" in edge
    assert "proxy_set_header Host 127.0.0.1;" in edge
    assert 'proxy_set_header X-Forwarded-For "";' in edge
    assert "proxy_set_header Origin" not in edge
    assert "server_name _; return 403;" in edge
    assert "client_max_body_size 1m;" in edge
    assert "access_log off;" in edge
    assert "error_log /dev/null;" in edge
    assert "resolver " not in edge


def test_compose_native_validation_if_cli_is_available():
    executable = shutil.which("docker")
    if executable is None:
        pytest.skip(
            "Docker CLI unavailable: runtime/config-engine validation unverified"
        )
    subprocess.run(
        [executable, "compose", "-f", str(ROOT / "compose.yaml"), "config", "--quiet"],
        cwd=ROOT,
        check=True,
        timeout=30,
    )
