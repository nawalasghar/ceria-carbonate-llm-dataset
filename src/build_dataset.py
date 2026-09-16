"""Merge all LLM-extracted JSON records into a single flat CSV dataset."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "data" / "extracted"
OUT = ROOT / "results" / "dataset.csv"

FIELDS = [
    "composition_label", "ceria_dopant", "dopant_fraction", "secondary_phase",
    "secondary_phase_wt_pct", "synthesis_route", "sintering_temp_C",
    "pellet_thickness_um", "relative_density_pct", "measurement_method",
    "atmosphere", "conductivity_type", "conductivity_S_cm", "conductivity_temp_C",
    "activation_energy_eV", "pmax_mW_cm2", "pmax_temp_C", "ocv_V", "fuel",
    "durability_h", "notes",
]


def load_records(folder: Path) -> pd.DataFrame:
    rows = []
    for f in sorted(folder.glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        for m in rec.get("materials", []):
            row = {"paper_id": rec.get("paper_id", f.stem), "citation": rec.get("citation")}
            row.update({k: m.get(k) for k in FIELDS})
            row["extraction_confidence"] = rec.get("extraction_confidence")
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_records(EXTRACTED)
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} material records from {df['paper_id'].nunique()} papers -> {OUT}")
    print("\nMetadata completeness (% of records with a value):")
    meta = ["measurement_method", "atmosphere", "conductivity_type",
            "pellet_thickness_um", "sintering_temp_C", "activation_energy_eV", "durability_h"]
    present = df[meta].notna()
    present["conductivity_type"] &= df["conductivity_type"].fillna("").str.lower() != "unspecified"
    pct = (present.mean() * 100).round(1)
    for k, v in pct.items():
        print(f"  {k:24s} {v:5.1f}%")
