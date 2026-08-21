"""
api/main.py  —  FastAPI application entry point. v2.2

New in v2.2
-----------
- Registers /api/search/* and /api/advisor/* routers
- /driver/map-data returns GeoJSON for Leaflet frontend
- All existing routes preserved for backward compat
- Structured logging, auth middleware, /ready endpoint unchanged
"""

import logging
import os
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

from agents.orchestrator    import OrchestratorAgent
from api.routes_discover    import router as discover_router
from api.routes_advisor     import router as advisor_router
from config                 import cfg
from middleware.auth         import APIKeyMiddleware, require_operator
from utils.observability     import setup_logging, get_counts, timed, inc

setup_logging(logging.INFO)
logger = logging.getLogger("api.main")

app = FastAPI(
    title="Multi-Agent EV Mobility Advisor",
    description=(
        "v2.2 — Global live discovery + modeled decision intelligence.\n\n"
        "**Discover**: find EV chargers, parking lots, and mobility hubs anywhere in the world.\n"
        "**Plan**: analyze any city for station setup with ranked zones and explainable scores."
    ),
    version="2.2.0",
)

# ── Middleware ────────────────────────────────────────────────────────────────
allow_origins = cfg.cors_origins if cfg.cors_origins != ["*"] else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=allow_origins,
                   allow_methods=["GET", "POST"], allow_headers=["*"])
app.add_middleware(APIKeyMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(discover_router)
app.include_router(advisor_router)

# ── Legacy orchestrator ───────────────────────────────────────────────────────
orchestrator = OrchestratorAgent()

# Serve frontend static files
import pathlib
_frontend = pathlib.Path(__file__).parent.parent / "frontend"
if _frontend.exists():
    app.mount("/app", StaticFiles(directory=str(_frontend), html=True), name="frontend")


# ── Request models ────────────────────────────────────────────────────────────

class ExpansionRequest(BaseModel):
    city:       str
    budget_usd: Optional[float] = 5_000_000
    top_n:      Optional[int]   = 3


class DriverRequest(BaseModel):
    location:        Optional[str]   = None
    latitude:        Optional[float] = None
    longitude:       Optional[float] = None
    max_distance_km: Optional[float] = 10.0
    connector_type:  Optional[str]   = None
    min_power_kw:    Optional[float] = None
    battery_pct:     Optional[float] = None

    @model_validator(mode="after")
    def check_location_or_coords(self) -> "DriverRequest":
        has_coords   = self.latitude is not None and self.longitude is not None
        has_location = bool(self.location and self.location.strip())
        if not has_coords and not has_location:
            raise ValueError("Provide 'location' or both 'latitude' and 'longitude'.")
        return self


class TaskRequest(BaseModel):
    task_type: str
    payload:   dict


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "Multi-Agent EV Mobility Advisor",
        "version": "2.2.0",
        "status":  "running",
        "docs":    "/docs",
        "frontend": "/app",
        "discover_routes": [
            "POST /api/search/discover",
            "POST /api/search/chargers",
            "POST /api/search/parking",
            "POST /api/search/mobility",
        ],
        "advisor_routes": [
            "POST /api/advisor/analyze-area",
            "POST /api/advisor/rank-zones",
            "POST /api/advisor/explain",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.2.0"}


@app.get("/ready")
async def ready():
    from utils.cache import geo_cache, provider_cache, advisor_cache
    return {
        "status":  "ready",
        "metrics": get_counts(),
        "cache_stats": {
            "geo":      geo_cache.stats(),
            "provider": provider_cache.stats(),
            "advisor":  advisor_cache.stats(),
        },
        "config": {
            "bq_available":    orchestrator.data_agent._bq_ok(),
            "llm_enabled":     cfg.vertex.enabled,
            "ocm_active":      cfg.providers.ocm_active,
            "osm_active":      cfg.providers.enable_osm,
            "google_places":   cfg.providers.google_places_active,
            "auth_required":   cfg.auth.require_auth,
        },
    }


# ── Legacy B2B endpoint (preserved) ──────────────────────────────────────────

@app.post("/company/plan-expansion", dependencies=[Depends(require_operator)])
async def plan_expansion(req: ExpansionRequest):
    inc("api.expansion.called")
    async with timed("api.expansion", logger, extra={"city": req.city}):
        try:
            result = await orchestrator.handle_expansion_request(
                city=req.city, budget_usd=req.budget_usd, top_n=req.top_n,
            )
            inc("api.expansion.ok")
            return result
        except Exception as e:
            inc("api.expansion.error")
            logger.exception("Expansion failed")
            raise HTTPException(status_code=500, detail=str(e))


# ── Legacy driver endpoint (preserved) ───────────────────────────────────────

@app.post("/driver/locate-charger")
async def locate_charger(req: DriverRequest):
    inc("api.driver.called")
    async with timed("api.driver", logger):
        try:
            result = await orchestrator.handle_driver_request(
                lat=req.latitude, lon=req.longitude,
                max_km=req.max_distance_km,
                location_name=req.location,
                connector_type=req.connector_type,
                min_power_kw=req.min_power_kw,
                battery_pct=req.battery_pct,
            )
            inc("api.driver.ok")
            return result
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            inc("api.driver.error")
            logger.exception("Driver request failed")
            raise HTTPException(status_code=500, detail=str(e))


# ── Map data endpoint ─────────────────────────────────────────────────────────

@app.post("/driver/map-data")
async def map_data(req: DriverRequest):
    """GeoJSON endpoint for Leaflet frontend."""
    inc("api.map.called")
    try:
        result   = await orchestrator.handle_driver_request(
            lat=req.latitude, lon=req.longitude,
            max_km=req.max_distance_km, location_name=req.location,
            connector_type=req.connector_type, min_power_kw=req.min_power_kw,
        )
        chargers = (
            result.get("results", {}).get("available_chargers", [])
            + result.get("results", {}).get("busy_chargers", [])
        )
        features = []
        for c in chargers:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [c.get("lon", 0), c.get("lat", 0)]},
                "properties": {
                    "id": c.get("id"), "name": c.get("name"),
                    "address": c.get("address"), "network": c.get("network"),
                    "kw": c.get("kw"), "total_ports": c.get("total_ports"),
                    "free_ports": c.get("free_ports", 0),
                    "current_status": c.get("current_status"),
                    "wait_time_minutes": c.get("wait_time_minutes"),
                    "distance_km": c.get("distance_km"),
                    "connector_types": c.get("connector_types", []),
                    "data_quality": c.get("data_quality"),
                    "rank_score": c.get("rank_score"),
                },
            })
        return {"type": "FeatureCollection", "features": features,
                "user_location": result.get("user_location")}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        inc("api.map.error")
        raise HTTPException(status_code=500, detail=str(e))


# ── Generic agent runner ──────────────────────────────────────────────────────

@app.post("/agent/run")
async def run_agent_task(req: TaskRequest):
    try:
        return await orchestrator.run_task(req.task_type, req.payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)
