# E4: is it a quirk of 2026? (branch exp/year-robustness)

Owner: A (HM-Claude). Verdict: **WIN (robust).** The qualitative conclusions repeat on 2025; absolute savings vary by year.

## Question
All headline results use 2026 as the test year. Do the same conclusions hold if we train on 2023-2024 and test on all of 2025?

## Run
`python -I -W ignore src/experiments/year_robustness/run.py` (same recipe and fixed settings as `src/multigrid.py`; only the split
differs: train 2023-2024, test 2025, never shuffled; days with missing hours dropped).

## Results (4-hour job; % cleaner than starting at midnight; model minus simple hour-of-week rule, g/kWh, 95% interval)
| Region (2025, 360-365 days) | 24 h: model % saved | 24 h model minus rule | 72 h: model % saved | 72 h model minus rule |
|---|---|---|---|---|
| Virginia | 4.3 | -11.0 [-13.5, -8.6] | 7.0 | -12.3 [-15.3, -9.1] |
| California | 29.5 | -10.9 [-13.8, -8.3] | 33.0 | -15.3 [-19.3, -12.5] |
| Texas | 24.6 | -1.3 [-4.0, +1.4] (tie) | 31.3 | -16.2 [-23.0, -10.1] |
| Germany | 37.2 | -2.5 [-6.7, +1.9] (tie) | 43.8 | -12.2 [-19.1, -4.3] |
| Great Britain | 17.5 | -15.7 [-19.1, -11.6] | 27.6 | -21.2 [-25.3, -16.2] |

Against "repeat yesterday" (persistence) at 24 h: Virginia -0.7 [-2.0, +0.7] and California +0.1 [-0.9, +1.0] (ties), Texas -6.7,
Germany -4.9, Britain -13.0 (model better); at 72 h the model beats persistence everywhere (-8.9 to -28.9).

## Honest reading
- Same pattern as 2026: at 3 days the model beats the simple rule in all five grids; at 24 h Texas and Germany tie it; Britain gains most.
- Absolute savings differ by year: California 29.5% (2025) vs 54.7% (2026), Virginia 4.3% vs 6.9%, Britain 17.5% vs 28.8%. The grids are
  changing (more solar and batteries), so "% cleaner" numbers should be read as one-year measurements, not constants.
- Small differences from 2026: California beats the simple rule at 24 h in both years (-10.9 vs -6.6); Texas beats persistence at 24 h in 2025 (-6.7) but ties it in 2026.

## Proposed README text (owner integrates)
"Robustness: training on 2023-2024 and testing on all of 2025 gives the same pattern (the model beats the simple rule in all five grids with 3 days of
slack and ties it in Texas and Germany at 24 h), but absolute savings differ by year (for example California 29.5% in 2025 vs 54.7% in 2026), so
treat the percentages as one-year measurements."

## Files
`results/experiments/year_robustness/year_robustness_2025.csv`
