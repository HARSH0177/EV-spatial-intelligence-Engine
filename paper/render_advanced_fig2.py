import os
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_advanced_fig2():
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

    # Color Palette: Elsevier EAAI Academic Standard
    C_BG_SLATE   = "#F8FAFC"
    C_BORDER_SLATE = "#CBD5E1"
    C_BG_PURPLE  = "#FAF5FF"
    C_BORDER_PURPLE = "#E9D5FF"
    C_BG_GREEN   = "#F0FDF4"
    C_BORDER_GREEN = "#BBF7D0"
    C_BG_AMBER   = "#FFFBEB"
    C_BORDER_AMBER = "#FDE68A"

    ACCENT_BLUE   = "#1E40AF"
    ACCENT_PURPLE = "#6D28D9"
    ACCENT_GREEN  = "#047857"
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
    ax.text(8.25, 9.85, "Stochastic M/M/c Erlang C Congestion Modeling & Closed-Form Tail Inversion Architecture",
            fontsize=15.0, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(8.25, 9.58, "Continuous-Time Markov Chain State Space  -->  Erlang C Congestion  -->  Analytic Inversion  -->  Theorem 1 Invariant Order",
            fontsize=10.2, fontstyle='italic', ha='center', va='center', color='#475569')

    # =========================================================================
    # ZONE 1: INPUT PARAMETER CONDITIONING & ERGODICITY GUARD (LEFT: x=0.5 to 4.2)
    # =========================================================================
    draw_card(0.5, 0.6, 3.7, 8.6, C_BG_SLATE, C_BORDER_SLATE, radius=0.35, lw=1.5)
    draw_header_banner(0.65, 8.82, 3.4, 0.33, ACCENT_BLUE, "1. PARAMETER CONDITIONING & GUARD")

    # Card 1.1: Arrival Process
    draw_card(0.65, 7.05, 3.4, 1.65, "#FFFFFF", "#2563EB", radius=0.18, lw=1.1)
    draw_header_banner(0.65, 8.38, 3.4, 0.32, "#2563EB", "Poisson Arrival Process", font_size=8.5)
    ax.text(2.35, 7.95, r"Mean Arrival Rate: $\lambda$ (vehicles/hour)", fontsize=7.6, ha='center', va='center', color='#1E293B')
    ax.text(2.35, 7.62, r"Non-homogeneous Poisson: $\lambda(t) = \bar{\lambda} \cdot \delta_{\mathrm{diurnal}}(t)$", fontsize=7.4, ha='center', va='center', color='#2563EB')
    ax.text(2.35, 7.28, "Aggregated spatial POI & commuter flux", fontsize=7.2, fontstyle='italic', ha='center', va='center', color='#64748B')

    # Card 1.2: Multiserver Topology
    draw_card(0.65, 5.05, 3.4, 1.80, "#FFFFFF", "#0284C7", radius=0.18, lw=1.1)
    draw_header_banner(0.65, 6.53, 3.4, 0.32, "#0284C7", "Multiserver Topology & Service", font_size=8.5)
    ax.text(2.35, 6.18, r"Parallel Charging Ports: $c \in \{2, 4, 8, 16\}$", fontsize=7.6, ha='center', va='center', color='#1E293B')
    ax.text(2.35, 5.85, r"Service Rate per Port: $\mu = 2.0$ veh/h", fontsize=7.6, ha='center', va='center', color='#1E293B')
    ax.text(2.35, 5.52, r"Mean Charging Duration: $1/\mu = 30.0$ min", fontsize=7.4, ha='center', va='center', color='#0284C7')
    ax.text(2.35, 5.22, r"Exponential Service Distribution: $B(t) = 1 - e^{-\mu t}$", fontsize=7.1, fontstyle='italic', ha='center', va='center', color='#64748B')

    # Card 1.3: Offered Load & Intensity
    draw_card(0.65, 3.05, 3.4, 1.80, "#FFFFFF", "#0F766E", radius=0.18, lw=1.1)
    draw_header_banner(0.65, 4.53, 3.4, 0.32, "#0F766E", "Offered Load & Server Intensity", font_size=8.5)
    ax.text(2.35, 4.18, r"Offered Traffic Load: $a = \frac{\lambda}{\mu}$ (Erlangs)", fontsize=7.6, ha='center', va='center', color='#1E293B')
    ax.text(2.35, 3.85, r"Mean Server Utilization: $\rho = \frac{\lambda}{c \cdot \mu} = \frac{a}{c}$", fontsize=7.6, ha='center', va='center', color='#0F766E')
    ax.text(2.35, 3.48, r"Critical Traffic Threshold: $\rho \to 1.0^-$", fontsize=7.4, ha='center', va='center', color='#1E293B')
    ax.text(2.35, 3.20, "Under-saturated vs. congested boundary", fontsize=7.1, fontstyle='italic', ha='center', va='center', color='#64748B')

    # Card 1.4: Stability & Ergodicity Guard
    draw_card(0.65, 0.80, 3.4, 2.05, "#EFF6FF", "#3B82F6", radius=0.18, lw=1.2)
    draw_header_banner(0.65, 2.53, 3.4, 0.32, ACCENT_SLATE, "Ergodicity & Stability Guardrail", font_size=8.4)
    ax.text(2.35, 2.18, r"Stability Condition: $\rho = \frac{\lambda}{c\mu} < 1.0$", fontsize=7.8, fontweight='bold', ha='center', va='center', color='#1E40AF')
    ax.text(2.35, 1.80, "Prevents infinite queue divergence\nGuarantees stationary state distribution $\pi$", fontsize=7.3, ha='center', va='center', color='#334155', linespacing=1.2)
    ax.text(2.35, 1.25, r"Circuit Breaker: If $\rho \geq 1.0 \Rightarrow$ Outage Flag" "\n" r"Triggers load shedding & dynamic re-routing", fontsize=7.1, ha='center', va='center', color='#B91C1C', linespacing=1.2)

    # =========================================================================
    # ZONE 2: CTMC STATE SPACE & ERLANG C CONGESTION SOLVER (CENTER-UPPER: x=4.5 to 11.8, y=4.7 to 9.2)
    # =========================================================================
    draw_card(4.5, 4.70, 7.3, 4.50, C_BG_PURPLE, C_BORDER_PURPLE, radius=0.35, lw=1.5)
    draw_header_banner(4.65, 8.82, 7.0, 0.33, ACCENT_PURPLE, "2. CONTINUOUS-TIME MARKOV CHAIN (CTMC) & ERLANG C SOLVER")

    # Visual CTMC Birth-Death Transition Diagram Box
    draw_card(4.65, 6.75, 7.0, 1.95, "#FFFFFF", ACCENT_PURPLE, radius=0.20, lw=1.1)
    draw_header_banner(4.65, 8.38, 7.0, 0.32, ACCENT_PURPLE, "Birth-Death Transition Lattice: State Space {0, 1, ..., c-1, c, c+1, ...}", font_size=8.2)

    # Render CTMC Nodes
    node_xs = [5.15, 6.05, 6.95, 8.05, 9.15, 10.35, 11.15]
    node_labels = ["0", "1", "2", r"$c-1$", r"$c$", r"$c+1$", "..."]
    for nx, nlab in zip(node_xs, node_labels):
        if nlab != "...":
            circle = patches.Circle((nx, 7.55), 0.24, facecolor='#EDE9FE', edgecolor=ACCENT_PURPLE, linewidth=1.2, zorder=4)
            ax.add_patch(circle)
            ax.text(nx, 7.55, nlab, fontsize=7.6, fontweight='bold', color='#4C1D95', ha='center', va='center', zorder=5)
        else:
            ax.text(nx, 7.55, nlab, fontsize=9.0, fontweight='bold', color='#6D28D9', ha='center', va='center')

    # Forward arrows (Birth: lambda)
    for i in range(len(node_xs) - 1):
        x1, x2 = node_xs[i] + 0.25, node_xs[i+1] - 0.25
        if node_xs[i+1] == 11.15:
            x2 = node_xs[i+1] - 0.15
        ax.annotate('', xy=(x2, 7.70), xytext=(x1, 7.70),
                    arrowprops=dict(arrowstyle="-|>", color='#7C3AED', lw=1.2, mutation_scale=9))
        ax.text((x1 + x2)/2, 7.86, r"$\lambda$", fontsize=7.2, color='#6D28D9', ha='center', va='center')

    # Backward arrows (Death: k*mu up to c*mu)
    death_rates = [r"$\mu$", r"$2\mu$", r"$(c-1)\mu$", r"$c\mu$", r"$c\mu$"]
    for i in range(len(death_rates)):
        x1, x2 = node_xs[i] + 0.25, node_xs[i+1] - 0.25
        if i == 2: # across gap to c-1
            pass
        ax.annotate('', xy=(x1, 7.40), xytext=(x2, 7.40),
                    arrowprops=dict(arrowstyle="-|>", color='#059669', lw=1.2, mutation_scale=9))
        ax.text((x1 + x2)/2, 7.24, death_rates[i], fontsize=6.8, color='#047857', ha='center', va='center')

    # Annotation under CTMC
    ax.text(6.05, 6.95, "[ Under-saturated regime: k < c ports busy ]", fontsize=6.8, color='#475569', ha='center')
    ax.text(9.75, 6.95, "[ Queueing regime: all c ports occupied; rate c·μ ]", fontsize=6.8, color='#B45309', ha='center')

    # Sub-card: Analytical Erlang C Formula & Waiting Time CDF
    draw_card(4.65, 4.85, 7.0, 1.80, "#FFFFFF", ACCENT_TEAL, radius=0.18, lw=1.1)
    draw_header_banner(4.65, 6.33, 7.0, 0.32, ACCENT_TEAL, "Closed-Form Erlang C Congestion & Waiting Time CDF", font_size=8.2)

    # Left: Erlang C Formula
    ax.text(6.35, 5.95, "Delay Probability (All Ports Saturated):", fontsize=7.4, fontweight='bold', ha='center', va='center', color='#0F766E')
    ax.text(6.35, 5.48, r"$C(c, a) = P(W_q > 0) = \frac{\frac{a^c}{c!(1-\rho)}}{\sum_{k=0}^{c-1}\frac{a^k}{k!} + \frac{a^c}{c!(1-\rho)}}$",
            fontsize=8.5, ha='center', va='center', color='#0F172A')
    ax.text(6.35, 5.02, r"Where $a = \lambda/\mu$, $\rho = a/c < 1.0$", fontsize=7.2, fontstyle='italic', ha='center', va='center', color='#475569')

    # Right: Waiting Time CDF
    ax.text(9.90, 5.95, "Defective Exponential Distribution:", fontsize=7.4, fontweight='bold', ha='center', va='center', color='#0F766E')
    ax.text(9.90, 5.50, r"$P(W_q \leq t) = 1 - C(c, a) \, e^{-c\mu(1-\rho)t}, \quad t \geq 0$",
            fontsize=8.2, ha='center', va='center', color='#0F172A')
    ax.text(9.90, 5.15, r"Point mass at zero wait: $P(W_q = 0) = 1 - C(c, a)$", fontsize=7.2, ha='center', va='center', color='#15803D')
    ax.text(9.90, 4.95, "Continuous tail for $t > 0$ under queueing condition", fontsize=6.8, fontstyle='italic', ha='center', va='center', color='#64748B')

    # =========================================================================
    # ZONE 3: EXACT TAIL INVERSION & COMPUTATIONAL SPEEDUP (CENTER-LOWER: x=4.5 to 11.8, y=0.6 to 4.5)
    # =========================================================================
    draw_card(4.5, 0.60, 7.3, 3.90, C_BG_GREEN, C_BORDER_GREEN, radius=0.35, lw=1.5)
    draw_header_banner(4.65, 4.15, 7.0, 0.33, ACCENT_GREEN, "3. EXACT TAIL PERCENTILE INVERSION & SPEEDUP ACCELERATOR")

    # Inversion Derivation Card
    draw_card(4.65, 2.25, 7.0, 1.80, "#FFFFFF", ACCENT_GREEN, radius=0.18, lw=1.1)
    draw_header_banner(4.65, 3.73, 7.0, 0.32, ACCENT_GREEN, "Closed-Form Quantile Inversion Solver", font_size=8.2)

    ax.text(8.15, 3.42, r"Set $P(W_q \leq t_p) = p \Leftrightarrow 1 - C(c, a) e^{-c\mu(1-\rho)t_p} = p$", fontsize=7.6, ha='center', va='center', color='#1E293B')
    ax.text(8.15, 3.02, r"$t_p = \max\left(0, \; -\frac{\ln\left(\frac{1-p}{C(c, a)}\right)}{c\,\mu\,(1 - \rho)}\right) = \max\left(0, \; \frac{\ln\left(\frac{C(c, a)}{1-p}\right)}{c\,\mu\,(1 - \rho)}\right)$",
            fontsize=8.5, fontweight='bold', ha='center', va='center', color='#047857')

    # Two columns for p50 and p90
    ax.text(6.30, 2.62, r"Median Wait Time ($p_{50}$, $p = 0.50$):", fontsize=7.3, fontweight='bold', ha='center', va='center', color='#1E40AF')
    ax.text(6.30, 2.38, r"$t_{0.50} = \max\left(0, \; \frac{\ln(2 \cdot C(c, a))}{c\,\mu\,(1-\rho)}\right)$", fontsize=7.6, ha='center', va='center', color='#0F172A')

    ax.text(10.00, 2.62, r"Tail Wait Time ($p_{90}$, $p = 0.90$):", fontsize=7.3, fontweight='bold', ha='center', va='center', color='#B91C1C')
    ax.text(10.00, 2.38, r"$t_{0.90} = \max\left(0, \; \frac{\ln(10 \cdot C(c, a))}{c\,\mu\,(1-\rho)}\right)$", fontsize=7.6, ha='center', va='center', color='#0F172A')

    # Computational Speedup Callout Card
    draw_card(4.65, 0.75, 7.0, 1.40, "#F0FDF4", "#16A34A", radius=0.18, lw=1.2)
    draw_header_banner(4.65, 1.83, 7.0, 0.30, "#15803D", "Empirical Computational Benchmark vs. Discrete Event Simulation (DES)", font_size=8.0)
    
    col_w = 2.15
    # Metric 1
    ax.text(5.75, 1.50, "Analytic Inversion Latency", fontsize=7.0, fontweight='bold', color='#15803D', ha='center')
    ax.text(5.75, 1.25, "< 0.15 ms", fontsize=10.0, fontweight='bold', color='#047857', ha='center')
    ax.text(5.75, 1.02, "Closed-form O(c) evaluation", fontsize=6.6, color='#64748B', ha='center')

    # Metric 2
    ax.text(8.15, 1.50, "DES Monte Carlo Latency", fontsize=7.0, fontweight='bold', color='#B91C1C', ha='center')
    ax.text(8.15, 1.25, "15.2 seconds", fontsize=10.0, fontweight='bold', color='#B91C1C', ha='center')
    ax.text(8.15, 1.02, "25,000 session trajectories", fontsize=6.6, color='#64748B', ha='center')

    # Metric 3
    ax.text(10.55, 1.50, "Real-Time Acceleration", fontsize=7.0, fontweight='bold', color='#6D28D9', ha='center')
    ax.text(10.55, 1.25, "> 100,000x Speedup", fontsize=10.0, fontweight='bold', color='#6D28D9', ha='center')
    ax.text(10.55, 1.02, "Zero simulation barrier", fontsize=6.6, color='#64748B', ha='center')

    # =========================================================================
    # ZONE 4: THEOREM 1 INVARIANT MESH & DOWNSTREAM COUPLING (RIGHT: x=12.1 to 16.0)
    # =========================================================================
    draw_card(12.1, 0.6, 3.9, 8.6, C_BG_AMBER, C_BORDER_AMBER, radius=0.35, lw=1.5)
    draw_header_banner(12.25, 8.82, 3.6, 0.33, ACCENT_AMBER, "4. THEOREM 1 INVARIANT VERIFICATION")

    # Theorem Proof Lattice Card
    draw_card(12.25, 5.80, 3.6, 2.90, "#FFFFFF", ACCENT_AMBER, radius=0.18, lw=1.2)
    draw_header_banner(12.25, 8.38, 3.6, 0.32, ACCENT_AMBER, "Theorem 1: Monotonic Ordering Invariant", font_size=8.2)

    ax.text(14.05, 8.08, r"$\forall \rho < 1.0, \; \forall c \in \mathbb{N}^+: \quad t_{0.50} \leq t_{0.90}$",
            fontsize=8.2, fontweight='bold', ha='center', va='center', color='#B45309')
    
    # 3 Regimes
    regimes = [
        ("Regime 1", r"$C(c, a) \leq 0.10$", r"$t_{0.50} = 0 \leq t_{0.90} = 0$", "Point mass domin.: zero wait at both", "#047857", 7.42),
        ("Regime 2", r"$0.10 < C(c, a) \leq 0.50$", r"$t_{0.50} = 0 < t_{0.90}$", "Median zero; tail wait emerges", "#0284C7", 6.72),
        ("Regime 3", r"$C(c, a) > 0.50$", r"$0 < t_{0.50} < t_{0.90}$", r"$\ln(2C) < \ln(10C) \Rightarrow$ Strict order", "#B91C1C", 6.02),
    ]
    for r_title, r_cond, r_res, r_note, r_col, r_y in regimes:
        draw_card(12.35, r_y - 0.18, 3.4, 0.60, "#FFFDF5", r_col, radius=0.10, lw=0.9)
        ax.text(12.50, r_y + 0.22, f"{r_title}: {r_cond}", fontsize=7.0, fontweight='bold', color=r_col, va='center')
        ax.text(12.50, r_y + 0.02, f"-->  {r_res}", fontsize=7.2, fontweight='bold', color='#0F172A', va='center')
        ax.text(12.50, r_y - 0.12, r_note, fontsize=6.6, fontstyle='italic', color='#64748B', va='center')

    # Empirical Verification Scorecard Card
    draw_card(12.25, 3.10, 3.6, 2.55, "#FFFFFF", ACCENT_TEAL, radius=0.18, lw=1.2)
    draw_header_banner(12.25, 5.33, 3.6, 0.32, ACCENT_TEAL, "Empirical Validation Across 728 Regimes", font_size=8.2)

    metrics = [
        ("Total Regimes Tested", "728 distinct (λ, μ, c)", "#0F172A", 4.98),
        ("Monotonicity Violations", "0 Violations (100.0% Adherence)", "#15803D", 4.45),
        ("Ground Truth MAE (vs. DES)", "9.39 minutes", "#0284C7", 3.92),
        ("Ground Truth RMSE", "15.72 minutes", "#6D28D9", 3.40),
    ]
    for m_label, m_val, m_col, m_y in metrics:
        ax.text(12.45, m_y + 0.12, m_label, fontsize=7.0, color='#475569', va='center')
        ax.text(12.45, m_y - 0.08, m_val, fontsize=7.6, fontweight='bold', color=m_col, va='center')

    # Downstream Integration Card
    draw_card(12.25, 0.80, 3.6, 2.15, "#F0F9FF", "#0284C7", radius=0.18, lw=1.2)
    draw_header_banner(12.25, 2.63, 3.6, 0.32, "#0284C7", "Downstream Multi-Agent Delivery", font_size=8.2)
    ax.text(14.05, 2.25, "Provenance Contract: [ ESTIMATED ]\nConfidence Score: 0.70 - 0.94",
            fontsize=7.4, fontweight='bold', color='#1E40AF', ha='center', linespacing=1.2)
    ax.text(14.05, 1.62, "Feeds ScoringAgent (Wait Utility Penalty)\nFeeds ExplanationAgent (Gemini 2.0 Hedging)\nGuarantees zero negative tail delays",
            fontsize=7.2, color='#1E293B', ha='center', linespacing=1.25)
    ax.text(14.05, 1.05, "FastAPI response: sub-second delivery", fontsize=7.0, fontstyle='italic', color='#64748B', ha='center')

    # =========================================================================
    # BUS CONNECTORS & ARROWS BETWEEN ZONES
    # =========================================================================
    # Connector 1: Zone 1 to Zone 2 (Parameter Ingestion to Markov State Engine)
    ax.annotate('', xy=(4.5, 7.7), xytext=(4.2, 7.7),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_BLUE, lw=2.0, mutation_scale=14))
    b1 = patches.FancyBboxPatch((4.05, 7.82), 0.60, 0.26, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                               facecolor="#FFFFFF", edgecolor=ACCENT_BLUE, linewidth=0.8, zorder=6)
    ax.add_patch(b1)
    ax.text(4.35, 7.95, r"$\lambda, \mu, c$", fontsize=7.2, fontweight='bold', color=ACCENT_BLUE, ha='center', va='center', zorder=7)

    # Connector 2: Zone 2 to Zone 3 (Erlang C Congestion to Percentile Inversion)
    ax.annotate('', xy=(8.15, 4.50), xytext=(8.15, 4.70),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_PURPLE, lw=2.0, mutation_scale=14))
    b2 = patches.FancyBboxPatch((7.25, 4.47), 1.80, 0.26, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                               facecolor="#FFFFFF", edgecolor=ACCENT_PURPLE, linewidth=0.8, zorder=6)
    ax.add_patch(b2)
    ax.text(8.15, 4.60, r"Delay Probability $C(c, a)$", fontsize=7.2, fontweight='bold', color=ACCENT_PURPLE, ha='center', va='center', zorder=7)

    # Connector 3: Zone 3 to Zone 4 (Quantiles to Theorem 1 Invariant Verification)
    ax.annotate('', xy=(12.1, 2.70), xytext=(11.8, 2.70),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_GREEN, lw=2.0, mutation_scale=14))
    b3 = patches.FancyBboxPatch((11.60, 2.82), 0.70, 0.26, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                               facecolor="#FFFFFF", edgecolor=ACCENT_GREEN, linewidth=0.8, zorder=6)
    ax.add_patch(b3)
    ax.text(11.95, 2.95, r"$t_{50}, t_{90}$", fontsize=7.2, fontweight='bold', color=ACCENT_GREEN, ha='center', va='center', zorder=7)

    # Connector 4: Upper Zone 2 to Zone 4 (CDF validation bus)
    ax.annotate('', xy=(12.1, 7.50), xytext=(11.8, 7.50),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_PURPLE, lw=1.8, linestyle="--", mutation_scale=12))
    b4 = patches.FancyBboxPatch((11.55, 7.62), 0.80, 0.24, boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=0.08),
                               facecolor="#FFFFFF", edgecolor=ACCENT_PURPLE, linewidth=0.8, zorder=6)
    ax.add_patch(b4)
    ax.text(11.95, 7.74, "CDF $P(W_q \leq t)$", fontsize=6.8, fontweight='bold', color=ACCENT_PURPLE, ha='center', va='center', zorder=7)

    # Output targets
    dirs = [
        r"C:\Users\HARSH AMBULE\Downloads\paper",
        r"C:\Users\HARSH AMBULE\Downloads\paper\figures",
        r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper",
        r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper\figures",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    primary_png = r"C:\Users\HARSH AMBULE\Downloads\paper\queue-model-flow.png"
    primary_pdf = r"C:\Users\HARSH AMBULE\Downloads\paper\queue-model-flow.pdf"
    plt.savefig(primary_png, dpi=300, facecolor='#FFFFFF', edgecolor='none')
    plt.savefig(primary_pdf, dpi=300, facecolor='#FFFFFF', edgecolor='none')
    plt.close()

    for d in dirs:
        for fname in ["queue-model-flow.png", "fig2_queue_flow.png"]:
            dst = os.path.join(d, fname)
            if os.path.abspath(primary_png) != os.path.abspath(dst):
                shutil.copyfile(primary_png, dst)
        for fname in ["queue-model-flow.pdf", "fig2_queue_flow.pdf"]:
            dst = os.path.join(d, fname)
            if os.path.abspath(primary_pdf) != os.path.abspath(dst):
                shutil.copyfile(primary_pdf, dst)

    print("Advanced Figure 2 rendered and mirrored to all targets successfully!")

if __name__ == "__main__":
    create_advanced_fig2()
