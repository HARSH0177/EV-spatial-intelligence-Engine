"""
PaperBanana 2025/2026 Academic Specification Renderer - Publication Gold Standard
Generates pristine, publication-grade academic diagrams for Elsevier EAAI:
- Figure 1: 4-Layer Autonomous Multi-Agent Decision Support Architecture
- Figure 2: Stochastic M/M/c Erlang C Queueing Flow & Analytic Tail Inversion Pipeline
- Figure 3: 3-Tier Data Provenance Framework & Epistemic Grounding Guardrails
- Figure 4: Comparative Tail Queue Delay (p90) Across Traffic Intensities
- Figure 5: Multi-Attribute Siting Utility vs. Greedy POI Clustering
- Figure 6: Global Metropolitan Scalability & Latency Profiling
"""

import os
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

paper_dir = r"C:\Users\HARSH AMBULE\Downloads\paper"
figures_dir = os.path.join(paper_dir, "figures")
repo_paper_dir = r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper"
repo_figures_dir = os.path.join(repo_paper_dir, "figures")

for d in [figures_dir, repo_paper_dir, repo_figures_dir]:
    os.makedirs(d, exist_ok=True)

plt.rcParams.update({
    'font.size': 9.0,
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Helvetica', 'Arial', 'Liberation Sans'],
    'mathtext.fontset': 'cm',
    'figure.dpi': 300
})


def draw_macro_zone(ax, x, y, w, h, bg_color, border_color, title="", subtitle="", corner_radius=0.035, lw=1.3):
    """Renders a macro-zone container with generous header clearance."""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0.0,rounding_size={corner_radius}",
                         facecolor=bg_color, edgecolor=border_color,
                         linewidth=lw, zorder=1)
    ax.add_patch(box)
    
    if title:
        ax.text(x + 0.25, y + h - 0.22, title, fontsize=10.2, fontweight='bold',
                color='#0F172A', va='top', ha='left', zorder=4)
    if subtitle:
        ax.text(x + 0.25, y + h - 0.46, subtitle, fontsize=8.0, fontstyle='italic',
                color='#475569', va='top', ha='left', zorder=4)


def draw_card(ax, x, y, w, h, header_text, header_color, body_items=None,
              body_bg='#FFFFFF', border_color=None, header_h=0.34, corner_radius=0.025,
              title_fs=8.6, body_fs=7.5, zorder=3):
    """
    Renders an academic card with a solid header bar and mathematically centered body items.
    """
    if border_color is None:
        border_color = header_color

    base = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0.0,rounding_size={corner_radius}",
                          facecolor=body_bg, edgecolor=border_color,
                          linewidth=1.1, zorder=zorder)
    ax.add_patch(base)
    
    header = FancyBboxPatch((x, y + h - header_h), w, header_h,
                            boxstyle=f"round,pad=0.0,rounding_size={corner_radius}",
                            facecolor=header_color, edgecolor=border_color,
                            linewidth=1.0, zorder=zorder + 1)
    ax.add_patch(header)
    
    ax.text(x + w / 2.0, y + h - header_h / 2.0, header_text,
            fontsize=title_fs, fontweight='bold', color='#FFFFFF',
            ha='center', va='center', zorder=zorder + 2)
    
    if body_items:
        body_h = h - header_h
        n = len(body_items)
        step = body_h / (n + 1.0)
        for i, item in enumerate(body_items):
            cy = y + body_h - (i + 1.0) * step
            ax.text(x + w / 2.0, cy, item,
                    fontsize=body_fs, color='#1E293B',
                    ha='center', va='center', zorder=zorder + 2)


def draw_bus_arrow(ax, points, color='#475569', lw=1.3, label="", label_pos=None):
    """Draws an orthogonal multi-segment bus arrow."""
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        is_last = (i == len(points) - 2)
        style = '->' if is_last else '-'
        ax.annotate("", xy=p2, xytext=p1,
                    arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=0, shrinkB=2),
                    zorder=5)
    if label and label_pos:
        ax.text(label_pos[0], label_pos[1], label, fontsize=6.8, color=color, fontweight='bold',
                ha='center', va='center', zorder=6,
                bbox=dict(boxstyle="round,pad=0.16", fc="#FFFFFF", ec=color, lw=0.6, alpha=0.96))


