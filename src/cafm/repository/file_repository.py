"""File-backed repository for CSV and Excel connectors.

File sources are inherently read-heavy.  Write operations (create, update,
delete) are supported only when the underlying connector implements them;
otherwise they raise :class:`~cafm.core.exceptions.DataError` with a clear
message.
"""

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


class FileRepository(Repository[T]):
    """Repository implementation backed by a file :class:`Connector`.

    Designed for CSV and Excel data sources.  Reads are always supported;
    writes are delegated to the connector and will raise
    :class:`~cafm.core.exceptions.DataError` when the connector does not
    implement the relevant write method.

    Parameters
    ----------
    connector:
        An already-connected file :class:`~cafm.connectors.base.Connector`
        (CSV or Excel).
    sheet_or_file:
        The table/sheet name as understood by the connector.  For CSV
        connectors this is typically the filename stem; for Excel it is
        the worksheet name.
    model_class:
        The Pydantic domain model class to hydrate from raw rows.
    id_field:
        Column name used as a logical primary key (defaults to ``"id"``).
    """

    def __init__(
        self,
        connector: Connector,
        sheet_or_file: str,
        model_class: type[T],
        id_field: str = "id",
    ) -> None:
        self._connector = connector
        self._sheet_or_file = sheet_or_file
        self._model_class = model_class
        self._id_field = id_field

    # ── Helpers ───────────────────────────────────────────────────

    def _build_metadata(self) -> RecordMetadata:
        return RecordMetadata(
            source_name=self._connector.name,
            source_type=self._connector.source_type,
            table_name=self._sheet_or_file,
        )

    def _row_to_model(self, row: RawRow) -> T:
        record = UnifiedRecord(data=row, metadata=self._build_metadata())
        return record.to_domain_model(self._model_class)  # type: ignore[return-value]

    def _apply_client_side_filter(
        self,
        rows: list[RawRow],
        filters: dict[str, Any] | None,
    ) -> list[RawRow]:
        """Apply equality filters in-memory.

        File connectors may not natively support filter push-down, so
        the repository applies residual filters on the returned data.
        """
        if not filters:
            return rows
        return [
            row
            for row in rows
            if all(row.get(k) == v for k, v in filters.items())
        ]

    @staticmethod
    def _apply_client_side_sort(
        rows: list[RawRow],
        order_by: str | None,
    ) -> list[RawRow]:
        """Sort rows in-memory by a single field."""
        if not order_by:
            return rows

        descending = order_by.startswith("-")
        field = order_by.lstrip("-")

        return sorted(
            rows,
            key=lambda r: (r.get(field) is None, r.get(field)),
            reverse=descending,
        )

    @staticmethod
    def _apply_client_side_pagination(
        rows: list[RawRow],
        offset: int,
        limit: int | None,
    ) -> list[RawRow]:
        """Slice the row list for pagination."""
        start = offset
        end = (offset + limit) if limit is not None else None
        return rows[start:end]

    def _write_not_supported(self, operation: str) -> DataError:
        return DataError(
            f"{operation} is not supported for file source "
            f"{self._connector.source_type.value!r} "
            f"({self._sheet_or_file!r})"
        )

    # ── Single-entity CRUD ────────────────────────────────────────

    async def get_by_id(self, entity_id: str) -> T | None:
        try:
            rows = await self._connector.fetch_rows(
                self._sheet_or_file,
                filters={self._id_field: entity_id},
                limit=1,
            )
        except NotImplementedError:
            # Connector does not support server-side filters — fetch all
            # and filter client-side.
            rows = await self._connector.fetch_rows(self._sheet_or_file)
            rows = [r for r in rows if str(r.get(self._id_field)) == str(entity_id)]
        except Exception as exc:
            raise QueryError(
                f"Failed to fetch from {self._sheet_or_file} "
                f"with {self._id_field}={entity_id!r}: {exc}"
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
            # Attempt to push filters to the connector.
            rows = await self._connector.fetch_rows(
                self._sheet_or_file,
                filters=filters,
            )
        except NotImplementedError:
            rows = await self._connector.fetch_rows(self._sheet_or_file)
            rows = self._apply_client_side_filter(rows, filters)
        except Exception as exc:
            raise QueryError(
                f"Failed to query {self._sheet_or_file}: {exc}"
            ) from exc

        # Client-side sort and paginate (files rarely support these natively).
        rows = self._apply_client_side_sort(rows, order_by)
        total = len(rows)
        rows = self._apply_client_side_pagination(rows, offset, limit)

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
            inserted = await self._connector.insert_rows(
                self._sheet_or_file, [row]
            )
        except NotImplementedError:
            raise self._write_not_supported("create") from None
        except Exception as exc:
            raise DataError(
                f"Failed to insert into {self._sheet_or_file}: {exc}"
            ) from exc

        if inserted < 1:
            raise DataError(
                f"Insert into {self._sheet_or_file} reported 0 rows affected"
            )

        logger.info(
            "file_entity_created",
            source=self._sheet_or_file,
            id=row.get(self._id_field),
        )
        return entity

    async def update(self, entity_id: str, updates: dict[str, Any]) -> T | None:
        updates.setdefault("updated_at", datetime.utcnow().isoformat())

        try:
            affected = await self._connector.update_rows(
                self._sheet_or_file,
                filters={self._id_field: entity_id},
                updates=updates,
            )
        except NotImplementedError:
            raise self._write_not_supported("update") from None
        except Exception as exc:
            raise DataError(
                f"Failed to update {self._sheet_or_file} "
                f"({self._id_field}={entity_id!r}): {exc}"
            ) from exc

        if affected == 0:
            return None

        logger.info(
            "file_entity_updated",
            source=self._sheet_or_file,
            id=entity_id,
            fields=list(updates.keys()),
        )
        return await self.get_by_id(entity_id)

    async def delete(self, entity_id: str) -> bool:
        try:
            affected = await self._connector.delete_rows(
                self._sheet_or_file,
                filters={self._id_field: entity_id},
            )
        except NotImplementedError:
            raise self._write_not_supported("delete") from None
        except Exception as exc:
            raise DataError(
                f"Failed to delete from {self._sheet_or_file} "
                f"({self._id_field}={entity_id!r}): {exc}"
            ) from exc

        if affected > 0:
            logger.info(
                "file_entity_deleted",
                source=self._sheet_or_file,
                id=entity_id,
            )
            return True
        return False

    # ── Aggregate helpers ─────────────────────────────────────────

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        try:
            return await self._connector.count_rows(
                self._sheet_or_file, filters=filters
            )
        except NotImplementedError:
            # Fall back to counting client-side.
            rows = await self._connector.fetch_rows(self._sheet_or_file)
            rows = self._apply_client_side_filter(rows, filters)
            return len(rows)
        except Exception as exc:
            raise QueryError(
                f"Failed to count rows in {self._sheet_or_file}: {exc}"
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
            inserted = await self._connector.insert_rows(
                self._sheet_or_file, rows
            )
        except NotImplementedError:
            raise self._write_not_supported("bulk_create") from None
        except Exception as exc:
            raise DataError(
                f"Bulk insert into {self._sheet_or_file} failed: {exc}"
            ) from exc

        logger.info(
            "file_entities_bulk_created",
            source=self._sheet_or_file,
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
                    self._sheet_or_file,
                    filters={self._id_field: entity_id},
                    updates=fields,
                )
                total_affected += affected
            except NotImplementedError:
                raise self._write_not_supported("bulk_update") from None
            except Exception as exc:
                raise DataError(
                    f"Bulk update failed at {self._id_field}={entity_id!r} "
                    f"in {self._sheet_or_file}: {exc}"
                ) from exc

        logger.info(
            "file_entities_bulk_updated",
            source=self._sheet_or_file,
            requested=len(updates),
            affected=total_affected,
        )
        return total_affected
