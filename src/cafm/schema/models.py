"""Unified schema Pydantic models.

These models represent data source schemas in a source-agnostic way.
Every connector's SchemaInspector produces instances of these models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cafm.core.types import DataSourceType, UnifiedDataType


class ColumnSchema(BaseModel):
    """Unified representation of a column / field / document key."""

    model_config = ConfigDict(frozen=True)

    name: str
    unified_type: UnifiedDataType
    native_type: str  # Original type string from source (e.g. "varchar(255)")
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default_value: str | None = None
    max_length: int | None = None
    description: str | None = None
    sample_values: list[Any] = Field(default_factory=list, max_length=5)
    statistics: dict[str, float] | None = None  # min, max, mean, null_count, cardinality


class IndexSchema(BaseModel):
    """Representation of a database index."""

    model_config = ConfigDict(frozen=True)

    name: str
    columns: list[str]
    unique: bool = False


class ForeignKeySchema(BaseModel):
    """Representation of a foreign key relationship."""

    model_config = ConfigDict(frozen=True)

    name: str
    columns: list[str]
    referenced_table: str
    referenced_columns: list[str]


class TableSchema(BaseModel):
    """Unified representation of a table / collection / sheet."""

    model_config = ConfigDict(frozen=True)

    name: str
    schema_name: str | None = None  # e.g. "public" in PostgreSQL
    columns: list[ColumnSchema]
    primary_key: list[str] = Field(default_factory=list)
    indexes: list[IndexSchema] = Field(default_factory=list)
    foreign_keys: list[ForeignKeySchema] = Field(default_factory=list)
    row_count: int | None = None
    description: str | None = None

    def get_column(self, name: str) -> ColumnSchema | None:
        """Look up a column by name."""
        return next((c for c in self.columns if c.name == name), None)

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


class DataSourceSchema(BaseModel):
    """Complete schema snapshot for a single data source."""

    model_config = ConfigDict(frozen=True)

    source_name: str
    source_type: DataSourceType
    tables: list[TableSchema]
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_table(self, name: str) -> TableSchema | None:
        """Look up a table by name."""
        return next((t for t in self.tables if t.name == name), None)

    @property
    def table_names(self) -> list[str]:
        return [t.name for t in self.tables]

    @property
    def table_count(self) -> int:
        return len(self.tables)
