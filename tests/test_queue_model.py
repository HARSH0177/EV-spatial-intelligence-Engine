"""
tests/test_queue_model.py  —  Improvement 5: M/M/c queue model unit tests.

Covers
------
- Erlang C boundary values (ρ→0, ρ→1, ρ>1)
- Expected wait monotonically increases with utilization
- Percentile waits ordered correctly (p50 ≤ p90)
- Overloaded queue returns Critical status and is_overloaded=True
- Edge cases: 1 port, high arrival rate, very short sessions
- Queue validator sanity checks
"""

import math
import pytest
from models.queue_model import MMcQueueModel
from models.queue_validator import QueueModelValidator


@pytest.fixture
def model():
    return MMcQueueModel()


@pytest.fixture
def validator():
    return QueueModelValidator()


# ── Basic correctness ─────────────────────────────────────────────────────────

def test_low_utilization_near_zero_wait(model):
    """Very low arrival rate should produce near-zero expected wait."""
    m = model.compute(arrival_rate_per_hour=0.1, avg_session_minutes=30, num_ports=8)
    assert m.expected_wait_min < 0.5
    assert m.queue_status == "Low"
    assert not m.is_overloaded


def test_high_utilization_positive_wait(model):
    """High arrival rate should produce positive expected wait."""
    m = model.compute(arrival_rate_per_hour=7.0, avg_session_minutes=30, num_ports=4)
    assert m.expected_wait_min > 0
    assert m.traffic_intensity > 0.5


def test_overloaded_queue(model):
    """ρ ≥ 1 should return overloaded state with Critical status."""
    m = model.compute(arrival_rate_per_hour=20.0, avg_session_minutes=60, num_ports=2)
    assert m.is_overloaded
    assert m.queue_status == "Critical"
    assert m.prob_wait == 1.0
    assert m.expected_wait_min > 0


def test_erlang_c_between_zero_and_one(model):
    """Erlang C P(W>0) must always be in [0, 1]."""
    for lam in [0.5, 2.0, 4.0, 8.0]:
        for c in [1, 2, 4, 8]:
            for mu_min in [15, 30, 60]:
                m = model.compute(lam, mu_min, c)
                assert 0.0 <= m.prob_wait <= 1.0, (
                    f"prob_wait={m.prob_wait} out of range for λ={lam} c={c} μ_min={mu_min}"
                )


def test_wait_increases_with_load(model):
    """Expected wait should increase as arrival rate increases (c and μ fixed)."""
    waits = [
        model.compute(lam, 30, 4).expected_wait_min
        for lam in [0.5, 2.0, 4.0, 6.0, 7.9]
    ]
    for i in range(len(waits) - 1):
        assert waits[i] <= waits[i + 1] + 1e-6, (
            f"Wait not monotone at index {i}: {waits}"
        )


def test_percentile_ordering(model):
    """p50 wait must be ≤ p90 wait."""
    m = model.compute(arrival_rate_per_hour=5.0, avg_session_minutes=25, num_ports=4)
    assert m.wait_p50_min <= m.wait_p90_min + 1e-6


def test_single_port(model):
    """Model must handle c=1 without error."""
    m = model.compute(arrival_rate_per_hour=1.0, avg_session_minutes=20, num_ports=1)
    assert m.num_ports == 1
    assert m.traffic_intensity > 0
    assert not math.isnan(m.expected_wait_min)


def test_utilization_pct_range(model):
    """Utilization pct should be in [0, 100]."""
    for lam in [0.1, 3.0, 9.9]:
        m = model.compute(lam, 30, 4)
        assert 0 <= m.utilization_pct <= 100


def test_status_thresholds(model):
    """Status tiers should match known utilization buckets."""
    low  = model.compute(0.5,  30, 8)   # very low load
    high = model.compute(5.5,  30, 4)   # high load
    assert low.queue_status  in ("Low", "Moderate")
    assert high.queue_status in ("High", "Critical")


def test_to_dict_has_required_keys(model):
    """to_dict() must contain all fields the API response depends on."""
    m = model.compute(3.0, 28, 6)
    d = m.to_dict()
    required = {
        "arrival_rate_per_hour", "service_rate_per_hour", "num_ports",
        "traffic_intensity", "prob_wait", "expected_wait_min",
        "wait_p50_min", "wait_p90_min", "utilization_pct",
        "queue_status", "is_overloaded",
    }
    assert required.issubset(d.keys()), f"Missing keys: {required - set(d.keys())}"


# ── Validator sanity checks ───────────────────────────────────────────────────

def test_sanity_no_warnings_healthy(validator):
    """Healthy inputs should produce no sanity warnings."""
    warnings = validator.sanity_check(lam=3.0, mu=2.0, c=4)
    assert len(warnings) == 0


def test_sanity_warns_overloaded(validator):
    """ρ ≥ 1 should produce an overload warning."""
    warnings = validator.sanity_check(lam=10.0, mu=1.0, c=2)
    assert any("overloaded" in w.lower() or "≥ 1" in w for w in warnings)


def test_sanity_warns_zero_arrival(validator):
    """λ = 0 should produce a warning."""
    warnings = validator.sanity_check(lam=0.0, mu=2.0, c=4)
    assert any("λ" in w for w in warnings)


def test_validate_stations_returns_summary(validator):
    """validate_stations should return a CalibrationSummary with correct count."""
    stats = [
        {"station_id": "ST001", "num_ports": 8, "kw": 150,
         "observed_sessions_per_hour": 4.0, "avg_session_minutes": 28,
         "predicted_arrival_rate": 3.8},
        {"station_id": "ST002", "num_ports": 4, "kw": 100,
         "observed_sessions_per_hour": 2.0, "avg_session_minutes": 35,
         "predicted_arrival_rate": 2.2},
    ]
    summary = validator.validate_stations(stats)
    assert summary.n_stations == 2
    assert 0 <= summary.mean_util_mae <= 1
    assert summary.mean_wait_mae_min >= 0
    assert len(summary.results) == 2
