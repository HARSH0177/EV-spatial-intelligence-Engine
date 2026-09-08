import os
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_advanced_fig3():
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

    # Palette
    C_BG_SLATE   = "#F8FAFC"
    C_BORDER_SLATE = "#CBD5E1"
    C_BG_PURPLE  = "#FAF5FF"
    C_BORDER_PURPLE = "#E9D5FF"
    C_BG_ROSE    = "#FFF1F2"
    C_BORDER_ROSE = "#FECDD3"
    C_BG_SKY     = "#F0F9FF"
    C_BORDER_SKY = "#BAE6FD"

    ACCENT_BLUE   = "#1E40AF"
    ACCENT_PURPLE = "#6D28D9"
    ACCENT_GREEN  = "#047857"
    ACCENT_RED    = "#B91C1C"
    ACCENT_AMBER  = "#B45309"
    ACCENT_SLATE  = "#334155"
    ACCENT_TEAL   = "#0F766E"

    def draw_card(x, y, w, h, bg, border, radius=0.25, lw=1.2, ls='-'):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=radius),
            facecolor=bg, edgecolor=border, linewidth=lw, linestyle=ls, zorder=2
        )
        ax.add_patch(box)
        return box

    def draw_header_banner(x, y, w, h, bg_color, text, text_color="#FFFFFF", font_size=9.2):
        banner = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.16),
            facecolor=bg_color, edgecolor=bg_color, linewidth=0.8, zorder=3
        )
        ax.add_patch(banner)
        ax.text(x + w/2, y + h/2, text, color=text_color, fontsize=font_size,
                fontweight='bold', ha='center', va='center', zorder=4)

    # =========================================================================
    # MAIN TITLE & SUBTITLE
    # =========================================================================
    ax.text(8.25, 9.85, "3-Tier Epistemic Data Provenance Framework & Zero-Fabrication Hedging Architecture",
            fontsize=15.0, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(8.25, 9.58, "Dynamic Confidence Classification  -->  State-Machine Routing  -->  LLM Hedging Interceptors  -->  Auditable JSON Contracts",
            fontsize=10.2, fontstyle='italic', ha='center', va='center', color='#475569')

    # =========================================================================
    # ZONE 1: MULTI-SOURCE INGESTION & CONFIDENCE RATING (LEFT: x=0.5 to 4.2)
    # =========================================================================
    draw_card(0.5, 0.6, 3.7, 8.6, C_BG_SLATE, C_BORDER_SLATE, radius=0.35, lw=1.5)
    draw_header_banner(0.65, 8.82, 3.4, 0.33, ACCENT_SLATE, "1. INGESTION & CONFIDENCE RATING")

    # Tier 1 Source Card: LIVE DATA
    draw_card(0.65, 6.25, 3.4, 2.45, "#FFFFFF", "#15803D", radius=0.18, lw=1.2)
    draw_header_banner(0.65, 8.38, 3.4, 0.32, "#15803D", "Tier 1: LIVE HARDWARE SYNC", font_size=8.5)
    ax.text(2.35, 8.08, "Confidence Band: [ 0.95 - 1.00 ]", fontsize=7.6, fontweight='bold', color='#15803D', ha='center')
    ax.text(2.35, 7.85, "Zero Statistical Estimation", fontsize=7.2, fontstyle='italic', color='#475569', ha='center')
    ax.text(2.35, 7.30, "• Active OCPP 1.6 WebSocket telemetry\n• BigQuery transaction lake verified records\n• Real-time socket occupancy & kW draw\n• Polling heartbeat: 5 - 15 seconds",
            fontsize=7.2, color='#1E293B', ha='center', linespacing=1.25)
    ax.text(2.35, 6.45, "Factual Ground Truth (Physical Assertion)", fontsize=7.0, fontweight='bold', color='#15803D', ha='center')

    # Tier 2 Source Card: ESTIMATED DATA
    draw_card(0.65, 3.55, 3.4, 2.55, "#FFFFFF", "#1D4ED8", radius=0.18, lw=1.2)
    draw_header_banner(0.65, 5.78, 3.4, 0.32, "#1D4ED8", "Tier 2: PREDICTIVE GEO-FUSION", font_size=8.5)
    ax.text(2.35, 5.48, "Confidence Band: [ 0.70 - 0.94 ]", fontsize=7.6, fontweight='bold', color='#1D4ED8', ha='center')
    ax.text(2.35, 5.25, "Analytic & Machine Learning Inference", fontsize=7.2, fontstyle='italic', color='#475569', ha='center')
    ax.text(2.35, 4.65, "• Multi-API spatial fusion (OCM + OSM + NREL)\n• M/M/c Erlang C queuing wait model\n• LightGBM diurnal demand regressor\n• Spatial radius clustering: Δd < 50 m",
            fontsize=7.2, color='#1E293B', ha='center', linespacing=1.25)
    ax.text(2.35, 3.75, "Probabilistic Upper/Lower Bounds", fontsize=7.0, fontweight='bold', color='#1D4ED8', ha='center')

    # Tier 3 Source Card: FALLBACK ESTIMATOR
    draw_card(0.65, 0.80, 3.4, 2.60, "#FFFFFF", "#B91C1C", radius=0.18, lw=1.2)
    draw_header_banner(0.65, 3.08, 3.4, 0.32, "#B91C1C", "Tier 3: OUTAGE FALLBACK PRIOR", font_size=8.5)
    ax.text(2.35, 2.78, "Confidence Band: [ 0.30 - 0.69 ]", fontsize=7.6, fontweight='bold', color='#B91C1C', ha='center')
    ax.text(2.35, 2.55, "Graceful Degradation Under Failure", fontsize=7.2, fontstyle='italic', color='#475569', ha='center')
    ax.text(2.35, 1.95, "• Upstream API timeout (> 3000 ms)\n• Historical municipal district capacity\n• Hardware telemetry offline / lost socket\n• Generates explicit fallback_reason error code",
            fontsize=7.2, color='#1E293B', ha='center', linespacing=1.25)
    ax.text(2.35, 1.02, "Heuristic Baseline (Strictly Hedged)", fontsize=7.0, fontweight='bold', color='#B91C1C', ha='center')

    # =========================================================================
    # ZONE 2: DYNAMIC STATE-MACHINE CLASSIFIER (CENTER-UPPER: x=4.5 to 11.8, y=4.7 to 9.2)
    # =========================================================================
    draw_card(4.5, 4.70, 7.3, 4.50, C_BG_PURPLE, C_BORDER_PURPLE, radius=0.35, lw=1.5)
    draw_header_banner(4.65, 8.82, 7.0, 0.33, ACCENT_PURPLE, "2. DYNAMIC PROVENANCE STATE-MACHINE & TRANSITION ROUTER")

    # Interactive 3-State Nodes Diagram
    draw_card(4.65, 6.70, 7.0, 2.00, "#FFFFFF", ACCENT_PURPLE, radius=0.20, lw=1.1)
    draw_header_banner(4.65, 8.38, 7.0, 0.32, ACCENT_PURPLE, "Real-Time Telemetry & Outage State Transition Lattice", font_size=8.2)

    # 3 State Pills (Width 1.60 with generous 0.95 gap between them)
    states = [
        ("STATE 1: LIVE", "Hardware Active\nHeartbeat < 30s", "#15803D", "#DCFCE7", 5.60),
        ("STATE 2: ESTIMATED", "Geo Ingested\nQueue Invariant Met", "#1D4ED8", "#DBEAFE", 8.15),
        ("STATE 3: FALLBACK", "Network Outage\nTimeout > 3.0s", "#B91C1C", "#FEE2E2", 10.70),
    ]
    for s_name, s_sub, s_border, s_bg, sx in states:
        box = patches.FancyBboxPatch((sx - 0.80, 7.20), 1.60, 0.95,
                                    boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.14),
                                    facecolor=s_bg, edgecolor=s_border, linewidth=1.3, zorder=4)
        ax.add_patch(box)
        ax.text(sx, 7.82, s_name, fontsize=7.2, fontweight='bold', color=s_border, ha='center', va='center', zorder=5)
        ax.text(sx, 7.42, s_sub, fontsize=6.6, color='#1E293B', ha='center', va='center', zorder=5, linespacing=1.15)

    # Transition arrows between State 1 and State 2 (in 0.95 gap: 6.40 to 7.35)
    ax.annotate('', xy=(7.25, 7.78), xytext=(6.50, 7.78),
                arrowprops=dict(arrowstyle="-|>", color='#6D28D9', lw=1.3, mutation_scale=9))
    ax.text(6.87, 7.94, "Telemetry Lost", fontsize=6.4, fontweight='bold', color='#6D28D9', ha='center', va='center')

    ax.annotate('', xy=(6.50, 7.36), xytext=(7.25, 7.36),
                arrowprops=dict(arrowstyle="-|>", color='#15803D', lw=1.3, mutation_scale=9))
    ax.text(6.87, 7.20, "Heartbeat Recv", fontsize=6.4, fontweight='bold', color='#15803D', ha='center', va='center')

    # Transition arrows between State 2 and State 3 (in 0.95 gap: 8.95 to 9.90)
    ax.annotate('', xy=(9.80, 7.78), xytext=(9.05, 7.78),
                arrowprops=dict(arrowstyle="-|>", color='#B91C1C', lw=1.3, mutation_scale=9))
    ax.text(9.42, 7.94, "API Timeout", fontsize=6.4, fontweight='bold', color='#B91C1C', ha='center', va='center')

    ax.annotate('', xy=(9.05, 7.36), xytext=(9.80, 7.36),
                arrowprops=dict(arrowstyle="-|>", color='#1D4ED8', lw=1.3, mutation_scale=9))
    ax.text(9.42, 7.20, "API Restored", fontsize=6.4, fontweight='bold', color='#1D4ED8', ha='center', va='center')

    ax.text(8.15, 6.85, "State Evaluation Frequency: Continuous per incoming REST / WebSocket request",
            fontsize=7.0, fontstyle='italic', color='#64748B', ha='center')

    # Router & Metadata Packaging Card
    draw_card(4.65, 4.85, 7.0, 1.75, "#FFFFFF", ACCENT_TEAL, radius=0.18, lw=1.1)
    draw_header_banner(4.65, 6.28, 7.0, 0.32, ACCENT_TEAL, "Provenance Metadata Packaging & Circuit Breaker", font_size=8.2)

    ax.text(6.30, 5.92, "Immutable Packaging Protocol:", fontsize=7.4, fontweight='bold', color='#0F766E', ha='center')
    ax.text(6.30, 5.40, "• Injects provenance_tier tag into query payload\n• Computes confidence score [0.30 - 1.00]\n• Locks raw numeric outputs from LLM mutation",
            fontsize=7.2, color='#1E293B', ha='center', linespacing=1.25)
    
    ax.text(10.00, 5.92, "Circuit Breaker Invariant:", fontsize=7.4, fontweight='bold', color='#B91C1C', ha='center')
    ax.text(10.00, 5.40, "• If rho >= 1.0 or delta_t > 3.0s --> Force FALLBACK\n• Attaches machine-readable fallback_reason code\n• Prohibits LLM from guessing unmeasured state",
            fontsize=7.2, color='#1E293B', ha='center', linespacing=1.25)

    # =========================================================================
    # ZONE 3: ZERO-FABRICATION LLM HEDGING SHIELD (CENTER-LOWER: x=4.5 to 11.8, y=0.6 to 4.5)
    # =========================================================================
    draw_card(4.5, 0.60, 7.3, 3.90, C_BG_ROSE, C_BORDER_ROSE, radius=0.35, lw=1.5)
    draw_header_banner(4.65, 4.15, 7.0, 0.33, ACCENT_RED, "3. ZERO-FABRICATION LLM HEDGING SHIELD & VERIFICATION GATE")

    # LLM Prompt Conditioned Contract Card
    draw_card(4.65, 2.35, 7.0, 1.70, "#FFFFFF", ACCENT_RED, radius=0.18, lw=1.1)
    draw_header_banner(4.65, 3.73, 7.0, 0.32, ACCENT_RED, "Prompt Lexical Contracts: Gemini 2.0 Flash Explainer", font_size=8.2)

    contracts = [
        ("LIVE", "Direct assertion allowed; state exact power & occupancy.", "Assert: 'Port 2 OCCUPIED @ 120 kW'", "#15803D", 3.42),
        ("ESTIMATED", "Mandatory probabilistic bounds; state p50 and p90 wait.", "Hedge: 'Wait ~8.3m (p90), 4.1m (p50)'", "#1D4ED8", 2.95),
        ("FALLBACK", "Epistemic disclaimer required; no live certainty.", "Disclose: 'Live offline; using prior'", "#B91C1C", 2.48),
    ]
    for c_title, c_desc, c_ex, c_col, cy in contracts:
        draw_card(4.75, cy - 0.15, 1.25, 0.30, "#F8FAFC", c_col, radius=0.08, lw=0.9)
        ax.text(5.37, cy, c_title, fontsize=6.8, fontweight='bold', color=c_col, ha='center', va='center')
        ax.text(6.15, cy, c_desc, fontsize=6.8, color='#1E293B', ha='left', va='center')
        ax.text(11.45, cy, c_ex, fontsize=6.7, fontstyle='italic', fontweight='semibold', color='#334155', ha='right', va='center')

    # Verification Gate & Interceptor Card
    draw_card(4.65, 0.75, 7.0, 1.50, "#FFFFFF", ACCENT_PURPLE, radius=0.18, lw=1.2)
    draw_header_banner(4.65, 1.93, 7.0, 0.30, ACCENT_PURPLE, "Semantic Output Interceptor & Hallucination Filter Gate", font_size=8.0)

    ax.text(6.30, 1.58, "Regex & Semantic AST Inspector", fontsize=7.2, fontweight='bold', color='#6D28D9', ha='center')
    ax.text(6.30, 1.20, "• Scans LLM draft for forbidden certainty tokens\n• Detects unverified assertions on FALLBACK / ESTIMATED\n• Automated rejection if lexical contract breached",
            fontsize=7.0, color='#1E293B', ha='center', linespacing=1.2)

    ax.text(10.00, 1.58, "Zero-Hallucination Adherence Rate", fontsize=7.2, fontweight='bold', color='#15803D', ha='center')
    ax.text(10.00, 1.30, "0 Breaches Detected", fontsize=10.0, fontweight='bold', color='#15803D', ha='center')
    ax.text(10.00, 1.05, "100.0% adherence across live deployments", fontsize=6.8, fontstyle='italic', color='#64748B', ha='center')

    # =========================================================================
    # ZONE 4: AUDITABLE JSON CONTRACT & CLIENT DELIVERY (RIGHT: x=12.1 to 16.0)
    # =========================================================================
    draw_card(12.1, 0.6, 3.9, 8.6, C_BG_SKY, C_BORDER_SKY, radius=0.35, lw=1.5)
    draw_header_banner(12.25, 8.82, 3.6, 0.33, ACCENT_BLUE, "4. AUDITABLE JSON & CLIENT DELIVERY")

    # Production JSON Payload Preview Card
    draw_card(12.25, 4.40, 3.6, 4.30, "#0F172A", "#334155", radius=0.18, lw=1.2)
    draw_header_banner(12.25, 8.38, 3.6, 0.32, "#334155", "Production API JSON Response Schema", font_size=8.2)

    json_lines = [
        ("{\n", "#F8FAFC"),
        ('  "station_id": "OCM-184920",\n', "#93C5FD"),
        ('  "provenance_tier": "ESTIMATED",\n', "#FCD34D"),
        ('  "confidence_score": 0.88,\n', "#86EFAC"),
        ('  "telemetry_sync": {\n', "#CBD5E1"),
        ('    "active_ports": 4,\n', "#F8FAFC"),
        ('    "status": "OPERATIONAL"\n', "#86EFAC"),
        ('  },\n', "#CBD5E1"),
        ('  "queue_metrics": {\n', "#CBD5E1"),
        ('    "wait_p50_min": 4.10,\n', "#F8FAFC"),
        ('    "wait_p90_min": 8.30,\n', "#F8FAFC"),
        ('    "rho": 0.65\n', "#F8FAFC"),
        ('  },\n', "#CBD5E1"),
        ('  "fallback_reason": null,\n', "#FCA5A5"),
        ('  "hedged_rationale": "High diurnal traffic\n    expect ~8.3m tail queue delay."\n', "#6EE7B7"),
        ("}", "#F8FAFC"),
    ]
    code_str = "".join([l[0] for l in json_lines])
    ax.text(12.45, 6.30, code_str, fontfamily='monospace', fontsize=6.8, color='#E2E8F0', va='center', linespacing=1.20)

    # FastAPI Gateway Card
    draw_card(12.25, 2.45, 3.6, 1.85, "#FFFFFF", ACCENT_BLUE, radius=0.18, lw=1.2)
    draw_header_banner(12.25, 3.98, 3.6, 0.32, ACCENT_BLUE, "FastAPI Sub-Second Gateway (Cloud Run)", font_size=8.2)
    ax.text(14.05, 3.65, "Sub-second SLA: p50 = 880 ms globally", fontsize=7.4, fontweight='bold', color='#1E40AF', ha='center')
    ax.text(14.05, 3.15, "• Token-bucket rate limiter: 500 req/min\n• Asynchronous non-blocking I/O (asyncio.gather)\n• Provenance schema validation on egress",
            fontsize=7.1, color='#1E293B', ha='center', linespacing=1.2)
    ax.text(14.05, 2.62, "Immutable API Contract Guarantee", fontsize=7.0, fontstyle='italic', color='#64748B', ha='center')

    # Multi-Stakeholder End Users Card
    draw_card(12.25, 0.80, 3.6, 1.55, "#EFF6FF", "#3B82F6", radius=0.18, lw=1.1)
    draw_header_banner(12.25, 2.03, 3.6, 0.30, "#2563EB", "Multi-Stakeholder Client Interface", font_size=8.0)
    ax.text(14.05, 1.62, "1. Drivers: Transparent queue wait & confidence badge\n2. CPOs: Siting suitability index & grid headroom\n3. Municipalities: EV readiness & spatial equity score",
            fontsize=7.1, color='#0F172A', ha='center', linespacing=1.22)
    ax.text(14.05, 1.00, "Leaflet.js interactive GIS map overlay", fontsize=6.8, fontstyle='italic', color='#64748B', ha='center')

    # =========================================================================
    # BUS CONNECTORS & ARROWS BETWEEN ZONES
    # =========================================================================
    # Connector 1: Zone 1 to Zone 2
    ax.annotate('', xy=(4.5, 7.5), xytext=(4.2, 7.5),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_SLATE, lw=2.0, mutation_scale=14))
    b1 = patches.FancyBboxPatch((3.95, 7.62), 0.80, 0.26, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                               facecolor="#FFFFFF", edgecolor=ACCENT_SLATE, linewidth=0.8, zorder=6)
    ax.add_patch(b1)
    ax.text(4.35, 7.75, "Raw Streams", fontsize=6.8, fontweight='bold', color=ACCENT_SLATE, ha='center', va='center', zorder=7)

    # Connector 2: Zone 2 down to Zone 3
    ax.annotate('', xy=(8.15, 4.50), xytext=(8.15, 4.70),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_PURPLE, lw=2.0, mutation_scale=14))
    b2 = patches.FancyBboxPatch((7.15, 4.47), 2.00, 0.26, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                               facecolor="#FFFFFF", edgecolor=ACCENT_PURPLE, linewidth=0.8, zorder=6)
    ax.add_patch(b2)
    ax.text(8.15, 4.60, "Tagged Provenance Contract", fontsize=7.0, fontweight='bold', color=ACCENT_PURPLE, ha='center', va='center', zorder=7)

    # Connector 3: Zone 3 to Zone 4 (Feeds into FastAPI Gateway at y=2.50)
    ax.annotate('', xy=(12.1, 2.50), xytext=(11.8, 2.50),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_BLUE, lw=1.8, mutation_scale=12))
    b3 = patches.FancyBboxPatch((11.42, 2.60), 1.05, 0.24, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                               facecolor="#FFFFFF", edgecolor=ACCENT_BLUE, linewidth=0.8, zorder=6)
    ax.add_patch(b3)
    ax.text(11.95, 2.72, "Verified Payload", fontsize=6.7, fontweight='bold', color=ACCENT_BLUE, ha='center', va='center', zorder=7)

    # Connector 4: Live Telemetry Direct Bypass (from Zone 1 directly to JSON Payload)
    # Route: (4.2, 8.4) -> (4.35, 8.4) -> (4.35, 9.35) -> (11.95, 9.35) -> (11.95, 8.55) -> (12.25, 8.55)
    telem_pts = [(4.2, 8.4), (4.35, 8.4), (4.35, 9.35), (11.95, 9.35), (11.95, 8.55), (12.25, 8.55)]
    for i in range(len(telem_pts) - 1):
        p1 = telem_pts[i]
        p2 = telem_pts[i+1]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#15803D', lw=1.6, linestyle="--", zorder=5)
    ax.annotate('', xy=(12.25, 8.55), xytext=(12.05, 8.55),
                arrowprops=dict(arrowstyle="-|>", color='#15803D', lw=1.6, mutation_scale=12))
    
    b_bypass = patches.FancyBboxPatch((6.8, 9.22), 2.7, 0.26, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                                     facecolor="#FFFFFF", edgecolor='#15803D', linewidth=0.8, zorder=6)
    ax.add_patch(b_bypass)
    ax.text(8.15, 9.35, "Direct Hardware Telemetry Sync (Bypass LLM)", fontsize=7.0, fontweight='bold', color='#15803D', ha='center', va='center', zorder=7)

    # Output targets
    dirs = [
        r"C:\Users\HARSH AMBULE\Downloads\paper",
        r"C:\Users\HARSH AMBULE\Downloads\paper\figures",
        r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper",
        r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper\figures",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    primary_png = r"C:\Users\HARSH AMBULE\Downloads\paper\data-provenance-matrix.png"
    primary_pdf = r"C:\Users\HARSH AMBULE\Downloads\paper\data-provenance-matrix.pdf"
    plt.savefig(primary_png, dpi=300, facecolor='#FFFFFF', edgecolor='none')
    plt.savefig(primary_pdf, dpi=300, facecolor='#FFFFFF', edgecolor='none')
    plt.close()

    for d in dirs:
        for fname in ["data-provenance-matrix.png", "fig3_data_provenance.png"]:
            dst = os.path.join(d, fname)
            if os.path.abspath(primary_png) != os.path.abspath(dst):
                shutil.copyfile(primary_png, dst)
        for fname in ["data-provenance-matrix.pdf", "fig3_data_provenance.pdf"]:
            dst = os.path.join(d, fname)
            if os.path.abspath(primary_pdf) != os.path.abspath(dst):
                shutil.copyfile(primary_pdf, dst)

    print("Advanced Figure 3 rendered and mirrored to all targets successfully!")

if __name__ == "__main__":
    create_advanced_fig3()
