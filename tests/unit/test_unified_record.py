"""Tests for UnifiedRecord and UnifiedResultSet."""

from cafm.core.types import DataSourceType
from cafm.models.record import RecordMetadata, UnifiedRecord
from cafm.models.resultset import UnifiedResultSet
from cafm.domain.assets import Asset


def _make_record(data=None):
    return UnifiedRecord(
        data=data or {"asset_id": "A-1", "name": "Pump", "category": "plumbing", "facility_id": "BLDG-1"},
        metadata=RecordMetadata(
            source_name="test_db",
            source_type=DataSourceType.POSTGRESQL,
            table_name="assets",
        ),
    )


def test_record_get():
    r = _make_record()
    assert r.get("asset_id") == "A-1"
    assert r.get("missing", "default") == "default"


def test_record_getitem():
    r = _make_record()
    assert r["name"] == "Pump"


def test_record_contains():
    r = _make_record()
    assert "asset_id" in r
    assert "nonexistent" not in r


def test_record_to_domain_model():
    r = _make_record()
    asset = r.to_domain_model(Asset)
    assert isinstance(asset, Asset)
    assert asset.asset_id == "A-1"
    assert asset.name == "Pump"


def test_resultset_as_dicts():
    records = [_make_record({"x": i}) for i in range(3)]
    rs = UnifiedResultSet(records=records, total_count=3)
    dicts = rs.as_dicts()
    assert len(dicts) == 3
    assert dicts[0] == {"x": 0}


def test_resultset_as_domain_models():
    records = [
        _make_record({"asset_id": f"A-{i}", "name": f"Asset {i}", "category": "c", "facility_id": "B"})
        for i in range(2)
    ]
    rs = UnifiedResultSet(records=records, total_count=2)
    assets = rs.as_domain_models(Asset)
    assert len(assets) == 2
    assert all(isinstance(a, Asset) for a in assets)


def test_resultset_properties():
    rs = UnifiedResultSet(records=[], total_count=0)
    assert rs.is_empty
    assert rs.count == 0
