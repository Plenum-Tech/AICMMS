"""Abstract base classes for all data source connectors.

Every connector plugin must subclass ``Connector`` and ``SchemaInspector``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict

from cafm.core.types import ConnectorState, DataSourceType, RawRow
from cafm.schema.models import DataSourceSchema, TableSchema


# ── Configuration ─────────────────────────────────────────────────


class ConnectorConfig(BaseModel):
    """Base configuration every connector receives."""

    model_config = ConfigDict(extra="forbid")

    name: str
    source_type: DataSourceType
    connection_params: dict[str, Any]
    options: dict[str, Any] = {}


# ── Schema Inspector ──────────────────────────────────────────────


class SchemaInspector(ABC):
    """Introspects a data source to produce unified schema models."""

    @abstractmethod
    async def list_tables(self) -> list[str]:
        """List all available tables / collections / sheets."""
        ...

    @abstractmethod
    async def discover_table(self, table_name: str) -> TableSchema:
        """Discover schema for a single table / collection / sheet."""
        ...

    @abstractmethod
    async def discover_schema(self) -> DataSourceSchema:
        """Full schema discovery (all tables)."""
        ...


# ── Abstract Connector ────────────────────────────────────────────


class Connector(ABC):
    """Abstract base class for all data source connectors.

    Lifecycle::

        1. __init__(config) — store config, do NOT connect
        2. connect()        — establish connection / session
        3. use fetch/write  — perform operations
        4. disconnect()     — release resources

    Use the ``session()`` context manager for automatic lifecycle.
    """

    source_type: ClassVar[DataSourceType]

    def __init__(self, config: ConnectorConfig) -> None:
        self._config = config
        self._state = ConnectorState.DISCONNECTED

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def state(self) -> ConnectorState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._state == ConnectorState.CONNECTED

    # ── Lifecycle ─────────────────────────────────────────────────

    @abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the data source."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Release connection resources."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the connection is alive and healthy."""
        ...

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Connector]:
        """Context manager: connect on enter, disconnect on exit."""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

    # ── Schema ────────────────────────────────────────────────────

    @abstractmethod
    def get_schema_inspector(self) -> SchemaInspector:
        """Return a SchemaInspector bound to this connection."""
        ...

    # ── Read ──────────────────────────────────────────────────────

    @abstractmethod
    async def fetch_rows(
        self,
        table: str,
        columns: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RawRow]:
        """Fetch rows from a table / collection / sheet."""
        ...

    @abstractmethod
    async def count_rows(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Count rows matching optional filters."""
        ...

    async def fetch_rows_streaming(
        self,
        table: str,
        columns: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
        batch_size: int = 1000,
    ) -> AsyncIterator[list[RawRow]]:
        """Stream rows in batches. Default implementation paginates fetch_rows."""
        offset = 0
        while True:
            batch = await self.fetch_rows(
                table, columns=columns, filters=filters, limit=batch_size, offset=offset
            )
            if not batch:
                break
            yield batch
            if len(batch) < batch_size:
                break
            offset += batch_size

    # ── Write (optional) ──────────────────────────────────────────

    async def insert_rows(self, table: str, rows: list[RawRow]) -> int:
        """Insert rows. Returns number inserted. Override if writable."""
        raise NotImplementedError(f"{self.source_type} connector does not support writes")

    async def update_rows(
        self, table: str, filters: dict[str, Any], updates: dict[str, Any]
    ) -> int:
        """Update rows matching filters. Returns number updated."""
        raise NotImplementedError(f"{self.source_type} connector does not support writes")

    async def delete_rows(self, table: str, filters: dict[str, Any]) -> int:
        """Delete rows matching filters. Returns number deleted."""
        raise NotImplementedError(f"{self.source_type} connector does not support writes")

    # ── Raw query (optional) ──────────────────────────────────────

    async def execute_raw(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[RawRow]:
        """Execute a raw query. Override if the source supports it."""
        raise NotImplementedError(f"{self.source_type} connector does not support raw queries")
