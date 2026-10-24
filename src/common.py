"""Shared paths, guide-driven code lookups, plotting style and statistics helpers.

Every path is resolved relative to the project root (the parent of ``src/``), so the
scripts behave identically no matter which directory they are launched from.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REF_DIR = ROOT / "data" / "reference"
PROC_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "outputs" / "figures"
TAB_DIR = ROOT / "outputs" / "tables"
STAT_DIR = ROOT / "outputs" / "statistical_results"
OUT_DIR = ROOT / "outputs"

PROCESSED_CSV = PROC_DIR / "collisions_2025_processed.csv"

for _d in (PROC_DIR, FIG_DIR, TAB_DIR, STAT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Column names in the 2025 CSV that differ from the names used in the official guide.
GUIDE_ALIASES = {
    "enhanced_severity_collision": "enhanced_collision_severity",
    "collision_adjusted_severity_serious": "collision_adjusted_serious",
    "collision_adjusted_severity_slight": "collision_adjusted_slight",
}

# Fields whose values are codes defined in the guide's "2024_code_list" sheet.
# (local_authority_* are handled separately: the guide lists > 200 codes for them.)
CODED_FIELDS = [
    "police_force", "collision_severity", "enhanced_severity_collision", "day_of_week",
    "first_road_class", "road_type", "junction_detail_historic", "junction_detail",
    "junction_control", "second_road_class", "pedestrian_crossing_human_control_historic",
    "pedestrian_crossing_physical_facilities_historic", "pedestrian_crossing",
    "light_conditions", "weather_conditions", "road_surface_conditions",
    "special_conditions_at_site", "carriageway_hazards_historic", "carriageway_hazards",
    "urban_or_rural_area", "did_police_officer_attend_scene_of_accident",
    "trunk_road_flag", "collision_injury_based",
]

SEVERITY_ORDER = ["Fatal", "Serious", "Slight"]
LIGHT_ORDER = ["Daylight", "Darkness - lights lit", "Darkness - lights unlit",
               "Darkness - no lighting", "Darkness - lighting unknown"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Fixed colour assignment per severity (colour-vision-deficiency-safe: Okabe-Ito based).
SEV_COLORS = {"Fatal": "#9B1C1C", "Serious": "#E69F00", "Slight": "#56B4E9"}
NEUTRAL = "#4D4D4D"
ACCENT = "#0072B2"


def find_single(folder: Path, pattern: str) -> Path:
    """Return the only file matching ``pattern`` in ``folder`` (detects actual filenames)."""
    hits = sorted(folder.glob(pattern))
    if len(hits) != 1:
        raise FileNotFoundError(f"Expected exactly one {pattern} in {folder}, found {len(hits)}")
    return hits[0]


def raw_csv_path() -> Path:
    return find_single(RAW_DIR, "*.csv")


def guide_path() -> Path:
    return find_single(REF_DIR, "*.xlsx")


def read_raw() -> pd.DataFrame:
    """Read the raw CSV exactly as shipped (no transformation)."""
    return pd.read_csv(raw_csv_path(), low_memory=False, encoding="utf-8")


def read_guide() -> pd.DataFrame:
    """Collision-table rows of the guide's code list."""
    g = pd.read_excel(guide_path(), sheet_name="2024_code_list")
    return g[g["table"] == "collision"].copy()


def guide_lookup(guide: pd.DataFrame, csv_field: str) -> dict:
    """Return {int code: label} for a coded field, read from the official guide."""
    field = GUIDE_ALIASES.get(csv_field, csv_field)
    rows = guide[guide["field name"] == field]
    out = {}
    for code, label in zip(rows["code/format"], rows["label"]):
        try:
            key = int(str(code).strip())
        except ValueError:
            continue
        out[key] = label if isinstance(label, str) else None
    return out


def save_json(obj, path: Path) -> None:
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (pd.Timestamp,)):
            return o.isoformat()
        raise TypeError(type(o))
    path.write_text(json.dumps(obj, indent=2, default=default), encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_processed() -> pd.DataFrame:
    """Load the processed dataset with the ordered categorical types restored."""
    df = pd.read_csv(PROCESSED_CSV, low_memory=False)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["severity"] = pd.Categorical(df["severity"], SEVERITY_ORDER, ordered=True)
    df["light"] = pd.Categorical(df["light"], LIGHT_ORDER, ordered=True)
    df["weekday"] = pd.Categorical(df["weekday"], WEEKDAY_ORDER, ordered=True)
    return df


def fmt_p(p: float) -> str:
    if p == 0 or p < 1e-300:
        return "< 1e-300"
    return f"{p:.3e}" if p < 0.001 else f"{p:.4f}"


def wilson_ci(k: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (np.nan, np.nan)
    ci = stats.binomtest(int(k), int(n)).proportion_ci(confidence_level=conf, method="wilson")
    return float(ci.low), float(ci.high)


def cramers_v(table: np.ndarray, chi2: float) -> dict:
    """Cramér's V and the Bergsma bias-corrected V for an r x c table."""
    n = table.sum()
    r, c = table.shape
    k = min(r - 1, c - 1)
    v = float(np.sqrt(chi2 / (n * k)))
    phi2 = chi2 / n
    phi2c = max(0.0, phi2 - (r - 1) * (c - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    cc = c - (c - 1) ** 2 / (n - 1)
    v_corr = float(np.sqrt(phi2c / min(rc - 1, cc - 1)))
    return {"v": v, "v_bias_corrected": v_corr, "df_star": k}


def cohen_v_label(v: float, df_star: int) -> str:
    """Cohen (1988) benchmarks for Cramér's V, scaled by min(r-1, c-1)."""
    small, medium, large = 0.10 / np.sqrt(df_star), 0.30 / np.sqrt(df_star), 0.50 / np.sqrt(df_star)
    if v < small:
        return "negligible"
    if v < medium:
        return "small"
    if v < large:
        return "medium"
    return "large"


def set_plot_style() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.titlesize": 11.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 10, "axes.edgecolor": "#BBBBBB", "axes.labelcolor": "#222222",
        "grid.color": "#E6E6E6", "grid.linewidth": 0.7,
        "xtick.color": "#333333", "ytick.color": "#333333",
        "legend.frameon": False, "axes.spines.top": False, "axes.spines.right": False,
    })


def save_fig(fig, name: str) -> Path:
    path = FIG_DIR / name
    fig.savefig(path)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path