# ==============================================================================
# FIGURE 1: 4-Layer Autonomous Multi-Agent Decision Support Architecture
# ==============================================================================
def render_figure_1_architecture():
    print("Rendering Figure 1 (PaperBanana Architecture Diagram - Gold Standard)...")
    fig, ax = plt.subplots(figsize=(14.6, 10.6), dpi=300)
    ax.set_xlim(0, 14.6)
    ax.set_ylim(0, 10.6)
    ax.axis('off')
    ax.add_patch(Rectangle((0, 0), 14.6, 10.6, facecolor='#FFFFFF', edgecolor='none', zorder=0))

    # Paper Title Header
    ax.text(7.3, 10.32, "EV-Spatial-Intelligence-Engine: Autonomous Multi-Agent Decision Support Architecture",
            fontsize=12.5, fontweight='bold', ha='center', va='top', color='#0F172A', zorder=10)
    ax.text(7.3, 10.02, "Decoupled 4-Layer Production Framework Deployed on Google Cloud Run with Vertex AI Gemini 2.0 Flash",
            fontsize=8.8, fontstyle='italic', ha='center', va='top', color='#64748B', zorder=10)

    # Layer 1: Gateway & UI
    draw_macro_zone(ax, 0.5, 7.75, 13.6, 2.05, bg_color='#F8FAFC', border_color='#94A3B8',
                    title="Layer 1: Client Interface & Asynchronous API Gateway",
                    subtitle="FastAPI asynchronous microservice gateway on Google Cloud Run with Leaflet.js dashboard")
    
    draw_card(ax, 0.8, 7.90, 3.9, 1.15,
              "FastAPI Asynchronous Gateway", '#1D4ED8',
              ["Asynchronous REST & WebSocket routing", "Token bucket rate limiting (500 req/min)", "Strict Pydantic v2 input validation"])
    
    draw_card(ax, 5.3, 7.90, 4.0, 1.15,
              "Interactive Spatial GIS Dashboard", '#0284C7',
              ["Leaflet.js client-side map rendering", "Dynamic isochrone reachability polygons", "Real-time socket telemetry visualization"])
    
    draw_card(ax, 9.9, 7.90, 3.9, 1.15,
              "Operational Dispatch & Shield", '#059669',
              ["Provider deduplication manager", "Circuit breaker & fallback controller", "OCPP 1.6 WebSocket hardware bridge"])

    # Layer 2: Multi-Agent Orchestration Mesh
    draw_macro_zone(ax, 0.5, 4.90, 13.6, 2.55, bg_color='#FAF5FF', border_color='#C084FC',
                    title="Layer 2: Autonomous Multi-Agent Orchestration Mesh",
                    subtitle="Six asynchronous cooperating agents executing non-blocking DAG workflows via asyncio.gather")
    
    agents = [
        ("OrchestratorAgent", '#7C3AED', ["Lifecycle coordinator", "Async DAG dispatch", "Error isolation"], 0.8),
        ("DriverAssistantAgent", '#2563EB', ["Geodesic spatial search", "Radius filter (10 km)", "Connector mapping"], 3.0),
        ("AdvisorAgent", '#0284C7', ["Administrative zoning", "Overpass/Nominatim sync", "Land suitability index"], 5.2),
        ("DataAgent", '#059669', ["BigQuery telemetry lake", "OCPP 1.6 WebSocket sync", "Hardware status polling"], 7.4),
        ("ScoringAgent", '#D97706', ["Multi-attribute matrix", "Constraint weights (sum=1)", "Pareto site ranking"], 9.6),
        ("ExplanationAgent", '#DC2626', ["Vertex AI Gemini Flash", "Provenance-grounded text", "Zero-fabrication hedging"], 11.8)
    ]
    
    for name, col, desc, px in agents:
        draw_card(ax, px, 5.08, 1.90, 1.55, name, col, desc, header_h=0.33, title_fs=8.2, body_fs=7.3)

    # Horizontal Agent Workflow Arrows
    for px in [2.70, 4.90, 7.10, 9.30, 11.50]:
        ax.annotate("", xy=(px + 0.30, 5.85), xytext=(px, 5.85),
                    arrowprops=dict(arrowstyle='->', color='#7C3AED', lw=1.3), zorder=6)

    # Layer 3: Mathematical & Predictive Core
    draw_macro_zone(ax, 0.5, 2.45, 13.6, 2.15, bg_color='#F0FDF4', border_color='#86EFAC',
                    title="Layer 3: Stochastic Mathematical Modeling & Invariant Verification Core",
                    subtitle="Analytical M/M/c queueing solver and LightGBM demand forecaster with verified ordering invariant")
    
    draw_card(ax, 0.8, 2.60, 3.9, 1.25,
              r"M/M/c Erlang C Queue Solver", '#047857',
              [r"Arrival $\lambda$ (Poisson), Service $\mu$ (Exp), $c$ ports",
               r"Delay Probability: $C(c, a) = [a^c / c!(1-\rho)] / \sum \dots$",
               r"Tail Percentile: $p_{90} = -\ln(0.10/C)/[c\mu(1-\rho)]$"])
    
    draw_card(ax, 5.3, 2.60, 4.0, 1.25,
              "Predictive Demand Forecaster (GBT)", '#0F766E',
              ["Gradient Boosted Decision Trees (LightGBM)",
               "Spatial features: POI density, traffic, amenities",
               "Cold-start charging demand & port utilization"])
    
    draw_card(ax, 9.9, 2.60, 3.9, 1.25,
              r"Automated Invariant Verification Mesh", '#B45309',
              [r"Theorem 1: $t_{0.50} \leq t_{0.90}$ guaranteed for $\rho < 1$",
               "728-regime full factorial parameter sweep",
               "100.0% adherence (0 violations detected)"])

    # Layer 4: Data Fusion Layer
    draw_macro_zone(ax, 0.5, 0.40, 13.6, 1.75, bg_color='#FFFBEB', border_color='#FDE68A',
                    title="Layer 4: Heterogeneous Spatial Data Fusion & Ingestion Layer",
                    subtitle="Multi-provider ingestion with Haversine distance deduplication (Delta d < 50 m)")
    
    sources = [
        ("OpenChargeMap", '#D97706', ["Global crowdsourced POIs", "Connector plug taxonomy"], 0.8),
        ("OpenStreetMap / Overpass", '#2563EB', ["Road network graph topology", "Commercial amenity counts"], 3.45),
        ("Google Places / AFDC", '#059669', ["Commercial place verification", "US DOE alternative fuels"], 6.10),
        ("BigQuery Telemetry", '#7C3AED', ["Historical charge sessions", "District utilization profiles"], 8.75),
        ("OCPP 1.6 WebSockets", '#DC2626', ["Real-time socket power state", "Active voltage & amperage"], 11.40)
    ]
    for name, col, desc, sx in sources:
        draw_card(ax, sx, 0.52, 2.45, 0.95, name, col, desc, header_h=0.30, title_fs=7.9, body_fs=7.1)

    # Inter-Layer Bus Connectors
    draw_bus_arrow(ax, [(2.75, 7.90), (2.75, 7.45)], color='#1D4ED8', lw=1.3,
                   label="Client Query", label_pos=(2.75, 7.68))
    
    draw_bus_arrow(ax, [(3.95, 5.08), (3.95, 4.75), (2.75, 4.75), (2.75, 3.85)],
                   color='#047857', lw=1.3, label=r"Arrival $\lambda$, Service $\mu$", label_pos=(3.35, 4.75))
    
    draw_bus_arrow(ax, [(2.75, 2.60), (2.75, 2.30), (14.25, 2.30), (14.25, 5.85), (13.70, 5.85)],
                   color='#DC2626', lw=1.3, label=r"Tail Delays $p_{50}, p_{90}$", label_pos=(14.25, 4.05))
    
    draw_bus_arrow(ax, [(9.95, 1.47), (9.95, 1.85), (9.60, 1.85), (9.60, 4.75), (8.35, 4.75), (8.35, 5.08)],
                   color='#7C3AED', lw=1.3, label="Live Hardware Telemetry", label_pos=(9.60, 2.30))

    pdf_path = os.path.join(figures_dir, "architecture-diagram.pdf")
    png_path = os.path.join(figures_dir, "architecture-diagram.png")
    fig.savefig(pdf_path, format='pdf', bbox_inches='tight')
    fig.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Figure 1 rendered in Gold Standard.")


