"""
api/schemas.py  —  Pydantic request/response models for all API routes.

Shared by routes_discover.py, routes_advisor.py, and main.py.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, model_validator


# ── Shared request base ───────────────────────────────────────────────────────

class LocationRequest(BaseModel):
    """
    Accepts either a human-readable location string OR raw coordinates.
    Both resolve to the same geo context.
    """
    location:        Optional[str]   = None
    latitude:        Optional[float] = None
    longitude:       Optional[float] = None
    max_distance_km: Optional[float] = None   # None → uses DEFAULT_SEARCH_RADIUS_KM

    @model_validator(mode="after")
    def check_location_or_coords(self) -> "LocationRequest":
        has_coords   = self.latitude is not None and self.longitude is not None
        has_location = bool(self.location and self.location.strip())
        if not has_coords and not has_location:
            raise ValueError(
                "Provide either 'location' (e.g. 'Pune, India') "
                "or both 'latitude' and 'longitude'."
            )
        return self


# ── Discover requests ─────────────────────────────────────────────────────────

class DiscoverRequest(LocationRequest):
    """
    Unified discover request.
    type filter: charger | parking | mobility_hub | all
    """
    type:            Optional[str]   = "all"   # charger | parking | mobility_hub | all
    connector_type:  Optional[str]   = None
    min_power_kw:    Optional[float] = None
    operator:        Optional[str]   = None
    open_now:        Optional[bool]  = None
    max_results:     Optional[int]   = 50


class ChargerSearchRequest(LocationRequest):
    connector_type:  Optional[str]   = None
    min_power_kw:    Optional[float] = None
    operator:        Optional[str]   = None
    max_results:     Optional[int]   = 50


class ParkingSearchRequest(LocationRequest):
    max_results:     Optional[int]   = 30


class MobilitySearchRequest(LocationRequest):
    max_results:     Optional[int]   = 20


# ── Advisor requests ──────────────────────────────────────────────────────────

class AnalyzeAreaRequest(BaseModel):
    """
    Plan flow: analyze a city/area for station setup.
    """
    location:  str
    top_n:     Optional[int]   = 5
    budget:    Optional[float] = None


class RankZonesRequest(BaseModel):
    location:  str
    top_n:     Optional[int]   = 10


class ExplainRequest(BaseModel):
    zone_id:   str
    location:  str


# ── Shared response components ────────────────────────────────────────────────

class DataQualitySummary(BaseModel):
    levels_present:  List[str]
    explanations:    dict
    total_results:   int


class GeoContext(BaseModel):
    city:         str
    display_name: str
    country:      str
    lat:          float
    lon:          float
    source:       str
