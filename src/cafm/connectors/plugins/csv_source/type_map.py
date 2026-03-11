"""Pandas / NumPy dtype -> UnifiedDataType mapping.

Shared by both the CSV and Excel connectors.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cafm.core.types import UnifiedDataType

# Maps pandas/numpy dtype kind codes to unified types.
# See: https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html
_DTYPE_KIND_MAP: dict[str, UnifiedDataType] = {
    "i": UnifiedDataType.INTEGER,   # signed integer
    "u": UnifiedDataType.INTEGER,   # unsigned integer
    "f": UnifiedDataType.FLOAT,     # floating-point
    "b": UnifiedDataType.BOOLEAN,   # boolean
    "M": UnifiedDataType.DATETIME,  # datetime64
    "m": UnifiedDataType.STRING,    # timedelta64 -> treat as string
    "U": UnifiedDataType.STRING,    # Unicode string
    "S": UnifiedDataType.STRING,    # byte string
    "O": UnifiedDataType.STRING,    # object (usually mixed / Python strings)
}

# Maps pandas dtype name strings to unified types (for named dtypes).
PANDAS_TYPE_MAP: dict[str, UnifiedDataType] = {
    "int8": UnifiedDataType.INTEGER,
    "int16": UnifiedDataType.INTEGER,
    "int32": UnifiedDataType.INTEGER,
    "int64": UnifiedDataType.INTEGER,
    "uint8": UnifiedDataType.INTEGER,
    "uint16": UnifiedDataType.INTEGER,
    "uint32": UnifiedDataType.INTEGER,
    "uint64": UnifiedDataType.INTEGER,
    "float16": UnifiedDataType.FLOAT,
    "float32": UnifiedDataType.FLOAT,
    "float64": UnifiedDataType.FLOAT,
    "bool": UnifiedDataType.BOOLEAN,
    "boolean": UnifiedDataType.BOOLEAN,
    "object": UnifiedDataType.STRING,
    "string": UnifiedDataType.STRING,
    "category": UnifiedDataType.STRING,
    "datetime64": UnifiedDataType.DATETIME,
    "datetime64[ns]": UnifiedDataType.DATETIME,
    "datetime64[us]": UnifiedDataType.DATETIME,
    "datetime64[ms]": UnifiedDataType.DATETIME,
    "timedelta64": UnifiedDataType.STRING,
    "timedelta64[ns]": UnifiedDataType.STRING,
}

# Nullable integer/boolean types introduced in recent pandas versions.
for _bits in (8, 16, 32, 64):
    PANDAS_TYPE_MAP[f"Int{_bits}"] = UnifiedDataType.INTEGER
    PANDAS_TYPE_MAP[f"UInt{_bits}"] = UnifiedDataType.INTEGER
PANDAS_TYPE_MAP["boolean"] = UnifiedDataType.BOOLEAN
PANDAS_TYPE_MAP["Float32"] = UnifiedDataType.FLOAT
PANDAS_TYPE_MAP["Float64"] = UnifiedDataType.FLOAT
PANDAS_TYPE_MAP["string"] = UnifiedDataType.STRING


def map_pandas_dtype(dtype: np.dtype | pd.api.types.CategoricalDtype) -> UnifiedDataType:  # type: ignore[type-arg]
    """Map a pandas/numpy dtype to a UnifiedDataType."""
    dtype_str = str(dtype)

    # Direct name lookup first
    if dtype_str in PANDAS_TYPE_MAP:
        return PANDAS_TYPE_MAP[dtype_str]

    # Try kind-code lookup for numpy dtypes
    try:
        kind = dtype.kind  # type: ignore[union-attr]
        if kind in _DTYPE_KIND_MAP:
            return _DTYPE_KIND_MAP[kind]
    except AttributeError:
        pass

    # Category dtype
    if isinstance(dtype, pd.CategoricalDtype):
        return UnifiedDataType.STRING

    return UnifiedDataType.UNKNOWN


def pandas_dtype_name(dtype: np.dtype | pd.api.types.CategoricalDtype) -> str:  # type: ignore[type-arg]
    """Return a clean native type string for a pandas dtype."""
    return str(dtype)
