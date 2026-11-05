"""Environment-backed, secret-free provider configuration."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from app.configuration import environment
from app.generation.contracts import ModelSettings


@dataclass(frozen=True)
class OpenAIProviderConfig:
    """OpenAI adapter settings; credentials are resolved only when creating a client."""

    provider: str = "openai"
    model: str | None = None
    api_key_env_var: str = "OPENAI_API_KEY"
    timeout_seconds: float = 30.0
    retry_count: int = 2
    temperature: float | None = None
    max_output_tokens: int = 1024
    max_provider_requests: int = 4

    def __post_init__(self) -> None:
        if self.provider != "openai":
            raise ValueError("provider must be 'openai'")
        if self.model is not None and not self.model.strip():
            raise ValueError("model must be non-empty when provided")
        if not self.api_key_env_var.strip():
            raise ValueError("api_key_env_var must be non-empty")
        _validate_limits(
            self.timeout_seconds,
            self.retry_count,
            self.temperature,
            self.max_output_tokens,
            self.max_provider_requests,
        )

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> OpenAIProviderConfig:
        """Read Reckon settings; never read or retain the API key itself."""
        values = environment(environ)
        try:
            return cls(
                provider=values.get("RECKON_PROVIDER", "openai").strip().lower(),
                model=_optional_str(values.get("RECKON_MODEL")),
                api_key_env_var=values.get(
                    "RECKON_API_KEY_ENV", "OPENAI_API_KEY"
                ).strip(),
                timeout_seconds=float(values.get("RECKON_TIMEOUT_SECONDS", "30")),
                retry_count=int(values.get("RECKON_RETRY_COUNT", "2")),
                temperature=_optional_float(values.get("RECKON_TEMPERATURE")),
                max_output_tokens=int(values.get("RECKON_MAX_OUTPUT_TOKENS", "1024")),
                max_provider_requests=int(
                    values.get("RECKON_MAX_PROVIDER_REQUESTS", "4")
                ),
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid Reckon provider configuration: {error}"
            ) from error

    def model_settings(self) -> ModelSettings:
        """Convert sampling and request settings to the provider-neutral contract."""
        return ModelSettings(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            timeout_seconds=self.timeout_seconds,
        )


def _optional_str(value: str | None) -> str | None:
    return value.strip() if value and value.strip() else None


def _optional_float(value: str | None) -> float | None:
    return None if value is None or not value.strip() else float(value)


@dataclass(frozen=True)
class OllamaProviderConfig:
    """Local-only settings; no credentials, cloud fallback, or implicit download."""

    provider: str = "ollama"
    model: str | None = None
    base_url: str = "http://127.0.0.1:11434"
    context_size: int = 4096
    timeout_seconds: float = 120.0
    retry_count: int = 0
    temperature: float | None = 0.0
    max_output_tokens: int = 1024
    max_provider_requests: int = 4

    def __post_init__(self) -> None:
        _validate_limits(
            self.timeout_seconds,
            self.retry_count,
            self.temperature,
            self.max_output_tokens,
            self.max_provider_requests,
        )
        if self.provider != "ollama" or self.retry_count != 0:
            raise ValueError("Local Ollama requires provider='ollama' and zero retries")
        if type(self.context_size) is not int or not 2048 <= self.context_size <= 32768:
            raise ValueError("context_size must be an integer from 2048 through 32768")
        if self.max_output_tokens + 256 >= self.context_size:
            raise ValueError("Context must leave room for input and output")
        validate_ollama_url(self.base_url)
        if self.model is not None:
            validate_local_model(self.model)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> OllamaProviderConfig:
        values = environment(environ)
        try:
            return cls(
                model=_optional_str(values.get("RECKON_MODEL")),
                base_url=values.get("RECKON_OLLAMA_URL", "http://127.0.0.1:11434"),
                context_size=int(values.get("RECKON_CONTEXT_SIZE", "4096")),
                timeout_seconds=float(values.get("RECKON_TIMEOUT_SECONDS", "120")),
                retry_count=int(values.get("RECKON_RETRY_COUNT", "0")),
                temperature=_optional_float(values.get("RECKON_TEMPERATURE", "0")),
                max_output_tokens=int(values.get("RECKON_MAX_OUTPUT_TOKENS", "1024")),
                max_provider_requests=int(
                    values.get("RECKON_MAX_PROVIDER_REQUESTS", "4")
                ),
            )
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid local Ollama configuration") from error

    def model_settings(self) -> ModelSettings:
        return ModelSettings(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            timeout_seconds=self.timeout_seconds,
        )


def validate_ollama_url(value: str) -> None:
    """Allow numeric loopback only: no DNS, userinfo, paths, queries or fragments."""
    import ipaddress
    from urllib.parse import urlsplit

    try:
        url = urlsplit(value)
        valid = (
            url.scheme == "http"
            and url.hostname is not None
            and ipaddress.ip_address(url.hostname).is_loopback
            and url.username is None
            and url.password is None
            and url.path in {"", "/"}
            and not url.query
            and not url.fragment
            and (url.port is None or 0 < url.port <= 65535)
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Ollama URL must be an HTTP numeric loopback origin")


def validate_local_model(model: str) -> None:
    """Require an explicit local tag; reject registries, paths and cloud aliases."""
    import re

    if (
        not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]*:[A-Za-z0-9][A-Za-z0-9_.-]*", model
        )
        or "cloud" in model.lower()
    ):
        raise ValueError(
            "An explicit local model:tag without cloud routing is required"
        )


def load_provider_config(
    environ: Mapping[str, str] | None = None,
) -> OllamaProviderConfig | OpenAIProviderConfig:
    """Ollama is the default; OpenAI remains explicit opt-in code, never fallback."""
    values = environment(environ)
    provider = values.get("RECKON_PROVIDER", "ollama").strip().lower()
    if provider == "ollama":
        return OllamaProviderConfig.from_env(values)
    if provider == "openai":
        return OpenAIProviderConfig.from_env(values)
    raise ValueError("Unsupported provider")


def _validate_limits(
    timeout_seconds: float,
    retry_count: int,
    temperature: float | None,
    max_output_tokens: int,
    max_provider_requests: int,
) -> None:
    if not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 120:
        raise ValueError("timeout_seconds must be finite and in (0, 120]")
    if type(retry_count) is not int or not 0 <= retry_count <= 5:
        raise ValueError("retry_count must be an integer from 0 through 5")
    if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 32768:
        raise ValueError("max_output_tokens must be an integer from 1 through 32768")
    if type(max_provider_requests) is not int or not 0 <= max_provider_requests <= 100:
        raise ValueError("max_provider_requests must be an integer from 0 through 100")
    ModelSettings(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        timeout_seconds=timeout_seconds,
    )
