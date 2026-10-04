"""Compare LLM-extracted records against manually verified gold records.

For every paper present in data/gold/, matches materials by composition_label
(case-insensitive, whitespace-normalised) and scores each field:
  - numeric fields: correct if within 5 % relative tolerance
  - text fields:    correct if normalised strings match
  - null handling:  both null = correct; one null = miss
Outputs results/evaluation.csv (per-field precision) and a summary.
"""
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
EXTRACTED = ROOT / "data" / "extracted"
OUT = ROOT / "results" / "evaluation.csv"

NUMERIC = {"dopant_fraction", "secondary_phase_wt_pct", "sintering_temp_C",
           "pellet_thickness_um", "relative_density_pct", "conductivity_S_cm",
           "conductivity_temp_C", "activation_energy_eV", "pmax_mW_cm2",
           "pmax_temp_C", "ocv_V", "durability_h"}
TEXT = {"ceria_dopant", "secondary_phase", "synthesis_route", "measurement_method",
        "atmosphere", "conductivity_type", "fuel"}
FIELDS = sorted(NUMERIC | TEXT)


def norm(s):
    return re.sub(r"[\s_\-–]+", "", str(s)).lower() if s is not None else None


def match(gold, pred, field):
    if gold is None and pred is None:
        return "both_null"
    if gold is None or pred is None:
        return "null_mismatch"
    if field in NUMERIC:
        try:
            g, p = float(gold), float(pred)
        except (TypeError, ValueError):
            return "wrong"
        return "correct" if abs(g - p) <= 0.05 * max(abs(g), 1e-12) else "wrong"
    return "correct" if norm(gold) == norm(pred) else "wrong"


def main():
    rows = []
    for gf in sorted(GOLD.glob("*.json")):
        ef = EXTRACTED / gf.name
        if not ef.exists():
            print(f"skip {gf.name}: no extracted file")
            continue
        gold = json.loads(gf.read_text(encoding="utf-8"))
        pred = json.loads(ef.read_text(encoding="utf-8"))
        pred_by_label = {norm(m["composition_label"]): m for m in pred.get("materials", [])}
        for gm in gold.get("materials", []):
            pm = pred_by_label.get(norm(gm["composition_label"]))
            for f in FIELDS:
                outcome = match(gm.get(f), pm.get(f) if pm else None, f) if pm else "material_missed"
                rows.append({"paper_id": gf.stem, "material": gm["composition_label"],
                             "field": f, "outcome": outcome})
    df = pd.DataFrame(rows)
    if df.empty:
        print("No gold records found in data/gold/.")
        return
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT.with_name("evaluation_detail.csv"), index=False)

    # per-field accuracy, counting both_null as correct and excluding nothing
    scored = df[df.outcome != "material_missed"].copy()
    scored["ok"] = scored.outcome.isin(["correct", "both_null"])
    summary = scored.groupby("field").agg(n=("ok", "size"), accuracy=("ok", "mean"),
                                          null_mismatch=("outcome", lambda s: (s == "null_mismatch").mean()))
    summary["accuracy"] = (summary["accuracy"] * 100).round(1)
    summary["null_mismatch"] = (summary["null_mismatch"] * 100).round(1)
    summary.to_csv(OUT)
    missed = (df.outcome == "material_missed").sum() // len(FIELDS)
    print(summary.to_string())
    print(f"\nOverall field accuracy: {scored.ok.mean()*100:.1f}%  |  materials missed entirely: {missed}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
