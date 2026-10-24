# Confirmatory data analysis - lighting conditions vs collision severity

**Research question.** Is there a statistically significant association between lighting conditions and collision severity?

- H0: Lighting conditions and collision severity are independent.
- H1: Lighting conditions and collision severity are associated.
- Significance level: alpha = 0.05
- Test: Pearson chi-square test of independence (5 x 3 table, no continuity correction)

## Data

101,525 collisions in the processed file; 16 with missing lighting (`-1`) were excluded (complete-case analysis), leaving **n = 101,509**. 'Darkness - lighting unknown' is a valid guide code and was retained as its own category.

## Test selection and assumptions

Both variables are categorical (lighting nominal with 5 categories; severity ordinal with 3 categories), so Pearson's chi-square test of independence is appropriate. Checks:

1. **Categories mutually exclusive and exhaustive** - each collision has exactly one lighting code and one severity code (verified: no duplicate collision IDs; see preprocessing summary).
2. **Sufficient expected counts** - minimum expected count = 10.31; cells with expected < 5: 0.0%; cells with expected < 1: 0. The usual rule (>= 80% of cells >= 5, none < 1) is met, so the asymptotic chi-square distribution is valid and no category merging or exact test is needed.
3. **Independence of observations** - each row is a separate reported collision, but collisions are not strictly independent draws (they cluster in space and time, e.g. a single event or weather system can generate several). This cannot be tested from the data and is a limitation: the nominal p-value is probably somewhat optimistic. With a p-value this far below alpha the decision is not sensitive to that.
4. **Random sampling** - the data are a census of police-reported injury collisions, not a random sample; inference is therefore about association in the 2025 reported data, not generalisation to unreported collisions.

An ordinal trend test (e.g. Cochran-Armitage) was not used because lighting has no natural single ordering across all five categories.

## Observed frequencies

| Lighting condition          |   Fatal |   Serious |   Slight |   Total |
|:----------------------------|--------:|----------:|---------:|--------:|
| Daylight                    |     883 |     17561 |    54370 |   72814 |
| Darkness - lights lit       |     267 |      5287 |    15151 |   20705 |
| Darkness - lights unlit     |      19 |       189 |      512 |     720 |
| Darkness - no lighting      |     268 |      1794 |     3620 |    5682 |
| Darkness - lighting unknown |      16 |       356 |     1216 |    1588 |

## Expected frequencies under H0

| Lighting condition          |   Fatal |   Serious |   Slight |
|:----------------------------|--------:|----------:|---------:|
| Daylight                    |  1042.3 |   18067   |  53704.7 |
| Darkness - lights lit       |   296.4 |    5137.4 |  15271.2 |
| Darkness - lights unlit     |    10.3 |     178.7 |    531   |
| Darkness - no lighting      |    81.3 |    1409.9 |   4190.8 |
| Darkness - lighting unknown |    22.7 |     394   |   1171.2 |

## Adjusted standardised residuals (|value| > 1.96 indicates a cell departing from independence)

| Lighting condition          |   Fatal |   Serious |   Slight |
|:----------------------------|--------:|----------:|---------:|
| Daylight                    |   -9.35 |     -8.17 |    10.54 |
| Darkness - lights lit       |   -1.93 |      2.7  |    -2.13 |
| Darkness - lights unlit     |    2.74 |      0.9  |    -1.62 |
| Darkness - no lighting      |   21.46 |     12.14 |   -17.71 |
| Darkness - lighting unknown |   -1.43 |     -2.23 |     2.57 |

## Test result

- chi-square statistic = **681.80**
- degrees of freedom = **8** ((5-1) x (3-1))
- p-value = **5.934e-142** (log10 p = -141.2)
- decision at alpha = 0.05: **Reject H0**

## Effect size

- Cramér's V = **0.0580** (95% bootstrap CI 0.0520-0.0650, 5,000 resamples, seed 20250101); bias-corrected V = 0.0576
- Benchmarks for df* = 2: small = 0.071, medium = 0.212, large = 0.354 -> **negligible**

## Severity proportions with 95% Wilson confidence intervals

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

One focused sensitivity analysis, reported in full (all four tests, none omitted). Urban/rural area and police attendance were chosen because the exploratory analysis (Figures 5-6) showed that rural roads are over-represented in unlit darkness and that police-attended collisions are more often Serious/Fatal and have a different lighting mix - i.e. they are plausible confounders/reporting effects; the choice was made after the EDA, not pre-registered. These four tests are consistency checks, not additional hypotheses. Where the chi-square expected-count rule fails (> 20% of cells < 5, or any < 1), a Monte Carlo permutation p-value (10,000 shuffles of severity within fixed margins) is used instead.

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

## Interpretation

- **Statistical significance.** Because p = 5.934e-142 is below alpha = 0.05, H0 is rejected: the data show a statistically significant association between lighting condition and collision severity.
- **Practical significance.** With n = 101,509 even small departures from independence are detectable, so significance alone is uninformative. Cramér's V = 0.058 (95% bootstrap CI 0.052-0.065; bias-corrected 0.058) is negligible by Cohen's benchmarks for df* = 2 (small 0.07, medium 0.21, large 0.35); V^2 = 0.0034, i.e. a very weak overall association. The overall effect is small because most collisions occur in daylight or lit darkness, where severity is close to the overall mix; the 'no lighting' row (only 5.6% of collisions) supplies 89.6% of the chi-square statistic.
- **Pattern.** The association is concentrated in darkness with no street lighting: Fatal or Serious share 36.3% (95% CI 35.0-37.5) vs 25.3% in daylight (risk ratio 1.43, 95% CI 1.38-1.49); Fatal share 4.7% vs 1.2% (RR 3.89, 95% CI 3.40-4.45). Cells with the largest adjusted residuals: Darkness - no lighting x Fatal (+21.5); Darkness - no lighting x Slight (-17.7); Darkness - no lighting x Serious (+12.1); Daylight x Slight (+10.5).
- **Robustness.** Stratified re-analysis (Urban: chi2(8) = 144.8, p 2.411e-27, V = 0.033; Rural: chi2(8) = 213.4, p 9.721e-42, V = 0.056; Police attended: chi2(8) = 317.3, p 8.699e-64, V = 0.047; No police attendance (incl. self-completion forms): chi2(8) = 77.5, p 0.0002 (Monte Carlo), V = 0.036). The association remains significant in every stratum; in every stratum 'no lighting' has the highest Fatal/Serious share. The association is therefore not simply an artefact of mixing urban/rural roads or police-attended and unattended reports, although the strata do not rule out other confounders (e.g. speed limit, road type, time of day).

## Limitations

- Association, not causation: lighting is correlated with time of day, season, road type, speed limit and rurality, and we have not adjusted for these.
- The data are reported collisions only; without exposure (traffic by lighting condition) the results cannot show that darkness *increases* risk, only how severity is distributed among collisions that were reported.
- Severity is recorded under two systems (injury-based vs. officer-reported), and police attendance varies; lighting is an officer's judgement.
- Observations are not strictly independent (see assumption 3).