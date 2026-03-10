"""FastAPI application factory — the main AICMMS API entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cafm.api.config import APIConfig
from cafm.api.dependencies import clear_app_state, set_app_state
from cafm.api.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    cafm_error_to_status,
)
from cafm.api.routes import assets, auth, connectors, dashboard, health, technicians, work_orders
from cafm.api.websocket import create_event_bridge, websocket_endpoint, ws_manager
from cafm.core.config import AppConfig
from cafm.core.events import EventBus
from cafm.core.exceptions import CAFMError
from cafm.integration.manager import IntegrationManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    # ── Startup ────────────────────────────────────────────────
    app_config = AppConfig()
    api_config = APIConfig()
    event_bus = EventBus()
    manager = IntegrationManager(config=app_config, event_bus=event_bus)

    await manager.start()

    # Wire shared state into dependency injection
    set_app_state(app_config, api_config, event_bus, manager)

    # Bridge EventBus → WebSocket for real-time updates
    create_event_bridge(event_bus, ws_manager)

    logger.info(
        "AICMMS API started on %s:%d (debug=%s)",
        api_config.host, api_config.port, api_config.debug,
    )

    yield

    # ── Shutdown ───────────────────────────────────────────────
    await manager.shutdown()
    clear_app_state()
    logger.info("AICMMS API shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    api_config = APIConfig()

    app = FastAPI(
        title="AICMMS API",
        description=(
            "AI-native Computer Maintenance Management System — "
            "API for facility management, asset tracking, work orders, "
            "predictive maintenance, and real-time command center."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware (order matters: first added = outermost) ─────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_config.cors_origins,
        allow_credentials=api_config.cors_allow_credentials,
        allow_methods=api_config.cors_allow_methods,
        allow_headers=api_config.cors_allow_headers,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, config=api_config)

    # ── Exception handlers ─────────────────────────────────────

    @app.exception_handler(CAFMError)
    async def cafm_error_handler(request: Request, exc: CAFMError) -> JSONResponse:
        """Map CAFMError subclasses to appropriate HTTP responses."""
        status_code = cafm_error_to_status(exc)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": exc.__class__.__name__,
                "detail": str(exc),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "ValueError", "detail": str(exc)},
        )

    # ── Routes ─────────────────────────────────────────────────

    # Health checks at root level
    app.include_router(health.router)

    # API v1 prefix
    api_v1_prefix = "/api/v1"
    app.include_router(auth.router, prefix=api_v1_prefix)
    app.include_router(connectors.router, prefix=api_v1_prefix)
    app.include_router(assets.router, prefix=api_v1_prefix)
    app.include_router(work_orders.router, prefix=api_v1_prefix)
    app.include_router(technicians.router, prefix=api_v1_prefix)
    app.include_router(dashboard.router, prefix=api_v1_prefix)

    # WebSocket endpoint
    app.websocket("/ws/dashboard")(websocket_endpoint)

    return app


# Module-level app instance for uvicorn
app = create_app()
