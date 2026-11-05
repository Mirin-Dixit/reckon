"""Bound request bytes and contain unexpected errors before server logging."""

import asyncio
import logging

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class SafeErrorMiddleware:
    """Handle unexpected HTTP errors without rethrowing raw details to Uvicorn."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def track_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, track_send)
        except Exception as error:
            logger.error("Unhandled API failure (%s)", type(error).__name__)
            if started:
                # A partially transmitted response cannot be replaced with a 500.
                # Preserve transport failure while suppressing raw exception context.
                raise RuntimeError("Response transmission failed") from None
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "The request could not be completed.",
                        "execution_status": None,
                    }
                },
            )
            await response(scope, receive, send)


class RequestBodyLimitMiddleware:
    def __init__(
        self, app: ASGIApp, max_bytes: int, timeout_seconds: float = 15.0
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.timeout_seconds = timeout_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        lengths = [
            value for key, value in scope["headers"] if key.lower() == b"content-length"
        ]
        if lengths:
            if len(lengths) != 1 or not lengths[0].isdigit():
                await self.reject(
                    scope,
                    receive,
                    send,
                    400,
                    "invalid_content_length",
                    "The request content length is invalid.",
                )
                return
            # Compare length first to avoid converting attacker-sized integers.
            value = lengths[0].lstrip(b"0") or b"0"
            maximum = str(self.max_bytes).encode("ascii")
            if len(value) > len(maximum) or (
                len(value) == len(maximum) and value > maximum
            ):
                await self.reject(
                    scope,
                    receive,
                    send,
                    413,
                    "request_too_large",
                    "The request body exceeds the size limit.",
                )
                return
        body = bytearray()
        deadline = asyncio.get_running_loop().time() + self.timeout_seconds
        while True:
            try:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TimeoutError
                message = await asyncio.wait_for(receive(), timeout=remaining)
            except TimeoutError:
                await self.reject(
                    scope,
                    receive,
                    send,
                    408,
                    "request_body_timeout",
                    "The request body was not received within the deadline.",
                )
                return
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_bytes:
                await self.reject(
                    scope,
                    receive,
                    send,
                    413,
                    "request_too_large",
                    "The request body exceeds the size limit.",
                )
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        replayed = False

        async def bounded_receive():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)

    @staticmethod
    async def reject(scope, receive, send, status, code, message):
        response = JSONResponse(
            status_code=status,
            headers={"Connection": "close"},
            content={
                "error": {"code": code, "message": message, "execution_status": None}
            },
        )
        await response(scope, receive, send)
