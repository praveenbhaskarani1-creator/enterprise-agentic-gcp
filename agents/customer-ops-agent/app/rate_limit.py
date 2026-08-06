"""Privacy-safe application-level request rate limiting."""

from __future__ import annotations

import asyncio
import hashlib
import math
import os
import time
from collections import deque
from collections.abc import Mapping
from typing import Any, Protocol

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class StructuredLogger(Protocol):
    """Minimal interface required from a structured event logger."""

    def log_struct(
        self,
        info: Mapping[str, Any],
        *,
        severity: str,
    ) -> None:
        """Write one structured event."""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply an in-memory sliding-window limit to POST requests."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool,
        requests_per_window: int,
        window_seconds: int,
        event_logger: StructuredLogger | None = None,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.event_logger = event_logger
        self._requests: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Allow the request or return HTTP 429 when its limit is exhausted."""
        if not self.enabled or self._is_exempt(request):
            return await call_next(request)

        client_key = self._client_key(request)
        allowed, remaining, reset_seconds = await self._consume(client_key)

        if not allowed:
            self._log_rejection(
                request=request,
                client_key=client_key,
                retry_after_seconds=reset_seconds,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Request rate limit exceeded.",
                    "retry_after_seconds": reset_seconds,
                },
                headers={
                    "Retry-After": str(reset_seconds),
                    "X-RateLimit-Limit": str(self.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(
            self.requests_per_window
        )
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _is_exempt(self, request: Request) -> bool:
        """Exclude health checks, metadata and read-only browser requests."""
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        return request.url.path in {"/health", "/version"}

    @staticmethod
    def _client_key(request: Request) -> str:
        """Use the direct connection address for the local safety limit."""
        if request.client is None:
            return "unknown"
        return request.client.host

    async def _consume(self, client_key: str) -> tuple[bool, int, int]:
        """Consume one request from a client's sliding time window."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        async with self._lock:
            for key, timestamps in list(self._requests.items()):
                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()
                if not timestamps:
                    del self._requests[key]

            timestamps = self._requests.setdefault(client_key, deque())

            if len(timestamps) >= self.requests_per_window:
                reset_seconds = max(
                    1,
                    math.ceil(
                        timestamps[0] + self.window_seconds - now
                    ),
                )
                return False, 0, reset_seconds

            timestamps.append(now)
            remaining = self.requests_per_window - len(timestamps)
            return True, remaining, self.window_seconds

    def _log_rejection(
        self,
        *,
        request: Request,
        client_key: str,
        retry_after_seconds: int,
    ) -> None:
        """Log rejection metadata without storing the client address."""
        if self.event_logger is None:
            return

        client_hash = hashlib.sha256(
            client_key.encode("utf-8")
        ).hexdigest()[:12]

        self.event_logger.log_struct(
            {
                "event_type": "RATE_LIMIT_REJECTED",
                "http_method": request.method,
                "path": request.url.path,
                "client_hash": client_hash,
                "limit": self.requests_per_window,
                "window_seconds": self.window_seconds,
                "retry_after_seconds": retry_after_seconds,
            },
            severity="WARNING",
        )


def _enabled_from_environment() -> bool:
    """Read the rate-limit feature flag."""
    return (
        os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower()
        in {"1", "true", "yes", "on"}
    )


def _positive_integer(name: str, default: int) -> int:
    """Read and validate a positive integer environment setting."""
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def add_rate_limit_middleware(
    app: FastAPI,
    *,
    event_logger: StructuredLogger | None = None,
) -> None:
    """Attach the configurable local safety limiter to FastAPI."""
    app.add_middleware(
        RateLimitMiddleware,
        enabled=_enabled_from_environment(),
        requests_per_window=_positive_integer(
            "RATE_LIMIT_REQUESTS_PER_WINDOW",
            60,
        ),
        window_seconds=_positive_integer(
            "RATE_LIMIT_WINDOW_SECONDS",
            60,
        ),
        event_logger=event_logger,
    )
