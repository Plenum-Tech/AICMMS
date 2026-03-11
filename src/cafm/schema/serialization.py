"""Schema export to JSON / dict formats."""

from __future__ import annotations

import json
from typing import Any

from cafm.schema.models import DataSourceSchema, TableSchema


def schema_to_dict(schema: DataSourceSchema) -> dict[str, Any]:
    """Convert a DataSourceSchema to a plain dictionary."""
    return schema.model_dump(mode="json")


def schema_to_json(schema: DataSourceSchema, indent: int = 2) -> str:
    """Serialize a DataSourceSchema to a JSON string."""
    return schema.model_dump_json(indent=indent)


def schema_from_dict(data: dict[str, Any]) -> DataSourceSchema:
    """Deserialize a DataSourceSchema from a dictionary."""
    return DataSourceSchema.model_validate(data)


def schema_from_json(json_str: str) -> DataSourceSchema:
    """Deserialize a DataSourceSchema from a JSON string."""
    return DataSourceSchema.model_validate_json(json_str)


def table_to_dict(table: TableSchema) -> dict[str, Any]:
    """Convert a single TableSchema to a plain dictionary."""
    return table.model_dump(mode="json")


def table_summary(table: TableSchema) -> str:
    """One-line summary of a table for display / logging."""
    cols = len(table.columns)
    pks = ", ".join(table.primary_key) if table.primary_key else "none"
    rows = table.row_count if table.row_count is not None else "?"
    return f"{table.name} ({cols} columns, PK: {pks}, ~{rows} rows)"


def schema_summary(schema: DataSourceSchema) -> str:
    """Multi-line summary of a full data source schema."""
    lines = [
        f"Source: {schema.source_name} ({schema.source_type})",
        f"Tables: {schema.table_count}",
        f"Discovered: {schema.discovered_at.isoformat()}",
        "",
    ]
    for table in schema.tables:
        lines.append(f"  - {table_summary(table)}")
    return "\n".join(lines)
