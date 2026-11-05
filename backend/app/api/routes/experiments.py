"""Synchronous experiment start and metadata endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_runtime_service, model_settings
from app.api.errors import ApiProblem
from app.api.models import EvaluationAccepted, EvaluationMetadata, EvaluationRequest
from app.api.routes.experiment_jobs import local_access
from app.evaluation.runner import ErrorHandlingMode, PolicyRunConfig
from app.generation.contracts import ProviderError, ProviderErrorKind
from app.retrieval.runtime import RetrievalFailure

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(local_access)])


def authorized_runtime(request: Request):
    """Block legacy empirical execution before runtime/provider initialization.

    A trusted server-side authorizer is injectable for offline contract tests.
    No environment variable or HTTP input enables empirical evaluation.
    Future real-data integration must verify acceptance and inference permission.
    """
    authorizer = request.app.state.evaluation_authorizer
    if authorizer is None:
        raise ApiProblem(403, "empirical_evaluation_deferred",
                         "Empirical evaluation is deferred. Use synthetic experiments.")
    authorizer()
    return get_runtime_service(request)


@router.post("/evaluations", response_model=EvaluationAccepted)
def start_evaluation(
    body: EvaluationRequest,
    request: Request,
    runtime=Depends(authorized_runtime),
):
    try:
        runner = runtime.evaluation_runner()
        generation_configuration = runtime.resolve_generation(body.generation)
        model = generation_configuration["model"]
        policies = [
            PolicyRunConfig(
                name=policy.name,
                policy=runtime.make_policy(
                    policy,
                    model,
                    model_settings(generation_configuration),
                ),
                parameters=_policy_parameters(
                    policy, model, generation_configuration["provider"],
                ),
            )
            for policy in body.policies
        ]
        record = runner.run(
            split=body.split,
            policies=policies,
            pipeline_factory=runtime.evaluation_pipeline_factory,
            retrieval_configuration=runtime.retrieval_configuration(body.retrieval),
            generation_configuration=generation_configuration,
            random_seed=body.random_seed,
            question_ids=body.question_ids,
            error_mode=(
                ErrorHandlingMode.FAIL_FAST
                if body.fail_fast
                else ErrorHandlingMode.CONTINUE
            ),
        )
    except RetrievalFailure as error:
        raise ApiProblem(error.status, error.code,
                         "The configured local retrieval could not be completed.",
                         error.execution_status) from None
    except ProviderError as error:
        if error.kind is ProviderErrorKind.CONFIGURATION:
            raise ApiProblem(
                503, "runtime_configuration", "The configured runtime is unavailable."
            ) from None
        logger.error("Evaluation provider setup failed (%s)", error.kind.value)
        raise ApiProblem(
            502, "provider_failure", "The evaluation provider could not be initialized."
        ) from None
    except ValueError as error:
        message = str(error)
        if "split" in message.lower() or "question id" in message.lower():
            raise ApiProblem(
                422,
                "invalid_evaluation_selection",
                "The split or question IDs are invalid.",
            ) from None
        logger.error("Evaluation configuration failed (%s)", type(error).__name__)
        raise ApiProblem(
            422,
            "invalid_evaluation_configuration",
            "The evaluation configuration is invalid.",
        ) from None
    except Exception as error:
        logger.error("Evaluation failed (%s)", type(error).__name__)
        raise ApiProblem(
            500, "evaluation_failure", "The evaluation could not be completed."
        ) from None

    registry = request.app.state.experiment_registry
    registry.add(record)
    status = (
        "partial"
        if record.metrics.get("partial") or record.stopped_early
        else "completed"
    )
    return EvaluationAccepted(
        experiment_id=record.experiment_id,
        status=status,
        split=record.benchmark_split,
        selected_question_count=len(record.selected_question_ids),
        observed_run_count=len(record.runs),
    )


@router.get("/evaluations/{experiment_id}", response_model=EvaluationMetadata)
def get_evaluation(experiment_id: str, request: Request):
    record = request.app.state.experiment_registry.get(experiment_id)
    if record is None:
        raise ApiProblem(
            404, "experiment_not_found", "The requested experiment was not found."
        )
    return EvaluationMetadata(
        experiment_id=record.experiment_id,
        status=(
            "partial"
            if record.metrics.get("partial") or record.stopped_early
            else "completed"
        ),
        split=record.benchmark_split,
        selected_question_ids=list(record.selected_question_ids),
        policy_names=[item["name"] for item in record.policy_configurations],
        observed_run_count=len(record.runs),
        stopped_early=record.stopped_early,
    )


def _policy_parameters(policy, model, provider):
    params = {
        "model": model,
        "provider": provider,
    }
    if policy.name == "threshold":
        params.update(
            {
                "score_type": policy.score_type,
                "threshold": policy.threshold,
                "direction": policy.direction,
                "missing_score_decision": policy.missing_score_decision,
            }
        )
    return params
