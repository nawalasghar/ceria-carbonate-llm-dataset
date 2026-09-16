# ceria-carbonate-llm-dataset

**LLM-assisted extraction of a metadata-rich pilot dataset of ceria-based composite
electrolytes for low-temperature solid oxide fuel cells (LT-SOFCs), plus a reproducible
grouped-cross-validation baseline.**

---

## Motivation

Ceria–carbonate composite electrolytes routinely achieve conductivities >0.1 S/cm at
300–600 °C, and dozens of papers report performance numbers for slight variants of the
same host system (Sm-, Ca-, Ba-, Al-doped ceria with Na/Li/K carbonate second phases).
Yet no machine-learning study has convincingly generalised across this literature. The
review this repository accompanies argues that the bottleneck is not model choice but
**dataset quality**: reported conductivities are rarely accompanied by

- the **measurement method** (2- or 4-probe DC, AC impedance, EIS),
- the **atmosphere** (air, H₂, wet H₂, fuel-cell condition),
- the **conductivity type** (total, grain, grain-boundary, ionic),
- **electrolyte thickness**, **relative density**, or **activation energy**.

Without those fields, two "0.15 S/cm" numbers from different papers are not comparable,
and any ML model trained across them learns noise. This project builds a small,
fully-inspectable pilot dataset that captures those metadata fields explicitly — including
recording them as `null` when the paper is silent — and demonstrates the downstream
consequences.

## What this repository is

A four-step reproducible workflow:

| # | Step | Script | Output |
|---|------|--------|--------|
| 1 | Extract structured records from full-text papers with a fixed schema | (interactive, LLM) | `data/extracted/*.json` |
| 2 | Merge JSON records into a flat dataset and print completeness | `src/build_dataset.py` | `results/dataset.csv` |
| 3 | Evaluate LLM extractions against manually verified records | `src/evaluate.py` | `results/evaluation.csv` |
| 4 | Plot per-paper metadata completeness | `src/plot_completeness.py` | `figures/metadata_completeness.png` |
| 5 | Grouped-CV random forest baseline (paper-disjoint train/test) | `src/baseline_model.py` | `results/baseline_metrics.txt`, `figures/parity.png` |

## Pilot dataset at a glance

- **9 primary papers** (2010–2024, Raza-group and collaborators): `ref04–ref12`
- **25 material records** — one per distinct composition, sample or measurement condition
- **12 metadata fields** per record (see schema below)
- **Conductivity range**: 6 × 10⁻³ – 3.1 × 10⁻¹ S/cm
- **Dopant space covered**: Sm, Ca, Al, Ba, Ca+Sm, Sm+Ba (as second-phase modifier)
- **Secondary phases**: Na₂CO₃, Li₂CO₃, K₂CO₃, and their binary and ternary mixtures

Two additional PDFs (`ref01_review`, `ref02_book`) are marked *excluded: not a primary
ceria study* in `data/papers/papers_list.csv`; `ref02_book.txt` is a placeholder because
the source PDF is scanned image-only.

## Repository layout

```
data/
├── papers/            plain-text sources (one file per paper)
│   ├── pdf/           original PDFs (gitignored)
│   ├── ref04_30ADC.txt … ref12_Ba-SDC.txt
│   ├── papers_list.csv    paper_id → citation, DOI, status
│   └── paper_txt_template.txt
├── extracted/         LLM-extracted JSON records, one per paper
└── gold/              manually verified records for the evaluation subset

prompts/               extract_prompt.md — the extraction instructions
schema/                extraction_schema.json — the field schema
src/                   build_dataset.py, evaluate.py, plot_completeness.py, baseline_model.py
results/               dataset.csv, evaluation.csv, baseline_metrics.txt
figures/               metadata_completeness.png, parity.png
```

## Extraction schema

Each record in `data/extracted/*.json` follows `schema/extraction_schema.json`:

