"""Excel file connector implementation using pandas + openpyxl."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd

from cafm.connectors.base import Connector, ConnectorConfig, SchemaInspector
from cafm.connectors.plugins.excel.type_map import map_pandas_dtype, pandas_dtype_name
from cafm.core.exceptions import ConnectionError, QueryError
from cafm.core.types import ConnectorState, DataSourceType, RawRow
from cafm.schema.models import ColumnSchema, DataSourceSchema, TableSchema

logger = logging.getLogger(__name__)


class ExcelSchemaInspector(SchemaInspector):
    """Infers schema from Excel sheets using pandas dtype detection."""

    def __init__(
        self,
        file_path: Path,
        sheet_names: list[str],
        source_name: str,
        sample_size: int = 1000,
    ) -> None:
        self._file_path = file_path
        self._sheet_names = sheet_names
        self._source_name = source_name
        self._sample_size = sample_size

    async def list_tables(self) -> list[str]:
        return list(self._sheet_names)

    async def discover_table(self, table_name: str) -> TableSchema:
        if table_name not in self._sheet_names:
            raise QueryError(f"Sheet '{table_name}' not found in workbook")

        df = pd.read_excel(
            self._file_path,
            sheet_name=table_name,
            nrows=self._sample_size,
            engine="openpyxl",
        )

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

        # Get total row count by reading entire sheet length column
        try:
            full_df = pd.read_excel(
                self._file_path,
                sheet_name=table_name,
                usecols=[0],
                engine="openpyxl",
            )
            row_count = len(full_df)
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
            source_type=DataSourceType.EXCEL,
            tables=tables,
            discovered_at=datetime.utcnow(),
        )


class ExcelConnector(Connector):
    """Connector for Excel (.xlsx) files.

    Expected ``connection_params``::

        {
            "file_path": "/path/to/workbook.xlsx"
        }

    Each worksheet is treated as a separate table. Use the sheet name
    as the ``table`` argument to ``fetch_rows`` and other methods.

    Options::

        {
            "sample_size": 1000
        }
    """

    source_type: ClassVar[DataSourceType] = DataSourceType.EXCEL

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._file_path: Path | None = None
        self._sheet_names: list[str] = []

    # ── Lifecycle ─────────────────────────────────────────────────

    async def connect(self) -> None:
        try:
            self._state = ConnectorState.CONNECTING
            params = self._config.connection_params

            file_path_str = params.get("file_path")
            if not file_path_str:
                raise ValueError("connection_params must include 'file_path'")

            path = Path(file_path_str)
            if not path.exists():
                raise FileNotFoundError(f"Excel file not found: {path}")
            if not path.is_file():
                raise ValueError(f"Path is not a file: {path}")

            # Read sheet names to validate the file
            xl = pd.ExcelFile(path, engine="openpyxl")
            self._sheet_names = xl.sheet_names
            xl.close()

            if not self._sheet_names:
                raise ValueError(f"No sheets found in {path}")

            self._file_path = path
            self._state = ConnectorState.CONNECTED
            logger.info(
                "Excel connector ready: %d sheet(s) in %s — %s",
                len(self._sheet_names),
                path.name,
                self._sheet_names,
            )
        except Exception as exc:
            self._state = ConnectorState.ERROR
            raise ConnectionError(f"Failed to connect to Excel source: {exc}") from exc

    async def disconnect(self) -> None:
        self._file_path = None
        self._sheet_names.clear()
        self._state = ConnectorState.DISCONNECTED

    async def health_check(self) -> bool:
        return self._file_path is not None and self._file_path.exists()

    # ── Schema ────────────────────────────────────────────────────

    def get_schema_inspector(self) -> SchemaInspector:
        if self._file_path is None:
            raise ConnectionError("Not connected")
        return ExcelSchemaInspector(
            file_path=self._file_path,
            sheet_names=self._sheet_names,
            source_name=self.name,
            sample_size=self._config.options.get("sample_size", 1000),
        )

    # ── Helpers ───────────────────────────────────────────────────

    def _ensure_connected(self) -> Path:
        if self._file_path is None:
            raise ConnectionError("Not connected")
        return self._file_path

    def _validate_sheet(self, sheet_name: str) -> None:
        if sheet_name not in self._sheet_names:
            raise QueryError(
                f"Sheet '{sheet_name}' not found. "
                f"Available: {self._sheet_names}"
            )

    def _read_sheet(self, sheet_name: str) -> pd.DataFrame:
        path = self._ensure_connected()
        self._validate_sheet(sheet_name)
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")

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
        try:
            df = self._read_sheet(table)

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
        except (ConnectionError, QueryError):
            raise
        except Exception as exc:
            raise QueryError(f"Query failed on sheet '{table}': {exc}") from exc

    async def count_rows(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
    ) -> int:
        try:
            df = self._read_sheet(table)
            if filters:
                df = self._apply_filters(df, filters)
            return len(df)
        except (ConnectionError, QueryError):
            raise
        except Exception as exc:
            raise QueryError(f"Count failed on sheet '{table}': {exc}") from exc

    # ── Write ─────────────────────────────────────────────────────

    async def insert_rows(self, table: str, rows: list[RawRow]) -> int:
        """Append rows to a sheet in the Excel workbook.

        Reads the entire workbook, appends rows to the target sheet,
        and writes back.  This is necessary because openpyxl does not
        support true in-place append for ``.xlsx`` files.
        """
        path = self._ensure_connected()
        self._validate_sheet(table)
        if not rows:
            return 0

        try:
            # Read all sheets into memory
            all_sheets: dict[str, pd.DataFrame] = pd.read_excel(
                path, sheet_name=None, engine="openpyxl"
            )

            # Append to the target sheet
            new_df = pd.DataFrame(rows)
            existing_df = all_sheets.get(table, pd.DataFrame())
            all_sheets[table] = pd.concat([existing_df, new_df], ignore_index=True)

            # Write everything back
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                for sheet_name, sheet_df in all_sheets.items():
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

            return len(rows)
        except Exception as exc:
            raise QueryError(f"Insert failed on sheet '{table}': {exc}") from exc
