"""
tests/test_station_registry.py  —  Improvement 5: station registry tests.

Covers
------
- Mock-dev fallback returns correctly shaped records
- Fallback _data_quality is "mock-dev"
- connector_type filter in DriverAssistantAgent._supports_connector
- Distance calculation correctness
- Ranking score properties (bounded, monotone)
- Connector filter removes incompatible stations
"""

import math
import pytest
from agents.driver_agent import DriverAssistantAgent
from agents.data_agent import _DEV_STATION_REGISTRY


@pytest.fixture
def agent():
    return DriverAssistantAgent()


# ── Dev fallback registry shape ───────────────────────────────────────────────

def test_dev_registry_not_empty():
    assert len(_DEV_STATION_REGISTRY) > 0


def test_dev_registry_required_fields():
    required = {"station_id", "name", "lat", "lon", "kw", "total_ports",
                "connector_types", "data_source", "_data_quality"}
    for s in _DEV_STATION_REGISTRY:
        missing = required - set(s.keys())
        assert not missing, f"Station {s.get('station_id')} missing: {missing}"


def test_dev_registry_data_quality_label():
    for s in _DEV_STATION_REGISTRY:
        assert s["_data_quality"] == "mock-dev", (
            f"Station {s['station_id']} should be labelled mock-dev"
        )


def test_dev_registry_valid_coords():
    for s in _DEV_STATION_REGISTRY:
        assert -90 <= s["lat"] <= 90,  f"Bad lat in {s['station_id']}"
        assert -180 <= s["lon"] <= 180, f"Bad lon in {s['station_id']}"


def test_dev_registry_positive_power():
    for s in _DEV_STATION_REGISTRY:
        assert s["kw"] > 0, f"kw must be positive in {s['station_id']}"


def test_dev_registry_connector_types_list():
    for s in _DEV_STATION_REGISTRY:
        assert isinstance(s["connector_types"], list), (
            f"connector_types must be a list in {s['station_id']}"
        )


# ── Connector filter ──────────────────────────────────────────────────────────

def test_supports_connector_exact_match(agent):
    station = {"connector_types": ["CCS", "CHAdeMO"]}
    assert agent._supports_connector(station, "CCS")
    assert agent._supports_connector(station, "CHAdeMO")


def test_supports_connector_case_insensitive(agent):
    station = {"connector_types": ["ccs", "j1772"]}
    assert agent._supports_connector(station, "CCS")
    assert agent._supports_connector(station, "J1772")


def test_supports_connector_no_match(agent):
    station = {"connector_types": ["J1772"]}
    assert not agent._supports_connector(station, "CCS")


def test_supports_connector_empty_allows_all(agent):
    """Unknown connector list should not filter out the station."""
    station = {"connector_types": []}
    assert agent._supports_connector(station, "CCS")


def test_supports_connector_missing_key(agent):
    """Missing connector_types key should not filter out the station."""
    station = {}
    assert agent._supports_connector(station, "Tesla")


# ── Distance calculation ──────────────────────────────────────────────────────

def test_dist_km_same_point(agent):
    assert agent._dist_km(37.76, -122.43, 37.76, -122.43) == pytest.approx(0.0, abs=1e-6)


def test_dist_km_known_pair(agent):
    # SFO to Oakland roughly 18 km
    d = agent._dist_km(37.6213, -122.3790, 37.7213, -122.2208)
    assert 15 < d < 22


def test_dist_km_symmetric(agent):
    d1 = agent._dist_km(37.76, -122.43, 37.79, -122.41)
    d2 = agent._dist_km(37.79, -122.41, 37.76, -122.43)
    assert abs(d1 - d2) < 1e-6


# ── Ranking score properties ──────────────────────────────────────────────────

def test_rank_score_bounded(agent):
    score = agent._compute_rank_score(
        wait_min=0, free_ports=4, total_ports=8,
        distance_km=1.0, power_kw=150,
    )
    assert 0.0 <= score <= 1.0


def test_rank_score_available_beats_busy(agent):
    avail = agent._compute_rank_score(0,  4, 8, 1.0, 150)
    busy  = agent._compute_rank_score(20, 0, 8, 1.0, 150)
    assert avail > busy


def test_rank_score_closer_beats_farther(agent):
    close = agent._compute_rank_score(0, 4, 8, 0.5, 150)
    far   = agent._compute_rank_score(0, 4, 8, 5.0, 150)
    assert close > far


def test_rank_score_fast_beats_slow(agent):
    fast = agent._compute_rank_score(0, 4, 8, 1.0, 250)
    slow = agent._compute_rank_score(0, 4, 8, 1.0,  22)
    assert fast > slow


def test_rank_explanation_contains_score(agent):
    expl = agent._rank_explanation(5.0, 2, 8, 1.2, 150, 0.732)
    assert "0.732" in expl
    assert "5" in expl   # wait time
