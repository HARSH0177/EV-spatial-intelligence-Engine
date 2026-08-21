"""
agents/driver_agent.py  —  Sub-agent: global discovery + enrichment.

v2.2.1 fixes
------------
BUG 1 FIXED: asyncio.coroutine removed in Python 3.11.
  All instances replaced with _empty_list() — a proper async coroutine.
BUG 2 FIXED: _supports_connector indentation corrected.
"""

import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from config import cfg
from models.queue_model            import MMcQueueModel
from models.demand_forecaster      import DemandForecaster
from realtime.nrel_client          import NRELClient
from realtime.openchargemap_client import ocm_client
from realtime.osm_places_client    import osm_client
from realtime.google_places_client import google_places_client
from utils.geo_enricher            import geo_enricher
from utils.provider_merge          import merge_and_dedupe
from utils.normalizers             import MobilityRecord
from utils.observability           import timed, inc

logger = logging.getLogger(__name__)

_queue_model = MMcQueueModel()
_forecaster  = DemandForecaster()
_nrel        = NRELClient()


# ── BUG 1 FIX: proper async empty-list coroutine ─────────────────────────────
async def _empty_list() -> list:
    """Replaces the removed asyncio.coroutine pattern for disabled task slots."""
    return []


class DriverAssistantAgent:
    def __init__(self):
        self.name        = "DriverAssistantAgent"
        self.queue_model = _queue_model
        self.forecaster  = _forecaster

    # ── Geocoding ─────────────────────────────────────────────────────────────

    async def geocode_location(self, location_name: str) -> dict:
        try:
            geo = await geo_enricher.enrich(location_name)
            return {
                "lat":              geo.lat,
                "lon":              geo.lon,
                "resolved_address": geo.display_name,
                "source":           geo.source,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.warning("GeoEnricher failed, trying direct Nominatim: %s", e)
            try:
                async with httpx.AsyncClient(timeout=8) as client:
                    resp = await client.get(
                        f"{cfg.providers.nominatim_url}/search",
                        params={"q": location_name, "format": "json", "limit": 1},
                        headers={"User-Agent": "EV-Advisor/2.2"},
                    )
                data = resp.json()
                if data:
                    return {
                        "lat":              float(data[0]["lat"]),
                        "lon":              float(data[0]["lon"]),
                        "resolved_address": data[0].get("display_name", location_name),
                        "source":           "nominatim_osm",
                    }
            except Exception as e2:
                logger.warning("Direct Nominatim also failed: %s", e2)
            raise ValueError(f"Could not resolve location '{location_name}'")

    # ── Discovery ─────────────────────────────────────────────────────────────

    async def find_nearby(
        self,
        lat:            float,
        lon:            float,
        max_km:         float,
        data_agent,
        record_type:    str             = "all",
        connector_type: Optional[str]   = None,
        min_power_kw:   Optional[float] = None,
    ) -> dict:
        async with timed("driver.find_nearby", logger, extra={"type": record_type}):
            want_all      = record_type == "all"
            want_chargers = want_all or record_type == "charger"
            want_parking  = want_all or record_type == "parking"
            want_mobility = want_all or record_type == "mobility_hub"

            tasks = [
                self._get_ocpp_records(data_agent, lat, lon, max_km)
                if want_chargers else _empty_list(),

                ocm_client.get_nearby(lat, lon, max_km, 50, connector_type, min_power_kw)
                if want_chargers else _empty_list(),

                google_places_client.get_ev_chargers(lat, lon, int(max_km * 1000))
                if want_chargers else _empty_list(),

                self._get_nrel_records(lat, lon, max_km)
                if want_chargers else _empty_list(),

                osm_client.get_parking_lots(lat, lon, int(max_km * 1000))
                if want_parking else _empty_list(),

                osm_client.get_mobility_hubs(lat, lon, int(max_km * 1000))
                if want_mobility else _empty_list(),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            ocpp_r = results[0] if not isinstance(results[0], Exception) else []
            ocm_r  = results[1] if not isinstance(results[1], Exception) else []
            gp_r   = results[2] if not isinstance(results[2], Exception) else []
            nrel_r = results[3] if not isinstance(results[3], Exception) else []
            park_r = results[4] if not isinstance(results[4], Exception) else []
            mob_r  = results[5] if not isinstance(results[5], Exception) else []

            ocpp_mob = [self._ocpp_to_record(s) for s in ocpp_r]

            merged = merge_and_dedupe(
                ocpp_mob, ocm_r, gp_r, nrel_r, park_r, mob_r,
                user_lat=lat, user_lon=lon,
            )

            if connector_type and want_chargers:
                ct = connector_type.upper()
                merged = [
                    r for r in merged
                    if r.type != "charger" or not r.connector_types
                    or any(ct in c.upper() for c in r.connector_types)
                ]
            if min_power_kw and want_chargers:
                merged = [
                    r for r in merged
                    if r.type != "charger" or r.power_kw is None
                    or r.power_kw >= min_power_kw
                ]

            chargers = [r for r in merged if r.type == "charger"]
            parking  = [r for r in merged if r.type == "parking"]
            mobility = [r for r in merged if r.type == "mobility_hub"]

            return {
                "chargers": chargers,
                "parking":  parking,
                "mobility": mobility,
                "hubs":     mobility,
            }

    async def find_nearby_chargers(
        self, lat, lon, max_km, data_agent, **kwargs
    ) -> dict:
        return await self.find_nearby(
            lat, lon, max_km, data_agent, record_type="charger", **kwargs
        )

    # ── Parallel enrichment ───────────────────────────────────────────────────

    async def enrich_with_live_availability(self, nearby: dict, data_agent) -> dict:
        now   = datetime.now(timezone.utc)
        hour  = now.hour
        items = nearby.get("chargers", [])

        if not items:
            return {**nearby, "current_hour": hour, "enriched_at": now.isoformat()}

        async with timed("driver.parallel_enrich", logger, extra={"n": len(items)}):
            enriched = await asyncio.gather(
                *[self._enrich_one(s, data_agent, now, hour) for s in items],
                return_exceptions=False,
            )

        return {
            "chargers":     list(enriched),
            "parking":      nearby.get("parking", []),
            "mobility":     nearby.get("mobility", []),
            "hubs":         nearby.get("hubs", []),
            "current_hour": hour,
            "enriched_at":  now.isoformat(),
        }

    async def _enrich_one(self, station, data_agent, now, hour) -> dict:
        station_id  = (getattr(station, "id", None)
                       or (station.get("id") if isinstance(station, dict) else ""))
        total_ports = (getattr(station, "total_ports", None)
                       or (station.get("total_ports", 4) if isinstance(station, dict) else 4)
                       or 4)
        power_kw    = getattr(station, "power_kw", 50) or 50
        data_source = getattr(station, "data_source", "unknown")
        base_dq     = getattr(station, "data_quality", "estimated")
        s_dict      = (station.to_dict() if hasattr(station, "to_dict")
                       else dict(station))

        try:
            if data_source == "ocpp_live" and base_dq != "mock-dev":
                port_rows = await data_agent.get_live_port_status(station_id)
                if port_rows and port_rows[0].get("_data_quality") == "mock-dev":
                    base_dq = "mock-dev"
                free_ports = sum(1 for p in port_rows if p.get("status") == "Available")
                charging   = sum(1 for p in port_rows if p.get("status") == "Charging")
            else:
                port_rows  = []
                free_ports = None
                charging   = None

            stats   = await data_agent.get_arrival_stats(station_id, hour)
            lam     = stats["arrival_rate_per_hour"]
            avg_min = stats["avg_session_minutes"]
            queue   = self.queue_model.compute(lam, avg_min, total_ports)

            if self.forecaster.needs_refit(station_id):
                sessions = await data_agent.get_session_history(station_id, days=30)
                self.forecaster.fit(station_id, sessions, power_kw=power_kw)
            forecast = self.forecaster.predict_utilization(station_id, at=now)

            if free_ports is None:
                pred_util  = forecast["predicted_utilization"]
                charging   = round(total_ports * pred_util)
                free_ports = max(0, total_ports - charging)

            status       = "Available" if free_ports > 0 else queue.queue_status
            wait_minutes = 0.0 if free_ports > 0 else queue.expected_wait_min

            rank_score = self._compute_rank_score(
                wait_minutes, free_ports, total_ports,
                s_dict.get("distance_km", 0), power_kw,
            )

            return {
                **s_dict,
                "port_detail":       port_rows,
                "free_ports":        free_ports,
                "charging_ports":    charging or 0,
                "total_ports":       total_ports,
                "current_status":    status,
                "wait_time_minutes": round(wait_minutes, 1),
                "wait_p90_minutes":  queue.wait_p90_min,
                "queue_metrics":     queue.to_dict(),
                "demand_forecast":   forecast,
                "rank_score":        round(rank_score, 4),
                "rank_explanation":  self._rank_explanation(
                    wait_minutes, free_ports, total_ports,
                    s_dict.get("distance_km", 0), power_kw, rank_score,
                ),
                "data_quality":      base_dq,
                "data_source":       data_source,
                "enriched_at":       now.isoformat(),
            }

        except Exception as exc:
            logger.warning("[%s] Enrichment failed: %s", station_id, exc)
            inc("enrichment.fallback")
            return {
                **s_dict,
                "port_detail":       [],
                "free_ports":        0,
                "charging_ports":    0,
                "total_ports":       total_ports,
                "current_status":    "Unknown",
                "wait_time_minutes": None,
                "wait_p90_minutes":  None,
                "queue_metrics":     {},
                "demand_forecast":   {},
                "rank_score":        0.0,
                "rank_explanation":  "Enrichment failed — data unavailable",
                "data_quality":      "fallback",
                "fallback_reason":   str(exc),
                "data_source":       data_source,
                "enriched_at":       now.isoformat(),
            }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _compute_rank_score(
        self, wait_min, free_ports, total_ports, distance_km, power_kw
    ) -> float:
        w           = cfg.ranking
        wait_score  = 1 - min(wait_min or 0, 60) / 60
        avail_score = free_ports / max(total_ports, 1)
        dist_score  = 1 - min(distance_km or 0, 20) / 20
        speed_score = min(power_kw or 50, 350) / 350
        return (
            w.wait_time       * wait_score
            + w.free_ports    * avail_score
            + w.distance      * dist_score
            + w.charger_speed * speed_score
        )

    def _rank_explanation(
        self, wait_min, free_ports, total_ports, distance_km, power_kw, score
    ) -> str:
        w = cfg.ranking
        return (
            f"Score {score:.3f}: wait {round(wait_min or 0)}min (×{w.wait_time}), "
            f"{free_ports}/{total_ports} free (×{w.free_ports}), "
            f"{distance_km}km (×{w.distance}), {power_kw}kW (×{w.charger_speed})"
        )

    async def _get_ocpp_records(
        self, data_agent, lat: float, lon: float, max_km: float
    ) -> list:
        registry = await data_agent.get_station_registry()
        result   = []
        for s in registry:
            d = self._dist_km(lat, lon, s["lat"], s["lon"])
            if d <= max_km:
                result.append({**s, "distance_km": round(d, 2), "id": s["station_id"]})
        return result

    async def _get_nrel_records(
        self, lat: float, lon: float, max_km: float
    ) -> list:
        try:
            raw = await _nrel.get_nearby_stations(lat, lon, radius_km=max_km)
            return [
                MobilityRecord(
                    id=r["id"], name=r["name"],
                    type="charger", subtypes=["ev_charger"],
                    lat=r["lat"], lon=r["lon"],
                    address=r.get("address"),
                    city=None, country=None,
                    operator=r.get("network"),
                    connector_types=r.get("connector_types", []),
                    power_kw=r.get("kw"),
                    total_ports=r.get("total_ports"),
                    available_ports=None, status=None,
                    price_info=None, accessibility=None,
                    data_source="nrel_afdc",
                    data_quality="estimated",
                    fallback_reason="NREL does not provide real-time status",
                    last_updated=None,
                )
                for r in raw
            ]
        except Exception:
            return []

    @staticmethod
    def _ocpp_to_record(s: dict) -> MobilityRecord:
        return MobilityRecord(
            id=s.get("station_id", s.get("id", "")),
            name=s.get("name", "EV Station"),
            type="charger", subtypes=["ev_charger"],
            lat=s.get("lat", 0), lon=s.get("lon", 0),
            address=s.get("address"),
            city=s.get("city"), country=None,
            operator=s.get("network"),
            connector_types=s.get("connector_types", []),
            power_kw=s.get("kw"),
            total_ports=s.get("total_ports"),
            available_ports=None, status=None,
            price_info=None, accessibility=None,
            data_source=s.get("data_source", "ocpp_live"),
            data_quality=s.get("_data_quality", "live"),
            fallback_reason=None, last_updated=None,
            distance_km=s.get("distance_km"),
        )

    @staticmethod
    def _supports_connector(station, connector_type: str) -> bool:
        if hasattr(station, "connector_types"):
            connectors = station.connector_types or []
        else:
            connectors = station.get("connector_types", []) or []
        if not connectors:
            return True
        from utils.normalizers import normalize_connector
        user_norm = normalize_connector(connector_type).upper()
        return any(normalize_connector(c).upper() == user_norm for c in connectors)

    @staticmethod
    def _dist_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R    = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a    = (math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))