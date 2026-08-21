"""
models/forecaster_eval.py  —  Improvement 7: Offline forecasting evaluation.

Design
------
- Holdout split: last 20% of sessions (chronological) used as test set.
- Metrics: MAE, RMSE, MAPE (where target > 0), baseline comparison.
- Baseline: naive predictor using the same hour-of-day mean from training set.
- Output: dict + optional JSON/CSV save for audit trail.

This module is evaluation-only and is never imported in the hot path.
Run with:  python -m models.forecaster_eval

Interview talking point
-----------------------
"We evaluate the demand forecaster offline using a temporal holdout — never
a random split, because time-series data has leakage risk with random splits.
We compare against a naive baseline (same-hour mean) to confirm the GBT
model adds value beyond a lookup table."
"""

import json
import logging
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

import numpy as np

from models.demand_forecaster import DemandForecaster, _build_features

logger = logging.getLogger(__name__)


@dataclass
class ForecastEvalResult:
    station_id:    str
    n_train:       int
    n_test:        int
    model_mae:     float
    model_rmse:    float
    model_mape:    Optional[float]   # None if any target == 0
    baseline_mae:  float
    baseline_rmse: float
    improvement_pct: float           # positive = model beats baseline
    model_source:  str               # "ml_model" | "historical_mean" | "default"
    eval_date:     str


class ForecastEvaluator:
    """
    Offline backtesting for DemandForecaster.
    Uses a temporal holdout split (no random shuffle).
    """

    HOLDOUT_FRACTION = 0.20   # last 20% of sessions = test set

    def evaluate_station(
        self,
        station_id: str,
        sessions:   List[dict],
        power_kw:   float = 50.0,
    ) -> ForecastEvalResult:
        """
        Evaluate the forecaster on one station's session history.

        Parameters
        ----------
        station_id : station identifier
        sessions   : list of session dicts with start_time + utilization_rate
        power_kw   : charger power rating (feature input)
        """
        if len(sessions) < 10:
            logger.warning("[%s] Too few sessions (%d) for eval", station_id, len(sessions))
            return self._empty_result(station_id, len(sessions))

        # Sort chronologically
        sessions_sorted = sorted(
            [s for s in sessions if isinstance(s.get("start_time"), datetime)],
            key=lambda s: s["start_time"],
        )

        split_idx = max(1, int(len(sessions_sorted) * (1 - self.HOLDOUT_FRACTION)))
        train     = sessions_sorted[:split_idx]
        test      = sessions_sorted[split_idx:]

        if not test:
            return self._empty_result(station_id, len(sessions_sorted))

        # Train on training set
        forecaster = DemandForecaster()
        forecaster.fit(station_id, train, power_kw=power_kw)

        # Evaluate on test set
        y_true, y_pred, y_base = [], [], []
        mean_train_util = float(np.mean([s.get("utilization_rate", 0.5) for s in train]))

        # Baseline: same-hour mean from training set
        hour_means = {}
        for s in train:
            h = s["start_time"].hour
            hour_means.setdefault(h, []).append(s.get("utilization_rate", 0.5))
        hour_means = {h: float(np.mean(v)) for h, v in hour_means.items()}

        for s in test:
            true_util = max(0.0, min(1.0, s.get("utilization_rate", 0.5)))
            pred      = forecaster.predict_utilization(
                station_id,
                at=s["start_time"],
                lag_util=s.get("lag_utilization", mean_train_util),
            )
            pred_util = pred["predicted_utilization"]
            base_util = hour_means.get(s["start_time"].hour, mean_train_util)

            y_true.append(true_util)
            y_pred.append(pred_util)
            y_base.append(base_util)

        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        y_base = np.array(y_base)

        model_mae    = float(np.mean(np.abs(y_true - y_pred)))
        model_rmse   = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        base_mae     = float(np.mean(np.abs(y_true - y_base)))
        base_rmse    = float(np.sqrt(np.mean((y_true - y_base) ** 2)))
        improvement  = ((base_mae - model_mae) / max(base_mae, 1e-9)) * 100

        # MAPE — only where target > 0
        nonzero_mask = y_true > 0
        model_mape   = (
            float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask])
                                  / y_true[nonzero_mask])) * 100)
            if nonzero_mask.any() else None
        )

        return ForecastEvalResult(
            station_id=station_id,
            n_train=len(train),
            n_test=len(test),
            model_mae=round(model_mae, 4),
            model_rmse=round(model_rmse, 4),
            model_mape=round(model_mape, 2) if model_mape else None,
            baseline_mae=round(base_mae, 4),
            baseline_rmse=round(base_rmse, 4),
            improvement_pct=round(improvement, 1),
            model_source=forecaster.predict_utilization(station_id)["source"],
            eval_date=datetime.utcnow().isoformat(),
        )

    def evaluate_all(
        self,
        station_sessions: dict,   # {station_id: [sessions]}
        power_by_station: dict,   # {station_id: kw}
    ) -> List[ForecastEvalResult]:
        results = []
        for station_id, sessions in station_sessions.items():
            kw = power_by_station.get(station_id, 50.0)
            r  = self.evaluate_station(station_id, sessions, power_kw=kw)
            results.append(r)
        return results

    def save_results(
        self,
        results: List[ForecastEvalResult],
        path: str = "forecast_eval.json",
    ) -> None:
        data = {
            "evaluation_date": datetime.utcnow().isoformat(),
            "n_stations": len(results),
            "aggregate": {
                "mean_mae":          round(float(np.mean([r.model_mae for r in results])), 4),
                "mean_rmse":         round(float(np.mean([r.model_rmse for r in results])), 4),
                "mean_improvement":  round(float(np.mean([r.improvement_pct for r in results])), 1),
            },
            "per_station": [asdict(r) for r in results],
        }
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Forecast evaluation saved to %s", path)
        except OSError as e:
            logger.warning("Could not save forecast eval: %s", e)

    @staticmethod
    def _empty_result(station_id: str, n: int) -> ForecastEvalResult:
        return ForecastEvalResult(
            station_id=station_id,
            n_train=n, n_test=0,
            model_mae=0.0, model_rmse=0.0, model_mape=None,
            baseline_mae=0.0, baseline_rmse=0.0,
            improvement_pct=0.0,
            model_source="insufficient_data",
            eval_date=datetime.utcnow().isoformat(),
        )


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    evaluator = ForecastEvaluator()
    logger.info("Run evaluate_all() with real session data from DataAgent.")
    logger.info("Example: python -c \"from models.forecaster_eval import *; ...\"")
    sys.exit(0)
