"""tests/test_geo_enricher.py — test GeoResult normalization and cache."""
import pytest
from utils.normalizers import GeoResult
from utils.geo_enricher import GeoEnricher
from utils.cache import TTLCache


def test_geo_result_now_iso():
    ts = GeoResult.now_iso()
    assert "T" in ts
    assert len(ts) > 10


def test_cache_key_deterministic():
    k1 = TTLCache.make_key("Pune", "India")
    k2 = TTLCache.make_key("Pune", "India")
    k3 = TTLCache.make_key("pune", "india")
    assert k1 == k2
    assert k1 == k3  # normalized to lowercase


def test_cache_set_get():
    from utils.cache import TTLCache
    c = TTLCache(ttl_seconds=60, name="test")
    c.set("city:pune", {"lat": 18.5, "lon": 73.8})
    r = c.get("city:pune")
    assert r is not None
    assert r["lat"] == 18.5


def test_cache_miss_returns_none():
    from utils.cache import TTLCache
    c = TTLCache(ttl_seconds=60, name="test2")
    assert c.get("nonexistent_key_xyz") is None


def test_cache_stats():
    from utils.cache import TTLCache
    c = TTLCache(ttl_seconds=60, name="stats_test")
    c.set("k1", "v1")
    c.get("k1")    # hit
    c.get("k99")   # miss
    s = c.stats()
    assert s["hits"] == 1
    assert s["misses"] == 1
    assert s["size"] == 1


def test_geo_result_to_dict():
    g = GeoResult(
        city="Pune", display_name="Pune, Maharashtra, India",
        country="India", country_code="IN",
        lat=18.52, lon=73.85,
        bbox={"south": 18.4, "north": 18.6, "west": 73.7, "east": 74.0},
        neighborhoods=[{"name": "Koregaon Park", "lat": 18.53, "lon": 73.89, "osm_type": "node", "osm_id": 1}],
        source="nominatim_osm", fetched_at="2024-01-01T00:00:00",
    )
    d = g.to_dict()
    assert d["city"] == "Pune"
    assert d["country_code"] == "IN"
    assert len(d["neighborhoods"]) == 1
    assert "bbox" in d


def test_normalizer_connector():
    from utils.normalizers import normalize_connector
    assert normalize_connector("TYPE1")   == "J1772"
    assert normalize_connector("CHADEMO") == "CHAdeMO"
    assert normalize_connector("tesla")   == "Tesla"
    assert normalize_connector("CCS2")    == "CCS"
    assert normalize_connector("")        == "Unknown"


def test_normalizer_status():
    from utils.normalizers import normalize_status
    assert normalize_status("Available")   == "Available"
    assert normalize_status("InUse")       == "Charging"
    assert normalize_status("Operational") == "Available"
    assert normalize_status("Offline")     == "Offline"
    assert normalize_status("")            == "Unknown"
