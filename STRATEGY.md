# AI + Climate strategy (Veritas AI Hackathon 2026)

Rubric used: Technical quality / Impact / Creativity / Clarity. Track asks for ONE place, time-split test (never shuffled), a simple-baseline comparison, and a named decision + decision-maker. Suggested projects (solar, PM2.5, EuroSAT) will be submitted by many teams; extra credit comes from our own user, data or question.

## Phase 1: 28 ideas (pitch | user | decision | data | model)
Measure
1. Data-center land-change tracker | Loudoun planning staff | which parcels to review | Sentinel-2 via Planetary Computer | segmentation/classifier
2. Tree-canopy loss in Ashburn | county arborist | where to enforce/replant | NLCD canopy + Sentinel-2 | change detection
3. Urban-heat map of Loudoun schools | facilities director | which school gets shade first | Landsat LST + NLCD | regression
4. Farmland-to-development conversion | land trust | which farms to protect | NLCD/Sentinel-2 | classifier
5. Cheap-sensor smoke correction | school nurse | trust PurpleAir or not | EPA smoke set (PurpleAir API needs key) | regression
6. Climate TRACE emitter map (Virginia) | state energy office | where to audit | Climate TRACE | clustering
7. Cafeteria tray CO2 | school lunch staff | menu swap | Food-101 + LCA tables | CNN
8. Greenwashing claim detector | consumer | skip a product | text | NLP
9. Methane plumes (Sentinel-5P) | regulator | inspect site | SRON | CNN (too heavy)
Predict
10. **Carbon-aware scheduler for Loudoun data centers** | data-center ops lead | when to run flexible AI jobs | EIA-930 PJM + Open-Meteo | GBM
11. Next-day solar (Pune/Loudoun) | homeowner | charge battery | NASA POWER | GBM (done earlier, brief seed)
12. Next-day PM2.5 for Loudoun | coach | hold practice | OpenAQ/EPA AQS | GBM
13. Old Town Alexandria flood call | city ops | close streets | NOAA tides | residual model
14. WBGT heat call for fields | athletic director | modify practice | Open-Meteo | quantile GBM
15. Dominion-zone peak-load alert | ops | pre-cool / shed | EIA DOM demand | GBM
16. Stormwater flood by street | public works | pre-position pumps | USGS gauges + NOAA rain | GBM
17. Potomac-region ozone alert | health dept | issue alert | EPA AQS | GBM
18. Data-center cooling-water use forecast | utility | plan withdrawals | weather + proxy | regression
19. Building energy forecast for a school | facilities | HVAC schedule | public school data (hard to find) | GBM
20. Wind/solar curtailment risk PJM | grid analyst | storage dispatch | EIA-930 | GBM
Reduce
21. Cleanest-hour EV charging for a school bus depot | fleet manager | charge window | same as #10 | GBM
22. Pre-cooling schedule using forecast | facilities | start HVAC early | weather + demand | rule+GBM
23. Where to plant trees for max cooling | county | planting list | #3 | ranking
24. Stormwater green-infrastructure siting | planner | where to build | NLCD+DEM | classifier
25. Heat-wave cooling-center siting | health dept | location | census+LST | optimization
26. Rooftop-solar potential from imagery | HOA | which roofs | aerial | segmentation
27. Demand-response bidder for data centers | ops | when to shed | EIA + weather | GBM
28. Meal carbon swap | student | choose lunch | #7 | classifier

## Phase 2: scoring (1-5; a novelty, b user+decision, c data in <30 min, d feasible 30h, e eval quality, f demo, g rubric fit)
| Idea | a | b | c | d | e | f | g | Total /35 |
|---|---|---|---|---|---|---|---|---|
| 10 Carbon-aware scheduler | 5 | 5 | 5 | 5 | 4 | 4 | 5 | **33** |
| 13 Old Town flood call | 4 | 5 | 5 | 5 | 5 | 4 | 5 | **33** |
| 14 WBGT practice heat call | 3 | 5 | 5 | 5 | 4 | 4 | 4 | 30 |
| 12 Loudoun PM2.5 | 2 | 5 | 4 | 5 | 4 | 4 | 4 | 28 |
| 1 Data-center land change | 5 | 3 | 3 | 2 | 2 | 5 | 3 | 23 |

Killed: 5 (PurpleAir API key), 9 (too heavy), 19 (no public data), 7/8/26 (weak baseline, off-brief for forecasting rigor). Meteomatics: killed (401, needs paid/trial account). Earthdata: killed as primary (login needed to download; search is open).

## Phase 3: data verification (actually tested)
| Source | Result |
|---|---|
| EIA-930 hourly PJM fuel mix (6-month CSVs, no key) | WORKS. 33,936 hourly rows, 2023-01-01 to 2026-11-15, ~0.1% missing, `unknown` fuel 100% empty. Column names changed in mid-2024 (hydro/solar/wind split, storage added); loader handles it. |
| EIA-930 SUBREGION (Dominion zone demand) | WORKS, 0.7% missing. |
| Dominion-only fuel mix | DOES NOT EXIST in EIA-930 (Dominion is a zone inside PJM). So "Dominion carbon intensity" is really PJM-wide intensity. PJM Data Miner has an API but needs an account; PJM returned 404 without a key. Say this plainly in the write-up. |
| EIA API v2 | Needs free key (empty response without it). Not used. |
| Open-Meteo historical FORECAST API (Ashburn) | WORKS, no key, 2023-01-01 onward, 0% missing. Using forecast archive (not actuals) avoids weather leakage. |
| Open-Meteo air quality | Loads, but values are model estimates, not measurements. |
| NOAA CO-OPS tides, station 8594900 (Washington, DC) | WORKS: 6-min water level and hourly NOAA predictions, no key. Nearest gauge to Old Town. |
| Microsoft Planetary Computer STAC | Catalog open (HTTP 200). Not tested for image download. |
| Meteomatics | HTTP 401 (paid/trial). Dropped. |
| Loudoun GeoHub | Site reachable, no dataset tested. |
Licensing: EIA and NOAA are US government public data; Open-Meteo is CC BY 4.0 (non-commercial free tier). Cite all.

