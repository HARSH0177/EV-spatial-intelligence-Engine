"""
agents/scoring_agent.py  —  Sub-agent: EV Business Potential Score.

Improvements in this version
------------------------------
#13 All weights come from config.cfg.scoring — no magic constants.
    Weights are validated at startup (must sum to 1.0 ± 0.01).
    Score breakdown includes both raw sub-score and weighted contribution
    so an operator can immediately see which factor is driving the score.
"""

import logging
from config import cfg

logger = logging.getLogger(__name__)


class ScoringAgent:
    def __init__(self):
        self.name = "ScoringAgent"
        self._weights = cfg.scoring

    async def score_zones(self, zones: list, competition: list, usage: list) -> list:
        comp_by_zip  = {c["zip_code"]: c for c in competition}
        usage_by_zip = {u["zip_code"]: u for u in usage}

        scored = []
        for zone in zones:
            z    = zone["zip_code"]
            comp = comp_by_zip.get(z, {})
            usg  = usage_by_zip.get(z, {})

            raw, weighted = self._compute_score(zone, comp, usg)
            final_score   = round(sum(weighted.values()), 3)

            scored.append({
                **zone,
                "score":               final_score,
                "score_breakdown":     raw,          # raw sub-scores (0-1 each)
                "weighted_breakdown":  weighted,     # weight × sub-score contributions
                "utilization_rate":    usg.get("utilization_rate", 0),
                "competitor_stations": comp.get("station_count", 0),
                "recommendation_tier": self._tier(final_score),
            })

        return sorted(scored, key=lambda x: x["score"], reverse=True)

    def _compute_score(self, zone: dict, comp: dict, usg: dict) -> tuple:
        """Return (raw_dict, weighted_dict) — both keyed by factor name."""
        w = self._weights

        ev_density    = min(zone.get("ev_registrations", 0) / max(zone.get("population", 1), 1), 1.0)
        ev_demand     = round(min(ev_density * 10, 1.0), 3)
        traffic       = round(min(zone.get("avg_daily_traffic", 0) / 80_000, 1.0), 3)
        stations      = comp.get("station_count", 0)
        comp_gap      = round(max(0.0, 1 - stations / 8), 3)
        grid          = round(min(zone.get("grid_capacity_kw", 0) / 8_000, 1.0), 3)
        land_cost     = round(1 - zone.get("land_cost_index", 0.5), 3)
        accessibility = round(zone.get("accessibility_score", 0.5), 3)

        raw = {
            "ev_demand":       ev_demand,
            "traffic":         traffic,
            "competition_gap": comp_gap,
            "grid":            grid,
            "land_cost":       land_cost,
            "accessibility":   accessibility,
        }
        weighted = {
            "ev_demand":       round(w.ev_demand       * ev_demand,     4),
            "traffic":         round(w.traffic         * traffic,       4),
            "competition_gap": round(w.competition_gap * comp_gap,      4),
            "grid":            round(w.grid            * grid,          4),
            "land_cost":       round(w.land_cost       * land_cost,     4),
            "accessibility":   round(w.accessibility   * accessibility, 4),
        }
        return raw, weighted

    @staticmethod
    def _tier(score: float) -> str:
        if score >= 0.70:   return "HIGH PRIORITY"
        elif score >= 0.50: return "MEDIUM PRIORITY"
        else:               return "LOW PRIORITY"