# ==============================================================================
# FIGURE 2: Stochastic M/M/c Erlang C Queueing Flow & Percentile Derivation
# ==============================================================================
def render_figure_2_queue_flow():
    print("Rendering Figure 2 (PaperBanana Queue Model Flow - Gold Standard)...")
    fig, ax = plt.subplots(figsize=(14.0, 6.4), dpi=300)
    ax.set_xlim(0, 14.0)
    ax.set_ylim(0, 6.4)
    ax.axis('off')
    ax.add_patch(Rectangle((0, 0), 14.0, 6.4, facecolor='#FFFFFF', edgecolor='none', zorder=0))

    # Header
    ax.text(7.0, 6.12, r"Stochastic $M/M/c$ Erlang C Formulation & Analytic Tail Wait-Time Inversion Pipeline",
            fontsize=12.2, fontweight='bold', ha='center', va='top', color='#0F172A')
    ax.text(7.0, 5.82, r"Continuous Markov Chain Birth-Death Modeling $\rightarrow$ Erlang C Delay Probability $\rightarrow$ Invariant Order $t_{0.50} \leq t_{0.90}$",
            fontsize=8.6, fontstyle='italic', ha='center', va='top', color='#475569')

    # Stage 1: Input Ingestion
    draw_macro_zone(ax, 0.5, 0.45, 2.9, 5.1, bg_color='#EFF6FF', border_color='#93C5FD',
                    title="1. Parameter Ingestion", subtitle="Station Hardware & Traffic")
    draw_card(ax, 0.7, 3.45, 2.5, 1.45,
              "Operational Rates", '#1D4ED8',
              [r"Arrival rate: $\lambda\ \mathrm{(veh/h)}$",
               r"Service rate: $\mu\ \mathrm{(veh/h/port)}$",
               r"Mean duration: $1/\mu\ \mathrm{(min)}$"])
    draw_card(ax, 0.7, 1.85, 2.5, 1.45,
              "Station Topology", '#1D4ED8',
              [r"Port capacity: $c \in \mathbb{N}^+$",
               r"Offered load: $a = \lambda / \mu$",
               r"Intensity: $\rho = \frac{\lambda}{c\cdot\mu} < 1$"])
    draw_card(ax, 0.7, 0.65, 2.5, 1.05,
              "Stability Condition", '#1E40AF',
              [r"$\rho < 1.0 \Rightarrow \mathrm{Ergodic}$",
               "Prevents infinite queueing"])

    # Stage 2: Erlang C Probability
    draw_macro_zone(ax, 3.8, 0.45, 3.1, 5.1, bg_color='#F5F3FF', border_color='#C4B5FD',
                    title="2. Erlang C Congestion", subtitle="Analytical State Solution")
    draw_card(ax, 4.0, 3.35, 2.7, 1.55,
              "Queue Probability", '#6D28D9',
              [r"$P(\mathrm{Queue}) = C(c, a)$",
               r"$C(c, a) = \frac{\frac{a^c}{c!(1-\rho)}}{\sum_{k=0}^{c-1}\frac{a^k}{k!} + \frac{a^c}{c!(1-\rho)}}$",
               "Exact closed-form expression"])
    draw_card(ax, 4.0, 1.25, 2.7, 1.85,
              "Waiting Time CDF", '#6D28D9',
              [r"$W_q \sim \mathrm{Queue\ Wait\ Time}$",
               r"$P(W_q \leq t) = 1 - C(c, a)e^{-c\mu(1-\rho)t}$",
               r"$t \geq 0 \quad (\mathrm{Point\ mass\ at\ } t=0)$",
               r"$P(W_q = 0) = 1 - C(c, a)$"])

    # Stage 3: Analytic Inversion
    draw_macro_zone(ax, 7.3, 0.45, 3.1, 5.1, bg_color='#ECFDF5', border_color='#A7F3D0',
                    title="3. Percentile Inversion", subtitle="Analytic Tail Calculation")
    draw_card(ax, 7.5, 3.35, 2.7, 1.55,
              r"Tail Percentile $t_p$", '#047857',
              [r"$1 - C\cdot e^{-c\mu(1-\rho)t_p} = p$",
               r"$t_p = \max\left(0, -\frac{\ln\left(\frac{1-p}{C(c,a)}\right)}{c\mu(1-\rho)}\right)$",
               "Eliminates simulation overhead"])
    draw_card(ax, 7.5, 1.25, 2.7, 1.85,
              "Operational Targets", '#047857',
              [r"Median: $p_{50} = \max\left(0, \frac{\ln(2C)}{c\mu(1-\rho)}\right)$",
               r"Tail: $p_{90} = \max\left(0, \frac{\ln(10C)}{c\mu(1-\rho)}\right)$",
               "Tail wait time drives driver churn",
               "Captures peak congestion delays"])

    # Stage 4: Invariant Proof & Grounding
    draw_macro_zone(ax, 10.8, 0.45, 2.7, 5.1, bg_color='#FFFBEB', border_color='#FDE68A',
                    title="4. Invariant Ordering", subtitle="Monotonicity & Delivery")
    draw_card(ax, 11.0, 3.25, 2.3, 1.65,
              "Theorem 1 Invariant", '#B45309',
              [r"$\forall \rho < 1 : t_{0.50} \leq t_{0.90}$",
               r"Case 1: $C \leq 0.10 \Rightarrow 0 \leq 0$",
               r"Case 2: $0.10 < C \leq 0.50 \Rightarrow 0 < t_{90}$",
               r"Case 3: $C > 0.50 \Rightarrow \ln 2C < \ln 10C$",
               "Proven unconditionally"])
    draw_card(ax, 11.0, 0.85, 2.3, 2.15,
              "Downstream Delivery", '#0369A1',
              ["Provenance Tag: ESTIMATED",
               "728 Regimes Verified",
               "0 Invariant Violations",
               "Feeds ExplanationAgent",
               "DES Ground Truth MAE: 9.39 min"])

    # Inter-stage arrows
    draw_bus_arrow(ax, [(3.4, 4.15), (4.0, 4.15)], color='#1D4ED8', lw=1.3,
                   label=r"Load $a, \rho$", label_pos=(3.7, 4.35))
    draw_bus_arrow(ax, [(6.7, 4.15), (7.5, 4.15)], color='#6D28D9', lw=1.3,
                   label=r"CDF $P(W_q \leq t)$", label_pos=(7.1, 4.35))
    draw_bus_arrow(ax, [(10.2, 4.15), (11.0, 4.15)], color='#047857', lw=1.3,
                   label=r"$p_{50}, p_{90}$", label_pos=(10.6, 4.35))

    pdf_path = os.path.join(figures_dir, "queue-model-flow.pdf")
    png_path = os.path.join(figures_dir, "queue-model-flow.png")
    fig.savefig(pdf_path, format='pdf', bbox_inches='tight')
    fig.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Figure 2 rendered in Gold Standard.")


