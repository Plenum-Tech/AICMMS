"""MongoDB schema introspection via document sampling."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from pymongo.database import Database as MongoDatabase

from cafm.connectors.base import SchemaInspector
from cafm.connectors.plugins.mongodb.type_map import map_bson_type, python_type_name
from cafm.core.types import DataSourceType
from cafm.schema.models import (
    ColumnSchema,
    DataSourceSchema,
    IndexSchema,
    TableSchema,
)


class MongoDBSchemaInspector(SchemaInspector):
    """Introspects MongoDB collections by sampling documents.

    Because MongoDB is schema-less, we sample *N* documents per collection
    and infer field names and types from the union of all sampled documents.
    """

    def __init__(
        self,
        database: MongoDatabase,
        source_name: str,
        sample_size: int = 100,
    ) -> None:
        self._db = database
        self._source_name = source_name
        self._sample_size = sample_size

    async def list_tables(self) -> list[str]:
        """List all collections (excluding system collections)."""
        return [
            name
            for name in self._db.list_collection_names()
            if not name.startswith("system.")
        ]

    async def discover_table(self, table_name: str) -> TableSchema:
        """Discover schema for a single collection via sampling."""
        collection = self._db[table_name]

        # Sample documents
        docs: list[dict[str, Any]] = list(
            collection.find().limit(self._sample_size)
        )

        # Infer fields: accumulate (field_name -> Counter of type names)
        field_types: dict[str, Counter[str]] = {}
        for doc in docs:
            self._walk_fields(doc, field_types, prefix="")

        # Build column schemas from inferred types
        columns: list[ColumnSchema] = []
        total_docs = len(docs) if docs else 1
        for field_name, type_counter in sorted(field_types.items()):
            # Most common type wins
            most_common_type = type_counter.most_common(1)[0][0]
            nullable = type_counter.get("null", 0) > 0 or (
                sum(type_counter.values()) < total_docs
            )
            columns.append(
                ColumnSchema(
                    name=field_name,
                    unified_type=map_bson_type(most_common_type),
                    native_type=most_common_type,
                    nullable=nullable,
                    primary_key=(field_name == "_id"),
                )
            )

        # Indexes
        indexes: list[IndexSchema] = []
        try:
            for idx_info in collection.list_indexes():
                idx_name = idx_info.get("name", "")
                if idx_name == "_id_":
                    continue  # skip default _id index
                idx_columns = list(idx_info.get("key", {}).keys())
                indexes.append(
                    IndexSchema(
                        name=idx_name,
                        columns=idx_columns,
                        unique=idx_info.get("unique", False),
                    )
                )
        except Exception:
            pass  # index listing may fail on some configs

        # Row count
        try:
            row_count = collection.estimated_document_count()
        except Exception:
            row_count = None

        pk_columns = ["_id"] if any(c.name == "_id" for c in columns) else []

        return TableSchema(
            name=table_name,
            columns=columns,
            primary_key=pk_columns,
            indexes=indexes,
            row_count=row_count,
        )

    async def discover_schema(self) -> DataSourceSchema:
        """Full schema discovery for all collections."""
        collection_names = await self.list_tables()
        tables = [await self.discover_table(name) for name in collection_names]
        return DataSourceSchema(
            source_name=self._source_name,
            source_type=DataSourceType.MONGODB,
            tables=tables,
            discovered_at=datetime.utcnow(),
        )

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _walk_fields(
        doc: dict[str, Any],
        field_types: dict[str, Counter[str]],
        prefix: str,
    ) -> None:
        """Recursively walk document fields and accumulate type counts.

        Nested documents produce dotted field names (e.g. ``address.city``).
        """
        for key, value in doc.items():
            full_key = f"{prefix}.{key}" if prefix else key
            type_name = python_type_name(value)

            if full_key not in field_types:
                field_types[full_key] = Counter()
            field_types[full_key][type_name] += 1

            # Recurse into nested documents (but not lists)
            if isinstance(value, dict):
                MongoDBSchemaInspector._walk_fields(value, field_types, prefix=full_key)
