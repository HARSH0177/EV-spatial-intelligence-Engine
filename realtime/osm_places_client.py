"""
realtime/osm_places_client.py  —  OSM / Overpass API client.

Provides:
  - Parking lots near a coordinate (OSM amenity=parking)
  - Mobility hubs / bicycle share stations
  - Amenity density counts (used in business signals)
  - Road connectivity proxy (motorway/primary density)

Cost: free always (Overpass is public infrastructure).
Rate limit: be polite — use cache, avoid tight polling.
"""

import logging
from typing import Optional

import httpx

from config import cfg
from utils.cache import provider_cache, TTLCache
from utils.normalizers import MobilityRecord, normalize_status

logger = logging.getLogger(__name__)
_USER_AGENT = "EV-Advisor/2.2"


class OSMPlacesClient:
    """
    Queries Overpass API for parking lots, mobility hubs, and planning proxies.
    """

    @property
    def _url(self) -> str:
        return cfg.providers.overpass_url

    # ── Parking lots ──────────────────────────────────────────────────────────

    async def get_parking_lots(
        self,
        lat:         float,
        lon:         float,
        radius_m:    int = 5000,
        max_results: int = 30,
    ) -> list[MobilityRecord]:
        cache_key = TTLCache.make_key("osm_parking", str(lat), str(lon), str(radius_m))
        cached    = provider_cache.get(cache_key)
        if cached is not None:
            return cached

        query = f"""
[out:json][timeout:15];
(
  node["amenity"="parking"]({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
  way["amenity"="parking"]({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
  node["parking"~"surface|multi-storey|underground|covered"]
     ({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
);
out center {max_results};
"""
        elements = await self._query(query)
        records  = [self._norm_parking(e) for e in elements if self._has_coords(e)]
        provider_cache.set(cache_key, records)
        logger.info("OSM parking: %d lots near (%.4f, %.4f)", len(records), lat, lon)
        return records

    # ── Mobility hubs ─────────────────────────────────────────────────────────

    async def get_mobility_hubs(
        self,
        lat:         float,
        lon:         float,
        radius_m:    int = 5000,
        max_results: int = 20,
    ) -> list[MobilityRecord]:
        cache_key = TTLCache.make_key("osm_mobility", str(lat), str(lon), str(radius_m))
        cached    = provider_cache.get(cache_key)
        if cached is not None:
            return cached

        query = f"""
[out:json][timeout:15];
(
  node["amenity"="bicycle_rental"]({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
  node["amenity"="car_sharing"]({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
  node["public_transport"="station"]({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
  node["highway"="bus_stop"]({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
);
out center {max_results};
"""
        elements = await self._query(query)
        records  = [self._norm_mobility(e) for e in elements if self._has_coords(e)]
        provider_cache.set(cache_key, records)
        logger.info("OSM mobility: %d hubs near (%.4f, %.4f)", len(records), lat, lon)
        return records

    # ── Planning proxies ──────────────────────────────────────────────────────

    async def get_amenity_density(self, lat: float, lon: float) -> dict:
        """
        Return counts of key amenity types for business signal computation.
        Used by AdvisorAgent for parking_presence_proxy, transit_density_proxy, etc.
        """
        cache_key = TTLCache.make_key("osm_amenity_density", str(lat), str(lon))
        cached    = provider_cache.get(cache_key)
        if cached is not None:
            return cached

        query = f"""
[out:json][timeout:20];
(
  node["amenity"~"parking|fuel|charging_station|bicycle_rental|bus_station|subway_entrance"]
     ({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
  node["shop"~"supermarket|mall|department_store"]
     ({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
  node["office"~"commercial|company"]
     ({lat-0.05},{lon-0.05},{lat+0.05},{lon+0.05});
);
out count;
"""
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._url,
                    data={"data": query},
                    headers={"User-Agent": _USER_AGENT},
                )
            data = resp.json()
            count = int(data.get("elements", [{}])[0].get("tags", {}).get("total", 0))
        except Exception as e:
            logger.debug("OSM amenity density failed: %s", e)
            count = 0

        result = {
            "amenity_count": count,
            "source":        "osm_overpass",
            "data_quality":  "estimated" if count > 0 else "fallback",
        }
        provider_cache.set(cache_key, result)
        return result

    async def get_existing_chargers(self, lat: float, lon: float) -> list:
        """Return OSM-mapped charging stations for competition density."""
        cache_key = TTLCache.make_key("osm_chargers", str(lat), str(lon))
        cached    = provider_cache.get(cache_key)
        if cached is not None:
            return cached

        query = f"""
[out:json][timeout:15];
node["amenity"="charging_station"]
   ({lat-0.1},{lon-0.1},{lat+0.1},{lon+0.1});
out 50;
"""
        elements = await self._query(query)
        result   = [e for e in elements if e.get("lat") and e.get("lon")]
        provider_cache.set(cache_key, result)
        return result

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _query(self, query: str) -> list:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._url,
                    data={"data": query},
                    headers={"User-Agent": _USER_AGENT},
                )
            resp.raise_for_status()
            return resp.json().get("elements", [])
        except Exception as e:
            logger.warning("Overpass query failed: %s", e)
            return []

    @staticmethod
    def _has_coords(el: dict) -> bool:
        center = el.get("center", {})
        return bool(
            (el.get("lat") and el.get("lon"))
            or (center.get("lat") and center.get("lon"))
        )

    @staticmethod
    def _get_lat_lon(el: dict) -> tuple:
        center = el.get("center", {})
        lat = el.get("lat") or center.get("lat", 0)
        lon = el.get("lon") or center.get("lon", 0)
        return float(lat), float(lon)

    def _norm_parking(self, el: dict) -> MobilityRecord:
        lat, lon = self._get_lat_lon(el)
        tags     = el.get("tags", {}) or {}
        name     = tags.get("name") or tags.get("description") or "Parking Lot"
        capacity = tags.get("capacity")
        try:
            ports = int(capacity) if capacity else None
        except (ValueError, TypeError):
            ports = None

        return MobilityRecord(
            id=             f"OSM-PARK-{el.get('id', 'X')}",
            name=           name,
            type=           "parking",
            subtypes=       [tags.get("parking", "surface")],
            lat=            lat,
            lon=            lon,
            address=        tags.get("addr:street") or None,
            city=           tags.get("addr:city") or None,
            country=        None,
            operator=       tags.get("operator") or None,
            connector_types=[],
            power_kw=       None,
            total_ports=    ports,
            available_ports=None,
            status=         "Unknown",
            price_info=     tags.get("fee") or None,
            accessibility=  tags.get("access") or None,
            data_source=    "osm_overpass",
            data_quality=   "estimated",
            fallback_reason="OSM does not provide real-time occupancy",
            last_updated=   None,
        )

    def _norm_mobility(self, el: dict) -> MobilityRecord:
        lat, lon = self._get_lat_lon(el)
        tags     = el.get("tags", {}) or {}
        amenity  = tags.get("amenity", "") or tags.get("public_transport", "mobility")
        name     = tags.get("name") or amenity.replace("_", " ").title()
        capacity = tags.get("capacity")
        try:
            ports = int(capacity) if capacity else None
        except (ValueError, TypeError):
            ports = None

        return MobilityRecord(
            id=             f"OSM-MOB-{el.get('id', 'X')}",
            name=           name,
            type=           "mobility_hub",
            subtypes=       [amenity],
            lat=            lat,
            lon=            lon,
            address=        tags.get("addr:street") or None,
            city=           tags.get("addr:city") or None,
            country=        None,
            operator=       tags.get("operator") or None,
            connector_types=[],
            power_kw=       None,
            total_ports=    ports,
            available_ports=None,
            status=         "Unknown",
            price_info=     None,
            accessibility=  tags.get("access") or None,
            data_source=    "osm_overpass",
            data_quality=   "estimated",
            fallback_reason="OSM does not provide real-time occupancy",
            last_updated=   None,
        )


# Module-level singleton
osm_client = OSMPlacesClient()
