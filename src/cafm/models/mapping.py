"""Source-to-unified field mapping rules.

Declarative mapping definitions that transform source field names
and types into the unified model representation.
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from cafm.core.types import RawRow


class FieldMapping(BaseModel):
    """Mapping rule for a single field."""

    source_field: str
    target_field: str
    transform: str | None = None  # Name of a registered transform function
    default_value: Any = None


class TableMapping(BaseModel):
    """Mapping rules for an entire table to a domain model."""

    source_table: str
    target_model: str  # Fully qualified class name, e.g. "cafm.domain.assets.Asset"
    field_mappings: list[FieldMapping] = Field(default_factory=list)
    extra_fields: dict[str, Any] = Field(default_factory=dict)  # Static fields to inject

    def apply(
        self,
        row: RawRow,
        transform_registry: dict[str, Callable[[Any], Any]] | None = None,
    ) -> RawRow:
        """Apply mapping rules to a raw row, producing a unified row."""
        transform_registry = transform_registry or {}
        result: RawRow = dict(self.extra_fields)

        for mapping in self.field_mappings:
            value = row.get(mapping.source_field, mapping.default_value)
            if mapping.transform and mapping.transform in transform_registry:
                value = transform_registry[mapping.transform](value)
            result[mapping.target_field] = value

        return result


class MappingRegistry:
    """Registry of table mappings, indexed by source_table name."""

    def __init__(self) -> None:
        self._mappings: dict[str, TableMapping] = {}
        self._transforms: dict[str, Callable[[Any], Any]] = {}

    def register_mapping(self, mapping: TableMapping) -> None:
        self._mappings[mapping.source_table] = mapping

    def register_transform(self, name: str, func: Callable[[Any], Any]) -> None:
        self._transforms[name] = func

    def get_mapping(self, source_table: str) -> TableMapping | None:
        return self._mappings.get(source_table)

    def apply(self, source_table: str, row: RawRow) -> RawRow:
        """Apply the registered mapping for a source table to a row."""
        mapping = self._mappings.get(source_table)
        if mapping is None:
            return row  # Pass through if no mapping registered
        return mapping.apply(row, self._transforms)
