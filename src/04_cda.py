"""Step 4 - Confirmatory data analysis: chi-square test of independence, lighting x severity.

H0: lighting conditions and collision severity are independent.
H1: lighting conditions and collision severity are associated.   alpha = 0.05

Outputs: outputs/tables/04_*.csv, outputs/statistical_results/04_cda_results.json,
outputs/statistical_results/04_cda_report.md and outputs/figures/fig07_cda_lighting_severity.png
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats

from common import (ACCENT, LIGHT_ORDER, NEUTRAL, SEVERITY_ORDER, STAT_DIR, TAB_DIR, cohen_v_label,
                    cramers_v, fmt_p, load_processed, save_fig, save_json, set_plot_style, wilson_ci)

ALPHA = 0.05
SEED = 20250101
N_BOOT = 5000


def chi2_test(obs: pd.DataFrame) -> dict:
    """Pearson chi-square test of independence (no continuity correction: table is larger than 2x2)."""
    chi2, p, dof, exp = stats.chi2_contingency(obs.values, correction=False)
    n = obs.values.sum()
    exp = pd.DataFrame(exp, index=obs.index, columns=obs.columns)
    v = cramers_v(obs.values.astype(float), chi2)
    row, col = obs.sum(axis=1).values[:, None], obs.sum(axis=0).values[None, :]
    adj = (obs.values - exp.values) / np.sqrt(exp.values * (1 - row / n) * (1 - col / n))
    contrib = (obs.values - exp.values) ** 2 / exp.values
    return {"chi2": float(chi2), "p": float(p), "log10_p": float(stats.chi2.logsf(chi2, dof) / np.log(10)), "dof": int(dof), "n": int(n),
            "expected": exp, "adj_resid": pd.DataFrame(adj, index=obs.index, columns=obs.columns),
            "contrib": pd.DataFrame(contrib, index=obs.index, columns=obs.columns),
            "min_expected": float(exp.values.min()), "pct_cells_lt5": float(100 * (exp.values < 5).mean()),
            "cells_lt1": int((exp.values < 1).sum()), **v}


def bootstrap_v(obs: pd.DataFrame, rng) -> tuple[float, float]:
    """Percentile CI for Cramér's V: parametric resampling of the table from its observed cell proportions."""
    n = int(obs.values.sum())
    p = (obs.values / n).ravel()
    draws = rng.multinomial(n, p, size=N_BOOT).reshape(N_BOOT, *obs.shape).astype(float)
    row = draws.sum(axis=2, keepdims=True); col = draws.sum(axis=1, keepdims=True)
    exp = row * col / n
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((draws - exp) ** 2 / exp, axis=(1, 2))
    k = min(obs.shape) - 1
    v = np.sqrt(chi2 / (n * k))
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def permutation_p(obs: pd.DataFrame, chi2_obs: float, rng, reps: int = 10000) -> float:
    """Monte Carlo permutation p-value (severity labels shuffled within the fixed margins); used when expected counts are too small."""
    r, c = obs.shape
    light = np.repeat(np.arange(r), obs.sum(axis=1).values.astype(int))
    sev = np.concatenate([np.repeat(np.arange(c), obs.values[i].astype(int)) for i in range(r)])
    exp = np.outer(obs.sum(axis=1), obs.sum(axis=0)) / obs.values.sum()
    hits = 0
    for _ in range(reps):
        t = np.bincount(light * c + rng.permutation(sev), minlength=r * c).reshape(r, c)
        hits += ((t - exp) ** 2 / exp).sum() >= chi2_obs - 1e-9
    return float((hits + 1) / (reps + 1))


def risk_ratio_ci(k1, n1, k0, n0, z=1.959964):
    """Risk ratio (group 1 vs reference group 0) with Katz log-method 95% CI."""
    rr = (k1 / n1) / (k0 / n0)
    se = np.sqrt(1 / k1 - 1 / n1 + 1 / k0 - 1 / n0)
    return float(rr), float(np.exp(np.log(rr) - z * se)), float(np.exp(np.log(rr) + z * se))


