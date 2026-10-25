"""Step 3 - Exploratory data analysis: summary tables (outputs/tables/03_*.csv), figures 1-6
(outputs/figures/) and data-driven interpretations (outputs/figure_interpretations.md).
"""
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import (ACCENT, LIGHT_ORDER, MONTH_NAMES, NEUTRAL, OUT_DIR, SEV_COLORS, SEVERITY_ORDER,
                    STAT_DIR, TAB_DIR, WEEKDAY_ORDER, load_processed, save_fig, save_json,
                    set_plot_style, wilson_ci)

GREY = "#9A9A9A"


def wrap(s, w=22):
    return "\n".join(textwrap.wrap(str(s), w))


def freq_table(df, col, order=None, name=None):
    s = df[col].astype("object").where(df[col].notna(), "Missing (-1)")
    vc = s.value_counts()
    if order is not None:
        vc = vc.reindex([o for o in order if o in vc.index] + [i for i in vc.index if i not in order])
    out = vc.rename_axis("category").reset_index(name="n")
    out.insert(0, "variable", name or col)
    out["pct_of_all"] = (100 * out["n"] / len(df)).round(2)
    valid = out["category"] != "Missing (-1)"
    out["pct_of_valid"] = np.where(valid, (100 * out["n"] / out.loc[valid, "n"].sum()).round(2), np.nan)
    return out


def ksi_table(df, col, order=None, min_n=0):
    g = df.dropna(subset=[col]).groupby(col, observed=True)
    rows = []
    for key, sub in g:
        n = len(sub)
        fatal = int((sub["severity"] == "Fatal").sum())
        serious = int((sub["severity"] == "Serious").sum())
        lo, hi = wilson_ci(fatal + serious, n)
        flo, fhi = wilson_ci(fatal, n)
        rows.append({"variable": col, "category": key, "n": n, "fatal": fatal, "serious": serious, "slight": n - fatal - serious,
                     "fatal_pct": 100 * fatal / n, "fatal_ci_low": 100 * flo, "fatal_ci_high": 100 * fhi,
                     "ksi_pct": 100 * (fatal + serious) / n, "ksi_ci_low": 100 * lo, "ksi_ci_high": 100 * hi})
    out = pd.DataFrame(rows)
    if order is not None:
        out["category"] = pd.Categorical(out["category"], order, ordered=True)
        out = out.sort_values("category")
        out["category"] = out["category"].astype(str)
    return out


