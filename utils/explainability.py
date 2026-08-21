"""
utils/explainability.py  —  Transparent explanation text generation.

Produces plain-English explanations that clearly separate:
  - real_inputs:    data from live/external providers
  - modeled_inputs: derived heuristics and estimates

Used by AdvisorAgent and ExplanationAgent to meet the
"no fake precision, no false confidence" requirement.
"""

from typing import Dict, Any


def build_zone_explanation(
    zone_name:       str,
    city:            str,
    viability_score: float,
    confidence_score: float,
    demand_score:    float,
    competition_score: float,
    accessibility_score: float,
    real_inputs:     Dict[str, Any],
    modeled_inputs:  Dict[str, Any],
    recommended_type: str,
    recommended_ports: int,
) -> str:
    """
    Build a transparent explanation for a zone recommendation.
    Explicitly names what data was real and what was modeled.
    """
    confidence_label = _confidence_label(confidence_score)
    viability_label  = _score_label(viability_score)

    # Summarize real data sources
    real_parts = []
    if real_inputs.get("charger_count") is not None:
        real_parts.append(f"{real_inputs['charger_count']} existing charger(s) from live inventory")
    if real_inputs.get("parking_count") is not None:
        real_parts.append(f"{real_inputs['parking_count']} parking lot(s) from OSM")
    if real_inputs.get("neighborhoods_used"):
        real_parts.append(f"neighborhood data from OpenStreetMap")
    real_summary = (
        "Real data used: " + "; ".join(real_parts) + "."
        if real_parts else
        "No live data sources were available for this zone."
    )

    # Summarize modeled signals
    model_parts = []
    for key, val in modeled_inputs.items():
        if val is not None:
            label = key.replace("_", " ").title()
            model_parts.append(f"{label}: {val:.2f}" if isinstance(val, float) else f"{label}: {val}")
    model_summary = (
        "Modeled signals: " + "; ".join(model_parts[:4]) + "."
        if model_parts else
        "All signals are model-derived."
    )

    return (
        f"{zone_name} in {city} shows {viability_label} setup viability "
        f"(score {viability_score:.2f}, confidence {confidence_label}). "
        f"Demand signal: {_score_label(demand_score)}; "
        f"Competition gap: {_score_label(competition_score)}; "
        f"Accessibility: {_score_label(accessibility_score)}. "
        f"Recommended: {recommended_type} with {recommended_ports} port(s). "
        f"{real_summary} "
        f"{model_summary}"
    )


def build_discover_explanation(
    result_count: int,
    city:         str,
    providers:    list,
    data_qualities: dict,
) -> str:
    """Plain-English summary of a discover search result."""
    quality_parts = []
    for quality, count in data_qualities.items():
        if count:
            quality_parts.append(f"{count} {quality}")

    provider_str = ", ".join(providers) if providers else "available sources"
    quality_str  = "; ".join(quality_parts) if quality_parts else "quality unknown"

    return (
        f"Found {result_count} result(s) near {city} "
        f"from {provider_str}. "
        f"Data quality breakdown: {quality_str}."
    )


def _score_label(score: float) -> str:
    if score >= 0.75: return "strong"
    if score >= 0.50: return "moderate"
    if score >= 0.25: return "low"
    return "very low"


def _confidence_label(score: float) -> str:
    if score >= 0.75: return "high"
    if score >= 0.50: return "medium"
    if score >= 0.25: return "low"
    return "very low"
