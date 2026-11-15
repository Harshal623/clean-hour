# E10: can tuning, more features, a blend or quantile loss beat the production model? (branch exp/model-variants)

Owner: A (HM-Claude). Verdict: **TIE (three variants) and LOSS (quantile).** The production model stays.

## Question
The production model is a change-target gradient-boosting model with fixed settings. Would per-grid tuning, extra history and fuel-mix features,
a validation-fit blend, or quantile loss improve the scheduling decision?

## Honest protocol (set before scoring 2026)
Every choice is made on 2025-H2 validation using models trained on 2023 to 2025-H1 only; a variant counts as "adopted on validation" only if it
beats the baseline settings by more than 0.1 g/kWh there (decision metric: mean chosen-window g/kWh averaged over 24 h and 72 h slack). Adopted
settings are refit on 2023-2025 and scored ONCE on 2026 against the production model. Kill rule: WIN in a grid needs adoption on validation AND a
95% 7-day block-bootstrap interval of (variant minus baseline) entirely below zero at BOTH 24 h and 72 h; overall WIN needs >= 3 of 5 grids; LOSS if any
grid is significantly worse. Baseline reproduces production numbers (checked: Britain 85.5 and 70.5 g/kWh).

Run: `python -I -W ignore src/experiments/model_variants/run_variant.py VARIANT GRID` (v1..v4), then `aggregate.py`.
V1 = random 15 of 27 (max_depth x learning_rate x min_samples_leaf) configs; V2 = 14-day same-hour mean/std/min plus same-hour fuel-share lags (gas, coal,
wind, solar, nuclear; none for Britain); V3 = blend of full model, history-only model and persistence with weights fit on validation (step 0.1);
V4 = quantile loss with q in {0.5, 0.75, 0.9} chosen on validation.

## Results (2026 test, g/kWh of the chosen window; variant minus baseline, negative = variant better; 95% interval)
| Variant | Grids adopted on validation | Significant at both delays | Notable |
|---|---|---|---|
| V1 hyperparameters | 3 of 5 | 0 of 5 | Texas -0.8 [-2.0, +0.3] at 24 h; California and Germany kept baseline settings |
| V2 extra features | 3 of 5 | 0 of 5 | all differences within about 1 g/kWh and intervals include 0 |
| V3 blend | 5 of 5 | 0 of 5 | significantly better at 24 h in 4 grids (California -0.25, Texas -1.79, Britain -0.66, Virginia -0.73), never at 72 h |
| V4 quantile | 3 of 5 | 0 of 5; significantly WORSE in Britain at 72 h (+1.5 [+0.2, +2.9]) | conservative lower bound did not help |

Full table: `results/experiments/model_variants/model_variants_summary.csv`; raw runs: `results/experiments/model_variants/raw/`.

## Honest reading
- Nothing beats the production model by a margin that survives both delays. The largest gains are 1-2 g/kWh (under 1% of the chosen window's intensity).
- The blend helps a little at 24 h in four grids but not at 72 h, so by our own rule it is a TIE. It is the only variant worth a second look.
- Quantile (conservative) forecasts do not help the choice and hurt in Britain at 3 days.
- Takeaway: the model is not tuning-limited; remaining headroom is mostly the gap to perfect hindsight (information the 18:00 forecast does not contain).

## Proposed README text (optional)
"We also tried per-grid hyperparameter tuning, extra history and fuel-mix features, a validation-fit blend and quantile loss (all chosen on 2025 H2 validation, scored once
on 2026). None beat the production model with an interval below zero at both 24 h and 72 h; the blend gained 0.3-1.8 g/kWh at 24 h in four grids only."