| Field | Type | Example / allowed values |
|---|---|---|
| `paper_id` | str | `ref06_SDC-Na2CO3` |
| `citation` | str | `Raza et al. 2010, IJHE 35:2684` |
| `materials[]` | list | one entry per distinct composition |
| `materials[].composition_label` | str | `SDC-Na2CO3 (80:20 wt%)` |
| `materials[].ceria_dopant` | str \| null | `Sm`, `Ca`, `Sm+Ca`, `Al`, `Ba` |
| `materials[].dopant_fraction` | number \| null | mole fraction on Ce site |
| `materials[].secondary_phase` | str \| null | `Na2CO3`, `(Li/Na)2CO3`, `none` |
| `materials[].secondary_phase_wt_pct` | number \| null | weight % |
| `materials[].synthesis_route` | str \| null | `co-precipitation`, `sol-gel`, `wet chemical`, … |
| `materials[].sintering_temp_C` | number \| null | °C |
| `materials[].pellet_thickness_um` | number \| null | µm |
| `materials[].relative_density_pct` | number \| null | % |
| `materials[].measurement_method` | str \| null | `EIS`, `2-probe DC`, `4-probe DC`, other |
| `materials[].atmosphere` | str \| null | `air`, `H2`, `H2/O2`, `fuel-cell condition` |
| `materials[].conductivity_type` | str \| null | `total`, `grain`, `grain-boundary`, `ionic`, `unspecified` |
| `materials[].conductivity_S_cm` | number \| null | S/cm |
| `materials[].conductivity_temp_C` | number \| null | °C |
| `materials[].activation_energy_eV` | number \| null | eV |
| `materials[].pmax_mW_cm2` | number \| null | mW/cm² |
| `materials[].pmax_temp_C` | number \| null | °C |
| `materials[].ocv_V` | number \| null | V |
| `materials[].fuel` | str \| null | `H2`, `CH4`, `biogas` |
| `materials[].durability_h` | number \| null | hours |
| `materials[].notes` | str \| null | ambiguities, unit conversions, caveats |
| `extraction_confidence` | enum | `high`, `medium`, `low` |
| `extraction_notes` | str | free text on what was unclear or missing |

## How the extraction was run

Extraction was performed with a large language model (Claude, Anthropic) in an
interactive session using `prompts/extract_prompt.md`, and every record was manually
verified against the source paper.

The prompt instructs the model to **use `null` when the paper is silent** rather than
guess, so that missing metadata is preserved as a measurable signal rather than
imputed silently.

## Reproduce the analysis

**Requirements:** Python ≥ 3.10, no external API access needed for steps 2–5.

```bash
python -m venv .venv
source .venv/bin/activate         # or: .venv\Scripts\activate on Windows
pip install -r requirements.txt

python src/build_dataset.py       # -> results/dataset.csv (+ completeness summary)
python src/plot_completeness.py   # -> figures/metadata_completeness.png
python src/evaluate.py            # -> results/evaluation.csv    (requires data/gold/)
python src/baseline_model.py      # -> results/baseline_metrics.txt, figures/parity.png
```

## Results

### Metadata completeness

Fraction of papers that report each field for at least one of their materials:

| Field | Reported |
|---|---:|
| Synthesis route | 100 % |
| Sintering temperature | 100 % |
| Pellet thickness | 100 % |
| Peak power density | 100 % |
| Measurement method | 78 % |
| Atmosphere | 78 % |
| Conductivity type | 78 % |
| Conductivity value | 78 % |
| Open-circuit voltage | 56 % |
| Activation energy | 33 % |
| Relative density | 11 % |
| Durability | 11 % |

The 22 %-of-papers gap on **method, atmosphere, and conductivity type** is exactly the
point the review makes: nearly one in five papers publishes a conductivity number
without saying how, where or of what.

### Grouped-CV baseline

Random-forest regressor predicting log₁₀ σ from composition, processing and measurement
features, evaluated with 5-fold `GroupKFold` (papers never overlap between train and
test):

| Metric | Value |
|---|---:|
| Records (σ > 0) | 15 |
| Groups (papers) | 7 |
| RMSE (log₁₀ σ) | 0.49 |
| R² | –0.23 |

**Negative R² is the intended finding**, not a bug: with 15 records from 7 papers and
40 % of the critical measurement metadata missing, a paper-disjoint model cannot beat
predicting the training mean. This validates the review's claim that a metadata-complete
dataset is a prerequisite for meaningful ML, not the model architecture.

## Scope and caveats

- **Pilot only.** Built from the papers cited in one review; not a comprehensive
  database. Numbers of records are small, and the baseline model is a workflow
  demonstration, not a performance claim.
- **Not normalised.** Values reported at different temperatures, atmospheres, or with
  different conductivity definitions are preserved as-is. Do not average them without
  taking `conductivity_type`, `conductivity_temp_C`, and `atmosphere` into account.
- **Abstract-only extractions** are flagged `extraction_confidence: low`. So are records
  where key values were read from figure descriptions rather than tables.
- **Paper-internal inconsistencies** (e.g. an abstract stating 0.19 S/cm at 460 °C and
  the body at 600 °C) are captured in the `notes` field of the affected material rather
  than silently resolved.
- **Composition ambiguities.** When a paper's stated synthesis ratio disagrees with its
  formula label (e.g. ref07 CSDC's 4:1:1 vs. Ce₀.₈Sm₀.₂₋ₓCaₓO₂₋δ), the discrepancy is
  documented rather than picked.

## Citation

If you use this dataset or code, please cite the accompanying review (reference to be
added on publication) and this repository.

## License

MIT for code. Extracted data values are derived from the cited publications and remain
subject to their original sources.
