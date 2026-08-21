"""
utils/geo_enricher.py  —  Global city/area geocoding and enrichment.

Sources
-------
1. Nominatim / OSM — text-to-location lookup, any city worldwide (free)
2. Overpass / OSM  — neighborhood / district extraction (free)

Caching
-------
Results cached in geo_cache (default TTL 24h) keyed by normalized query.
Same city queried twice never hits the network.

Returns
-------
GeoResult with: city, display_name, country, lat, lon, bbox,
                neighborhoods[], source, fetched_at

Interview talking point
-----------------------
"GeoEnricher abstracts the geocoding layer so all agents use one consistent
place object.  It's globally usable — 'Pune', 'Berlin', 'Nairobi', 'Tokyo'
all resolve correctly.  Neighborhood discovery uses the Overpass admin
boundary query, which returns real district shapes from OSM for any city."
"""

import asyncio
import logging
from typing import Optional

import httpx

from config import cfg
from utils.cache import geo_cache, TTLCache
from utils.normalizers import GeoResult

logger = logging.getLogger(__name__)

_USER_AGENT = "EV-Advisor-GeoEnricher/2.2 (github.com/ev-advisor)"


class GeoEnricher:
    """
    Resolve any city/area string to a normalized GeoResult.
    Singleton-safe: stateless methods, shared cache.
    """

    # ── Public API ────────────────────────────────────────────────────────────

    async def enrich(self, query: str) -> GeoResult:
        """
        Resolve a location query to a full GeoResult.
        Checks cache first; fetches from Nominatim + Overpass on miss.

        Parameters
        ----------
        query : any human-readable location string, e.g.
                "Pune", "Berlin, Germany", "Castro District, San Francisco"

        Raises
        ------
        ValueError if geocoding completely fails
        """
        cache_key = TTLCache.make_key(query)
        cached    = geo_cache.get(cache_key)
        if cached:
            return cached

        result = await self._resolve(query)
        geo_cache.set(cache_key, result)
        return result

    async def enrich_bbox(self, query: str) -> dict:
        """Return just the bbox dict for a query."""
        result = await self.enrich(query)
        return result.bbox

    # ── Internal geocoding ────────────────────────────────────────────────────

    async def _resolve(self, query: str) -> GeoResult:
        nominatim_url = cfg.providers.nominatim_url

        params = {
            "q":              query,
            "format":         "json",
            "limit":          1,
            "addressdetails": 1,
            "extratags":      1,
            "namedetails":    1,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{nominatim_url}/search",
                    params=params,
                    headers={"User-Agent": _USER_AGENT},
                )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("Nominatim geocoding failed for '%s': %s", query, e)
            raise ValueError(f"Could not geocode '{query}': {e}") from e

        if not data:
            raise ValueError(f"Nominatim returned no results for '{query}'")

        hit      = data[0]
        lat      = float(hit["lat"])
        lon      = float(hit["lon"])
        addr     = hit.get("address", {})
        country  = addr.get("country", "")
        cc       = addr.get("country_code", "").upper()
        city_raw = (
            addr.get("city") or addr.get("town") or addr.get("village")
            or addr.get("county") or addr.get("state") or query
        )
        bb       = hit.get("boundingbox", [])
        bbox     = {
            "south": float(bb[0]) if len(bb) >= 4 else lat - 0.05,
            "north": float(bb[1]) if len(bb) >= 4 else lat + 0.05,
            "west":  float(bb[2]) if len(bb) >= 4 else lon - 0.05,
            "east":  float(bb[3]) if len(bb) >= 4 else lon + 0.05,
        }

        # Fetch neighborhoods from Overpass (best-effort)
        neighborhoods = []
        if cfg.providers.enable_osm:
            try:
                neighborhoods = await self._fetch_neighborhoods(lat, lon, bbox)
            except Exception as e:
                logger.debug("Neighborhood fetch failed for %s: %s", query, e)

        result = GeoResult(
            city=city_raw,
            display_name=hit.get("display_name", query),
            country=country,
            country_code=cc,
            lat=lat,
            lon=lon,
            bbox=bbox,
            neighborhoods=neighborhoods,
            source="nominatim_osm",
            fetched_at=GeoResult.now_iso(),
        )
        logger.info(
            "Geocoded '%s' → %s, %s (%.4f, %.4f) %d neighborhoods",
            query, city_raw, country, lat, lon, len(neighborhoods),
        )
        return result

    async def _fetch_neighborhoods(
        self, lat: float, lon: float, bbox: dict
    ) -> list:
        """
        Use Overpass to fetch neighborhood / district boundaries near lat/lon.
        Returns list of {name, lat, lon, osm_type, osm_id}.
        """
        overpass_url = cfg.providers.overpass_url
        # Query admin boundaries level 8-10 (neighborhoods/districts) within bbox
        south, north = bbox["south"], bbox["north"]
        west,  east  = bbox["west"],  bbox["east"]
        query = f"""
[out:json][timeout:15];
(
  node["place"~"neighbourhood|suburb|district|quarter"]
     ({south},{west},{north},{east});
  way["place"~"neighbourhood|suburb|district|quarter"]
     ({south},{west},{north},{east});
);
out center 30;
"""
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                overpass_url,
                data={"data": query},
                headers={"User-Agent": _USER_AGENT},
            )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])

        result = []
        for el in elements[:20]:   # cap at 20 neighborhoods
            name = el.get("tags", {}).get("name") or el.get("tags", {}).get("name:en")
            if not name:
                continue
            center = el.get("center", {})
            elat   = center.get("lat") or el.get("lat")
            elon   = center.get("lon") or el.get("lon")
            if elat is None or elon is None:
                continue
            result.append({
                "name":     name,
                "lat":      float(elat),
                "lon":      float(elon),
                "osm_type": el.get("type", "node"),
                "osm_id":   el.get("id"),
            })

        return result


# Module-level singleton
geo_enricher = GeoEnricher()
