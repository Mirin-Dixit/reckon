"""Health endpoint."""

from fastapi import APIRouter, Request

from app.api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    manager = request.app.state.runtime_manager
    runtime = manager.get()
    initialized = runtime is not None
    return HealthResponse(
        status="ok" if initialized else "degraded",
        application="RAGBench Studio",
        api_version=request.app.version,
        runtime_initialized=initialized,
        generation_configured=(
            getattr(runtime, "generation_configured", False) if initialized else False
        ),
        provider_connection_tested=False,
    )
