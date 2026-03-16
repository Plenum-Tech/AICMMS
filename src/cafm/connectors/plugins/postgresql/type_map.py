"""PostgreSQL native type -> UnifiedDataType mapping."""

from __future__ import annotations

from cafm.core.types import UnifiedDataType

# Maps lowercased PostgreSQL type names to unified types.
PG_TYPE_MAP: dict[str, UnifiedDataType] = {
    # String types
    "character varying": UnifiedDataType.STRING,
    "varchar": UnifiedDataType.STRING,
    "character": UnifiedDataType.STRING,
    "char": UnifiedDataType.STRING,
    "text": UnifiedDataType.TEXT,
    "name": UnifiedDataType.STRING,
    "citext": UnifiedDataType.STRING,
    # Numeric types
    "smallint": UnifiedDataType.INTEGER,
    "integer": UnifiedDataType.INTEGER,
    "bigint": UnifiedDataType.INTEGER,
    "int2": UnifiedDataType.INTEGER,
    "int4": UnifiedDataType.INTEGER,
    "int8": UnifiedDataType.INTEGER,
    "serial": UnifiedDataType.INTEGER,
    "bigserial": UnifiedDataType.INTEGER,
    "real": UnifiedDataType.FLOAT,
    "double precision": UnifiedDataType.FLOAT,
    "float4": UnifiedDataType.FLOAT,
    "float8": UnifiedDataType.FLOAT,
    "numeric": UnifiedDataType.DECIMAL,
    "decimal": UnifiedDataType.DECIMAL,
    "money": UnifiedDataType.DECIMAL,
    # Boolean
    "boolean": UnifiedDataType.BOOLEAN,
    "bool": UnifiedDataType.BOOLEAN,
    # Date/time
    "date": UnifiedDataType.DATE,
    "timestamp without time zone": UnifiedDataType.DATETIME,
    "timestamp with time zone": UnifiedDataType.DATETIME,
    "timestamp": UnifiedDataType.DATETIME,
    "timestamptz": UnifiedDataType.DATETIME,
    "time without time zone": UnifiedDataType.TIME,
    "time with time zone": UnifiedDataType.TIME,
    "time": UnifiedDataType.TIME,
    "interval": UnifiedDataType.STRING,
    # Binary
    "bytea": UnifiedDataType.BINARY,
    # UUID
    "uuid": UnifiedDataType.UUID,
    # JSON
    "json": UnifiedDataType.JSON,
    "jsonb": UnifiedDataType.JSON,
    # Array (generic)
    "array": UnifiedDataType.ARRAY,
    "anyarray": UnifiedDataType.ARRAY,
    # Other
    "xml": UnifiedDataType.TEXT,
    "inet": UnifiedDataType.STRING,
    "cidr": UnifiedDataType.STRING,
    "macaddr": UnifiedDataType.STRING,
    "point": UnifiedDataType.STRING,
    "line": UnifiedDataType.STRING,
    "polygon": UnifiedDataType.STRING,
    "tsvector": UnifiedDataType.STRING,
    "tsquery": UnifiedDataType.STRING,
    "oid": UnifiedDataType.INTEGER,
}


def map_pg_type(native_type: str) -> UnifiedDataType:
    """Map a PostgreSQL type name to a UnifiedDataType.

    Handles parameterized types like ``varchar(255)`` and array types
    like ``integer[]``.
    """
    normalized = native_type.lower().strip()

    # Handle array notation: integer[], text[], etc.
    if normalized.endswith("[]"):
        return UnifiedDataType.ARRAY

    # Handle parameterized types: varchar(255) -> varchar
    base_type = normalized.split("(")[0].strip()

    return PG_TYPE_MAP.get(base_type, UnifiedDataType.UNKNOWN)
