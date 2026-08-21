# EV Advisor — Evaluation Harness & Benchmark Suite

This directory contains the automated evaluation framework used to benchmark the **EV Spatial Intelligence Engine** against production deployments.

---

## 📊 Benchmark Overview

The evaluation suite runs **56 automated test checks** across 11 core system dimensions to measure:
1. **API Reliability & Uptime:** End-to-end HTTP 200 verification across all public and internal endpoints.
2. **Input Validation Precision:** Edge-case fuzzing and schema verification (100% 422 rejection rate on malformed payloads).
3. **Global Spatial Coverage:** Validation across 10 global metropolitan areas spanning 5 continents.
4. **Data Transparency:** Verification that 100% of responses carry explicit data provenance tags (`live`, `estimated`, or `fallback`).
5. **Queueing Model Invariant ($p_{50} \le p_{90}$):** Parameterized stress-testing of M/M/c Erlang C queueing equations across 728 arrival rate ($\lambda$), service time ($\mu$), and capacity ($c$) combinations.
6. **Geodesic Math Precision:** Validation of Haversine distance computations against known global geodesic ground truth pairs.
7. **GeoJSON Spec Compliance:** Point geometry, coordinate bounds, and RFC 7946 FeatureCollection validation.
8. **End-to-End Latency Profiles:** $p_{50}$, mean, and $p_{95}$ response time percentiles across multi-run distributions.

---

## 🚀 Running the Benchmark

### Prerequisites
```bash
pip install httpx numpy scikit-learn
```

### Execution Against Production
```bash
python eval/benchmark.py
```

### Execution Target Configuration
You can customize the evaluation target URL by setting the `BASE_URL` environment variable:
```bash
BASE_URL="https://ev-advisor-api-79118074976.us-central1.run.app" python eval/benchmark.py
```

---

## 📈 Latest Production Benchmark Results (2026-08-04)

```
========================================================================
EV ADVISOR — COMPREHENSIVE BENCHMARK EVALUATION
Target: https://ev-advisor-api-79118074976.us-central1.run.app
========================================================================

  TOTAL CHECKS: 56
  PASSED:       51
  PASS RATE:    91.1%

  Per-Section Breakdown:
    reliability          11/11 (100.0%)
    validation           10/10 (100.0%)
    geo_coverage         10/10 (100.0%)
    data_quality         1/1 (100.0%)
    type_filter          1/3 (33.3%)
    geojson              5/5 (100.0%)
    haversine            5/5 (100.0%)
    queue_model          5/5 (100.0%)
    data_fusion          1/1 (100.0%)
    expansion            2/5 (40.0%)

  === KEY METRICS ===
  API Reliability:       11/11 endpoints returning 200 (100.0%)
  Input Validation:      10/10 invalid requests -> 422 (100.0%)
  Geographic Coverage:   10/10 cities returning data (5 continents)
  Distance Accuracy:     avg error = 0.28% across 5 known pairs (99.72% accuracy)
  Queue Model Invariant: p50 <= p90 holds for 728/728 configs (100.0%)
  Data Quality Labels:   0/144 unlabeled (100.0% labeled)
  GeoJSON Spec:          5/5 valid FeatureCollections (100.0%)
  Discovery Latency:     p50 = 880ms (sub-second)
========================================================================
```
