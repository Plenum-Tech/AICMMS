"""Incremental data synchronization engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cafm.connectors.base import Connector
from cafm.core.types import RawRow

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a sync operation."""
    source_name: str
    table: str
    inserted: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    synced_at: datetime = field(default_factory=datetime.utcnow)
    errors: list[str] = field(default_factory=list)


class DataSyncEngine:
    """Synchronizes data between two connectors incrementally.

    Uses a key field to match records and a timestamp field
    to detect changes since the last sync.
    """

    def __init__(
        self,
        source: Connector,
        target: Connector,
        table: str,
        key_field: str = "id",
        timestamp_field: str = "updated_at",
    ) -> None:
        self._source = source
        self._target = target
        self._table = table
        self._key_field = key_field
        self._timestamp_field = timestamp_field
        self._last_sync: datetime | None = None

    async def sync(self, full: bool = False) -> SyncResult:
        """Run sync.

        Args:
            full: If True, does a full sync ignoring last_sync timestamp.
        """
        result = SyncResult(source_name=self._source.name, table=self._table)

        # Extract from source
        filters: dict[str, Any] | None = None
        if not full and self._last_sync:
            filters = {f"{self._timestamp_field}__gte": self._last_sync.isoformat()}

        source_rows = await self._source.fetch_rows(self._table, filters=filters)
        logger.info("Sync %s: fetched %d rows from source", self._table, len(source_rows))

        if not source_rows:
            return result

        # Get existing keys in target
        target_rows = await self._target.fetch_rows(
            self._table,
            columns=[self._key_field],
        )
        existing_keys = {row[self._key_field] for row in target_rows}

        # Split into inserts vs updates
        to_insert: list[RawRow] = []
        to_update: list[RawRow] = []

        for row in source_rows:
            key = row.get(self._key_field)
            if key in existing_keys:
                to_update.append(row)
            else:
                to_insert.append(row)

        # Insert new records
        if to_insert:
            await self._target.insert_rows(self._table, to_insert)
            result.inserted = len(to_insert)

        # Update existing records
        for row in to_update:
            key = row.pop(self._key_field, None)
            if key:
                await self._target.update_rows(
                    self._table,
                    filters={self._key_field: key},
                    updates=row,
                )
                result.updated += 1

        self._last_sync = datetime.utcnow()
        result.synced_at = self._last_sync

        logger.info(
            "Sync %s complete: %d inserted, %d updated",
            self._table, result.inserted, result.updated,
        )

        return result

    @property
    def last_sync(self) -> datetime | None:
        return self._last_sync
