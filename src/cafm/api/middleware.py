"""Custom middleware for the AICMMS API."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from cafm.api.config import APIConfig
from cafm.core.exceptions import (
    AuthenticationError,
    CAFMError,
    ConfigurationError,
    ConnectorError,
    ConnectorNotFoundError,
    DataError,
    IntegrationError,
    SchemaError,
)

logger = logging.getLogger(__name__)


# ── Exception → HTTP status mapping ───────────────────────────────

EXCEPTION_STATUS_MAP: dict[type, int] = {
    ConnectorNotFoundError: status.HTTP_404_NOT_FOUND,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    SchemaError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ConfigurationError: status.HTTP_400_BAD_REQUEST,
    DataError: status.HTTP_400_BAD_REQUEST,
    ConnectorError: status.HTTP_502_BAD_GATEWAY,
    IntegrationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    CAFMError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def cafm_error_to_status(exc: CAFMError) -> int:
    """Map a CAFMError subclass to an HTTP status code."""
    for exc_type, http_status in EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return http_status
    return status.HTTP_500_INTERNAL_SERVER_ERROR


# ── Request logging middleware ─────────────────────────────────────


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 1),
                "client": request.client.host if request.client else "unknown",
            },
        )
        # Attach timing header
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.1f}"
        return response


# ── Rate limiting middleware ───────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter per client IP."""

    def __init__(self, app, config: APIConfig | None = None) -> None:
        super().__init__(app)
        self._config = config or APIConfig()
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/ready", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0  # 1-minute window

        # Prune old entries
        timestamps = self._requests[client_ip]
        self._requests[client_ip] = [t for t in timestamps if t > window_start]

        if len(self._requests[client_ip]) >= self._config.rate_limit_per_minute:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": "60"},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
