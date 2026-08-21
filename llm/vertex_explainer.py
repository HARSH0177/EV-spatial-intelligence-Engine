"""
llm/vertex_explainer.py  —  Improvement 14: Vertex AI Gemini explanations.

Auth
----
Uses Application Default Credentials (ADC) — NO API key required.
On Cloud Run: the runtime service account is used automatically.
Local dev:    run `gcloud auth application-default login` once.
Required IAM role on the service account: roles/aiplatform.user

The LLM explains deterministic results — it does NOT compute them.
All numerical inputs are passed as structured context.
Prompt constraints prevent hallucinated facts.

Cost note
---------
Gemini 2.0 Flash has a free quota tier on Vertex AI.
At scale (>1M tokens/month) charges apply.
Toggle off with LLM_ENABLED=false at zero cost.

Interview talking point
-----------------------
"We separate the LLM's role from the scoring pipeline.  The queue model,
demand forecaster, and scoring agent produce deterministic numbers.  Gemini
receives those numbers as structured context and produces a plain-English
justification.  This means the LLM cannot fabricate a score — it can only
narrate one that already exists."
"""

import asyncio
import logging
from typing import Optional

from config import cfg

logger = logging.getLogger(__name__)

_model = None   # lazy-initialised singleton


def _get_model():
    """
    Lazy-initialise the Vertex AI GenerativeModel using ADC.
    Returns None if Vertex AI is unavailable (missing library or disabled).
    """
    global _model
    if _model is not None:
        return _model

    if not cfg.vertex.enabled:
        logger.info("LLM disabled via LLM_ENABLED=false")
        return None

    if not cfg.vertex.project_id:
        logger.warning("GOOGLE_CLOUD_PROJECT not set — LLM unavailable")
        return None

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        # IAM auth: uses ADC automatically — no API key
        vertexai.init(
            project=cfg.vertex.project_id,
            location=cfg.vertex.location,
        )
        _model = GenerativeModel(cfg.vertex.model)
        logger.info(
            "Vertex AI initialised: project=%s location=%s model=%s",
            cfg.vertex.project_id, cfg.vertex.location, cfg.vertex.model,
        )
        return _model

    except ImportError:
        logger.warning("google-cloud-aiplatform[vertexai] not installed — LLM unavailable")
        return None
    except Exception as exc:
        logger.warning("Vertex AI init failed: %s — LLM unavailable", exc)
        return None


# ── Prompt templates ──────────────────────────────────────────────────────────

_DRIVER_PROMPT = """\
You are a concise EV charging assistant. Given the structured data below,
write 2-3 sentences explaining which charger is the best choice and why.

Rules:
- Only reference facts provided in the data. Do not add external information.
- Do not mention specific prices, battery chemistry, or grid specs.
- Be factual, plain-language, driver-friendly.
- If data_quality is "estimated", note the recommendation is based on a forecast.

Nearest available charger:
  Name:         {name}
  Distance:     {distance_km} km
  Free ports:   {free_ports} of {total_ports}
  Charger type: {charger_type} ({kw} kW)
  Network:      {network}
  Wait time:    {wait_min} min (p90: {wait_p90} min)
  Queue status: {queue_status}
  Data quality: {data_quality}
  Forecast src: {forecast_source}

Ranking score: {rank_score:.3f}
Score breakdown: wait={wait_w}, availability={avail_w}, distance={dist_w}, speed={speed_w}
"""

_OPERATOR_PROMPT = """\
You are a concise EV infrastructure advisor. Given the structured data below,
write 3-4 sentences justifying this ZIP code as a top expansion location.

Rules:
- Only reference facts in the data. Do not invent market conditions.
- Mention the key score drivers explicitly.
- Flag any risks visible in the data (e.g. high land cost, low grid capacity).
- Be professional and data-driven.

ZIP code: {zip_code}
City: {city}
EV Business Score: {score:.3f} ({tier})

Score breakdown:
  EV demand:        {ev_demand:.3f} (weight {w_ev})
  Traffic:          {traffic:.3f} (weight {w_traffic})
  Competition gap:  {competition_gap:.3f} (weight {w_comp})
  Grid capacity:    {grid:.3f} (weight {w_grid})
  Land cost score:  {land_cost:.3f} (weight {w_land})
  Accessibility:    {accessibility:.3f} (weight {w_access})

Key facts:
  EV registrations: {ev_reg}
  Daily traffic:    {daily_traffic:,}
  Competitors:      {competitors}
  Grid capacity:    {grid_kw} kW
"""


