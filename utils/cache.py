"""
utils/cache.py  —  Lightweight TTL in-memory cache.

Design
------
Thread-safe for asyncio usage (single-threaded event loop).
Keys are strings; values are any serializable object.
Separate TTL per cache instance.

Usage
-----
from utils.cache import TTLCache
_geo_cache = TTLCache(ttl_seconds=86400)

result = _geo_cache.get("pune_india")
if result is None:
    result = await fetch_geocode("Pune, India")
    _geo_cache.set("pune_india", result)
"""

import hashlib
import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Simple TTL in-memory cache.
    Not suitable for multi-process / multi-instance deployments
    (use BigQuery or Redis for cross-instance persistence).

    Cost note: free always; replaced by Redis/Memorystore at scale.
    """

    def __init__(self, ttl_seconds: int = 3600, name: str = "cache"):
        self._store:   dict[str, tuple[Any, float]] = {}
        self._ttl:     int  = ttl_seconds
        self._name:    str  = name
        self._hits:    int  = 0
        self._misses:  int  = 0

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            self._misses += 1
            logger.debug("[%s] cache expired: %s", self._name, key[:60])
            return None
        self._hits += 1
        logger.debug("[%s] cache hit: %s", self._name, key[:60])
        return value

    def set(self, key: str, value: Any, ttl_override: Optional[int] = None) -> None:
        ttl  = ttl_override if ttl_override is not None else self._ttl
        self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> dict:
        expired = sum(
            1 for _, (_, exp) in self._store.items()
            if time.time() > exp
        )
        return {
            "name":    self._name,
            "size":    len(self._store),
            "expired": expired,
            "hits":    self._hits,
            "misses":  self._misses,
            "hit_rate": round(self._hits / max(self._hits + self._misses, 1), 3),
        }

    @staticmethod
    def make_key(*parts: str) -> str:
        """Create a normalized, safe cache key from arbitrary string parts."""
        raw = "|".join(str(p).lower().strip() for p in parts)
        return hashlib.md5(raw.encode()).hexdigest()


# ── Module-level shared caches ────────────────────────────────────────────────
# Import these directly in other modules for consistent TTL per category.

from config import cfg as _cfg

geo_cache      = TTLCache(ttl_seconds=_cfg.cache.geo_ttl_seconds,      name="geo")
provider_cache = TTLCache(ttl_seconds=_cfg.cache.provider_ttl_seconds, name="provider")
advisor_cache  = TTLCache(ttl_seconds=_cfg.cache.advisor_ttl_seconds,  name="advisor")