# ==============================================================================
# FIGURE 3: Three-Tier Data Provenance & Grounding Matrix
# ==============================================================================
def render_figure_3_provenance():
    print("Rendering Figure 3 (PaperBanana Provenance Architecture Matrix - Gold Standard)...")
    fig, ax = plt.subplots(figsize=(14.8, 7.0), dpi=300)
    ax.set_xlim(0, 14.8)
    ax.set_ylim(0, 7.0)
    ax.axis('off')
    ax.add_patch(Rectangle((0, 0), 14.8, 7.0, facecolor='#FFFFFF', edgecolor='none', zorder=0))

    # Header
    ax.text(7.4, 6.72, "3-Tier Data Provenance Framework & Epistemic Grounding Guardrails",
            fontsize=12.2, fontweight='bold', ha='center', va='top', color='#0F172A')
    ax.text(7.4, 6.42, "Immutable Confidence Scoring and Fallback Contracts Guiding Natural Language Explanation",
            fontsize=8.6, fontstyle='italic', ha='center', va='top', color='#475569')

    # Tier 1: LIVE (x: 0.60 to 4.55, w: 3.95)
    draw_macro_zone(ax, 0.60, 0.45, 3.95, 5.6, bg_color='#F0FDF4', border_color='#86EFAC',
                    title="Tier 1: LIVE DATA", subtitle="Direct Hardware & Telemetry Sync")
    draw_card(ax, 0.80, 4.30, 3.55, 1.05,
              "Confidence Score: 0.95 - 1.00", '#15803D',
              ["Highest reliability tier;",
               "zero statistical estimation"],
              body_bg='#F0FDF4', title_fs=9.0, body_fs=7.6)
    draw_card(ax, 0.80, 2.45, 3.55, 1.65,
              "Upstream Telemetry Sources", '#16A34A',
              ["Active OCPP 1.6 WebSocket telemetry",
               "BigQuery verified session transaction lake",
               "Real-time connector voltage & amperage readings"],
              title_fs=8.6, body_fs=7.5)
    draw_card(ax, 0.80, 0.65, 3.55, 1.60,
              "LLM Explanation Protocol", '#16A34A',
              ["Unrestricted factual assertions allowed",
               "Direct statements of current socket occupancy",
               "Example: 'Port 2 is active at 120 kW'"],
              title_fs=8.6, body_fs=7.5)

    # Tier 2: ESTIMATED (x: 5.42 to 9.37, w: 3.95)
    draw_macro_zone(ax, 5.42, 0.45, 3.95, 5.6, bg_color='#EFF6FF', border_color='#93C5FD',
                    title="Tier 2: ESTIMATED DATA", subtitle="Multi-Source Geo Fusion & Predictive Models")
    draw_card(ax, 5.62, 4.30, 3.55, 1.05,
              "Confidence Score: 0.70 - 0.94", '#1D4ED8',
              ["Statistical & analytical inference",
               "with verified ordering invariants"],
              body_bg='#EFF6FF', title_fs=9.0, body_fs=7.6)
    draw_card(ax, 5.62, 2.45, 3.55, 1.65,
              "Predictive & Fusion Sources", '#2563EB',
              ["Multi-API spatial fusion (OCM + OSM + NREL)",
               "Stochastic M/M/c Erlang C queueing solver",
               "Gradient Boosted Tree cold-start demand regressor"],
              title_fs=8.6, body_fs=7.5)
    draw_card(ax, 5.62, 0.65, 3.55, 1.60,
              "LLM Explanation Protocol", '#2563EB',
              ["Mandatory probabilistic qualification",
               "Disclose statistical percentiles (p50 / p90)",
               "Example: 'Projected wait time: 8.3 min (p90)'"],
              title_fs=8.6, body_fs=7.5)

    # Tier 3: FALLBACK (x: 10.25 to 14.20, w: 3.95)
    draw_macro_zone(ax, 10.25, 0.45, 3.95, 5.6, bg_color='#FEF2F2', border_color='#FCA5A5',
                    title="Tier 3: FALLBACK ESTIMATOR", subtitle="Graceful Degradation Under Outages")
    draw_card(ax, 10.45, 4.30, 3.55, 1.05,
              "Confidence Score: 0.30 - 0.69", '#B91C1C',
              ["Outage fallback activated;",
               "regional capacity priors"],
              body_bg='#FEF2F2', title_fs=9.0, body_fs=7.6)
    draw_card(ax, 10.45, 2.45, 3.55, 1.65,
              "Fallback Estimation Sources", '#DC2626',
              ["Deterministic regional baseline estimators",
               "Historical municipal district capacity priors",
               "Structured fallback_reason error contracts"],
              title_fs=8.6, body_fs=7.5)
    draw_card(ax, 10.45, 0.65, 3.55, 1.60,
              "LLM Explanation Protocol", '#DC2626',
              ["Strict epistemic hedging required",
               "Prohibits presenting estimates as live ground truth",
               "Example: 'Live status offline; default regional avg'"],
              title_fs=8.6, body_fs=7.5)

    # Degradation bus arrows placed cleanly in the whitespace gap between Card 1s
    draw_bus_arrow(ax, [(4.55, 4.82), (5.42, 4.82)], color='#2563EB', lw=1.3,
                   label="Telemetry\nInactive", label_pos=(4.985, 4.82))
    draw_bus_arrow(ax, [(9.37, 4.82), (10.25, 4.82)], color='#DC2626', lw=1.3,
                   label="API Outage\n/ Timeout", label_pos=(9.81, 4.82))

    pdf_path = os.path.join(figures_dir, "data-provenance-matrix.pdf")
    png_path = os.path.join(figures_dir, "data-provenance-matrix.png")
    fig.savefig(pdf_path, format='pdf', bbox_inches='tight')
    fig.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Figure 3 rendered in Gold Standard.")


