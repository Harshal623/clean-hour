# Clean-Hour: when should a Loudoun data center run its flexible AI jobs?

**Track:** Climate
**Team:** <TEAM NAMES HERE>
**Code:** this repo. Notebook with outputs: `notebooks/loudoun_carbon_scheduler.ipynb`. Demo: `python app/app.py`.

## The problem
Loudoun County, Virginia hosts the densest cluster of data centers in the world, and AI training and batch jobs run 24/7 on the grid that serves them. The grid's carbon intensity (grams of CO2 per kWh) changes hour to hour as gas, coal and nuclear plants ramp. A data-center operations lead who can delay a flexible job by half a day or more can run it in a cleaner window, if they can predict tomorrow's hours. We test whether an ML forecast beats simple rules for that decision.

## What we built
- **Who/when:** an operations lead at 18:00, deciding when tomorrow's 4-hour flexible batch job (for example an AI training chunk) will start.
- **In:** the last week of grid carbon intensity, PJM's demand forecast, Dominion-zone demand, and Loudoun's weather forecast.
- **Out:** a forecast of the next days' hourly carbon intensity, the recommended start hour within the allowed delay, the expected saving, or "unsure, run now".
- **Demo:** `python app/app.py` (Gradio). Pick a 2026 test day and an allowed delay of 0/12/24/48/72 hours.

## What we added
Our own idea (not one of the three suggested projects). Own user: a Loudoun data-center operator. Own data: Dominion-zone demand plus an hourly forecast-weather archive for Ashburn. Own question: how much scheduling flexibility does an operator need before an ML forecast beats simple rules, and is the forecast needed at all?

## How it works
- **Data (all public, no personal data):** EIA-930 hourly PJM fuel mix and Dominion-zone demand, Jan 2023 to Nov 2026 (33,912 hours; 4 hours truly missing, never filled); Open-Meteo historical forecasts for Ashburn. Carbon intensity = fuel mix x lifecycle emission factors (IPCC AR5; oil and "other" are our assumptions). Dominion alone has no public fuel mix, so the signal is **PJM-wide average emissions, not Loudoun-specific and not marginal**.
- **Model:** gradient boosting (scikit-learn HistGradientBoosting) predicting each target hour's intensity from history up to 18:00 the day before, the hours ahead, demand and weather. The job window is the lowest forecast 4-hour block within the allowed delay.
- **Split:** train 2023-2025, test 2026 (311 usable days, 3 dropped for missing hours). Never shuffled. Hyperparameters fixed; the "unsure" threshold was tuned on 2025 H2.
- **Baselines:** run immediately; persistence (repeat the latest same-hour values); hour-of-week climatology from training years; perfect foresight as a ceiling.
- Integrity details and the leakage audit are in `docs/DATA_AUDIT.md`; the go/no-go decision is in `DECISION.md`.

## Results (2026 test, gCO2/kWh of the chosen 4-hour window; lower is better)
| Allowed delay | Run now | Persistence | Hour-of-week climatology | Our model | Perfect foresight |
|---|---|---|---|---|---|
| 12 h | 353.4 | 329.8 | 342.9 | 330.5 | 325.5 |
| 24 h | 353.4 | 330.6 | 342.6 | 330.3 | 324.7 |
| 48 h | 353.4 | 330.6 | 337.2 | 323.6 | 315.8 |
| 72 h | 353.4 | 330.6 | 331.0 | 318.2 | 309.7 |

- The model beats climatology by about 12-14 g/kWh at every delay, with 95% intervals (7-day block bootstrap) all below zero, e.g. 24 h: -12.3 [-14.9, -9.9]. Savings versus running immediately: 6.5% at 12-24 h, 8.4% at 48 h, 9.9% at 72 h; perfect foresight would give 8-12%.
- **Barely any gain over persistence at short delays.** At 12 h and 24 h the model and "repeat yesterday" are statistically tied (24 h: -0.3 [-1.9, +1.3]; history-only model -1.1 [-2.2, -0.1]). The model clearly beats persistence only at 48-72 h (-7.0 and -12.4), partly because persistence cannot use extra slack.
- A history-only model (no weather or demand forecast) still beats climatology at every delay, so the result does not depend on those two inputs.
- Robust to emission factors: across five factor sets the model-minus-climatology gap stayed between -11.9 and -20.2 g/kWh.
- **The "unsure, run now" rule did not help**: no measurable change in cost on test. We keep it in the demo as a safety option and say so.
- **Where it fails:** the worst days (2026-02-20, 2026-01-09, 2026-01-10) had forecast error of 17-22 g/kWh versus 13.8 on average; two were back to back, and the model picked a window that turned out dirtier than the best one. Weekends are weak (model beats climatology by just 1.1 g/kWh at 24 h vs 16.7 on weekdays). On 6-8% of days the chosen window is dirtier than running immediately.
- Total headroom is small (8-12%) because PJM average intensity is fairly flat.

## What we'd do next
1. Use PJM marginal emission rates (needs a PJM Data Miner account), which better reflect what a shifted job actually changes.
2. Use real day-ahead forecasts instead of archive weather, and test on a second year.

## Sources
See `CREDITS.md`.
