"""MSSQL (SQL Server) schema introspection using SQLAlchemy Inspector."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from cafm.connectors.base import SchemaInspector
from cafm.connectors.plugins.mssql.type_map import map_mssql_type
from cafm.core.types import DataSourceType
from cafm.schema.models import (
    ColumnSchema,
    DataSourceSchema,
    ForeignKeySchema,
    IndexSchema,
    TableSchema,
)


class MSSQLSchemaInspector(SchemaInspector):
    """Introspects SQL Server databases using SQLAlchemy's Inspector."""

    def __init__(
        self,
        engine: Engine,
        source_name: str,
        schema: str = "dbo",
        sample_size: int = 5,
    ) -> None:
        self._engine = engine
        self._source_name = source_name
        self._schema = schema
        self._sample_size = sample_size

    async def list_tables(self) -> list[str]:
        """List all tables in the configured schema."""
        insp = inspect(self._engine)
        return insp.get_table_names(schema=self._schema)

    async def discover_table(self, table_name: str) -> TableSchema:
        """Discover schema for a single table."""
        insp = inspect(self._engine)

        # Columns
        raw_columns = insp.get_columns(table_name, schema=self._schema)
        pk_constraint = insp.get_pk_constraint(table_name, schema=self._schema)
        pk_columns: list[str] = (
            pk_constraint.get("constrained_columns", []) if pk_constraint else []
        )

        columns: list[ColumnSchema] = []
        for col in raw_columns:
            native_type = str(col["type"])
            columns.append(
                ColumnSchema(
                    name=col["name"],
                    unified_type=map_mssql_type(native_type),
                    native_type=native_type,
                    nullable=col.get("nullable", True),
                    primary_key=col["name"] in pk_columns,
                    default_value=str(col["default"]) if col.get("default") else None,
                )
            )

        # Indexes
        raw_indexes = insp.get_indexes(table_name, schema=self._schema)
        indexes = [
            IndexSchema(
                name=idx.get("name", ""),
                columns=idx.get("column_names", []),
                unique=idx.get("unique", False),
            )
            for idx in raw_indexes
            if idx.get("name")
        ]

        # Foreign keys
        raw_fks = insp.get_foreign_keys(table_name, schema=self._schema)
        foreign_keys = [
            ForeignKeySchema(
                name=fk.get("name", ""),
                columns=fk.get("constrained_columns", []),
                referenced_table=fk.get("referred_table", ""),
                referenced_columns=fk.get("referred_columns", []),
            )
            for fk in raw_fks
        ]

        # Row count estimate
        row_count = self._get_row_count(table_name)

        return TableSchema(
            name=table_name,
            schema_name=self._schema,
            columns=columns,
            primary_key=pk_columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            row_count=row_count,
        )

    async def discover_schema(self) -> DataSourceSchema:
        """Full schema discovery for all tables."""
        table_names = await self.list_tables()
        tables = [await self.discover_table(name) for name in table_names]
        return DataSourceSchema(
            source_name=self._source_name,
            source_type=DataSourceType.MSSQL,
            tables=tables,
            discovered_at=datetime.utcnow(),
        )

    def _get_row_count(self, table_name: str) -> int | None:
        """Get approximate row count from sys.dm_db_partition_stats."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT SUM(p.rows) "
                        "FROM sys.partitions p "
                        "INNER JOIN sys.tables t ON p.object_id = t.object_id "
                        "INNER JOIN sys.schemas s ON t.schema_id = s.schema_id "
                        "WHERE t.name = :table_name AND s.name = :schema_name "
                        "AND p.index_id IN (0, 1)"
                    ),
                    {"table_name": table_name, "schema_name": self._schema},
                )
                row = result.fetchone()
                return int(row[0]) if row and row[0] is not None else None
        except Exception:
            return None