## Phase 4: pick
WINNER: #10 Carbon-aware scheduler. BACKUP: #13 Old Town flood call (identical score; NOAA predictions are a genuinely hard baseline; data already verified).
Why: one place (Loudoun, the world's densest data-center market), one decision-maker (a data-center operations lead), a concrete decision (which 4-hour window in tomorrow), very few teams will pick it.
Strongest argument AGAINST (and it is real, from our first run):
- The decision gain is small. Even a perfect oracle saves only 8.0% vs running at midnight, because PJM-wide average intensity is fairly flat (mean 346, std 34 g/kWh).
- The model cuts hourly error 28% vs persistence (12.5 vs 17.3 g/kWh), but when turned into the scheduling decision it saves only 1.0 g/kWh more than persistence and is better on just 39% of days. That is close to a tie.
- Average intensity is not marginal intensity; marginal rates (what a shifted job actually changes) need a PJM account.
So the pitch must NOT be "model saves X tons". The honest "own question" is: how much scheduling flexibility does an operator need before a forecast beats simple rules? Add (a) flexibility sweep (job can slip 0/12/24/48/72 h), (b) season/weekday breakdown, (c) sensitivity to emission-factor choices, (d) a "don't bother, run now" option when forecast spread is small. If the sweep shows no model advantage anywhere, switch to the flood backup right after the sweep (budget about 2 h for it).

### Build spec
- User and moment: data-center ops lead at 18:00 deciding when tomorrow's 4-hour flexible batch (AI training chunk) runs.
- Input -> output: last 24 h/7 d carbon intensity, PJM day-ahead demand forecast, Loudoun weather forecast -> predicted hourly intensity for tomorrow, recommended start hour, expected gCO2/kWh saved vs run-now, confidence ("unsure, run default").
- Data: EIA-930 PJM + Dominion-zone demand; Open-Meteo historical forecasts. 2023-01 to 2026-11. Train 2023-01..2025-06, validate 2025-07..2025-12 (tuning), TEST 2026-01..2026-11 (315 days, touched once). Never shuffled.
- Baselines: persistence (same hour yesterday), same hour last week, month x hour climatology, "run 2-6am" rule, oracle as upper bound.
- Metrics: hourly MAE; mean gCO2/kWh of the chosen window; share of oracle saving captured; share of days better than persistence. Chosen because the decision is the window, not the hourly value.
- Model: HistGradientBoosting first (done); improvement = quantile/spread model for the "unsure" option and flexibility sweep.
- Own thing: own user (Loudoun data-center operator), own data (Dominion-zone demand + forecast-archive weather), own question (how much flexibility does a forecast need).
- Failure analysis: worst days (cold snaps, PJM peaks, high wind days), by season, weekday/weekend, and whether errors cluster when gas/coal switch at the margin.
- Demo (60 s): Gradio page: pick a date -> forecast curve vs actual, highlighted best window, saving vs naive, a baseline bar chart, one failure day.
- Hours: H0-2 data loaded (DONE), H2-8 baseline + model (DONE, below), H8-14 flexibility sweep + seasons + sensitivity, H14-18 failure analysis, H18-22 Gradio + Colab notebook with outputs, H22-26 write-up + video, H26-28 submit (>=2 h before 11:59 PM ET Nov 15), buffer rest.
- Submission checklist: public GitHub or Colab (outputs saved), write-up in the Veritas template, credits list, optional 2-min video, track = Climate, all team names/emails exact, open every link in incognito, state AI tools used (Claude Code).

## Results so far (TEST 2026-01-01 .. 2026-11-11, 315 days, exactly as printed)
Hourly MAE g/kWh: persistence 17.31; last week 25.86; climatology 23.38; gradient boosting 12.48.
Window intensity g/kWh: midnight 353.09; 2-6am 348.87; persistence 330.24; climatology 339.52; model 329.22; oracle 324.89. Model captures 85% of the oracle saving but persistence already captures about 82%.

## Sources / credits (log)
- EIA Hourly Electric Grid Monitor (EIA-930): https://www.eia.gov/electricity/gridmonitor/
- Open-Meteo Historical Forecast API: https://open-meteo.com/en/docs/historical-forecast-api
- Emission factors: IPCC AR5 WG3 Annex III (lifecycle medians); `other` = 230 is our assumption (sensitivity check to do)
- scikit-learn HistGradientBoostingRegressor; pandas; numpy
- NOAA CO-OPS (backup only, verified not used): https://api.tidesandcurrents.noaa.gov/
- AI tool: Claude Code (Anthropic) for ideation and code
