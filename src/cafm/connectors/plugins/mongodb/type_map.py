"""MongoDB BSON type -> UnifiedDataType mapping."""

from __future__ import annotations

from cafm.core.types import UnifiedDataType

# Maps BSON type names (as returned by $type or inferred from Python types)
# to unified types.
BSON_TYPE_MAP: dict[str, UnifiedDataType] = {
    # String
    "string": UnifiedDataType.STRING,
    "str": UnifiedDataType.STRING,
    # Integer types
    "int": UnifiedDataType.INTEGER,
    "long": UnifiedDataType.INTEGER,
    "int32": UnifiedDataType.INTEGER,
    "int64": UnifiedDataType.INTEGER,
    # Float / Decimal
    "double": UnifiedDataType.FLOAT,
    "decimal": UnifiedDataType.DECIMAL,
    "decimal128": UnifiedDataType.DECIMAL,
    # Boolean
    "bool": UnifiedDataType.BOOLEAN,
    "boolean": UnifiedDataType.BOOLEAN,
    # Date / Time
    "date": UnifiedDataType.DATETIME,
    "datetime": UnifiedDataType.DATETIME,
    "timestamp": UnifiedDataType.DATETIME,
    # ObjectId
    "objectid": UnifiedDataType.STRING,
    "objectId": UnifiedDataType.STRING,
    # Compound types
    "array": UnifiedDataType.ARRAY,
    "list": UnifiedDataType.ARRAY,
    "object": UnifiedDataType.JSON,
    "dict": UnifiedDataType.JSON,
    # Binary
    "bindata": UnifiedDataType.BINARY,
    "binData": UnifiedDataType.BINARY,
    "bytes": UnifiedDataType.BINARY,
    # Null
    "null": UnifiedDataType.UNKNOWN,
    "none": UnifiedDataType.UNKNOWN,
    "NoneType": UnifiedDataType.UNKNOWN,
    # Regex
    "regex": UnifiedDataType.STRING,
}

# Maps Python type names to BSON-style type names for the type_map lookup.
_PYTHON_TYPE_TO_BSON: dict[str, str] = {
    "str": "string",
    "int": "int",
    "float": "double",
    "bool": "bool",
    "datetime": "datetime",
    "date": "date",
    "list": "array",
    "dict": "object",
    "bytes": "bindata",
    "NoneType": "null",
    "ObjectId": "objectId",
    "Decimal128": "decimal128",
    "Regex": "regex",
}


def python_type_name(value: object) -> str:
    """Return the BSON-like type string for a Python value."""
    type_name = type(value).__name__
    return _PYTHON_TYPE_TO_BSON.get(type_name, type_name)


def map_bson_type(bson_type: str) -> UnifiedDataType:
    """Map a BSON / Python type name to a UnifiedDataType."""
    normalized = bson_type.lower().strip()
    return BSON_TYPE_MAP.get(normalized, UnifiedDataType.UNKNOWN)
