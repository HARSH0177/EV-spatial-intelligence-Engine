"""
agents/orchestrator.py  —  Primary coordinator agent.

Improvements in this version
------------------------------
#6  Every workflow step is timed and logged via utils.observability.timed().
    Request IDs are threaded through all log lines for traceability.
#3  Driver workflow uses parallel enrichment (delegated to driver_agent).
#12 Connector type / min power / battery_pct filters passed through.
"""

import logging
import time
from typing import Optional

from agents.data_agent        import DataAgent
from agents.scoring_agent     import ScoringAgent
from agents.driver_agent      import DriverAssistantAgent
from agents.explanation_agent import ExplanationAgent
from utils.observability      import timed, inc, new_request_id

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    def __init__(self):
        self.data_agent        = DataAgent()
        self.scoring_agent     = ScoringAgent()
        self.driver_agent      = DriverAssistantAgent()
        self.explanation_agent = ExplanationAgent()
        self.name              = "OrchestratorAgent"

    # ─── Workflow 1: Expansion Planning ──────────────────────────────────────

    async def handle_expansion_request(
        self, city: str, budget_usd: float, top_n: int
    ) -> dict:
        req_id       = new_request_id()
        workflow_log = []
        start        = time.perf_counter()
        inc("workflow.expansion.started")

        async with timed("workflow.expansion", logger, extra={"req_id": req_id, "city": city}):

            async with timed("step.zone_profiles", logger):
                workflow_log.append("Step 1: DataAgent → fetching zone profiles")
                zones = await self.data_agent.get_zone_profiles(city)

            async with timed("step.competition_usage", logger):
                workflow_log.append("Step 2: DataAgent → competition & usage data")
                competition = await self.data_agent.get_competition_data(city)
                usage       = await self.data_agent.get_charger_usage(city)

            async with timed("step.scoring", logger):
                workflow_log.append("Step 3: ScoringAgent → EV Business Potential Scores")
                scored_zones = await self.scoring_agent.score_zones(zones, competition, usage)

            top_zones = scored_zones[:top_n]
            workflow_log.append(f"Step 4: OrchestratorAgent → selected top {top_n} zones")

            async with timed("step.report", logger):
                workflow_log.append("Step 5: ExplanationAgent → building report (+ LLM)")
                report = await self.explanation_agent.build_expansion_report(
                    top_zones, city, budget_usd
                )

            async with timed("step.persist", logger):
                workflow_log.append("Step 6: DataAgent → persisting to BigQuery")
                save_id = await self.data_agent.save_recommendation(city, top_zones, report)

        inc("workflow.expansion.completed")
        return {
            "workflow":          "company-expansion-planning",
            "request_id":        req_id,
            "city":              city,
            "budget_usd":        budget_usd,
            "recommendation_id": save_id,
            "top_zones":         top_zones,
            "report":            report,
            "workflow_log":      workflow_log,
            "agents_involved":   [
                "OrchestratorAgent", "DataAgent", "ScoringAgent",
                "ExplanationAgent", "VertexAI/Gemini (optional)",
            ],
            "elapsed_seconds": round(time.perf_counter() - start, 2),
        }

    # ─── Workflow 2: Driver Charger Locator ───────────────────────────────────

    async def handle_driver_request(
        self,
        lat:            Optional[float],
        lon:            Optional[float],
        max_km:         float,
        location_name:  Optional[str]   = None,
        connector_type: Optional[str]   = None,
        min_power_kw:   Optional[float] = None,
        battery_pct:    Optional[float] = None,   # reserved for future ETA calc
    ) -> dict:
        req_id       = new_request_id()
        workflow_log = []
        start        = time.perf_counter()
        geocode_info = None
        inc("workflow.driver.started")

        async with timed("workflow.driver", logger, extra={"req_id": req_id}):

            # Step 0: Geocode
            if location_name and (lat is None or lon is None):
                async with timed("step.geocode", logger):
                    workflow_log.append(f"Step 0: geocoding '{location_name}'")
                    geocode_info = await self.driver_agent.geocode_location(location_name)
                    lat = geocode_info["lat"]
                    lon = geocode_info["lon"]
                    workflow_log.append(
                        f"         ↳ ({lat:.5f}, {lon:.5f}) via {geocode_info['source']}"
                    )

            # Step 1: Find nearby (dynamic registry + NREL)
            async with timed("step.find_nearby", logger):
                workflow_log.append("Step 1: find nearby chargers (registry + NREL fallback)")
                nearby = await self.driver_agent.find_nearby_chargers(
                    lat, lon, max_km, self.data_agent,
                    connector_type=connector_type,
                    min_power_kw=min_power_kw,
                )

            # Steps 2-4: Parallel enrichment (BQ live status + M/M/c + ML forecast)
            async with timed("step.enrich", logger, extra={"n": len(nearby.get("chargers", []))}):
                workflow_log.append(
                    "Steps 2-4: parallel enrichment — live BQ status + M/M/c + ML forecast"
                )
                enriched = await self.driver_agent.enrich_with_live_availability(
                    nearby, self.data_agent
                )

            # Step 5: Format
            async with timed("step.format", logger):
                workflow_log.append("Step 5: ExplanationAgent → ranking + LLM tip")
                result = await self.explanation_agent.build_driver_response(
                    enriched, lat, lon
                )

        inc("workflow.driver.completed")
        response = {
            "workflow":         "driver-charger-locator",
            "request_id":       req_id,
            "user_location":    {"lat": lat, "lon": lon},
            "max_distance_km":  max_km,
            "filters_applied":  {
                "connector_type": connector_type,
                "min_power_kw":   min_power_kw,
                "battery_pct":    battery_pct,
            },
            "results":          result,
            "workflow_log":     workflow_log,
            "agents_involved":  [
                "OrchestratorAgent", "DriverAssistantAgent",
                "DataAgent", "ExplanationAgent",
                "MMcQueueModel", "DemandForecaster",
                "VertexAI/Gemini (optional)",
            ],
            "elapsed_seconds":  round(time.perf_counter() - start, 2),
        }

        if geocode_info:
            response["geocoded_from"] = {
                "input":            location_name,
                "resolved_address": geocode_info["resolved_address"],
                "source":           geocode_info["source"],
                "coordinates":      {"lat": lat, "lon": lon},
            }

        return response

    # ─── Generic Task Runner ──────────────────────────────────────────────────

    async def run_task(self, task_type: str, payload: dict) -> dict:
        if task_type == "expansion":
            return await self.handle_expansion_request(
                city=payload.get("city", "San Francisco"),
                budget_usd=payload.get("budget_usd", 5_000_000),
                top_n=payload.get("top_n", 3),
            )
        elif task_type == "locate":
            return await self.handle_driver_request(
                lat=payload.get("latitude"),
                lon=payload.get("longitude"),
                max_km=payload.get("max_distance_km", 10.0),
                location_name=payload.get("location"),
                connector_type=payload.get("connector_type"),
                min_power_kw=payload.get("min_power_kw"),
                battery_pct=payload.get("battery_pct"),
            )
        elif task_type == "status":
            from utils.observability import get_counts
            return {
                "agent":      self.name,
                "sub_agents": [
                    "DataAgent", "ScoringAgent",
                    "DriverAssistantAgent", "ExplanationAgent",
                    "MMcQueueModel", "DemandForecaster",
                ],
                "status":  "all_healthy",
                "metrics": get_counts(),
            }
        else:
            return {"error": f"Unknown task_type: {task_type}"}
