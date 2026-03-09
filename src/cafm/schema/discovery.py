"""Schema discovery orchestrator.

Coordinates calling each connector's SchemaInspector and producing
unified DataSourceSchema instances.
"""

from __future__ import annotations

from datetime import datetime

from cafm.core.events import Event, EventBus, EventType
from cafm.core.types import DataSourceType
from cafm.schema.models import DataSourceSchema


class SchemaDiscoveryService:
    """Orchestrates schema discovery across one or more connectors."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus or EventBus()
        self._cache: dict[str, DataSourceSchema] = {}

    async def discover(
        self,
        connector: object,  # Type: Connector (forward ref to avoid circular import)
        source_name: str,
        source_type: DataSourceType,
        use_cache: bool = True,
    ) -> DataSourceSchema:
        """Discover the full schema of a connected data source.

        Args:
            connector: A connected Connector instance.
            source_name: Human-readable name for the source.
            source_type: The DataSourceType enum value.
            use_cache: If True, return cached schema if available.

        Returns:
            A DataSourceSchema snapshot.
        """
        if use_cache and source_name in self._cache:
            return self._cache[source_name]

        # connector is expected to have get_schema_inspector()
        inspector = connector.get_schema_inspector()  # type: ignore[attr-defined]
        tables = []

        table_names = await inspector.list_tables()
        for table_name in table_names:
            table_schema = await inspector.discover_table(table_name)
            tables.append(table_schema)

        schema = DataSourceSchema(
            source_name=source_name,
            source_type=source_type,
            tables=tables,
            discovered_at=datetime.utcnow(),
        )

        self._cache[source_name] = schema

        await self._event_bus.publish(
            Event(
                type=EventType.SCHEMA_DISCOVERED,
                source=source_name,
                payload={"table_count": len(tables)},
            )
        )

        return schema

    def get_cached(self, source_name: str) -> DataSourceSchema | None:
        """Return a previously cached schema, or None."""
        return self._cache.get(source_name)

    def invalidate(self, source_name: str) -> None:
        """Remove a source from the cache."""
        self._cache.pop(source_name, None)

    def invalidate_all(self) -> None:
        """Clear the entire schema cache."""
        self._cache.clear()
