"""MongoDB-backed repository for document-oriented data access."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypeVar

import structlog

from cafm.connectors.base import Connector
from cafm.core.exceptions import DataError, QueryError
from cafm.core.types import DataSourceType, RawRow
from cafm.models.base import CAFMBaseModel
from cafm.models.record import RecordMetadata, UnifiedRecord
from cafm.models.resultset import UnifiedResultSet
from cafm.repository.base import Repository

T = TypeVar("T", bound=CAFMBaseModel)

logger = structlog.get_logger(__name__)


class MongoRepository(Repository[T]):
    """Repository implementation backed by a MongoDB :class:`Connector`.

    MongoDB stores documents in collections rather than rows in tables.
    This repository maps CAFM domain models to/from MongoDB documents,
    using the connector's standard ``fetch_rows``, ``insert_rows``,
    ``update_rows``, ``delete_rows``, and ``count_rows`` methods (which,
    for a MongoDB connector, operate on collections/documents).

    Parameters
    ----------
    connector:
        An already-connected MongoDB :class:`~cafm.connectors.base.Connector`.
    collection_name:
        Name of the MongoDB collection this repository operates on.
    model_class:
        The Pydantic domain model class to hydrate from raw documents.
    id_field:
        Field name used as the primary identifier.  Defaults to ``"_id"``,
        which is MongoDB's native document identifier.
    """

    def __init__(
        self,
        connector: Connector,
        collection_name: str,
        model_class: type[T],
        id_field: str = "_id",
    ) -> None:
        self._connector = connector
        self._collection_name = collection_name
        self._model_class = model_class
        self._id_field = id_field

    # ── Helpers ───────────────────────────────────────────────────

    def _build_metadata(self) -> RecordMetadata:
        return RecordMetadata(
            source_name=self._connector.name,
            source_type=DataSourceType.MONGODB,
            table_name=self._collection_name,
        )

    def _normalise_document(self, doc: RawRow) -> RawRow:
        """Normalise a MongoDB document for domain model consumption.

        MongoDB returns ``_id`` as an ``ObjectId`` by default.  If the
        domain model uses a different id field name we copy the value
        across; the raw ``_id`` (if present) is stringified so Pydantic
        can validate it.
        """
        normalised = dict(doc)
        if "_id" in normalised:
            normalised["_id"] = str(normalised["_id"])
        return normalised

    def _row_to_model(self, doc: RawRow) -> T:
        normalised = self._normalise_document(doc)
        record = UnifiedRecord(data=normalised, metadata=self._build_metadata())
        return record.to_domain_model(self._model_class)  # type: ignore[return-value]

    def _entity_to_document(self, entity: T) -> RawRow:
        """Serialise a domain model to a MongoDB-compatible document dict."""
        return entity.model_dump(mode="python", exclude_none=True)

    # ── Single-entity CRUD ────────────────────────────────────────

    async def get_by_id(self, entity_id: str) -> T | None:
        try:
            rows = await self._connector.fetch_rows(
                self._collection_name,
                filters={self._id_field: entity_id},
                limit=1,
            )
        except Exception as exc:
            raise QueryError(
                f"Failed to fetch document from {self._collection_name} "
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
            effective_filters = dict(filters) if filters else {}
            if order_by is not None:
                effective_filters["__order_by__"] = order_by

            docs = await self._connector.fetch_rows(
                self._collection_name,
                filters=effective_filters if effective_filters else None,
                limit=limit,
                offset=offset,
            )
            total = await self._connector.count_rows(
                self._collection_name,
                filters=filters,
            )
        except Exception as exc:
            raise QueryError(
                f"Failed to query collection {self._collection_name}: {exc}"
            ) from exc

        metadata = self._build_metadata()
        records = [
            UnifiedRecord(data=self._normalise_document(doc), metadata=metadata)
            for doc in docs
        ]

        return UnifiedResultSet(
            records=records,
            total_count=total,
            offset=offset,
            limit=limit,
            has_more=(offset + len(records)) < total,
        )

    async def create(self, entity: T) -> T:
        doc = self._entity_to_document(entity)
        doc.setdefault("created_at", datetime.utcnow().isoformat())

        try:
            inserted = await self._connector.insert_rows(
                self._collection_name, [doc]
            )
        except Exception as exc:
            raise DataError(
                f"Failed to insert into {self._collection_name}: {exc}"
            ) from exc

        if inserted < 1:
            raise DataError(
                f"Insert into {self._collection_name} reported 0 documents affected"
            )

        logger.info(
            "document_created",
            collection=self._collection_name,
            id=doc.get(self._id_field),
        )
        return entity

    async def update(self, entity_id: str, updates: dict[str, Any]) -> T | None:
        updates.setdefault("updated_at", datetime.utcnow().isoformat())

        try:
            affected = await self._connector.update_rows(
                self._collection_name,
                filters={self._id_field: entity_id},
                updates=updates,
            )
        except Exception as exc:
            raise DataError(
                f"Failed to update document in {self._collection_name} "
                f"({self._id_field}={entity_id!r}): {exc}"
            ) from exc

        if affected == 0:
            return None

        logger.info(
            "document_updated",
            collection=self._collection_name,
            id=entity_id,
            fields=list(updates.keys()),
        )
        return await self.get_by_id(entity_id)

    async def delete(self, entity_id: str) -> bool:
        try:
            affected = await self._connector.delete_rows(
                self._collection_name,
                filters={self._id_field: entity_id},
            )
        except Exception as exc:
            raise DataError(
                f"Failed to delete from {self._collection_name} "
                f"({self._id_field}={entity_id!r}): {exc}"
            ) from exc

        if affected > 0:
            logger.info(
                "document_deleted",
                collection=self._collection_name,
                id=entity_id,
            )
            return True
        return False

    # ── Aggregate helpers ─────────────────────────────────────────

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        try:
            return await self._connector.count_rows(
                self._collection_name, filters=filters
            )
        except Exception as exc:
            raise QueryError(
                f"Failed to count documents in {self._collection_name}: {exc}"
            ) from exc

    # ── Bulk operations ───────────────────────────────────────────

    async def bulk_create(self, entities: list[T]) -> list[T]:
        if not entities:
            return []

        now = datetime.utcnow().isoformat()
        docs: list[RawRow] = []
        for entity in entities:
            doc = self._entity_to_document(entity)
            doc.setdefault("created_at", now)
            docs.append(doc)

        try:
            inserted = await self._connector.insert_rows(
                self._collection_name, docs
            )
        except Exception as exc:
            raise DataError(
                f"Bulk insert into {self._collection_name} failed: {exc}"
            ) from exc

        logger.info(
            "documents_bulk_created",
            collection=self._collection_name,
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
                    self._collection_name,
                    filters={self._id_field: entity_id},
                    updates=fields,
                )
                total_affected += affected
            except Exception as exc:
                raise DataError(
                    f"Bulk update failed at {self._id_field}={entity_id!r} "
                    f"in {self._collection_name}: {exc}"
                ) from exc

        logger.info(
            "documents_bulk_updated",
            collection=self._collection_name,
            requested=len(updates),
            affected=total_affected,
        )
        return total_affected
