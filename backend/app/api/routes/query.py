"""Single-query orchestration endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_runtime_service
from app.api.errors import ApiProblem
from app.api.models import QueryRequest, QueryResponse
from app.api.routes.experiment_jobs import local_access
from app.evaluation.serialization import sanitize_serialized
from app.generation.contracts import ExecutionStatus, ProviderError, ProviderErrorKind
from app.retrieval.runtime import RetrievalFailure

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(local_access)])


@router.post("/query", response_model=QueryResponse)
def query(body: QueryRequest, runtime=Depends(get_runtime_service)):
    if body.policy.name in {"always_answer", "prompt_abstention"}:
        can_generate = getattr(runtime, "can_generate", None)
        if callable(can_generate) and not can_generate(body.generation.model):
            raise ApiProblem(
                503,
                "generation_not_configured",
                "Model generation is not configured on this server.",
            )
    try:
        result = runtime.execute_query(body)
    except RetrievalFailure as error:
        raise ApiProblem(error.status, error.code,
                         "The configured local retrieval could not be completed.",
                         error.execution_status) from None
    except ProviderError as error:
        if error.kind is ProviderErrorKind.CONFIGURATION:
            raise ApiProblem(
                503, "runtime_configuration", "The configured runtime is unavailable."
            ) from None
        logger.error("Query provider setup failed (%s)", error.kind.value)
        raise ApiProblem(
            502, "provider_failure", "The provider request could not be completed."
        ) from None
    except Exception as error:
        logger.error("Query runtime failed (%s)", type(error).__name__)
        raise ApiProblem(
            500, "runtime_failure", "The query could not be completed."
        ) from None

    if result.execution_status is not ExecutionStatus.SUCCEEDED:
        if result.execution_status is ExecutionStatus.FAILED and not _can_generate(
            runtime, body.generation.model
        ):
            raise ApiProblem(
                503,
                "generation_not_configured",
                "Model generation is not configured on this server.",
                result.execution_status.value,
            )
        status_code = (
            504 if result.execution_status is ExecutionStatus.TIMED_OUT else 502
        )
        messages = {
            ExecutionStatus.TIMED_OUT: "The query runtime timed out.",
            ExecutionStatus.REFUSED: (
                "The provider refused or could not safely complete the request."
            ),
            ExecutionStatus.INCOMPLETE: "The provider returned an incomplete response.",
        }
        raise ApiProblem(
            status_code,
            "runtime_execution_failure",
            messages.get(result.execution_status, "The query runtime failed."),
            result.execution_status.value,
        )

    payload = sanitize_serialized(result.to_dict())
    reason = payload.get("decision_reason") or payload.get("abstention_reason")
    response = dict(
        experiment_id=body.experiment_id,
        run_id=body.run_id,
        decision=payload["decision"],
        answer=payload["answer"],
        clarification_question=payload["clarification_question"],
        decision_reason=reason,
        citations=payload["citations"],
        retrieved_evidence=(payload.get("retrieval") or {}).get("evidence", []),
        evidence_assessment=payload["evidence_assessment"],
        policy_name=payload["policy_name"],
        policy_parameters=payload["policy_parameters"],
        provider=payload["provider"],
        execution_status=payload["execution_status"],
        unsupported_premises=payload["unsupported_premises"],
        surfaced_contradictions=payload["surfaced_contradictions"],
        prompt_version=payload["prompt_version"],
        latency_ms=payload["latency_ms"],
        token_usage=payload["token_usage"],
        scores=payload["scores"],
        retrieval_parameters=(payload.get("retrieval") or {}).get("parameters", {}),
    )
    return QueryResponse.model_validate(sanitize_serialized(response))


def _can_generate(runtime, requested_model):
    checker = getattr(runtime, "can_generate", None)
    if callable(checker):
        return checker(requested_model)
    return getattr(runtime, "generation_configured", True)
