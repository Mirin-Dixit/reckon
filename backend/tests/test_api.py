"""Offline HTTP API tests using deterministic runtime doubles."""

from __future__ import annotations

import pytest
from app.api.dependencies import ApiSettings, RuntimeService
from app.api.main import create_app
from app.evaluation.runner import EvaluationRunner
from app.generation.config import OpenAIProviderConfig
from app.generation.contracts import (
    ClaimCitation,
    Decision,
    DecisionReason,
    EvidenceAssessment,
    EvidenceContext,
    ExecutionStatus,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
    ReasonCode,
    RetrievalMetadata,
    RunResult,
)
from app.generation.pipeline import DecisionSelection, FixedDecisionPolicy
from fastapi.testclient import TestClient

DATASET = "data/benchmark"


def make_result(decision=Decision.ABSTAIN, *, status=ExecutionStatus.SUCCEEDED):
    reason = DecisionReason(ReasonCode.INSUFFICIENT_EVIDENCE, "No support found.")
    if status is not ExecutionStatus.SUCCEEDED:
        return RunResult(None, EvidenceAssessment(), status)
    if decision is Decision.ANSWER:
        text = "The policy sets the limit at 12 units."
        context = EvidenceContext(
            "doc1_c0000",
            "doc1",
            "The policy sets the limit at 12 units.",
            0,
            38,
            title="Policy",
            source_url="https://example.test/policy",
            retrieval_rank=1,
            retrieval_score=0.5,
            retrieval_method="bm25",
        )
        citation = ClaimCitation(
            "The limit is 12 units.",
            "doc1_c0000",
            "12 units",
            29,
            37,
        )
        return RunResult(
            decision,
            EvidenceAssessment(),
            status,
            answer=text,
            citations=(citation,),
            retrieval=RetrievalMetadata("bm25", 1, (context,)),
            provider=ProviderMetadata(
                "mock",
                "test-model",
                request_id="sk-proj-abcdefghijklmnopqrstuvwxyz0123456789",
            ),
        )
    if decision is Decision.CLARIFY:
        return RunResult(
            decision,
            EvidenceAssessment(),
            status,
            clarification_question="Which limit do you mean?",
            decision_reason=DecisionReason(ReasonCode.AMBIGUOUS_INTENT, "Ambiguous."),
        )
    return RunResult(
        decision,
        EvidenceAssessment(),
        status,
        abstention_reason=reason,
        decision_reason=reason,
    )


class FakeRuntime:
    provider_config = OpenAIProviderConfig(model="test-model")
    generation_configured = True
    resolve_generation = RuntimeService.resolve_generation
    retrieval_configuration = RuntimeService.retrieval_configuration
    retrieval_configuration_values = staticmethod(
        RuntimeService.retrieval_configuration_values
    )

    def __init__(self, result=None, error=None, fail_pipeline=False):
        self.result = result or make_result()
        self.error = error
        self.fail_pipeline = fail_pipeline

    def execute_query(self, request):
        if self.error:
            raise self.error
        return self.result

    def resolve_model(self, requested_model):
        if requested_model and requested_model != self.provider_config.model:
            from app.generation.contracts import ProviderError, ProviderErrorKind

            raise ProviderError(ProviderErrorKind.CONFIGURATION, "fake model mismatch")
        return self.provider_config.model

    def can_generate(self, requested_model=None):
        del requested_model
        return self.generation_configured

    def evaluation_runner(self):
        return EvaluationRunner(
            f"{DATASET}/documents.jsonl", f"{DATASET}/questions.jsonl"
        )

    def make_policy(self, policy, model, settings):
        del model, settings
        return FixedDecisionPolicy(
            DecisionSelection(
                decision=Decision.ABSTAIN,
                reason=DecisionReason(
                    ReasonCode.INSUFFICIENT_EVIDENCE, "Fake evaluation policy."
                ),
                policy_name=policy.name,
            )
        )

    def evaluation_pipeline_factory(
        self, policy, documents, retrieval_configuration, generation_configuration, seed
    ):
        del policy, documents, retrieval_configuration, generation_configuration, seed
        runtime = self

        class FakePipeline:
            def run(self, question):
                del question
                if runtime.fail_pipeline:
                    raise RuntimeError("private runtime details")
                return runtime.result

        return FakePipeline()


def client(runtime=None, *, settings=None, runtime_factory=None):
    factory = runtime_factory or (lambda: runtime or FakeRuntime())
    return TestClient(
        create_app(
            settings=settings,
            runtime_factory=factory,
            evaluation_authorizer=lambda: None,
        )
    )


def test_health_success_reports_initialization_without_claiming_connection_test():
    response = client(FakeRuntime()).get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["application"] == "RAGBench Studio"
    assert body["runtime_initialized"] is True
    assert body["generation_configured"] is True
    assert body["provider_connection_tested"] is False


