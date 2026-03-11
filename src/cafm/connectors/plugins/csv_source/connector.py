"""CSV file connector implementation using pandas."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd

from cafm.connectors.base import Connector, ConnectorConfig, SchemaInspector
from cafm.connectors.plugins.csv_source.type_map import map_pandas_dtype, pandas_dtype_name
from cafm.core.exceptions import ConnectionError, QueryError
from cafm.core.types import ConnectorState, DataSourceType, RawRow
from cafm.schema.models import ColumnSchema, DataSourceSchema, TableSchema

logger = logging.getLogger(__name__)


class CSVSchemaInspector(SchemaInspector):
    """Infers schema from CSV files using pandas dtype detection."""

    def __init__(
        self,
        tables: dict[str, Path],
        source_name: str,
        sample_size: int = 1000,
    ) -> None:
        self._tables = tables
        self._source_name = source_name
        self._sample_size = sample_size

    async def list_tables(self) -> list[str]:
        return sorted(self._tables.keys())

    async def discover_table(self, table_name: str) -> TableSchema:
        path = self._tables.get(table_name)
        if path is None:
            raise QueryError(f"CSV table '{table_name}' not found")

        df = pd.read_csv(path, nrows=self._sample_size)
        columns: list[ColumnSchema] = []
        for col_name in df.columns:
            dtype = df[col_name].dtype
            columns.append(
                ColumnSchema(
                    name=str(col_name),
                    unified_type=map_pandas_dtype(dtype),
                    native_type=pandas_dtype_name(dtype),
                    nullable=bool(df[col_name].isna().any()),
                )
            )

        # Count total rows (read only the first column for speed)
        try:
            total = sum(1 for _ in open(path, encoding="utf-8")) - 1  # subtract header
            row_count = max(total, 0)
        except Exception:
            row_count = len(df)

        return TableSchema(
            name=table_name,
            columns=columns,
            row_count=row_count,
        )

    async def discover_schema(self) -> DataSourceSchema:
        table_names = await self.list_tables()
        tables = [await self.discover_table(name) for name in table_names]
        return DataSourceSchema(
            source_name=self._source_name,
            source_type=DataSourceType.CSV,
            tables=tables,
            discovered_at=datetime.utcnow(),
        )


class CSVConnector(Connector):
    """Connector for CSV files.

    Expected ``connection_params``::

        {
            "file_path": "/path/to/data.csv"
        }

    Or for a directory of CSVs::

        {
            "directory": "/path/to/csv_folder"
        }

    When a single file is specified, the table name is the file stem
    (e.g. ``data`` for ``data.csv``).  When a directory is specified,
    each ``.csv`` file becomes a table.

    Options::

        {
            "delimiter": ",",
            "encoding": "utf-8",
            "sample_size": 1000
        }
    """

    source_type: ClassVar[DataSourceType] = DataSourceType.CSV

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._tables: dict[str, Path] = {}
        self._delimiter: str = config.options.get("delimiter", ",")
        self._encoding: str = config.options.get("encoding", "utf-8")

    # ── Lifecycle ─────────────────────────────────────────────────

    async def connect(self) -> None:
        try:
            self._state = ConnectorState.CONNECTING
            params = self._config.connection_params

            if "file_path" in params:
                path = Path(params["file_path"])
                if not path.exists():
                    raise FileNotFoundError(f"CSV file not found: {path}")
                if not path.is_file():
                    raise ValueError(f"Path is not a file: {path}")
                self._tables[path.stem] = path

            elif "directory" in params:
                directory = Path(params["directory"])
                if not directory.exists():
                    raise FileNotFoundError(f"Directory not found: {directory}")
                if not directory.is_dir():
                    raise ValueError(f"Path is not a directory: {directory}")
                csv_files = sorted(directory.glob("*.csv"))
                if not csv_files:
                    raise FileNotFoundError(f"No CSV files found in {directory}")
                for csv_file in csv_files:
                    self._tables[csv_file.stem] = csv_file
            else:
                raise ValueError(
                    "connection_params must include 'file_path' or 'directory'"
                )

            # Validate that we can read headers from every file
            for table_name, path in self._tables.items():
                pd.read_csv(
                    path,
                    nrows=0,
                    delimiter=self._delimiter,
                    encoding=self._encoding,
                )

            self._state = ConnectorState.CONNECTED
            logger.info(
                "CSV connector ready: %d table(s) — %s",
                len(self._tables),
                list(self._tables.keys()),
            )
        except Exception as exc:
            self._state = ConnectorState.ERROR
            raise ConnectionError(f"Failed to connect to CSV source: {exc}") from exc

    async def disconnect(self) -> None:
        self._tables.clear()
        self._state = ConnectorState.DISCONNECTED

    async def health_check(self) -> bool:
        return all(path.exists() for path in self._tables.values())

    # ── Schema ────────────────────────────────────────────────────

    def get_schema_inspector(self) -> SchemaInspector:
        if not self._tables:
            raise ConnectionError("Not connected")
        return CSVSchemaInspector(
            tables=self._tables,
            source_name=self.name,
            sample_size=self._config.options.get("sample_size", 1000),
        )

    # ── Helpers ───────────────────────────────────────────────────

    def _resolve_path(self, table: str) -> Path:
        path = self._tables.get(table)
        if path is None:
            raise QueryError(
                f"Table '{table}' not found. Available: {list(self._tables.keys())}"
            )
        return path

    def _read_csv(self, path: Path) -> pd.DataFrame:
        return pd.read_csv(path, delimiter=self._delimiter, encoding=self._encoding)

    @staticmethod
    def _apply_filters(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
        """Apply simple equality filters to a DataFrame."""
        for col_name, value in filters.items():
            if col_name in df.columns:
                df = df[df[col_name] == value]
        return df

    # ── Read ──────────────────────────────────────────────────────

    async def fetch_rows(
        self,
        table: str,
        columns: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RawRow]:
        path = self._resolve_path(table)
        try:
            df = self._read_csv(path)

            if filters:
                df = self._apply_filters(df, filters)

            if offset:
                df = df.iloc[offset:]

            if limit is not None:
                df = df.iloc[:limit]

            if columns:
                df = df[list(columns)]

            # Replace NaN with None for cleaner output
            df = df.where(pd.notna(df), None)
            return df.to_dict(orient="records")
        except QueryError:
            raise
        except Exception as exc:
            raise QueryError(f"Query failed on {table}: {exc}") from exc

    async def count_rows(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
    ) -> int:
        path = self._resolve_path(table)
        try:
            df = self._read_csv(path)
            if filters:
                df = self._apply_filters(df, filters)
            return len(df)
        except QueryError:
            raise
        except Exception as exc:
            raise QueryError(f"Count failed on {table}: {exc}") from exc

    # ── Write ─────────────────────────────────────────────────────

    async def insert_rows(self, table: str, rows: list[RawRow]) -> int:
        path = self._resolve_path(table)
        if not rows:
            return 0
        try:
            new_df = pd.DataFrame(rows)
            # Append without overwriting: write header only if file is empty/new
            new_df.to_csv(
                path,
                mode="a",
                header=not path.exists() or path.stat().st_size == 0,
                index=False,
                sep=self._delimiter,
                encoding=self._encoding,
            )
            return len(rows)
        except Exception as exc:
            raise QueryError(f"Insert failed on {table}: {exc}") from exc
