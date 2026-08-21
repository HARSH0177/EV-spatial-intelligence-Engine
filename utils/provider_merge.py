"""
utils/provider_merge.py  —  Merge and deduplicate provider results.

Strategy
--------
1. Collect results from OCM, OSM, Google Places, NREL, OCPP
2. Deduplicate by proximity (200m threshold) — prefer higher-quality source
3. Sort by distance from user
4. Attach distance_km field

Source priority order (highest confidence first):
  ocpp_live > openchargemap > nrel_afdc > google_places > osm_overpass

Interview talking point
-----------------------
"We merge results from multiple providers using a spatial deduplication
strategy — two records within 200m of each other are considered the same
station. We keep the record from the higher-priority source so live OCPP
data always wins over a static OCM entry for the same physical station."
"""

import math
import logging
from typing import List, Optional

from utils.normalizers import MobilityRecord

logger = logging.getLogger(__name__)

# Source priority: lower index = higher priority kept in dedupe
_SOURCE_PRIORITY = [
    "ocpp_live",
    "openchargemap",
    "nrel_afdc",
    "google_places",
    "osm_overpass",
    "mock-dev",
]

_DEDUP_RADIUS_KM = 0.20   # 200m


def merge_and_dedupe(
    *record_lists: List[MobilityRecord],
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    max_results: int = 100,
) -> List[MobilityRecord]:
    """
    Merge multiple provider result lists, deduplicate by proximity,
    and attach distance_km if user coordinates are provided.

    Parameters
    ----------
    *record_lists : one or more lists of MobilityRecord
    user_lat, user_lon : user location for distance computation and sorting
    max_results : cap on returned records

    Returns
    -------
    Deduplicated, distance-sorted list of MobilityRecord.
    """
    all_records: List[MobilityRecord] = []
    for lst in record_lists:
        if lst:
            all_records.extend(lst)

    if not all_records:
        return []

    # Attach distance
    if user_lat is not None and user_lon is not None:
        for r in all_records:
            r.distance_km = round(_dist_km(user_lat, user_lon, r.lat, r.lon), 2)

    # Sort by source priority first, then distance
    def _sort_key(r: MobilityRecord):
        pri = _source_priority(r.data_source)
        dst = r.distance_km if r.distance_km is not None else 999
        return (pri, dst)

    all_records.sort(key=_sort_key)

    # Deduplicate
    kept: List[MobilityRecord] = []
    for record in all_records:
        is_dup = False
        for existing in kept:
            if existing.type != record.type:
                continue
            if _dist_km(record.lat, record.lon, existing.lat, existing.lon) < _DEDUP_RADIUS_KM:
                is_dup = True
                break
        if not is_dup:
            kept.append(record)

    # Final sort by distance
    if user_lat is not None and user_lon is not None:
        kept.sort(key=lambda r: r.distance_km if r.distance_km is not None else 999)

    result = kept[:max_results]
    logger.debug(
        "merge_and_dedupe: %d input → %d after dedup (cap %d)",
        len(all_records), len(kept), max_results,
    )
    return result


def summarize_quality(records: List[MobilityRecord]) -> dict:
    """Return data-quality distribution for observability."""
    counts: dict = {}
    for r in records:
        counts[r.data_quality] = counts.get(r.data_quality, 0) + 1
    return counts


def provider_names(records: List[MobilityRecord]) -> List[str]:
    """Return sorted unique provider names present in the record list."""
    return sorted({r.data_source for r in records})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _source_priority(source: str) -> int:
    try:
        return _SOURCE_PRIORITY.index(source)
    except ValueError:
        return len(_SOURCE_PRIORITY)


def _dist_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R    = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a    = (math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