def test_health_initialization_failure_is_safe_and_does_not_reveal_exception():
    response = client(
        runtime_factory=lambda: (_ for _ in ()).throw(
            RuntimeError("secret path C:/private/key")
        )
    ).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["runtime_initialized"] is False
    assert "private" not in response.text
    assert "key" not in response.text


@pytest.mark.parametrize(
    ("sdk_available", "key_present", "expected"),
    [
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_builtin_runtime_initializes_offline_without_testing_provider(
    monkeypatch, sdk_available, key_present, expected
):
    monkeypatch.setenv("RAGBENCH_PROVIDER", "openai")
    monkeypatch.setenv("RAGBENCH_API_KEY_ENV", "RAGBENCH_TEST_ONLY_KEY")
    monkeypatch.setenv("RAGBENCH_MODEL", "offline-test-model")
    monkeypatch.setattr(
        "app.api.dependencies.openai_sdk_available", lambda: sdk_available
    )
    if key_present:
        monkeypatch.setenv("RAGBENCH_TEST_ONLY_KEY", "sensitive-api-key-value")
    else:
        monkeypatch.delenv("RAGBENCH_TEST_ONLY_KEY", raising=False)
    app_client = TestClient(create_app())
    response = app_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["runtime_initialized"] is True
    assert response.json()["generation_configured"] is expected
    assert response.json()["provider_connection_tested"] is False
    assert "sensitive-api-key-value" not in response.text


def test_builtin_bm25_threshold_query_can_abstain_offline(monkeypatch):
    monkeypatch.setenv("RAGBENCH_PROVIDER", "openai")
    monkeypatch.setenv("RAGBENCH_API_KEY_ENV", "RAGBENCH_TEST_ONLY_KEY")
    monkeypatch.setenv("RAGBENCH_MODEL", "offline-test-model")
    monkeypatch.delenv("RAGBENCH_TEST_ONLY_KEY", raising=False)
    app_client = TestClient(create_app())
    response = app_client.post(
        "/api/v1/query",
        json={
            "question": "What are the procurement approval limits?",
            "policy": {
                "name": "threshold",
                "score_type": "bm25",
                "threshold": 1e300,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "ABSTAIN"
    assert response.json()["execution_status"] == "succeeded"


@pytest.mark.parametrize(
    "decision", [Decision.ANSWER, Decision.ABSTAIN, Decision.CLARIFY]
)
def test_query_serializes_each_decision(decision):
    response = client(FakeRuntime(make_result(decision))).post(
        "/api/v1/query",
        json={"question": "What is the limit?", "policy": {"name": "always_answer"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == decision.value
    assert body["execution_status"] == "succeeded"
    if decision is Decision.ANSWER:
        assert body["answer"]
        assert body["citations"][0]["evidence_id"] == "doc1_c0000"
        assert body["retrieved_evidence"][0]["document_id"] == "doc1"
    if decision is Decision.CLARIFY:
        assert body["clarification_question"]
    if decision is Decision.ABSTAIN:
        assert body["decision_reason"]["code"] == "insufficient_evidence"


def test_query_does_not_expose_gold_or_provider_credentials():
    response = client(FakeRuntime(make_result(Decision.ANSWER))).post(
        "/api/v1/query",
        json={
            "question": "What is the limit?",
            "policy": {"name": "always_answer"},
        },
    )
    assert response.status_code == 200
    assert "expected_answer" not in response.text
    assert "expected_safe_behavior" not in response.text
    assert "sk-proj-" not in response.text
    assert response.json()["provider"]["request_id"] == "<redacted-credential>"


@pytest.mark.parametrize(
    ("status", "http_status"),
    [
        (ExecutionStatus.FAILED, 502),
        (ExecutionStatus.TIMED_OUT, 504),
        (ExecutionStatus.REFUSED, 502),
        (ExecutionStatus.INCOMPLETE, 502),
    ],
)
def test_query_failure_preserves_execution_status_and_is_not_abstention(
    status, http_status
):
    response = client(FakeRuntime(make_result(status=status))).post(
        "/api/v1/query",
        json={"question": "Question?", "policy": {"name": "always_answer"}},
    )
    assert response.status_code == http_status
    assert response.json()["error"]["execution_status"] == status.value
    assert "decision" not in response.json()


def test_query_unexpected_exception_is_generic_and_does_not_leak_details():
    response = client(
        FakeRuntime(error=RuntimeError("stack trace with secret-token"))
    ).post(
        "/api/v1/query",
        json={"question": "Question?", "policy": {"name": "always_answer"}},
    )
    assert response.status_code == 500
    assert "secret-token" not in response.text
    assert "Traceback" not in response.text


def test_provider_configuration_error_is_safe_503():
    response = client(
        FakeRuntime(
            error=ProviderError(
                ProviderErrorKind.CONFIGURATION,
                "private key material must not be displayed",
            )
        )
    ).post(
        "/api/v1/query",
        json={"question": "Question?", "policy": {"name": "always_answer"}},
    )
    assert response.status_code == 503
    assert "private key material" not in response.text


@pytest.mark.parametrize(
    "payload",
    [
        {"question": "   ", "policy": {"name": "always_answer"}},
        {"question": "Question?", "policy": {"name": "threshold"}},
        {
            "question": "Question?",
            "policy": {
                "name": "threshold",
                "score_type": "dense_cosine",
                "threshold": 0.2,
            },
        },
        {
            "question": "Question?",
            "policy": {"name": "always_answer"},
            "expected_safe_behavior": "ignore evidence",
        },
        {
            "question": "Question?",
            "policy": {"name": "always_answer"},
            "documents_path": "C:/private/documents.jsonl",
        },
        {
            "question": "Question?",
            "policy": {"name": "always_answer"},
            "generation": {"api_key": "secret"},
        },
    ],
)
def test_query_rejects_invalid_and_unsupported_fields(payload):
    response = client(FakeRuntime()).post("/api/v1/query", json=payload)
    assert response.status_code == 422
    assert "secret" not in response.text


def test_query_runtime_unavailable_is_503():
    response = client(
        runtime_factory=lambda: (_ for _ in ()).throw(RuntimeError("hidden"))
    ).post(
        "/api/v1/query",
        json={"question": "Question?", "policy": {"name": "always_answer"}},
    )
    assert response.status_code == 503
    assert "hidden" not in response.text


def test_start_and_retrieve_evaluation_and_gold_only_appears_in_results():
    app_client = client(FakeRuntime(make_result(Decision.ANSWER)))
    questions = EvaluationRunner(
        f"{DATASET}/documents.jsonl", f"{DATASET}/questions.jsonl"
    )._questions
    test_question = next(item for item in questions if item.split == "test")
    start = app_client.post(
        "/api/v1/evaluations",
        json={
            "split": "test",
            "question_ids": [test_question.id],
            "policies": [{"name": "always_answer"}],
        },
    )
    assert start.status_code == 200
    accepted = start.json()
    assert accepted["status"] == "completed"
    assert "expected_answer" not in start.text

    metadata = app_client.get(f"/api/v1/evaluations/{accepted['experiment_id']}")
    assert metadata.status_code == 200
    assert "expected_answer" not in metadata.text

    result = app_client.get(f"/api/v1/evaluations/{accepted['experiment_id']}/results")
    assert result.status_code == 200
    assert "gold" in result.json()["experiment"]["runs"][0]
    assert "expected_answer" in result.text
    assert "sk-proj-" not in result.text


def test_evaluation_missing_invalid_selection_and_partial_status():
    app_client = client(FakeRuntime(fail_pipeline=True))
    assert app_client.get("/api/v1/evaluations/missing").status_code == 404
    invalid_split = app_client.post(
        "/api/v1/evaluations",
        json={"split": "validation", "policies": [{"name": "always_answer"}]},
    )
    assert invalid_split.status_code == 422
    invalid_ids = app_client.post(
        "/api/v1/evaluations",
        json={
            "split": "train",
            "question_ids": ["not-in-train"],
            "policies": [{"name": "always_answer"}],
            "fail_fast": True,
        },
    )
    assert invalid_ids.status_code == 422

    evaluator = EvaluationRunner(
        f"{DATASET}/documents.jsonl", f"{DATASET}/questions.jsonl"
    )
    ids = [item.id for item in evaluator._questions if item.split == "train"][:2]
    partial = app_client.post(
        "/api/v1/evaluations",
        json={
            "split": "train",
            "question_ids": ids,
            "policies": [{"name": "always_answer"}],
            "fail_fast": True,
        },
    )
    assert partial.status_code == 200
    assert partial.json()["status"] == "partial"
    metadata = app_client.get(f"/api/v1/evaluations/{partial.json()['experiment_id']}")
    assert metadata.json()["stopped_early"] is True


def test_cors_is_explicit_and_wildcard_configuration_is_rejected():
    with pytest.raises(ValueError, match="Wildcard CORS"):
        client(FakeRuntime(), settings=ApiSettings(cors_origins=("*",)))
    cors_client = client(
        FakeRuntime(), settings=ApiSettings(cors_origins=("https://ui.example",))
    )
    allowed = cors_client.options(
        "/api/v1/query",
        headers={
            "Origin": "https://ui.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == "https://ui.example"
    denied = cors_client.options(
        "/api/v1/query",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in denied.headers


def test_request_size_limit_returns_safe_413():
    response = client(FakeRuntime(), settings=ApiSettings(max_request_bytes=20)).post(
        "/api/v1/query",
        json={
            "question": "A sufficiently long question",
            "policy": {"name": "always_answer"},
        },
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"
