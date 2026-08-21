"""
tests/test_discover_api.py  —  Discover endpoint integration tests.

All tests run offline:
  - GOOGLE_CLOUD_PROJECT=""  → DataAgent uses mock data
  - LLM_ENABLED=false        → no Vertex AI calls
  - External HTTP calls are NOT made (OCM/OSM/Nominatim unavailable in CI)
    so we verify structure, status codes, and graceful fallback behaviour.
"""

import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "")
os.environ.setdefault("LLM_ENABLED",          "false")
os.environ.setdefault("REQUIRE_AUTH",          "false")
os.environ.setdefault("ENABLE_OCM",            "false")   # disable live calls in CI
os.environ.setdefault("ENABLE_OSM_OVERPASS",   "false")
os.environ.setdefault("ENABLE_GOOGLE_PLACES",  "false")

from api.main import app

client = TestClient(app, raise_server_exceptions=False)

SF = {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5.0}


# ── /api/search/discover ─────────────────────────────────────────────────────

class TestDiscoverEndpoint:

    def test_returns_200_with_coords(self):
        r = client.post("/api/search/discover", json=SF)
        assert r.status_code == 200

    def test_response_has_required_fields(self):
        r = client.post("/api/search/discover", json=SF)
        body = r.json()
        assert "results"              in body
        assert "total_found"          in body
        assert "providers_used"       in body
        assert "data_quality_summary" in body
        assert "user_location"        in body

    def test_results_is_list(self):
        r = client.post("/api/search/discover", json=SF)
        assert isinstance(r.json()["results"], list)

    def test_missing_location_and_coords_returns_422(self):
        r = client.post("/api/search/discover", json={"max_distance_km": 5})
        assert r.status_code == 422

    def test_type_filter_charger(self):
        r = client.post("/api/search/discover",
                        json={**SF, "type": "charger"})
        assert r.status_code == 200
        for item in r.json()["results"]:
            assert item["type"] == "charger"

    def test_type_filter_parking(self):
        r = client.post("/api/search/discover",
                        json={**SF, "type": "parking"})
        assert r.status_code == 200
        for item in r.json()["results"]:
            assert item["type"] == "parking"

    def test_type_filter_mobility(self):
        r = client.post("/api/search/discover",
                        json={**SF, "type": "mobility_hub"})
        assert r.status_code == 200
        for item in r.json()["results"]:
            assert item["type"] == "mobility_hub"

    def test_result_schema_fields(self):
        r = client.post("/api/search/discover", json=SF)
        for item in r.json()["results"]:
            assert "id"           in item
            assert "name"         in item
            assert "type"         in item
            assert "lat"          in item
            assert "lon"          in item
            assert "data_source"  in item
            assert "data_quality" in item

    def test_data_quality_labels_valid(self):
        valid = {"live", "estimated", "fallback", "mock-dev", "unknown"}
        r     = client.post("/api/search/discover", json=SF)
        for item in r.json()["results"]:
            assert item["data_quality"] in valid, (
                f"Invalid data_quality: {item['data_quality']}"
            )

    def test_connector_filter_passes_through(self):
        r = client.post("/api/search/discover",
                        json={**SF, "connector_type": "CCS", "type": "charger"})
        assert r.status_code == 200

    def test_power_filter_passes_through(self):
        r = client.post("/api/search/discover",
                        json={**SF, "min_power_kw": 50, "type": "charger"})
        assert r.status_code == 200
        for item in r.json()["results"]:
            if item["type"] == "charger" and item.get("power_kw") is not None:
                assert item["power_kw"] >= 50

    def test_request_id_present(self):
        r = client.post("/api/search/discover", json=SF)
        assert "request_id" in r.json()


# ── /api/search/chargers ──────────────────────────────────────────────────────

class TestChargersEndpoint:

    def test_returns_200(self):
        r = client.post("/api/search/chargers", json=SF)
        assert r.status_code == 200

    def test_only_charger_type(self):
        r = client.post("/api/search/chargers", json=SF)
        for item in r.json()["results"]:
            assert item["type"] == "charger"

    def test_missing_location_returns_422(self):
        r = client.post("/api/search/chargers", json={})
        assert r.status_code == 422


# ── /api/search/parking ───────────────────────────────────────────────────────

class TestParkingEndpoint:

    def test_returns_200(self):
        r = client.post("/api/search/parking", json=SF)
        assert r.status_code == 200

    def test_only_parking_type(self):
        r = client.post("/api/search/parking", json=SF)
        for item in r.json()["results"]:
            assert item["type"] == "parking"


# ── /api/search/mobility ─────────────────────────────────────────────────────

class TestMobilityEndpoint:

    def test_returns_200(self):
        r = client.post("/api/search/mobility", json=SF)
        assert r.status_code == 200

    def test_only_mobility_type(self):
        r = client.post("/api/search/mobility", json=SF)
        for item in r.json()["results"]:
            assert item["type"] == "mobility_hub"