def main() -> None:
    set_plot_style()
    rng = np.random.default_rng(SEED)
    df = load_processed()
    n_all = len(df)
    cc = df.dropna(subset=["light", "severity"]).copy()
    n_excl = n_all - len(cc)
    obs = pd.crosstab(cc["light"], cc["severity"]).reindex(index=LIGHT_ORDER, columns=SEVERITY_ORDER)
    obs.index.name, obs.columns.name = "Lighting condition", "Collision severity"

    res = chi2_test(obs)
    v_lo, v_hi = bootstrap_v(obs, rng)
    v_label = cohen_v_label(res["v"], res["df_star"])
    reject = res["p"] < ALPHA
    cut = [0.10 / np.sqrt(res["df_star"]), 0.30 / np.sqrt(res["df_star"]), 0.50 / np.sqrt(res["df_star"])]

    obs.assign(Total=obs.sum(axis=1)).to_csv(TAB_DIR / "04_observed_frequencies.csv")
    res["expected"].round(2).to_csv(TAB_DIR / "04_expected_frequencies.csv")
    res["adj_resid"].round(2).to_csv(TAB_DIR / "04_adjusted_residuals.csv")
    (100 * res["contrib"] / res["chi2"]).round(2).to_csv(TAB_DIR / "04_chi2_contribution_pct.csv")

    # ------------------------------------------------ proportions with Wilson CIs
    rows = []
    ref = obs.loc["Daylight"]
    for lab in LIGHT_ORDER + ["All (valid lighting)"]:
        r = obs.sum(axis=0) if lab.startswith("All") else obs.loc[lab]
        n = int(r.sum())
        d = {"lighting": lab, "n": n}
        for name, k in [("Fatal", r["Fatal"]), ("Serious", r["Serious"]), ("Slight", r["Slight"]), ("KSI (Fatal+Serious)", r["Fatal"] + r["Serious"])]:
            lo, hi = wilson_ci(int(k), n)
            d.update({f"{name}_n": int(k), f"{name}_pct": 100 * k / n, f"{name}_ci_low": 100 * lo, f"{name}_ci_high": 100 * hi})
        if lab not in ("Daylight",) and not lab.startswith("All"):
            for name, k, k0 in [("KSI", r["Fatal"] + r["Serious"], ref["Fatal"] + ref["Serious"]), ("Fatal", r["Fatal"], ref["Fatal"])]:
                rr, lo, hi = risk_ratio_ci(int(k), n, int(k0), int(ref.sum()))
                d.update({f"{name}_RR_vs_daylight": rr, f"{name}_RR_ci_low": lo, f"{name}_RR_ci_high": hi})
        rows.append(d)
    prop = pd.DataFrame(rows)
    prop.to_csv(TAB_DIR / "04_severity_proportions_wilson_ci.csv", index=False)
    P = prop.set_index("lighting")

    # ------------------------------------------------ robustness: stratified tests
    cc2 = cc.copy()
    cc2["police_attendance"] = np.where(cc2["did_police_officer_attend_scene_of_accident"] == 1, "Police attended", "No police attendance (incl. self-completion forms)")
    strata_rows = []
    strata_defs = [("area_type", ["Urban", "Rural"]),
                   ("police_attendance", ["Police attended", "No police attendance (incl. self-completion forms)"])]
    for var, levels in strata_defs:
        for lev in levels:
            sub = cc2[cc2[var] == lev]
            o = pd.crosstab(sub["light"], sub["severity"]).reindex(index=LIGHT_ORDER, columns=SEVERITY_ORDER, fill_value=0)
            r = chi2_test(o)
            vlo, vhi = bootstrap_v(o, rng)
            assumptions_ok = r["pct_cells_lt5"] <= 20 and r["cells_lt1"] == 0
            mc_p = np.nan if assumptions_ok else permutation_p(o, r["chi2"], rng)
            p_used = r["p"] if assumptions_ok else mc_p
            row = {"stratifier": var, "stratum": lev, "n": r["n"], "chi2": r["chi2"], "dof": r["dof"], "p_asymptotic": r["p"],
                   "p_monte_carlo_10000": mc_p, "p_used": p_used, "p_used_text": fmt_p(p_used) if assumptions_ok else ("< 0.0001 (Monte Carlo)" if mc_p <= 1.5 / 10001 else f"{mc_p:.4f} (Monte Carlo)"),
                   "cramers_v": r["v"], "v_ci_low": vlo, "v_ci_high": vhi,
                   "effect_size": cohen_v_label(r["v"], r["df_star"]), "min_expected": r["min_expected"], "pct_cells_expected_lt5": r["pct_cells_lt5"],
                   "chi2_assumptions_met": assumptions_ok}
            for lab in LIGHT_ORDER:
                row[f"KSI%_{lab}"] = 100 * (o.loc[lab, "Fatal"] + o.loc[lab, "Serious"]) / o.loc[lab].sum()
            strata_rows.append(row)
    strata = pd.DataFrame(strata_rows)
    strata.to_csv(TAB_DIR / "04_robustness_stratified_tests.csv", index=False)

    # ------------------------------------------------ result record
    top_cells = (res["adj_resid"].stack().rename("adj_resid").reset_index()
                 .assign(abs_resid=lambda x: x["adj_resid"].abs()).sort_values("abs_resid", ascending=False).head(4))
    nl = P.loc["Darkness - no lighting"]
    day = P.loc["Daylight"]
    out = {
        "research_question": "Is there a statistically significant association between lighting conditions and collision severity?",
        "H0": "Lighting conditions and collision severity are independent.", "H1": "Lighting conditions and collision severity are associated.",
        "alpha": ALPHA, "test": "Pearson chi-square test of independence (5 x 3 table, no continuity correction)",
        "n_total": n_all, "n_excluded_missing_lighting": n_excl, "n_analysed": res["n"],
        "chi2": res["chi2"], "dof": res["dof"], "p_value": res["p"], "p_value_formatted": fmt_p(res["p"]), "log10_p": res["log10_p"],
        "decision": "Reject H0" if reject else "Fail to reject H0",
        "cramers_v": res["v"], "cramers_v_ci95": [v_lo, v_hi], "cramers_v_bias_corrected": res["v_bias_corrected"], "df_star": res["df_star"],
        "cohen_thresholds_small_medium_large": cut, "effect_size_label": v_label,
        "min_expected": res["min_expected"], "pct_cells_expected_lt5": res["pct_cells_lt5"], "cells_expected_lt1": res["cells_lt1"],
        "top_adjusted_residual_cells": top_cells.drop(columns="abs_resid").round(2).to_dict("records"),
        "ksi_overall_pct": P.loc["All (valid lighting)", "KSI (Fatal+Serious)_pct"],
        "bootstrap_reps": N_BOOT, "seed": SEED,
        "proportions": prop.round(3).to_dict("records"), "robustness": strata.round(5).to_dict("records"),
    }

    # ------------------------------------------------ figure 7
    div = LinearSegmentedColormap.from_list("bw", ["#0072B2", "#F2F2F2", "#D55E00"])
    fig = plt.figure(figsize=(14, 4.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 1], wspace=0.5)
    ax = fig.add_subplot(gs[0])
    lim = max(10, float(np.ceil(res["adj_resid"].abs().values.max() / 5) * 5))
    im = ax.imshow(res["adj_resid"].values, cmap=div, vmin=-lim, vmax=lim, aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(SEVERITY_ORDER)
    ax.set_yticks(range(5)); ax.set_yticklabels([c.replace("Darkness - ", "Dark: ") for c in LIGHT_ORDER])
    for i in range(5):
        for j in range(3):
            ax.text(j, i, f"{res['adj_resid'].values[i, j]:+.1f}\n(n={obs.values[i, j]:,})", ha="center", va="center", fontsize=8.5,
                    color="white" if abs(res["adj_resid"].values[i, j]) > 0.65 * lim else "#111")
    ax.grid(False); ax.set_title("(a) Adjusted residuals\n(observed vs expected under H0)", fontsize=10.5)
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", location="bottom", fraction=0.06, pad=0.14); cb.set_label("adjusted residual (SD units)", fontsize=8.5)
    for k, (key, title, xlab) in enumerate([("KSI (Fatal+Serious)", "(b) Fatal or Serious share", "% Fatal or Serious"), ("Fatal", "(c) Fatal share", "% Fatal")]):
        ax = fig.add_subplot(gs[k + 1])
        y = np.arange(5)[::-1]
        vals = P.loc[LIGHT_ORDER]
        ax.hlines(y, vals[f"{key}_ci_low"], vals[f"{key}_ci_high"], color=ACCENT, lw=2.2)
        ax.scatter(vals[f"{key}_pct"], y, color=ACCENT, s=50, zorder=3, edgecolor="white", linewidth=0.8)
        ax.axvline(P.loc["All (valid lighting)", f"{key}_pct"], color=NEUTRAL, ls="--", lw=1)
        ax.set_yticks(y); ax.set_yticklabels([c.replace("Darkness - ", "Dark: ") for c in LIGHT_ORDER] if k == 0 else [])
        ax.set_xlim(0, float(vals[f"{key}_ci_high"].max()) * 1.22); ax.set_ylim(-0.5, 4.5)
        ax.set_xlabel(xlab); ax.set_title(title, fontsize=10.5); ax.grid(axis="y", visible=False)
        for yy, (_, r) in zip(y, vals.iterrows()):
            ax.text(r[f"{key}_ci_high"] + 0.02 * ax.get_xlim()[1], yy, f"{r[f'{key}_pct']:.1f}%", fontsize=8.5, va="center")
    fig.suptitle(f"Figure 7. Lighting x severity: chi-square({res['dof']}) = {res['chi2']:,.1f}, p {('< 1e-300' if res['p'] < 1e-300 else '= ' + fmt_p(res['p']))}, Cramér's V = {res['v']:.3f} ({v_label}); n = {res['n']:,}",
                 x=0.01, ha="left", fontweight="bold", fontsize=11.5, y=1.03)
    fig.text(0.01, -0.04, "Panels (b)-(c): points = observed %, bars = 95% Wilson CI, dashed line = overall % (all valid-lighting collisions). Positive (orange) residuals = more collisions than expected under independence.",
             fontsize=8.3, color=NEUTRAL)
    save_fig(fig, "fig07_cda_lighting_severity.png")

    # ------------------------------------------------ interpretation text
    rob_consistent = bool((strata["p_used"] < ALPHA).all())
    no_light_top = bool(all(strata.loc[i, [f"KSI%_{l}" for l in LIGHT_ORDER]].astype(float).idxmax() == "KSI%_Darkness - no lighting" for i in strata.index))
    nl_contrib = float(100 * res["contrib"].loc["Darkness - no lighting"].sum() / res["chi2"])
    nl_share = float(100 * obs.loc["Darkness - no lighting"].sum() / res["n"])
    rob_txt = "; ".join(f"{r.stratum}: chi2({int(r.dof)}) = {r.chi2:,.1f}, p {r.p_used_text}, V = {r.cramers_v:.3f}" for r in strata.itertuples())
    interp = {
        "decision": (f"Because p = {fmt_p(res['p'])} is {'below' if reject else 'not below'} alpha = {ALPHA}, H0 is {'rejected' if reject else 'not rejected'}: "
                     + ("the data show a statistically significant association between lighting condition and collision severity." if reject else "there is no statistically significant association.")),
        "practical": (f"With n = {res['n']:,} even small departures from independence are detectable, so significance alone is uninformative. Cramér's V = {res['v']:.3f} "
                      f"(95% bootstrap CI {v_lo:.3f}-{v_hi:.3f}; bias-corrected {res['v_bias_corrected']:.3f}) is {v_label} by Cohen's benchmarks for df* = {res['df_star']} "
                      f"(small {cut[0]:.2f}, medium {cut[1]:.2f}, large {cut[2]:.2f}); V^2 = {res['v'] ** 2:.4f}, i.e. a very weak overall association. The overall effect is small because most collisions occur in daylight or lit darkness, "
                      f"where severity is close to the overall mix; the 'no lighting' row (only {nl_share:.1f}% of collisions) supplies {nl_contrib:.1f}% of the chi-square statistic."),
        "pattern": (f"The association is concentrated in darkness with no street lighting: Fatal or Serious share {nl['KSI (Fatal+Serious)_pct']:.1f}% "
                    f"(95% CI {nl['KSI (Fatal+Serious)_ci_low']:.1f}-{nl['KSI (Fatal+Serious)_ci_high']:.1f}) vs {day['KSI (Fatal+Serious)_pct']:.1f}% in daylight "
                    f"(risk ratio {nl['KSI_RR_vs_daylight']:.2f}, 95% CI {nl['KSI_RR_ci_low']:.2f}-{nl['KSI_RR_ci_high']:.2f}); Fatal share {nl['Fatal_pct']:.1f}% vs {day['Fatal_pct']:.1f}% "
                    f"(RR {nl['Fatal_RR_vs_daylight']:.2f}, 95% CI {nl['Fatal_RR_ci_low']:.2f}-{nl['Fatal_RR_ci_high']:.2f}). Cells with the largest adjusted residuals: "
                    + "; ".join(f"{c['Lighting condition']} x {c['Collision severity']} ({c['adj_resid']:+.1f})" for c in out['top_adjusted_residual_cells']) + "."),
        "robustness": (f"Stratified re-analysis ({rob_txt}). "
                       + ("The association remains significant in every stratum" if rob_consistent else "The association is not significant in every stratum")
                       + ("; in every stratum 'no lighting' has the highest Fatal/Serious share. " if no_light_top else ". ")
                       + "The association is therefore not simply an artefact of mixing urban/rural roads or police-attended and unattended reports, although the strata do not rule out other confounders (e.g. speed limit, road type, time of day)."),
    }
    out["interpretation"] = interp
    save_json(out, STAT_DIR / "04_cda_results.json")

    # ------------------------------------------------ markdown report
    lines = [
        "# Confirmatory data analysis - lighting conditions vs collision severity", "",
        f"**Research question.** {out['research_question']}", "",
        f"- H0: {out['H0']}", f"- H1: {out['H1']}", f"- Significance level: alpha = {ALPHA}", f"- Test: {out['test']}", "",
        "## Data", "",
        f"{n_all:,} collisions in the processed file; {n_excl} with missing lighting (`-1`) were excluded (complete-case analysis), leaving **n = {res['n']:,}**. "
        "'Darkness - lighting unknown' is a valid guide code and was retained as its own category.", "",
        "## Test selection and assumptions", "",
        "Both variables are categorical (lighting nominal with 5 categories; severity ordinal with 3 categories), so Pearson's chi-square test of independence is appropriate. Checks:", "",
        "1. **Categories mutually exclusive and exhaustive** - each collision has exactly one lighting code and one severity code (verified: no duplicate collision IDs; see preprocessing summary).",
        f"2. **Sufficient expected counts** - minimum expected count = {res['min_expected']:.2f}; cells with expected < 5: {res['pct_cells_lt5']:.1f}%; cells with expected < 1: {res['cells_lt1']}. "
        + ("The usual rule (>= 80% of cells >= 5, none < 1) is met, so the asymptotic chi-square distribution is valid and no category merging or exact test is needed." if res['pct_cells_lt5'] <= 20 and res['cells_lt1'] == 0 else "The usual rule is NOT met."),
        "3. **Independence of observations** - each row is a separate reported collision, but collisions are not strictly independent draws (they cluster in space and time, e.g. a single event or weather system can generate several). This cannot be tested from the data and is a limitation: the nominal p-value is probably somewhat optimistic. With a p-value this far below alpha the decision is not sensitive to that.",
        "4. **Random sampling** - the data are a census of police-reported injury collisions, not a random sample; inference is therefore about association in the 2025 reported data, not generalisation to unreported collisions.", "",
        "An ordinal trend test (e.g. Cochran-Armitage) was not used because lighting has no natural single ordering across all five categories.", "",
        "## Observed frequencies", "", obs.assign(Total=obs.sum(axis=1)).to_markdown(), "",
        "## Expected frequencies under H0", "", res["expected"].round(1).to_markdown(), "",
        "## Adjusted standardised residuals (|value| > 1.96 indicates a cell departing from independence)", "", res["adj_resid"].round(2).to_markdown(), "",
        "## Test result", "",
        f"- chi-square statistic = **{res['chi2']:,.2f}**", f"- degrees of freedom = **{res['dof']}** ((5-1) x (3-1))",
        f"- p-value = **{fmt_p(res['p'])}** (log10 p = {res['log10_p']:.1f})", f"- decision at alpha = {ALPHA}: **{out['decision']}**", "",
        "## Effect size", "",
        f"- Cramér's V = **{res['v']:.4f}** (95% bootstrap CI {v_lo:.4f}-{v_hi:.4f}, {N_BOOT:,} resamples, seed {SEED}); bias-corrected V = {res['v_bias_corrected']:.4f}",
        f"- Benchmarks for df* = {res['df_star']}: small = {cut[0]:.3f}, medium = {cut[1]:.3f}, large = {cut[2]:.3f} -> **{v_label}**", "",
        "## Severity proportions with 95% Wilson confidence intervals", "",
        prop[["lighting", "n", "Fatal_pct", "Fatal_ci_low", "Fatal_ci_high", "KSI (Fatal+Serious)_pct", "KSI (Fatal+Serious)_ci_low", "KSI (Fatal+Serious)_ci_high",
              "KSI_RR_vs_daylight", "KSI_RR_ci_low", "KSI_RR_ci_high", "Fatal_RR_vs_daylight", "Fatal_RR_ci_low", "Fatal_RR_ci_high"]].round(2).to_markdown(index=False), "",
        "Risk ratios compare each category with Daylight (Katz log-method CI). Fatal outcomes are rare (1.4% overall), so Fatal intervals are wide in small categories (e.g. 'lights unlit', n = 720).", "",
        "## Robustness: the same test within strata", "",
        "One focused sensitivity analysis, reported in full (all four tests, none omitted). Urban/rural area and police attendance were chosen because the exploratory analysis (Figures 5-6) showed that rural roads are over-represented in unlit darkness and that "
        "police-attended collisions are more often Serious/Fatal and have a different lighting mix - i.e. they are plausible confounders/reporting effects; the choice was made after the EDA, not pre-registered. "
        "These four tests are consistency checks, not additional hypotheses. Where the chi-square expected-count rule fails (> 20% of cells < 5, or any < 1), a Monte Carlo permutation p-value (10,000 shuffles of severity within fixed margins) is used instead.", "",
        strata[["stratifier", "stratum", "n", "chi2", "dof", "p_used_text", "cramers_v", "v_ci_low", "v_ci_high", "effect_size", "min_expected", "pct_cells_expected_lt5", "chi2_assumptions_met"]].round(4).to_markdown(index=False), "",
        "KSI share by lighting within each stratum:", "",
        strata[["stratum"] + [f"KSI%_{l}" for l in LIGHT_ORDER]].round(1).to_markdown(index=False), "",
        "## Interpretation", "",
        f"- **Statistical significance.** {interp['decision']}", f"- **Practical significance.** {interp['practical']}", f"- **Pattern.** {interp['pattern']}", f"- **Robustness.** {interp['robustness']}", "",
        "## Limitations", "",
        "- Association, not causation: lighting is correlated with time of day, season, road type, speed limit and rurality, and we have not adjusted for these.",
        "- The data are reported collisions only; without exposure (traffic by lighting condition) the results cannot show that darkness *increases* risk, only how severity is distributed among collisions that were reported.",
        "- Severity is recorded under two systems (injury-based vs. officer-reported), and police attendance varies; lighting is an officer's judgement.",
        "- Observations are not strictly independent (see assumption 3).",
    ]
    (STAT_DIR / "04_cda_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"CDA: chi2({res['dof']}) = {res['chi2']:.2f}, p = {fmt_p(res['p'])}, V = {res['v']:.4f} [{v_lo:.4f}, {v_hi:.4f}] ({v_label}); decision: {out['decision']}")


if __name__ == "__main__":
    main()
