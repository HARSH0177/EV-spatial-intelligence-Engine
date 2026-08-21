"""
eval/benchmark.py — Comprehensive evaluation harness for EV Advisor.
Evaluates API reliability, input validation, geographic coverage, queue model correctness,
data quality labels, Haversine accuracy, GeoJSON compliance, and latency percentiles.
"""

import json
import math
import os
import sys
import time
import statistics
from collections import defaultdict

import httpx

BASE = os.environ.get("BASE_URL", "https://ev-advisor-api-79118074976.us-central1.run.app")
TIMEOUT = int(os.environ.get("BENCHMARK_TIMEOUT", "45"))

all_results = []
section_results = defaultdict(list)


def api(method, path, body=None, timeout=TIMEOUT):
    url = f"{BASE}{path}"
    start = time.time()
    try:
        if method == "GET":
            r = httpx.get(url, timeout=timeout)
        else:
            r = httpx.post(url, json=body, timeout=timeout)
        elapsed = round(time.time() - start, 3)
        return r, elapsed
    except Exception as e:
        elapsed = round(time.time() - start, 3)
        return None, elapsed


def record(section, name, passed, latency, detail=""):
    status = "PASS" if passed else "FAIL"
    all_results.append({
        "section": section,
        "name": name,
        "status": status,
        "latency": latency,
        "detail": detail
    })
    section_results[section].append(passed)
    icon = "[PASS]" if passed else "[FAIL]"
    lat_str = f"{latency:.2f}s" if latency else "N/A"
    print(f"  {icon} {name} ({lat_str}) {detail}")


