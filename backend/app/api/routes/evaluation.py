"""Explicitly gold-bearing evaluation result endpoint."""

from fastapi import APIRouter, Request

from app.api.errors import ApiProblem
from app.api.models import EvaluationResults

router = APIRouter()


@router.get("/evaluations/{experiment_id}/results", response_model=EvaluationResults)
def get_evaluation_results(experiment_id: str, request: Request):
    record = request.app.state.experiment_registry.get(experiment_id)
    if record is None:
        raise ApiProblem(
            404, "experiment_not_found", "The requested experiment was not found."
        )
    return EvaluationResults(experiment=record.to_dict())
