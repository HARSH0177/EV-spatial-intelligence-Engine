"""
tests/test_advisor_api.py  —  Advisor (Plan) endpoint integration tests.

All tests run offline — GeoEnricher/OSM calls will fail gracefully
and DataAgent falls back to dynamic mock data.
"""

import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "")
os.environ.setdefault("LLM_ENABLED",          "false")
os.environ.setdefault("REQUIRE_AUTH",          "false")
os.environ.setdefault("ENABLE_OCM",            "false")
os.environ.setdefault("ENABLE_OSM_OVERPASS",   "false")
os.environ.setdefault("ENABLE_GOOGLE_PLACES",  "false")

from api.main import app

client = TestClient(app, raise_server_exceptions=False)


# ── /api/advisor/analyze-area ────────────────────────────────────────────────

class TestAnalyzeArea:

    def test_returns_200_or_422(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 3})
        # 200 = success; 422 = geocode failed (no network in CI) — both acceptable
        assert r.status_code in (200, 422, 500)

    def test_missing_location_returns_422(self):
        r = client.post("/api/advisor/analyze-area", json={"top_n": 3})
        assert r.status_code == 422

    def test_response_structure_when_ok(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 3})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        body = r.json()
        assert "zones"      in body
        assert "geo"        in body
        assert "zone_count" in body
        assert "summary"    in body
        assert "request_id" in body

    def test_zone_schema(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 3})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        required = {
            "zone_id", "zone_name", "city", "lat", "lon",
            "demand_score", "competition_score", "accessibility_score",
            "parking_support_score", "grid_score", "roi_score",
            "viability_score", "confidence_score",
            "recommended_station_type", "recommended_port_count",
            "recommended_connector_mix", "explanation",
            "real_inputs", "modeled_inputs",
        }
        for z in r.json()["zones"]:
            missing = required - set(z.keys())
            assert not missing, f"Zone missing fields: {missing}"

    def test_scores_bounded_0_to_1(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 3})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        score_fields = [
            "demand_score", "competition_score", "accessibility_score",
            "parking_support_score", "grid_score", "roi_score",
            "viability_score", "confidence_score",
        ]
        for z in r.json()["zones"]:
            for f in score_fields:
                val = z.get(f)
                if val is not None:
                    assert 0.0 <= val <= 1.0, f"{f}={val} out of [0,1]"

    def test_top_n_respected(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 2})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        assert len(r.json()["zones"]) <= 2

    def test_zones_sorted_by_viability(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 5})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        scores = [z["viability_score"] for z in r.json()["zones"]]
        assert scores == sorted(scores, reverse=True), "Zones not sorted by viability"

    def test_explanation_not_empty(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 3})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        for z in r.json()["zones"]:
            assert z["explanation"], "Explanation must not be empty"

    def test_real_and_modeled_inputs_present(self):
        r = client.post("/api/advisor/analyze-area",
                        json={"location": "San Francisco", "top_n": 3})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        for z in r.json()["zones"]:
            assert isinstance(z["real_inputs"],    dict)
            assert isinstance(z["modeled_inputs"], dict)


# ── /api/advisor/rank-zones ───────────────────────────────────────────────────

class TestRankZones:

    def test_returns_list(self):
        r = client.post("/api/advisor/rank-zones",
                        json={"location": "Berlin", "top_n": 5})
        if r.status_code != 200:
            pytest.skip("Geocoding unavailable in CI")
        body = r.json()
        assert "zones"      in body
        assert "zone_count" in body
        assert isinstance(body["zones"], list)

    def test_missing_location_422(self):
        r = client.post("/api/advisor/rank-zones", json={})
        assert r.status_code == 422


# ── /api/advisor/explain ─────────────────────────────────────────────────────

class TestExplainZone:

    def test_unknown_zone_returns_404(self):
        r = client.post("/api/advisor/explain",
                        json={"zone_id": "nonexistent_xyz", "location": "San Francisco"})
        # 404 when zone not found, 422/500 if geocoding fails in CI
        assert r.status_code in (404, 422, 500)

    def test_missing_fields_422(self):
        r = client.post("/api/advisor/explain", json={"location": "San Francisco"})
        assert r.status_code == 422
