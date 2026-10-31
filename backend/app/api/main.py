"""FastAPI application factory and safe transport-level error handling."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app.api.dependencies import ApiSettings, ExperimentRegistry, RuntimeManager
from app.api.errors import ApiProblem
from app.api.middleware import RequestBodyLimitMiddleware, SafeErrorMiddleware
from app.api.models import ErrorResponse
from app.api.routes import evaluation, experiments, health, query


def create_app(*, settings: ApiSettings | None = None, runtime_factory=None) -> FastAPI:
    config = settings or ApiSettings.from_env()
    if "*" in config.cors_origins:
        raise ValueError("Wildcard CORS origins are not allowed")

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        try:
            yield
        finally:
            await run_in_threadpool(application.state.runtime_manager.close)

    application = FastAPI(
        title="RAGBench Studio API",
        lifespan=lifespan,
        version="0.1.0",
        description=(
            "Research API for retrieval, answer/abstain decisions, and evaluation."
        ),
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
        responses={
            status: {"model": ErrorResponse}
            for status in (400, 404, 405, 413, 422, 500, 502, 503, 504)
        },
    )
    application.state.settings = config
    application.state.runtime_manager = RuntimeManager(runtime_factory)
    application.state.experiment_registry = ExperimentRegistry()

    application.add_middleware(
        RequestBodyLimitMiddleware, max_bytes=config.max_request_bytes
    )
    application.add_middleware(SafeErrorMiddleware)

    if config.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(config.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    @application.exception_handler(ApiProblem)
    async def api_problem_handler(request: Request, error: ApiProblem):
        del request
        body = ErrorResponse(
            error={
                "code": error.code,
                "message": error.message,
                "execution_status": error.execution_status,
            }
        )
        return JSONResponse(
            status_code=error.status_code,
            content=body.model_dump(),
        )

    @application.exception_handler(HTTPException)
    async def http_error_handler(request: Request, error: HTTPException):
        del request
        messages = {
            404: ("not_found", "The requested resource was not found."),
            405: ("method_not_allowed", "The HTTP method is not allowed."),
        }
        code, message = messages.get(
            error.status_code, ("http_error", "The request could not be completed.")
        )
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {"code": code, "message": message, "execution_status": None}
            },
            headers={"Allow": error.headers["Allow"]}
            if error.headers and "Allow" in error.headers
            else None,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, error: RequestValidationError):
        del error
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_request",
                    "message": "The request body or parameters are invalid.",
                    "execution_status": None,
                }
            },
        )

    prefix = "/api/v1"
    application.include_router(health.router, prefix=prefix, tags=["health"])
    application.include_router(query.router, prefix=prefix, tags=["query"])
    application.include_router(experiments.router, prefix=prefix, tags=["evaluations"])
    application.include_router(evaluation.router, prefix=prefix, tags=["evaluations"])
    return application


app = create_app()
