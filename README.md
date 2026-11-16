# Clean-Hour: cleaner hours for Northern Virginia homes and Loudoun's data centers (and does it travel?)

**Track:** Climate
**Team:** Harshal Mahadik, Aarush Gutha, Sidharth Mantri (TJHSST)
**Our place:** Northern Virginia on the PJM grid, home of Loudoun County's data-center corridor.
**Run it in Google Colab (about 2 minutes, no downloads):** [Open in Colab](https://colab.research.google.com/github/Harshal623/clean-hour/blob/main/notebooks/clean_hour_colab.ipynb) (`notebooks/clean_hour_colab.ipynb`).
**Demo:** `python app/app.py` (simple web app; a Replay tab tested on 2026 days and a Live tab for Great Britain (NESO's official carbon forecast) and Germany (renewable-share forecast)). **Notebook with outputs:** `notebooks/clean_hour.ipynb` (Virginia deep dive: `notebooks/virginia_deep_dive.ipynb`).

> A forecast that predicts carbon better is not automatically better at choosing the cleanest hours. In Virginia, training a second stage to rank hours captured 91% of the best possible saving against 85% for the plain model; that gain did not transfer to California, Texas, Germany or Britain, and we report where it holds and where it does not.

## The problem
Electricity is not equally clean all day. The power plants that run at 7 PM are different from the ones that run at 2 AM, so the same appliance can cause very different CO2 depending on when it starts. Our home region, Northern Virginia, hosts one of the world's biggest concentrations of data centers, which run flexible batch jobs (AI training chunks, backups, video processing) that could start at almost any hour. Families have the same choice with an electric car, a dishwasher or laundry. Nobody tells them when the grid is cleanest. We built a forecast and a simple tool for that choice in our own region, then tested whether the same method works on four other grids.

## What we built
- **Who/when:** a Northern Virginia household (or a data-center operations lead) in the evening, deciding when to start something tomorrow, or within three days.
- **In:** the appliance or job length, how long it can wait (12 h, 24 h, 3 days), and the region (Virginia first; California, Texas, Germany and Britain also work).
- **Out:** one plain-English answer ("Start Friday at 2 PM, about 44% cleaner than starting at midnight"), a green-to-red strip of the coming hours, and a hindsight check of what really happened.
- **Under the hood:** a gradient-boosting forecast of the grid's hourly carbon intensity (grams of CO2 per kWh), made at 18:00 the evening before from the last week of grid data, demand forecasts and local weather forecasts.

## What we added
Our own idea (not one of the three suggested projects). Own place and user: Northern Virginia homes and the Loudoun data-center corridor. Own data: PJM fuel mix plus Dominion-zone demand and a forecast-weather archive for Ashburn. Own questions: (1) how long must a job be able to wait before a forecast beats simple rules, (2) is a better hourly forecast really a better choice of hours, and (3) does it hold up in a new situation, meaning four other grids on two other continents.

## How it works
- **Data (public, no personal data), Jan 2023 to Nov 2026:** EIA-930 hourly fuel mix for PJM (our Virginia grid), California and Texas; Energy-Charts (Fraunhofer ISE) for Germany; NESO Carbon Intensity API for Great Britain; Open-Meteo historical weather forecasts. Carbon intensity = fuel mix x lifecycle emission factors (IPCC AR5; oil and "other" fuels are our assumptions). PJM serves Virginia but is a multi-state grid, and Dominion alone has no public fuel mix, so our signal is **PJM-wide average emissions, not Loudoun-specific and not marginal**.
- **Split:** train 2023-2025, test every day of 2026 (311 Virginia days; 3 dropped for missing hours, never filled). Never shuffled.
- **Model:** gradient boosting (scikit-learn) predicting the change from the recent same-hour average. The demo replays the saved 2026 forecasts in `results/test_predictions_all.csv.gz`; `results/final_model.joblib` is the trained model artifact kept for a future live version, not what the app runs. Our first version predicted the level directly and was worse than "repeat yesterday" in California (hourly error 44.1 vs 34.9 g/kWh); predicting the change fixed it (34.6). Both are kept (`results/multigrid_summary_direct.csv`).
- **Tuning tried and rejected:** per-grid hyperparameters, extra history and fuel-mix features, a validation-fit blend and quantile loss were chosen on 2025 H2 validation and scored once on 2026; none beat the production model with an interval below zero at both 24 h and 72 h (`docs/experiments/model-variants.md`).
- **Baselines:** start at midnight; persistence ("repeat the latest same-hour values"); hour-of-week average from training years; perfect hindsight as a ceiling. Intervals are 95% from a 7-day block bootstrap.
- Integrity and leakage notes: `docs/DATA_AUDIT.md`.

## Results in Northern Virginia (PJM)
Test = all of 2026, a 4-hour job decided at 18:00 the evening before. Grams of CO2 per kWh of the chosen window (lower is better):

| Job can wait | Start at midnight | Repeat yesterday | Hour-of-week average | Our model | Perfect hindsight |
|---|---|---|---|---|---|
| 12 h | 353.4 | 329.8 | 342.9 | 329.2 | 325.5 |
| 24 h | 353.4 | 330.6 | 342.6 | 329.1 | 324.7 |
| 48 h | 353.4 | 330.6 | 337.2 | 323.1 | 315.8 |
| 72 h | 353.4 | 330.6 | 331.0 | 318.1 | 309.7 |

- Shifting saves 6.9% at 24 hours and 10.0% at 3 days versus midnight; perfect hindsight would save 8.1% and 12.4%. Virginia's grid is the flattest of our five (hourly spread about 34 g/kWh vs 60 to 124 elsewhere), so the headroom is modest, and we say so.
- The model beats the hour-of-week average by about 13-14 g/kWh at every delay (24 h: -13.5 [-15.9, -11.4]).
- Against "repeat yesterday" it is a near tie when the wait is short (12 h: -0.6 [-1.8, +0.5]; 24 h: -1.5 [-2.8, -0.2]) and clearly better at 3 days (-12.5 [-15.3, -9.5]).
- **A better forecast is not automatically a better choice** (Sidharth's analysis, `results/experiments/`, on the first Virginia model whose level was predicted directly). That model cut hourly error by 35% versus "repeat yesterday" (13.8 vs 21.5 g/kWh) yet chose hours no better. A second-stage model trained to rank hours rather than predict levels captured 87-89% of the perfect saving instead of 78-81%, and beat the first model by about 2.7 g/kWh at every delay (95% intervals below zero). Scored on May-Nov 2026 only, because Jan-Apr 2026 was used to train it. With our final model the Virginia gain is smaller (91% vs 85% of the perfect saving at 24 h; -1.8 g/kWh [-2.5, -1.2]), and **it did not transfer**: in California, Texas, Germany and Britain the first model already captured 85-98% of the perfect saving and the stacker was tied or slightly worse (`docs/experiments/decision-focused-grids.md`). So the effect shows up where the daily pattern is weak (Virginia's flat grid), not everywhere.
- **Households:** 24 hours of flexibility saves about 73 kg CO2 a year for an electric car (assuming 3,000 kWh a year; 95% range 64-82) versus starting at midnight. Against a more realistic 19:00 plug-in (the dirtiest hour of the day in 2026), a dishwasher that can wait a day saves about 10% of its emissions and an EV that must finish by 7 AM about 5% (`results/experiments/household_shift.csv`).
- **Data centers (arithmetic, not a measurement):** a flexible 10 MW batch load running 4 hours a day, shifted with 24 hours of slack, avoids about 24 g/kWh x 40 MWh = 1 tonne CO2 a day, roughly 355 tonnes a year on this grid.
- **Who has the flexibility:** batch AI training chunks, backups and video processing could wait 12-24 hours; latency-sensitive services cannot (`DECISION.md`).
- **Where it fails:** worst days were 2026-02-20 (43 g/kWh worse than the best window), 01-09 (39) and 01-10 (38); two were back to back, after shifts in the generation mix the evening forecast could not see. On about 8% of days the advice was worse than starting at midnight.

## Does it travel? Four other grids (a transfer test)
Same method, same split, % cleaner than starting at midnight with 24 hours of flexibility (model vs the simple hour-of-week rule vs perfect hindsight): California 54.7 / 51.7 / 55.6; Texas 29.7 / 29.3 / 32.0; Germany 46.5 / 46.4 / 48.8; Great Britain 28.8 / 3.8 / 35.1. With 3 days of slack the model beats the simple rule in all five grids, including Virginia (-13 to -35 g/kWh). In sunny California, Germany and Texas a plain "run at midday" rule is almost as good for same-day shifting; in wind-driven Britain the forecast matters at every delay, but NESO's own official forecast beats ours by 4 to 6 g/kWh. Under five different emission-factor sets (results/ef_sensitivity_multigrid.csv; Britain excluded because NESO supplies its own intensity) the 3-day advantage over the simple rule stays significant in all four fuel-mix grids, and the 24-hour picture does not change (California and Virginia beat the rule; Texas and Germany tie). Figure: `results/multigrid_savings.png`; per-grid failure days: `results/failures_by_grid.png`; table: `results/multigrid_summary.csv`.

## Related work (what is and is not new)
Shifting flexible computing to cleaner hours is well studied: Wiesner et al., "Let's Wait Awhile" (Middleware 2021, arXiv 2110.13234) analysed Germany, Great Britain, France and California in 2020; LiteCast (Joseph, Savadi and Souza, arXiv 2511.06187) reports across 50 regions that preserving the ranking of hours matters more than forecast error. Google's production system (Radovanovic et al., arXiv 2106.11750) delays flexible workloads using day-ahead forecasts, and a University of Alberta paper reports that higher forecast accuracy does not necessarily mean lower emissions (Sohrabbeig, Ardakanian and Musilek). We do not claim these ideas as new. What we add is a held-out 2026 test with simple baselines and honest intervals, a household framing, a Virginia/Loudoun focus, and a boundary condition: the benefit of ranking-focused training appeared only in the flattest grid.

## Robustness
Training on 2023-2024 and testing on all of 2025 gives the same pattern (the model beats the simple rule in all five grids with 3 days of slack and ties it in Texas and Germany at 24 h; `docs/experiments/year-robustness.md`), but absolute savings differ by year (California 29.5% in 2025 vs 54.7% in 2026, Virginia 4.3% vs 6.9%), so read the percentages as one-year measurements.

## Limits
Average, not marginal, emissions of a whole regional grid. A coarse estimate of marginal intensity (net-load regression fitted on 2023-2025; `docs/experiments/estimated-marginal.md`) agrees with our advice in Virginia and California (68.8% and 89.8% of 2026 days) but not in Texas or Germany, where it suggests the benefit of shifting at the margin could be smaller or absent; that estimate is a proxy and unvalidated. The savings baseline (midnight) is deliberately naive. The demo replays 2026 days; a live version needs live grid feeds. No user test has been done yet.

## What we'd do next
1. Use PJM marginal emission rates and live forecasts, and test a second year.
2. Try it with one real family and one data-center operator, and write down what confuses them.

## Sources
See `CREDITS.md`.
