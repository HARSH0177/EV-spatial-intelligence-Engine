import os
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_redesigned_fig1():
    # Publication-grade typography and canvas setup
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
        'mathtext.fontset': 'dejavuserif',
        'axes.edgecolor': '#94A3B8',
        'figure.dpi': 300
    })

    fig = plt.figure(figsize=(16.5, 10.2), facecolor='#FFFFFF')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16.5)
    ax.set_ylim(0, 10.2)
    ax.axis('off')

    # Color Palette: Soft Tech & Scientific Pastels (PaperBanana 2025/2026 Academic Standard)
    C_BG_INGEST = "#F8FAFC"      # Slate white
    C_BORDER_INGEST = "#CBD5E1"
    C_BG_AGENT = "#F5F3FF"       # Soft Lavender
    C_BORDER_AGENT = "#DDD6FE"
    C_BG_MATH = "#F0FDF4"        # Soft Mint
    C_BORDER_MATH = "#BBF7D0"
    C_BG_LLM = "#FEF2F2"         # Soft Coral
    C_BORDER_LLM = "#FECACA"
    C_BG_CLIENT = "#F0F9FF"      # Soft Sky
    C_BORDER_CLIENT = "#BAE6FD"

    # Deep Accent Colors
    ACCENT_BLUE = "#1E40AF"
    ACCENT_PURPLE = "#6D28D9"
    ACCENT_GREEN = "#047857"
    ACCENT_RED = "#B91C1C"
    ACCENT_TEAL = "#0F766E"
    ACCENT_AMBER = "#B45309"
    ACCENT_SLATE = "#334155"

    def draw_card(x, y, w, h, bg, border, radius=0.25, lw=1.2, ls='-'):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=radius),
            facecolor=bg, edgecolor=border, linewidth=lw, linestyle=ls, zorder=2
        )
        ax.add_patch(box)
        return box

    def draw_header_banner(x, y, w, h, bg_color, text, text_color="#FFFFFF", font_size=9.5):
        banner = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.18),
            facecolor=bg_color, edgecolor=bg_color, linewidth=0.8, zorder=3
        )
        ax.add_patch(banner)
        ax.text(x + w/2, y + h/2, text, color=text_color, fontsize=font_size,
                fontweight='bold', ha='center', va='center', zorder=4)

    # =========================================================================
    # MAIN TITLE & SUBTITLE
    # =========================================================================
    ax.text(8.25, 9.85, "EV-Spatial-Intelligence-Engine: Autonomous Multi-Agent Decision Architecture",
            fontsize=15.5, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(8.25, 9.58, "Decoupled Asynchronous Coordination Mesh with Stochastic M/M/c Queueing Solvers and Epistemic Provenance Guardrails",
            fontsize=10.5, fontstyle='italic', ha='center', va='center', color='#475569')

    # =========================================================================
    # 1. LEFT ZONE: HETEROGENEOUS INGESTION & HARDWARE TELEMETRY
    # =========================================================================
    draw_card(0.5, 0.6, 3.4, 8.6, C_BG_INGEST, C_BORDER_INGEST, radius=0.35, lw=1.5)
    draw_header_banner(0.65, 8.80, 3.1, 0.35, ACCENT_SLATE, "1. HETEROGENEOUS DATA FUSION")

    sources = [
        ("OpenChargeMap API", "Global POI Registry (35k+ plugs)\nTaxonomy & connector standard normalization", "#2563EB", 7.65),
        ("OpenStreetMap Overpass", "Urban road network graph topology\nCommercial retail & amenity densities", "#0284C7", 6.45),
        ("NREL Alternative Fuels", "US DOE verified DCFC hubs\nFederal network compliance schemas", "#0D9488", 5.25),
        ("BigQuery Telemetry Lake", "Historical charge session intervals\nDistrict utilization & diurnal patterns", "#7C3AED", 4.05),
        ("OCPP 1.6 WebSocket Server", "Direct bidirectional hardware link\nLive port occupancy, voltage & kW", "#DC2626", 2.85),
    ]
    for title, desc, col, y_pos in sources:
        draw_card(0.65, y_pos, 3.1, 1.0, "#FFFFFF", col, radius=0.18, lw=1.0)
        draw_header_banner(0.65, y_pos + 0.68, 3.1, 0.32, col, title, font_size=8.5)
        ax.text(2.20, y_pos + 0.34, desc, fontsize=7.6, ha='center', va='center', color='#334155', linespacing=1.2)

    # Spatial Deduplication Module
    draw_card(0.65, 0.8, 3.1, 1.85, "#EFF6FF", "#3B82F6", radius=0.22, lw=1.2)
    draw_header_banner(0.65, 2.30, 3.1, 0.35, ACCENT_BLUE, "Spatial Deduplication Engine")
    ax.text(2.20, 1.55, "Haversine Distance Clustering\nThreshold: Δd < 50 meters\nResolves duplicate cross-API records\ninto unified station entities",
            fontsize=7.8, ha='center', va='center', color='#1E293B', linespacing=1.25)

    # =========================================================================
    # 2. CENTER-UPPER ZONE: AUTONOMOUS MULTI-AGENT ORCHESTRATION MESH
    # =========================================================================
    draw_card(4.2, 4.45, 7.8, 4.75, C_BG_AGENT, C_BORDER_AGENT, radius=0.35, lw=1.5)
    draw_header_banner(4.35, 8.82, 7.5, 0.33, ACCENT_PURPLE, "2. AUTONOMOUS MULTI-AGENT COORDINATION MESH (asyncio.gather DAG)")

    # Master Orchestrator at Top Center of Mesh
    draw_card(6.35, 7.35, 3.5, 1.30, "#FFFFFF", ACCENT_PURPLE, radius=0.22, lw=1.5)
    draw_header_banner(6.35, 8.32, 3.5, 0.33, ACCENT_PURPLE, "OrchestratorAgent (Coordinator)")
    ax.text(8.10, 7.82, "End-to-End Workflow DAG Dispatcher\nParallel Task Distribution • Request Lifecycle Tracking\nCircuit Breaker & Fallback Handler",
            fontsize=7.8, ha='center', va='center', color='#334155', linespacing=1.2)

    # 3 Parallel Worker Agents in middle tier
    agents = [
        ("DriverAssistantAgent", "Geodesic radius search (10 km)\nConnector & power taxonomy\nBattery SOC filtering", "#2563EB", 4.45, 5.75, 2.3, 1.30),
        ("AdvisorAgent", "Administrative zoning lookup\nOverpass / Nominatim sync\nLand suitability index", "#0284C7", 6.95, 5.75, 2.3, 1.30),
        ("DataAgent", "Hardware WebSocket polling\nBigQuery session queries\nLive cache synchronization", "#059669", 9.45, 5.75, 2.3, 1.30),
    ]
    for name, desc, col, x_pos, y_pos, w, h in agents:
        draw_card(x_pos, y_pos, w, h, "#FFFFFF", col, radius=0.18, lw=1.1)
        draw_header_banner(x_pos, y_pos + h - 0.30, w, 0.30, col, name, font_size=8.0)
        ax.text(x_pos + w/2, y_pos + 0.48, desc, fontsize=7.4, ha='center', va='center', color='#334155', linespacing=1.2)

    # Arrows from Orchestrator to Workers
    for tx in [5.6, 8.1, 10.6]:
        ax.annotate('', xy=(tx, 7.05), xytext=(tx, 7.35),
                    arrowprops=dict(arrowstyle="-|>", color=ACCENT_PURPLE, lw=1.4, mutation_scale=11))

    # Subtle aggregation arrows from Workers to ScoringAgent
    for wx in [5.6, 8.1, 10.6]:
        ax.annotate('', xy=(wx, 5.50), xytext=(wx, 5.75),
                    arrowprops=dict(arrowstyle="-|>", color=ACCENT_AMBER, lw=1.1, linestyle=":", mutation_scale=9))

    # Scoring Agent (Aggregator in Agent Mesh - Widened with ample margins & 2-line layout)
    draw_card(4.65, 4.58, 6.9, 0.92, "#FFFFFF", ACCENT_AMBER, radius=0.18, lw=1.2)
    draw_header_banner(4.65, 5.18, 6.9, 0.32, ACCENT_AMBER, "ScoringAgent: Multi-Attribute Utility Optimization", font_size=8.3)
    ax.text(8.10, 4.96, r"Utility Formulation: $U(s) = \sum w_i f_i(s)$ with Normalized Weights $\sum w_i = 1.0$",
            fontsize=7.4, ha='center', va='center', color='#1E293B')
    ax.text(8.10, 4.74, "Grid Headroom (+17.3%)  •  Competitor Saturation (-35.3%)  •  CapEx (-9.4%)",
            fontsize=7.2, fontweight='semibold', ha='center', va='center', color='#475569')

    # =========================================================================
    # 3. CENTER-LOWER ZONE: STOCHASTIC MATHEMATICAL & PREDICTIVE CORE
    # =========================================================================
    draw_card(4.2, 0.6, 7.8, 3.55, C_BG_MATH, C_BORDER_MATH, radius=0.35, lw=1.5)
    draw_header_banner(4.35, 3.82, 7.5, 0.33, ACCENT_GREEN, "3. STOCHASTIC MATHEMATICAL MODELING & INVARIANT MESH")

    # M/M/c Erlang C Box
    draw_card(4.4, 0.75, 3.6, 3.0, "#FFFFFF", ACCENT_GREEN, radius=0.22, lw=1.2)
    draw_header_banner(4.4, 3.42, 3.6, 0.33, ACCENT_GREEN, r"M/M/c Erlang C Queue Solver")

    # Clean spaced math lines to avoid glyph collision
    ax.text(6.20, 3.15, r"Arrival rate: $\lambda$, Service rate: $\mu$, Ports: $c$", fontsize=7.5, ha='center', va='center', color='#1E293B')
    ax.text(6.20, 2.90, r"Traffic intensity: $\rho = \frac{\lambda}{c\cdot\mu} < 1.0$", fontsize=7.5, ha='center', va='center', color='#1E293B')
    
    ax.text(6.20, 2.58, "Erlang C Delay Probability:", fontsize=7.5, fontweight='bold', ha='center', va='center', color='#047857')
    ax.text(6.20, 2.22, r"$C(c, a) = \frac{\frac{a^c}{c!(1-\rho)}}{\sum_{k=0}^{c-1}\frac{a^k}{k!} + \frac{a^c}{c!(1-\rho)}}$",
            fontsize=8.8, ha='center', va='center', color='#0F172A')

    ax.text(6.20, 1.70, r"Tail Percentile Inversion ($p$-th percentile):", fontsize=7.5, fontweight='bold', ha='center', va='center', color='#047857')
    ax.text(6.20, 1.32, r"$t_p = \max\left(0, \; -\frac{\ln\left(\frac{1-p}{C(c,a)}\right)}{c\mu(1-\rho)}\right)$",
            fontsize=8.5, ha='center', va='center', color='#0F172A')
    
    ax.text(6.20, 0.95, r"Closed-form $p_{50}$ (median) and $p_{90}$ (tail delay)", fontsize=7.2, fontstyle='italic', ha='center', va='center', color='#475569')

    # Invariant Verification & Demand Forecaster
    draw_card(8.2, 2.30, 3.6, 1.45, "#FFFFFF", ACCENT_TEAL, radius=0.20, lw=1.1)
    draw_header_banner(8.2, 3.42, 3.6, 0.33, ACCENT_TEAL, "Theorem 1: Invariant Verification Mesh")
    ax.text(10.0, 2.80, r"$\forall \rho < 1 : t_{0.50} \leq t_{0.90}$" + " unconditionally\n"
            r"Verified across 728 distinct $(\lambda, \mu, c)$ regimes" "\n"
            r"$\mathbf{0\ Violations\ Detected}$ (100.0% adherence)",
            fontsize=7.4, ha='center', va='center', color='#0F172A', linespacing=1.25)

    draw_card(8.2, 0.75, 3.6, 1.40, "#FFFFFF", "#0284C7", radius=0.20, lw=1.1)
    draw_header_banner(8.2, 1.82, 3.6, 0.33, "#0284C7", "Predictive Demand Forecaster (GBT)")
    ax.text(10.0, 1.30, "Gradient Boosted Trees (LightGBM)\nPOI density, traffic flow, municipal demographics\nCold-start port utilization & diurnal demand profiles",
            fontsize=7.3, ha='center', va='center', color='#334155', linespacing=1.2)

    # =========================================================================
    # 4. RIGHT ZONE: EPISTEMIC PROVENANCE, EXPLANATION & CLIENT INTERFACE
    # =========================================================================
    draw_card(12.3, 0.6, 3.7, 8.6, C_BG_CLIENT, C_BORDER_CLIENT, radius=0.35, lw=1.5)
    draw_header_banner(12.45, 8.80, 3.4, 0.35, ACCENT_BLUE, "4. EPISTEMIC GROUNDING & CLIENT")

    # Explanation Agent
    draw_card(12.45, 6.75, 3.4, 1.9, "#FFFFFF", ACCENT_RED, radius=0.22, lw=1.3)
    draw_header_banner(12.45, 8.30, 3.4, 0.35, ACCENT_RED, "ExplanationAgent (Gemini 2.0 Flash)")
    ax.text(14.15, 7.50, "Vertex AI Gemini 2.0 Flash Explainer\n"
            r"$\bullet$ Receives deterministic structured results" "\n"
            r"$\bullet$ Prompt conditioned on provenance tags" "\n"
            r"$\bullet$ Zero-fabrication hedging protocol" "\n"
            r"$\bullet$ Plain-English executive rationale",
            fontsize=7.5, ha='center', va='center', color='#1E293B', linespacing=1.25)

    # 3-Tier Provenance Shield
    draw_card(12.45, 4.35, 3.4, 2.25, C_BG_LLM, C_BORDER_LLM, radius=0.22, lw=1.2)
    draw_header_banner(12.45, 6.25, 3.4, 0.35, ACCENT_RED, "3-Tier Provenance Shield", font_size=8.8)
    prov_boxes = [
        ("LIVE [0.95 - 1.00]", "Hardware sync; direct assertion", "#15803D", 5.65),
        ("ESTIMATED [0.70 - 0.94]", "M/M/c & GBT; probabilistic bounds", "#1D4ED8", 5.00),
        ("FALLBACK [0.30 - 0.69]", "Outage priors; explicit fallback_reason", "#B91C1C", 4.35),
    ]
    for p_title, p_desc, p_col, p_y in prov_boxes:
        draw_card(12.6, p_y + 0.05, 3.1, 0.52, "#FFFFFF", p_col, radius=0.12, lw=0.9)
        ax.text(12.75, p_y + 0.38, p_title, fontsize=7.2, fontweight='bold', color=p_col, va='center')
        ax.text(12.75, p_y + 0.18, p_desc, fontsize=6.8, color='#475569', va='center')

    # FastAPI & Interactive Dashboard
    draw_card(12.45, 2.25, 3.4, 1.95, "#FFFFFF", ACCENT_BLUE, radius=0.22, lw=1.2)
    draw_header_banner(12.45, 3.85, 3.4, 0.35, ACCENT_BLUE, "FastAPI Async Gateway (Google Cloud Run)")
    ax.text(14.15, 3.05, "Sub-second SLA: p50 = 880 ms globally\nToken-bucket rate limiter (500 req/min)\nInteractive Leaflet.js GIS map rendering\nDynamic isochrone reachability polygons\nReal-time socket power state overlays",
            fontsize=7.4, ha='center', va='center', color='#1E293B', linespacing=1.25)

    # Deliverables & End User Outputs
    draw_card(12.45, 0.8, 3.4, 1.3, "#EFF6FF", "#3B82F6", radius=0.18, lw=1.0)
    draw_header_banner(12.45, 1.75, 3.4, 0.32, "#2563EB", "End-User Decision Outputs", font_size=8.2)
    ax.text(14.15, 1.28, "1. Drivers: Nearby station ranking + tail wait (p90)\n2. CPOs / Investors: 5-year CapEx siting viable sites\n3. Municipalities: Grid impact & EV readiness index",
            fontsize=7.3, ha='center', va='center', color='#0F172A', linespacing=1.2)

    # =========================================================================
    # SYSTEM DATA BUSSES & INTER-LAYER CONNECTORS
    # =========================================================================
    # 1. Ingestion to Agent Mesh (Deduplicated Stream)
    ax.annotate('', xy=(4.2, 6.2), xytext=(3.9, 6.2),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_BLUE, lw=2.0, mutation_scale=14))
    ax.text(4.05, 6.45, "Fused\nStream", fontsize=7.5, fontweight='bold', color=ACCENT_BLUE, ha='center')

    # 2. Agent Mesh to Math Solvers
    ax.annotate('', xy=(8.1, 4.15), xytext=(8.1, 4.58),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_GREEN, lw=1.8, mutation_scale=12))
    badge = patches.FancyBboxPatch(
        (7.35, 4.18), 1.5, 0.24,
        boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
        facecolor="#FFFFFF", edgecolor=ACCENT_GREEN, linewidth=0.9, zorder=5
    )
    ax.add_patch(badge)
    ax.text(8.1, 4.30, r"Traffic $\lambda, \mu, c$", fontsize=7.2, fontweight='bold', color=ACCENT_GREEN, ha='center', va='center', zorder=6)

    # 3. Orthogonal Routing: Math Solvers up to ExplanationAgent
    # Route from (11.8, 3.0) -> (12.1, 3.0) -> (12.1, 7.4) -> (12.45, 7.4)
    math_bus_pts = [(11.8, 3.0), (12.1, 3.0), (12.1, 7.4), (12.45, 7.4)]
    for i in range(len(math_bus_pts) - 1):
        p1 = math_bus_pts[i]
        p2 = math_bus_pts[i+1]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=ACCENT_GREEN, lw=1.8, linestyle="-", zorder=5)
    ax.annotate('', xy=(12.45, 7.4), xytext=(12.25, 7.4),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_GREEN, lw=1.8, mutation_scale=12))
    
    badge_math = patches.FancyBboxPatch(
        (11.45, 5.05), 1.3, 0.35,
        boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.10),
        facecolor="#FFFFFF", edgecolor=ACCENT_GREEN, linewidth=0.8, zorder=6
    )
    ax.add_patch(badge_math)
    ax.text(12.1, 5.22, r"Tail Delays $p_{50}, p_{90}$", fontsize=7.0, fontweight='bold', color=ACCENT_GREEN, ha='center', va='center', zorder=7)

    # 4. Multi-agent decisions to Client Gateway
    ax.annotate('', xy=(14.15, 6.70), xytext=(14.15, 6.60),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_BLUE, lw=1.8, mutation_scale=12))

    # 5. Live Telemetry Bypass (Purple Bus from Ingestion directly to Provenance Shield)
    bus_pts = [(3.75, 3.35), (4.05, 3.35), (4.05, 0.4), (12.15, 0.4), (12.15, 5.5), (12.45, 5.5)]
    for i in range(len(bus_pts) - 1):
        p1 = bus_pts[i]
        p2 = bus_pts[i+1]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#9333EA", lw=1.6, linestyle="--", zorder=5)
    ax.annotate('', xy=(12.45, 5.5), xytext=(12.25, 5.5),
                arrowprops=dict(arrowstyle="-|>", color="#9333EA", lw=1.6, mutation_scale=12))
    
    badge_telem = patches.FancyBboxPatch(
        (4.7, 0.25), 6.8, 0.30,
        boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.10),
        facecolor="#FFFFFF", edgecolor="#9333EA", linewidth=0.8, zorder=6
    )
    ax.add_patch(badge_telem)
    ax.text(8.1, 0.40, "Immutable Live Hardware Telemetry Bus (Direct Socket Status Sync — Bypass Hallucination Path)",
            fontsize=7.6, fontweight='bold', color="#7E22CE", ha='center', va='center', zorder=7)

    # Output targets
    dirs = [
        r"C:\Users\HARSH AMBULE\Downloads\paper",
        r"C:\Users\HARSH AMBULE\Downloads\paper\figures",
        r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper",
        r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper\figures",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # Save to primary Downloads/paper first
    primary_png = r"C:\Users\HARSH AMBULE\Downloads\paper\architecture-diagram.png"
    primary_pdf = r"C:\Users\HARSH AMBULE\Downloads\paper\architecture-diagram.pdf"
    plt.savefig(primary_png, dpi=300, facecolor='#FFFFFF', edgecolor='none')
    plt.savefig(primary_pdf, dpi=300, facecolor='#FFFFFF', edgecolor='none')
    plt.close()

    # Mirror to all figure directories and aliases
    for d in dirs:
        for fname in ["architecture-diagram.png", "fig1_architecture.png"]:
            dst = os.path.join(d, fname)
            if os.path.abspath(primary_png) != os.path.abspath(dst):
                shutil.copyfile(primary_png, dst)
        for fname in ["architecture-diagram.pdf", "fig1_architecture.pdf"]:
            dst = os.path.join(d, fname)
            if os.path.abspath(primary_pdf) != os.path.abspath(dst):
                shutil.copyfile(primary_pdf, dst)

    print("Redesigned Figure 1 rendered and mirrored to all targets successfully!")

if __name__ == "__main__":
    create_redesigned_fig1()
