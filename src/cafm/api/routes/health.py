"""Health check and readiness endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from cafm.api.dependencies import get_integration_manager
from cafm.api.schemas.common import HealthResponse
from cafm.integration.manager import IntegrationManager

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic liveness check."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(
    manager: IntegrationManager = Depends(get_integration_manager),
) -> HealthResponse:
    """Readiness check — verifies all critical components."""
    sources = manager.list_sources()
    components: dict[str, str] = {
        "integration_manager": "ready",
        "event_bus": "ready",
    }

    # Check each active connector
    for source in sources:
        try:
            healthy = await manager.test_connection(source)
            components[f"connector:{source}"] = "healthy" if healthy else "unhealthy"
        except Exception:
            components[f"connector:{source}"] = "error"

    overall = "ready" if all(
        v in ("ready", "healthy") for v in components.values()
    ) else "degraded"

    return HealthResponse(
        status=overall,
        version="0.1.0",
        uptime_seconds=round(time.time() - _start_time, 1),
        active_connectors=len(sources),
        components=components,
    )
