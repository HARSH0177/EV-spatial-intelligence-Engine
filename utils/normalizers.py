"""
utils/normalizers.py  —  Normalize provider payloads into shared schemas.

Two target schemas:
  1. MobilityRecord  — charger / parking / mobility_hub
  2. ZoneRecord      — planning zone with scores

All fields use snake_case. data_quality is always explicit.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import List, Optional
from datetime import datetime, timezone


# ── Mobility record schema ────────────────────────────────────────────────────

@dataclass
class MobilityRecord:
    """
    Normalized record for a charger, parking lot, or mobility hub.
    Every field not known from the source is None — never fabricated.
    """
    id:              str
    name:            str
    type:            str                    # charger | parking | mobility_hub
    subtypes:        List[str]
    lat:             float
    lon:             float
    address:         Optional[str]
    city:            Optional[str]
    country:         Optional[str]
    operator:        Optional[str]
    connector_types: List[str]
    power_kw:        Optional[float]
    total_ports:     Optional[int]
    available_ports: Optional[int]
    status:          Optional[str]
    price_info:      Optional[str]
    accessibility:   Optional[str]
    data_source:     str
    data_quality:    str                    # live | estimated | fallback | mock-dev
    fallback_reason: Optional[str]
    last_updated:    Optional[str]
    distance_km:     Optional[float] = None # set after geo filter

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def unknown_quality(reason: str) -> str:
        return f"fallback:{reason}"


# ── Zone record schema ────────────────────────────────────────────────────────

@dataclass
class ZoneRecord:
    """
    Normalized planning zone recommendation.
    Scores are float 0–1. confidence_score reflects data completeness.
    real_inputs / modeled_inputs document what was real vs inferred.
    """
    zone_id:                  str
    zone_name:                str
    city:                     str
    country:                  str
    lat:                      float
    lon:                      float
    demand_score:             float
    competition_score:        float
    accessibility_score:      float
    parking_support_score:    float
    grid_score:               float
    roi_score:                float
    viability_score:          float
    confidence_score:         float
    recommended_station_type: str
    recommended_port_count:   int
    recommended_connector_mix: List[str]
    explanation:              str
    real_inputs:              dict
    modeled_inputs:           dict

    def to_dict(self) -> dict:
        return asdict(self)


# ── Geo result schema ─────────────────────────────────────────────────────────

@dataclass
class GeoResult:
    city:         str
    display_name: str
    country:      str
    country_code: str
    lat:          float
    lon:          float
    bbox:         dict           # {south, north, west, east}
    neighborhoods: List[dict]   # [{name, lat, lon, osm_type, osm_id}]
    source:       str
    fetched_at:   str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


# ── Normalization helpers ─────────────────────────────────────────────────────

def normalize_connector(raw: str) -> str:
    """Normalize connector type strings to canonical names."""
    raw = (raw or "").strip().upper()
    _MAP = {
        "TYPE1": "J1772", "SAE J1772": "J1772",
        "TYPE2": "Type2",  "IEC 62196": "Type2",
        "CCS1":  "CCS",    "CCS2": "CCS", "COMBO": "CCS",
        "CHADEMO": "CHAdeMO",
        "TESLA": "Tesla",  "NACS": "Tesla",
        "GB/T": "GB/T",
        "SCHUKO": "Schuko",
    }
    return _MAP.get(raw, raw) or "Unknown"


def normalize_status(raw: str) -> str:
    raw = (raw or "").lower()
    if any(k in raw for k in ("available", "operational", "free")):
        return "Available"
    if any(k in raw for k in ("charging", "occupied", "busy", "inuse")):
        return "Charging"
    if any(k in raw for k in ("offline", "unknown", "unresolved")):
        return "Offline"
    if any(k in raw for k in ("planned", "coming")):
        return "Planned"
    return "Unknown"


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
