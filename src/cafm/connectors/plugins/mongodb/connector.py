"""MongoDB connector implementation using pymongo."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase

from cafm.connectors.base import Connector, ConnectorConfig, SchemaInspector
from cafm.connectors.plugins.mongodb.schema_inspector import MongoDBSchemaInspector
from cafm.core.exceptions import ConnectionError, QueryError
from cafm.core.types import ConnectorState, DataSourceType, RawRow


class MongoDBConnector(Connector):
    """Connector for MongoDB databases.

    Expected ``connection_params``::

        {
            "host": "localhost",
            "port": 27017,
            "database": "mydb",
            "username": "user",     # optional
            "password": "pass",     # optional
            "auth_source": "admin"  # optional
        }

    Or provide a ``url`` key with a full MongoDB connection string and
    a ``database`` key::

        {
            "url": "mongodb://user:pass@host:27017",
            "database": "mydb"
        }
    """

    source_type: ClassVar[DataSourceType] = DataSourceType.MONGODB

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._client: MongoClient | None = None  # type: ignore[type-arg]
        self._db: MongoDatabase | None = None  # type: ignore[type-arg]

    def _build_url(self) -> str:
        params = self._config.connection_params
        if "url" in params:
            return params["url"]
        host = params.get("host", "localhost")
        port = params.get("port", 27017)
        username = params.get("username")
        password = params.get("password")
        auth_source = params.get("auth_source", "admin")
        if username and password:
            return f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_source}"
        return f"mongodb://{host}:{port}/"

    # ── Lifecycle ─────────────────────────────────────────────────

    async def connect(self) -> None:
        try:
            self._state = ConnectorState.CONNECTING
            url = self._build_url()
            database_name = self._config.connection_params.get("database")
            if not database_name:
                self._state = ConnectorState.ERROR
                raise ConnectionError("MongoDB connection_params must include 'database'")

            self._client = MongoClient(
                url,
                serverSelectionTimeoutMS=self._config.options.get(
                    "server_selection_timeout_ms", 5000
                ),
            )
            # Verify connectivity
            self._client.server_info()
            self._db = self._client[database_name]
            self._state = ConnectorState.CONNECTED
        except ConnectionError:
            raise
        except Exception as exc:
            self._state = ConnectorState.ERROR
            raise ConnectionError(f"Failed to connect to MongoDB: {exc}") from exc

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
        self._state = ConnectorState.DISCONNECTED

    async def health_check(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.server_info()
            return True
        except Exception:
            return False

    # ── Schema ────────────────────────────────────────────────────

    def get_schema_inspector(self) -> SchemaInspector:
        if self._db is None:
            raise ConnectionError("Not connected")
        return MongoDBSchemaInspector(
            database=self._db,
            source_name=self.name,
            sample_size=self._config.options.get("sample_size", 100),
        )

    # ── Helpers ───────────────────────────────────────────────────

    def _get_collection(self, name: str) -> Any:
        """Return a pymongo Collection, raising if not connected."""
        if self._db is None:
            raise ConnectionError("Not connected")
        return self._db[name]

    @staticmethod
    def _build_filter(filters: dict[str, Any] | None) -> dict[str, Any]:
        """Convert simple equality filters to a MongoDB query dict.

        Supports basic operators via special prefixes:
            {"age": 25}                  -> {"age": 25}
            {"age__gt": 25}              -> {"age": {"$gt": 25}}
            {"age__gte": 25, "age__lt": 50} -> {"age": {"$gte": 25, "$lt": 50}}
        """
        if not filters:
            return {}

        mongo_filter: dict[str, Any] = {}
        op_suffixes = {
            "__gt": "$gt",
            "__gte": "$gte",
            "__lt": "$lt",
            "__lte": "$lte",
            "__ne": "$ne",
            "__in": "$in",
            "__nin": "$nin",
        }

        for key, value in filters.items():
            matched_op = False
            for suffix, mongo_op in op_suffixes.items():
                if key.endswith(suffix):
                    field = key[: -len(suffix)]
                    mongo_filter.setdefault(field, {})[mongo_op] = value
                    matched_op = True
                    break
            if not matched_op:
                mongo_filter[key] = value

        return mongo_filter

    # ── Read ──────────────────────────────────────────────────────

    async def fetch_rows(
        self,
        table: str,
        columns: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RawRow]:
        collection = self._get_collection(table)
        query = self._build_filter(filters)

        # Build projection
        projection: dict[str, int] | None = None
        if columns:
            projection = {col: 1 for col in columns}
            # Always exclude _id unless explicitly requested
            if "_id" not in columns:
                projection["_id"] = 0

        try:
            cursor = collection.find(query, projection)
            if offset:
                cursor = cursor.skip(offset)
            if limit is not None:
                cursor = cursor.limit(limit)

            rows: list[RawRow] = []
            for doc in cursor:
                # Convert ObjectId to string for serialization
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                rows.append(doc)
            return rows
        except Exception as exc:
            raise QueryError(f"Query failed on {table}: {exc}") from exc

    async def count_rows(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
    ) -> int:
        collection = self._get_collection(table)
        query = self._build_filter(filters)
        try:
            return collection.count_documents(query)
        except Exception as exc:
            raise QueryError(f"Count failed on {table}: {exc}") from exc

    # ── Write ─────────────────────────────────────────────────────

    async def insert_rows(self, table: str, rows: list[RawRow]) -> int:
        collection = self._get_collection(table)
        if not rows:
            return 0
        try:
            result = collection.insert_many(rows)
            return len(result.inserted_ids)
        except Exception as exc:
            raise QueryError(f"Insert failed on {table}: {exc}") from exc

    async def update_rows(
        self, table: str, filters: dict[str, Any], updates: dict[str, Any]
    ) -> int:
        collection = self._get_collection(table)
        query = self._build_filter(filters)
        try:
            result = collection.update_many(query, {"$set": updates})
            return result.modified_count
        except Exception as exc:
            raise QueryError(f"Update failed on {table}: {exc}") from exc

    async def delete_rows(self, table: str, filters: dict[str, Any]) -> int:
        collection = self._get_collection(table)
        query = self._build_filter(filters)
        try:
            result = collection.delete_many(query)
            return result.deleted_count
        except Exception as exc:
            raise QueryError(f"Delete failed on {table}: {exc}") from exc