# ── Public API ────────────────────────────────────────────────────────────────

async def explain_driver_recommendation(
    nearest:        dict,
    rank_score:     float,
    ranking_weights: object,
) -> Optional[str]:
    """
    Generate a plain-English explanation for the top charger recommendation.

    Parameters
    ----------
    nearest         : enriched charger dict from ExplanationAgent
    rank_score      : composite ranking score (0-1)
    ranking_weights : RankingWeights instance from config

    Returns
    -------
    Natural-language explanation string, or None if LLM is unavailable/disabled.
    """
    model = _get_model()
    if model is None:
        return None

    qm = nearest.get("queue_metrics", {})
    prompt = _DRIVER_PROMPT.format(
        name=nearest.get("name", "Unknown"),
        distance_km=nearest.get("distance_km", "?"),
        free_ports=nearest.get("free_ports", "?"),
        total_ports=nearest.get("total_ports", "?"),
        charger_type=nearest.get("type", "Unknown"),
        kw=nearest.get("kw", "?"),
        network=nearest.get("network", "Unknown"),
        wait_min=nearest.get("wait_time_minutes", 0),
        wait_p90=nearest.get("wait_p90_minutes", 0),
        queue_status=qm.get("queue_status", "Unknown"),
        data_quality=nearest.get("data_quality", "unknown"),
        forecast_source=nearest.get("demand_forecast", {}).get("source", "unknown"),
        rank_score=rank_score,
        wait_w=ranking_weights.wait_time,
        avail_w=ranking_weights.free_ports,
        dist_w=ranking_weights.distance,
        speed_w=ranking_weights.charger_speed,
    )

    return await _call_model(prompt, label="driver_recommendation")


async def explain_operator_zone(zone: dict, scoring_weights: object) -> Optional[str]:
    """
    Generate a plain-English justification for an operator expansion zone.

    Parameters
    ----------
    zone            : scored zone dict with score_breakdown
    scoring_weights : ScoringWeights instance from config
    """
    model = _get_model()
    if model is None:
        return None

    sb = zone.get("score_breakdown", {})
    prompt = _OPERATOR_PROMPT.format(
        zip_code=zone.get("zip_code", "?"),
        city=zone.get("city", "?"),
        score=zone.get("score", 0),
        tier=zone.get("recommendation_tier", "?"),
        ev_demand=sb.get("ev_demand", 0),
        traffic=sb.get("traffic", 0),
        competition_gap=sb.get("competition_gap", 0),
        grid=sb.get("grid", 0),
        land_cost=sb.get("land_cost", 0),
        accessibility=sb.get("accessibility", 0),
        w_ev=scoring_weights.ev_demand,
        w_traffic=scoring_weights.traffic,
        w_comp=scoring_weights.competition_gap,
        w_grid=scoring_weights.grid,
        w_land=scoring_weights.land_cost,
        w_access=scoring_weights.accessibility,
        ev_reg=zone.get("ev_registrations", "?"),
        daily_traffic=zone.get("daily_traffic", 0),
        competitors=zone.get("existing_competitors", 0),
        grid_kw=zone.get("grid_capacity_kw", "?"),
    )

    return await _call_model(prompt, label="operator_zone")


# ── Internal call helper ──────────────────────────────────────────────────────

async def _call_model(prompt: str, label: str = "llm") -> Optional[str]:
    """Run the Vertex AI call in an executor so it doesn't block the event loop."""
    model = _get_model()
    if model is None:
        return None

    def _blocking_call():
        from vertexai.generative_models import GenerationConfig
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                max_output_tokens=cfg.vertex.max_tokens,
                temperature=cfg.vertex.temperature,
            ),
        )
        return response.text.strip()

    loop = asyncio.get_event_loop()
    try:
        text = await asyncio.wait_for(
            loop.run_in_executor(None, _blocking_call),
            timeout=15.0,
        )
        logger.debug("[%s] LLM response: %d chars", label, len(text))
        return text
    except asyncio.TimeoutError:
        logger.warning("[%s] Vertex AI call timed out", label)
        return None
    except Exception as exc:
        logger.warning("[%s] Vertex AI call failed: %s", label, exc)
        return None