def main():
    print("=" * 72)
    print("EV ADVISOR — COMPREHENSIVE BENCHMARK EVALUATION")
    print(f"Target: {BASE}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    # 1. API RELIABILITY
    print("\n--- SECTION 1: API RELIABILITY ---")
    endpoints = [
        ("GET",  "/health", None),
        ("GET",  "/ready", None),
        ("GET",  "/", None),
        ("POST", "/driver/locate-charger", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST", "/driver/map-data", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST", "/api/search/discover", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST", "/api/search/chargers", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST", "/api/search/parking", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST", "/api/search/mobility", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST", "/company/plan-expansion", {"city": "San Francisco", "budget_usd": 5000000, "top_n": 3}),
        ("POST", "/agent/run", {"task_type": "status", "payload": {}}),
    ]

    for method, path, body in endpoints:
        r, lat = api(method, path, body)
        ok = r is not None and r.status_code == 200
        record("reliability", f"{method} {path}", ok, lat, f"HTTP {r.status_code if r else 'TIMEOUT'}")

    # 2. INPUT VALIDATION
    print("\n--- SECTION 2: INPUT VALIDATION ---")
    validation_cases = [
        ("/driver/locate-charger", {}, "no location at all"),
        ("/driver/locate-charger", {"max_distance_km": 5}, "missing lat/lon and location"),
        ("/api/search/discover", {}, "empty body"),
        ("/api/search/discover", {"max_distance_km": 5}, "missing coords"),
        ("/api/search/chargers", {"latitude": 37.7}, "missing longitude"),
        ("/api/search/parking", {}, "empty body"),
        ("/api/search/mobility", {}, "empty body"),
        ("/api/advisor/analyze-area", {}, "missing location"),
        ("/api/advisor/analyze-area", {"top_n": 3}, "missing location field"),
        ("/api/advisor/rank-zones", {}, "missing location"),
    ]

    for path, body, desc in validation_cases:
        r, lat = api("POST", path, body)
        ok = r is not None and r.status_code == 422
        record("validation", f"POST {path} ({desc})", ok, lat, f"HTTP {r.status_code if r else 'ERR'}")

    # 3. GEOGRAPHIC COVERAGE
    print("\n--- SECTION 3: GEOGRAPHIC COVERAGE (10 cities, 5 continents) ---")
    cities = [
        ("San Francisco", 37.7749, -122.4194, "North America"),
        ("New York",      40.7128,  -74.0060, "North America"),
        ("London",        51.5074,   -0.1278, "Europe"),
        ("Berlin",        52.5200,   13.4050, "Europe"),
        ("Tokyo",         35.6762,  139.6503, "Asia"),
        ("Pune",          18.5204,   73.8567, "Asia"),
        ("Sydney",       -33.8688,  151.2093, "Oceania"),
        ("Nairobi",       -1.2921,   36.8219, "Africa"),
        ("Sao Paulo",    -23.5505,  -46.6333, "South America"),
        ("Dubai",         25.2048,   55.2708, "Middle East"),
    ]

    geo_results = []
    continents_covered = set()

    for city, lat, lon, continent in cities:
        r, lat_time = api("POST", "/api/search/discover", {"latitude": lat, "longitude": lon, "max_distance_km": 10})
        if r and r.status_code == 200:
            data = r.json()
            total = data.get("total_found", 0)
            providers = data.get("providers_used", [])
            geo_results.append({"city": city, "continent": continent, "total": total, "providers": len(providers)})
            continents_covered.add(continent)
            record("geo_coverage", f"{city} ({continent})", total > 0, lat_time, f"{total} results from {len(providers)} providers")
        else:
            geo_results.append({"city": city, "continent": continent, "total": 0, "providers": 0})
            record("geo_coverage", f"{city} ({continent})", False, lat_time, f"HTTP {r.status_code if r else 'TIMEOUT'}")

    # 4. DATA QUALITY DISTRIBUTION
    print("\n--- SECTION 4: DATA QUALITY LABEL DISTRIBUTION ---")
    dq_counts = defaultdict(int)
    dq_total = 0
    unlabeled = 0

    for city, lat, lon, _ in cities[:5]:
        r, _ = api("POST", "/api/search/discover", {"latitude": lat, "longitude": lon, "max_distance_km": 10})
        if r and r.status_code == 200:
            for item in r.json().get("results", []):
                dq = item.get("data_quality")
                if dq:
                    dq_counts[dq] += 1
                else:
                    unlabeled += 1
                dq_total += 1

    record("data_quality", "0% unlabeled results", unlabeled == 0, 0, f"{dq_total} items checked")

    # 5. TYPE FILTERING
    print("\n--- SECTION 5: TYPE FILTERING CORRECTNESS ---")
    filter_tests = [
        ("/api/search/chargers", "charger"),
        ("/api/search/parking", "parking"),
        ("/api/search/mobility", "mobility_hub"),
    ]

    for path, expected_type in filter_tests:
        r, lat_time = api("POST", path, {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 10})
        if r and r.status_code == 200:
            results = r.json().get("results", [])
            correct = sum(1 for item in results if item.get("type") == expected_type)
            total = len(results)
            pct = round(correct / max(total, 1) * 100, 1) if total > 0 else 0.0
            record("type_filter", f"{path} -> only {expected_type}", pct == 100.0 and total > 0, lat_time, f"{correct}/{total} correct ({pct}%)")
        else:
            record("type_filter", f"{path} -> only {expected_type}", False, lat_time, "request failed")

    # 6. GEOJSON OUTPUT
    print("\n--- SECTION 6: GEOJSON OUTPUT CORRECTNESS ---")
    for city, lat, lon, _ in cities[:5]:
        r, lat_time = api("POST", "/driver/map-data", {"latitude": lat, "longitude": lon, "max_distance_km": 10})
        if r and r.status_code == 200:
            data = r.json()
            is_fc = data.get("type") == "FeatureCollection"
            features = data.get("features", [])
            all_points = all(f.get("geometry", {}).get("type") == "Point" for f in features) if features else True
            all_have_props = all("properties" in f for f in features) if features else True
            valid_coords = all(len(f.get("geometry", {}).get("coordinates", [])) == 2 for f in features) if features else True
            ok = is_fc and all_points and all_have_props and valid_coords
            record("geojson", f"map-data {city}", ok, lat_time, f"{len(features)} features, valid={ok}")
        else:
            record("geojson", f"map-data {city}", False, lat_time, "request failed")

    # 7. HAVERSINE DISTANCE
    print("\n--- SECTION 7: HAVERSINE DISTANCE ACCURACY ---")
    known_distances = [
        ("Pune", "Mumbai", 18.52, 73.85, 19.07, 72.87, 120.0),
        ("NYC", "Boston", 40.7128, -74.0060, 42.3601, -71.0589, 306.0),
        ("London", "Paris", 51.5074, -0.1278, 48.8566, 2.3522, 344.0),
        ("Tokyo", "Osaka", 35.6762, 139.6503, 34.6937, 135.5023, 397.0),
        ("SF", "LA", 37.7749, -122.4194, 34.0522, -118.2437, 559.0),
    ]

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance_errors = []
    for city1, city2, lat1, lon1, lat2, lon2, expected in known_distances:
        computed = haversine(lat1, lon1, lat2, lon2)
        error_pct = abs(computed - expected) / expected * 100
        distance_errors.append(error_pct)
        ok = error_pct < 5.0
        record("haversine", f"{city1}-{city2}: {computed:.1f}km vs {expected:.0f}km", ok, 0, f"error={error_pct:.1f}%")

    # 8. QUEUE MODEL INVARIANT
    print("\n--- SECTION 8: QUEUE MODEL p50 <= p90 INVARIANT ---")
    try:
        from models.queue_model import MMcQueueModel
        qm = MMcQueueModel()
        invariant_violations = 0
        total_configs = 0

        for lam in [0.5, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20]:
            for avg_min in [10, 15, 20, 25, 30, 40, 60]:
                for ports in [1, 2, 3, 4, 5, 6, 8, 10]:
                    total_configs += 1
                    result = qm.compute(lam, avg_min, ports)
                    if result.wait_p50_min > result.wait_p90_min + 0.001:
                        invariant_violations += 1

        pct_correct = round((total_configs - invariant_violations) / total_configs * 100, 2)
        record("queue_model", f"p50 <= p90 across {total_configs} configs", invariant_violations == 0, 0, f"{pct_correct}% correct, {invariant_violations} violations")

        boundary_cases = [
            (0, 30, 4, "zero arrivals"),
            (100, 5, 2, "extreme overload"),
            (0.1, 60, 1, "single port low load"),
            (10, 10, 10, "balanced load"),
        ]
        for lam, avg, ports, desc in boundary_cases:
            r = qm.compute(lam, avg, ports)
            ok = r.wait_p50_min <= r.wait_p90_min + 0.001
            record("queue_model", f"Boundary: {desc}", ok, 0, f"p50={r.wait_p50_min}, p90={r.wait_p90_min}")

    except Exception as e:
        record("queue_model", "local queue import", False, 0, str(e))

    # 9. LATENCY BENCHMARKS
    print("\n--- SECTION 9: LATENCY BENCHMARKS (3 runs each) ---")
    latency_endpoints = [
        ("GET /health",          "GET",  "/health", None),
        ("GET /ready",           "GET",  "/ready", None),
        ("POST discover (SF)",   "POST", "/api/search/discover", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST chargers (SF)",   "POST", "/api/search/chargers", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST parking (SF)",    "POST", "/api/search/parking", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST locate (Pune)",   "POST", "/driver/locate-charger", {"latitude": 18.52, "longitude": 73.85, "max_distance_km": 5}),
        ("POST map-data (SF)",   "POST", "/driver/map-data", {"latitude": 37.7749, "longitude": -122.4194, "max_distance_km": 5}),
        ("POST agent/status",    "POST", "/agent/run", {"task_type": "status", "payload": {}}),
    ]

    for name, method, path, body in latency_endpoints:
        times = []
        for _ in range(3):
            r, lat = api(method, path, body)
            if r and r.status_code == 200:
                times.append(lat)
        if times:
            p50 = round(statistics.median(times), 3)
            avg = round(statistics.mean(times), 3)
            p_max = round(max(times), 3)
            print(f"  {name}: p50={p50}s, avg={avg}s, max={p_max}s ({len(times)} runs)")

    # 10. MULTI-SOURCE DATA FUSION
    print("\n--- SECTION 10: MULTI-SOURCE DATA FUSION ---")
    provider_counts = []
    all_providers_seen = set()

    for city, lat, lon, _ in cities:
        r, _ = api("POST", "/api/search/discover", {"latitude": lat, "longitude": lon, "max_distance_km": 10})
        if r and r.status_code == 200:
            providers = r.json().get("providers_used", [])
            provider_counts.append(len(providers))
            all_providers_seen.update(providers)

    if provider_counts:
        avg_providers = round(statistics.mean(provider_counts), 1)
        record("data_fusion", f"Avg {avg_providers} providers/request", avg_providers >= 1, 0, f"seen: {sorted(all_providers_seen)}")

    # 11. EXPANSION PLANNING
    print("\n--- SECTION 11: EXPANSION PLANNING ZONE RANKING ---")
    r, lat_time = api("POST", "/company/plan-expansion", {"city": "San Francisco", "budget_usd": 5000000, "top_n": 5})
    if r and r.status_code == 200:
        data = r.json()
        zones = data.get("top_zones", [])
        scores = [z.get("viability_score", 0) for z in zones]
        is_sorted = scores == sorted(scores, reverse=True)
        all_bounded = all(0 <= s <= 1 for s in scores)
        record("expansion", "Zones sorted by viability (descending)", is_sorted, lat_time, f"scores={scores}")
        record("expansion", "All viability scores in [0,1]", all_bounded, 0, f"range=[{min(scores) if scores else 0}, {max(scores) if scores else 0}]")
    else:
        record("expansion", "Expansion API call", False, lat_time, f"HTTP {r.status_code if r else 'ERR'}")

    # SUMMARY
    print("\n" + "=" * 72)
    print("FINAL BENCHMARK SUMMARY")
    print("=" * 72)
    total_pass = sum(1 for r in all_results if r["status"] == "PASS")
    total = len(all_results)
    print(f"\n  TOTAL CHECKS: {total}")
    print(f"  PASSED:       {total_pass}")
    print(f"  PASS RATE:    {round(total_pass/max(total,1)*100, 1)}%")


if __name__ == "__main__":
    main()
