"""Step 2 - Preprocess the raw collision data.

The raw CSV is only ever read (its SHA-256 is verified before and after). The processed
dataset keeps every row and the original code columns verbatim, and adds guide-based
label columns, cleaned numeric fields and derived time variables.

Outputs: data/processed/collisions_2025_processed.csv, outputs/preprocessing_summary.md,
outputs/tables/02_*.csv and outputs/statistical_results/02_preprocessing_metrics.json
"""
import hashlib

import numpy as np
import pandas as pd

from common import (CODED_FIELDS, LIGHT_ORDER, MONTH_NAMES, OUT_DIR, PROCESSED_CSV, ROOT,
                    SEVERITY_ORDER, STAT_DIR, TAB_DIR, WEEKDAY_ORDER, guide_lookup, raw_csv_path,
                    read_guide, read_raw, save_json)

# Short names for the variables that the analysis uses most.
SHORT_NAMES = {
    "collision_severity": "severity", "light_conditions": "light", "weather_conditions": "weather",
    "road_surface_conditions": "road_surface", "urban_or_rural_area": "area_type",
    "police_force": "police_force_name", "collision_injury_based": "severity_reporting_basis",
}
LEGACY_COLS = [
    "junction_detail_historic", "pedestrian_crossing_human_control_historic",
    "pedestrian_crossing_physical_facilities_historic", "special_conditions_at_site",
    "carriageway_hazards_historic",
]
# Labels the guide leaves blank for code 0 are interpreted as "none recorded".
BLANK_ZERO_LABEL = "None recorded"


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pct(x, n) -> str:
    return f"{100 * x / n:.2f}%"


