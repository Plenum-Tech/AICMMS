"""MySQL native type -> UnifiedDataType mapping."""

from __future__ import annotations

from cafm.core.types import UnifiedDataType

# Maps lowercased MySQL type names to unified types.
MYSQL_TYPE_MAP: dict[str, UnifiedDataType] = {
    # Integer types
    "tinyint": UnifiedDataType.INTEGER,
    "smallint": UnifiedDataType.INTEGER,
    "mediumint": UnifiedDataType.INTEGER,
    "int": UnifiedDataType.INTEGER,
    "integer": UnifiedDataType.INTEGER,
    "bigint": UnifiedDataType.INTEGER,
    # Float / Double
    "float": UnifiedDataType.FLOAT,
    "double": UnifiedDataType.FLOAT,
    "double precision": UnifiedDataType.FLOAT,
    "real": UnifiedDataType.FLOAT,
    # Decimal
    "decimal": UnifiedDataType.DECIMAL,
    "numeric": UnifiedDataType.DECIMAL,
    "dec": UnifiedDataType.DECIMAL,
    "fixed": UnifiedDataType.DECIMAL,
    # String types
    "char": UnifiedDataType.STRING,
    "varchar": UnifiedDataType.STRING,
    "tinytext": UnifiedDataType.TEXT,
    "text": UnifiedDataType.TEXT,
    "mediumtext": UnifiedDataType.TEXT,
    "longtext": UnifiedDataType.TEXT,
    # Binary types
    "binary": UnifiedDataType.BINARY,
    "varbinary": UnifiedDataType.BINARY,
    "blob": UnifiedDataType.BINARY,
    "tinyblob": UnifiedDataType.BINARY,
    "mediumblob": UnifiedDataType.BINARY,
    "longblob": UnifiedDataType.BINARY,
    # Date / Time types
    "date": UnifiedDataType.DATE,
    "datetime": UnifiedDataType.DATETIME,
    "timestamp": UnifiedDataType.DATETIME,
    "time": UnifiedDataType.TIME,
    "year": UnifiedDataType.INTEGER,
    # Boolean
    "bool": UnifiedDataType.BOOLEAN,
    "boolean": UnifiedDataType.BOOLEAN,
    # JSON
    "json": UnifiedDataType.JSON,
    # Enum / Set (treated as strings)
    "enum": UnifiedDataType.STRING,
    "set": UnifiedDataType.STRING,
    # Spatial (rare — treat as string)
    "geometry": UnifiedDataType.STRING,
    "point": UnifiedDataType.STRING,
    "linestring": UnifiedDataType.STRING,
    "polygon": UnifiedDataType.STRING,
    # Bit
    "bit": UnifiedDataType.INTEGER,
}


def map_mysql_type(native_type: str) -> UnifiedDataType:
    """Map a MySQL type name to a UnifiedDataType.

    Handles parameterized types like ``varchar(255)`` and display-width
    types like ``int(11)``.
    """
    normalized = native_type.lower().strip()

    # TINYINT(1) is the MySQL boolean idiom
    if normalized.startswith("tinyint(1)"):
        return UnifiedDataType.BOOLEAN

    # Strip parameters: varchar(255) -> varchar, decimal(10,2) -> decimal
    base_type = normalized.split("(")[0].strip()

    # Strip UNSIGNED / SIGNED qualifiers
    base_type = base_type.replace(" unsigned", "").replace(" signed", "").strip()

    return MYSQL_TYPE_MAP.get(base_type, UnifiedDataType.UNKNOWN)
