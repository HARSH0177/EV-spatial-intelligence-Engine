"""
tests/test_api_paths.py  —  Improvement 5: FastAPI path integration tests.

Uses FastAPI's TestClient (no real network calls needed).
BigQuery and Vertex AI are not called — DataAgent falls back to mock data
when GOOGLE_CLOUD_PROJECT is unset, which is always true in CI.

Covers
------
- GET /health returns 200
- GET /ready  returns 200 with metric keys
- POST /driver/locate-charger with coords returns results
- POST /driver/locate-charger missing both location and coords → 422
- POST /driver/locate-charger with connector_type filter
- POST /driver/map-data returns GeoJSON FeatureCollection
- POST /company/plan-expansion returns report structure
- POST /agent/run with task_type=status returns healthy
"""

import os
import pytest
from fastapi.testclient import TestClient

# Ensure no real BQ or Vertex calls during tests
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "")
os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("REQUIRE_AUTH", "false")

from api.main import app

client = TestClient(app)

SF_COORDS = {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 10.0}


# ── Health / readiness ────────────────────────────────────────────────────────

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_ready_ok():
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert "metrics" in body
    assert "config" in body


def test_root_ok():
    r = client.get("/")
    assert r.status_code == 200
    assert "version" in r.json()


# ── Driver locator ────────────────────────────────────────────────────────────

def test_driver_locate_with_coords():
    r = client.post("/driver/locate-charger", json=SF_COORDS)
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert "workflow_log" in body
    assert "elapsed_seconds" in body


def test_driver_locate_with_location_name():
    r = client.post("/driver/locate-charger", json={
        "location": "San Francisco, CA",
        "max_distance_km": 10,
    })
    # May return 200 (OSM resolved) or 422 (no network in CI)
    # Both are acceptable — we just confirm no 500
    assert r.status_code in (200, 422)


def test_driver_locate_missing_both_returns_422():
    r = client.post("/driver/locate-charger", json={"max_distance_km": 5})
    assert r.status_code == 422


def test_driver_locate_connector_filter():
    r = client.post("/driver/locate-charger", json={
        **SF_COORDS,
        "connector_type": "CCS",
    })
    assert r.status_code == 200
    body = r.json()
    # All returned chargers must support CCS (or have empty connector_types)
    all_chargers = (
        body["results"].get("available_chargers", [])
        + body["results"].get("busy_chargers", [])
    )
    for c in all_chargers:
        ct = c.get("connector_types", [])
        if ct:
            assert any("CCS" in t.upper() for t in ct), (
                f"Station {c.get('id')} missing CCS: {ct}"
            )


def test_driver_locate_results_structure():
    r = client.post("/driver/locate-charger", json=SF_COORDS)
    assert r.status_code == 200
    results = r.json()["results"]
    required_keys = {
        "user_location", "system_tip", "available_chargers",
        "busy_chargers", "total_chargers_found",
        "data_quality_summary", "ranking_config",
    }
    assert required_keys.issubset(results.keys())


def test_driver_locate_data_quality_labels():
    r = client.post("/driver/locate-charger", json=SF_COORDS)
    assert r.status_code == 200
    results   = r.json()["results"]
    all_chars = results["available_chargers"] + results["busy_chargers"]
    valid_dq  = {"live", "estimated", "fallback", "mock-dev", "unknown"}
    for c in all_chars:
        assert c.get("data_quality") in valid_dq, (
            f"Station {c.get('id')} has invalid data_quality: {c.get('data_quality')}"
        )


# ── Map data ──────────────────────────────────────────────────────────────────

def test_map_data_returns_geojson():
    r = client.post("/driver/map-data", json=SF_COORDS)
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert "features" in body
    for f in body["features"]:
        assert f["type"] == "Feature"
        assert f["geometry"]["type"] == "Point"
        assert len(f["geometry"]["coordinates"]) == 2
        props = f["properties"]
        assert "name" in props
        assert "current_status" in props
        assert "data_quality" in props


# ── Expansion planning ────────────────────────────────────────────────────────

def test_expansion_returns_report():
    r = client.post("/company/plan-expansion", json={
        "city": "San Francisco",
        "budget_usd": 5_000_000,
        "top_n": 3,
    })
    assert r.status_code == 200
    body = r.json()
    assert "report" in body
    assert "top_zones" in body
    report = body["report"]
    assert "summary" in report
    assert "zone_analysis" in report
    assert "scoring_model" in report
    assert "weights" in report["scoring_model"]


def test_expansion_zone_has_weighted_breakdown():
    r = client.post("/company/plan-expansion", json={
        "city": "San Francisco", "budget_usd": 5_000_000, "top_n": 2,
    })
    assert r.status_code == 200
    zones = r.json()["top_zones"]
    for z in zones:
        assert "weighted_breakdown" in z, "weighted_breakdown missing from zone"
        assert "score_breakdown" in z


# ── Generic agent runner ──────────────────────────────────────────────────────

def test_agent_run_status():
    r = client.post("/agent/run", json={"task_type": "status", "payload": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "all_healthy"
    assert "metrics" in body


def test_agent_run_unknown_type():
    r = client.post("/agent/run", json={"task_type": "invalid_xyz", "payload": {}})
    assert r.status_code == 200
    assert "error" in r.json()