def main() -> None:
    csv_path = raw_csv_path()
    hash_before = sha256(csv_path)
    raw = read_raw()
    guide = read_guide()
    n0, c0 = raw.shape
    log = []  # (step, result) pairs written to the summary
    m = {"raw_rows": n0, "raw_cols": c0, "raw_sha256": hash_before}

    # ---------------------------------------------------------------- 1. duplicates
    idx_dup = int(raw["collision_index"].duplicated().sum())
    ref_dup = int(raw["collision_ref_no"].duplicated().sum())
    full_dup = int(raw.duplicated().sum())
    content_dup = int(raw.drop(columns=["collision_index", "collision_ref_no"]).duplicated().sum())
    idx_mismatch = int((raw["collision_index"] != raw["collision_year"].astype(str) + raw["collision_ref_no"]).sum())
    near_keys = ["date", "time", "location_easting_osgr", "location_northing_osgr",
                 "number_of_vehicles", "number_of_casualties", "police_force"]
    near = raw[raw.duplicated(subset=near_keys, keep=False)].sort_values(near_keys)
    near.to_csv(TAB_DIR / "02_possible_duplicate_pairs.csv", index=False)
    m.update(dup_collision_index=idx_dup, dup_collision_ref_no=ref_dup, dup_full_rows=full_dup,
             dup_all_but_ids=content_dup, index_year_ref_mismatch=idx_mismatch,
             near_duplicate_rows=len(near))
    log.append(("Duplicate checks",
                f"Duplicated `collision_index`: {idx_dup}; duplicated `collision_ref_no`: {ref_dup}; fully duplicated rows: {full_dup}; "
                f"rows identical in every field except the two IDs: {content_dup}; rows where `collision_index` != `collision_year`+`collision_ref_no`: {idx_mismatch}. "
                f"A looser screen (same date, time, easting/northing, vehicles, casualties and force) flags {len(near)} rows "
                f"({len(near) // 2} pair) with different IDs - listed in `outputs/tables/02_possible_duplicate_pairs.csv`. "
                f"Different IDs mean they are separately recorded collisions, so they were **kept**. No rows removed."))

    # ---------------------------------------------------------------- 2. date / time
    dt_date = pd.to_datetime(raw["date"], format="%d/%m/%Y", errors="coerce")
    t = pd.to_datetime(raw["time"], format="%H:%M", errors="coerce")
    bad_date, bad_time = int(dt_date.isna().sum()), int(t.isna().sum())
    outside_year = int((dt_date.dt.year != 2025).sum())
    weekday_from_date = dt_date.dt.day_name()
    dow_lookup = guide_lookup(guide, "day_of_week")
    weekday_from_code = raw["day_of_week"].map(dow_lookup)
    dow_mismatch = int((weekday_from_date != weekday_from_code).sum())
    m.update(unparseable_dates=bad_date, unparseable_times=bad_time, dates_outside_2025=outside_year,
             weekday_code_vs_date_mismatch=dow_mismatch, date_min=str(dt_date.min().date()), date_max=str(dt_date.max().date()))
    log.append(("Date/time conversion",
                f"`date` (DD/MM/YYYY) and `time` (HH:MM) parsed with explicit formats: {bad_date} unparseable dates, {bad_time} unparseable times, "
                f"{outside_year} dates outside 2025 (range {m['date_min']} to {m['date_max']}). The guide's `day_of_week` code (1 = Sunday) agrees with the weekday "
                f"computed from the date " + ("in every row." if dow_mismatch == 0 else f"except in {dow_mismatch} rows.")))

    # ---------------------------------------------------------------- 3. sentinel / missing values
    nan_cols = raw.columns[raw.isna().any()].tolist()
    nan_summary = {c: int(raw[c].isna().sum()) for c in nan_cols}
    m["nan_columns"] = nan_summary

    la_dist_all_minus1 = bool((raw["local_authority_district"] == -1).all())
    m["local_authority_district_all_minus1"] = la_dist_all_minus1

    legacy_missing = (raw[LEGACY_COLS] == -1)
    all_legacy_missing = legacy_missing.all(axis=1)
    any_legacy_present = ~legacy_missing.all(axis=1)
    legacy_forces = sorted(raw.loc[any_legacy_present, "police_force"].unique().tolist())
    mixed = int((legacy_missing.any(axis=1) & ~all_legacy_missing).sum())
    legacy_equals_not_injury = bool((any_legacy_present == (raw["collision_injury_based"] == 0)).all())
    m.update(legacy_all_missing_rows=int(all_legacy_missing.sum()), legacy_any_present_rows=int(any_legacy_present.sum()),
             legacy_rows_with_partial_missing=mixed, legacy_present_iff_not_injury_based=legacy_equals_not_injury)

    enh_missing = raw["enhanced_severity_collision"] == -1
    inj0 = raw["collision_injury_based"] == 0
    enh_equals_inj0 = bool((enh_missing == inj0).all())
    scot = raw["police_force"] == 99
    trunk_m1_scot = int(((raw["trunk_road_flag"] == -1) & scot).sum())
    trunk_m1 = int((raw["trunk_road_flag"] == -1).sum())
    lsoa_m1 = raw["lsoa_of_accident_location"] == "-1"
    lsoa_m1_scot = int((lsoa_m1 & scot).sum())
    jc_m1_nonjunction = int(((raw["junction_control"] == -1) & (raw["junction_detail"] == 0)).sum())
    jc_code0 = int((raw["junction_control"] == 0).sum())
    m.update(enhanced_missing_equals_not_injury_based=enh_equals_inj0, trunk_missing=trunk_m1, trunk_missing_scotland=trunk_m1_scot,
             lsoa_missing=int(lsoa_m1.sum()), lsoa_missing_scotland=lsoa_m1_scot, scotland_rows=int(scot.sum()),
             junction_control_minus1_at_nonjunction=jc_m1_nonjunction, junction_control_code0_rows=jc_code0)

    log.append(("Missing-value detection",
                f"True blanks (NaN) exist only in {', '.join(f'`{k}` ({v})' for k, v in nan_summary.items())} (location fields: 'Null if not known' in the guide); these rows were kept because location is not used in the analysis. "
                f"All other missingness is encoded with the guide's sentinel `-1` (\"Data missing or out of range\") - see `outputs/tables/02_missing_value_handling.csv`."))
    log.append(("Structural vs. genuine `-1` values",
                f"(a) `local_authority_district` is `-1` in {'all' if la_dist_all_minus1 else 'some'} rows, i.e. carries no information in the 2025 file - the column was dropped (the ONS-code fields `local_authority_ons_district`/`local_authority_highway(_current)` remain). "
                f"(b) The five legacy-specification fields ({', '.join(f'`{c}`' for c in LEGACY_COLS)}) are `-1` together in {int(all_legacy_missing.sum()):,} rows ({pct(all_legacy_missing.sum(), n0)}); "
                f"only {int(any_legacy_present.sum()):,} rows from {len(legacy_forces)} forces carry legacy values (these are exactly the rows with `collision_injury_based` = 0: {'verified' if legacy_equals_not_injury else 'NOT exact'}), "
                f"and {mixed} rows are only partly missing. These `-1`s mean 'not collected under this specification', not a data error. "
                f"The harmonised 2024-specification fields (`junction_detail`, `pedestrian_crossing`, `carriageway_hazards`) are used instead; legacy columns are retained unlabelled. "
                f"(c) `enhanced_severity_collision` is `-1` exactly when `collision_injury_based` = 0 ({'verified' if enh_equals_inj0 else 'NOT exact'}; {int(enh_missing.sum()):,} rows), "
                f"i.e. the enhanced scale exists only for injury-based reporting. "
                f"(d) `trunk_road_flag` is `-1` in {trunk_m1:,} rows, {trunk_m1_scot:,} of them Police Scotland; `lsoa_of_accident_location` is `-1` in {int(lsoa_m1.sum()):,} rows, {lsoa_m1_scot:,} of them Police Scotland (LSOAs are England/Wales only, as the guide states). "
                f"(e) `junction_control` never takes the guide's code 0 ({jc_code0} rows); instead {jc_m1_nonjunction:,} of its {int((raw['junction_control'] == -1).sum()):,} `-1` values occur where `junction_detail` = 0 (not at a junction). "
                f"These were recoded to 'Not at junction or within 20 metres' (the guide's definition of code 0); the remaining `-1` values were treated as missing."))

    # ---------------------------------------------------------------- 4. build processed frame
    df = raw.drop(columns=["local_authority_district"]).copy()
    dropped_cols = ["local_authority_district"]

    # numeric cleaning: -1 sentinel -> NaN in road-number and OSGR fields
    for c in ["first_road_number", "second_road_number"]:
        df[c] = df[c].where(df[c] != -1)
    df["lsoa_of_accident_location"] = df["lsoa_of_accident_location"].where(~lsoa_m1)
    df["local_authority_highway_current"] = df["local_authority_highway_current"].where(df["local_authority_highway_current"] != "-1")
    df["enhanced_severity_collision_clean"] = df["enhanced_severity_collision"].where(df["enhanced_severity_collision"] != -1)

    # code -> label for every coded field (guide-driven); -1 becomes missing
    label_cols = {}
    for field in CODED_FIELDS:
        if field not in df:
            continue
        lk = guide_lookup(guide, field)
        lk = {k: (v if v is not None else BLANK_ZERO_LABEL) for k, v in lk.items()}
        lk.pop(-1, None)
        out = SHORT_NAMES.get(field, f"{field}_label")
        label_cols[field] = out
        df[out] = df[field].map(lk)
    # recode structural junction_control -1 (see above)
    jc_fix = (df["junction_control"] == -1) & (df["junction_detail"] == 0)
    df.loc[jc_fix, "junction_control_label"] = guide_lookup(guide, "junction_control")[0]
    m["junction_control_recoded_rows"] = int(jc_fix.sum())

    # derived time variables
    df["datetime"] = pd.to_datetime(raw["date"] + " " + raw["time"], format="%d/%m/%Y %H:%M")
    df["month"] = df["datetime"].dt.month
    df["month_name"] = df["month"].map(lambda i: MONTH_NAMES[i - 1])
    df["weekday"] = weekday_from_date
    df["is_weekend"] = df["weekday"].isin(["Saturday", "Sunday"])
    df["hour"] = df["datetime"].dt.hour
    bins = [-1, 5, 9, 15, 19, 23]
    names = ["Night (00-05)", "Morning (06-09)", "Midday (10-15)", "Evening peak (16-19)", "Late evening (20-23)"]
    df["time_period"] = pd.cut(df["hour"], bins=bins, labels=names).astype(str)
    # analysis flags
    df["is_ksi"] = df["collision_severity"].isin([1, 2])  # Killed or Seriously Injured (fatal + serious)
    df["is_dark"] = df["light_conditions"].isin([4, 5, 6, 7]).astype("boolean").mask(df["light_conditions"] == -1)
    df["flag_daylight_small_hours"] = (df["light_conditions"] == 1) & (df["hour"] <= 3)
    df["flag_dark_midday"] = df["light_conditions"].isin([4, 5, 6, 7]) & df["hour"].between(10, 14)
    df["flag_multi_casualty_10plus"] = df["number_of_casualties"] >= 10

    # consistency checks (reported, never "fixed" silently)
    sev_vs_enh = pd.crosstab(raw["collision_severity"], raw["enhanced_severity_collision"])
    sev_vs_enh.to_csv(TAB_DIR / "02_severity_vs_enhanced_severity.csv")
    expected = {1: {1, -1}, 2: {5, 6, 7, -1}, 3: {3, -1}}
    sev_incons = int(sum(sev_vs_enh.loc[s, c] for s in sev_vs_enh.index for c in sev_vs_enh.columns
                         if c not in expected[s]))
    cas_lt1 = int((raw["number_of_casualties"] < 1).sum())
    veh_lt1 = int((raw["number_of_vehicles"] < 1).sum())
    speed_valid = {20, 30, 40, 50, 60, 70}
    speed_invalid = int((~raw["speed_limit"].isin(speed_valid)).sum())
    rc_nonzero_num = int(((raw["first_road_class"].isin([5, 6])) & (raw["first_road_number"] != 0)).sum())
    rc_numbered_zero = int(((raw["first_road_class"].isin([1, 2, 3, 4])) & (raw["first_road_number"] == 0)).sum())
    lat_bad = int((~raw["latitude"].dropna().between(49.8, 60.9)).sum())
    lon_bad = int((~raw["longitude"].dropna().between(-8.7, 1.8)).sum())
    ds_n = int(df["flag_daylight_small_hours"].sum())
    ds_months = df.loc[df["flag_daylight_small_hours"], "month"].value_counts().sort_index().to_dict()
    dm_n = int(df["flag_dark_midday"].sum())
    m.update(severity_vs_enhanced_inconsistent=sev_incons, casualties_lt1=cas_lt1, vehicles_lt1=veh_lt1,
             speed_limit_invalid=speed_invalid, c_or_unclassified_with_road_number=rc_nonzero_num,
             numbered_class_with_zero_number=rc_numbered_zero, lat_outside_uk_box=lat_bad, lon_outside_uk_box=lon_bad,
             daylight_00_03h=ds_n, daylight_00_03h_by_month=ds_months, dark_10_14h=dm_n)
    log.append(("Invalid values & category consistency (vs. official guide)",
                f"Every code in the {len(CODED_FIELDS)} coded fields exists in the guide (0 unmapped codes; see `outputs/tables/01_code_coverage.csv`). "
                f"`speed_limit` has {speed_invalid} values outside the valid set {sorted(speed_valid)}; `number_of_vehicles`/`number_of_casualties` have {veh_lt1}/{cas_lt1} values below 1; "
                f"coordinates outside a UK bounding box: {lat_bad} latitudes, {lon_bad} longitudes. "
                f"`collision_severity` and `enhanced_severity_collision` are mutually consistent " + ("in every row" if sev_incons == 0 else f"except in {sev_incons} rows")
                + " (Fatal<->Fatal, Serious<->Very/Moderately/Less serious, Slight<->Slight; where the enhanced value is not `-1`). "
                f"Road numbers: {rc_nonzero_num} C/Unclassified roads carry a number and {rc_numbered_zero} numbered-class roads have number 0. "
                f"Plausibility flags (flagged, **not removed** - lighting is an officer's judgement): {ds_n} 'Daylight' collisions between 00:00 and 03:59 "
                f"({100 * ds_n / int((raw['light_conditions'] == 1).sum()):.2f}% of Daylight records; spread across all months, by month: {', '.join(f'{MONTH_NAMES[k - 1]} {v}' for k, v in ds_months.items())}, so not explained by midsummer twilight alone) "
                f"and {dm_n} 'Darkness' collisions between 10:00 and 14:59 (could reflect fog, tunnels or recording error). Flag columns `flag_daylight_small_hours` and `flag_dark_midday` are provided."))
    log.append(("Unknown / 'Other' categories",
                "Codes meaning 'unknown (self reported)' or 'Unknown' (weather 9, road type 9, junction/crossing 99, etc.) and 'Other' (weather 8) are valid guide codes; they were kept as their own labelled categories "
                "rather than set to missing, and are shown separately in tables/figures."))

    # outlier inspection
    out_rows = []
    for c in ["number_of_vehicles", "number_of_casualties"]:
        q1, q3 = raw[c].quantile([0.25, 0.75])
        hi = q3 + 1.5 * (q3 - q1)
        out_rows.append({"variable": c, "q1": q1, "q3": q3, "upper_fence_1.5IQR": hi, "n_above_fence": int((raw[c] > hi).sum()),
                         "pct_above_fence": round(100 * (raw[c] > hi).mean(), 2), "max": int(raw[c].max()),
                         "n_ge_10": int((raw[c] >= 10).sum()), "p99": raw[c].quantile(0.99)})
    outl = pd.DataFrame(out_rows)
    outl.to_csv(TAB_DIR / "02_outlier_inspection.csv", index=False)
    top = raw.nlargest(5, "number_of_casualties")[["collision_index", "number_of_vehicles", "number_of_casualties", "collision_severity", "date", "time"]]
    top.to_csv(TAB_DIR / "02_top_casualty_collisions.csv", index=False)
    m["max_casualties"] = int(raw["number_of_casualties"].max())
    m["max_vehicles"] = int(raw["number_of_vehicles"].max())
    log.append(("Outlier inspection",
                f"Both count variables are right-skewed. The 1.5xIQR rule is degenerate for them (casualties: Q1 = Q3 = 1, so every collision with 2+ casualties, "
                f"{int(outl.loc[1, 'n_above_fence']):,} = {outl.loc[1, 'pct_above_fence']}%, would be flagged; vehicles: {int(outl.loc[0, 'n_above_fence']):,} = {outl.loc[0, 'pct_above_fence']}% above the fence), "
                f"so extremes were inspected through the 99th percentile (vehicles {outl.loc[0, 'p99']:.0f}, casualties {outl.loc[1, 'p99']:.0f}) and the maxima (vehicles {m['max_vehicles']}; casualties {m['max_casualties']}; "
                f"{int(outl.loc[1, 'n_ge_10'])} collisions with >= 10 casualties, {int(outl.loc[0, 'n_ge_10'])} with >= 10 vehicles). "
                f"These are plausible rare multi-vehicle / mass-casualty events that cannot be disproved from the dataset, so **no outliers were removed**; medians and percentiles are reported alongside means. Flag: `flag_multi_casualty_10plus`."))

    # ---------------------------------------------------------------- 5. missing-value handling table
    desc = {
        "location_easting_osgr": ("Genuine (guide: 'Null if not known')", "Left as NaN; rows kept (location not used)"),
        "location_northing_osgr": ("Genuine (guide: 'Null if not known')", "Left as NaN; rows kept (location not used)"),
        "longitude": ("Genuine (guide: 'Null if not known')", "Left as NaN; rows kept (location not used)"),
        "latitude": ("Genuine (guide: 'Null if not known')", "Left as NaN; rows kept (location not used)"),
        "local_authority_district": ("Field empty for the whole 2025 file", "Column dropped"),
        "light_conditions": ("Genuine missing/out of range", "Label = NaN; rows kept; excluded only from the lighting x severity test (complete-case)"),
        "road_surface_conditions": ("Genuine missing/out of range", "Label = NaN; rows kept; excluded from surface-specific summaries"),
        "first_road_class": ("Genuine missing/out of range", "Label = NaN; road number set to NaN"),
        "second_road_class": ("Genuine missing/out of range", "Label = NaN"),
        "junction_detail": ("Genuine missing/out of range", "Label = NaN"),
        "junction_control": ("Mostly structural (not at a junction, coded -1 instead of 0)", "Recoded to 'Not at junction...' where junction_detail = 0; otherwise NaN"),
        "pedestrian_crossing": ("Genuine missing/out of range", "Label = NaN"),
        "carriageway_hazards": ("Genuine missing/out of range", "Label = NaN"),
        "trunk_road_flag": ("Mostly structural (Police Scotland)", "Label = NaN"),
        "lsoa_of_accident_location": ("Structural (England/Wales only)", "Set to NaN"),
        "enhanced_severity_collision": ("Structural (only for injury-based reporting)", "Label = NaN; cleaned copy `enhanced_severity_collision_clean`"),
        "first_road_number": ("Genuine missing/out of range", "Set to NaN"),
        "second_road_number": ("Mostly structural (-1 whenever second_road_class is 0 = no second road, or itself missing/unknown)", "Set to NaN"),
        "local_authority_highway_current": ("Genuine missing/out of range", "Set to NaN"),
    }
    for c in LEGACY_COLS:
        desc[c] = ("Structural (field not collected under the 2024 specification)", "Retained as raw codes; not used in analysis")
    mv = []
    for c in raw.columns:
        n_nan = int(raw[c].isna().sum())
        n_m1 = int((raw[c].astype(str) == "-1").sum())
        if n_nan or n_m1:
            kind, handling = desc.get(c, ("Unclassified", "Reviewed"))
            mv.append({"column": c, "n_nan": n_nan, "n_minus_one": n_m1, "pct_missing": round(100 * (n_nan + n_m1) / n0, 2),
                       "interpretation": kind, "handling": handling})
    mvdf = pd.DataFrame(mv).sort_values("pct_missing", ascending=False)
    mvdf.to_csv(TAB_DIR / "02_missing_value_handling.csv", index=False)

    # ---------------------------------------------------------------- 6. finalise
    df["severity"] = pd.Categorical(df["severity"], SEVERITY_ORDER, ordered=True)
    df["light"] = pd.Categorical(df["light"], LIGHT_ORDER, ordered=True)
    df["weekday"] = pd.Categorical(df["weekday"], WEEKDAY_ORDER, ordered=True)
    df.to_csv(PROCESSED_CSV, index=False)

    assert sha256(csv_path) == hash_before, "raw file changed!"
    n1, c1 = df.shape
    m.update(processed_rows=n1, processed_cols=c1, rows_removed=n0 - n1, dropped_columns=dropped_cols,
             label_columns=sorted(label_cols.values()),
             derived_columns=["datetime", "month", "month_name", "weekday", "is_weekend", "hour", "time_period", "is_ksi", "is_dark",
                              "flag_daylight_small_hours", "flag_dark_midday", "flag_multi_casualty_10plus", "enhanced_severity_collision_clean"],
             raw_unchanged=True, processed_file=PROCESSED_CSV.relative_to(ROOT).as_posix(),
             processed_size_mb=round(PROCESSED_CSV.stat().st_size / 1e6, 1))
    save_json(m, STAT_DIR / "02_preprocessing_metrics.json")

    cmp_df = pd.DataFrame({"": ["Rows", "Columns"], "Original": [n0, c0], "Processed": [n1, c1]})
    cmp_df.to_csv(TAB_DIR / "02_dimension_comparison.csv", index=False)
    log.append(("Code-to-label transformation",
                f"{len(label_cols)} coded fields were labelled from the guide's `2024_code_list` sheet (read programmatically, not retyped). Original code columns are retained verbatim; labels are in "
                f"`severity`, `light`, `weather`, `road_surface`, `area_type`, `police_force_name`, `severity_reporting_basis` and `<field>_label` columns. `-1` becomes a missing label. "
                f"Guide code 0 for `special_conditions_at_site`/`carriageway_hazards` has a blank label; it is labelled '{BLANK_ZERO_LABEL}'."))
    log.append(("Derived variables",
                "`datetime`, `month`, `month_name`, `weekday` (from the date), `is_weekend`, `hour`, `time_period` (Night 00-05, Morning 06-09, Midday 10-15, Evening peak 16-19, Late evening 20-23), "
                "`is_ksi` (Fatal or Serious), `is_dark` (guide codes 4-7), plus the three plausibility/outlier flag columns."))

    lines = [
        "# Preprocessing summary", "",
        f"Source file: `{csv_path.relative_to(ROOT).as_posix()}` (SHA-256 `{hash_before[:16]}...`, verified unchanged after processing). "
        f"Processed file: `{m['processed_file']}` ({m['processed_size_mb']} MB).", "",
        "## Original vs. processed dimensions", "", cmp_df.to_markdown(index=False), "",
        f"No rows were removed ({n0 - n1}). Columns: -{len(dropped_cols)} dropped ({', '.join(dropped_cols)}), "
        f"+{c1 - (c0 - len(dropped_cols))} added (labels, cleaned fields, derived variables and flags).", "",
        "## Operations and results", "",
    ]
    for i, (step, res) in enumerate(log, 1):
        lines += [f"{i}. **{step}.** {res}", ""]
    lines += ["## Missing-value handling table", "", mvdf.to_markdown(index=False), "",
              "## Outlier inspection", "", outl.to_markdown(index=False), "",
              "## Data types in the processed file", "", df.dtypes.astype(str).value_counts().to_frame("n_columns").to_markdown(), ""]
    (OUT_DIR / "preprocessing_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Processed: {n0:,}x{c0} -> {n1:,}x{c1}; rows removed: {n0 - n1}; raw file unchanged.")


if __name__ == "__main__":
    main()
