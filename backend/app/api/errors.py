"""Safe API error types and response helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApiProblem(Exception):
    status_code: int
    code: str
    message: str
    execution_status: str | None = None
