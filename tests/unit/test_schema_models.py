"""Tests for unified schema models."""

from cafm.core.types import DataSourceType, UnifiedDataType
from cafm.schema.models import ColumnSchema, DataSourceSchema, TableSchema
from cafm.schema.diff import compare_schemas, ChangeType
from cafm.schema.serialization import schema_to_json, schema_from_json, schema_summary


def _make_schema(tables=None, name="test_src"):
    return DataSourceSchema(
        source_name=name,
        source_type=DataSourceType.POSTGRESQL,
        tables=tables or [],
    )


def _make_table(name="users", columns=None):
    return TableSchema(
        name=name,
        columns=columns or [
            ColumnSchema(name="id", unified_type=UnifiedDataType.INTEGER, native_type="integer", primary_key=True),
            ColumnSchema(name="name", unified_type=UnifiedDataType.STRING, native_type="varchar(255)"),
        ],
        primary_key=["id"],
    )


def test_column_schema():
    col = ColumnSchema(name="age", unified_type=UnifiedDataType.INTEGER, native_type="int4")
    assert col.name == "age"
    assert col.unified_type == UnifiedDataType.INTEGER
    assert col.nullable is True


def test_table_schema_get_column():
    table = _make_table()
    assert table.get_column("id") is not None
    assert table.get_column("nonexistent") is None
    assert table.column_names == ["id", "name"]


def test_data_source_schema():
    table = _make_table()
    schema = _make_schema(tables=[table])
    assert schema.table_count == 1
    assert schema.get_table("users") is not None
    assert schema.get_table("missing") is None


def test_schema_serialization_roundtrip():
    table = _make_table()
    schema = _make_schema(tables=[table])
    json_str = schema_to_json(schema)
    restored = schema_from_json(json_str)
    assert restored.source_name == schema.source_name
    assert len(restored.tables) == 1
    assert restored.tables[0].name == "users"


def test_schema_diff_no_changes():
    schema = _make_schema(tables=[_make_table()])
    diff = compare_schemas(schema, schema)
    assert not diff.has_changes


def test_schema_diff_table_added():
    old = _make_schema(tables=[_make_table("users")])
    new = _make_schema(tables=[_make_table("users"), _make_table("assets")])
    diff = compare_schemas(old, new)
    assert diff.has_changes
    added = [c for c in diff.changes if c.change_type == ChangeType.TABLE_ADDED]
    assert len(added) == 1
    assert added[0].table_name == "assets"


def test_schema_diff_column_type_changed():
    old_table = TableSchema(
        name="t",
        columns=[ColumnSchema(name="x", unified_type=UnifiedDataType.STRING, native_type="varchar")],
    )
    new_table = TableSchema(
        name="t",
        columns=[ColumnSchema(name="x", unified_type=UnifiedDataType.INTEGER, native_type="integer")],
    )
    diff = compare_schemas(_make_schema([old_table]), _make_schema([new_table]))
    type_changes = [c for c in diff.changes if c.change_type == ChangeType.COLUMN_TYPE_CHANGED]
    assert len(type_changes) == 1
    assert type_changes[0].column_name == "x"


def test_schema_summary():
    schema = _make_schema(tables=[_make_table()])
    s = schema_summary(schema)
    assert "test_src" in s
    assert "users" in s
