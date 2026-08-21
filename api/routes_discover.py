"""
api/routes_discover.py  —  Unified discover endpoints.

v2.2.1 fixes
------------
BUG 1 FIXED: asyncio.coroutine removed in Python 3.11.
  All `asyncio.coroutine(lambda: [])()` replaced with `_empty_list()`.
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.schemas import (
    DiscoverRequest, ChargerSearchRequest,
    ParkingSearchRequest, MobilitySearchRequest,
)
from utils.geo_enricher     import geo_enricher
from utils.provider_merge   import merge_and_dedupe, summarize_quality, provider_names
from utils.observability    import timed, inc, new_request_id
from realtime.openchargemap_client import ocm_client
from realtime.osm_places_client    import osm_client
from realtime.google_places_client import google_places_client
from config import cfg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["Discover"])


# ── BUG 1 FIX: proper async empty-list coroutine ─────────────────────────────
async def _empty_list() -> list:
    """Replaces asyncio.coroutine(lambda: [])() which is removed in Python 3.11."""
    return []


# ── Shared discovery helper ───────────────────────────────────────────────────

async def _run_discovery(
    lat:            float,
    lon:            float,
    radius_km:      float,
    want_chargers:  bool           = True,
    want_parking:   bool           = False,
    want_mobility:  bool           = False,
    connector_type: Optional[str]   = None,
    min_power_kw:   Optional[float] = None,
    max_results:    int             = 50,
) -> dict:
    """Run all enabled provider fetches in parallel and merge results."""

    # Build coroutine list — _empty_list() for disabled paths (BUG 1 FIX)
    tasks = [
        ocm_client.get_nearby(lat, lon, radius_km, max_results,
                              connector_type, min_power_kw)
        if want_chargers else _empty_list(),

        google_places_client.get_ev_chargers(
            lat, lon, int(radius_km * 1000), max_results
        )
        if want_chargers else _empty_list(),

        osm_client.get_parking_lots(lat, lon, int(radius_km * 1000), max_results)
        if want_parking else _empty_list(),

        osm_client.get_mobility_hubs(lat, lon, int(radius_km * 1000), max_results)
        if want_mobility else _empty_list(),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    ocm_results      = results[0] if not isinstance(results[0], Exception) else []
    gp_results       = results[1] if not isinstance(results[1], Exception) else []
    parking_results  = results[2] if not isinstance(results[2], Exception) else []
    mobility_results = results[3] if not isinstance(results[3], Exception) else []

    merged = merge_and_dedupe(
        ocm_results, gp_results, parking_results, mobility_results,
        user_lat=lat, user_lon=lon,
        max_results=max_results,
    )

    return {
        "results":              [r.to_dict() for r in merged],
        "total_found":          len(merged),
        "providers_used":       provider_names(merged),
        "data_quality_summary": summarize_quality(merged),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/discover")
async def discover(req: DiscoverRequest):
    """
    Combined discover endpoint.
    Returns chargers, parking, and/or mobility hubs based on `type` filter.
    Accepts location name (geocoded) or raw lat/lon.
    """
    req_id = new_request_id()
    inc("api.discover.called")

    async with timed("api.discover", logger, extra={"req_id": req_id}):
        try:
            lat, lon, radius_km = await _resolve_location(req)
            want_all      = (req.type or "all") == "all"
            want_chargers = want_all or req.type == "charger"
            want_parking  = want_all or req.type == "parking"
            want_mobility = want_all or req.type == "mobility_hub"

            payload = await _run_discovery(
                lat=lat, lon=lon, radius_km=radius_km,
                want_chargers=want_chargers,
                want_parking=want_parking,
                want_mobility=want_mobility,
                connector_type=req.connector_type,
                min_power_kw=req.min_power_kw,
                max_results=req.max_results or 50,
            )
            inc("api.discover.ok")
            return {
                "request_id":    req_id,
                "user_location": {"lat": lat, "lon": lon},
                "radius_km":     radius_km,
                **payload,
            }
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            inc("api.discover.error")
            logger.exception("Discover failed")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/chargers")
async def search_chargers(req: ChargerSearchRequest):
    """Search for EV chargers only — globally, any city."""
    req_id = new_request_id()
    inc("api.chargers.called")
    try:
        lat, lon, radius_km = await _resolve_location(req)
        payload = await _run_discovery(
            lat=lat, lon=lon, radius_km=radius_km,
            want_chargers=True, want_parking=False, want_mobility=False,
            connector_type=req.connector_type,
            min_power_kw=req.min_power_kw,
            max_results=req.max_results or 50,
        )
        inc("api.chargers.ok")
        return {
            "request_id":    req_id,
            "user_location": {"lat": lat, "lon": lon},
            **payload,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        inc("api.chargers.error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parking")
async def search_parking(req: ParkingSearchRequest):
    """Search for parking lots only."""
    req_id = new_request_id()
    inc("api.parking.called")
    try:
        lat, lon, radius_km = await _resolve_location(req)
        payload = await _run_discovery(
            lat=lat, lon=lon, radius_km=radius_km,
            want_chargers=False, want_parking=True, want_mobility=False,
            max_results=req.max_results or 30,
        )
        inc("api.parking.ok")
        return {
            "request_id":    req_id,
            "user_location": {"lat": lat, "lon": lon},
            **payload,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        inc("api.parking.error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mobility")
async def search_mobility(req: MobilitySearchRequest):
    """Search for mobility hubs only."""
    req_id = new_request_id()
    inc("api.mobility.called")
    try:
        lat, lon, radius_km = await _resolve_location(req)
        payload = await _run_discovery(
            lat=lat, lon=lon, radius_km=radius_km,
            want_chargers=False, want_parking=False, want_mobility=True,
            max_results=req.max_results or 20,
        )
        inc("api.mobility.ok")
        return {
            "request_id":    req_id,
            "user_location": {"lat": lat, "lon": lon},
            **payload,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        inc("api.mobility.error")
        raise HTTPException(status_code=500, detail=str(e))


# ── Location resolver ─────────────────────────────────────────────────────────

async def _resolve_location(req) -> tuple:
    """Resolve location from request — geocode name or use coords directly."""
    radius_km = req.max_distance_km or cfg.search.default_radius_km
    if req.latitude is not None and req.longitude is not None:
        return req.latitude, req.longitude, radius_km
    geo = await geo_enricher.enrich(req.location)
    return geo.lat, geo.lon, radius_km