def main() -> None:
    set_plot_style()
    df = load_processed()
    N = len(df)
    R = {"n": N}  # numbers reused by interpretations / summary

    # ================================================================ descriptive statistics
    num_vars = ["number_of_vehicles", "number_of_casualties", "speed_limit", "hour", "month"]
    rows = []
    for c in num_vars:
        s = df[c]
        rows.append({"variable": c, "n": int(s.count()), "mean": s.mean(), "median": s.median(), "mode": s.mode().iloc[0],
                     "std": s.std(), "min": s.min(), "q1": s.quantile(.25), "q3": s.quantile(.75), "p99": s.quantile(.99),
                     "max": s.max(), "skewness": s.skew()})
    desc = pd.DataFrame(rows).round(3)
    desc.to_csv(TAB_DIR / "03_descriptive_numeric.csv", index=False)
    R["desc"] = desc.set_index("variable").to_dict("index")

    freq = pd.concat([
        freq_table(df, "severity", SEVERITY_ORDER),
        freq_table(df, "light", LIGHT_ORDER),
        freq_table(df, "weather"),
        freq_table(df, "road_surface"),
        freq_table(df, "road_type_label"),
        freq_table(df, "area_type"),
        freq_table(df, "first_road_class_label"),
        freq_table(df, "junction_detail_label"),
        freq_table(df, "junction_control_label"),
        freq_table(df, "pedestrian_crossing_label"),
        freq_table(df.assign(speed_limit_mph=df["speed_limit"].astype(str)), "speed_limit_mph"),
        freq_table(df, "weekday", WEEKDAY_ORDER),
        freq_table(df, "month_name", MONTH_NAMES),
        freq_table(df, "time_period"),
        freq_table(df, "severity_reporting_basis"),
        freq_table(df, "trunk_road_flag_label"),
        freq_table(df, "did_police_officer_attend_scene_of_accident_label"),
    ], ignore_index=True)
    freq.to_csv(TAB_DIR / "03_frequency_tables.csv", index=False)
    f = lambda v, c: freq[(freq.variable == v) & (freq.category == c)].iloc[0]  # noqa: E731

    # ================================================================ univariate
    sev = freq[freq.variable == "severity"].set_index("category")
    R["sev_n"] = sev["n"].to_dict(); R["sev_pct"] = sev["pct_of_all"].to_dict()
    R["ksi_n"] = int(sev.loc[["Fatal", "Serious"], "n"].sum()); R["ksi_pct"] = 100 * R["ksi_n"] / N

    monthly = (df.groupby(["month", "month_name"]).agg(collisions=("severity", "size"), ksi=("is_ksi", "sum"),
                                                      dark=("is_dark", lambda s: s.sum()), valid_light=("is_dark", "count"),
                                                      casualties=("number_of_casualties", "sum")).reset_index())
    monthly["ksi_pct"] = 100 * monthly["ksi"] / monthly["collisions"]
    monthly["dark_pct"] = 100 * monthly["dark"] / monthly["valid_light"]
    monthly["days_in_month"] = pd.to_datetime(dict(year=2025, month=monthly["month"], day=1)).dt.days_in_month
    monthly["collisions_per_day"] = monthly["collisions"] / monthly["days_in_month"]
    monthly.to_csv(TAB_DIR / "03_monthly_summary.csv", index=False)

    days = pd.Series(pd.date_range("2025-01-01", "2025-12-31"))
    n_weekend_days, n_weekday_days = int((days.dt.day_of_week >= 5).sum()), int((days.dt.day_of_week < 5).sum())
    hourly = (df.groupby(["hour", "is_weekend"]).size().unstack(fill_value=0)
              .rename(columns={False: "weekday_total", True: "weekend_total"}))
    hourly["weekday_per_day"] = hourly["weekday_total"] / n_weekday_days
    hourly["weekend_per_day"] = hourly["weekend_total"] / n_weekend_days
    hk = ksi_table(df, "hour").set_index("category")
    hourly["ksi_pct"] = hk["ksi_pct"].values; hourly["ksi_ci_low"] = hk["ksi_ci_low"].values; hourly["ksi_ci_high"] = hk["ksi_ci_high"].values
    hourly["dark_pct"] = 100 * df.groupby("hour")["is_dark"].apply(lambda s: s.sum() / s.count())
    hourly.reset_index().to_csv(TAB_DIR / "03_hourly_summary.csv", index=False)

    weekday = ksi_table(df, "weekday", WEEKDAY_ORDER)
    weekday.to_csv(TAB_DIR / "03_weekday_summary.csv", index=False)

    R["month_max"] = monthly.loc[monthly["collisions"].idxmax(), ["month_name", "collisions"]].tolist()
    R["month_min"] = monthly.loc[monthly["collisions"].idxmin(), ["month_name", "collisions"]].tolist()
    R["month_dark_max"] = monthly.loc[monthly["dark_pct"].idxmax(), ["month_name", "dark_pct"]].tolist()
    R["month_dark_min"] = monthly.loc[monthly["dark_pct"].idxmin(), ["month_name", "dark_pct"]].tolist()
    R["month_ksi_max"] = monthly.loc[monthly["ksi_pct"].idxmax(), ["month_name", "ksi_pct"]].tolist()
    R["month_ksi_min"] = monthly.loc[monthly["ksi_pct"].idxmin(), ["month_name", "ksi_pct"]].tolist()
    R["hour_peak_weekday"] = int(hourly["weekday_per_day"].idxmax()); R["hour_peak_weekend"] = int(hourly["weekend_per_day"].idxmax())
    R["hour_peak_weekday_val"] = float(hourly["weekday_per_day"].max()); R["hour_peak_weekend_val"] = float(hourly["weekend_per_day"].max())
    R["hour_ksi_max"] = int(hourly["ksi_pct"].idxmax()); R["hour_ksi_max_val"] = float(hourly["ksi_pct"].max())
    R["hour_ksi_min"] = int(hourly["ksi_pct"].idxmin()); R["hour_ksi_min_val"] = float(hourly["ksi_pct"].min())
    R["weekday_counts"] = weekday.set_index("category")["n"].to_dict()
    R["weekday_ksi"] = weekday.set_index("category")["ksi_pct"].to_dict()
    R["weekday_per_day_total"] = float(hourly["weekday_per_day"].sum()); R["weekend_per_day_total"] = float(hourly["weekend_per_day"].sum())
    R["hourly_weekday_morning_peak"] = float(hourly.loc[7:9, "weekday_per_day"].mean())
    R["pm_peak_weekday_hours"] = hourly.loc[15:17, "weekday_per_day"].round(2).to_dict()
    R["monthly"] = monthly.set_index("month_name")[["collisions", "ksi_pct", "dark_pct"]].to_dict("index")

    # ================================================================ bivariate: severity x lighting
    lt = df.dropna(subset=["light"])
    ct = pd.crosstab(lt["light"], lt["severity"]).reindex(index=LIGHT_ORDER)[SEVERITY_ORDER]
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    sl = ksi_table(df, "light", LIGHT_ORDER)
    sl.to_csv(TAB_DIR / "03_severity_by_lighting.csv", index=False)
    pd.concat([ct, ct_pct.add_suffix("_row_pct")], axis=1).assign(total=ct.sum(axis=1)).to_csv(TAB_DIR / "03_severity_by_lighting_crosstab.csv")
    R["light_ksi"] = sl.set_index("category")[["n", "fatal_pct", "ksi_pct"]].to_dict("index")
    R["light_ksi_overall_valid"] = float(100 * lt["is_ksi"].mean())

    # ================================================================ severity x road/weather/etc.
    df["speed_limit_mph"] = df["speed_limit"].astype(str)
    cond_specs = [("speed_limit_mph", None), ("weather", None), ("road_surface", None), ("road_type_label", None),
                  ("area_type", None), ("junction_detail_label", None), ("first_road_class_label", None),
                  ("time_period", None), ("is_weekend", None), ("month_name", MONTH_NAMES),
                  ("severity_reporting_basis", None), ("trunk_road_flag_label", None),
                  ("did_police_officer_attend_scene_of_accident_label", None)]
    cond = pd.concat([ksi_table(df, c, o) for c, o in cond_specs], ignore_index=True)
    cond.to_csv(TAB_DIR / "03_ksi_by_conditions.csv", index=False)
    R["ksi_overall"] = float(100 * df["is_ksi"].mean())
    cget = lambda v: cond[cond.variable == v].set_index("category")  # noqa: E731
    R["speed_ksi"] = cget("speed_limit_mph")["ksi_pct"].to_dict()
    R["speed_n"] = cget("speed_limit_mph")["n"].to_dict()
    R["weather_ksi"] = cget("weather")[["n", "ksi_pct", "ksi_ci_low", "ksi_ci_high"]].to_dict("index")
    R["surface_ksi"] = cget("road_surface")[["n", "ksi_pct"]].to_dict("index")
    R["roadtype_ksi"] = cget("road_type_label")[["n", "ksi_pct"]].to_dict("index")
    R["area_ksi"] = cget("area_type")[["n", "ksi_pct"]].to_dict("index")
    R["junction_ksi"] = cget("junction_detail_label")[["n", "ksi_pct"]].to_dict("index")
    R["tp_ksi"] = cget("time_period")[["n", "ksi_pct"]].to_dict("index")
    R["reporting_ksi"] = cget("severity_reporting_basis")[["n", "ksi_pct"]].to_dict("index")
    R["attend_ksi"] = cget("did_police_officer_attend_scene_of_accident_label")[["n", "ksi_pct"]].to_dict("index")
    R["weekend_ksi"] = cget("is_weekend")[["n", "ksi_pct"]].to_dict("index")

    # lighting x area / speed (descriptive confounding view)
    la = (df.dropna(subset=["light", "area_type"]).query("area_type in ['Urban','Rural']")
          .groupby(["area_type", "light"], observed=True).agg(n=("is_ksi", "size"), ksi_pct=("is_ksi", lambda s: 100 * s.mean())).reset_index())
    la.to_csv(TAB_DIR / "03_ksi_by_lighting_and_area.csv", index=False)
    R["light_area"] = la.pivot(index="light", columns="area_type", values="ksi_pct").round(2).to_dict("index")
    R["area_share_by_light"] = (100 * pd.crosstab(lt["light"], lt["area_type"], normalize="index")["Rural"]).round(1).to_dict()
    R["speed_share_by_light_ge60"] = (100 * lt.assign(fast=lt["speed_limit"] >= 60).groupby("light", observed=True)["fast"].mean()).round(1).to_dict()
    R["rural_share_overall"] = float(100 * (df["area_type"] == "Rural").mean())

    # numeric by severity
    nb = df.groupby("severity", observed=True)[["number_of_vehicles", "number_of_casualties"]].agg(["mean", "median", "max"]).round(3)
    nb.columns = ["_".join(c) for c in nb.columns]
    nb.to_csv(TAB_DIR / "03_numeric_by_severity.csv")
    R["cas_by_sev"] = nb["number_of_casualties_mean"].to_dict(); R["veh_by_sev"] = nb["number_of_vehicles_mean"].to_dict()

    # ================================================================ FIGURES
    ax_label = dict(fontsize=10)

    # ---- Figure 1: severity distribution
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    vals = [R["sev_n"][s] for s in SEVERITY_ORDER]
    bars = ax.barh(SEVERITY_ORDER, vals, color=[SEV_COLORS[s] for s in SEVERITY_ORDER], height=0.55)
    ax.invert_yaxis()
    for b, s in zip(bars, SEVERITY_ORDER):
        ax.text(b.get_width() + N * 0.008, b.get_y() + b.get_height() / 2, f"{R['sev_n'][s]:,}  ({R['sev_pct'][s]:.1f}%)", va="center", fontsize=9.5, color="#222")
    ax.set_xlim(0, max(vals) * 1.28)
    ax.set_xlabel("Number of reported collisions"); ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Figure 1. Collision severity, Great Britain 2025 (n = {N:,})")
    fig.text(0.0, -0.1, f"Fatal + Serious (KSI) = {R['ksi_n']:,} collisions ({R['ksi_pct']:.1f}%).", fontsize=8.5, color=NEUTRAL)
    save_fig(fig, "fig01_severity_distribution.png")

    # ---- Figure 2: lighting and weather distributions
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.1), gridspec_kw={"width_ratios": [1, 1.1]})
    ax = axes[0]
    ls = freq[(freq.variable == "light") & (freq.category != "Missing (-1)")].set_index("category").reindex(LIGHT_ORDER)
    ax.barh([wrap(c, 20) for c in ls.index], ls["pct_of_valid"], color=ACCENT, height=0.6); ax.invert_yaxis()
    for i, (p, n) in enumerate(zip(ls["pct_of_valid"], ls["n"])):
        ax.text(p + 1, i, f"{p:.1f}%  (n={int(n):,})", va="center", fontsize=8.8)
    ax.set_xlim(0, 100); ax.set_xlabel("% of collisions with a recorded lighting condition"); ax.grid(axis="y", visible=False)
    ax.set_title("(a) Light conditions")
    ax = axes[1]
    ws = freq[(freq.variable == "weather") & (freq.category != "Missing (-1)")].sort_values("n", ascending=False)
    cols = [GREY if c in ("Unknown", "Other") else ACCENT for c in ws["category"]]
    ax.barh([wrap(c, 24) for c in ws["category"]], ws["pct_of_valid"], color=cols, height=0.6); ax.invert_yaxis()
    for i, (p, n) in enumerate(zip(ws["pct_of_valid"], ws["n"])):
        ax.text(p + 1, i, f"{p:.1f}%  (n={int(n):,})", va="center", fontsize=8.8)
    ax.set_xlim(0, 105); ax.set_xlabel("% of collisions"); ax.grid(axis="y", visible=False)
    ax.set_title("(b) Weather conditions")
    fig.suptitle("Figure 2. Lighting and weather at the time of reported collisions", x=0.01, ha="left", fontweight="bold", fontsize=12, y=1.02)
    fig.text(0.01, -0.03, "Grey bars = 'Other'/'Unknown' codes. 16 collisions with missing lighting are excluded from panel (a).", fontsize=8.5, color=NEUTRAL)
    fig.tight_layout()
    save_fig(fig, "fig02_lighting_weather_distribution.png")

    # ---- Figure 3: monthly pattern
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.9))
    ax = axes[0]
    ax.bar(monthly["month_name"], monthly["collisions"], color=ACCENT, width=0.65)
    for x, v in zip(monthly["month_name"], monthly["collisions"]):
        ax.text(x, v + 80, f"{v / 1000:.1f}k", ha="center", fontsize=8.2)
    ax.set_ylim(0, monthly["collisions"].max() * 1.12); ax.grid(axis="x", visible=False)
    ax.set_ylabel("Reported collisions"); ax.set_title("(a) Collisions per month")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax = axes[1]
    ax.plot(monthly["month_name"], monthly["dark_pct"], color=NEUTRAL, marker="o", lw=2, ms=6)
    for x, v in zip(monthly["month_name"], monthly["dark_pct"]):
        ax.text(x, v + 1.6, f"{v:.0f}%", ha="center", fontsize=8.2)
    ax.set_ylim(0, monthly["dark_pct"].max() * 1.2); ax.grid(axis="x", visible=False)
    ax.set_ylabel("% of collisions in darkness"); ax.set_title("(b) Share of collisions occurring in darkness")
    fig.suptitle("Figure 3. Monthly pattern of reported collisions, 2025", x=0.01, ha="left", fontweight="bold", fontsize=12, y=1.03)
    fig.tight_layout()
    save_fig(fig, "fig03_monthly_pattern.png")

    # ---- Figure 4: hourly pattern
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.0))
    ax = axes[0]
    ax.plot(hourly.index, hourly["weekday_per_day"], color=ACCENT, lw=2.2, marker="o", ms=4, label=f"Weekdays (Mon-Fri, {n_weekday_days} days)")
    ax.plot(hourly.index, hourly["weekend_per_day"], color="#D55E00", lw=2.2, marker="s", ms=4, label=f"Weekend (Sat-Sun, {n_weekend_days} days)")
    ax.set_xticks(range(0, 24, 3)); ax.set_xlabel("Hour of day (00 = 00:00-00:59)"); ax.set_ylabel("Mean collisions per day")
    ax.legend(loc="upper left"); ax.set_title("(a) Collisions per day, by hour"); ax.set_ylim(bottom=0)
    ax = axes[1]
    ax.plot(hourly.index, hourly["ksi_pct"], color="#B36B00", lw=2.2, marker="o", ms=4)
    ax.axhline(R["ksi_overall"], color=NEUTRAL, ls="--", lw=1)
    ax.text(23.4, R["ksi_overall"] - 0.7, f"overall {R['ksi_overall']:.1f}%", ha="right", va="top", fontsize=8.5, color=NEUTRAL)
    ax.set_xticks(range(0, 24, 3)); ax.set_xlabel("Hour of day"); ax.set_ylabel("% of collisions Fatal or Serious")
    ax.set_title("(b) Share Fatal/Serious, by hour"); ax.set_ylim(bottom=0)
    fig.suptitle("Figure 4. Hourly pattern of reported collisions and severity, 2025", x=0.01, ha="left", fontweight="bold", fontsize=12, y=1.03)
    fig.tight_layout()
    save_fig(fig, "fig04_hourly_pattern.png")

    # ---- Figure 5: severity by lighting (100 % stacked)
    fig, ax = plt.subplots(figsize=(10.5, 3.9))
    ypos = np.arange(len(LIGHT_ORDER))
    left = np.zeros(len(LIGHT_ORDER))
    for s in ["Slight", "Serious", "Fatal"]:
        w = ct_pct[s].values
        ax.barh(ypos, w, left=left, color=SEV_COLORS[s], height=0.62, label=s, edgecolor="white", linewidth=1.2)
        if s != "Fatal":
            for y, l, ww in zip(ypos, left, w):
                ax.text(l + ww / 2, y, f"{ww:.1f}%", ha="center", va="center", fontsize=9, color="#111")
        left += w
    for y, lab in zip(ypos, LIGHT_ORDER):
        r = sl.set_index("category").loc[lab]
        ax.text(101.5, y, f"Fatal {r['fatal_pct']:.1f}%  |  KSI {r['ksi_pct']:.1f}%  |  n={int(r['n']):,}", va="center", fontsize=8.8)
    ax.set_yticks(ypos); ax.set_yticklabels([wrap(c, 20) for c in LIGHT_ORDER]); ax.invert_yaxis()
    ax.set_xlim(0, 100); ax.set_xlabel("% of collisions in each lighting category"); ax.grid(axis="y", visible=False)
    ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(0, 1.13), title=None)
    ax.set_title("Figure 5. Collision severity by lighting condition", pad=26)
    fig.text(0.0, -0.09, "Fatal segment (right-hand edge of each bar) is too thin to label; its share is given at right. KSI = Fatal + Serious. 16 missing-lighting collisions excluded.", fontsize=8.3, color=NEUTRAL)
    save_fig(fig, "fig05_severity_by_lighting.png")

    # ---- Figure 6: KSI share by road / weather / speed / area
    panels = [("speed_limit_mph", "(a) Speed limit (mph)", None), ("road_type_label", "(b) Road type", None),
              ("weather", "(c) Weather", None), ("area_type", "(d) Urban / rural", None)]
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.2))
    for ax, (v, title, _) in zip(axes.ravel(), panels):
        t = cond[cond.variable == v].copy()
        if v == "speed_limit_mph":
            t = t.assign(k=t["category"].astype(int)).sort_values("k")
        else:
            t = t.sort_values("ksi_pct", ascending=True if v != "speed_limit_mph" else True)
        if v == "area_type":
            t = t[t["category"].isin(["Urban", "Rural"])]
        y = np.arange(len(t))
        colors = [GREY if c in ("Unknown", "Other") else ACCENT for c in t["category"]]
        ax.barh(y, t["ksi_pct"], color=colors, height=0.62)
        for yy, p_ in zip(y, t["ksi_pct"]):
            ax.text(p_ + 0.6, yy, f"{p_:.1f}%", va="center", fontsize=8.5)
        ax.axvline(R["ksi_overall"], color=NEUTRAL, ls="--", lw=1)
        ax.set_yticks(y); ax.set_yticklabels([f"{wrap(c, 26)}\n(n={n:,})" for c, n in zip(t["category"], t["n"])], fontsize=8.6)
        ax.set_xlim(0, 45); ax.set_ylim(-0.6, len(t) - 0.4)
        if v == "speed_limit_mph":
            ax.invert_yaxis()
        ax.set_xlabel("% of collisions Fatal or Serious"); ax.set_title(title); ax.grid(axis="y", visible=False)
    fig.suptitle(f"Figure 6. Share of collisions that were Fatal or Serious, by road and weather characteristics\n(bars = %; dashed line = overall {R['ksi_overall']:.1f}%; grey = 'Other'/'Unknown')",
                 x=0.01, ha="left", fontweight="bold", fontsize=11.5, y=1.02)
    fig.tight_layout()
    save_fig(fig, "fig06_ksi_by_road_weather.png")

    # ================================================================ interpretations (numbers pulled from results)
    ls = freq[freq.variable == "light"].set_index("category")["pct_of_valid"]
    ws = freq[freq.variable == "weather"].set_index("category")["pct_of_valid"]
    dark_total = 100 - ls["Daylight"]
    lk = R["light_ksi"]
    att = R["attend_ksi"]
    att_self = [v for k, v in att.items() if k.startswith("No -")][0]
    unk_w = df[df["weather"] == "Unknown"]["did_police_officer_attend_scene_of_accident"].value_counts(normalize=True)
    R["unknown_weather_not_attended_pct"] = float(100 * (1 - unk_w.get(1, 0)))
    mpd = monthly.set_index("month_name")["collisions_per_day"]
    R["collisions_per_day_range"] = [float(mpd.min()), mpd.idxmin(), float(mpd.max()), mpd.idxmax()]
    wk_8 = float(hourly.loc[8, "weekday_per_day"])
    night_ksi = float(hourly.loc[0:4, "ksi_pct"].min())
    night_wkend_gt = bool((hourly.loc[0:4, "weekend_per_day"] > hourly.loc[0:4, "weekday_per_day"]).all())
    sp = R["speed_ksi"]
    wk_ksi = [R["weekday_ksi"][d] for d in WEEKDAY_ORDER[:5]]
    interp = {
        "fig01_severity_distribution.png": (
            f"Most reported collisions are Slight ({R['sev_pct']['Slight']:.1f}%, n={R['sev_n']['Slight']:,}); "
            f"{R['sev_pct']['Serious']:.1f}% are Serious (n={R['sev_n']['Serious']:,}) and {R['sev_pct']['Fatal']:.1f}% Fatal (n={R['sev_n']['Fatal']:,}). "
            f"Combined, {R['ksi_pct']:.1f}% of collisions were Fatal or Serious (KSI). The distribution is strongly imbalanced, so Fatal collisions are rare events and any "
            f"category-level comparison of fatal outcomes rests on small counts."),
        "fig02_lighting_weather_distribution.png": (
            f"{ls['Daylight']:.1f}% of collisions with a recorded lighting condition occurred in daylight and {dark_total:.1f}% in darkness; within darkness, "
            f"lit streets dominate ({ls['Darkness - lights lit']:.1f}% of all collisions), followed by unlit roads with no lighting ({ls['Darkness - no lighting']:.1f}%), "
            f"unknown lighting ({ls['Darkness - lighting unknown']:.1f}%) and lights unlit ({ls['Darkness - lights unlit']:.1f}%). "
            f"Weather was 'fine, no high winds' in {ws['Fine no high winds']:.1f}% of collisions and 'raining, no high winds' in {ws['Raining no high winds']:.1f}%; "
            f"fog/mist and every snow category are each below 0.5%. 'Other' and 'Unknown' account for {ws['Other'] + ws['Unknown']:.1f}%. "
            f"These are shares of reported collisions, not of journeys, so they do not show that fine weather or daylight are more dangerous."),
        "fig03_monthly_pattern.png": (
            f"Monthly collision counts are fairly stable: from {R['month_min'][1]:,} ({R['month_min'][0]}) to {R['month_max'][1]:,} ({R['month_max'][0]}). February is the shortest month; "
            f"per day, the range is {R['collisions_per_day_range'][0]:.0f} ({R['collisions_per_day_range'][1]}) to {R['collisions_per_day_range'][2]:.0f} ({R['collisions_per_day_range'][3]}). "
            f"In contrast the share of collisions in darkness varies strongly with season, from {R['month_dark_min'][1]:.1f}% in {R['month_dark_min'][0]} to {R['month_dark_max'][1]:.1f}% in {R['month_dark_max'][0]}, "
            f"following day length. Lighting condition is therefore tied to the calendar (and, as Figure 4 shows, to the hour), which matters when interpreting any lighting-severity association."),
        "fig04_hourly_pattern.png": (
            f"On weekdays collisions peak at 08:00 ({wk_8:.1f} per day) and, higher, at {R['hour_peak_weekday']:02d}:00 ({R['hour_peak_weekday_val']:.1f} per day), consistent with commuting hours; "
            f"on weekends there is one broad afternoon peak around {R['hour_peak_weekend']:02d}:00 ({R['hour_peak_weekend_val']:.1f} per day)"
            + (" and more collisions per day than on weekdays in every hour from 00:00 to 04:59" if night_wkend_gt else "") + ". "
            f"The share of collisions that are Fatal/Serious is highest overnight (up to {R['hour_ksi_max_val']:.1f}% at {R['hour_ksi_max']:02d}:00; at least {night_ksi:.1f}% in every hour from 00:00 to 04:59) and lowest at "
            f"{R['hour_ksi_min']:02d}:00 ({R['hour_ksi_min_val']:.1f}%), against {R['ksi_overall']:.1f}% overall. Weekend days also show a higher KSI share (Saturday {R['weekday_ksi']['Saturday']:.1f}%, "
            f"Sunday {R['weekday_ksi']['Sunday']:.1f}%) than Monday-Friday ({min(wk_ksi):.1f}-{max(wk_ksi):.1f}%). "
            f"The busiest hours are not the most severe hours."),
        "fig05_severity_by_lighting.png": (
            f"Compared with daylight (KSI {lk['Daylight']['ksi_pct']:.1f}%, Fatal {lk['Daylight']['fatal_pct']:.1f}%), the Fatal/Serious share is higher in lit darkness "
            f"({lk['Darkness - lights lit']['ksi_pct']:.1f}%, Fatal {lk['Darkness - lights lit']['fatal_pct']:.1f}%), with unlit lights ({lk['Darkness - lights unlit']['ksi_pct']:.1f}%, Fatal {lk['Darkness - lights unlit']['fatal_pct']:.1f}%, n={lk['Darkness - lights unlit']['n']:,}) "
            f"and especially with no lighting (KSI {lk['Darkness - no lighting']['ksi_pct']:.1f}%, Fatal {lk['Darkness - no lighting']['fatal_pct']:.1f}%, "
            f"{lk['Darkness - no lighting']['fatal_pct'] / lk['Daylight']['fatal_pct']:.1f} times the daylight fatal share). Darkness with unknown lighting is the exception "
            f"(KSI {lk['Darkness - lighting unknown']['ksi_pct']:.1f}%, Fatal {lk['Darkness - lighting unknown']['fatal_pct']:.1f}%), a category likely linked to collisions recorded without police attendance (see Figure 6 note). "
            f"The pattern is descriptive: rural roads are over-represented in unlit darkness (rural share {R['area_share_by_light']['Darkness - no lighting']:.0f}% of 'no lighting' collisions vs {R['area_share_by_light']['Daylight']:.0f}% in daylight), "
            f"so lighting is entangled with road environment."),
        "fig06_ksi_by_road_weather.png": (
            f"(a) The KSI share rises with speed limit from {sp['20']:.1f}% (20 mph) through {sp['30']:.1f}% (30), {sp['40']:.1f}% (40) and {sp['50']:.1f}% (50) to {sp['60']:.1f}% (60 mph); "
            f"it is lower at 70 mph ({sp['70']:.1f}%), so the relationship is not monotonic. "
            f"(b) Single carriageways ({R['roadtype_ksi']['Single carriageway']['ksi_pct']:.1f}%) exceed dual carriageways ({R['roadtype_ksi']['Dual carriageway']['ksi_pct']:.1f}%), one-way streets ({R['roadtype_ksi']['One way street']['ksi_pct']:.1f}%), "
            f"slip roads ({R['roadtype_ksi']['Slip road']['ksi_pct']:.1f}%) and roundabouts ({R['roadtype_ksi']['Roundabout']['ksi_pct']:.1f}%). "
            f"(c) Weather shows little difference between the two common categories (fine {R['weather_ksi']['Fine no high winds']['ksi_pct']:.1f}%, rain {R['weather_ksi']['Raining no high winds']['ksi_pct']:.1f}%); fog/mist and fine-with-high-wind categories are higher "
            f"(about 32%) but are based on few collisions. The very low 'Unknown' weather share ({R['weather_ksi']['Unknown']['ksi_pct']:.1f}%) is likely a reporting effect: "
            f"{R['unknown_weather_not_attended_pct']:.0f}% of 'Unknown weather' collisions had no police officer attending, and KSI share is "
            f"{att['Yes']['ksi_pct']:.1f}% where an officer attended vs {att['No']['ksi_pct']:.1f}% (no attendance) and {att_self['ksi_pct']:.1f}% (self-completion form). "
            f"(d) Rural collisions are more often Fatal/Serious ({R['area_ksi']['Rural']['ksi_pct']:.1f}%) than urban ones ({R['area_ksi']['Urban']['ksi_pct']:.1f}%)."),
    }
    (OUT_DIR / "figure_interpretations.md").write_text(
        "# Interpretation of EDA figures (generated from the output tables)\n\n"
        + "\n\n".join(f"**{k}**  \n{v}" for k, v in interp.items()) + "\n", encoding="utf-8")
    R["interpretations"] = interp

    save_json(R, STAT_DIR / "03_eda_results.json")
    print("EDA complete: tables 03_*.csv and figures 1-6 written.")


if __name__ == "__main__":
    main()
