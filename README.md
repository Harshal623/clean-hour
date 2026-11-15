# Clean-Hour: when is electricity cleanest? A tool for households in five countries

**Track:** Climate
**Team:** Harshal Mahadik, Aarush Gutha, Sidharth Mantri (TJHSST)
**Demo:** `python app/app.py` (simple web app). **Notebook with outputs:** `notebooks/loudoun_carbon_scheduler.ipynb` (Virginia deep dive; the multi-grid results come from `src/multigrid.py`).

## The problem
Electricity is not equally clean all day. In California the grid is cleanest at midday when solar peaks; in Britain it depends on the wind; in Texas and Germany it swings with sun, wind and gas. A person who charges an electric car, runs the dishwasher or does laundry at midnight often uses much dirtier power than if they waited a few hours, but nobody tells them when. Millions of homes, and businesses with flexible jobs (including Loudoun County's data centers), could shift use for free. We ask: how much CO2 does shifting save in five very different grids, and where does a machine-learning forecast actually beat simple rules like "run at midday"?

## What we built
- **Who/when:** an ordinary household in the evening, deciding when to start an appliance tomorrow, or within three days.
- **In:** their region (California, Texas, Virginia/Mid-Atlantic, Germany, Great Britain), the appliance (car 4 h, dishwasher 2 h, laundry 3 h, water heater 3 h), and how long it can wait (12 h, 24 h, 3 days).
- **Out:** one plain-English answer ("Start Friday at 2 PM, about 44% cleaner than starting at midnight"), a green-to-red colour strip of the coming hours, and a hindsight check of what really happened that day.
- **Under the hood:** a gradient-boosting forecast of the grid's hourly carbon intensity (grams of CO2 per kWh), made at 18:00 the evening before from the last week of data, demand forecasts (where public) and local weather forecasts.

## What we added
Our own idea (not one of the three suggested projects). Own user: ordinary households, not just experts. Own data: five grids on three continents from four public sources. Own question: **where does an ML forecast beat simple rules, and how much longer must you be able to wait before it matters?** We also run a first deep dive on one data-center cluster (Loudoun County, Virginia; see `DECISION.md`).

## How it works
- **Data (public, no personal data), Jan 2023 to Nov 2026:** EIA-930 hourly fuel mix for PJM (Virginia), California (CISO) and Texas (ERCOT); Energy-Charts (Fraunhofer ISE) for Germany; NESO Carbon Intensity API for Great Britain; Open-Meteo historical weather forecasts for each region. Carbon intensity = fuel mix x lifecycle emission factors (IPCC AR5; oil and "other" fuels are our assumptions). Great Britain uses NESO's official published values.
- **Split:** train 2023-2025, test every day of 2026 (311-314 days per grid). Never shuffled. Test days with a missing hour are dropped; missing hours are never filled.
- **Model:** gradient boosting (scikit-learn) predicting the change from the recent same-hour average. Our first version predicted the level directly; it was worse than persistence in California (hourly error 44.1 vs 34.9 g/kWh) because California's grid keeps getting cleaner year over year. Predicting the change fixed that (34.6). That is our one measured model improvement; first-version results are kept in `results/multigrid_summary_direct.csv`.
- **Baselines:** start at midnight; persistence ("repeat the latest same-hour values"); hour-of-week average from training years; perfect hindsight as a ceiling. 95% intervals use a 7-day block bootstrap.
- Data-integrity and leakage notes: `docs/DATA_AUDIT.md`.

## Results (test = all of 2026; 4-hour job; savings are versus starting at midnight)
% cleaner than starting at midnight, job can wait 24 hours:

| Region | Our advice | Simple "average week" rule | Perfect hindsight | Model minus simple rule (g/kWh, 95% interval) |
|---|---|---|---|---|
| California | 54.7% | 51.7% | 55.6% | -6.6 [-8.2, -4.3] |
| Texas | 29.7% | 29.3% | 32.0% | -1.3 [-3.3, +0.6] |
| Virginia | 6.9% | 3.0% | 8.1% | -13.5 [-15.9, -11.4] |
| Germany | 46.5% | 46.4% | 48.8% | -0.5 [-3.9, +2.1] |
| Great Britain | 28.8% | 3.8% | 35.1% | -29.9 [-36.2, -24.3] |

If the job can wait 3 days: our advice 59.0 / 34.8 / 10.0 / 52.1 / 41.2% (California / Texas / Virginia / Germany / Britain) versus the simple rule 52.8 / 30.5 / 6.3 / 48.4 / 12.0%. The model beats the simple rule in all five grids, with intervals below zero (-13 to -35 g/kWh).

What this says, honestly:
- **Shifting helps everywhere**, a lot in solar-rich grids (California, Germany) because midnight is when power is dirtiest.
- **In the sunny, gas-heavy grids, a simple "run at midday" rule is almost as good as machine learning for same-day shifting.** In Texas and Germany the model is statistically tied with the simple rule at 24 hours. The forecast matters more the longer you can wait.
- **In wind-driven Great Britain the forecast matters at every delay** (about 30 g/kWh better than the simple rule at 24 h). But **NESO's own official forecast beats ours** by about 4 to 6 g/kWh (95% intervals above zero), so we do not claim to beat the professionals.
- **Against "repeat the latest values" (persistence)** the model is close at 24 hours (within 1.5 g/kWh in Virginia, California and Texas; 4.8 better in Germany and 7.8 in Britain) and wins clearly at 3 days.
- Hourly forecast error, model vs persistence (g/kWh): Virginia 14.2 vs 21.4, California 34.6 vs 34.9 (a tie), Texas 39.8 vs 55.0, Germany 59.7 vs 90.1, Britain 29.3 vs 46.9.
- **Where it fails:** the worst day in each grid was far off the best possible choice: Texas 2026-02-13 and 02-14 (134 and 111 g/kWh worse than the best window), Germany 2026-01-10 (117), Britain 2026-03-05 (87), Virginia 2026-02-20 (43), California 2026-10-11 (21). On 15% of days in Britain and 8% in Virginia the advice was worse than simply starting at midnight; in California never. Failures cluster in time, around sudden shifts in the generation mix after the evening forecast.
- **Household impact (24 h of flexibility; we assume 3,000 kWh a year for an electric car):** about 73 kg CO2 a year in Virginia, 104 Britain, 301 Texas, 361 California, 508 Germany (95% ranges in `results/household_impact.csv`). Laundry plus dishwasher (assumed 400 kWh a year) saves roughly one-seventh of that.
- **Limits:** this is the **average** carbon intensity of the whole regional grid, not marginal emissions and not your own electricity company. The baseline is midnight, which is deliberately naive. The demo replays 2026 days; a live version needs live grid feeds.

## What we'd do next
1. Run it live (UK and German APIs publish forecasts) and add marginal-emission rates.
2. Add more grids, especially in countries with fast-growing demand, and test a second year.

## Deep dive: Loudoun County data centers
The same method applied to one cluster (PJM grid, 4-hour AI job): see `DECISION.md` and `docs/DATA_AUDIT.md`. PJM is the flattest of our grids (hourly spread about 34 g/kWh vs 60 to 124 elsewhere), so savings there are the smallest (6.9% at 24 h, 10.0% at 3 days).

## Sources
See `CREDITS.md`.
