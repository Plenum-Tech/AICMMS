"""Connection lifecycle management: health checks and graceful shutdown."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from cafm.connectors.base import Connector
from cafm.core.events import Event, EventBus, EventType

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manages the lifecycle of multiple active connectors.

    Responsibilities:
      - Track active connectors by name.
      - Periodic health checks.
      - Graceful shutdown of all connectors.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus or EventBus()
        self._connectors: dict[str, Connector] = {}
        self._health_task: asyncio.Task[None] | None = None

    @property
    def active_connectors(self) -> dict[str, Connector]:
        return dict(self._connectors)

    async def register(self, connector: Connector) -> None:
        """Connect and start tracking a connector."""
        await connector.connect()
        self._connectors[connector.name] = connector
        await self._event_bus.publish(
            Event(
                type=EventType.CONNECTOR_CONNECTED,
                source=connector.name,
                payload={"source_type": str(connector.source_type)},
            )
        )
        logger.info("Connector connected: %s", connector.name)

    async def unregister(self, name: str) -> None:
        """Disconnect and stop tracking a connector by name."""
        connector = self._connectors.pop(name, None)
        if connector is not None:
            await connector.disconnect()
            await self._event_bus.publish(
                Event(type=EventType.CONNECTOR_DISCONNECTED, source=name)
            )
            logger.info("Connector disconnected: %s", name)

    async def health_check_all(self) -> dict[str, bool]:
        """Run health checks on all active connectors."""
        results: dict[str, bool] = {}
        for name, connector in self._connectors.items():
            try:
                results[name] = await connector.health_check()
            except Exception:
                results[name] = False
                logger.exception("Health check failed for %s", name)
                await self._event_bus.publish(
                    Event(
                        type=EventType.CONNECTOR_ERROR,
                        source=name,
                        payload={"error": "health_check_failed"},
                    )
                )
        return results

    def start_health_checks(self, interval_seconds: int = 60) -> None:
        """Start periodic health checks in the background."""
        if self._health_task is not None:
            return

        async def _loop() -> None:
            while True:
                await asyncio.sleep(interval_seconds)
                await self.health_check_all()

        self._health_task = asyncio.create_task(_loop())

    def stop_health_checks(self) -> None:
        """Stop periodic health checks."""
        if self._health_task is not None:
            self._health_task.cancel()
            self._health_task = None

    async def shutdown(self) -> None:
        """Gracefully disconnect all connectors and stop health checks."""
        self.stop_health_checks()
        names = list(self._connectors.keys())
        for name in names:
            await self.unregister(name)
        logger.info("All connectors shut down")

    def get(self, name: str) -> Connector | None:
        """Get an active connector by name."""
        return self._connectors.get(name)
