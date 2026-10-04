"""Heatmap of which metadata fields each paper reports (the data-quality figure)."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results" / "dataset.csv"
OUT = ROOT / "figures" / "metadata_completeness.png"

FIELDS = ["synthesis_route", "sintering_temp_C", "pellet_thickness_um", "relative_density_pct",
          "measurement_method", "atmosphere", "conductivity_type", "conductivity_S_cm",
          "activation_energy_eV", "pmax_mW_cm2", "ocv_V", "durability_h"]
LABELS = ["Synthesis route", "Sintering T", "Thickness", "Rel. density", "Meas. method",
          "Atmosphere", "σ type", "σ value", "Ea", "Pmax", "OCV", "Durability"]

df = pd.read_csv(DATA)
present = df[FIELDS].notna().copy()
present["conductivity_type"] &= df["conductivity_type"].fillna("").str.lower() != "unspecified"
per_paper = present.groupby(df["paper_id"]).max().astype(int)

fig, ax = plt.subplots(figsize=(9, max(3, 0.32 * len(per_paper) + 1.5)))
ax.imshow(per_paper.values, cmap="Greens", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(FIELDS)), LABELS, rotation=45, ha="right")
ax.set_yticks(range(len(per_paper)), per_paper.index)
for i in range(per_paper.shape[0]):
    for j in range(per_paper.shape[1]):
        ax.text(j, i, "✓" if per_paper.iat[i, j] else "–", ha="center", va="center", fontsize=8,
                color="white" if per_paper.iat[i, j] else "grey")
pct = per_paper.mean() * 100
ax.set_title("Metadata reported per paper (column mean: " +
             ", ".join(f"{l} {p:.0f}%" for l, p in zip(LABELS[4:7], pct.iloc[4:7])) + ")", fontsize=9)
plt.tight_layout()
OUT.parent.mkdir(exist_ok=True)
plt.savefig(OUT, dpi=200)
print(f"-> {OUT}")
print((per_paper.mean() * 100).round(0).astype(int).to_string())
