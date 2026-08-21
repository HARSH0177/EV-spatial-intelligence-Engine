# EV-Spatial-Intelligence-Engine ⚡

<div align="center">

![EV Spatial Intelligence Engine Hero Banner](https://raw.githubusercontent.com/HARSH0177/EV-spatial-intelligence-Engine/main/assets/hero-banner.svg?v=2.2)

<br/><br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Google Cloud Run](https://img.shields.io/badge/Google_Cloud_Run-Deployed-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![BigQuery](https://img.shields.io/badge/BigQuery-Analytics-669DF6?style=for-the-badge&logo=googlebigquery&logoColor=white)](https://cloud.google.com/bigquery)
[![Vertex AI](https://img.shields.io/badge/Vertex_AI-Gemini_2.0_Flash-EA4335?style=for-the-badge&logo=google&logoColor=white)](https://cloud.google.com/vertex-ai)
[![OCPP 1.6](https://img.shields.io/badge/Protocol-OCPP_1.6_WebSocket-FFA000?style=for-the-badge&logo=socketdotio&logoColor=white)](https://www.openchargealliance.org/)
[![Benchmark](https://img.shields.io/badge/Eval_Pass_Rate-91.1%25-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](eval/)

**Autonomous 6-Agent EV Infrastructure Planning & Spatial Decision Engine**

[Live Application Demo](https://ev-advisor-api-79118074976.us-central1.run.app/app/) • [Swagger OpenAPI Documentation](https://ev-advisor-api-79118074976.us-central1.run.app/docs) • [Evaluation Benchmark](eval/)

</div>

---

## 📖 About The Project

As global electric vehicle adoption accelerates, urban planners, charging network operators (CPOs), and fleet managers face a fundamental scaling bottleneck: **How to accurately discover charging infrastructure and strategically site new charging hubs without relying on hardcoded city metadata or brittle single-source APIs.**

Traditional approaches suffer from three systemic failure modes:
1. **The Single-Source Illusion:** Relying solely on Google Places or OpenStreetMap results in massive data blindspots — missing live port hardware states, proprietary fleet telemetry, or regional government registries.
2. **Deterministic Guesswork for Queues:** Most applications assume zero wait times or use static averages, failing to capture the stochastic reality of vehicle arrivals ($\lambda$) and charging durations ($\mu$).
3. **Black-Box AI Hallucinations:** Generative AI wrappers frequently hallucinate non-existent addresses and fabricated power ratings when ungrounded by rigorous spatial mathematics.

**EV-Spatial-Intelligence-Engine** solves this by decoupling the spatial intelligence pipeline into **6 autonomous specialized agents**. The engine ingests, deduplicates, and fuses data across **6 live global data sources**, executes **$M/M/c$ Erlang C queueing theory** to model driver wait distributions ($p_{50}$ and $p_{90}$), applies Gradient Boosted demand forecasting, and grounds **Vertex AI Gemini 2.0 Flash** synthesis in transparent 3-tier data provenance labels (`live` $\rightarrow$ `estimated` $\rightarrow$ `fallback`).

---

## 🌟 Key System Capabilities

- **6-Agent Autonomous Orchestration:** Decoupled multi-agent execution pipeline with asynchronous task routing and graceful fallback chains.
- **Global Spatial Coverage (Zero Hardcoding):** Dynamically geocodes, extracts district shapes, and models amenities for any city worldwide (validated across San Francisco, London, Berlin, Tokyo, Pune, Nairobi, São Paulo, and Dubai).
- **Applied Queueing Theory ($M/M/c$ Erlang C):** Computes $p_{50}$ and $p_{90}$ driver wait times with mathematically proven percentile bounds across 728+ parameter configurations.
- **3-Tier Data Provenance & Transparency:** Every station and zone recommendation carries explicit tagging (`live` $\rightarrow$ `estimated` $\rightarrow$ `fallback`) with quantitative confidence scoring.
- **Sub-Second Real-Time Discovery:** Multi-source async ingestion pipeline with in-memory TTL caching delivering **$p_{50} = 880\text{ms}$** response times.
- **56-Check Automated Benchmark Suite:** Comprehensive production evaluation harness achieving a **91.1% pass rate** on live GCP Cloud Run infrastructure.

---

## 🏗️ System Architecture & Visual Pipeline

<div align="center">
  <img src="https://raw.githubusercontent.com/HARSH0177/EV-spatial-intelligence-Engine/main/assets/architecture-diagram.svg?v=2.2" alt="System Architecture Diagram" width="100%" />
</div>

<br/>

### 🔍 Architectural Layer Breakdown

The system architecture diagram above illustrates the 4-layer asynchronous data processing pipeline:

1. **Layer 1 — Interface & API Gateway Layer:**  
   Users interact through a single, responsive Leaflet.js single-page application (`/app`) and a high-throughput FastAPI async gateway. Deployed on auto-scaling Google Cloud Run, it routes discovery queries and site-planning jobs across asynchronous workers.
2. **Layer 2 — Autonomous Multi-Agent Orchestration Layer:**  
   The `OrchestratorAgent` coordinates 5 specialized agents. `DriverAssistantAgent` manages spatial indexing, connector filters, and distance ranking. `AdvisorAgent` extracts administrative districts and synthesizes candidate zones. `ScoringAgent` computes multi-criteria viability scores. `DataAgent` queries BigQuery telemetry and active ports, while `ExplanationAgent` prompts Gemini 2.0 Flash for structured natural-language reasoning.
3. **Layer 3 — Mathematical & Predictive Machine Learning Layer:**  
   Executes continuous $M/M/c$ Erlang C stochastic queueing calculations, runs Gradient Boosted Regressors (`DemandForecaster`) for port load estimation, and triggers `QueueModelValidator` to guarantee mathematical consistency ($p_{50} \le p_{90}$) across all traffic intensities.
4. **Layer 4 — Live Data Fusion & Hardware Protocol Layer:**  
   Fuses 6 live external sources (OpenChargeMap, OSM Overpass, Google Places, NREL AFDC, BigQuery, and OCPP 1.6 WebSockets) through a spatial deduplication engine (`ProviderMerge`), ensuring robust fallback when individual upstream APIs experience latency or rate limits.

<br/>

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#E8F5E9', 'primaryTextColor': '#1B3B2B', 'primaryBorderColor': '#81C784', 'lineColor': '#2E4A3E', 'secondaryColor': '#EDE7F6', 'tertiaryColor': '#E3F2FD' }}}%%
graph TD
    subgraph ClientLayer ["1. Client & Gateway Layer"]
        UI["Leaflet.js + OpenStreetMap SPA<br/>(/app)"]
        API_GW["FastAPI REST & WebSocket Gateway"]
    end

    subgraph AgentLayer ["2. Autonomous Multi-Agent Orchestration"]
        ORCH["OrchestratorAgent<br/>(Task Routing & Pipeline Coordinator)"]
        DRIVER["DriverAssistantAgent<br/>(Discovery, Geo-Radius, Connector Filter)"]
        ADVISOR["AdvisorAgent<br/>(Site Selection, District Extraction, Scoring)"]
        DATA["DataAgent<br/>(BigQuery Aggregations, Port Status)"]
        SCORING["ScoringAgent<br/>(Multi-Factor Viability Matrix)"]
        EXPLAIN["ExplanationAgent<br/>(Vertex AI Gemini 2.0 Synthesis)"]
    end

    subgraph ModelLayer ["3. Mathematical & Predictive Models"]
        QUEUE["M/M/c Erlang C Queue Model<br/>(Wait Time p50 / p90 Distributions)"]
        FORECAST["DemandForecaster<br/>(Gradient Boosted Regressor)"]
        VALIDATOR["QueueModelValidator<br/>(Invariant Assertion Engine)"]
    end

    subgraph DataFusionLayer ["4. Live Data Fusion & Provider Ingestion"]
        MERGE["ProviderMerge & Deduplication Engine"]
        GEO["GeoEnricher (Nominatim + Overpass Boundaries)"]
        CACHE["In-Memory Multi-Tier TTL Cache"]
    end

    subgraph ExternalSources ["External Providers & Hardware Protocols"]
        OCM["OpenChargeMap API<br/>(Global Registry)"]
        OSM["OpenStreetMap / Overpass API<br/>(Parking & Amenities)"]
        GPLACES["Google Places API<br/>(EV Enrichment)"]
        NREL["NREL AFDC API<br/>(US Station Fallback)"]
        BQ["Google BigQuery<br/>(Session Telemetry & Ports)"]
        OCPP["OCPP 1.6 WebSocket Server<br/>(Live Hardware Status)"]
    end

    UI --> API_GW
    API_GW --> ORCH
    ORCH --> DRIVER
    ORCH --> ADVISOR

    DRIVER --> MERGE
    DRIVER --> QUEUE
    ADVISOR --> GEO
    ADVISOR --> SCORING
    ADVISOR --> EXPLAIN

    SCORING --> QUEUE
    SCORING --> FORECAST
    EXPLAIN --> DATA

    MERGE --> OCM
    MERGE --> OSM
    MERGE --> GPLACES
    MERGE --> NREL
    MERGE --> OCPP

    GEO --> OSM
    DATA --> BQ
    QUEUE --> VALIDATOR
```

---

## 🤖 Multi-Agent Ecosystem

| Agent | Responsibility | Core Technology |
|---|---|---|
| **OrchestratorAgent** | High-level request lifecycle management, routing, and fallback coordination | Asyncio, State Machine |
| **DriverAssistantAgent** | Real-time charger search, connector normalization (CCS, CHAdeMO, Type2, Tesla), distance sorting | Haversine Geodesic, Spatial Indexing |
| **AdvisorAgent** | Global city district discovery, competition analysis, and candidate zone synthesis | Overpass API, Seeded Deterministic Heuristics |
| **DataAgent** | Fleet session telemetry querying, port utilization statistics, and hardware sync | BigQuery Async Client, OCPP 1.6 Central |
| **ScoringAgent** | Multi-attribute utility matrix combining demand, grid load, ROI, and accessibility | Vectorized Composite Weighted Scoring |
| **ExplanationAgent** | Natural language reasoning explaining *why* a site was selected and what signals were modeled | Vertex AI Gemini 2.0 Flash |

---

## 📐 Mathematical Formulation ($M/M/c$ Erlang C Model)

<div align="center">
  <img src="https://raw.githubusercontent.com/HARSH0177/EV-spatial-intelligence-Engine/main/assets/queue-model-flow.svg?v=2.2" alt="Queue Model Flow Diagram" width="100%" />
</div>

<br/>

### 🔬 Stochastic Wait-Time Estimation Pipeline

The queueing flow diagram above maps the mathematical lifecycle of every wait-time prediction:

1. **Stage 1 — Poisson Arrival Process ($\lambda$):**  
   Models random vehicle arrival rates ($\lambda$ vehicles/hr) derived from urban traffic indices, localized amenity density, and EV adoption penetration proxies.
2. **Stage 2 — Multi-Server Port Capacity ($c$, $\mu$):**  
   Calculates traffic intensity $\rho = \frac{\lambda}{c \cdot \mu}$. When $\rho < 1.0$, the Erlang C delay probability formula $C(c, a)$ computes the exact probability that all $c$ chargers are occupied upon arrival.
3. **Stage 3 — Percentile Wait Estimation ($p_{50}$ & $p_{90}$):**  
   Evaluates the cumulative wait-time probability $P(T_q > t)$ to extract median ($p_{50}$) and 90th percentile tail ($p_{90}$) delay distributions.
4. **Stage 4 — Invariant Assertion Mesh:**  
   The mathematical invariant ($p_{50} \le p_{90}$) is continuously verified across **728 parameter configurations** ($\lambda \in [0.5, 20]$, $\mu \in [10, 60\text{ min}]$, $c \in [1, 10]$) with **100.0% adherence** and zero boundary violations.

---

### 🧮 Formal Queueing Equations

#### 1. Traffic Intensity ($\rho$)
$$\rho = \frac{\lambda}{c \cdot \mu} \quad (\text{System is stable when } \rho < 1)$$

#### 2. Erlang C Delay Probability ($C(c, a)$)
The exact probability that an arriving vehicle finds all $c$ charging ports occupied and must queue:

$$C(c, a) = \frac{\frac{a^c}{c!} \cdot \frac{1}{1 - \rho}}{\sum_{k=0}^{c-1} \frac{a^k}{k!} + \frac{a^c}{c!} \cdot \frac{1}{1 - \rho}} \quad \text{where } a = \frac{\lambda}{\mu}$$

#### 3. Percentile Wait-Time Invariant ($p_{50} \le p_{90}$)
The cumulative distribution function of waiting time $T_q$ for delayed vehicles yields exact percentiles:

$$P(T_q > t) = C(c, a) \cdot e^{-c\mu(1-\rho)t}$$

$$t_{p} = \max\left(0, \; -\frac{\ln\left(\frac{1 - p}{C(c, a)}\right)}{c\mu(1-\rho)}\right)$$

---

## 🌐 3-Tier Data Provenance & Quality System

<div align="center">
  <img src="https://raw.githubusercontent.com/HARSH0177/EV-spatial-intelligence-Engine/main/assets/data-provenance-matrix.svg?v=2.2" alt="Data Provenance Matrix" width="100%" />
</div>

<br/>

### 🛡️ Data Provenance Tiers & Confidence Scoring

To ensure full transparency and avoid black-box decision making, every returned station and planning zone carries an immutable data quality label:

1. **Tier 1: LIVE (Confidence: 0.95 – 1.00)**  
   Direct ground-truth telemetry from OCPP 1.6 WebSocket servers and active BigQuery port sessions. Captures verified live connector power and real-time charging status.
2. **Tier 2: ESTIMATED (Confidence: 0.70 – 0.94)**  
   Synthesized from spatial API fusion (OpenChargeMap, Google Places, OSM Overpass) and modeled via $M/M/c$ Erlang C queueing theory and Gradient Boosted demand forecasts.
3. **Tier 3: FALLBACK (Confidence: 0.30 – 0.69)**  
   Employs deterministic seeded heuristics when external APIs experience network outages or rate limits. Carries an explicit `fallback_reason` field so users always know what is real vs. inferred.

<br/>

| Source | Integration Role | Data Provenance Label | Fallback Behavior |
|---|---|---|---|
| **Google BigQuery** | Session telemetry & port utilization | `live` / `mock-dev` | Mock local registry |
| **OpenChargeMap** | Global charging stations & power specs | `estimated` | Overpass fallback |
| **Google Places** | Surrounding commercial POI density | `estimated` | OSM amenity fallback |
| **OSM / Overpass** | Parking lots, transit hubs, district polygons | `estimated` | Seeded heuristic |
| **NREL AFDC** | High-density North American stations | `estimated` | Global OCM fallback |
| **OCPP 1.6** | Real-time WebSocket hardware port state | `live` | Queue model estimate |

---

## 📊 Live Evaluation & Benchmark Results

The codebase includes an end-to-end evaluation harness ([`eval/benchmark.py`](eval/benchmark.py)) that executes against live production instances:

```
========================================================================
EV ADVISOR — PRODUCTION BENCHMARK EVALUATION
Target: https://ev-advisor-api-79118074976.us-central1.run.app
========================================================================
  TOTAL CHECKS:  56
  PASSED:        51
  OVERALL SCORE: 91.1% PASS RATE
========================================================================
```

| Evaluation Dimension | Benchmark Metric | Result | Status |
|---|---|---|:---:|
| **API Reliability** | Core endpoint availability across 11 routes | **100.0% (11/11)** | ✅ PASS |
| **Input Validation** | Rejection precision on malformed/fuzzed payloads | **100.0% (10/10 $\rightarrow$ 422)** | ✅ PASS |
| **Geographic Coverage** | Successful live data return across 10 global cities | **100.0% (10/10 cities, 5 continents)** | ✅ PASS |
| **Queue Invariant** | $p_{50} \le p_{90}$ verified over parameter mesh | **100.0% (728/728 configs)** | ✅ PASS |
| **Distance Precision** | Haversine vs. known global city pair ground truth | **99.72% (0.28% avg error)** | ✅ PASS |
| **Data Provenance** | Unlabeled response rate (transparency guarantee) | **0% unlabeled (144/144 tagged)** | ✅ PASS |
| **GeoJSON Compliance** | RFC 7946 spec validity on Point feature collections | **100.0% (5/5 valid)** | ✅ PASS |
| **Discovery Latency** | Median response time across multi-run queries ($p_{50}$) | **880 milliseconds** | ✅ PASS |

---

## 📡 REST API Reference

### 1. Driver Discovery Routes
- `POST /api/search/discover` — Unified multi-modal search (chargers, parking, mobility hubs).
- `POST /api/search/chargers` — Filtered charger discovery with power & connector filters.
- `POST /api/search/parking` — Surrounding parking facility locations.
- `POST /api/search/mobility` — Public transit hubs, bus platforms, bike-share stations.
- `POST /driver/map-data` — GeoJSON `FeatureCollection` for Leaflet/Mapbox rendering.

### 2. Site Selection & Advisor Routes
- `POST /api/advisor/analyze-area` — Full spatial analysis for a target city with ranked zones.
- `POST /api/advisor/rank-zones` — Multi-criteria zone ranking based on budget & power constraints.
- `POST /company/plan-expansion` — Executive expansion planning report with LLM synthesis.

### 3. System & Monitoring
- `GET /health` — Liveness probe (`{"status": "healthy", "version": "2.2.0"}`).
- `GET /ready` — Readiness probe with active provider status and cache telemetry.

---

## 🛠️ Local Development & Quickstart

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/HARSH0177/EV-spatial-intelligence-Engine.git
cd EV-spatial-intelligence-Engine

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and provide your API keys:
```bash
cp .env.example .env
```

```env
GOOGLE_CLOUD_PROJECT=your-project-id
ENABLE_OCM=true
OPENCHARGEMAP_API_KEY=your_ocm_key
ENABLE_OSM_OVERPASS=true
ENABLE_GOOGLE_PLACES=true
GOOGLE_MAPS_API_KEY=your_google_maps_key
NREL_API_KEY=your_nrel_key
LLM_ENABLED=true
```

### 3. Launch Local Server
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```
Open [`http://localhost:8080/app`](http://localhost:8080/app) for the interactive dashboard or [`http://localhost:8080/docs`](http://localhost:8080/docs) for the interactive Swagger UI.

### 4. Run Test Suite
```bash
pytest tests/ -v
```

### 5. Run Production Benchmark
```bash
python eval/benchmark.py
```

---

## 🚢 Google Cloud Run Deployment

The service is fully containerized and deployable via Google Cloud Build & Cloud Run:

```bash
# 1. Build container image via Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ev-advisor:latest .

# 2. Deploy service to Cloud Run
gcloud run deploy ev-advisor-api \
  --image gcr.io/YOUR_PROJECT_ID/ev-advisor:latest \
  --region us-central1 \
  --project YOUR_PROJECT_ID \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1
```

---

## 📂 Repository Structure

```
.
├── assets/                     # Light-theme pastel architectural diagrams & visual assets
│   ├── hero-banner.svg         # High-resolution vector project banner & key metrics
│   ├── architecture-diagram.svg# Complete multi-agent & data fusion pipeline architecture
│   ├── queue-model-flow.svg    # Stochastic Erlang C M/M/c mathematical flow diagram
│   └── data-provenance-matrix.svg # 3-tier data provenance & confidence framework
├── agents/                     # Autonomous multi-agent implementations
│   ├── advisor_agent.py        # Spatial site-selection and zone synthesis
│   ├── data_agent.py           # BigQuery telemetry & port aggregator
│   ├── driver_agent.py         # Real-time search & connector matching
│   ├── explanation_agent.py    # Vertex AI LLM decision synthesizer
│   ├── orchestrator.py         # Multi-agent coordinator
│   └── scoring_agent.py        # Multi-attribute viability scoring
├── api/                        # FastAPI routers, schemas, and endpoints
│   ├── main.py                 # Application bootstrap & middleware
│   ├── routes_advisor.py       # Area planning & zone ranking routes
│   ├── routes_discover.py      # Spatial search & discovery routes
│   └── schemas.py              # Pydantic v2 validation contracts
├── eval/                       # Evaluation framework & benchmark harness
│   ├── benchmark.py            # 56-check production benchmark suite
│   └── README.md               # Benchmark methodology & metrics
├── frontend/                   # Interactive Leaflet.js dashboard UI
│   └── index.html              # Unified 2-in-1 spatial map application
├── llm/                        # Vertex AI Gemini 2.0 Flash integration
│   └── vertex_explainer.py     # Structured prompt generation & synthesis
├── middleware/                 # API security & authentication middleware
│   └── auth.py                 # Role-based API key validation
├── models/                     # Mathematical & predictive models
│   ├── demand_forecaster.py    # Gradient Boosted regressor
│   ├── forecaster_eval.py      # MAE / RMSE forecast evaluation
│   ├── queue_model.py          # M/M/c Erlang C queue equations
│   └── queue_validator.py      # Erlang C mathematical invariant verifier
├── realtime/                   # External API clients & protocol handlers
│   ├── google_places_client.py # Google Places API integration
│   ├── nrel_client.py          # NREL Alternative Fuels Data Center
│   ├── ocpp_central.py         # OCPP 1.6 WebSocket Central System
│   ├── ocpp_simulator.py       # Simulated OCPP charger hardware
│   ├── openchargemap_client.py # OpenChargeMap global API client
│   └── osm_places_client.py    # OpenStreetMap Overpass spatial queries
├── scripts/                    # Deployment & BigQuery bootstrap scripts
├── tests/                      # Pytest unit & integration test suites
├── config.py                   # Centralized Pydantic application config
├── Dockerfile                  # Container definition (Python 3.11-slim)
└── requirements.txt            # Production dependencies
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
