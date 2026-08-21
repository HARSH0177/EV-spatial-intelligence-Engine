"""
realtime/google_places_client.py  —  Optional Google Places enrichment.

Only active when ENABLE_GOOGLE_PLACES=true AND GOOGLE_MAPS_API_KEY is set.
Used for EV station search enrichment where OCM coverage is sparse.

Cost: free tier 10k requests/month; may cost at scale.
"""

import logging
from typing import Optional

import httpx

from config import cfg
from utils.cache import provider_cache, TTLCache
from utils.normalizers import MobilityRecord, normalize_status

logger = logging.getLogger(__name__)

_PLACES_URL  = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
_USER_AGENT  = "EV-Advisor/2.2"


class GooglePlacesClient:
    """
    Optional Google Places client for EV charging enrichment.
    Returns [] immediately if not configured.
    """

    async def get_ev_chargers(
        self,
        lat:         float,
        lon:         float,
        radius_m:    int        = 5000,
        max_results: int        = 20,
    ) -> list[MobilityRecord]:
        if not cfg.providers.google_places_active:
            return []

        cache_key = TTLCache.make_key("gplaces", str(lat), str(lon), str(radius_m))
        cached    = provider_cache.get(cache_key)
        if cached is not None:
            return cached

        raw     = await self._fetch(lat, lon, radius_m)
        records = [self._normalise(r) for r in raw[:max_results]]
        provider_cache.set(cache_key, records)
        logger.info("Google Places: %d EV results near (%.4f, %.4f)", len(records), lat, lon)
        return records

    async def _fetch(self, lat: float, lon: float, radius_m: int) -> list:
        params = {
            "location": f"{lat},{lon}",
            "radius":   radius_m,
            "type":     "electric_vehicle_charging_station",
            "key":      cfg.providers.google_maps_key,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(_PLACES_URL, params=params,
                                        headers={"User-Agent": _USER_AGENT})
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            logger.warning("Google Places fetch failed: %s", e)
            return []

    @staticmethod
    def _normalise(raw: dict) -> MobilityRecord:
        geo      = raw.get("geometry", {}).get("location", {})
        opening  = raw.get("opening_hours", {})
        is_open  = opening.get("open_now")

        status   = "Available" if is_open else ("Offline" if is_open is False else "Unknown")
        dq       = "estimated"

        return MobilityRecord(
            id=             f"GP-{raw.get('place_id', 'X')}",
            name=           raw.get("name", "EV Station"),
            type=           "charger",
            subtypes=       ["ev_charger"],
            lat=            float(geo.get("lat", 0)),
            lon=            float(geo.get("lng", 0)),
            address=        raw.get("vicinity") or None,
            city=           None,
            country=        None,
            operator=       None,
            connector_types=[],
            power_kw=       None,
            total_ports=    None,
            available_ports=None,
            status=         status,
            price_info=     None,
            accessibility=  None,
            data_source=    "google_places",
            data_quality=   dq,
            fallback_reason="Google Places does not provide live port-level data",
            last_updated=   None,
        )


# Module-level singleton
google_places_client = GooglePlacesClient()
