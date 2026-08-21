"""
realtime/openchargemap_client.py  —  Open Charge Map (OCM) client.

Open Charge Map is the primary global EV charger inventory.
No API key required for basic access; key increases rate limits.

API docs: https://openchargemap.org/site/develop/api

Cost: free (key-less rate-limited); production should use an API key.
"""

import hashlib
import logging
from typing import Optional

import httpx

from config import cfg
from utils.cache import provider_cache, TTLCache
from utils.normalizers import MobilityRecord, normalize_connector, normalize_status

logger = logging.getLogger(__name__)

_OCM_BASE = cfg.providers.ocm_base_url
_USER_AGENT = "EV-Advisor/2.2"


class OpenChargeMapClient:
    """
    Fetches EV charger data from Open Charge Map.
    Returns normalized MobilityRecord list.
    """

    async def get_nearby(
        self,
        lat:             float,
        lon:             float,
        radius_km:       float      = 10.0,
        max_results:     int        = 50,
        connector_type:  Optional[str]   = None,
        min_power_kw:    Optional[float] = None,
    ) -> list[MobilityRecord]:
        if not cfg.providers.ocm_active:
            logger.debug("OCM disabled via config")
            return []

        cache_key = TTLCache.make_key("ocm", str(lat), str(lon), str(radius_km), str(connector_type), str(min_power_kw))
        cached    = provider_cache.get(cache_key)
        if cached is not None:
            return cached

        raw     = await self._fetch(lat, lon, radius_km, max_results)
        records = [self._normalise(r) for r in raw]

        # Apply filters
        if connector_type:
            ct = connector_type.upper()
            records = [
                r for r in records
                if not r.connector_types or any(ct in c.upper() for c in r.connector_types)
            ]
        if min_power_kw:
            records = [r for r in records if r.power_kw is None or r.power_kw >= min_power_kw]

        provider_cache.set(cache_key, records)
        logger.info("OCM: %d chargers for (%.4f, %.4f) r=%.1fkm", len(records), lat, lon, radius_km)
        return records

    async def _fetch(self, lat: float, lon: float, radius_km: float, max_results: int) -> list:
        params = {
            "output":          "json",
            "latitude":        lat,
            "longitude":       lon,
            "distance":        radius_km,
            "distanceunit":    "KM",
            "maxresults":      max_results,
            "compact":         True,
            "verbose":         False,
            "includecomments": False,
        }
        if cfg.providers.ocm_api_key:
            params["key"] = cfg.providers.ocm_api_key

        try:
            async with httpx.AsyncClient(timeout=12) as client:
                resp = await client.get(
                    f"{_OCM_BASE}/poi/",
                    params=params,
                    headers={"User-Agent": _USER_AGENT},
                )
            resp.raise_for_status()
            return resp.json() or []
        except Exception as e:
            logger.warning("OCM fetch failed: %s", e)
            return []

    @staticmethod
    def _normalise(raw: dict) -> MobilityRecord:
        addr_info    = raw.get("AddressInfo", {}) or {}
        conns        = raw.get("Connections", []) or []
        status_type  = raw.get("StatusType", {}) or {}

        # Connector types
        connector_types = []
        max_kw          = None
        total_ports     = 0
        for c in conns:
            ct = c.get("ConnectionType", {}) or {}
            title = ct.get("Title", "") or ""
            if title:
                connector_types.append(normalize_connector(title))
            kw_raw = c.get("PowerKW")
            if kw_raw:
                try:
                    kw = float(kw_raw)
                    max_kw = max(max_kw or 0, kw)
                except (ValueError, TypeError):
                    pass
            qty = c.get("Quantity") or 1
            try:
                total_ports += int(qty)
            except (ValueError, TypeError):
                total_ports += 1

        connector_types = list(dict.fromkeys(connector_types))  # dedupe

        # Address
        street  = addr_info.get("AddressLine1") or ""
        city    = addr_info.get("Town") or addr_info.get("City") or ""
        country = addr_info.get("Country", {}).get("Title", "") if isinstance(addr_info.get("Country"), dict) else ""
        address = ", ".join(p for p in [street, city] if p) or None

        # Operator
        op = raw.get("OperatorInfo", {}) or {}
        operator = op.get("Title") or None

        # Status
        status_title = status_type.get("Title", "") or ""
        status = normalize_status(status_title)

        # Data quality
        is_live = status_type.get("IsOperational") is True
        dq      = "estimated" if not is_live else "live"
        if not status_title:
            dq = "fallback"

        return MobilityRecord(
            id=             f"OCM-{raw.get('ID', 'X')}",
            name=           addr_info.get("Title") or "EV Charger",
            type=           "charger",
            subtypes=       ["ev_charger"],
            lat=            float(addr_info.get("Latitude", 0)),
            lon=            float(addr_info.get("Longitude", 0)),
            address=        address,
            city=           city or None,
            country=        country or None,
            operator=       operator,
            connector_types=connector_types,
            power_kw=       round(max_kw, 1) if max_kw else None,
            total_ports=    total_ports or None,
            available_ports=None,   # OCM doesn't provide real-time port status
            status=         status,
            price_info=     raw.get("UsageCost") or None,
            accessibility=  None,
            data_source=    "openchargemap",
            data_quality=   dq,
            fallback_reason="OCM does not provide real-time port status" if dq != "live" else None,
            last_updated=   raw.get("DateLastStatusUpdate") or None,
        )


# Module-level singleton
ocm_client = OpenChargeMapClient()
