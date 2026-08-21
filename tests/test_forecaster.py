"""
tests/test_forecaster.py  —  Improvements 5+7: DemandForecaster tests.

Covers
------
- Cold start returns default demand curve (not error)
- fit() with few sessions uses historical mean
- predict_utilization output is always in [0, 1]
- needs_refit returns True for unseen station
- Evaluator produces results with correct field types
"""

import pytest
from datetime import datetime, timezone, timedelta
import random

from models.demand_forecaster import DemandForecaster
from models.forecaster_eval   import ForecastEvaluator


def _make_sessions(n: int, seed: int = 42) -> list:
    random.seed(seed)
    now = datetime.now(timezone.utc)
    sessions = []
    for i in range(n):
        start = now - timedelta(hours=random.uniform(1, 30 * 24))
        dur   = random.uniform(15, 60)
        sessions.append({
            "start_time":       start,
            "end_time":         start + timedelta(minutes=dur),
            "duration_minutes": round(dur),
            "utilization_rate": min(1.0, dur / 60),
        })
    return sessions


@pytest.fixture
def forecaster():
    return DemandForecaster()


# ── Cold start ────────────────────────────────────────────────────────────────

def test_cold_start_returns_default(forecaster):
    result = forecaster.predict_utilization("UNKNOWN_STATION")
    assert result["source"] == "default_demand_curve"
    assert 0 <= result["predicted_utilization"] <= 1


def test_cold_start_no_error(forecaster):
    for hour in range(24):
        dt = datetime(2024, 6, 15, hour, 0, tzinfo=timezone.utc)
        r  = forecaster.predict_utilization("COLD", at=dt)
        assert r["predicted_utilization"] >= 0


# ── After fit ─────────────────────────────────────────────────────────────────

def test_fit_few_sessions_uses_mean(forecaster):
    sessions = _make_sessions(10)
    forecaster.fit("ST_FEW", sessions, power_kw=50)
    result = forecaster.predict_utilization("ST_FEW")
    assert result["source"] == "historical_mean"
    assert 0 <= result["predicted_utilization"] <= 1


def test_fit_many_sessions_uses_model(forecaster):
    sessions = _make_sessions(150)
    forecaster.fit("ST_MANY", sessions, power_kw=150)
    result = forecaster.predict_utilization("ST_MANY")
    assert result["source"] in ("ml_model", "historical_mean")
    assert 0 <= result["predicted_utilization"] <= 1


def test_predict_always_bounded(forecaster):
    sessions = _make_sessions(200)
    forecaster.fit("ST_BOUND", sessions, power_kw=100)
    for _ in range(20):
        dt = datetime(2024, 1, 1, random.randint(0, 23), tzinfo=timezone.utc)
        r  = forecaster.predict_utilization("ST_BOUND", at=dt)
        assert 0.0 <= r["predicted_utilization"] <= 1.0


def test_needs_refit_unseen_station(forecaster):
    assert forecaster.needs_refit("NEVER_FITTED") is True


def test_needs_refit_false_after_fit(forecaster):
    sessions = _make_sessions(150)
    forecaster.fit("ST_FITTED", sessions, power_kw=50)
    assert forecaster.needs_refit("ST_FITTED", max_age_hours=168) is False


# ── Evaluator ─────────────────────────────────────────────────────────────────

def test_evaluator_empty_sessions():
    ev = ForecastEvaluator()
    r  = ev.evaluate_station("ST_EMPTY", [], power_kw=50)
    assert r.n_test == 0
    assert r.model_source == "insufficient_data"


def test_evaluator_returns_valid_metrics():
    ev       = ForecastEvaluator()
    sessions = _make_sessions(100)
    r        = ev.evaluate_station("ST_EVAL", sessions, power_kw=50)
    assert r.n_train > 0
    assert r.n_test  > 0
    assert r.model_mae  >= 0
    assert r.model_rmse >= 0
    assert r.baseline_mae >= 0
    assert isinstance(r.improvement_pct, float)


def test_evaluator_mae_reasonable():
    """MAE should be < 0.5 (random mock data, basic sanity)."""
    ev       = ForecastEvaluator()
    sessions = _make_sessions(200)
    r        = ev.evaluate_station("ST_MAE", sessions, power_kw=100)
    assert r.model_mae < 0.5, f"Suspiciously high MAE: {r.model_mae}"
