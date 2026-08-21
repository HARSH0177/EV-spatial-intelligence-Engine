"""
agents/explanation_agent.py  —  Sub-agent: reports, ranking, LLM explanations.

Improvements in this version
------------------------------
#9  data_quality labels ("live","estimated","fallback","mock-dev") surfaced
    in every driver response with a plain-English note.
#10 Ranking is driven by pre-computed rank_score from DriverAssistantAgent.
    Explanation strings come from rank_explanation field.
#13 Operator expansion report includes score transparency, weight table,
    and an explainable rationale per zone.  LLM explanation optionally
    appended per zone.
#14 Vertex AI Gemini explanations called asynchronously via vertex_explainer.
    Fallback to deterministic text if LLM is disabled or unavailable.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from config import cfg
from llm.vertex_explainer import explain_driver_recommendation, explain_operator_zone

logger = logging.getLogger(__name__)


# ── Data quality human-readable notes (Improvement 9) ────────────────────────

_DQ_NOTES = {
    "live":      "Real-time port status from OCPP charger hardware.",
    "estimated": "ML-predicted availability based on session history. No live sensor.",
    "fallback":  "Live data unavailable — showing cached/estimated fallback.",
    "mock-dev":  "Demo mode: hardcoded dev data. Not suitable for production use.",
    "unknown":   "Data source unknown.",
}


class ExplanationAgent:
    def __init__(self):
        self.name = "ExplanationAgent"

    # ── Expansion Report (Improvement 13) ─────────────────────────────────────

    async def build_expansion_report(
        self, top_zones: list, city: str, budget_usd: float
    ) -> dict:
        budget_per_zone = budget_usd / max(len(top_zones), 1)
        zone_details, infra_plans = [], []
        w = cfg.scoring   # scoring weights for transparency

        for i, z in enumerate(top_zones, 1):
            zip_code    = z["zip_code"]
            score       = z["score"]
            traffic     = z.get("avg_daily_traffic", 0)
            ev_reg      = z.get("ev_registrations", 0)
            population  = z.get("population", 0)
            grid_kw     = z.get("grid_capacity_kw", 0)
            competitors = z.get("competitor_stations", 0)
            sb          = z.get("score_breakdown", {})

            fast_chargers = max(4, min(16, round(traffic / 4000)))
            parking_slots = fast_chargers * 3
            bike_docks    = round(parking_slots * 0.5)
            est_cost      = fast_chargers * 75_000 + parking_slots * 8_000 + bike_docks * 2_000

            # LLM explanation (optional, async, falls back to deterministic)
            llm_explanation = await explain_operator_zone(
                {**z, "city": city,
                 "daily_traffic": traffic,
                 "ev_registrations": ev_reg,
                 "existing_competitors": competitors,
                 "grid_capacity_kw": grid_kw},
                w,
            )

            zone_details.append({
                "rank":               i,
                "zip_code":           zip_code,
                "score":              score,
                "tier":               z["recommendation_tier"],
                "ev_registrations":   ev_reg,
                "population":         population,
                "daily_traffic":      traffic,
                "grid_capacity_kw":   grid_kw,
                "existing_competitors": competitors,
                "score_breakdown":    sb,
                # Improvement 13: weight table alongside scores
                "score_weights": {
                    "ev_demand":       w.ev_demand,
                    "traffic":         w.traffic,
                    "competition_gap": w.competition_gap,
                    "grid":            w.grid,
                    "land_cost":       w.land_cost,
                    "accessibility":   w.accessibility,
                },
                "llm_explanation":    llm_explanation or self._fallback_zone_explanation(z, city),
            })
            infra_plans.append({
                "zip_code":    zip_code,
                "rank":        i,
                "infrastructure": {
                    "fast_chargers_150kw": fast_chargers,
                    "ev_parking_slots":    parking_slots,
                    "bike_scooter_docks":  bike_docks,
                },
                "estimated_capex_usd":  est_cost,
                "allocated_budget_usd": round(budget_per_zone),
                "within_budget":        est_cost <= budget_per_zone,
                "rationale": (
                    f"ZIP {zip_code}: {ev_reg} EV registrations, "
                    f"{traffic:,} daily traffic, {competitors} competitors, "
                    f"{grid_kw} kW grid. Score: {score:.3f}"
                ),
            })

        top_zips = [z["zip_code"] for z in top_zones]
        summary  = (
            f"Top {len(top_zones)} ZIP codes in {city}: {', '.join(top_zips)}. "
            f"Total budget ${budget_usd:,.0f} across {len(top_zones)} zones."
        )

        return {
            "summary":              summary,
            "city":                 city,
            "analysis_date":        datetime.now(timezone.utc).isoformat(),
            "total_budget_usd":     budget_usd,
            "zone_analysis":        zone_details,
            "infrastructure_plans": infra_plans,
            "scoring_model": {
                "description": "EV Business Potential Score — 6-factor weighted model",
                "weights":     {
                    "ev_demand":       w.ev_demand,
                    "traffic":         w.traffic,
                    "competition_gap": w.competition_gap,
                    "grid":            w.grid,
                    "land_cost":       w.land_cost,
                    "accessibility":   w.accessibility,
                },
                "note": "Weights configurable via SCORE_W_* environment variables.",
            },
            "next_steps": [
                "Commission site surveys in recommended ZIP codes",
                "Initiate utility grid connection negotiations",
                "Secure zoning and permit applications",
                "Engage real-estate partners for land acquisition",
                "Begin equipment procurement for fast charger units",
            ],
        }

    # ── Driver Response (Improvements 9+10+14) ────────────────────────────────

    async def build_driver_response(
        self,
        enriched:  dict,
        user_lat:  float,
        user_lon:  float,
    ) -> dict:
        chargers  = enriched.get("chargers", [])
        hubs      = enriched.get("hubs", [])
        hour      = enriched.get("current_hour", 12)

        if not chargers:
            return self._empty_response(user_lat, user_lon, hour)

        # Sort by pre-computed rank_score descending (Improvement 10)
        chargers_ranked = sorted(
            chargers, key=lambda c: c.get("rank_score", 0), reverse=True
        )

        available = [c for c in chargers_ranked if (c.get("free_ports") or 0) > 0]
        busy      = [c for c in chargers_ranked if (c.get("free_ports") or 0) == 0]
        nearest   = available[0] if available else None

        # LLM explanation for top recommendation (Improvement 14)
        llm_text = None
        if nearest:
            llm_text = await explain_driver_recommendation(
                nearest,
                nearest.get("rank_score", 0.0),
                cfg.ranking,
            )

        # Deterministic fallback tip
        if available:
            det_tip = f"{len(available)} charger(s) available nearby."
        else:
            avg_w = round(sum(c.get("wait_time_minutes") or 0 for c in busy) / max(len(busy), 1))
            det_tip = f"All {len(chargers)} chargers busy. Estimated wait ~{avg_w} min."

        # Collect unique data quality levels present in results
        dq_present = list({c.get("data_quality", "unknown") for c in chargers})
        dq_notes   = {k: _DQ_NOTES[k] for k in dq_present if k in _DQ_NOTES}

        return {
            "user_location":        {"lat": user_lat, "lon": user_lon},
            "current_time_utc":     f"{hour:02d}:00",
            "system_tip":           llm_text or det_tip,
            "recommendation_basis": llm_text and "vertex_ai_gemini" or "deterministic",
            "available_chargers":   available,
            "busy_chargers":        busy,
            "nearby_hubs":          hubs,
            "total_chargers_found": len(chargers),
            "total_free_ports":     sum((c.get("free_ports") or 0) for c in chargers),
            "nearest_available":    nearest,
            # Improvement 9: transparent data quality
            "data_quality_summary": {
                "levels_present": dq_present,
                "explanations":   dq_notes,
            },
            # Improvement 10: ranking config surfaced
            "ranking_config": {
                "weights": {
                    "wait_time":     cfg.ranking.wait_time,
                    "free_ports":    cfg.ranking.free_ports,
                    "distance":      cfg.ranking.distance,
                    "charger_speed": cfg.ranking.charger_speed,
                },
                "note": "Override via RANK_W_* environment variables.",
            },
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fallback_zone_explanation(zone: dict, city: str) -> str:
        sb  = zone.get("score_breakdown", {})
        top = sorted(sb.items(), key=lambda x: x[1], reverse=True)[:2]
        top_factors = " and ".join(k.replace("_", " ") for k, _ in top)
        return (
            f"ZIP {zone.get('zip_code')} in {city} scores {zone.get('score', 0):.3f} "
            f"({zone.get('recommendation_tier', '?')}), driven mainly by {top_factors}."
        )

    @staticmethod
    def _empty_response(lat: float, lon: float, hour: int) -> dict:
        return {
            "user_location":        {"lat": lat, "lon": lon},
            "current_time_utc":     f"{hour:02d}:00",
            "system_tip":           "No chargers found within the requested radius.",
            "recommendation_basis": "deterministic",
            "available_chargers":   [],
            "busy_chargers":        [],
            "nearby_hubs":          [],
            "total_chargers_found": 0,
            "total_free_ports":     0,
            "nearest_available":    None,
            "data_quality_summary": {"levels_present": [], "explanations": {}},
            "ranking_config":       {},
        }
