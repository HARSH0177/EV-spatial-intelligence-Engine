"""
realtime/nrel_client.py  —  NREL Alternative Fuels Station API client.

Used as fallback data source when OCPP real-time data is unavailable.
Results cached in-memory with 15-minute TTL.

Free key at: https://developer.nrel.gov/signup/
Cost: free always (rate limits apply on DEMO_KEY).
"""

import asyncio
import hashlib
import logging
import os
import time

import httpx

from utils.normalizers import MobilityRecord

logger = logging.getLogger(__name__)

NREL_API_KEY  = os.environ.get("NREL_API_KEY", "DEMO_KEY")
NREL_BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"
CACHE_TTL_SEC = int(os.environ.get("NREL_CACHE_TTL_SEC", 900))


class NRELClient:
    def __init__(self):
        self._cache: dict = {}
        self._lock  = asyncio.Lock()

    async def get_nearby_stations(
        self,
        lat:         float,
        lon:         float,
        radius_km:   float = 10.0,
        max_results: int   = 20,
    ) -> list:
        cache_key = self._cache_key(lat, lon, radius_km)
        async with self._lock:
            cached = self._cache.get(cache_key)
            if cached and time.time() < cached[1]:
                return cached[0]

        stations = await self._fetch(lat, lon, radius_km, max_results)
        async with self._lock:
            self._cache[cache_key] = (stations, time.time() + CACHE_TTL_SEC)
        return stations

    async def _fetch(
        self, lat: float, lon: float, radius_km: float, max_results: int
    ) -> list:
        params = {
            "api_key":   NREL_API_KEY,
            "fuel_type": "ELEC",
            "latitude":  lat,
            "longitude": lon,
            "radius":    round(radius_km * 0.621371, 2),
            "limit":     max_results,
            "status":    "E",
            "access":    "public",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(NREL_BASE_URL, params=params)
            resp.raise_for_status()
            return [self._normalise(s) for s in resp.json().get("fuel_stations", [])]
        except Exception as e:
            logger.warning("NREL API fetch failed: %s", e)
            return []

    @staticmethod
    def _normalise(raw: dict) -> MobilityRecord:
        ev_l2  = raw.get("ev_level2_evse_num") or 0
        ev_dc  = raw.get("ev_dc_fast_num") or 0
        total  = ev_l2 + ev_dc
        city   = raw.get("city", "")
        state  = raw.get("state", "")
        return MobilityRecord(
            id=             f"NREL-{raw.get('id', 'X')}",
            name=           raw.get("station_name", "EV Station"),
            type=           "charger",
            subtypes=       ["ev_charger"],
            lat=            float(raw.get("latitude", 0)),
            lon=            float(raw.get("longitude", 0)),
            address=        f"{raw.get('street_address', '')}, {city}, {state}".strip(", "),
            city=           city or None,
            country=        None,
            operator=       raw.get("ev_network") or "Unknown",
            connector_types=[],
            power_kw=       50 if ev_dc > 0 else 7,
            total_ports=    max(total, 1),
            available_ports=None,
            status=         None,
            price_info=     None,
            accessibility=  None,
            data_source=    "nrel_afdc",
            data_quality=   "estimated",
            fallback_reason="NREL does not provide real-time status",
            last_updated=   None,
        )

    @staticmethod
    def _cache_key(lat: float, lon: float, radius_km: float) -> str:
        return hashlib.md5(
            f"{lat:.3f}:{lon:.3f}:{radius_km:.1f}".encode()
        ).hexdigest()