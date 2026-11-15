# E3: does shifting by AVERAGE intensity also help by an estimated MARGINAL intensity? (branch exp/estimated-marginal)

Owner: A (HM-Claude). Verdict: **MIXED. Agrees in Virginia and California, disagrees in Texas and Germany.** Coarse proxy; see caveats.

## Question
Critics say scheduling should follow the marginal plant, not the grid average. Public marginal rates for our grids are not
freely available (PJM's need an account), so we estimate a coarse proxy and check whether following the average-based
advice also lowers it.

## Method (src/experiments/estimated_marginal/run.py)
Net-load regression in the spirit of Hawkes (2010) and Siler-Evans et al. (2012): in each (season x 6-hour block) group,
regress the hourly change of each dispatchable fuel (coal, gas, oil, hydro, nuclear, other) on the hourly change in net load
(generation minus wind minus solar); negative slopes set to zero and the rest normalised to sum to 1; marginal intensity =
sum(share x emission factor). Fitted on 2023-2025 only; applied to 2026 days. Britain excluded (no fuel mix in our pipeline).
Run: `python -I -W ignore src/experiments/estimated_marginal/run.py`.

## Results (24 h delay, 4-hour job, 2026 test days, hindsight windows; g/kWh)
| Region | Days | Average intensity saved by the average rule | Estimated marginal saved by the average rule | Days the average rule lowers the marginal proxy | Average intensity saved by the marginal rule |
|---|---|---|---|---|---|
| Virginia | 311 | 28.7 | +36.4 | 69% | -4.9 |
| California | 314 | 122.3 | +42.9 | 90% | +91.4 |
| Texas | 314 | 108.4 | -17.8 | 0% | -9.1 |
| Germany | 314 | 177.9 | -13.8 | 33% | -4.1 |

Estimated marginal intensity is high everywhere (Virginia about 466, California 267, Texas 551, Germany 635 g/kWh on average),
because dispatchable plants that respond to load are mostly gas and coal.

## Honest reading
- Where the average-based advice also lowers the marginal proxy (Virginia, California) the two signals agree.
- In Texas and Germany the average-optimal window is slightly WORSE by the marginal proxy (-17.8 and -13.8 g/kWh), so the
  headline savings there are average-emissions savings that the marginal view does not confirm.
- The proxy is coarse (one value per season and 6-hour block, no dispatch model), its Texas profile is nearly flat
  (514-582), and day-to-day marginal variation is invisible to it. Treat as a sanity check, not a result to headline.
- Implication for the write-up: keep the limit "average, not marginal" and add that a rough marginal check agreed for
  Virginia and California but not for Texas and Germany.

## Proposed README text (owner integrates)
"A rough marginal-emissions check (net-load regression, fitted on 2023-2025) agreed with the average-based advice in Virginia
and California but not in Texas and Germany, where the marginal plant is almost always gas or coal
(docs/experiments/estimated-marginal.md)."

## Files
`results/experiments/estimated_marginal/marginal_agreement.csv`, `estimated_marginal_profiles.png`
