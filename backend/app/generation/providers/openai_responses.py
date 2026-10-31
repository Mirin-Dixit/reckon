"""OpenAI Responses API adapter for the provider-neutral generation contract."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from typing import Any

from app.generation.config import OpenAIProviderConfig
from app.generation.contracts import (
    ExecutionStatus,
    GenerationRequest,
    GenerationResponse,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
    TokenUsage,
)


class OpenAIResponsesProvider:
    """Implement ``LLMProvider`` using the official OpenAI Python SDK.

    SDK imports are lazy and remain inside this adapter. Built-in SDK retries are
    disabled so the adapter's bounded retry policy is the only retry layer.
    """

    def __init__(
        self,
        config: OpenAIProviderConfig,
        *,
        client: Any | None = None,
        environ: Mapping[str, str] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self._sleep = sleep_fn
        if client is not None:
            self._client = client
            return

        environment = os.environ if environ is None else environ
        api_key = environment.get(config.api_key_env_var)
        if not api_key:
            raise ProviderError(
                ProviderErrorKind.CONFIGURATION,
                f"Required API key environment variable is missing: "
                f"{config.api_key_env_var}",
                provider="openai",
            )
        try:
            from openai import OpenAI
        except ImportError as error:
            raise ProviderError(
                ProviderErrorKind.CONFIGURATION,
                "Install the optional 'openai' dependency to use this adapter",
                provider="openai",
            ) from error
        self._client = OpenAI(
            api_key=api_key,
            timeout=config.timeout_seconds,
            max_retries=0,
        )

    def close(self) -> None:
        """Release the owned SDK client's connection pool."""
        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Make one Responses API generation call with bounded transient retries."""
        if self.config.provider != "openai":
            raise ProviderError(
                ProviderErrorKind.CONFIGURATION,
                "OpenAIResponsesProvider requires provider='openai'",
                provider="openai",
            )
        retries = self.config.retry_count
        for attempt in range(retries + 1):
            try:
                return self._generate_once(request)
            except ProviderError as error:
                if not error.retryable or attempt >= retries:
                    raise
                self._sleep(min(0.25 * (2**attempt), 2.0))
        raise AssertionError("bounded retry loop exited unexpectedly")

    def _generate_once(self, request: GenerationRequest) -> GenerationResponse:
        effective_model = self.config.model or request.model
        timeout_seconds = request.settings.timeout_seconds
        parameters: dict[str, Any] = {
            "model": effective_model,
            "instructions": request.system_instruction,
            "input": request.user_content,
            "store": False,
        }
        temperature = (
            request.settings.temperature
            if request.settings.temperature is not None
            else self.config.temperature
        )
        max_output_tokens = (
            request.settings.max_output_tokens
            if request.settings.max_output_tokens is not None
            else self.config.max_output_tokens
        )
        if temperature is not None:
            parameters["temperature"] = temperature
        if max_output_tokens is not None:
            parameters["max_output_tokens"] = max_output_tokens
        if request.structured_output is not None:
            spec = request.structured_output
            parameters["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": spec.name,
                    "schema": spec.schema,
                    "strict": spec.strict,
                }
            }

        client = self._client
        with_options = getattr(client, "with_options", None)
        if callable(with_options):
            client = with_options(timeout=timeout_seconds, max_retries=0)
        started_at = time.perf_counter()
        try:
            response = client.responses.create(**parameters)
        except Exception as error:
            kind, retryable = _normalize_sdk_error(error)
            raise ProviderError(
                kind=kind,
                message=_safe_error_message(kind),
                retryable=retryable,
                provider="openai",
                request_id=_request_id(error),
            ) from None

        metadata = ProviderMetadata(
            provider="openai",
            model=str(getattr(response, "model", effective_model)),
            request_id=_request_id(response),
        )
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        status = str(getattr(response, "status", "completed"))
        refusal_text = _find_refusal(response)
        if refusal_text is not None:
            return GenerationResponse(
                content=refusal_text,
                metadata=metadata,
                status=ExecutionStatus.REFUSED,
                latency_ms=latency_ms,
                token_usage=_usage(response),
                finish_reason="refusal",
            )
        if status == "incomplete":
            return GenerationResponse(
                content=_response_text(response),
                metadata=metadata,
                status=ExecutionStatus.INCOMPLETE,
                latency_ms=latency_ms,
                token_usage=_usage(response),
                finish_reason=status,
            )
        if status != "completed":
            raise ProviderError(
                ProviderErrorKind.UNKNOWN,
                "OpenAI returned an unsuccessful response status",
                provider="openai",
                request_id=metadata.request_id,
            )

        content = _response_text(response)
        structured_content = None
        if request.structured_output is not None:
            if not content:
                raise ProviderError(
                    ProviderErrorKind.MALFORMED_RESPONSE,
                    "OpenAI returned no structured output",
                    provider="openai",
                    request_id=metadata.request_id,
                )
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                raise ProviderError(
                    ProviderErrorKind.MALFORMED_RESPONSE,
                    "OpenAI returned malformed structured output",
                    provider="openai",
                    request_id=metadata.request_id,
                ) from None
            if not isinstance(parsed, dict):
                raise ProviderError(
                    ProviderErrorKind.MALFORMED_RESPONSE,
                    "OpenAI structured output must be a JSON object",
                    provider="openai",
                    request_id=metadata.request_id,
                )
            structured_content = parsed
        elif not content:
            raise ProviderError(
                ProviderErrorKind.MALFORMED_RESPONSE,
                "OpenAI returned no text output",
                provider="openai",
                request_id=metadata.request_id,
            )
        return GenerationResponse(
            content=content,
            structured_content=structured_content,
            metadata=metadata,
            status=ExecutionStatus.SUCCEEDED,
            latency_ms=latency_ms,
            token_usage=_usage(response),
            finish_reason=status,
        )


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        return output_text
    pieces: list[str] = []
    for item in getattr(response, "output", ()) or ():
        for content in getattr(item, "content", ()) or ():
            if getattr(content, "type", None) == "output_text":
                value = getattr(content, "text", None)
                if isinstance(value, str):
                    pieces.append(value)
    return "".join(pieces)


def _find_refusal(response: Any) -> str | None:
    for item in getattr(response, "output", ()) or ():
        for content in getattr(item, "content", ()) or ():
            if getattr(content, "type", None) == "refusal":
                refusal = getattr(content, "refusal", None)
                return (
                    refusal
                    if isinstance(refusal, str)
                    else "Model refused the request"
                )
    return None


def _usage(response: Any) -> TokenUsage | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    return TokenUsage(
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
    )


def _request_id(value: Any) -> str | None:
    request_id = getattr(value, "_request_id", None) or getattr(
        value, "request_id", None
    )
    return request_id if isinstance(request_id, str) else None


def _normalize_sdk_error(error: Exception) -> tuple[ProviderErrorKind, bool]:
    names = {base.__name__ for base in type(error).__mro__}
    if "APITimeoutError" in names or "TimeoutError" in names:
        return ProviderErrorKind.TIMEOUT, True
    if "AuthenticationError" in names:
        return ProviderErrorKind.AUTHENTICATION, False
    if "RateLimitError" in names:
        return ProviderErrorKind.RATE_LIMIT, True
    if "APIConnectionError" in names or "ConnectionError" in names:
        return ProviderErrorKind.TRANSIENT, True
    status_code = getattr(error, "status_code", None)
    if status_code in (408, 409):
        return ProviderErrorKind.TRANSIENT, True
    if isinstance(status_code, int) and status_code >= 500:
        return ProviderErrorKind.TRANSIENT, True
    if "BadRequestError" in names or "UnprocessableEntityError" in names:
        return ProviderErrorKind.INVALID_REQUEST, False
    if "APIStatusError" in names or isinstance(status_code, int):
        return ProviderErrorKind.INVALID_REQUEST, False
    return ProviderErrorKind.UNKNOWN, False


def _safe_error_message(kind: ProviderErrorKind) -> str:
    return {
        ProviderErrorKind.TIMEOUT: "OpenAI request timed out",
        ProviderErrorKind.AUTHENTICATION: "OpenAI authentication failed",
        ProviderErrorKind.RATE_LIMIT: "OpenAI rate limit was reached",
        ProviderErrorKind.TRANSIENT: "OpenAI request failed due to a transient error",
        ProviderErrorKind.INVALID_REQUEST: "OpenAI rejected the request",
        ProviderErrorKind.UNKNOWN: "OpenAI request failed",
    }.get(kind, "OpenAI request failed")
