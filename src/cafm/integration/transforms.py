"""Built-in data transformation functions for pipelines."""

from __future__ import annotations

from typing import Any, Callable

from cafm.core.types import RawRow


# Transform type: takes a list of rows, returns a transformed list
TransformFn = Callable[[list[RawRow]], list[RawRow]]


def rename_fields(mapping: dict[str, str]) -> TransformFn:
    """Rename field keys in each row.

    Args:
        mapping: ``{"old_name": "new_name", ...}``
    """
    def _transform(rows: list[RawRow]) -> list[RawRow]:
        result = []
        for row in rows:
            new_row = {}
            for k, v in row.items():
                new_row[mapping.get(k, k)] = v
            result.append(new_row)
        return result
    return _transform


def select_fields(fields: list[str]) -> TransformFn:
    """Keep only the specified fields, dropping the rest."""
    def _transform(rows: list[RawRow]) -> list[RawRow]:
        return [{k: row.get(k) for k in fields} for row in rows]
    return _transform


def exclude_fields(fields: list[str]) -> TransformFn:
    """Remove specified fields from each row."""
    field_set = set(fields)
    def _transform(rows: list[RawRow]) -> list[RawRow]:
        return [{k: v for k, v in row.items() if k not in field_set} for row in rows]
    return _transform


def cast_fields(type_map: dict[str, str]) -> TransformFn:
    """Cast field values to specified types.

    Supported type strings: "str", "int", "float", "bool".
    """
    casters: dict[str, Callable[[Any], Any]] = {
        "str": str,
        "int": lambda v: int(float(v)) if v is not None else None,
        "float": lambda v: float(v) if v is not None else None,
        "bool": lambda v: bool(v) if v is not None else None,
    }

    def _transform(rows: list[RawRow]) -> list[RawRow]:
        result = []
        for row in rows:
            new_row = dict(row)
            for field, type_name in type_map.items():
                if field in new_row and type_name in casters:
                    try:
                        new_row[field] = casters[type_name](new_row[field])
                    except (ValueError, TypeError):
                        pass  # Leave as-is on failure
            result.append(new_row)
        return result
    return _transform


def filter_rows(predicate: Callable[[RawRow], bool]) -> TransformFn:
    """Keep only rows matching the predicate."""
    def _transform(rows: list[RawRow]) -> list[RawRow]:
        return [row for row in rows if predicate(row)]
    return _transform


def add_static_fields(fields: dict[str, Any]) -> TransformFn:
    """Add static key-value pairs to every row."""
    def _transform(rows: list[RawRow]) -> list[RawRow]:
        return [{**row, **fields} for row in rows]
    return _transform


def deduplicate(key_fields: list[str]) -> TransformFn:
    """Remove duplicate rows based on a composite key."""
    def _transform(rows: list[RawRow]) -> list[RawRow]:
        seen: set[tuple[Any, ...]] = set()
        result = []
        for row in rows:
            key = tuple(row.get(f) for f in key_fields)
            if key not in seen:
                seen.add(key)
                result.append(row)
        return result
    return _transform


def chain_transforms(*transforms: TransformFn) -> TransformFn:
    """Compose multiple transforms into a single pipeline."""
    def _transform(rows: list[RawRow]) -> list[RawRow]:
        for t in transforms:
            rows = t(rows)
        return rows
    return _transform


# Registry of built-in transforms by name
BUILTIN_TRANSFORMS: dict[str, Callable[..., TransformFn]] = {
    "rename": rename_fields,
    "select": select_fields,
    "exclude": exclude_fields,
    "cast": cast_fields,
    "filter": filter_rows,
    "add_fields": add_static_fields,
    "deduplicate": deduplicate,
}
