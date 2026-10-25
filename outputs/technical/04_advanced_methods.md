# Optional technical documentation - advanced methods for the lighting x severity analysis

Supporting material only; none of it is needed for the main report. All values are produced by `src/04_cda.py` and are the same calculations stored in `04_cda_results.json`.

## Chi-square assumption checks

Minimum expected count = 10.31; cells with expected < 5: 0.0%; cells with expected < 1: 0. The usual rule (>= 80% of cells >= 5, none < 1) is met.
An ordinal trend test (e.g. Cochran-Armitage) was not used because lighting has no natural single ordering across all five categories.

## Effect size detail

- Cramér's V = 0.0580; 95% percentile bootstrap CI 0.0520-0.0650 (5,000 multinomial resamples, seed 20250101); bias-corrected V = 0.0576; V^2 = 0.0034
- Cohen benchmarks for df* = 2: small = 0.071, medium = 0.212, large = 0.354 -> **negligible**

## Adjusted standardised residuals (|value| > 1.96 indicates a cell departing from independence)

| Lighting condition          |   Fatal |   Serious |   Slight |
|:----------------------------|--------:|----------:|---------:|
| Daylight                    |   -9.35 |     -8.17 |    10.54 |
| Darkness - lights lit       |   -1.93 |      2.7  |    -2.13 |
| Darkness - lights unlit     |    2.74 |      0.9  |    -1.62 |
| Darkness - no lighting      |   21.46 |     12.14 |   -17.71 |
| Darkness - lighting unknown |   -1.43 |     -2.23 |     2.57 |

The association is concentrated in darkness with no street lighting: Fatal or Serious share 36.3% (95% CI 35.0-37.5) vs 25.3% in daylight (risk ratio 1.43, 95% CI 1.38-1.49); Fatal share 4.7% vs 1.2% (RR 3.89, 95% CI 3.40-4.45). Cells with the largest adjusted residuals: Darkness - no lighting x Fatal (+21.5); Darkness - no lighting x Slight (-17.7); Darkness - no lighting x Serious (+12.1); Daylight x Slight (+10.5).

## Severity proportions with 95% Wilson confidence intervals and risk ratios

| lighting                    |      n |   Fatal_pct |   Fatal_ci_low |   Fatal_ci_high |   KSI (Fatal+Serious)_pct |   KSI (Fatal+Serious)_ci_low |   KSI (Fatal+Serious)_ci_high |   KSI_RR_vs_daylight |   KSI_RR_ci_low |   KSI_RR_ci_high |   Fatal_RR_vs_daylight |   Fatal_RR_ci_low |   Fatal_RR_ci_high |
|:----------------------------|-------:|------------:|---------------:|----------------:|--------------------------:|-----------------------------:|------------------------------:|---------------------:|----------------:|-----------------:|-----------------------:|------------------:|-------------------:|
| Daylight                    |  72814 |        1.21 |           1.14 |            1.29 |                     25.33 |                        25.02 |                         25.65 |               nan    |          nan    |           nan    |                 nan    |            nan    |             nan    |
| Darkness - lights lit       |  20705 |        1.29 |           1.14 |            1.45 |                     26.82 |                        26.23 |                         27.43 |                 1.06 |            1.03 |             1.09 |                   1.06 |              0.93 |               1.22 |
| Darkness - lights unlit     |    720 |        2.64 |           1.7  |            4.08 |                     28.89 |                        25.7  |                         32.3  |                 1.14 |            1.02 |             1.28 |                   2.18 |              1.39 |               3.41 |
| Darkness - no lighting      |   5682 |        4.72 |           4.2  |            5.3  |                     36.29 |                        35.05 |                         37.55 |                 1.43 |            1.38 |             1.49 |                   3.89 |              3.4  |               4.45 |
| Darkness - lighting unknown |   1588 |        1.01 |           0.62 |            1.63 |                     23.43 |                        21.41 |                         25.57 |                 0.92 |            0.85 |             1.01 |                   0.83 |              0.51 |               1.36 |
| All (valid lighting)        | 101509 |        1.43 |           1.36 |            1.51 |                     26.24 |                        25.97 |                         26.52 |               nan    |          nan    |           nan    |                 nan    |            nan    |             nan    |

