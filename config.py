"""
config.py  —  Single source of truth for all configurable values.

v2.2 additions
--------------
- ENABLE_OCM / OPENCHARGEMAP_API_KEY
- ENABLE_OSM_OVERPASS
- ENABLE_GOOGLE_PLACES
- CACHE_TTL_SECONDS
- DEFAULT_SEARCH_RADIUS_KM
- BIGQUERY_DATASET / BIGQUERY_LOCATION
- LOG_LEVEL
"""

import os
from dataclasses import dataclass, field
from typing import List

# ── Helpers ───────────────────────────────────────────────────────────────────

def _env_list(key: str, default: str = "") -> List[str]:
    return [v.strip() for v in os.environ.get(key, default).split(",") if v.strip()]

def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except ValueError:
        return default

def _env_bool(key: str, default: bool) -> bool:
    return os.environ.get(key, str(default)).lower() in ("1", "true", "yes")

def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default


# ── Provider config ───────────────────────────────────────────────────────────

@dataclass
class ProviderConfig:
    """
    External data provider feature flags and keys.
    All keys come from environment — never hardcoded.
    """
    # Open Charge Map — primary global EV charger registry
    enable_ocm:         bool  = field(default_factory=lambda: _env_bool("ENABLE_OCM", True))
    ocm_api_key:        str   = field(default_factory=lambda: os.environ.get("OPENCHARGEMAP_API_KEY", ""))
    ocm_base_url:       str   = "https://api.openchargemap.io/v3"

    # OSM / Overpass — parking lots, mobility hubs, districts, road proxies
    enable_osm:         bool  = field(default_factory=lambda: _env_bool("ENABLE_OSM_OVERPASS", True))
    overpass_url:       str   = field(default_factory=lambda: os.environ.get(
        "OVERPASS_URL", "https://overpass-api.de/api/interpreter"
    ))
    nominatim_url:      str   = field(default_factory=lambda: os.environ.get(
        "NOMINATIM_URL", "https://nominatim.openstreetmap.org"
    ))

    # Google Places — optional enrichment, used only if key is set
    enable_google_places: bool = field(default_factory=lambda: _env_bool("ENABLE_GOOGLE_PLACES", False))
    google_maps_key:      str  = field(default_factory=lambda: os.environ.get("GOOGLE_MAPS_API_KEY", ""))

    # NREL AFDC — kept for backward compat
    nrel_api_key:         str  = field(default_factory=lambda: os.environ.get("NREL_API_KEY", "DEMO_KEY"))

    @property
    def google_places_active(self) -> bool:
        return self.enable_google_places and bool(self.google_maps_key)

    @property
    def ocm_active(self) -> bool:
        return self.enable_ocm  # works without key (rate-limited)


# ── Cache config ──────────────────────────────────────────────────────────────

@dataclass
class CacheConfig:
    """In-memory TTL cache settings."""
    ttl_seconds:        int  = field(default_factory=lambda: _env_int("CACHE_TTL_SECONDS", 3600))
    geo_ttl_seconds:    int  = field(default_factory=lambda: _env_int("GEO_CACHE_TTL_SECONDS", 86400))  # 24h
    provider_ttl_seconds: int = field(default_factory=lambda: _env_int("PROVIDER_CACHE_TTL_SECONDS", 900))  # 15m
    advisor_ttl_seconds:  int = field(default_factory=lambda: _env_int("ADVISOR_CACHE_TTL_SECONDS", 3600))   # 1h


# ── Search defaults ───────────────────────────────────────────────────────────

@dataclass
class SearchConfig:
    default_radius_km:   float = field(default_factory=lambda: _env_float("DEFAULT_SEARCH_RADIUS_KM", 10.0))
    max_results:         int   = field(default_factory=lambda: _env_int("MAX_SEARCH_RESULTS", 50))
    max_zones_returned:  int   = field(default_factory=lambda: _env_int("MAX_ZONES_RETURNED", 10))


# ── Ranking weights ───────────────────────────────────────────────────────────

@dataclass
class RankingWeights:
    wait_time:     float = field(default_factory=lambda: _env_float("RANK_W_WAIT",  0.40))
    free_ports:    float = field(default_factory=lambda: _env_float("RANK_W_FREE",  0.25))
    distance:      float = field(default_factory=lambda: _env_float("RANK_W_DIST",  0.20))
    charger_speed: float = field(default_factory=lambda: _env_float("RANK_W_SPEED", 0.15))

    def validate(self) -> None:
        total = self.wait_time + self.free_ports + self.distance + self.charger_speed
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"RankingWeights must sum to 1.0, got {total:.3f}")


