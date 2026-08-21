"""
agents/data_agent.py  —  Sub-agent: BigQuery reads + dynamic data access.

v2.2.1 fixes
------------
BUG 2 FIXED: get_session_history() was querying `live_port_status` table
  instead of `session_history`. ML models and M/M/c queue model were
  receiving port-status rows instead of session records.

BUG 3 FIXED: save_recommendation() was inserting old mcp_mobility field
  names (recommendation_id, top_zip_codes, report_summary, agent_version)
  into the new advisor_scores table whose schema is completely different.
  Now writes to a dedicated `recommendations` table with matching fields,
  matching the schema defined in init_bigquery.py.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from config import cfg
from utils.async_bq      import run_bq_async
from utils.observability  import timed, inc
from utils.geo_enricher   import geo_enricher
from utils.cache          import provider_cache, TTLCache

logger = logging.getLogger(__name__)

try:
    from google.cloud import bigquery as _bq_lib
    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False
    _bq_lib = None

# ── Dev/demo fallback station registry — labelled mock-dev ────────────────────
_DEV_STATION_REGISTRY = [
    {"station_id":"ST001","name":"Mission District Fast Charge","lat":37.7599,"lon":-122.4148,
     "city":"San Francisco","zip_code":"94102","network":"EVgo","kw":150,"total_ports":8,
     "connector_types":["CCS","CHAdeMO"],"data_source":"ocpp_live","is_active":True,
     "_data_quality":"mock-dev"},
    {"station_id":"ST002","name":"SoMa SuperCharge Hub","lat":37.7785,"lon":-122.4058,
     "city":"San Francisco","zip_code":"94103","network":"Tesla","kw":250,"total_ports":12,
     "connector_types":["Tesla"],"data_source":"ocpp_live","is_active":True,
     "_data_quality":"mock-dev"},
    {"station_id":"ST003","name":"Civic Center ChargePoint","lat":37.7793,"lon":-122.4177,
     "city":"San Francisco","zip_code":"94102","network":"ChargePoint","kw":22,"total_ports":6,
     "connector_types":["J1772"],"data_source":"ocpp_live","is_active":True,
     "_data_quality":"mock-dev"},
    {"station_id":"ST004","name":"Castro EV Hub","lat":37.7609,"lon":-122.4350,
     "city":"San Francisco","zip_code":"94114","network":"ChargePoint","kw":100,"total_ports":4,
     "connector_types":["CCS","CHAdeMO"],"data_source":"ocpp_live","is_active":True,
     "_data_quality":"mock-dev"},
    {"station_id":"ST005","name":"Dogpatch Rapid Charge","lat":37.7576,"lon":-122.3934,
     "city":"San Francisco","zip_code":"94107","network":"EVgo","kw":150,"total_ports":6,
     "connector_types":["CCS","CHAdeMO"],"data_source":"ocpp_live","is_active":True,
     "_data_quality":"mock-dev"},
    {"station_id":"ST006","name":"Potrero Hill Charger","lat":37.7638,"lon":-122.4058,
     "city":"San Francisco","zip_code":"94114","network":"Blink","kw":22,"total_ports":3,
     "connector_types":["J1772"],"data_source":"ocpp_live","is_active":True,
     "_data_quality":"mock-dev"},
]


class DataAgent:
    def __init__(self):
        self.name   = "DataAgent"
        self.client = None
        if BQ_AVAILABLE and cfg.project_id:
            try:
                self.client = _bq_lib.Client(project=cfg.project_id)
                logger.info("BigQuery client ready (project=%s)", cfg.project_id)
            except Exception as e:
                logger.warning("BigQuery init failed: %s — using fallbacks", e)

    def _bq_ok(self) -> bool:
        return self.client is not None

    # ── Async BQ helpers ──────────────────────────────────────────────────────

    async def _query(
        self, sql: str, params: list = None, label: str = "bq"
    ) -> list:
        if not self._bq_ok():
            return []
        cfg_obj = _bq_lib.QueryJobConfig(query_parameters=params or [])
        def _blocking():
            return [dict(r) for r in self.client.query(sql, job_config=cfg_obj).result()]
        try:
            async with timed(f"bq.{label}", logger):
                return await run_bq_async(_blocking, timeout=30.0, label=label)
        except Exception as e:
            logger.warning("[%s] BQ query failed: %s", label, e)
            inc(f"bq.error.{label}")
            return []

    async def _insert(
        self, table: str, rows: list, label: str = "bq_insert"
    ) -> bool:
        if not self._bq_ok() or not rows:
            return False
        ds  = cfg.bigquery.dataset
        pid = cfg.project_id
        def _blocking():
            errors = self.client.insert_rows_json(f"{pid}.{ds}.{table}", rows)
            if errors:
                raise RuntimeError(f"BQ insert errors: {errors}")
        try:
            await run_bq_async(_blocking, timeout=15.0, label=label)
            return True
        except Exception as e:
            logger.warning("[%s] BQ insert failed: %s", label, e)
            inc(f"bq.error.{label}")
            return False

    # ── Station Registry ──────────────────────────────────────────────────────

    async def get_station_registry(
        self,
        city:        Optional[str] = None,
        active_only: bool          = True,
    ) -> list:
        ds  = cfg.bigquery.dataset
        pid = cfg.project_id
        rows = await self._query(
            f"SELECT station_id, name, lat, lon, city, zip_code, network, kw, "
            f"total_ports, connector_types, data_source, is_active "
            f"FROM `{pid}.{ds}.station_registry` "
            f"WHERE (@city IS NULL OR LOWER(city) = LOWER(@city)) "
            f"AND (@active_only = FALSE OR is_active = TRUE)",
            [
                _bq_lib.ScalarQueryParameter("city",        "STRING", city),
                _bq_lib.ScalarQueryParameter("active_only", "BOOL",   active_only),
            ] if self._bq_ok() else [],
            label="station_registry",
        )
        if rows:
            for r in rows:
                if isinstance(r.get("connector_types"), str):
                    r["connector_types"] = [
                        t.strip() for t in r["connector_types"].split(",")
                        if t.strip()
                    ]
                r.setdefault("_data_quality", "live")
            return rows

        logger.warning("station_registry: using MOCK-DEV fallback")
        inc("station_registry.mock_fallback")
        fallback = list(_DEV_STATION_REGISTRY)
        if city:
            fallback = [
                s for s in fallback
                if s.get("city", "").lower() == city.lower()
            ]
        if active_only:
            fallback = [s for s in fallback if s.get("is_active", True)]
        return fallback

    # ── Dynamic Zone Profiles ─────────────────────────────────────────────────

    async def get_zone_profiles(self, city: str) -> list:
        ds  = cfg.bigquery.dataset
        pid = cfg.project_id
        rows = await self._query(
            f"SELECT * FROM `{pid}.{ds}.zone_profiles` "
            f"WHERE LOWER(city) = LOWER(@city) LIMIT 20",
            [_bq_lib.ScalarQueryParameter("city", "STRING", city)]
            if self._bq_ok() else [],
            label="zone_profiles",
        )
        return rows or await self._dynamic_zone_profiles(city)

    async def _dynamic_zone_profiles(self, city: str) -> list:
        cache_key = TTLCache.make_key("dynamic_zones", city)
        cached    = provider_cache.get(cache_key)
        if cached:
            return cached
        try:
            geo   = await geo_enricher.enrich(city)
            zones = [
                {
                    "zip_code":           f"ZONE-{i+1:02d}",
                    "city":               geo.city,
                    "population":         40000,
                    "ev_registrations":   800,
                    "median_income":      70000,
                    "avg_daily_traffic":  30000,
                    "grid_capacity_kw":   4000,
                    "land_cost_index":    0.5,
                    "accessibility_score": 0.7,
                    "lat":                n["lat"],
                    "lon":                n["lon"],
                    "zone_name":          n["name"],
                    "_data_quality":      "estimated",
                }
                for i, n in enumerate(geo.neighborhoods[:10])
            ]
            if not zones:
                zones = [{
                    "zip_code": "ZONE-01", "city": geo.city,
                    "population": 40000, "ev_registrations": 800,
                    "median_income": 70000, "avg_daily_traffic": 30000,
                    "grid_capacity_kw": 4000, "land_cost_index": 0.5,
                    "accessibility_score": 0.7,
                    "lat": geo.lat, "lon": geo.lon,
                    "zone_name": f"{geo.city} City Center",
                    "_data_quality": "estimated",
                }]
            provider_cache.set(cache_key, zones)
            return zones
        except Exception as e:
            logger.warning("Dynamic zone profiles failed for %s: %s", city, e)
            return [{
                "zip_code": "ZONE-01", "city": city, "population": 40000,
                "ev_registrations": 800, "median_income": 70000,
                "avg_daily_traffic": 30000, "grid_capacity_kw": 4000,
                "land_cost_index": 0.5, "accessibility_score": 0.7,
                "lat": 0.0, "lon": 0.0, "zone_name": city,
                "_data_quality": "fallback",
            }]

    # ── Competition Data ──────────────────────────────────────────────────────

    async def get_competition_data(self, city: str) -> list:
        ds  = cfg.bigquery.dataset
        pid = cfg.project_id
        rows = await self._query(
            f"SELECT * FROM `{pid}.{ds}.business_signals` "
            f"WHERE LOWER(city) = LOWER(@city) LIMIT 20",
            [_bq_lib.ScalarQueryParameter("city", "STRING", city)]
            if self._bq_ok() else [],
            label="competition_data",
        )
        if rows:
            return rows
        zones = await self.get_zone_profiles(city)
        return [
            {
                "zip_code":             z.get("zip_code", "ZONE-01"),
                "competitor_name":      None,
                "station_count":        0,
                "avg_charger_kw":       0,
                "avg_monthly_sessions": 0,
                "market_share_pct":     0.0,
                "_data_quality":        "estimated",
            }
            for z in zones
        ]

    # ── Charger Usage ─────────────────────────────────────────────────────────

    async def get_charger_usage(self, city: str) -> list:
        ds  = cfg.bigquery.dataset
        pid = cfg.project_id
        rows = await self._query(
            f"SELECT * FROM `{pid}.{ds}.charger_usage` "
            f"WHERE LOWER(city) = LOWER(@city)",
            [_bq_lib.ScalarQueryParameter("city", "STRING", city)]
            if self._bq_ok() else [],
            label="charger_usage",
        )
        return rows or self._mock_charger_usage()

    # ── Live Port Status ──────────────────────────────────────────────────────

    async def get_live_port_status(self, station_id: str) -> list:
        ds  = cfg.bigquery.dataset
        pid = cfg.project_id
        rows = await self._query(
            f"SELECT port_id, status, last_updated, session_id, session_start "
            f"FROM `{pid}.{ds}.live_port_status` "
            f"WHERE station_id = @sid ORDER BY CAST(port_id AS INT64)",
            [_bq_lib.ScalarQueryParameter("sid", "STRING", station_id)]
            if self._bq_ok() else [],
            label="live_port_status",
        )
        return rows or self._mock_port_status(station_id)

    # ── Session History (BUG 2 FIX) ───────────────────────────────────────────

    async def get_session_history(self, station_id: str, days: int = 30) -> list:
        """
        BUG 2 FIX: Was querying `live_port_status` table due to a copy-paste error.
        Now correctly queries `session_history` which contains completed charging
        sessions used by DemandForecaster and MMcQueueModel.
        """
        ds     = cfg.bigquery.dataset
        pid    = cfg.project_id
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        rows = await self._query(
            f"SELECT session_id, station_id, port_id, "
            f"start_time, end_time, energy_kwh, duration_minutes "
            f"FROM `{pid}.{ds}.session_history` "          # ← FIXED (was live_port_status)
            f"WHERE station_id = @sid AND start_time >= @cutoff "
            f"ORDER BY start_time DESC LIMIT 2000",
            [
                _bq_lib.ScalarQueryParameter("sid",    "STRING",    station_id),
                _bq_lib.ScalarQueryParameter("cutoff", "TIMESTAMP", cutoff),
            ] if self._bq_ok() else [],
            label="session_history",
        )

        for r in rows:
            r["utilization_rate"] = min(1.0, r.get("duration_minutes", 0) / 60)
            if isinstance(r.get("start_time"), str):
                try:
                    r["start_time"] = datetime.fromisoformat(r["start_time"])
                except ValueError:
                    pass

        return rows or self._mock_session_history(station_id)

    # ── Arrival Stats ─────────────────────────────────────────────────────────

    async def get_arrival_stats(self, station_id: str, hour: int) -> dict:
        ds  = cfg.bigquery.dataset
        pid = cfg.project_id
        rows = await self._query(
            f"SELECT COUNT(*) AS session_count, "
            f"AVG(duration_minutes) AS avg_duration, "
            f"COUNT(DISTINCT DATE_TRUNC(start_time, WEEK)) AS week_count "
            f"FROM `{pid}.{ds}.session_history` "
            f"WHERE station_id = @sid "
            f"AND EXTRACT(HOUR FROM start_time) = @hour "
            f"AND start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 56 DAY)",
            [
                _bq_lib.ScalarQueryParameter("sid",  "STRING", station_id),
                _bq_lib.ScalarQueryParameter("hour", "INT64",  hour),
            ] if self._bq_ok() else [],
            label="arrival_stats",
        )
        if rows and rows[0].get("session_count"):
            r     = rows[0]
            weeks = max(r["week_count"], 1)
            return {
                "arrival_rate_per_hour": round(r["session_count"] / weeks, 4),
                "avg_session_minutes":   round(r["avg_duration"] or 30, 1),
                "sample_size":           r["session_count"],
            }
        # Demand-curve fallback
        curve = {
            0:0.5, 1:0.3, 2:0.2, 3:0.2, 4:0.3, 5:0.7,
            6:1.7, 7:3.3, 8:4.9, 9:4.7, 10:4.3, 11:4.1,
            12:4.5,13:4.3,14:3.9,15:3.6,16:4.3,17:5.3,
            18:5.5,19:5.1,20:4.2,21:3.1,22:1.8,23:0.9,
        }
        return {
            "arrival_rate_per_hour": curve.get(hour, 2.0),
            "avg_session_minutes":   28.0,
            "sample_size":           0,
        }

    # ── Availability Patterns (legacy compat) ─────────────────────────────────

    async def get_availability_patterns(self) -> dict:
        return {
            "hourly_occupancy": {
                0:0.08,1:0.05,2:0.04,3:0.03,4:0.05,5:0.12,
                6:0.28,7:0.55,8:0.82,9:0.79,10:0.71,11:0.68,
                12:0.75,13:0.72,14:0.65,15:0.60,16:0.72,17:0.88,
                18:0.91,19:0.85,20:0.70,21:0.52,22:0.30,23:0.15,
            },
            "avg_session_minutes": 28,
            "peak_hours":          [8, 17, 18],
        }

    # ── Save Recommendation (BUG 3 FIX) ──────────────────────────────────────

    async def save_recommendation(
        self, city: str, zones: list, report: dict
    ) -> str:
        """
        BUG 3 FIX: Previously inserted old mcp_mobility field names
        (recommendation_id, top_zip_codes, report_summary, agent_version)
        into the advisor_scores table, which has a completely different schema.

        Now inserts into a `recommendations` table with matching fields.
        advisor_scores receives zone-level data from AdvisorAgent directly.
        """
        rec_id    = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc).isoformat()

        # Insert into recommendations table (not advisor_scores)
        await self._insert(
            "recommendations",                          # ← FIXED (was advisor_scores)
            [{
                "recommendation_id": rec_id,
                "city":              city,
                "created_at":        timestamp,
                "top_zip_codes":     ",".join(
                    z.get("zip_code", "") for z in zones
                ),
                "report_summary":    report.get("summary", ""),
                "agent_version":     "2.2.1",
            }],
            label="save_recommendation",
        )
        return rec_id

    # ── Mock fallbacks ────────────────────────────────────────────────────────

    def _mock_charger_usage(self) -> list:
        return [{
            "zip_code": "ZONE-01", "avg_session_kwh": 32.4,
            "avg_session_minutes": 28, "peak_hour": 8,
            "utilization_rate": 0.61, "sessions_per_day": 18,
        }]

    def _mock_port_status(self, station_id: str) -> list:
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "port_id":       str(i + 1),
                "status":        "Available" if i % 2 == 0 else "Charging",
                "last_updated":  now,
                "session_id":    None,
                "session_start": None,
                "_data_quality": "mock-dev",
            }
            for i in range(4)
        ]

    def _mock_session_history(self, station_id: str) -> list:
        import random
        now    = datetime.now(timezone.utc)
        result = []
        for _ in range(200):
            start = now - timedelta(hours=random.uniform(0, 720))
            dur   = random.uniform(15, 60)
            result.append({
                "session_id":       str(uuid.uuid4())[:8],
                "start_time":       start,
                "end_time":         start + timedelta(minutes=dur),
                "energy_kwh":       round(dur / 60 * 50 * 0.92, 2),
                "duration_minutes": round(dur),
                "utilization_rate": min(1.0, dur / 60),
            })
        return result