# ==============================================================================
# FIGURE 4: Comparative Tail Queue Delay Curves (Proposed vs Baselines)
# ==============================================================================
def render_figure_4_queue_comparison():
    print("Rendering Figure 4 (Queue Delay Curves)...")
    fig, ax = plt.subplots(figsize=(8.2, 4.8), dpi=300)

    rhos = np.array([0.25, 0.50, 0.69, 0.81, 0.90])
    sim_gt = np.array([0.00, 7.84, 31.56, 62.05, 121.47])
    proposed_mmc = np.array([0.00, 8.30, 33.83, 72.92, 154.80])
    lumped_mm1 = np.array([5.76, 17.27, 37.99, 74.83, 155.42])
    static_heur = np.array([15.00, 15.00, 15.00, 15.00, 15.00])

    ax.plot(rhos, sim_gt, 'o-', color='#1B5E20', linewidth=2.4, markersize=8,
            label='Simulation Ground Truth (25k sessions)', zorder=5)
    ax.plot(rhos, proposed_mmc, 's--', color='#0D47A1', linewidth=2.0, markersize=7,
            label='Proposed M/M/c Erlang C (MAE: 9.39 min, RMSE: 15.72 min)', zorder=4)
    ax.plot(rhos, lumped_mm1, '^-.', color='#C62828', linewidth=1.8, markersize=7,
            label='Lumped M/M/1 Baseline (MAE: 13.67 min, RMSE: 17.21 min)', zorder=3)
    ax.plot(rhos, static_heur, 'd:', color='#546E7A', linewidth=1.5, markersize=6,
            label='Static 15-min Baseline (MAE: 38.45 min, RMSE: 53.10 min)', zorder=2)

    ax.set_xlabel(r'Traffic Intensity ($\rho = \lambda / (c\cdot\mu)$)', fontweight='bold')
    ax.set_ylabel(r'90th Percentile Wait Time $p_{90}$ (minutes)', fontweight='bold')
    ax.set_title(r'Comparative Tail Queue Delay ($p_{90}$) across Traffic Intensities ($c=4$ ports, $\mu=2.0$)',
                 pad=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlim(0.2, 0.95)
    ax.set_ylim(-5, 175)
    ax.legend(frameon=True, facecolor='#FAFAFA', edgecolor='#D0D0D0', loc='upper left')
    plt.tight_layout()

    fig4_pdf = os.path.join(figures_dir, "fig_queue_comparison.pdf")
    fig4_png = os.path.join(figures_dir, "fig_queue_comparison.png")
    fig.savefig(fig4_pdf, format='pdf', bbox_inches='tight')
    fig.savefig(fig4_png, format='png', dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(figures_dir, "fig4_queue_comparison.png"), format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Figure 4 rendered in Gold Standard.")


# ==============================================================================
# FIGURE 5: Siting Sensitivity (4 Independent Panels)
# ==============================================================================
def render_figure_5_siting():
    print("Rendering Figure 5 (Multi-Attribute Siting Utility)...")
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(14, 3.8), dpi=300)

    labels = ['Greedy POI', 'Proposed']
    colors = ['#90A4AE', '#2E7D32']

    # Panel 1: Grid Headroom (kW)
    vals1 = [350.1, 410.5]
    ax1.bar(labels, vals1, color=colors, width=0.52, edgecolor='#37474F')
    ax1.set_ylabel('Capacity (kW)', fontweight='bold')
    ax1.set_title('Grid Headroom\n(+17.3%)', fontweight='bold', pad=8)
    ax1.set_ylim(0, 490)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    for i, v in enumerate(vals1):
        ax1.text(i, v + 10, f"{v:.1f} kW", ha='center', fontweight='bold', fontsize=9.5)

    # Panel 2: Competitor Overlap (count)
    vals2 = [3.4, 2.2]
    ax2.bar(labels, vals2, color=['#90A4AE', '#0288D1'], width=0.52, edgecolor='#37474F')
    ax2.set_ylabel('Stations (within 1.5 km)', fontweight='bold')
    ax2.set_title('Competitor Overlap\n(-35.3%)', fontweight='bold', pad=8)
    ax2.set_ylim(0, 4.4)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    for i, v in enumerate(vals2):
        ax2.text(i, v + 0.1, f"{v:.1f}", ha='center', fontweight='bold', fontsize=9.5)

    # Panel 3: Composite Viability Score (0-1)
    vals3 = [0.339, 0.394]
    ax3.bar(labels, vals3, color=['#90A4AE', '#7B1FA2'], width=0.52, edgecolor='#37474F')
    ax3.set_ylabel('Index (0 - 1)', fontweight='bold')
    ax3.set_title('Composite Score\n(+16.1%)', fontweight='bold', pad=8)
    ax3.set_ylim(0, 0.48)
    ax3.grid(axis='y', linestyle='--', alpha=0.5)
    for i, v in enumerate(vals3):
        ax3.text(i, v + 0.012, f"{v:.3f}", ha='center', fontweight='bold', fontsize=9.5)

    # Panel 4: Installation CapEx (USD)
    vals4 = [96435, 87393]
    ax4.bar(labels, vals4, color=['#90A4AE', '#E65100'], width=0.52, edgecolor='#37474F')
    ax4.set_ylabel('Cost (USD $)', fontweight='bold')
    ax4.set_title('Installation CapEx\n(-9.4%)', fontweight='bold', pad=8)
    ax4.set_ylim(0, 115000)
    ax4.grid(axis='y', linestyle='--', alpha=0.5)
    for i, v in enumerate(vals4):
        ax4.text(i, v + 2500, f"${v:,.0f}", ha='center', fontweight='bold', fontsize=9.5)

    plt.suptitle('Multi-Attribute Siting Utility vs. Greedy POI Clustering (Controlled Synthetic Analysis)',
                 fontsize=12.0, fontweight='bold', y=1.03)
    plt.tight_layout()

    fig5_pdf = os.path.join(figures_dir, "fig_siting_synthetic.pdf")
    fig5_png = os.path.join(figures_dir, "fig_siting_synthetic.png")
    fig.savefig(fig5_pdf, format='pdf', bbox_inches='tight')
    fig.savefig(fig5_png, format='png', dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(figures_dir, "fig5_siting_tradeoffs.png"), format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Figure 5 rendered in Gold Standard.")


# ==============================================================================
# FIGURE 6: Global Metropolitan Generalization & Latency Profiling
# ==============================================================================
def render_figure_6_latency():
    print("Rendering Figure 6 (Global Metropolitan Latency Profiling)...")
    cities = [
        ("San Francisco (N. America)", 840, '#66BB6A'),
        ("Dubai (Middle East)", 850, '#66BB6A'),
        ("Pune (Asia)", 860, '#66BB6A'),
        ("Berlin (Europe)", 870, '#42A5F5'),
        ("Nagpur (Asia)", 875, '#42A5F5'),
        ("Bengaluru (Asia)", 880, '#42A5F5'),
        ("London (Europe)", 890, '#42A5F5'),
        ("São Paulo (S. America)", 905, '#AB47BC'),
        ("Tokyo (Asia)", 910, '#AB47BC'),
        ("Nairobi (Africa)", 920, '#AB47BC')
    ]

    names = [c[0] for c in cities]
    lats = [c[1] for c in cities]
    colors = [c[2] for c in cities]

    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=300)
    y_pos = np.arange(len(names))

    bars = ax.barh(y_pos, lats, height=0.60, color=colors, edgecolor='#37474F', linewidth=0.9, zorder=3)
    
    # 880 ms median reference line
    median_val = 880
    ax.axvline(x=median_val, color='#D32F2F', linestyle='--', linewidth=1.5,
               label=f'Median Across All Runs ($p_{{50}} = {median_val}$ ms)', zorder=4)

    # Position text cleanly
    for i, v in enumerate(lats):
        if v <= median_val:
            ax.text(v - 12, i, f"{v} ms", va='center', ha='right', fontweight='bold', fontsize=9.0, color='#FFFFFF', zorder=5)
        else:
            ax.text(v + 8, i, f"{v} ms", va='center', ha='left', fontweight='bold', fontsize=9.0, color='#1E293B', zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9.5)
    ax.set_xlabel(r'Median Response Latency $p_{50}$ (milliseconds)', fontweight='bold', fontsize=10.5)
    ax.set_title('Global Metropolitan Scalability & Sub-Second Latency (Google Cloud Run)',
                 fontweight='bold', fontsize=11.2, pad=12)
    ax.set_xlim(700, 1030)
    ax.grid(axis='x', linestyle='--', alpha=0.5, zorder=1)
    
    ax.legend(frameon=True, facecolor='#FAFAFA', edgecolor='#D0D0D0', loc='lower right', fontsize=9.2)
    plt.tight_layout()

    fig6_pdf = os.path.join(figures_dir, "fig6_global_latency.pdf")
    fig6_png = os.path.join(figures_dir, "fig6_global_latency.png")
    fig.savefig(fig6_pdf, format='pdf', bbox_inches='tight')
    fig.savefig(fig6_png, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Figure 6 rendered in Gold Standard.")


def synchronize_all_assets():
    all_files = [
        "architecture-diagram.pdf", "architecture-diagram.png",
        "queue-model-flow.pdf", "queue-model-flow.png",
        "data-provenance-matrix.pdf", "data-provenance-matrix.png",
        "fig1_architecture.png", "fig2_queue_flow.png", "fig3_data_provenance.png",
        "fig_queue_comparison.pdf", "fig_queue_comparison.png", "fig4_queue_comparison.png",
        "fig_siting_synthetic.pdf", "fig_siting_synthetic.png", "fig5_siting_tradeoffs.png",
        "fig6_global_latency.pdf", "fig6_global_latency.png"
    ]
    
    # Aliases
    shutil.copyfile(os.path.join(figures_dir, "architecture-diagram.png"), os.path.join(figures_dir, "fig1_architecture.png"))
    shutil.copyfile(os.path.join(figures_dir, "queue-model-flow.png"), os.path.join(figures_dir, "fig2_queue_flow.png"))
    shutil.copyfile(os.path.join(figures_dir, "data-provenance-matrix.png"), os.path.join(figures_dir, "fig3_data_provenance.png"))

    for fname in all_files:
        src = os.path.join(figures_dir, fname)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(paper_dir, fname))
            shutil.copyfile(src, os.path.join(repo_paper_dir, fname))
            shutil.copyfile(src, os.path.join(repo_figures_dir, fname))
    
    print("All PaperBanana academic figures successfully rendered and synchronized.")


if __name__ == "__main__":
    render_figure_1_architecture()
    render_figure_2_queue_flow()
    render_figure_3_provenance()
    render_figure_4_queue_comparison()
    render_figure_5_siting()
    render_figure_6_latency()
    synchronize_all_assets()
