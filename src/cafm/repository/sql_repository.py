"""SQL-backed repository for PostgreSQL, MySQL, and MSSQL connectors."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypeVar

import structlog

from cafm.connectors.base import Connector
from cafm.core.exceptions import DataError, QueryError
from cafm.core.types import RawRow
from cafm.models.base import CAFMBaseModel
from cafm.models.record import RecordMetadata, UnifiedRecord
from cafm.models.resultset import UnifiedResultSet
from cafm.repository.base import Repository

T = TypeVar("T", bound=CAFMBaseModel)

logger = structlog.get_logger(__name__)


class SQLRepository(Repository[T]):
    """Repository implementation backed by a SQL :class:`Connector`.

    Works with any connector whose ``source_type`` is one of the relational
    SQL variants (PostgreSQL, MySQL, MSSQL).  All reads and writes are
    delegated to the connector's ``fetch_rows`` / ``insert_rows`` /
    ``update_rows`` / ``delete_rows`` / ``count_rows`` methods.

    Parameters
    ----------
    connector:
        An already-connected :class:`~cafm.connectors.base.Connector`.
    table_name:
        Name of the database table this repository operates on.
    model_class:
        The Pydantic domain model class to hydrate from raw rows.
    id_field:
        Column name used as the primary key (defaults to ``"id"``).
    """

    def __init__(
        self,
        connector: Connector,
        table_name: str,
        model_class: type[T],
        id_field: str = "id",
    ) -> None:
        self._connector = connector
        self._table_name = table_name
        self._model_class = model_class
        self._id_field = id_field

    # ── Helpers ───────────────────────────────────────────────────

    def _build_metadata(self) -> RecordMetadata:
        """Create provenance metadata for rows returned by this repository."""
        return RecordMetadata(
            source_name=self._connector.name,
            source_type=self._connector.source_type,
            table_name=self._table_name,
        )

    def _row_to_record(self, row: RawRow) -> UnifiedRecord:
        """Wrap a raw row dict in a :class:`UnifiedRecord`."""
        return UnifiedRecord(data=row, metadata=self._build_metadata())

    def _record_to_model(self, record: UnifiedRecord) -> T:
        """Convert a :class:`UnifiedRecord` to the domain model ``T``."""
        return record.to_domain_model(self._model_class)  # type: ignore[return-value]

    def _row_to_model(self, row: RawRow) -> T:
        """Shortcut: raw row -> domain model in one step."""
        return self._record_to_model(self._row_to_record(row))

    # ── Single-entity CRUD ────────────────────────────────────────

    async def get_by_id(self, entity_id: str) -> T | None:
        try:
            rows = await self._connector.fetch_rows(
                self._table_name,
                filters={self._id_field: entity_id},
                limit=1,
            )
        except Exception as exc:
            raise QueryError(
                f"Failed to fetch {self._table_name} with "
                f"{self._id_field}={entity_id!r}: {exc}"
            ) from exc

        if not rows:
            return None
        return self._row_to_model(rows[0])

    async def get_all(
        self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
        order_by: str | None = None,
    ) -> UnifiedResultSet:
        try:
            # Build connector-level filters; ordering is added as a
            # special key that SQL connectors can interpret.
            effective_filters = dict(filters) if filters else {}
            if order_by is not None:
                effective_filters["__order_by__"] = order_by

            rows = await self._connector.fetch_rows(
                self._table_name,
                filters=effective_filters if effective_filters else None,
                limit=limit,
                offset=offset,
            )
            total = await self._connector.count_rows(
                self._table_name,
                filters=filters,
            )
        except Exception as exc:
            raise QueryError(
                f"Failed to query {self._table_name}: {exc}"
            ) from exc

        metadata = self._build_metadata()
        records = [UnifiedRecord(data=row, metadata=metadata) for row in rows]

        return UnifiedResultSet(
            records=records,
            total_count=total,
            offset=offset,
            limit=limit,
            has_more=(offset + len(records)) < total,
        )

    async def create(self, entity: T) -> T:
        row = entity.model_dump(mode="python", exclude_none=True)
        row.setdefault("created_at", datetime.utcnow().isoformat())

        try:
            inserted = await self._connector.insert_rows(self._table_name, [row])
        except Exception as exc:
            raise DataError(
                f"Failed to insert into {self._table_name}: {exc}"
            ) from exc

        if inserted < 1:
            raise DataError(f"Insert into {self._table_name} reported 0 rows affected")

        logger.info(
            "entity_created",
            table=self._table_name,
            id=row.get(self._id_field),
        )
        return entity

    async def update(self, entity_id: str, updates: dict[str, Any]) -> T | None:
        updates.setdefault("updated_at", datetime.utcnow().isoformat())

        try:
            affected = await self._connector.update_rows(
                self._table_name,
                filters={self._id_field: entity_id},
                updates=updates,
            )
        except Exception as exc:
            raise DataError(
                f"Failed to update {self._table_name} "
                f"({self._id_field}={entity_id!r}): {exc}"
            ) from exc

        if affected == 0:
            return None

        logger.info(
            "entity_updated",
            table=self._table_name,
            id=entity_id,
            fields=list(updates.keys()),
        )
        return await self.get_by_id(entity_id)

    async def delete(self, entity_id: str) -> bool:
        try:
            affected = await self._connector.delete_rows(
                self._table_name,
                filters={self._id_field: entity_id},
            )
        except Exception as exc:
            raise DataError(
                f"Failed to delete from {self._table_name} "
                f"({self._id_field}={entity_id!r}): {exc}"
            ) from exc

        if affected > 0:
            logger.info(
                "entity_deleted",
                table=self._table_name,
                id=entity_id,
            )
            return True
        return False

    # ── Aggregate helpers ─────────────────────────────────────────

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        try:
            return await self._connector.count_rows(
                self._table_name, filters=filters
            )
        except Exception as exc:
            raise QueryError(
                f"Failed to count rows in {self._table_name}: {exc}"
            ) from exc

    # ── Bulk operations ───────────────────────────────────────────

    async def bulk_create(self, entities: list[T]) -> list[T]:
        if not entities:
            return []

        now = datetime.utcnow().isoformat()
        rows: list[RawRow] = []
        for entity in entities:
            row = entity.model_dump(mode="python", exclude_none=True)
            row.setdefault("created_at", now)
            rows.append(row)

        try:
            inserted = await self._connector.insert_rows(self._table_name, rows)
        except Exception as exc:
            raise DataError(
                f"Bulk insert into {self._table_name} failed: {exc}"
            ) from exc

        logger.info(
            "entities_bulk_created",
            table=self._table_name,
            requested=len(entities),
            inserted=inserted,
        )
        return entities

    async def bulk_update(self, updates: list[tuple[str, dict[str, Any]]]) -> int:
        if not updates:
            return 0

        now = datetime.utcnow().isoformat()
        total_affected = 0

        for entity_id, fields in updates:
            fields.setdefault("updated_at", now)
            try:
                affected = await self._connector.update_rows(
                    self._table_name,
                    filters={self._id_field: entity_id},
                    updates=fields,
                )
                total_affected += affected
            except Exception as exc:
                raise DataError(
                    f"Bulk update failed at {self._id_field}={entity_id!r} "
                    f"in {self._table_name}: {exc}"
                ) from exc

        logger.info(
            "entities_bulk_updated",
            table=self._table_name,
            requested=len(updates),
            affected=total_affected,
        )
        return total_affected
