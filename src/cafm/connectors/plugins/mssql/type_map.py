"""MSSQL (SQL Server) native type -> UnifiedDataType mapping."""

from __future__ import annotations

from cafm.core.types import UnifiedDataType

# Maps lowercased SQL Server type names to unified types.
MSSQL_TYPE_MAP: dict[str, UnifiedDataType] = {
    # Integer types
    "int": UnifiedDataType.INTEGER,
    "integer": UnifiedDataType.INTEGER,
    "bigint": UnifiedDataType.INTEGER,
    "smallint": UnifiedDataType.INTEGER,
    "tinyint": UnifiedDataType.INTEGER,
    # Bit (boolean)
    "bit": UnifiedDataType.BOOLEAN,
    # Float / Real
    "float": UnifiedDataType.FLOAT,
    "real": UnifiedDataType.FLOAT,
    # Decimal / Numeric / Money
    "decimal": UnifiedDataType.DECIMAL,
    "numeric": UnifiedDataType.DECIMAL,
    "money": UnifiedDataType.DECIMAL,
    "smallmoney": UnifiedDataType.DECIMAL,
    # String types (non-Unicode)
    "char": UnifiedDataType.STRING,
    "varchar": UnifiedDataType.STRING,
    "text": UnifiedDataType.TEXT,
    # String types (Unicode)
    "nchar": UnifiedDataType.STRING,
    "nvarchar": UnifiedDataType.STRING,
    "ntext": UnifiedDataType.TEXT,
    # Date / Time types
    "date": UnifiedDataType.DATE,
    "datetime": UnifiedDataType.DATETIME,
    "datetime2": UnifiedDataType.DATETIME,
    "smalldatetime": UnifiedDataType.DATETIME,
    "datetimeoffset": UnifiedDataType.DATETIME,
    "time": UnifiedDataType.TIME,
    # Binary types
    "binary": UnifiedDataType.BINARY,
    "varbinary": UnifiedDataType.BINARY,
    "image": UnifiedDataType.BINARY,
    # Special types
    "uniqueidentifier": UnifiedDataType.UUID,
    "xml": UnifiedDataType.TEXT,
    "sql_variant": UnifiedDataType.UNKNOWN,
    # Hierarchyid / Geography / Geometry (treat as string)
    "hierarchyid": UnifiedDataType.STRING,
    "geography": UnifiedDataType.STRING,
    "geometry": UnifiedDataType.STRING,
    # Timestamp / rowversion
    "timestamp": UnifiedDataType.BINARY,
    "rowversion": UnifiedDataType.BINARY,
}


def map_mssql_type(native_type: str) -> UnifiedDataType:
    """Map a SQL Server type name to a UnifiedDataType.

    Handles parameterized types like ``varchar(255)``, ``nvarchar(max)``,
    ``decimal(18,2)``, etc.
    """
    normalized = native_type.lower().strip()

    # Strip parameters: varchar(255) -> varchar, decimal(18,2) -> decimal
    base_type = normalized.split("(")[0].strip()

    return MSSQL_TYPE_MAP.get(base_type, UnifiedDataType.UNKNOWN)
