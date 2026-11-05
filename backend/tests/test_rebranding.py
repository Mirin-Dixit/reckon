"""Brand metadata and legacy settings remain independent of research contracts."""

import json
from pathlib import Path

import pytest
from app.api.dependencies import ApiSettings
from app.api.main import create_app
from app.configuration import environment
from app.generation.config import load_provider_config
from fastapi.testclient import TestClient


@pytest.mark.parametrize("suffix", ["MODEL", "CORS_ORIGINS", "DENSE_CACHE_DIR",
                                   "EXPERIMENT_STORE_PATH", "OLLAMA_URL"])
def test_environment_alias_precedence_and_no_mutation(suffix):
    legacy, current = "RAGBENCH_" + suffix, "RECKON_" + suffix
    values = {legacy: "old"}
    assert environment(values)[current] == "old"
    assert values == {legacy: "old"}
    assert environment({**values, current: "new"})[current] == "new"
    assert environment({**values, current: ""})[current] == ""


def test_legacy_provider_and_api_configuration():
    assert load_provider_config({"RAGBENCH_MODEL": "qwen3:4b-q4_K_M"}).model == (
        "qwen3:4b-q4_K_M"
    )
    settings = ApiSettings.from_env({
        "RAGBENCH_CORS_ORIGINS": "http://127.0.0.1:3000",
    })
    assert settings.cors_origins == (
        "http://127.0.0.1:3000",
    )


def test_reckon_api_metadata_and_no_gold_initialization(tmp_path):
    def forbidden():
        raise AssertionError("No model or gold loading")
    app = create_app(runtime_factory=forbidden,
                     experiment_store_path=tmp_path / "absent.sqlite3")
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["application"] == "Reckon"
        assert client.get("/api/v1/openapi.json").json()["info"]["title"] == "Reckon"
    assert not (tmp_path / "absent.sqlite3").exists()


def test_legacy_volume_is_external_and_not_recreated():
    root = Path(__file__).resolve().parents[2]
    config = json.loads((root / "compose.legacy-state.yaml").read_text())
    assert config["volumes"]["state"] == {
        "external": True, "name": "ragbench-p6-check_state",
    }
    assert json.loads((root / "compose.yaml").read_text())["name"] == "reckon"
