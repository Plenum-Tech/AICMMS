"""Tests for data transformation functions."""

from cafm.integration.transforms import (
    rename_fields,
    select_fields,
    exclude_fields,
    cast_fields,
    filter_rows,
    add_static_fields,
    deduplicate,
    chain_transforms,
)


def test_rename_fields():
    rows = [{"old_name": "value", "keep": 1}]
    result = rename_fields({"old_name": "new_name"})(rows)
    assert result[0]["new_name"] == "value"
    assert result[0]["keep"] == 1
    assert "old_name" not in result[0]


def test_select_fields():
    rows = [{"a": 1, "b": 2, "c": 3}]
    result = select_fields(["a", "c"])(rows)
    assert result[0] == {"a": 1, "c": 3}


def test_exclude_fields():
    rows = [{"a": 1, "b": 2, "c": 3}]
    result = exclude_fields(["b"])(rows)
    assert result[0] == {"a": 1, "c": 3}


def test_cast_fields():
    rows = [{"count": "42", "price": "9.99"}]
    result = cast_fields({"count": "int", "price": "float"})(rows)
    assert result[0]["count"] == 42
    assert result[0]["price"] == 9.99


def test_filter_rows():
    rows = [{"status": "active"}, {"status": "inactive"}, {"status": "active"}]
    result = filter_rows(lambda r: r["status"] == "active")(rows)
    assert len(result) == 2


def test_add_static_fields():
    rows = [{"a": 1}]
    result = add_static_fields({"source": "legacy"})(rows)
    assert result[0]["source"] == "legacy"


def test_deduplicate():
    rows = [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}, {"id": 2, "v": "c"}]
    result = deduplicate(["id"])(rows)
    assert len(result) == 2
    assert result[0]["v"] == "a"


def test_chain_transforms():
    rows = [{"old": "10", "drop": "x"}]
    t = chain_transforms(
        rename_fields({"old": "count"}),
        exclude_fields(["drop"]),
        cast_fields({"count": "int"}),
    )
    result = t(rows)
    assert result[0] == {"count": 10}
