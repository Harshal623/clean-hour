# Rubric review and suggested upgrades (Sidharth's Claude, Nov 15)

Numbers here come from `results/experiments/` (see its README). Owners decide what to adopt.

## Biggest risk: "one place"
The Climate brief says "Focus on one location or region" and judges "usually score better" for a
project "tied to a real place" than "the whole planet". Five grids on three continents can read as
the planet. Suggested framing that keeps the multi-grid work:
- **Main place:** Northern Virginia households and the Loudoun data-center corridor on the PJM grid
  (our own place, our own school's region).
- **Other four grids:** a "does it transfer?" test of the same method, one table, one paragraph.
  That is an "own question" (does it hold up in a new situation), which the brief rewards.

## One main takeaway (clarity)
Candidate headline: "A model that is better at predicting carbon is not automatically better at
choosing clean hours. Training it for the choice captures 87-89% of the best possible saving,
up from 78-81%." It is honest, surprising, and backed by held-out months (May-Nov 2026).

## Technical quality: what to add to the write-up
1. Report forecast accuracy as well as the decision metric: MAE 13.8 (model) vs 21.5 (persistence)
   vs 29.7 (climatology) g/kWh, by horizon (`accuracy_by_horizon.csv`).
2. Show the mismatch: the model finds tomorrow's 4 cleanest hours on 51% of days vs 54% for
   "repeat yesterday" (`ranking_accuracy.csv`).
3. The fix and its test: decision stacker, rolling origin, beats the original model at every delay
   (about -2.7 g/kWh, all 95% CIs below zero) and ties persistence at 12-24 h instead of losing to it.
4. Keep the failure section and add: in May-Nov the original full model lost to persistence at
   12-24 h, a sign its weather/demand inputs drift.

## Impact: honest household numbers
- Plugging in at 19:00 is the dirtiest time of day in every month of 2026 (`clean_hours_heatmap.png`).
- Dishwasher that can wait a day: forecast picks save about 10-11% of its emissions; EV that must
  be charged by 07:00: about 5%, and a simple "after midnight" rule gets most of that.
- Per household per year, with stated ASSUMED usage: EV about 47-75 kg CO2, dishwasher 5-11 kg.
  Grid-average, not marginal; say so next to every number.
- Scale it up only with a sourced count (for example Virginia's registered EVs) and show the
  arithmetic, never a bare total.

## Creativity
- The "train for the decision, not the number" angle is the fresh part; most teams will report MAE.
- The heatmap answers a question any family has: "when is the grid cleanest where I live?"
- Demo idea for the app owner: show "plug in now" vs "plug in at the suggested time" side by side
  with the grams saved for that night.

## Gaps judges may notice
- No user test. Ten minutes with one parent or neighbour using the app, and one quote, would help.
- The 2026 Jan-Apr months were used to train the stacker, so its scored period is May-Nov only;
  say this plainly.
- Data hosts were unreachable from this agent's sandbox, so the first-stage model was not retrained
  here; the stacker works on top of the saved test forecasts.
