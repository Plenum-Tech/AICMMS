"""Excel (pandas/openpyxl) dtype -> UnifiedDataType mapping.

Reuses the same pandas dtype mapping as the CSV connector since both
rely on pandas for type inference.
"""

from __future__ import annotations

# Re-export the shared pandas type mapping utilities.
from cafm.connectors.plugins.csv_source.type_map import (
    PANDAS_TYPE_MAP,
    map_pandas_dtype,
    pandas_dtype_name,
)

__all__ = [
    "PANDAS_TYPE_MAP",
    "map_pandas_dtype",
    "pandas_dtype_name",
]
