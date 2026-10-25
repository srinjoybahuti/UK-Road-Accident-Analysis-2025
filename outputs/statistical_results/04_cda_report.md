# Confirmatory data analysis - lighting conditions vs collision severity

**Research question.** Is there a statistically significant association between lighting conditions and collision severity?

- H0: Lighting conditions and collision severity are independent.
- H1: Lighting conditions and collision severity are associated.
- Significance level: alpha = 0.05
- Test: Pearson chi-square test of independence (5 x 3 table, no continuity correction)

## Data

101,525 collisions in the processed file; 16 with missing lighting (`-1`) were excluded, leaving **n = 101,509**. 'Darkness - lighting unknown' is a valid guide code and was kept as its own category.

## Why a chi-square test

Both variables are categorical (lighting: 5 categories; severity: 3 categories), so the chi-square test of independence is appropriate. Its main requirement - enough expected counts in every cell - is met (smallest expected count = 10.31; 0% of cells below 5). Collisions are not strictly independent (they cluster in space and time) and the data are a census of reported collisions, not a random sample, so results describe the 2025 reported data only.

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

## Test result

- chi-square statistic = **681.80**
- degrees of freedom = **8** ((5-1) x (3-1))
- p-value = **5.934e-142**
- decision at alpha = 0.05: **Reject H0**
- Cramér's V = **0.058** (negligible)

## Severity by lighting (percentages)

| lighting                    |      n |   Fatal % |   Serious % |   Slight % |   Fatal or Serious % |
|:----------------------------|-------:|----------:|------------:|-----------:|---------------------:|
| Daylight                    |  72814 |       1.2 |        24.1 |       74.7 |                 25.3 |
| Darkness - lights lit       |  20705 |       1.3 |        25.5 |       73.2 |                 26.8 |
| Darkness - lights unlit     |    720 |       2.6 |        26.2 |       71.1 |                 28.9 |
| Darkness - no lighting      |   5682 |       4.7 |        31.6 |       63.7 |                 36.3 |
| Darkness - lighting unknown |   1588 |       1   |        22.4 |       76.6 |                 23.4 |
| All (valid lighting)        | 101509 |       1.4 |        24.8 |       73.8 |                 26.2 |

## Interpretation

- **Statistical significance.** Because p = 5.934e-142 is below alpha = 0.05, H0 is rejected: the data show a statistically significant association between lighting condition and collision severity.
- **Practical significance.** The association is very weak: Cramér's V = 0.058 (negligible). With n = 101,509 even tiny differences are statistically significant, so the size of the difference matters more than the p-value. Most collisions occur in daylight or lit darkness, where the severity mix is close to the overall mix; the 'no lighting' group is only 5.6% of collisions but accounts for 89.6% of the chi-square statistic.
- **Pattern.** The difference comes mainly from darkness with no street lighting: 36.3% of these collisions were Fatal or Serious, against 25.3% in daylight, and 4.7% were Fatal against 1.2% in daylight (about 3.9 times as high). Other lighting groups are close to the overall 26.2%.

## Limitations

- Association, not causation: lighting is related to time of day, season, road type, speed limit and rural/urban location, which were not adjusted for.
- Reported collisions only, with no traffic exposure data: the results show how severity is distributed among reported collisions, not that darkness increases risk.
- Severity is recorded under two systems (injury-based vs officer-reported), police attendance varies, and lighting is an officer's judgement.
- Collisions are not strictly independent observations.

Optional advanced methods (bootstrap CI, Wilson CIs, risk ratios, residuals, stratified robustness checks): `outputs/technical/04_advanced_methods.md`.