# ── Scoring weights ───────────────────────────────────────────────────────────

@dataclass
class ScoringWeights:
    ev_demand:       float = field(default_factory=lambda: _env_float("SCORE_W_EV",       0.25))
    traffic:         float = field(default_factory=lambda: _env_float("SCORE_W_TRAFFIC",  0.20))
    competition_gap: float = field(default_factory=lambda: _env_float("SCORE_W_COMP_GAP", 0.20))
    grid:            float = field(default_factory=lambda: _env_float("SCORE_W_GRID",     0.15))
    land_cost:       float = field(default_factory=lambda: _env_float("SCORE_W_LAND",     0.10))
    accessibility:   float = field(default_factory=lambda: _env_float("SCORE_W_ACCESS",   0.10))


# ── Auth config ───────────────────────────────────────────────────────────────

@dataclass
class AuthConfig:
    api_key_header: str       = "X-API-Key"
    api_keys:       List[str] = field(default_factory=lambda: _env_list("API_KEYS"))
    require_auth:   bool      = field(default_factory=lambda: _env_bool("REQUIRE_AUTH", False))
    public_paths:   List[str] = field(default_factory=lambda: [
        "/", "/health", "/ready", "/docs", "/openapi.json", "/redoc",
        "/api/search/discover", "/api/search/chargers",
        "/api/search/parking",  "/api/search/mobility",
        "/api/advisor/analyze-area", "/api/advisor/rank-zones",
        "/api/advisor/explain",
    ])


# ── Vertex AI config ──────────────────────────────────────────────────────────

@dataclass
class VertexConfig:
    project_id:  str  = field(default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
    location:    str  = field(default_factory=lambda: os.environ.get("VERTEX_LOCATION", "us-central1"))
    model:       str  = field(default_factory=lambda: os.environ.get("VERTEX_MODEL", "gemini-2.0-flash-001"))
    enabled:     bool = field(default_factory=lambda: _env_bool("LLM_ENABLED", True))
    max_tokens:  int  = 512
    temperature: float = 0.2


# ── BigQuery config ───────────────────────────────────────────────────────────

@dataclass
class BigQueryConfig:
    project_id:  str = field(default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
    dataset:     str = field(default_factory=lambda: os.environ.get("BIGQUERY_DATASET", "ev_advisor_core"))
    location:    str = field(default_factory=lambda: os.environ.get("BIGQUERY_LOCATION", "US"))
    # Legacy dataset name for backward compat
    legacy_dataset: str = "mcp_mobility"


# ── Main app config ───────────────────────────────────────────────────────────

@dataclass
class AppConfig:
    project_id:          str           = field(default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
    port:                int           = field(default_factory=lambda: int(os.environ.get("PORT", 8080)))
    log_level:           str           = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    cors_origins:        List[str]     = field(default_factory=lambda: _env_list("CORS_ORIGINS", "*"))
    bq_executor_workers: int           = field(default_factory=lambda: int(os.environ.get("BQ_EXECUTOR_WORKERS", "4")))
    ocpp_ws_url:         str           = field(default_factory=lambda: os.environ.get("OCPP_WS_URL", "ws://localhost:9000"))

    # Sub-configs
    auth:      AuthConfig     = field(default_factory=AuthConfig)
    vertex:    VertexConfig   = field(default_factory=VertexConfig)
    ranking:   RankingWeights = field(default_factory=RankingWeights)
    scoring:   ScoringWeights = field(default_factory=ScoringWeights)
    providers: ProviderConfig = field(default_factory=ProviderConfig)
    cache:     CacheConfig    = field(default_factory=CacheConfig)
    search:    SearchConfig   = field(default_factory=SearchConfig)
    bigquery:  BigQueryConfig = field(default_factory=BigQueryConfig)

    # Legacy convenience shortcuts
    @property
    def bq_dataset(self) -> str:
        return self.bigquery.dataset

    @property
    def google_maps_key(self) -> str:
        return self.providers.google_maps_key


# Module-level singleton
cfg = AppConfig()
