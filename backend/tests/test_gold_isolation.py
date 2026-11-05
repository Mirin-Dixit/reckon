"""Inference consumes documents; gold loading belongs to evaluation only.

These guards cover the supported application path, not arbitrary trusted Python
callbacks, dynamic imports, or malicious code running inside the same process.
"""

import ast
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest
from app.api import dependencies
from app.api.main import create_app
from app.api.models import QueryRequest
from app.generation.contracts import GenerationResponse, ProviderMetadata
from app.generation.policies import (
    AlwaysAnswerPolicy,
    PromptAbstentionPolicy,
    ThresholdAbstentionPolicy,
)
from app.ingestion.schema import ValidationError
from fastapi.testclient import TestClient


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    text = "Procurement requests require manager approval."
    document = {
        "id": "r1-doc", "title": "Procurement", "text": text,
        "source_url": "https://example.test/procurement",
    }
    question = {
        "id": "r1-question", "question": "What approval is required?",
        "is_answerable": True, "question_type": "single_fact", "split": "dev",
        "absence_note": None, "unanswerable_category": None,
        "expected_answer": "GOLD_ANSWER_SENTINEL",
        "expected_safe_behavior": "GOLD_BEHAVIOR_SENTINEL",
        "evidence_spans": [{
            "id": f"{document['id']}_s0_{len(text)}",
            "doc_id": document["id"], "text": text,
            "start_char": 0, "end_char": len(text),
        }],
    }
    documents = tmp_path / "documents.jsonl"
    questions = tmp_path / "questions.jsonl"
    documents.write_text(json.dumps(document) + "\n", encoding="utf-8")
    questions.write_text(json.dumps(question) + "\n", encoding="utf-8")
    monkeypatch.setattr(dependencies, "DOCUMENTS_PATH", documents)
    monkeypatch.setattr(dependencies, "QUESTIONS_PATH", questions)
    monkeypatch.delenv("RECKON_MODEL", raising=False)
    return documents, questions


def forbid_question_reads(monkeypatch, questions):
    original_open, original_read_bytes = Path.open, Path.read_bytes

    def guard_open(path, *args, **kwargs):
        assert path != questions, "Query path tried to open benchmark questions"
        return original_open(path, *args, **kwargs)

    def guard_read_bytes(path, *args, **kwargs):
        assert path != questions, "Query path tried to read benchmark questions"
        return original_read_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard_open)
    monkeypatch.setattr(Path, "read_bytes", guard_read_bytes)


@pytest.mark.parametrize("unavailable", ["missing", "unreadable"])
def test_health_and_query_do_not_require_or_read_questions(
    corpus, monkeypatch, unavailable
):
    _, questions = corpus
    if unavailable == "missing":
        questions.unlink()  # This test owns its temporary fixture only.
    forbid_question_reads(monkeypatch, questions)
    with TestClient(create_app(evaluation_authorizer=lambda: None)) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["runtime_initialized"] is True
        query = client.post("/api/v1/query", json={
            "question": "procurement approval",
            "policy": {
                "name": "threshold", "score_type": "bm25", "threshold": 1_000_000,
            },
        })
        assert query.status_code == 200, query.text
        assert query.json()["decision"] == "ABSTAIN"
        assert query.json()["retrieved_evidence"]


