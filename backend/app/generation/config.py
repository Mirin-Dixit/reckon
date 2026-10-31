"""Environment-backed, secret-free provider configuration."""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass

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
    max_output_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.provider != "openai":
            raise ValueError("provider must be 'openai'")
        if self.model is not None and not self.model.strip():
            raise ValueError("model must be non-empty when provided")
        if not self.api_key_env_var.strip():
            raise ValueError("api_key_env_var must be non-empty")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive and finite")
        if type(self.retry_count) is not int or not 0 <= self.retry_count <= 5:
            raise ValueError("retry_count must be an integer from 0 through 5")
        ModelSettings(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            timeout_seconds=self.timeout_seconds,
        )

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> OpenAIProviderConfig:
        """Read RAGBench settings; never read or retain the API key itself."""
        values = os.environ if environ is None else environ
        try:
            return cls(
                provider=values.get("RAGBENCH_PROVIDER", "openai").strip().lower(),
                model=_optional_str(values.get("RAGBENCH_MODEL")),
                api_key_env_var=values.get(
                    "RAGBENCH_API_KEY_ENV", "OPENAI_API_KEY"
                ).strip(),
                timeout_seconds=float(values.get("RAGBENCH_TIMEOUT_SECONDS", "30")),
                retry_count=int(values.get("RAGBENCH_RETRY_COUNT", "2")),
                temperature=_optional_float(values.get("RAGBENCH_TEMPERATURE")),
                max_output_tokens=_optional_int(
                    values.get("RAGBENCH_MAX_OUTPUT_TOKENS")
                ),
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid RAGBench provider configuration: {error}"
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


def _optional_int(value: str | None) -> int | None:
    return None if value is None or not value.strip() else int(value)
