"""AI Context Builder — generates schema + data context for LLM consumption.

This module builds structured context objects that give an LLM
everything it needs to understand the facility data and generate
queries or answer questions about it (per AICMMS Query Interface spec).
"""

from __future__ import annotations

import logging
from typing import Any

from cafm.schema.models import DataSourceSchema, TableSchema

logger = logging.getLogger(__name__)


class AIContext:
    """Builds rich context objects for LLM consumption."""

    def __init__(self, integration_manager: Any) -> None:
        """
        Args:
            integration_manager: An IntegrationManager instance.
                Typed as Any to avoid circular imports.
        """
        self._manager = integration_manager

    async def build_schema_context(
        self, source_name: str | None = None
    ) -> dict[str, Any]:
        """Build a structured context suitable for LLM system prompts.

        Returns a dict like::

            {
                "sources": [{"name": ..., "type": ..., "tables_count": ...}],
                "tables": [
                    {
                        "source": "facility_db",
                        "name": "assets",
                        "description": "...",
                        "columns": [{"name": ..., "type": ..., "nullable": ...}],
                        "primary_key": [...],
                        "relationships": [...],
                        "row_count": 2847
                    }
                ]
            }
        """
        if source_name:
            schemas = {source_name: await self._manager.get_source_schema(source_name)}
        else:
            schemas = await self._manager.get_all_schemas()

        sources: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []

        for name, schema in schemas.items():
            sources.append({
                "name": name,
                "type": str(schema.source_type),
                "tables_count": schema.table_count,
            })

            for table in schema.tables:
                tables.append(self._table_to_context(name, table))

        return {"sources": sources, "tables": tables}

    def _table_to_context(self, source: str, table: TableSchema) -> dict[str, Any]:
        """Convert a TableSchema to an LLM-friendly dict."""
        columns = [
            {
                "name": col.name,
                "type": str(col.unified_type),
                "native_type": col.native_type,
                "nullable": col.nullable,
                "primary_key": col.primary_key,
                "description": col.description,
            }
            for col in table.columns
        ]

        relationships = [
            {
                "from": f"{table.name}.{', '.join(fk.columns)}",
                "to": f"{fk.referenced_table}.{', '.join(fk.referenced_columns)}",
                "type": "many-to-one",
            }
            for fk in table.foreign_keys
        ]

        return {
            "source": source,
            "name": table.name,
            "schema": table.schema_name,
            "description": table.description,
            "columns": columns,
            "primary_key": table.primary_key,
            "relationships": relationships,
            "row_count": table.row_count,
        }

    async def build_nl_schema_description(
        self, source_name: str | None = None
    ) -> str:
        """Generate natural language description of the schema for LLM.

        Produces a text block like:

            Source "facility_db" (postgresql) contains 15 tables:

            Table "assets" (2847 rows):
              - asset_id (string, PK): Unique asset identifier
              - name (string): Human-readable asset name
              ...
        """
        context = await self.build_schema_context(source_name)
        lines: list[str] = []

        for src in context["sources"]:
            lines.append(f'Source "{src["name"]}" ({src["type"]}) contains {src["tables_count"]} tables:\n')

        for table in context["tables"]:
            row_info = f" ({table['row_count']} rows)" if table.get("row_count") else ""
            lines.append(f'Table "{table["name"]}"{row_info}:')

            for col in table["columns"]:
                pk_marker = ", PK" if col["primary_key"] else ""
                null_marker = ", nullable" if col["nullable"] else ""
                desc = f": {col['description']}" if col.get("description") else ""
                lines.append(f'  - {col["name"]} ({col["type"]}{pk_marker}{null_marker}){desc}')

            if table.get("relationships"):
                for rel in table["relationships"]:
                    lines.append(f'  FK: {rel["from"]} -> {rel["to"]}')
            lines.append("")

        return "\n".join(lines)

    async def get_sample_data(
        self, source_name: str, table: str, n: int = 5
    ) -> list[dict[str, Any]]:
        """Get sample rows from a table for few-shot prompting."""
        result = await self._manager.query(source_name, table, limit=n)
        return result.as_dicts()
