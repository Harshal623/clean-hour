# Experiments log (Sidharth's Claude, Nov 14-15)

All numbers below come from scripts in `src/experiments/`, run on `results/test_predictions.csv.gz`
(the saved 2026 test forecasts of the models trained on 2023-2025). No raw data was re-downloaded,
no 2026 day was used to train the first-stage models. Re-run: `python -I src/experiments/reeval.py`,
then `decision_stack.py`, `household_shift.py`, `figures.py`.

## 1. Re-check of the reported numbers (`reeval.py`)
The scheduling table in README/DECISION reproduces exactly from the saved predictions
(e.g. 24 h: run now 353.4, persistence 330.6, climatology 342.6, model 330.3, perfect 324.7).

Hourly forecast accuracy, 2026 test, gCO2/kWh (`accuracy_by_horizon.csv`):

| method | MAE all | MAE day 1 | MAE day 3 | RMSE all | skill vs persistence |
|---|---|---|---|---|---|
| persistence | 21.5 | 17.4 | 24.2 | 27.7 | 0% |
| hour-of-week climatology | 29.7 | 29.8 | 29.6 | 36.1 | -39% |
| model (full) | 13.8 | 12.8 | 14.6 | 17.4 | +35% |
| model (history only) | 18.8 | 15.5 | 21.2 | 23.9 | +12% |

**Key finding: lower error does not mean better choices.** The full model cuts hourly error by 35%,
yet it finds the 4 cleanest hours of tomorrow on 51% of days vs 54% for "repeat yesterday"
(`ranking_accuracy.csv`). The model is trained to get the level right (it runs about 4 g/kWh high),
while the scheduler only needs the ORDER of the hours.

## 2. Tried: blend model + persistence (`reeval.py`, part 4) -> small, mostly not significant
Weight chosen on Jan-Apr 2026, scored on May-Nov 2026. Better than the model at 12 h
(-2.4 [-3.5, -1.5] g/kWh) but not significantly at 24-72 h. Not adopted.

## 3. Tried: decision-trained second stage ("decision stacker") -> ADOPT
`decision_stack.py`. A small gradient-boosting model learns the SHAPE of the next 76 hours
(each hour minus that day's mean) from the first-stage forecasts, persistence, climatology,
calendar and weather. Rolling origin: to score month m it trains only on 2026 days before m;
scored May-Nov 2026 (191 days). One configuration, not tuned on the scored months.

| allowed delay | persistence | original model | decision stacker | perfect | stacker minus model, 95% CI | stacker minus persistence, 95% CI |
|---|---|---|---|---|---|---|
| 12 h | 330.6 | 333.3 | **330.3** | 327.4 | -2.9 [-4.2, -1.9] | -0.3 [-1.1, +0.7] |
| 24 h | 331.2 | 333.2 | **330.3** | 327.1 | -2.9 [-4.3, -1.7] | -0.9 [-2.0, +0.1] |
| 48 h | 331.2 | 326.3 | **323.7** | 319.0 | -2.6 [-4.0, -1.3] | -7.6 [-9.7, -5.1] |
| 72 h | 331.2 | 320.9 | **318.2** | 313.1 | -2.7 [-4.0, -1.2] | -13.0 [-15.7, -9.2] |

Share of the perfect-foresight saving captured: original model 78-81%, decision stacker 87-89%
at every delay. It beats the original model at every delay, and at 12-24 h it closes the gap to
persistence (statistical tie, no longer worse). Figure: `capture_vs_flexibility.png`.
Also: a plain average of the three shapes (model, history-only model, persistence; no training)
already captures 82-88%, so most of the gain is "combine forecasts and judge them on ranking".

Caveat: in May-Nov 2026 the original full model was significantly WORSE than persistence at 12-24 h
(+2.7 and +2.0 g/kWh), while in Jan-Nov overall it was a tie. Its weather/demand inputs may drift.

## 4. Household version (`household_shift.py`)
Start an appliance at 19:00 (default) or let the tool pick, using forecasts issued 25 h earlier.

| scenario (Jan-Nov 2026) | default g/kWh | perfect saves | original model saves | repeat yesterday saves |
|---|---|---|---|---|
| EV 4 h, finish by 07:00 | 367.6 | 5.5% | 5.1% | 4.8% |
| dishwasher 2 h, within a day | 366.3 | 11.9% | 10.0% (dirtier than default on 2.6% of days) | 9.5% (6.8%) |

May-Nov, dishwasher: decision stacker saves 11.2% vs 10.2% for the original model.
With our ASSUMED yearly use (EV 2,500-4,000 kWh; dishwasher 150-300 kWh) that is about
47-75 kg CO2 a year for an EV and 5-11 kg for a dishwasher, per household, on grid-average emissions.
Honest message: for an EV, simply "charge after midnight" gets most of the gain; the forecast
matters more for appliances that can wait a full day (midday solar hours in spring and autumn).

## 5. When are the clean hours? (`clean_hours_heatmap.png`)
2026 actual PJM average intensity by hour and month: 19:00-22:00 is the dirtiest time in every
month (when people get home). The cleanest hour is always in daylight: 12:00-14:00 in Jan-May
and October (solar), and mid-morning 09:00-10:00 in Jun-Sep and November, before the afternoon
air-conditioning peak. Overnight hours are cleaner than the evening but rarely the cleanest.
