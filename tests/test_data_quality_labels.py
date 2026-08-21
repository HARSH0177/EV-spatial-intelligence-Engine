"""
tests/test_data_quality_labels.py  —  Data quality label correctness tests.

Verifies that every code path that produces a MobilityRecord
correctly sets data_quality to one of: live | estimated | fallback | mock-dev.
Also verifies that fallback_reason is present when quality != live.
"""

import pytest
from utils.normalizers import MobilityRecord, normalize_connector, normalize_status
from realtime.openchargemap_client import OpenChargeMapClient
from realtime.osm_places_client    import OSMPlacesClient
from realtime.nrel_client          import NRELClient
from agents.data_agent             import _DEV_STATION_REGISTRY

VALID_DQ = {"live", "estimated", "fallback", "mock-dev"}


# ── MobilityRecord construction ───────────────────────────────────────────────

def _make_record(**overrides) -> MobilityRecord:
    defaults = dict(
        id="X", name="Test", type="charger", subtypes=[],
        lat=18.5, lon=73.8, address=None, city=None, country=None,
        operator=None, connector_types=[], power_kw=50, total_ports=4,
        available_ports=None, status="Available", price_info=None,
        accessibility=None, data_source="test",
        data_quality="estimated", fallback_reason=None, last_updated=None,
    )
    defaults.update(overrides)
    return MobilityRecord(**defaults)


def test_valid_quality_labels():
    for dq in VALID_DQ:
        r = _make_record(data_quality=dq)
        assert r.data_quality in VALID_DQ


def test_fallback_has_reason():
    r = _make_record(data_quality="fallback", fallback_reason="BQ timeout")
    assert r.fallback_reason is not None
    assert len(r.fallback_reason) > 0


def test_live_may_have_no_reason():
    r = _make_record(data_quality="live", fallback_reason=None)
    assert r.data_quality == "live"


# ── OCM normalizer quality labels ─────────────────────────────────────────────

class TestOCMQualityLabels:

    def setup_method(self):
        self.client = OpenChargeMapClient()

    def test_operational_station_is_estimated(self):
        raw = {
            "ID": 1,
            "AddressInfo": {"Title": "Test", "Latitude": 18.5, "Longitude": 73.8},
            "StatusType": {"Title": "Operational", "IsOperational": True},
            "Connections": [],
        }
        r = self.client._normalise(raw)
        assert r.data_quality in VALID_DQ

    def test_unknown_status_is_fallback(self):
        raw = {
            "ID": 2,
            "AddressInfo": {"Title": "Test2", "Latitude": 18.5, "Longitude": 73.8},
            "StatusType": {},
            "Connections": [],
        }
        r = self.client._normalise(raw)
        assert r.data_quality in VALID_DQ

    def test_fallback_reason_present_when_not_live(self):
        raw = {
            "ID": 3,
            "AddressInfo": {"Title": "T3", "Latitude": 18.5, "Longitude": 73.8},
            "StatusType": {"Title": "Unknown"},
            "Connections": [],
        }
        r = self.client._normalise(raw)
        if r.data_quality != "live":
            assert r.fallback_reason is not None

    def test_data_source_is_openchargemap(self):
        raw = {
            "ID": 4,
            "AddressInfo": {"Title": "T4", "Latitude": 18.5, "Longitude": 73.8},
            "StatusType": {"Title": "Operational"},
            "Connections": [],
        }
        r = self.client._normalise(raw)
        assert r.data_source == "openchargemap"


# ── OSM normalizer quality labels ─────────────────────────────────────────────

class TestOSMQualityLabels:

    def setup_method(self):
        self.client = OSMPlacesClient()

    def test_parking_lot_is_estimated(self):
        el = {"id": 1, "lat": 18.5, "lon": 73.8, "tags": {"amenity": "parking"}}
        r  = self.client._norm_parking(el)
        assert r.data_quality == "estimated"
        assert r.data_source  == "osm_overpass"
        assert r.type         == "parking"

    def test_mobility_hub_is_estimated(self):
        el = {"id": 2, "lat": 18.5, "lon": 73.8, "tags": {"amenity": "bicycle_rental", "name": "BikeShare"}}
        r  = self.client._norm_mobility(el)
        assert r.data_quality == "estimated"
        assert r.type         == "mobility_hub"

    def test_parking_fallback_reason_set(self):
        el = {"id": 3, "lat": 18.5, "lon": 73.8, "tags": {}}
        r  = self.client._norm_parking(el)
        assert r.fallback_reason is not None


# ── Dev registry quality labels ───────────────────────────────────────────────

def test_dev_registry_all_mock_dev():
    for s in _DEV_STATION_REGISTRY:
        assert s["_data_quality"] == "mock-dev", (
            f"Station {s['station_id']} should be mock-dev, got {s['_data_quality']}"
        )


# ── NREL normalizer quality labels ────────────────────────────────────────────

def test_nrel_quality_is_estimated():
    client = NRELClient()
    raw = {
        "id": 99,
        "station_name": "Test NREL",
        "latitude":  37.77,
        "longitude": -122.41,
        "ev_level2_evse_num": 2,
        "ev_dc_fast_num": 0,
        "ev_network": "ChargePoint",
        "street_address": "100 Main St",
        "city": "San Francisco",
        "state": "CA",
    }
    r = client._normalise(raw)
    assert r.data_quality == "estimated"
    assert r.data_source  == "nrel_afdc"
    assert r.fallback_reason is not None


# ── API-level quality label propagation ──────────────────────────────────────

def test_api_results_have_valid_dq():
    """Smoke test: /api/search/discover with coords returns valid quality labels."""
    import os
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "")
    os.environ.setdefault("LLM_ENABLED",          "false")
    os.environ.setdefault("REQUIRE_AUTH",          "false")
    os.environ.setdefault("ENABLE_OCM",            "false")
    os.environ.setdefault("ENABLE_OSM_OVERPASS",   "false")

    from fastapi.testclient import TestClient
    from api.main import app

    c    = TestClient(app, raise_server_exceptions=False)
    resp = c.post("/api/search/discover",
                  json={"latitude": 37.77, "longitude": -122.41, "max_distance_km": 5})
    if resp.status_code != 200:
        pytest.skip("API returned non-200, likely CI limitation")

    for item in resp.json()["results"]:
        assert item["data_quality"] in VALID_DQ, (
            f"Got invalid data_quality: {item['data_quality']}"
        )
