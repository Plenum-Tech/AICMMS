"""Central Integration Manager — the primary entry point for all consumers."""

from __future__ import annotations

import logging
from typing import Any

from cafm.connectors.base import Connector, ConnectorConfig
from cafm.connectors.lifecycle import LifecycleManager
from cafm.connectors.registry import ConnectorRegistry
from cafm.core.config import AppConfig
from cafm.core.events import EventBus
from cafm.core.types import DataSourceType, RawRow
from cafm.integration.pipeline import Pipeline, PipelineResult
from cafm.integration.scheduler import Scheduler
from cafm.models.record import RecordMetadata, UnifiedRecord
from cafm.models.resultset import UnifiedResultSet
from cafm.schema.discovery import SchemaDiscoveryService
from cafm.schema.models import DataSourceSchema

logger = logging.getLogger(__name__)


class IntegrationManager:
    """Central orchestrator that wires connectors, schemas, pipelines and queries.

    This is the main API for external consumers (including the AI layer).

    Usage::

        manager = IntegrationManager()
        await manager.start()

        await manager.add_source(ConnectorConfig(
            name="facility_db",
            source_type="postgresql",
            connection_params={"url": "postgresql://..."},
        ))

        schema = await manager.get_source_schema("facility_db")
        results = await manager.query("facility_db", "assets", filters={"status": "active"})

        await manager.shutdown()
    """

    def __init__(
        self,
        config: AppConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or AppConfig()
        self._event_bus = event_bus or EventBus()
        self._registry = ConnectorRegistry()
        self._lifecycle = LifecycleManager(self._event_bus)
        self._schema_service = SchemaDiscoveryService(self._event_bus)
        self._pipelines: dict[str, Pipeline] = {}
        self._scheduler = Scheduler()

    # ── Lifecycle ─────────────────────────────────────────────────

    async def start(self) -> None:
        """Initialize the manager: discover plugins and start services."""
        if self._config.auto_discover_plugins:
            self._registry.discover_plugins()
        logger.info(
            "IntegrationManager started. Registered connectors: %s",
            self._registry.list_registered(),
        )

    async def shutdown(self) -> None:
        """Gracefully shut down all connectors and the scheduler."""
        self._scheduler.stop()
        await self._lifecycle.shutdown()
        logger.info("IntegrationManager shut down")

    # ── Source management ─────────────────────────────────────────

    async def add_source(self, config: ConnectorConfig) -> str:
        """Register and connect a new data source.

        Returns the source name.
        """
        connector = self._registry.create(config)
        await self._lifecycle.register(connector)
        logger.info("Source added: %s (%s)", config.name, config.source_type)
        return config.name

    async def remove_source(self, name: str) -> None:
        """Disconnect and remove a data source."""
        await self._lifecycle.unregister(name)
        self._schema_service.invalidate(name)

    async def test_connection(self, name: str) -> bool:
        """Test if a source connection is healthy."""
        connector = self._lifecycle.get(name)
        if connector is None:
            return False
        return await connector.health_check()

    def list_sources(self) -> list[str]:
        """List all active source names."""
        return list(self._lifecycle.active_connectors.keys())

    def get_connector(self, name: str) -> Connector | None:
        """Get a connector by source name."""
        return self._lifecycle.get(name)

    # ── Schema ────────────────────────────────────────────────────

    async def get_source_schema(
        self, name: str, refresh: bool = False
    ) -> DataSourceSchema:
        """Discover or return cached schema for a source."""
        connector = self._lifecycle.get(name)
        if connector is None:
            raise ValueError(f"Source '{name}' not found")

        if refresh:
            self._schema_service.invalidate(name)

        return await self._schema_service.discover(
            connector, name, connector.source_type, use_cache=not refresh
        )

    async def get_all_schemas(self) -> dict[str, DataSourceSchema]:
        """Discover schemas for all active sources."""
        schemas: dict[str, DataSourceSchema] = {}
        for name in self.list_sources():
            schemas[name] = await self.get_source_schema(name)
        return schemas

    # ── Query ─────────────────────────────────────────────────────

    async def query(
        self,
        source_name: str,
        table: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> UnifiedResultSet:
        """Query a data source and return unified results."""
        connector = self._lifecycle.get(source_name)
        if connector is None:
            raise ValueError(f"Source '{source_name}' not found")

        effective_limit = limit or self._config.default_query_limit

        rows = await connector.fetch_rows(
            table, columns=columns, filters=filters,
            limit=effective_limit, offset=offset,
        )
        total = await connector.count_rows(table, filters=filters)

        metadata = RecordMetadata(
            source_name=source_name,
            source_type=connector.source_type,
            table_name=table,
        )
        records = [UnifiedRecord(data=row, metadata=metadata) for row in rows]

        return UnifiedResultSet(
            records=records,
            total_count=total,
            offset=offset,
            limit=effective_limit,
            has_more=(offset + len(records)) < total,
        )

    # ── Pipelines ─────────────────────────────────────────────────

    def register_pipeline(self, pipeline: Pipeline) -> None:
        """Register a named pipeline."""
        self._pipelines[pipeline.name] = pipeline

    async def run_pipeline(self, pipeline_name: str) -> PipelineResult:
        """Execute a registered pipeline."""
        pipeline = self._pipelines.get(pipeline_name)
        if pipeline is None:
            raise ValueError(f"Pipeline '{pipeline_name}' not registered")

        connectors = self._lifecycle.active_connectors
        return await pipeline.execute(connectors)

    def list_pipelines(self) -> list[str]:
        return list(self._pipelines.keys())

    # ── Scheduler ─────────────────────────────────────────────────

    @property
    def scheduler(self) -> Scheduler:
        return self._scheduler

    # ── Convenience ───────────────────────────────────────────────

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def registry(self) -> ConnectorRegistry:
        return self._registry
