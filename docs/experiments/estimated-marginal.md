# E3: does average-based shifting also help by an ESTIMATED marginal measure? (branch exp/estimated-marginal)

Owner: A (HM-Claude). Verdict: **MIXED.** Holds in Virginia and California; the proxy says it may not in Texas and Germany.

## Question
Our savings use AVERAGE grid intensity. Critics say the right signal is the MARGINAL plant. PJM's marginal rates need
an account and the other grids publish none, so we estimate a coarse proxy and check whether the hours that are cleanest
by average are also cleaner by the proxy.

## Method (coarse by design)
Net-load regression in the spirit of Hawkes (2010) and Siler-Evans et al. (2012): for each (season x 6-hour block) group,
regress the hourly change of each dispatchable fuel on the hourly change in net load (generation minus wind minus solar);
negative slopes set to 0 and slopes normalised to sum to 1; marginal intensity = sum(share x emission factor).
Fitted on 2023-2025 only; evaluated on 2026 test days with the actual hourly intensity (hindsight, 24 h of slack, 4-hour job).
This gives a daily SHAPE per block and season, not a dispatch model, and it cannot validate itself against real marginal rates.
Run: `python -I -W ignore src/experiments/estimated_marginal/run.py`. Britain excluded (no fuel mix in our pipeline).

## Results (g/kWh saved versus starting at midnight; hindsight best window by AVERAGE intensity)
| Region | days | saved by the average rule, measured by AVERAGE | measured by ESTIMATED MARGINAL | % days it lowers estimated marginal | saved if we had optimised the marginal proxy instead |
|---|---|---|---|---|---|
| Virginia | 311 | 28.7 | +36.4 | 68.8% | 94.9 (and -4.9 by average) |
| California | 314 | 122.3 | +42.9 | 89.8% | 83.9 (and +91.4 by average) |
| Texas | 314 | 108.4 | -17.8 | 0.0% | 20.7 (and -9.1 by average) |
| Germany | 314 | 177.9 | -13.8 | 32.5% | 36.6 (and -4.1 by average) |

Estimated marginal intensity (lifecycle g/kWh): Virginia 396-569, California 181-373, Texas 514-582, Germany 600-699
(by season and block; see `results/experiments/estimated_marginal/`).

## Honest reading
- In Virginia and California, moving to the cleanest hours by average also lowers the estimated marginal intensity on most
  days, so the main claim holds under this proxy.
- In Texas and Germany the proxy says the average-cleanest hours (midday solar) are NOT cleaner at the margin (coal or gas
  still sets the margin; solar just displaces average). If the proxy is right, average-based savings there overstate the
  effect of one extra shifted load. We cannot confirm the proxy, so this is a limitation, not a finding about those grids.
- In Virginia the hours that minimise estimated marginal intensity are NOT the hours that minimise average intensity
  (only 1% of days have similar windows; shifting by marginal would cost -4.9 g/kWh on the average measure). Average and
  marginal rank hours differently there, so the result depends on which one you believe.

## Proposed README text (owner integrates)
"Limits: we use average, not marginal, emissions. A coarse estimate of marginal intensity (net-load regression, fitted on
2023-2025) agrees with our advice in Virginia and California (68.8% and 89.8% of 2026 days) but not in Texas or Germany, where
it suggests the benefit of shifting at the margin could be smaller or absent. The estimate is a proxy and unvalidated."

## Files
`results/experiments/estimated_marginal/marginal_agreement.csv`, `estimated_marginal_profiles.png`
