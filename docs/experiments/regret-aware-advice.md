# E2: can the tool say "unsure, run now" on risky days? (branch exp/regret-aware-advice)

Owner: A (HM-Claude). Verdict: **LOSS against the pre-set kill rule (1 of 5 grids); one informative trade-off in Britain.**

## Question
The earlier "unsure" rule (act only if predicted saving >= a threshold) gave no gain. Add AGREEMENT between three independent
forecasts (full model, history-only model, persistence): act only if the predicted saving is large enough AND the three pick start
times within a tolerance. Does this remove the "harmful" days (advice dirtier than starting at midnight) without costing much?

## Run
`python -I -W ignore src/experiments/regret_aware_advice/run.py` (24 h of slack, 4-hour job). Threshold and tolerance tuned on
Jan-Apr 2026 only (120 days), scored once on May-Nov 2026 (191-194 days). First-stage models trained on 2023-2025.
Kill rule (set before running): WIN only if harmful days fall with a 95% block-bootstrap interval below zero AND mean cost rises
by < 0.5 g/kWh, in at least 3 of 5 grids.

## Results (May-Nov 2026)
| Region | acts on | harmful days: always act -> with rule | change [95% CI], pp | mean g/kWh: always -> with rule (change [CI]) |
|---|---|---|---|---|
| Virginia | 92% | 6.8% -> 4.7% | -2.1 [-4.7, -0.5] | 331.4 -> 331.9 (+0.48 [0.12, 0.88]) |
| California | 98% | 0.0% -> 0.0% | 0 | 110.9 -> 111.3 (+0.37) |
| Texas | 100% | 1.0% -> 1.0% | 0 | unchanged |
| Germany | 98% | 1.6% -> 1.6% | 0 | unchanged |
| Great Britain | 74% | 13.4% -> 4.1% | -9.3 [-13.9, -4.6] | 87.3 -> 88.6 (+1.35 [-0.46, 3.44]) |

Result: 1 of 5 grids meets the kill rule (Virginia, narrowly: the cost rise is 0.48). Britain removes most harmful days but pays 1.35 g/kWh,
above our 0.5 limit.

## Honest reading
- In California, Texas and Germany harmful days are already rare (0-1.6%), so there is nothing to fix.
- Virginia and Britain are where the advice is sometimes harmful (6.8% and 13.4% of days). Agreement between forecasts catches about a third
  (Virginia) to two thirds (Britain) of those, at a small cost in average savings. That is a real trade-off a household can choose, but it is
  not a free win, and the tuning set is only 120 days.
- Still not adopted into the app; the app keeps its simple "no clear winner" message for tiny predicted gains.

## Proposed README text (owner integrates; optional)
"Where the advice is sometimes worse than starting at midnight (6.8% of days in Virginia, 13.4% in Britain), asking three forecasts to agree before acting
cut those days to 4.7% and 4.1% at a cost of about 0.5 to 1.4 g/kWh in average savings (tuned on Jan-Apr 2026, scored on May-Nov)."

## Files
`results/experiments/regret_aware_advice/regret_aware_advice.csv`
