"""Service layer for data connector operations."""

from __future__ import annotations

import logging
import time
from typing import Any

from cafm.connectors.base import ConnectorConfig
from cafm.core.events import Event, EventBus, EventType
from cafm.core.types import ConnectorState, DataSourceType
from cafm.integration.manager import IntegrationManager
from cafm.schema.models import DataSourceSchema

logger = logging.getLogger(__name__)


class ConnectorService:
    """Business logic for managing data source connectors.

    Wraps IntegrationManager with higher-level operations suitable for
    the API layer: validation, error handling, event emission.
    """

    def __init__(self, manager: IntegrationManager, event_bus: EventBus) -> None:
        self._manager = manager
        self._event_bus = event_bus

    async def add_connector(
        self,
        name: str,
        source_type: DataSourceType,
        connection_params: dict[str, Any],
        description: str | None = None,
    ) -> dict[str, Any]:
        """Register and connect a new data source."""
        config = ConnectorConfig(
            name=name,
            source_type=source_type,
            connection_params=connection_params,
        )
        await self._manager.add_source(config)

        await self._event_bus.publish(Event(
            type=EventType.CONNECTOR_CONNECTED,
            source="connector_service",
            payload={"name": name, "source_type": source_type},
        ))

        return {
            "name": name,
            "source_type": source_type,
            "state": ConnectorState.CONNECTED,
            "description": description,
        }

    async def remove_connector(self, name: str) -> None:
        """Disconnect and remove a data source."""
        await self._manager.remove_source(name)
        await self._event_bus.publish(Event(
            type=EventType.CONNECTOR_DISCONNECTED,
            source="connector_service",
            payload={"name": name},
        ))

    async def test_connection(self, name: str) -> dict[str, Any]:
        """Test connectivity of a registered source."""
        start = time.perf_counter()
        healthy = await self._manager.test_connection(name)
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "name": name,
            "healthy": healthy,
            "latency_ms": round(latency_ms, 1),
            "error": None if healthy else "Health check failed",
        }

    def list_connectors(self) -> list[dict[str, Any]]:
        """List all active connectors with basic info."""
        sources = self._manager.list_sources()
        results = []
        for name in sources:
            connector = self._manager.get_connector(name)
            results.append({
                "name": name,
                "source_type": connector.source_type if connector else "unknown",
                "state": connector.state if connector else ConnectorState.DISCONNECTED,
            })
        return results

    def get_connector_info(self, name: str) -> dict[str, Any] | None:
        """Get detailed information about a specific connector."""
        connector = self._manager.get_connector(name)
        if connector is None:
            return None
        return {
            "name": name,
            "source_type": connector.source_type,
            "state": connector.state,
        }

    async def discover_schema(
        self, name: str, refresh: bool = False
    ) -> DataSourceSchema:
        """Discover the schema for a data source."""
        return await self._manager.get_source_schema(name, refresh=refresh)

    async def query_source(
        self,
        source_name: str,
        table: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Query a data source and return structured results."""
        result_set = await self._manager.query(
            source_name, table, columns=columns, filters=filters,
            limit=limit, offset=offset,
        )
        return {
            "source_name": source_name,
            "table": table,
            "rows": result_set.as_dicts(),
            "total_count": result_set.total_count,
            "offset": result_set.offset,
            "limit": result_set.limit,
            "has_more": result_set.has_more,
        }

    def list_registered_types(self) -> list[str]:
        """List all registered connector types (plugin types)."""
        return self._manager.registry.list_registered()
