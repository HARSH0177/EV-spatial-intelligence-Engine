import os
import subprocess
import shutil
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# Publication styling
plt.rcParams.update({
    'font.size': 10.5,
    'font.family': 'sans-serif',
    'axes.labelsize': 11,
    'axes.titlesize': 11.5,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9.5,
    'figure.titlesize': 13,
    'figure.dpi': 300
})

paper_dir = r"C:\Users\HARSH AMBULE\Downloads\paper"
figures_dir = os.path.join(paper_dir, "figures")
repo_paper_dir = r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\paper"
repo_figures_dir = os.path.join(repo_paper_dir, "figures")
assets_dir = r"C:\Users\HARSH AMBULE\Downloads\ev advisor new live\ev advisor new live\assets"
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

for d in [figures_dir, repo_paper_dir, repo_figures_dir]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------
# 1. Convert SVG diagrams to PNG and PDF
# -------------------------------------------------------------
svg_targets = [
    ("architecture-diagram.svg", "architecture-diagram", 1200, 720),
    ("queue-model-flow.svg", "queue-model-flow", 1100, 400),
    ("data-provenance-matrix.svg", "data-provenance-matrix", 1100, 360),
]

for svg_name, base_name, w, h in svg_targets:
    svg_path = os.path.join(assets_dir, svg_name)
    if os.path.exists(svg_path):
        html_wrapper = os.path.join(figures_dir, f"temp_{base_name}.html")
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
        png_out = os.path.join(figures_dir, f"{base_name}.png")
        cmd = [
            edge_path,
            "--headless",
            "--disable-gpu",
            f"--window-size={w},{h}",
            "--hide-scrollbars",
            f"--screenshot={png_out}",
            html_wrapper
        ]
        subprocess.run(cmd, check=True)
        if os.path.exists(html_wrapper):
            os.remove(html_wrapper)
        
        # Convert PNG to high-DPI PDF
        pdf_out = os.path.join(figures_dir, f"{base_name}.pdf")
        with Image.open(png_out) as img:
            rgb_img = img.convert("RGB")
            rgb_img.save(pdf_out, "PDF", resolution=300.0)
        print(f"Rendered {base_name}.png and {base_name}.pdf")

# Also create aliases matching fig1, fig2, fig3 for backward compatibility
for base, num in [("architecture-diagram", "fig1_architecture"), ("queue-model-flow", "fig2_queue_flow"), ("data-provenance-matrix", "fig3_data_provenance")]:
    shutil.copyfile(os.path.join(figures_dir, f"{base}.png"), os.path.join(figures_dir, f"{num}.png"))

# -------------------------------------------------------------
# 2. Generate Figure 4: Queue Delay Curves (Proposed vs Baselines)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.2, 4.8), dpi=300)

rhos = np.array([0.25, 0.50, 0.69, 0.81, 0.90])
sim_gt = np.array([0.00, 7.84, 31.56, 62.05, 121.47])
proposed_mmc = np.array([0.00, 8.30, 33.83, 72.92, 154.80])
lumped_mm1 = np.array([5.76, 17.27, 37.99, 74.83, 155.42])
static_heur = np.array([15.00, 15.00, 15.00, 15.00, 15.00])

ax.plot(rhos, sim_gt, 'o-', color='#1B5E20', linewidth=2.4, markersize=8, label='Simulation Ground Truth (25k sessions)', zorder=5)
ax.plot(rhos, proposed_mmc, 's--', color='#0D47A1', linewidth=2.0, markersize=7, label='Proposed M/M/c Erlang C (MAE: 9.39 min, RMSE: 15.72 min)', zorder=4)
ax.plot(rhos, lumped_mm1, '^-.', color='#C62828', linewidth=1.8, markersize=7, label='Lumped M/M/1 Baseline (MAE: 13.67 min, RMSE: 17.21 min)', zorder=3)
ax.plot(rhos, static_heur, 'd:', color='#546E7A', linewidth=1.5, markersize=6, label='Static 15-min Baseline (MAE: 38.45 min, RMSE: 53.10 min)', zorder=2)

ax.set_xlabel(r'Traffic Intensity ($\rho = \lambda / (c\cdot\mu)$)', fontweight='bold')
ax.set_ylabel(r'90th Percentile Wait Time $p_{90}$ (minutes)', fontweight='bold')
ax.set_title(r'Comparative Tail Queue Delay ($p_{90}$) across Traffic Intensities ($c=4$ ports, $\mu=2.0$)', pad=12, fontweight='bold')
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
print("Generated fig_queue_comparison.pdf and .png")

# -------------------------------------------------------------
# 3. Generate Figure 5: Siting Sensitivity (4 Independent Panels)
# -------------------------------------------------------------
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

plt.suptitle('Multi-Attribute Siting Utility vs. Greedy POI Clustering (Controlled Synthetic Analysis)', fontsize=12.5, fontweight='bold', y=1.03)
plt.tight_layout()

fig5_pdf = os.path.join(figures_dir, "fig_siting_synthetic.pdf")
fig5_png = os.path.join(figures_dir, "fig_siting_synthetic.png")
fig.savefig(fig5_pdf, format='pdf', bbox_inches='tight')
fig.savefig(fig5_png, format='png', dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(figures_dir, "fig5_siting_tradeoffs.png"), format='png', dpi=300, bbox_inches='tight')
plt.close(fig)
print("Generated fig_siting_synthetic.pdf and .png")

# -------------------------------------------------------------
# 4. Copy all figure files to paper/ root and repo directories
# -------------------------------------------------------------
all_figure_names = [
    "architecture-diagram.pdf", "architecture-diagram.png",
    "queue-model-flow.pdf", "queue-model-flow.png",
    "data-provenance-matrix.pdf", "data-provenance-matrix.png",
    "fig_queue_comparison.pdf", "fig_queue_comparison.png",
    "fig_siting_synthetic.pdf", "fig_siting_synthetic.png",
    "fig1_architecture.png", "fig2_queue_flow.png", "fig3_data_provenance.png",
    "fig4_queue_comparison.png", "fig5_siting_tradeoffs.png"
]

for fname in all_figure_names:
    src = os.path.join(figures_dir, fname)
    if os.path.exists(src):
        # copy to paper root
        shutil.copyfile(src, os.path.join(paper_dir, fname))
        # copy to repo paper root
        shutil.copyfile(src, os.path.join(repo_paper_dir, fname))
        # copy to repo paper/figures/
        shutil.copyfile(src, os.path.join(repo_figures_dir, fname))

print("Successfully synchronized all figure assets across paper and repository directories.")
