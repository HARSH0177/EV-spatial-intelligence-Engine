"""
models/queue_model.py  —  M/M/c (Erlang C) queuing model for EV charger wait times.
"""

import math
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class QueueMetrics:
    arrival_rate_per_hour: float
    service_rate_per_hour: float
    num_ports:             int
    traffic_intensity:     float
    prob_wait:             float
    expected_wait_min:     float
    wait_p50_min:          float
    wait_p90_min:          float
    utilization_pct:       float
    queue_status:          str
    is_overloaded:         bool

    def to_dict(self) -> dict:
        return asdict(self)


class MMcQueueModel:

    def compute(
        self,
        arrival_rate_per_hour: float,
        avg_session_minutes:   float,
        num_ports:             int,
    ) -> QueueMetrics:
        lam = max(arrival_rate_per_hour, 1e-9)
        mu  = 60.0 / max(avg_session_minutes, 1.0)
        c   = max(num_ports, 1)
        rho = lam / (c * mu)

        if rho >= 1.0:
            return QueueMetrics(
                arrival_rate_per_hour=round(lam, 4),
                service_rate_per_hour=round(mu, 4),
                num_ports=c,
                traffic_intensity=round(min(rho, 9.99), 4),
                prob_wait=1.0,
                expected_wait_min=round(avg_session_minutes * 2, 1),
                wait_p50_min=round(avg_session_minutes, 1),
                wait_p90_min=round(avg_session_minutes * 3, 1),
                utilization_pct=100.0,
                queue_status="Critical",
                is_overloaded=True,
            )

        ec           = self._erlang_c(lam, mu, c, rho)
        denom        = c * mu - lam
        exp_wait_min = (ec / denom * 60) if denom > 0 else avg_session_minutes * 2
        p50          = self._percentile_wait(0.50, ec, c, mu, lam)
        p90          = self._percentile_wait(0.90, ec, c, mu, lam)
        util_pct     = rho * 100

        if util_pct < 50:   status = "Low"
        elif util_pct < 65: status = "Moderate"
        elif util_pct < 90: status = "High"
        else:               status = "Critical"

        return QueueMetrics(
            arrival_rate_per_hour=round(lam, 4),
            service_rate_per_hour=round(mu, 4),
            num_ports=c,
            traffic_intensity=round(rho, 4),
            prob_wait=round(ec, 4),
            expected_wait_min=round(exp_wait_min, 1),
            wait_p50_min=round(p50, 1),
            wait_p90_min=round(p90, 1),
            utilization_pct=round(util_pct, 1),
            queue_status=status,
            is_overloaded=False,
        )

    def _erlang_c(self, lam: float, mu: float, c: int, rho: float) -> float:
        a = lam / mu
        try:
            log_num = c * math.log(a) - math.lgamma(c + 1) - math.log(1 - rho)
        except (ValueError, OverflowError):
            return 1.0

        log_terms = []
        for k in range(c):
            try:
                log_terms.append(k * math.log(max(a, 1e-300)) - math.lgamma(k + 1))
            except (ValueError, OverflowError):
                continue

        if not log_terms:
            return 1.0

        pivot   = max(log_terms + [log_num])
        sum_exp = sum(math.exp(t - pivot) for t in log_terms)
        num_exp = math.exp(log_num - pivot)
        total   = sum_exp + num_exp
        return min(num_exp / total, 1.0) if total > 0 else 1.0

    def _percentile_wait(self, percentile: float, erlang_c: float,
                         c: int, mu: float, lam: float) -> float:
        denom = c * mu - lam
        if denom <= 0 or erlang_c <= 0:
            return 0.0
        tail = (1.0 - percentile) / erlang_c
        if tail <= 0 or tail > 1.0:
            return 0.0
        try:
            return max(0.0, -math.log(tail) / denom * 60)
        except (ValueError, ZeroDivisionError):
            return 0.0