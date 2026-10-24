# UK Road Collision Analysis 2025 - CES 2103 Data Analytics, IA3

Reproducible Python project covering **preprocessing, exploratory data analysis (EDA) and confirmatory data analysis (CDA)** of the 2025 Department for Transport (STATS19) road-collision file.

**Primary research question:** Is there a statistically significant association between lighting conditions and collision severity? (H0: independent; H1: associated; alpha = 0.05; Pearson chi-square test of independence.)

> The 4-5 page report is *not* part of this repository. `outputs/analysis_summary.md` collects the verified numbers, figure interpretations and conclusions needed to write it.

## Folder structure

```text
DA_IA3_PROJECT/
├── data/
│   ├── raw/          collisions_2025.csv           (original, never modified; not tracked by Git)
│   ├── reference/    data_guide_2025.xlsx          (official code list; used only to decode values)
│   └── processed/    collisions_2025_processed.csv (generated; not tracked by Git)
├── src/
│   ├── common.py          shared paths, guide lookups, plotting style, statistics helpers
│   ├── 01_inspection.py   inspect raw CSV + guide (schema, dtypes, codes, coverage)
│   ├── 02_preprocessing.py  cleaning, labelling, derived variables, processed dataset
│   ├── 03_eda.py          descriptive statistics, tables, figures 1-6, interpretations
│   ├── 04_cda.py          chi-square test, Cramér's V, Wilson CIs, robustness, figure 7
│   └── 05_summary.py      assembles outputs/analysis_summary.md from the results above
├── outputs/
│   ├── figures/             fig01 ... fig07 (PNG, 300 dpi)
│   ├── tables/              numerical summary tables (CSV)
│   ├── statistical_results/ JSON results + CDA report
│   ├── inspection_report.md, preprocessing_summary.md, figure_interpretations.md
│   └── analysis_summary.md  <- fact base for the written report
├── reports/        (empty; reserved for the written report)
├── run_all.py      run the whole pipeline
├── requirements.txt
└── README.md
```

## Setup (Windows)

Use a **native Windows Python 3.12+** (tested on 3.13). If several Pythons are installed (e.g. MSYS2), call the launcher explicitly - an MSYS2 `python` creates a virtual environment with a non-Windows layout (`.venv\bin`).

```powershell
cd path\to\DA_IA3_Project
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Reproduce everything

From the project root:

```powershell
.\.venv\Scripts\python.exe run_all.py
```

This runs steps 01-05 in order (about 20 seconds), regenerating the processed data, all tables, figures, statistical results and `outputs/analysis_summary.md`. Each step can also be run on its own, e.g. `.\.venv\Scripts\python.exe src\04_cda.py` (steps 02-05 need the outputs of the earlier steps). Paths are resolved relative to the project folder, so the scripts work from any current directory. Random components (bootstrap CIs, Monte Carlo p-value) use a fixed seed.

Input files are detected by extension: exactly one `*.csv` in `data/raw/` and one `*.xlsx` in `data/reference/` are expected.

## Method in brief

- **Preprocessing:** duplicate and ID checks; guide-based code validation and code-to-label mapping (labels are read from the guide, not retyped); `-1` ("missing/out of range") handled per column after distinguishing structural from genuine missingness; date/time parsing; derived month/weekday/hour/period/KSI/dark variables; outliers inspected and kept; raw file hash verified unchanged. No rows are deleted.
- **EDA:** descriptive statistics, frequency tables, severity/lighting/weather/time/road analyses, 6 figures.
- **CDA:** chi-square test of independence on lighting (5 categories) x severity (3), with assumption checks, expected counts, adjusted residuals, Cramér's V (bootstrap CI), Wilson CIs, risk ratios, and one stratified robustness check (urban/rural; police attendance).

## Interpretation notes

- The data are *reported collisions* without traffic exposure: results describe how severity is distributed, not the risk of travelling in darkness. No causal claims are made.
- With ~100k observations p-values are tiny for almost any difference; effect sizes (Cramér's V) carry the practical interpretation.
- The file covers Great Britain (no Northern Ireland forces).

## Git

The folder is not a Git repository yet. `.gitignore` excludes `.venv/`, `data/raw/` and `data/processed/` so the raw and large generated files stay out of version control. Nothing has been pushed anywhere.
