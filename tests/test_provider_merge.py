"""tests/test_provider_merge.py — deduplication and merge logic."""
import pytest
from utils.normalizers import MobilityRecord
from utils.provider_merge import merge_and_dedupe, summarize_quality, provider_names, _dist_km


def _make(id, lat, lon, src="openchargemap", dq="estimated", rtype="charger"):
    return MobilityRecord(
        id=id, name=f"Station {id}", type=rtype, subtypes=[],
        lat=lat, lon=lon, address=None, city=None, country=None,
        operator=None, connector_types=[], power_kw=50, total_ports=4,
        available_ports=None, status="Available", price_info=None,
        accessibility=None, data_source=src, data_quality=dq,
        fallback_reason=None, last_updated=None,
    )


def test_merge_empty_lists():
    result = merge_and_dedupe([], [])
    assert result == []


def test_merge_single_list():
    records = [_make("A", 18.52, 73.85), _make("B", 18.53, 73.86)]
    result  = merge_and_dedupe(records)
    assert len(result) == 2


def test_dedup_removes_nearby_duplicate():
    """Two records within 200m of same type should be deduped."""
    r1 = _make("A", 18.5200, 73.8500, src="ocpp_live",      dq="live")
    r2 = _make("B", 18.5201, 73.8501, src="openchargemap",  dq="estimated")
    result = merge_and_dedupe([r1], [r2])
    assert len(result) == 1
    # Higher-priority source (ocpp_live) should be kept
    assert result[0].data_source == "ocpp_live"


def test_dedup_keeps_different_types():
    """A charger and a parking lot at the same coords are different types — both kept."""
    r1 = _make("A", 18.52, 73.85, rtype="charger")
    r2 = _make("B", 18.52, 73.85, rtype="parking")
    result = merge_and_dedupe([r1], [r2])
    assert len(result) == 2


def test_dedup_keeps_far_apart():
    """Records more than 200m apart should both be kept."""
    r1 = _make("A", 18.5200, 73.8500)
    r2 = _make("B", 18.5250, 73.8550)  # ~700m away
    result = merge_and_dedupe([r1], [r2])
    assert len(result) == 2


def test_distance_attached_when_user_provided():
    r = _make("A", 18.52, 73.85)
    result = merge_and_dedupe([r], user_lat=18.52, user_lon=73.85)
    assert result[0].distance_km == pytest.approx(0.0, abs=0.05)


def test_sorted_by_distance():
    far   = _make("FAR",  18.60, 73.90)
    close = _make("NEAR", 18.52, 73.85)
    result = merge_and_dedupe([far, close], user_lat=18.52, user_lon=73.85)
    assert result[0].id == "NEAR"


def test_max_results_cap():
    records = [_make(str(i), 18.5 + i*0.01, 73.8) for i in range(20)]
    result  = merge_and_dedupe(records, max_results=5)
    assert len(result) == 5


def test_summarize_quality():
    records = [
        _make("A", 18.52, 73.85, dq="live"),
        _make("B", 18.53, 73.86, dq="estimated"),
        _make("C", 18.54, 73.87, dq="estimated"),
    ]
    summary = summarize_quality(records)
    assert summary["live"] == 1
    assert summary["estimated"] == 2


def test_provider_names():
    records = [
        _make("A", 18.52, 73.85, src="openchargemap"),
        _make("B", 18.53, 73.86, src="osm_overpass"),
        _make("C", 18.54, 73.87, src="openchargemap"),
    ]
    names = provider_names(records)
    assert "openchargemap" in names
    assert "osm_overpass" in names
    assert len(names) == 2  # deduped


def test_dist_km_zero():
    assert _dist_km(18.52, 73.85, 18.52, 73.85) == pytest.approx(0.0, abs=1e-6)


def test_dist_km_known():
    # Pune to Mumbai ~120 km straight-line
    d = _dist_km(18.52, 73.85, 19.07, 72.87)
    assert 110 < d < 135