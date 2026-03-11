"""MySQL connector implementation using SQLAlchemy."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar

from sqlalchemy import MetaData, Table, create_engine, func, select, text
from sqlalchemy.engine import Engine

from cafm.connectors.base import Connector, ConnectorConfig, SchemaInspector
from cafm.connectors.plugins.mysql.schema_inspector import MySQLSchemaInspector
from cafm.core.exceptions import ConnectionError, QueryError
from cafm.core.types import ConnectorState, DataSourceType, RawRow


class MySQLConnector(Connector):
    """Connector for MySQL databases.

    Expected ``connection_params``::

        {
            "host": "localhost",
            "port": 3306,
            "database": "mydb",
            "username": "user",
            "password": "pass"
        }

    Or provide a ``url`` key with a full SQLAlchemy connection string.
    """

    source_type: ClassVar[DataSourceType] = DataSourceType.MYSQL

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._engine: Engine | None = None
        self._metadata: MetaData | None = None

    def _build_url(self) -> str:
        params = self._config.connection_params
        if "url" in params:
            return params["url"]
        host = params.get("host", "localhost")
        port = params.get("port", 3306)
        database = params.get("database", "")
        username = params.get("username", "")
        password = params.get("password", "")
        charset = params.get("charset", "utf8mb4")
        return (
            f"mysql+pymysql://{username}:{password}@{host}:{port}"
            f"/{database}?charset={charset}"
        )

    # ── Lifecycle ─────────────────────────────────────────────────

    async def connect(self) -> None:
        try:
            self._state = ConnectorState.CONNECTING
            url = self._build_url()
            self._engine = create_engine(
                url,
                pool_size=self._config.options.get("pool_size", 5),
                pool_pre_ping=True,
            )
            # Verify connectivity
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._metadata = MetaData()
            self._metadata.reflect(bind=self._engine)
            self._state = ConnectorState.CONNECTED
        except Exception as exc:
            self._state = ConnectorState.ERROR
            raise ConnectionError(f"Failed to connect to MySQL: {exc}") from exc

    async def disconnect(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._metadata = None
        self._state = ConnectorState.DISCONNECTED

    async def health_check(self) -> bool:
        if self._engine is None:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    # ── Schema ────────────────────────────────────────────────────

    def get_schema_inspector(self) -> SchemaInspector:
        if self._engine is None:
            raise ConnectionError("Not connected")
        return MySQLSchemaInspector(
            engine=self._engine,
            source_name=self.name,
            sample_size=self._config.options.get("sample_size", 5),
        )

    # ── Read ──────────────────────────────────────────────────────

    def _get_table(self, table_name: str) -> Table:
        if self._metadata is None or self._engine is None:
            raise ConnectionError("Not connected")
        table = self._metadata.tables.get(table_name)
        if table is None:
            raise QueryError(f"Table '{table_name}' not found in reflected metadata")
        return table

    async def fetch_rows(
        self,
        table: str,
        columns: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RawRow]:
        sa_table = self._get_table(table)

        if columns:
            cols = [sa_table.c[c] for c in columns]
            stmt = select(*cols)
        else:
            stmt = select(sa_table)

        if filters:
            for col_name, value in filters.items():
                stmt = stmt.where(sa_table.c[col_name] == value)

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        try:
            with self._engine.connect() as conn:  # type: ignore[union-attr]
                result = conn.execute(stmt)
                return [dict(row._mapping) for row in result]
        except Exception as exc:
            raise QueryError(f"Query failed on {table}: {exc}") from exc

    async def count_rows(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
    ) -> int:
        sa_table = self._get_table(table)
        stmt = select(func.count()).select_from(sa_table)

        if filters:
            for col_name, value in filters.items():
                stmt = stmt.where(sa_table.c[col_name] == value)

        try:
            with self._engine.connect() as conn:  # type: ignore[union-attr]
                result = conn.execute(stmt)
                return result.scalar() or 0
        except Exception as exc:
            raise QueryError(f"Count failed on {table}: {exc}") from exc

    # ── Write ─────────────────────────────────────────────────────

    async def insert_rows(self, table: str, rows: list[RawRow]) -> int:
        sa_table = self._get_table(table)
        try:
            with self._engine.begin() as conn:  # type: ignore[union-attr]
                conn.execute(sa_table.insert(), rows)
            return len(rows)
        except Exception as exc:
            raise QueryError(f"Insert failed on {table}: {exc}") from exc

    async def update_rows(
        self, table: str, filters: dict[str, Any], updates: dict[str, Any]
    ) -> int:
        sa_table = self._get_table(table)
        stmt = sa_table.update().values(**updates)
        for col_name, value in filters.items():
            stmt = stmt.where(sa_table.c[col_name] == value)
        try:
            with self._engine.begin() as conn:  # type: ignore[union-attr]
                result = conn.execute(stmt)
                return result.rowcount
        except Exception as exc:
            raise QueryError(f"Update failed on {table}: {exc}") from exc

    async def delete_rows(self, table: str, filters: dict[str, Any]) -> int:
        sa_table = self._get_table(table)
        stmt = sa_table.delete()
        for col_name, value in filters.items():
            stmt = stmt.where(sa_table.c[col_name] == value)
        try:
            with self._engine.begin() as conn:  # type: ignore[union-attr]
                result = conn.execute(stmt)
                return result.rowcount
        except Exception as exc:
            raise QueryError(f"Delete failed on {table}: {exc}") from exc

    # ── Raw ───────────────────────────────────────────────────────

    async def execute_raw(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[RawRow]:
        if self._engine is None:
            raise ConnectionError("Not connected")
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return [dict(row._mapping) for row in result]
        except Exception as exc:
            raise QueryError(f"Raw query failed: {exc}") from exc
