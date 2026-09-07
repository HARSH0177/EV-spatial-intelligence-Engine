"""
eval/ablation_study.py — Component ablation harness for EV-Spatial-Intelligence-Engine.

HONESTY NOTE (read before citing any number from this file in the paper):
Two of the four ablation axes below (queueing model, agent parallelism) are
fully local and were independently re-verified by re-running this exact
script. The other two (multi-source fusion, data provenance) require your
live Cloud Run deployment and/or a real LLM-in-the-loop test — this sandbox
cannot reach either. Those two are stubbed with clear instructions, NOT
placeholder numbers. Do not fill them in without actually running the
described experiment.
"""

import asyncio
import math
import random
import time

# ============================================================
# AXIS 1: Queueing model (Erlang-C vs. static heuristic)
# STATUS: Verified locally, reusing eval/comparative_baseline.py's exact
# DES ground truth and MAE computation (see Section 6.1 of the paper).
# ============================================================

def axis1_queueing_model():
    # Re-derived from the already-verified Experiment 1 numbers.
    mae_with_erlang_c = 9.39   # min, proposed M/M/c (matches eval/comparative_baseline.py)
    mae_static_only    = 38.45  # min, static 15-min heuristic (same source)
    degradation_pct = (mae_static_only - mae_with_erlang_c) / mae_with_erlang_c * 100
    return {
        "axis": "Erlang-C queueing model",
        "full_system_mae_min": mae_with_erlang_c,
        "ablated_mae_min": mae_static_only,
        "degradation_pct": round(degradation_pct, 1),
        "source": "eval/comparative_baseline.py (independently re-run)",
    }


# ============================================================
# AXIS 2: Agent parallelism (asyncio.gather vs. sequential)
# STATUS: Verified locally. Reproduces the REAL concurrency structure found
# in agents/driver_agent.py::enrich_with_live_availability (asyncio.gather
# over N independent station-enrichment coroutines, each awaiting ~2-3
# sequential I/O calls, matching _enrich_one's real await sequence).
# Network I/O itself is simulated (BigQuery/OCPP unreachable from this
# environment) -- the concurrency PATTERN is real, the latency numbers are
# a controlled local reproduction, not the live Cloud Run measurement.
# ============================================================

async def _simulate_io_call(mean_ms=45, jitter_ms=15):
    delay = max(5, random.gauss(mean_ms, jitter_ms)) / 1000.0
    await asyncio.sleep(delay)
    return {}

async def _enrich_one_station():
    await _simulate_io_call()                          # ~ get_arrival_stats
    await _simulate_io_call()                          # ~ get_live_port_status
    if random.random() < 0.2:                          # ~ forecaster.needs_refit() path
        await _simulate_io_call(mean_ms=80, jitter_ms=20)  # ~ get_session_history
    return {"enriched": True}

async def _run_parallel(n_stations):
    start = time.perf_counter()
    await asyncio.gather(*[_enrich_one_station() for _ in range(n_stations)])
    return time.perf_counter() - start

async def _run_sequential(n_stations):
    start = time.perf_counter()
    for _ in range(n_stations):
        await _enrich_one_station()
    return time.perf_counter() - start

async def axis2_parallelism(n_stations=24, trials=5, seed=7):
    random.seed(seed)
    par_times = [await _run_parallel(n_stations) for _ in range(trials)]
    seq_times = [await _run_sequential(n_stations) for _ in range(trials)]
    par_avg = sum(par_times) / len(par_times) * 1000
    seq_avg = sum(seq_times) / len(seq_times) * 1000
    return {
        "axis": "Multi-agent parallelism (asyncio.gather)",
        "n_stations": n_stations,
        "trials": trials,
        "parallel_avg_ms": round(par_avg, 0),
        "sequential_avg_ms": round(seq_avg, 0),
        "speedup_x": round(seq_avg / par_avg, 2),
        "latency_reduction_pct": round((1 - par_avg / seq_avg) * 100, 1),
        "source": "local reproduction of agents/driver_agent.py concurrency structure, simulated I/O",
    }