Risk ratios compare each category with Daylight (Katz log-method CI). Fatal outcomes are rare (1.4% overall), so Fatal intervals are wide in small categories (e.g. 'lights unlit', n = 720).

## Robustness: the same test within strata

Urban/rural area and police attendance were chosen after the EDA because rural roads are over-represented in unlit darkness and police-attended collisions have a different severity and lighting mix; the choice was not pre-registered. These four tests are consistency checks, not additional hypotheses. Where the chi-square expected-count rule fails (> 20% of cells < 5, or any < 1), a Monte Carlo permutation p-value (10,000 shuffles of severity within fixed margins) is used instead.

| stratifier        | stratum                                            |     n |     chi2 |   dof | p_used_text          |   cramers_v |   v_ci_low |   v_ci_high | effect_size   |   min_expected |   pct_cells_expected_lt5 | chi2_assumptions_met   |
|:------------------|:---------------------------------------------------|------:|---------:|------:|:---------------------|------------:|-----------:|------------:|:--------------|---------------:|-------------------------:|:-----------------------|
| area_type         | Urban                                              | 67145 | 144.772  |     8 | 2.411e-27            |      0.0328 |     0.0282 |      0.0393 | negligible    |         3.5072 |                  13.3333 | True                   |
| area_type         | Rural                                              | 34360 | 213.361  |     8 | 9.721e-42            |      0.0557 |     0.0481 |      0.0657 | negligible    |         7.2694 |                   0      | True                   |
| police_attendance | Police attended                                    | 71365 | 317.258  |     8 | 8.699e-64            |      0.0471 |     0.0405 |      0.0553 | negligible    |        11.4409 |                   0      | True                   |
| police_attendance | No police attendance (incl. self-completion forms) | 30144 |  77.4829 |     8 | 0.0002 (Monte Carlo) |      0.0358 |     0.0183 |      0.0789 | negligible    |         0.066  |                  26.6667 | False                  |

KSI share by lighting within each stratum:

| stratum                                            |   KSI%_Daylight |   KSI%_Darkness - lights lit |   KSI%_Darkness - lights unlit |   KSI%_Darkness - no lighting |   KSI%_Darkness - lighting unknown |
|:---------------------------------------------------|----------------:|-----------------------------:|-------------------------------:|------------------------------:|-----------------------------------:|
| Urban                                              |            22.8 |                         26.7 |                           26.8 |                          29.6 |                               22.6 |
| Rural                                              |            30.2 |                         27.5 |                           32.5 |                          37   |                               25.6 |
| Police attended                                    |            31.2 |                         31.7 |                           32.3 |                          37.8 |                               34.7 |
| No police attendance (incl. self-completion forms) |            12.7 |                         13.8 |                           16.3 |                          17   |                               15.5 |

Stratified re-analysis (Urban: chi2(8) = 144.8, p 2.411e-27, V = 0.033; Rural: chi2(8) = 213.4, p 9.721e-42, V = 0.056; Police attended: chi2(8) = 317.3, p 8.699e-64, V = 0.047; No police attendance (incl. self-completion forms): chi2(8) = 77.5, p 0.0002 (Monte Carlo), V = 0.036). The association remains significant in every stratum; in every stratum 'no lighting' has the highest Fatal/Serious share. The association is therefore not simply an artefact of mixing urban/rural roads or police-attended and unattended reports, although the strata do not rule out other confounders (e.g. speed limit, road type, time of day).

## References for the advanced methods

- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association*, 22(158), 209-212.
- Katz, D., Baptista, J., Azen, S. P., & Pike, M. C. (1978). Obtaining confidence intervals for the risk ratio in cohort studies. *Biometrics*, 34(3), 469-474.
- Bergsma, W. (2013). A bias-correction for Cramér's V and Tschuprow's T. *Journal of the Korean Statistical Society*, 42(3), 323-328.
- Agresti, A. (2013). *Categorical Data Analysis* (3rd ed.). Wiley.