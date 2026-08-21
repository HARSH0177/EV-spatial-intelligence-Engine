"""
api/routes_advisor.py  —  Advisor (Plan) endpoints.

Routes
------
POST /api/advisor/analyze-area   — full zone analysis for a city
POST /api/advisor/rank-zones     — ranked zone list only
POST /api/advisor/explain        — explanation for a specific zone
"""

import logging

from fastapi import APIRouter, HTTPException

from api.schemas            import AnalyzeAreaRequest, RankZonesRequest, ExplainRequest
from agents.advisor_agent   import advisor_agent
from utils.observability    import timed, inc, new_request_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/advisor", tags=["Advisor"])


@router.post("/analyze-area")
async def analyze_area(req: AnalyzeAreaRequest):
    """
    Full planning analysis for a city/area.
    Returns geo context, ranked zones with scores, and explanations.
    Works for any city worldwide: Pune, Berlin, Nairobi, Tokyo, San Francisco.
    """
    req_id = new_request_id()
    inc("api.advisor.analyze.called")

    async with timed("api.advisor.analyze", logger, extra={"req_id": req_id, "location": req.location}):
        try:
            result = await advisor_agent.analyze_area(
                query=req.location,
                top_n=req.top_n or 5,
                budget=req.budget,
            )
            inc("api.advisor.analyze.ok")
            return {"request_id": req_id, **result}
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            inc("api.advisor.analyze.error")
            logger.exception("Advisor analyze failed")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/rank-zones")
async def rank_zones(req: RankZonesRequest):
    """
    Return ranked zones without full geo context.
    Lighter response for summary views.
    """
    req_id = new_request_id()
    inc("api.advisor.rank.called")

    try:
        zones = await advisor_agent.rank_zones(req.location, top_n=req.top_n or 10)
        inc("api.advisor.rank.ok")
        return {
            "request_id": req_id,
            "location":   req.location,
            "zones":      [z.to_dict() for z in zones],
            "zone_count": len(zones),
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        inc("api.advisor.rank.error")
        logger.exception("Advisor rank failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def explain_zone(req: ExplainRequest):
    """
    Return detailed explanation for a zone.
    Pulls from cached analysis if available.
    """
    req_id = new_request_id()
    inc("api.advisor.explain.called")

    try:
        result = await advisor_agent.analyze_area(req.location, top_n=10)
        zones  = result.get("zones", [])
        target = next((z for z in zones if z.get("zone_id") == req.zone_id), None)

        if not target:
            raise HTTPException(
                status_code=404,
                detail=f"Zone '{req.zone_id}' not found in analysis for '{req.location}'.",
            )

        inc("api.advisor.explain.ok")
        return {
            "request_id":    req_id,
            "zone_id":       req.zone_id,
            "zone_name":     target.get("zone_name"),
            "explanation":   target.get("explanation"),
            "real_inputs":   target.get("real_inputs", {}),
            "modeled_inputs": target.get("modeled_inputs", {}),
            "confidence_score": target.get("confidence_score"),
            "viability_score":  target.get("viability_score"),
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        inc("api.advisor.explain.error")
        logger.exception("Advisor explain failed")
        raise HTTPException(status_code=500, detail=str(e))
