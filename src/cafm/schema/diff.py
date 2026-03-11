"""Schema comparison and drift detection.

Compares two DataSourceSchema snapshots and reports what changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from cafm.schema.models import ColumnSchema, DataSourceSchema, TableSchema


class ChangeType(StrEnum):
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_TYPE_CHANGED = "column_type_changed"
    COLUMN_NULLABLE_CHANGED = "column_nullable_changed"
    ROW_COUNT_CHANGED = "row_count_changed"


@dataclass(frozen=True)
class SchemaChange:
    """A single schema change between two snapshots."""

    change_type: ChangeType
    table_name: str
    column_name: str | None = None
    old_value: Any = None
    new_value: Any = None

    def __str__(self) -> str:
        parts = [f"[{self.change_type}] {self.table_name}"]
        if self.column_name:
            parts.append(f".{self.column_name}")
        if self.old_value is not None or self.new_value is not None:
            parts.append(f": {self.old_value!r} -> {self.new_value!r}")
        return "".join(parts)


@dataclass
class SchemaDiff:
    """Result of comparing two schema snapshots."""

    changes: list[SchemaChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def breaking_changes(self) -> list[SchemaChange]:
        """Changes that could break consumers (removals, type changes)."""
        breaking = {
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.COLUMN_TYPE_CHANGED,
        }
        return [c for c in self.changes if c.change_type in breaking]

    def summary(self) -> str:
        if not self.has_changes:
            return "No schema changes detected."
        lines = [f"{len(self.changes)} change(s) detected:"]
        for change in self.changes:
            lines.append(f"  {change}")
        return "\n".join(lines)


def compare_schemas(old: DataSourceSchema, new: DataSourceSchema) -> SchemaDiff:
    """Compare two schema snapshots and return a diff."""
    diff = SchemaDiff()

    old_tables = {t.name: t for t in old.tables}
    new_tables = {t.name: t for t in new.tables}

    # Added tables
    for name in new_tables:
        if name not in old_tables:
            diff.changes.append(SchemaChange(ChangeType.TABLE_ADDED, name))

    # Removed tables
    for name in old_tables:
        if name not in new_tables:
            diff.changes.append(SchemaChange(ChangeType.TABLE_REMOVED, name))

    # Changed tables
    for name in old_tables:
        if name in new_tables:
            _compare_tables(old_tables[name], new_tables[name], diff)

    return diff


def _compare_tables(old: TableSchema, new: TableSchema, diff: SchemaDiff) -> None:
    """Compare two table schemas."""
    old_cols = {c.name: c for c in old.columns}
    new_cols = {c.name: c for c in new.columns}

    for col_name in new_cols:
        if col_name not in old_cols:
            diff.changes.append(
                SchemaChange(ChangeType.COLUMN_ADDED, old.name, col_name)
            )

    for col_name in old_cols:
        if col_name not in new_cols:
            diff.changes.append(
                SchemaChange(ChangeType.COLUMN_REMOVED, old.name, col_name)
            )

    for col_name in old_cols:
        if col_name in new_cols:
            _compare_columns(old.name, old_cols[col_name], new_cols[col_name], diff)

    if old.row_count is not None and new.row_count is not None:
        if old.row_count != new.row_count:
            diff.changes.append(
                SchemaChange(
                    ChangeType.ROW_COUNT_CHANGED,
                    old.name,
                    old_value=old.row_count,
                    new_value=new.row_count,
                )
            )


def _compare_columns(
    table_name: str, old: ColumnSchema, new: ColumnSchema, diff: SchemaDiff
) -> None:
    """Compare two column schemas."""
    if old.unified_type != new.unified_type:
        diff.changes.append(
            SchemaChange(
                ChangeType.COLUMN_TYPE_CHANGED,
                table_name,
                old.name,
                old_value=old.unified_type,
                new_value=new.unified_type,
            )
        )

    if old.nullable != new.nullable:
        diff.changes.append(
            SchemaChange(
                ChangeType.COLUMN_NULLABLE_CHANGED,
                table_name,
                old.name,
                old_value=old.nullable,
                new_value=new.nullable,
            )
        )
