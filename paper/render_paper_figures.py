import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt

# Set publication style
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'figure.dpi': 300
})

figures_dir = r"C:\Users\HARSH AMBULE\Downloads\paper\figures"
source_figures_dir = r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\assets"
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

os.makedirs(figures_dir, exist_ok=True)

# 1. Convert SVGs to PNG via Headless Edge with exact viewport crop
svg_targets = [
    ("architecture-diagram.svg", "fig1_architecture.png", 1100, 680),
    ("queue-model-flow.svg", "fig2_queue_flow.png", 1000, 360),
    ("data-provenance-matrix.svg", "fig3_data_provenance.png", 1000, 320),
]

for svg_name, png_name, w, h in svg_targets:
    svg_path = os.path.join(source_figures_dir, svg_name)
    if os.path.exists(svg_path):
        # Create a clean HTML wrapper to render SVG at high DPI
        html_wrapper = os.path.join(figures_dir, f"temp_{svg_name}.html")
        with open(html_wrapper, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #FFFFFF; display: flex; justify-content: center; align-items: center; width: {w}px; height: {h}px; overflow: hidden; }}
  img {{ width: 100%; height: 100%; object-fit: contain; }}
</style>
</head>
<body>
  <img src="file:///{svg_path.replace(os.sep, '/')}" />
</body>
</html>""")
        
        out_png = os.path.join(figures_dir, png_name)
        cmd = [
            edge_path,
            "--headless",
            "--disable-gpu",
            f"--window-size={w},{h}",
            "--hide-scrollbars",
            f"--screenshot={out_png}",
            html_wrapper
        ]
        subprocess.run(cmd, check=True)
        if os.path.exists(html_wrapper):
            os.remove(html_wrapper)
        print(f"Rendered {png_name} successfully.")

# 2. Generate Figure 4: Queue Delay Curves (Proposed vs Baselines vs Sim Ground Truth)
fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)

rhos = np.array([0.25, 0.50, 0.69, 0.81, 0.90])
sim_gt = np.array([0.00, 7.84, 31.56, 62.05, 121.47])
proposed_mmc = np.array([0.00, 8.30, 33.83, 72.92, 154.80])
lumped_mm1 = np.array([5.76, 17.27, 37.99, 74.83, 155.42])
static_heur = np.array([15.00, 15.00, 15.00, 15.00, 15.00])

ax.plot(rhos, sim_gt, 'o-', color='#1B5E20', linewidth=2.5, markersize=8, label='Simulation Ground Truth (25k sessions)', zorder=5)
ax.plot(rhos, proposed_mmc, 's--', color='#0D47A1', linewidth=2, markersize=7, label='Proposed M/M/c Erlang C (MAE: 9.39 min)', zorder=4)
ax.plot(rhos, lumped_mm1, '^-.', color='#B7410E', linewidth=1.8, markersize=7, label='Lumped M/M/1 Baseline (MAE: 13.67 min)', zorder=3)
ax.plot(rhos, static_heur, 'd:', color='#546E7A', linewidth=1.5, markersize=6, label='Static 15-min Heuristic (MAE: 38.45 min)', zorder=2)

ax.set_xlabel(r'Traffic Intensity ($\rho = \lambda / (c\cdot\mu)$)')
ax.set_ylabel(r'90th Percentile Wait Time $p_{90}$ (minutes)')
ax.set_title(r'Comparative Tail Queue Delay ($p_{90}$) across Traffic Intensities ($c=4$ ports)', pad=12, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_xlim(0.2, 0.95)
ax.set_ylim(-5, 175)
ax.legend(frameon=True, facecolor='#FAFAFA', edgecolor='#D0D0D0')
plt.tight_layout()
fig4_path = os.path.join(figures_dir, "fig4_queue_comparison.png")
fig.savefig(fig4_path, dpi=300)
plt.close(fig)
print("Generated fig4_queue_comparison.png successfully.")

# 3. Generate Figure 5: Spatial Siting Viability Trade-offs
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 4.2), dpi=300)

labels = ['Greedy POI', 'Proposed Engine']
colors = ['#B0BEC5', '#2E7D32']

# Metric 1: Grid Headroom
ax1.bar(labels, [350.1, 410.5], color=colors, width=0.55, edgecolor='#37474F')
ax1.set_ylabel('Available Capacity (kW)')
ax1.set_title('Grid Headroom\n(+17.3%)', fontweight='bold')
ax1.set_ylim(0, 480)
ax1.grid(axis='y', linestyle='--', alpha=0.5)
for i, v in enumerate([350.1, 410.5]):
    ax1.text(i, v + 10, f"{v:.1f} kW", ha='center', fontweight='bold', fontsize=10)

# Metric 2: Competitor Saturation
ax2.bar(labels, [3.4, 2.2], color=['#FF8A65', '#4FC3F7'], width=0.55, edgecolor='#37474F')
ax2.set_ylabel('Stations within 1.5 km')
ax2.set_title('Competitor Cannibalization\n(-35.3%)', fontweight='bold')
ax2.set_ylim(0, 4.5)
ax2.grid(axis='y', linestyle='--', alpha=0.5)
for i, v in enumerate([3.4, 2.2]):
    ax2.text(i, v + 0.1, f"{v:.1f}", ha='center', fontweight='bold', fontsize=10)

# Metric 3: Multi-Criteria Utility
ax3.bar(labels, [0.339, 0.394], color=['#CFD8DC', '#7E57C2'], width=0.55, edgecolor='#37474F')
ax3.set_ylabel('Normalized Score (0 - 1)')
ax3.set_title('Composite Utility Score\n(+16.1%)', fontweight='bold')
ax3.set_ylim(0, 0.48)
ax3.grid(axis='y', linestyle='--', alpha=0.5)
for i, v in enumerate([0.339, 0.394]):
    ax3.text(i, v + 0.01, f"{v:.3f}", ha='center', fontweight='bold', fontsize=10)

plt.suptitle('Spatial Siting Resilience: Multi-Attribute Matrix vs. Greedy POI Clustering', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig5_path = os.path.join(figures_dir, "fig5_siting_tradeoffs.png")
fig.savefig(fig5_path, dpi=300)
plt.close(fig)
print("Generated fig5_siting_tradeoffs.png successfully.")

# 4. Generate Figure 6: Global Scalability & Latency Breakdown
fig, ax = plt.subplots(figsize=(8.5, 4.5), dpi=300)

cities = ['Dubai', 'Pune', 'Berlin', 'Nagpur', 'Bengaluru', 'London', 'San Francisco', 'São Paulo', 'Tokyo', 'Nairobi']
latencies = [850, 860, 870, 875, 880, 890, 840, 905, 910, 920]
continents = ['Middle East', 'Asia', 'Europe', 'Asia', 'Asia', 'Europe', 'N. America', 'S. America', 'Asia', 'Africa']

y_pos = np.arange(len(cities))
colors_bar = ['#81C784' if l < 870 else '#64B5F6' if l < 900 else '#BA68C8' for l in latencies]

bars = ax.barh(y_pos, latencies, color=colors_bar, height=0.65, edgecolor='#455A64')
ax.set_yticks(y_pos)
ax.set_yticklabels([f"{c} ({cnt})" for c, cnt in zip(cities, continents)])
ax.set_xlabel('Median Response Latency $p_{50}$ (milliseconds)')
ax.set_title('Global Metropolitan Generalization & Sub-Second Latency (Google Cloud Run)', pad=12, fontweight='bold')
ax.axvline(880, color='#E53935', linestyle='--', linewidth=1.5, label='Median Across All Runs ($p_{50} = 880$ ms)')
ax.set_xlim(700, 1000)
ax.grid(axis='x', linestyle='--', alpha=0.5)

for bar in bars:
    w = bar.get_width()
    ax.text(w + 5, bar.get_y() + bar.get_height()/2, f"{int(w)} ms", va='center', fontsize=9.5, fontweight='bold')

ax.legend(loc='lower right', frameon=True, facecolor='#FFFFFF')
plt.tight_layout()
fig6_path = os.path.join(figures_dir, "fig6_global_latency.png")
fig.savefig(fig6_path, dpi=300)
plt.close(fig)
print("Generated fig6_global_latency.png successfully.")