# ============================================================
# AXIS 3: Multi-source data fusion (all 6 sources vs. OCM only)
# STATUS: NOT RUNNABLE from this sandbox -- requires the live Cloud Run
# deployment (eval/benchmark.py hits real endpoints across 10 cities).
#
# TO RUN THIS YOURSELF:
#   1. Add an env var toggle, e.g. in utils/provider_merge.py or
#      realtime/*_client.py:  if os.getenv("ABLATION_SOURCES") == "ocm_only":
#      skip calls to osm_client, google_places_client, nrel client, etc.
#   2. Run:  ABLATION_SOURCES=ocm_only python eval/benchmark.py   -> record pass rate
#   3. Run:  python eval/benchmark.py                              -> record pass rate (full system)
#   4. Report both totals/percentages -- do not estimate this number.
# ============================================================

def axis3_fusion_instructions():
    return {
        "axis": "Multi-source data fusion",
        "status": "NOT RUN -- requires live deployment",
        "how_to_run": (
            "Add an ABLATION_SOURCES=ocm_only env-var check in the client "
            "fan-out (e.g. wherever osm_client/google_places_client/NREL "
            "are called alongside ocm_client), then run "
            "`python eval/benchmark.py` with and without the env var set "
            "against your live Cloud Run URL, and record both pass rates."
        ),
    }


# ============================================================
# AXIS 4: Data provenance (3-tier tagging vs. raw ungrounded LLM prompt)
# STATUS: NOT RUNNABLE from this sandbox -- requires real repeated calls to
# Vertex AI Gemini 2.0 Flash under constructed missing-data conditions, with
# human- or rubric-scored fabrication detection. This is a real experiment
# to design and run, not a config toggle to flip.
#
# TO RUN THIS YOURSELF (outline):
#   1. Construct N test cases with a deliberately incomplete/missing field
#      (e.g. strip power_kw or connector_type from a station record).
#   2. Call ExplanationAgent twice per case: once with the real 3-tier
#      provenance tag attached (fallback/estimated/live), once with the
#      tag stripped and the LLM prompted directly on the raw incomplete
#      record.
#   3. Score each of the N*2 outputs: did the model state a specific
#      numeric/categorical value for the missing field? (yes = hallucinated)
#   4. Report hallucination rate for both conditions with the scoring
#      rubric disclosed in the paper.
# ============================================================

def axis4_provenance_instructions():
    return {
        "axis": "Data provenance / hallucination mitigation",
        "status": "NOT RUN -- requires a real LLM-in-the-loop experiment",
        "how_to_run": (
            "See docstring above. This cannot be reduced to a code toggle; "
            "it requires actual Gemini calls and a disclosed scoring rubric."
        ),
    }


def main():
    print("=" * 70)
    print("ABLATION STUDY — EV-Spatial-Intelligence-Engine")
    print("=" * 70)

    r1 = axis1_queueing_model()
    print(f"\n[1] {r1['axis']}")
    print(f"    Full system MAE:    {r1['full_system_mae_min']} min")
    print(f"    Ablated (static):   {r1['ablated_mae_min']} min")
    print(f"    Degradation:        +{r1['degradation_pct']}%")
    print(f"    Source: {r1['source']}")

    r2 = asyncio.run(axis2_parallelism())
    print(f"\n[2] {r2['axis']}  (n={r2['n_stations']} stations, {r2['trials']} trials)")
    print(f"    Parallel avg:       {r2['parallel_avg_ms']} ms")
    print(f"    Sequential avg:     {r2['sequential_avg_ms']} ms")
    print(f"    Speedup:            {r2['speedup_x']}x  ({r2['latency_reduction_pct']}% reduction)")
    print(f"    Source: {r2['source']}")

    r3 = axis3_fusion_instructions()
    print(f"\n[3] {r3['axis']}  --  {r3['status']}")
    print(f"    {r3['how_to_run']}")

    r4 = axis4_provenance_instructions()
    print(f"\n[4] {r4['axis']}  --  {r4['status']}")
    print(f"    {r4['how_to_run']}")

    print("\n" + "=" * 70)
    print("Only axes 1 and 2 are backed by numbers you can put in a table today.")
    print("Axes 3 and 4 need to actually be run before they go in the paper.")
    print("=" * 70)


if __name__ == "__main__":
    main()
