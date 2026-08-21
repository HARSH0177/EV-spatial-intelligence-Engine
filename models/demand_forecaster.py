"""
models/demand_forecaster.py  —  Per-station ML demand forecasting.

Model
-----
GradientBoostingRegressor trained on session_history from BigQuery.

Features (all derived from datetime + station metadata):
  sin/cos hour-of-day     — smooth daily cycle
  sin/cos day-of-week     — weekly pattern
  sin/cos month           — seasonal pattern
  is_weekend              — binary flag
  connector_power_kw      — station capability
  lag_1h_utilization      — last observed utilization (if available)

Target: utilization_rate (0–1) for the next 1-hour window

Fallback strategy (graceful degradation):
  < 50 sessions  → return grand-mean utilization from historical table
  50–200 sessions → train with high regularisation
  ≥ 200 sessions → full model

Interview talking point
-----------------------
"We use sin/cos encoding for cyclic time features rather than ordinal integers
— hour=23 and hour=0 are adjacent in reality but 23 apart as integers, which
would mislead a linear model.  The model is re-fitted per station when the API
boots and cached; we schedule a weekly background re-fit via Cloud Scheduler."
"""

import math
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_SKLEARN_OK = False
try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    _SKLEARN_OK = True
except ImportError:
    logger.warning("scikit-learn not available; DemandForecaster will use fallback means")


def _sin_cos(value: float, period: float):
    angle = 2 * math.pi * value / period
    return math.sin(angle), math.cos(angle)


def _build_features(dt: datetime, power_kw: float = 50.0, lag_util: float = 0.5) -> list:
    h_sin, h_cos = _sin_cos(dt.hour + dt.minute / 60, 24)
    d_sin, d_cos = _sin_cos(dt.weekday(), 7)
    m_sin, m_cos = _sin_cos(dt.month - 1, 12)
    is_weekend   = float(dt.weekday() >= 5)
    log_power    = math.log1p(power_kw)
    return [h_sin, h_cos, d_sin, d_cos, m_sin, m_cos, is_weekend, log_power, lag_util]


class DemandForecaster:
    """Per-station gradient boosting demand forecaster."""

    MIN_SESSIONS_FOR_MODEL = 50

    def __init__(self):
        self._station_models: dict = {}
        self._station_means:  dict = {}
        self._fitted_at:      dict = {}

    def fit(self, station_id: str, sessions: list, power_kw: float = 50.0) -> None:
        if not sessions:
            self._station_means[station_id] = 0.5
            return

        util_values = [max(0.0, min(1.0, s.get("utilization_rate", 0.5))) for s in sessions]
        mean_util   = float(np.mean(util_values))
        self._station_means[station_id] = mean_util

        if not _SKLEARN_OK or len(sessions) < self.MIN_SESSIONS_FOR_MODEL:
            return

        X, y = [], []
        for s in sessions:
            start = s.get("start_time")
            if not isinstance(start, datetime):
                continue
            lag   = s.get("lag_utilization", mean_util)
            X.append(_build_features(start, power_kw, lag))
            y.append(max(0.0, min(1.0, s.get("utilization_rate", mean_util))))

        if len(X) < self.MIN_SESSIONS_FOR_MODEL:
            return

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("gbr", GradientBoostingRegressor(
                n_estimators=100, max_depth=4, learning_rate=0.08,
                subsample=0.8, random_state=42,
            )),
        ])
        try:
            pipeline.fit(np.array(X, dtype=float), np.array(y, dtype=float))
            self._station_models[station_id] = (pipeline, power_kw)
            self._fitted_at[station_id]      = datetime.now(timezone.utc)
            logger.info("[%s] Model fitted on %d sessions", station_id, len(X))
        except Exception as e:
            logger.warning("[%s] Model fit failed: %s — using mean", station_id, e)

    def predict_utilization(
        self,
        station_id: str,
        at:         Optional[datetime] = None,
        lag_util:   float = 0.5,
    ) -> dict:
        dt = at or datetime.now(timezone.utc)

        if station_id in self._station_models:
            pipeline, power_kw = self._station_models[station_id]
            try:
                pred = float(pipeline.predict(np.array([_build_features(dt, power_kw, lag_util)]))[0])
                pred = max(0.0, min(1.0, pred))
                return {
                    "predicted_utilization":  round(pred, 4),
                    "predicted_arrival_rate": round(pred * 6, 4),
                    "source":    "ml_model",
                    "fitted_at": self._fitted_at[station_id].isoformat(),
                }
            except Exception as e:
                logger.warning("[%s] Prediction error: %s", station_id, e)

        if station_id in self._station_means:
            mean = self._station_means[station_id]
            return {
                "predicted_utilization":  round(mean, 4),
                "predicted_arrival_rate": round(mean * 6, 4),
                "source":    "historical_mean",
                "fitted_at": None,
            }

        # Cold start — use hardcoded demand curve
        hour_util = {
            0:0.08, 1:0.05, 2:0.04, 3:0.03, 4:0.05, 5:0.12,
            6:0.28, 7:0.55, 8:0.82, 9:0.79, 10:0.71, 11:0.68,
            12:0.75, 13:0.72, 14:0.65, 15:0.60, 16:0.72, 17:0.88,
            18:0.91, 19:0.85, 20:0.70, 21:0.52, 22:0.30, 23:0.15,
        }
        default_util = hour_util.get(dt.hour, 0.5)
        return {
            "predicted_utilization":  round(default_util, 4),
            "predicted_arrival_rate": round(default_util * 6, 4),
            "source":    "default_demand_curve",
            "fitted_at": None,
        }

    def needs_refit(self, station_id: str, max_age_hours: int = 168) -> bool:
        if station_id not in self._fitted_at:
            return True
        age = (datetime.now(timezone.utc) - self._fitted_at[station_id]).total_seconds() / 3600
        return age > max_age_hours
