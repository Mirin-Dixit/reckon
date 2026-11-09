"""Bounded local-only Ollama inference, without SDKs or remote fallbacks."""

from __future__ import annotations

import http.client
import json
import re
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from typing import Any
from urllib.parse import urlsplit

from app.generation.config import (
    OllamaProviderConfig,
    validate_local_model,
    validate_ollama_url,
)
from app.generation.contracts import (
    ExecutionStatus,
    GenerationRequest,
    GenerationResponse,
    ProviderError,
    ProviderErrorKind,
    ProviderMetadata,
    TokenUsage,
)

MAX_REQUEST_BYTES = 65_536
MAX_RESPONSE_BYTES = 1_048_576
CONTEXT_OVERHEAD = 256
JsonTransport = Callable[[str, str, dict | None, float], dict[str, Any]]


def _error(kind: ProviderErrorKind, message: str) -> ProviderError:
    return ProviderError(kind, message, provider="ollama")


class LocalHttpTransport:
    """Connect directly to a validated IP: no proxies, redirects or auth headers."""

    def __init__(self, base_url: str) -> None:
        validate_ollama_url(base_url)
        url = urlsplit(base_url)
        self.host, self.port = url.hostname, url.port or 80

    def __call__(
        self, method: str, path: str, payload: dict | None, timeout: float
    ) -> dict[str, Any]:
        if timeout <= 0:
            raise _error(ProviderErrorKind.TIMEOUT, "Local Ollama request timed out")
        body = (
            None
            if payload is None
            else json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        )
        if body is not None and len(body) > MAX_REQUEST_BYTES:
            raise _error(
                ProviderErrorKind.INVALID_REQUEST, "Local request is too large"
            )
        connection = http.client.HTTPConnection(self.host, self.port, timeout=timeout)
        try:
            connection.request(
                method,
                path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise _error(
                    ProviderErrorKind.CONFIGURATION, "Ollama redirects are forbidden"
                )
            if response.status != 200:
                kind = (
                    ProviderErrorKind.CONFIGURATION
                    if response.status == 404
                    else ProviderErrorKind.INVALID_REQUEST
                    if response.status in (400, 422)
                    else ProviderErrorKind.TRANSIENT
                )
                raise _error(kind, "Local Ollama request failed")
            if (
                response.getheader("Content-Type", "").split(";")[0].strip().lower()
                != "application/json"
            ):
                raise _error(
                    ProviderErrorKind.MALFORMED_RESPONSE, "Ollama did not return JSON"
                )
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise _error(
                    ProviderErrorKind.MALFORMED_RESPONSE, "Local response is too large"
                )
            result = json.loads(data)
            if not isinstance(result, dict) or "error" in result:
                msg = (
                    str(result.get("error", ""))
                    if isinstance(result, dict)
                    else ""
                )
                kind = (
                    ProviderErrorKind.INVALID_REQUEST
                    if "context" in msg.lower()
                    else ProviderErrorKind.MALFORMED_RESPONSE
                )
                raise _error(
                    kind,
                    f"Local Ollama request rejected: {msg}"
                    if msg
                    else "Invalid Ollama response",
                )
            return result
        except TimeoutError:
            raise _error(
                ProviderErrorKind.TIMEOUT, "Local Ollama request timed out"
            ) from None
        except (OSError, http.client.HTTPException):
            raise _error(
                ProviderErrorKind.TRANSIENT, "Local Ollama server unavailable"
            ) from None
        except (ValueError, UnicodeError):
            raise _error(
                ProviderErrorKind.MALFORMED_RESPONSE, "Malformed Ollama JSON"
            ) from None
        finally:
            connection.close()


class OllamaProvider:
    """One inference at a time and one attempt budget for the adapter lifetime."""

    def __init__(
        self,
        config: OllamaProviderConfig,
        *,
        transport: JsonTransport | None = None,
    ) -> None:
        self.config = config
        self._transport = transport or LocalHttpTransport(config.base_url)
        self._lock = threading.Lock()
        self._attempts = 0
        self._closed = False
        self._metadata_cache: dict[str, tuple[ProviderMetadata, int]] = {}

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _metadata(self, model: str, timeout: float) -> ProviderMetadata:
        validate_local_model(model)
        if model in self._metadata_cache:
            metadata, allowance = self._metadata_cache[model]
            self._template_allowance = allowance
            return metadata
        deadline = time.monotonic() + timeout

        def read(method: str, path: str, body: dict | None = None) -> dict:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _error(ProviderErrorKind.TIMEOUT, "Local metadata timed out")
            return self._transport(method, path, body, remaining)

        tags = read("GET", "/api/tags").get("models")
        if not isinstance(tags, list):
            raise _error(
                ProviderErrorKind.MALFORMED_RESPONSE, "Invalid local model inventory"
            )
        item = next(
            (
                item
                for item in tags
                if isinstance(item, dict)
                and item.get("name", item.get("model")) == model
            ),
            None,
        )
        if item is None:
            raise _error(
                ProviderErrorKind.CONFIGURATION,
                "Configured local model is not installed",
            )
        if (
            item.get("remote_host")
            or item.get("remote_model")
            or type(item.get("size")) is not int
            or item["size"] <= 0
        ):
            raise _error(
                ProviderErrorKind.CONFIGURATION,
                "Installed local weights are required; remote aliases are forbidden",
            )
        # Ollama represents remote aliases in both tags and show responses.
        shown = read("POST", "/api/show", {"model": model})
        if any(
            record.get(key)
            for record in (item, shown)
            for key in ("remote_host", "remote_model")
        ):
            raise _error(
                ProviderErrorKind.CONFIGURATION, "Remote Ollama models are forbidden"
            )
        details = shown.get("details") or item.get("details") or {}
        if not isinstance(details, dict):
            details = {}
        # Context accounting is restricted to the approved Qwen3 family. Include
        # coarse static template text and delimiters as a preflight framing estimate.
        # Dynamic template directives (loops/conditionals) are stripped so template
        # source syntax is not counted as tokens; dynamic framing expansions remain
        # bounded by CONTEXT_OVERHEAD.
        info = shown.get("model_info") or {}
        if not isinstance(info, dict) or info.get("general.architecture") != "qwen3":
            raise _error(
                ProviderErrorKind.CONFIGURATION,
                "Only local Qwen3 is verified for context accounting",
            )
        template_raw = str(shown.get("template", ""))
        template_static = re.sub(r"\{\{.*?\}\}", "", template_raw, flags=re.DOTALL)
        self._template_allowance = len(template_static.encode("utf-8"))
        version = None
        try:
            version = read("GET", "/api/version").get("version")
        except ProviderError:
            pass  # Runtime version is optional provenance, never invented.
        metadata = ProviderMetadata(
            provider="ollama",
            model=model,
            model_digest=_optional_text(item.get("digest")),
            quantization=_optional_text(details.get("quantization_level")),
            api_version=_optional_text(version),
        )
        self._metadata_cache[model] = (metadata, self._template_allowance)
        return metadata

    def available(self, model: str) -> bool:
        try:
            if not self._lock.acquire(timeout=1):
                return False
            try:
                if self._closed:
                    return False
                self._metadata(model, 2.0)
                return True
            finally:
                self._lock.release()
        except (ProviderError, ValueError):
            return False

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        timeout = min(request.settings.timeout_seconds, self.config.timeout_seconds)
        deadline = time.monotonic() + timeout
        if not self._lock.acquire(timeout=timeout):
            raise _error(ProviderErrorKind.TIMEOUT, "Local inference slot timed out")
        try:
            if self._closed:
                raise _error(
                    ProviderErrorKind.CONFIGURATION, "Local provider is closed"
                )
            model = self.config.model or request.model
            if self.config.model and request.model != model:
                raise _error(
                    ProviderErrorKind.CONFIGURATION,
                    "Request model conflicts with configuration",
                )
            output_limit = (
                request.settings.max_output_tokens or self.config.max_output_tokens
            )
            if output_limit > self.config.max_output_tokens:
                raise _error(
                    ProviderErrorKind.CONFIGURATION,
                    "Output exceeds local server ceiling",
                )
            payload = {
                "model": model,
                "stream": False,
                "think": False,
                "messages": [
                    {"role": "system", "content": request.system_instruction},
                    {"role": "user", "content": request.user_content},
                ],
                "options": {
                    "num_ctx": self.config.context_size,
                    "num_predict": output_limit,
                    "temperature": (
                        request.settings.temperature
                        if request.settings.temperature is not None
                        else self.config.temperature
                    ),
                },
                "keep_alive": "5m",
            }
            if request.structured_output is not None:
                payload["format"] = request.structured_output.schema
            payload_bytes = len(
                json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )
            if payload_bytes > MAX_REQUEST_BYTES:
                raise _error(
                    ProviderErrorKind.INVALID_REQUEST, "Local request is too large"
                )
            # Coarse preflight estimate: in byte-level BPE, prompt tokens typically
            # average ~3.5-4.5 B/tok for English and structured JSON. 2 bytes per
            # token provides a preflight estimate to reject obviously oversized
            # inputs before network dispatch without claiming a guaranteed upper bound.
            # Exact token limits are enforced post-response from Ollama token counts.
            prompt_bytes = len(
                request.system_instruction.encode("utf-8")
            ) + len(request.user_content.encode("utf-8"))
            estimated_prompt_tokens = (prompt_bytes + 1) // 2
            if (
                estimated_prompt_tokens + output_limit + CONTEXT_OVERHEAD
                > self.config.context_size
            ):
                raise _error(
                    ProviderErrorKind.INVALID_REQUEST,
                    "Context budget exceeded; no evidence was truncated",
                )

            def remaining() -> float:
                value = deadline - time.monotonic()
                if value <= 0:
                    raise _error(ProviderErrorKind.TIMEOUT, "Local inference timed out")
                return value

            metadata = self._metadata(model, remaining())
            if (
                estimated_prompt_tokens
                + output_limit
                + CONTEXT_OVERHEAD
                + self._template_allowance
                > self.config.context_size
            ):
                raise _error(
                    ProviderErrorKind.INVALID_REQUEST,
                    "Model template exceeds the available context budget",
                )
            if self._attempts >= self.config.max_provider_requests:
                raise _error(
                    ProviderErrorKind.RATE_LIMIT,
                    "Local request attempt budget exhausted",
                )
            self._attempts += 1
            result = self._transport("POST", "/api/chat", payload, remaining())
            return self._response(request, result, metadata)
        finally:
            self._lock.release()

    def _response(
        self,
        request: GenerationRequest,
        result: dict,
        metadata: ProviderMetadata,
    ) -> GenerationResponse:
        message = result.get("message")
        if (
            result.get("model") != metadata.model
            or not isinstance(message, dict)
            or message.get("role") != "assistant"
            or message.get("tool_calls")
            or message.get("thinking")
        ):
            raise _error(
                ProviderErrorKind.MALFORMED_RESPONSE, "Invalid local assistant response"
            )
        content = message.get("content")
        if not isinstance(content, str):
            raise _error(
                ProviderErrorKind.MALFORMED_RESPONSE, "Missing local response content"
            )
        reason = result.get("done_reason")
        metadata = replace(metadata, completion_reason=_optional_text(reason))
        incomplete = result.get("done") is not True or reason == "length"
        if not incomplete and reason != "stop":
            raise _error(
                ProviderErrorKind.MALFORMED_RESPONSE,
                "Unrecognized local completion status",
            )
        structured = None
        if not incomplete and request.structured_output is not None:
            try:
                structured = json.loads(content)
                if not isinstance(structured, dict):
                    raise ValueError
            except (ValueError, TypeError):
                raise _error(
                    ProviderErrorKind.MALFORMED_RESPONSE,
                    "Invalid local structured output",
                ) from None
        prompt, generated = result.get("prompt_eval_count"), result.get("eval_count")
        for value in (prompt, generated):
            if value is not None and (type(value) is not int or value < 0):
                raise _error(
                    ProviderErrorKind.MALFORMED_RESPONSE, "Invalid local token counts"
                )
        duration = result.get("total_duration")
        if duration is not None and (type(duration) is not int or duration < 0):
            raise _error(ProviderErrorKind.MALFORMED_RESPONSE, "Invalid local timing")
        limit = request.settings.max_output_tokens or self.config.max_output_tokens
        if (prompt is not None and prompt + limit > self.config.context_size) or (
            generated is not None and generated > limit
        ):
            raise _error(
                ProviderErrorKind.MALFORMED_RESPONSE,
                "Local token budget was not respected",
            )
        return GenerationResponse(
            content=content,
            structured_content=structured,
            metadata=metadata,
            status=ExecutionStatus.INCOMPLETE
            if incomplete
            else ExecutionStatus.SUCCEEDED,
            finish_reason=_optional_text(reason),
            token_usage=TokenUsage(
                input_tokens=prompt,
                output_tokens=generated,
                total_tokens=prompt + generated
                if prompt is not None and generated is not None
                else None,
            ),
            latency_ms=duration / 1_000_000 if duration is not None else None,
        )


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None
