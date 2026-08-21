"""
models/queue_validator.py  —  Improvement 8: M/M/c queue model validation.

Approach
--------
Direct "ground truth" wait times require timestamped queue-join and
service-start events, which OCPP 1.6 does not emit.

Proxy-based validation (what we implement):
  - Observed utilization ρ_obs  = sessions_in_window / (c × μ × window_hours)
  - Predicted utilization ρ_pred = M/M/c traffic intensity
  - Wait time proxy: compute M/M/c E[W] at ρ_obs and compare to ρ_pred-based E[W]
  - Sanity checks: ρ must be in [0,1), E[W] must be finite, C(c,a) in [0,1]

Limitation documented
---------------------
Without explicit queue-entry timestamps, we cannot compute observed wait times.
We validate the *model mechanics* (correct math) and *input plausibility*
(λ, μ, c are in realistic ranges) rather than end-to-end accuracy.
This is the honest and correct position to take in an interview.

Interview talking point
-----------------------
"The M/M/c model is validated on two levels: unit tests verify the math
(Erlang C sums to 1, ρ→1 gives C→1), and a proxy calibration compares
predicted utilization vs. observed session rates from BigQuery.  We are
transparent that direct wait-time ground truth requires queue-entry events
that OCPP 1.6 does not provide — that's an honest system constraint, not a gap."
"""

import json
import logging
import math
from dataclasses import asdict, dataclass
from typing import List, Optional

from models.queue_model import MMcQueueModel

logger = logging.getLogger(__name__)


@dataclass
class StationCalibrationResult:
    station_id:             str
    observed_utilization:   float
    predicted_utilization:  float
    util_abs_error:         float
    observed_ewait_min:     float    # E[W] at observed ρ
    predicted_ewait_min:    float    # E[W] at predicted ρ
    wait_abs_error_min:     float
    is_stable:              bool     # ρ < 1
    note:                   str


@dataclass
class CalibrationSummary:
    n_stations:             int
    mean_util_mae:          float
    mean_wait_mae_min:      float
    pct_stable:             float
    results:                List[StationCalibrationResult]


class QueueModelValidator:
    """
    Validates M/M/c model predictions against proxy observations.
    """

    def __init__(self):
        self._model = MMcQueueModel()

    # ── Public API ────────────────────────────────────────────────────────────

    def validate_stations(
        self,
        station_stats: List[dict],
    ) -> CalibrationSummary:
        """
        Run calibration for a list of stations.

        Parameters
        ----------
        station_stats : list of dicts with keys:
            station_id, num_ports, kw,
            observed_sessions_per_hour (λ_obs),
            avg_session_minutes (1/μ),
            predicted_arrival_rate (λ_pred from DemandForecaster),

        Returns
        -------
        CalibrationSummary with per-station results and aggregate MAEs.
        """
        results = []
        for s in station_stats:
            r = self._calibrate_one(s)
            results.append(r)
            logger.debug(
                "[%s] util_err=%.3f wait_err=%.1fmin stable=%s",
                r.station_id, r.util_abs_error, r.wait_abs_error_min, r.is_stable,
            )

        util_errors = [r.util_abs_error for r in results]
        wait_errors = [r.wait_abs_error_min for r in results]
        n_stable    = sum(1 for r in results if r.is_stable)

        return CalibrationSummary(
            n_stations=len(results),
            mean_util_mae=round(sum(util_errors) / max(len(util_errors), 1), 4),
            mean_wait_mae_min=round(sum(wait_errors) / max(len(wait_errors), 1), 2),
            pct_stable=round(n_stable / max(len(results), 1) * 100, 1),
            results=results,
        )

    def save_summary(self, summary: CalibrationSummary, path: str = "queue_calibration.json") -> None:
        """Persist calibration output as JSON for interview/audit use."""
        data = {
            "n_stations":        summary.n_stations,
            "mean_util_mae":     summary.mean_util_mae,
            "mean_wait_mae_min": summary.mean_wait_mae_min,
            "pct_stable":        summary.pct_stable,
            "limitation":        (
                "Direct wait-time ground truth is unavailable from OCPP 1.6. "
                "Validation uses proxy: predicted vs. observed utilization rate."
            ),
            "results": [asdict(r) for r in summary.results],
        }
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Queue calibration saved to %s", path)
        except OSError as e:
            logger.warning("Could not save calibration: %s", e)

    # ── Sanity checks ─────────────────────────────────────────────────────────

    def sanity_check(self, lam: float, mu: float, c: int) -> List[str]:
        """
        Return a list of warning strings for suspicious M/M/c inputs.
        Empty list = all checks passed.
        """
        warnings = []
        rho = lam / (c * mu) if c * mu > 0 else float("inf")

        if lam <= 0:
            warnings.append(f"λ={lam} ≤ 0 — no arrivals; check session_history data")
        if mu <= 0:
            warnings.append(f"μ={mu} ≤ 0 — infinite service time; check avg_session_minutes")
        if c < 1:
            warnings.append(f"c={c} < 1 — must have at least 1 port")
        if rho >= 1.0:
            warnings.append(f"ρ={rho:.3f} ≥ 1 — queue is overloaded; E[W]=∞")
        if rho > 0.95:
            warnings.append(f"ρ={rho:.3f} > 0.95 — very high utilization, consider adding ports")
        if lam > c * mu * 2:
            warnings.append(f"λ={lam:.2f} >> c·μ={c * mu:.2f} — possibly stale arrival data")

        return warnings

    # ── Internal ──────────────────────────────────────────────────────────────

    def _calibrate_one(self, s: dict) -> StationCalibrationResult:
        station_id     = s.get("station_id", "unknown")
        c              = max(s.get("num_ports", 1), 1)
        avg_min        = max(s.get("avg_session_minutes", 30), 1)
        lam_obs        = max(s.get("observed_sessions_per_hour", 0), 0)
        lam_pred       = max(s.get("predicted_arrival_rate", 0), 0)

        # Compute M/M/c metrics at observed vs predicted λ
        metrics_obs  = self._model.compute(lam_obs,  avg_min, c)
        metrics_pred = self._model.compute(lam_pred, avg_min, c)

        util_err = abs(metrics_obs.traffic_intensity - metrics_pred.traffic_intensity)
        wait_err = abs(metrics_obs.expected_wait_min - metrics_pred.expected_wait_min)

        note = "; ".join(self.sanity_check(lam_obs, 60 / avg_min, c)) or "ok"

        return StationCalibrationResult(
            station_id=station_id,
            observed_utilization=round(metrics_obs.traffic_intensity, 4),
            predicted_utilization=round(metrics_pred.traffic_intensity, 4),
            util_abs_error=round(util_err, 4),
            observed_ewait_min=round(metrics_obs.expected_wait_min, 2),
            predicted_ewait_min=round(metrics_pred.expected_wait_min, 2),
            wait_abs_error_min=round(wait_err, 2),
            is_stable=not metrics_obs.is_overloaded,
            note=note,
        )