@pytest.mark.parametrize("invalid", ["malformed_json", "duplicate_document_id"])
def test_documents_only_runtime_preserves_validation(corpus, invalid):
    documents, _ = corpus
    original = documents.read_text(encoding="utf-8")
    documents.write_text(
        "{not-json\n" if invalid == "malformed_json" else original + original,
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        dependencies.RuntimeService.from_environment()


class RecordingProvider:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        evidence = json.loads(request.user_content)["evidence"][0]
        if request.structured_output.name == "rag_decision":
            payload = {
                "decision": "ANSWER", "reason": "The passage supports an answer.",
                "reason_code": "other",
                "supporting_evidence_ids": [evidence["evidence_id"]],
                "self_assessment": 0.75,
                "clarification_question": None,
            }
        else:
            payload = {
                "answer": "Manager approval is required.",
                "unsupported_premises": [], "contradictions": [],
                "citations": [{
                    "claim": "Manager approval is required.",
                    "evidence_id": evidence["evidence_id"],
                    "quote": evidence["text"],
                }],
            }
        return GenerationResponse(
            content=json.dumps(payload), structured_content=payload,
            metadata=ProviderMetadata("mock", request.model),
        )


@pytest.mark.parametrize("name", ["always_answer", "prompt_abstention", "threshold"])
def test_gold_does_not_enter_any_query_policy_or_generation_prompt(
    corpus, monkeypatch, name
):
    _, questions = corpus
    forbid_question_reads(monkeypatch, questions)
    policy_calls = []
    for policy_type in (AlwaysAnswerPolicy, PromptAbstentionPolicy,
                        ThresholdAbstentionPolicy):
        original = policy_type.decide

        def capture(self, question, assessment, evidence, decide=original):
            policy_calls.append({
                "question": question, "assessment": asdict(assessment),
                "evidence": [asdict(item) for item in evidence],
            })
            return decide(self, question, assessment, evidence)

        monkeypatch.setattr(policy_type, "decide", capture)
    runtime = dependencies.RuntimeService.from_environment()
    runtime.provider = provider = RecordingProvider()
    policy = {"name": name}
    if name == "threshold":
        policy.update(score_type="bm25", threshold=0)
    try:
        result = runtime.execute_query(QueryRequest.model_validate({
            "question": "What procurement approval is required?",
            "policy": policy, "generation": {"model": "offline-test-model"},
        }))
        assert result.decision.value == "ANSWER"
        assert result.execution_status.value == "succeeded"
        assert len(policy_calls) == 1
        assert provider.requests
        captured = json.dumps(policy_calls) + json.dumps([
            {"system": req.system_instruction, "user": req.user_content}
            for req in provider.requests
        ])
        for forbidden in ("GOLD_", "expected_answer", "expected_safe_behavior",
                          "is_answerable", "unanswerable_category", "evidence_spans"):
            assert forbidden not in captured
        for request in provider.requests:
            assert set(json.loads(request.user_content)) == {"question", "evidence"}
    finally:
        runtime.close()


def test_evaluation_still_loads_gold_and_records_exact_snapshot_fingerprints(corpus):
    documents, questions = corpus
    expected = {
        "documents_sha256": hashlib.sha256(documents.read_bytes()).hexdigest(),
        "questions_sha256": hashlib.sha256(questions.read_bytes()).hexdigest(),
    }
    with TestClient(create_app(evaluation_authorizer=lambda: None)) as client:
        started = client.post("/api/v1/evaluations", json={
            "split": "dev", "policies": [{
                "name": "threshold", "score_type": "bm25", "threshold": 1_000_000,
            }],
        })
        assert started.status_code == 200, started.text
        identifier = started.json()["experiment_id"]
        reply = client.get(f"/api/v1/evaluations/{identifier}/results")
        assert reply.status_code == 200
        experiment = reply.json()["experiment"]
        assert experiment["dataset_fingerprint"] == expected
        assert experiment["runs"][0]["gold"]["expected_answer"] == (
            "GOLD_ANSWER_SENTINEL"
        )
        assert experiment["runs"][0]["observed"]["decision"] == "ABSTAIN"


GOLD_LOADERS = {
    "load_dataset", "load_dataset_snapshot", "load_questions_from_jsonl",
}


def prohibited_gold_access(source, *, evaluation_adapter=False):
    """Catch ordinary imports, aliases and module-qualified loader calls.

    Evaluation orchestration is permitted only in its named API adapter method.
    This deliberately does not pretend to sandbox reflection or arbitrary code.
    """
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree)
               for child in ast.iter_child_nodes(node)}
    violations = []
    runner_names = {"EvaluationRunner"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for item in node.names:
                if module.endswith("evaluation.runner") and (
                    item.name == "EvaluationRunner"
                ):
                    runner_names.add(item.asname or item.name)
                if module.endswith(("ingestion.loader", "ingestion.schema")) or (
                    module in {"loader", "schema", "app.ingestion", "ingestion"}
                ):
                    if item.name in GOLD_LOADERS | {"Question", "*"}:
                        violations.append(node.lineno)
        if not isinstance(node, ast.Call):
            continue
        name = (node.func.id if isinstance(node.func, ast.Name)
                else node.func.attr if isinstance(node.func, ast.Attribute) else "")
        if name in GOLD_LOADERS or name == "Question":
            violations.append(node.lineno)
        if name == "from_dict" and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            owner_name = (owner.id if isinstance(owner, ast.Name)
                          else owner.attr if isinstance(owner, ast.Attribute) else "")
            if owner_name == "Question":
                violations.append(node.lineno)
        if name in runner_names:
            parent = parents.get(node)
            while parent is not None and not isinstance(parent, ast.FunctionDef):
                parent = parents.get(parent)
            if not (evaluation_adapter and parent is not None
                    and parent.name == "evaluation_runner"):
                violations.append(node.lineno)
    return violations


def test_inference_modules_cannot_import_or_call_gold_loaders():
    root = Path("backend/app")
    evaluation_routes = {"api/routes/experiments.py", "api/routes/evaluation.py"}
    for directory in ("retrieval", "generation", "api"):
        for path in (root / directory).rglob("*.py"):
            relative = path.relative_to(root).as_posix()
            if relative in evaluation_routes:
                continue
            violations = prohibited_gold_access(
                path.read_text(encoding="utf-8-sig"),
                evaluation_adapter=relative == "api/dependencies.py",
            )
            assert not violations, f"Gold loading in {relative}: lines {violations}"


@pytest.mark.parametrize("source", [
    "from app.ingestion.loader import load_dataset as read_gold",
    "from app.ingestion.loader import *",
    "import app.ingestion.loader as data; data.load_dataset_snapshot('d', 'q')",
    "from app.ingestion import loader as data; data.load_questions_from_jsonl('q')",
    "from app.ingestion.schema import Question as GoldQuestion",
    "from app.ingestion import Question as GoldQuestion",
    "from ..ingestion.loader import load_questions_from_jsonl as read_gold",
    "import app.ingestion.schema as data; data.Question.from_dict({})",
    "def from_environment():\n    return EvaluationRunner('d', 'q')",
])
def test_architectural_guard_detects_prohibited_access(source):
    assert prohibited_gold_access(source, evaluation_adapter=True)


def test_architectural_guard_allows_documents_and_explicit_evaluation_adapter():
    source = (
        "from app.ingestion.loader import load_documents_from_jsonl\n"
        "from app.evaluation.runner import EvaluationRunner as Runner\n"
        "def from_environment():\n    return load_documents_from_jsonl('d')\n"
        "def evaluation_runner():\n    return Runner('d', 'q')\n"
    )
    assert prohibited_gold_access(source)
    assert not prohibited_gold_access(source, evaluation_adapter=True)
