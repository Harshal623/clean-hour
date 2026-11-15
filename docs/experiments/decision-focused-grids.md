# E1: does "train for the decision, not the number" transfer beyond Virginia? (branch exp/decision-focused-grids)

Owner: A (HM-Claude). Verdict: **TIE / does not transfer.** The stacker clearly helps in Virginia only.

## Question
Sidharth's decision stacker (`src/experiments/decision_stack.py`, Virginia only) learns the SHAPE of the next
76 hours so that it ranks hours well, instead of predicting levels. It captured 87-89% of the perfect saving in
Virginia vs 78-81% for the first model. Is that a general finding or a Virginia quirk?

## Run
`python -I -W ignore src/experiments/decision_focused_grids/run.py` (needs `results/test_predictions_all_ext.csv.gz`,
produced by `src/multigrid.py`). Same recipe and fixed configuration as Sid's, applied to all five grids.

## Data and split
First-stage models trained on 2023-2025 only. Stacker: rolling origin, for month m (May..Nov 2026) trained on 2026 days
before m only. Scored on May-Nov 2026 (191-194 days per grid). Job = 4 h, decided at 18:00 the evening before.
Note: the first-stage model here is the FINAL (change-target) model, which is better than the first Virginia model
Sid started from, so Virginia's gain is smaller than his number (-1.8 vs -2.9 at 24 h).

## Results (24 h and 72 h; "minus model" negative = stacker better; 95% 7-day block bootstrap)
| Region | Delay | % of perfect saving: persistence / first model / stacker | stacker minus first model [95% CI] |
|---|---|---|---|
| Virginia | 24 h | 85.3 / 84.5 / 90.8 | -1.77 [-2.53, -1.15] |
| Virginia | 72 h | 56.8 / 82.7 / 87.5 | -2.02 [-3.40, -0.42] |
| California | 24 h | 97.5 / 98.4 / 98.3 | +0.11 [-0.36, +0.66] |
| California | 72 h | 84.4 / 92.5 / 91.0 | +2.24 [+0.16, +5.63] (stacker WORSE) |
| Texas | 24 h | 94.0 / 94.8 / 95.6 | -0.88 [-2.00, -0.39] |
| Texas | 72 h | 75.8 / 85.9 / 84.8 | +1.59 [-2.47, +5.90] |
| Germany | 24 h | 97.5 / 97.8 / 98.6 | -1.79 [-3.83, +0.21] |
| Germany | 72 h | 86.7 / 95.1 / 94.7 | +0.95 [-2.15, +4.22] |
| Great Britain | 24 h | 75.1 / 85.5 / 85.3 | +0.11 [-1.19, +1.31] |
| Great Britain | 72 h | 54.4 / 85.0 / 83.5 | +1.06 [-0.62, +3.01] |

Kill rule (set before running): WIN needs the stacker's interval entirely below zero at both 24 h and 72 h in at
least 3 of 5 grids. Result: 1 of 5 (Virginia). **Not a WIN.**

## Honest reading
- The decision-focused second stage helps in Virginia, the flattest grid (hourly spread about 34 g/kWh), where
  getting the level right matters least and the ORDER of hours is subtle.
- In California, Germany and Texas the first model already captures 95-98% of the perfect saving at 24 h (the
  daily solar cycle makes ranking easy), so there is nothing left to gain; at 72 h the stacker is slightly worse or
  tied (California +2.2, interval above zero).
- So "a better forecast is not automatically a better choice" holds where the daily pattern is weak, and does not
  generalise as "always train for ranking". Related published finding: LiteCast (arXiv 2511.06187) reports ranking
  preservation matters more than error across 50 regions; our contribution here is a held-out 2026 test and the
  boundary condition (flat grids).
- The stacker's training data is only 2026 months before the scored month, so early months have little data.

## Proposed README text (owner integrates; do NOT claim a general win)
"In Virginia a second-stage model trained to rank hours captured 91% of the perfect saving at 24 h versus 85% for the
first model (-1.8 g/kWh [-2.5, -1.2]). It did not transfer: in California, Texas, Germany and Britain the first model
already captured 85-98% and the stacker was tied or slightly worse (results/experiments/decision_focused_grids/)."

## Files
`results/experiments/decision_focused_grids/decision_focused_grids.csv`
