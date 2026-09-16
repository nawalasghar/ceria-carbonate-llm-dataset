"""Small random-forest baseline: predict log10(conductivity) from composition /
processing / measurement features, using GROUPED cross-validation so that no
paper appears in both train and test folds (Section 6.7 validation strategy).
This is a demonstration of the workflow, not a claim of predictive performance."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "results" / "dataset.csv")
df = df.dropna(subset=["conductivity_S_cm"])
df = df[df.conductivity_S_cm > 0]

NUM = ["dopant_fraction", "secondary_phase_wt_pct", "sintering_temp_C",
       "pellet_thickness_um", "conductivity_temp_C"]
CAT = ["ceria_dopant", "secondary_phase", "synthesis_route", "measurement_method",
       "atmosphere", "conductivity_type"]
X, y, groups = df[NUM + CAT], np.log10(df.conductivity_S_cm), df.paper_id

n_groups = groups.nunique()
if len(df) < 8 or n_groups < 3:
    raise SystemExit(f"Need >=8 records from >=3 papers; have {len(df)} from {n_groups}.")

pre = ColumnTransformer([
    ("num", SimpleImputer(strategy="median"), NUM),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="constant", fill_value="missing")),
                      ("oh", OneHotEncoder(handle_unknown="ignore"))]), CAT),
])
model = Pipeline([("pre", pre), ("rf", RandomForestRegressor(n_estimators=300, random_state=0))])
cv = GroupKFold(n_splits=min(5, n_groups))
pred = cross_val_predict(model, X, y, groups=groups, cv=cv)

rmse = float(np.sqrt(np.mean((pred - y) ** 2)))
r2 = float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2))
msg = (f"Records: {len(df)} from {n_groups} papers | GroupKFold({cv.get_n_splits()})\n"
       f"RMSE(log10 sigma) = {rmse:.3f}   R2 = {r2:.3f}\n"
       "Note: tiny pilot dataset; metrics illustrate the grouped-validation workflow only.\n")
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results" / "baseline_metrics.txt").write_text(msg)
print(msg)

fig, ax = plt.subplots(figsize=(4.5, 4.5))
ax.scatter(y, pred, s=30, alpha=0.8)
lo, hi = min(y.min(), pred.min()) - 0.2, max(y.max(), pred.max()) + 0.2
ax.plot([lo, hi], [lo, hi], "k--", lw=1)
ax.set_xlabel("Measured log10 σ (S/cm)"); ax.set_ylabel("Predicted log10 σ (S/cm)")
ax.set_title(f"Grouped-CV parity (RMSE {rmse:.2f})", fontsize=10)
plt.tight_layout(); plt.savefig(ROOT / "figures" / "parity.png", dpi=200)
