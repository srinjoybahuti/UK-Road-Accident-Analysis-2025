"""Step 1 - Inspect the raw collision CSV and the official data guide (read-only).

Nothing is modified. Outputs: outputs/tables/01_*.csv, outputs/inspection_report.md and
outputs/statistical_results/01_inspection_metrics.json
"""
import pandas as pd

from common import (CODED_FIELDS, GUIDE_ALIASES, OUT_DIR, ROOT, STAT_DIR, TAB_DIR, guide_lookup,
                    guide_path, raw_csv_path, read_guide, read_raw, save_json)


def main() -> None:
    csv_path, xlsx_path = raw_csv_path(), guide_path()
    raw_bytes = csv_path.read_bytes()
    has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
    raw_bytes.decode("utf-8")  # raises if the file is not valid UTF-8
    crlf = raw_bytes.count(b"\r\n")

    df = read_raw()
    guide_all = pd.read_excel(xlsx_path, sheet_name=None)
    guide = read_guide()
    guide_fields = set(guide["field name"])

    # ---- column profile ------------------------------------------------------------
    rows = []
    for col in df.columns:
        s = df[col]
        gname = GUIDE_ALIASES.get(col, col)
        rows.append({
            "column": col, "dtype": str(s.dtype), "n_missing_nan": int(s.isna().sum()),
            "n_minus_one": int((s == -1).sum()) if pd.api.types.is_numeric_dtype(s) or s.dtype == "object" else 0,
            "n_unique": int(s.nunique()), "example": s.iloc[0],
            "in_guide": gname in guide_fields, "guide_name": gname if gname != col else "",
        })
    profile = pd.DataFrame(rows)
    # string columns: count the literal "-1" sentinel too
    for i, col in enumerate(df.columns):
        if not pd.api.types.is_numeric_dtype(df[col]):
            profile.loc[i, "n_minus_one"] = int((df[col].astype(str) == "-1").sum())
    profile.to_csv(TAB_DIR / "01_column_profile.csv", index=False)

    # ---- code coverage against the guide ------------------------------------------
    cov = []
    for col in CODED_FIELDS:
        lk = guide_lookup(guide, col)
        vals = df[col]
        bad = ~vals.isin(lk.keys())
        cov.append({
            "column": col, "n_codes_in_guide": len(lk), "n_distinct_in_data": int(vals.nunique()),
            "codes_not_in_guide": sorted(vals[bad].unique().tolist()), "rows_not_in_guide": int(bad.sum()),
            "n_minus_one": int((vals == -1).sum()), "pct_minus_one": round(100 * (vals == -1).mean(), 2),
        })
    cov = pd.DataFrame(cov)
    cov.to_csv(TAB_DIR / "01_code_coverage.csv", index=False)

    # ---- fields with free-form / very long code lists ------------------------------
    la_checks = []
    for col in ["local_authority_ons_district", "local_authority_highway"]:
        gcodes = set(guide.loc[guide["field name"] == col, "code/format"].astype(str))
        miss = ~df[col].astype(str).isin(gcodes)
        la_checks.append({"column": col, "n_distinct": int(df[col].nunique()),
                          "rows_with_code_not_in_guide_list": int(miss.sum()),
                          "codes_not_in_guide_list": sorted(df.loc[miss, col].astype(str).unique().tolist())})
    la_checks.append({"column": "local_authority_highway_current", "n_distinct": int(df["local_authority_highway_current"].nunique()),
                      "rows_with_code_not_in_guide_list": 0,
                      "codes_not_in_guide_list": ["guide provides no code list ('See latest ONS code list')"]})
    la_checks.append({"column": "local_authority_district", "n_distinct": int(df["local_authority_district"].nunique()),
                      "rows_with_code_not_in_guide_list": 0,
                      "codes_not_in_guide_list": [f"all {int((df['local_authority_district'] == -1).sum())} rows are -1"]})
    pd.DataFrame(la_checks).to_csv(TAB_DIR / "01_local_authority_coverage.csv", index=False)

    metrics = {
        "csv_file": csv_path.relative_to(ROOT).as_posix(), "csv_size_bytes": csv_path.stat().st_size,
        "csv_encoding": "UTF-8" + (" with BOM" if has_bom else " (no BOM)"), "crlf_line_endings": crlf > 0,
        "guide_file": xlsx_path.relative_to(ROOT).as_posix(), "guide_sheets": {k: list(v.shape) for k, v in guide_all.items()},
        "rows": len(df), "columns": df.shape[1],
        "dtype_counts": df.dtypes.astype(str).value_counts().to_dict(),
        "collision_year_values": sorted(df["collision_year"].unique().tolist()),
        "columns_renamed_in_guide": GUIDE_ALIASES,
        "columns_not_in_guide": profile.loc[~profile["in_guide"], "column"].tolist(),
        "columns_with_nan": profile.loc[profile["n_missing_nan"] > 0, ["column", "n_missing_nan"]].to_dict("records"),
        "coded_fields_with_codes_outside_guide": cov.loc[cov["rows_not_in_guide"] > 0, "column"].tolist(),
    }
    save_json(metrics, STAT_DIR / "01_inspection_metrics.json")

    # ---- human-readable report -----------------------------------------------------
    lines = [
        "# Step 1 - Raw data and data-guide inspection", "",
        f"- **Collision file:** `{metrics['csv_file']}` ({metrics['csv_size_bytes'] / 1e6:.1f} MB), {metrics['csv_encoding']}, "
        f"comma-separated, header row present.",
        f"- **Guide file:** `{metrics['guide_file']}` - sheets: "
        + ", ".join(f"`{k}` ({v[0]} rows x {v[1]} cols)" for k, v in metrics["guide_sheets"].items()) + ".",
        f"- **Dimensions:** {len(df):,} rows x {df.shape[1]} columns; dtypes: {metrics['dtype_counts']}.",
        f"- `collision_year` takes only the value(s) {metrics['collision_year_values']}.",
        f"- Columns whose names differ between CSV and guide: {GUIDE_ALIASES}.",
        f"- CSV columns with no entry in the guide's collision table: {metrics['columns_not_in_guide'] or 'none'}.",
        f"- Columns containing NaN (true blanks): "
        + (", ".join(f"`{d['column']}` ({d['n_missing_nan']})" for d in metrics['columns_with_nan']) or "none") + ".",
        f"- Coded fields with codes absent from the guide: {metrics['coded_fields_with_codes_outside_guide'] or 'none'}.", "",
        "## Column profile", "", profile.drop(columns=["example"]).to_markdown(index=False), "",
        "## Code coverage against the official guide", "", cov.to_markdown(index=False), "",
        "## Local-authority code coverage", "", pd.DataFrame(la_checks).to_markdown(index=False), "",
        "Note: the guide's sheet is titled `2024_code_list`; it is the only code list supplied and is used for the 2025 file. "
        "The sheet `2011_to_2024_conversion` documents how legacy (2011-specification) fields map to the 2024 specification.",
    ]
    (OUT_DIR / "inspection_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Inspected {csv_path.name}: {len(df):,} x {df.shape[1]}; coded fields with out-of-guide codes: "
          f"{metrics['coded_fields_with_codes_outside_guide'] or 'none'}")


if __name__ == "__main__":
    main()
