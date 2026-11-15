# Team task board (two people, each using Claude)

Rules so we don't collide
1. `git pull --rebase` before you start, before every commit, and every ~30 minutes. Push small commits often (the history proves the work happened during the hackathon).
2. Each file has ONE owner (below). If you need a change in someone else's file, add a line under "Requests" instead of editing it.
3. Tick a task by changing `[ ]` to `[x]` and adding your initials. Commit tasks.md on its own.
4. Never commit big data (data/*.csv is git-ignored). Results CSVs/PNGs in results/ are fine.
5. Deadline: Sun Nov 15, 11:59 PM ET. Submit a first version by 9:30 PM ET.

## The project (new direction, see README once updated)
Clean-Hour: "When is electricity cleanest tomorrow?" A simple tool for ordinary households (charge the EV, run the dishwasher or laundry) in five grids on three continents: Virginia, California, Texas, Germany, Great Britain. Question we test: in which grids does an ML forecast actually beat simple rules, and how much CO2 does shifting save? The Loudoun data-center work becomes one case study (src/sweep.py, DECISION.md).

## Person A (Harshal's Claude): data + evaluation
Owns: src/grids.py, src/multigrid.py, src/sweep.py, src/final.py, results/, DECISION.md, docs/DATA_AUDIT.md
- [x] A1 Load 5 grids (src/grids.py) [HM-Claude]
- [x] A2 [HM-Claude] Multi-grid evaluation: model vs persistence vs hour-of-week climatology vs perfect foresight; 95% CIs; GB also vs NESO's own forecast (src/multigrid.py -> results/multigrid_summary.csv, results/test_predictions_all.csv.gz)
- [ ] A3 Failure analysis per grid (worst days are in multigrid_summary.csv column worst_days; add a figure) + emission-factor sensitivity for the 4 new grids
- [x] A4 [HM-Claude] Household impact numbers (kg CO2 per year for an EV / dishwasher) with honest ranges -> results/household_impact.csv

## Person B (teammate's Claude): product + writing
Owns: app/, README.md, CREDITS.md, docs/VIDEO_SCRIPT.md, submission/, notebooks/
- [x] B1 [done early by HM-Claude, new simple UI is in app/app.py; B may polish wording/design] Rebuild app/app.py as a simple household app: pick your region, pick an appliance (EV 4h, dishwasher 2h, laundry 2h, water heater 3h), pick how long it can wait (tonight / within a day / within 3 days), pick a day. Output a big plain-English answer, a green-to-red hourly colour bar, and "you save about X% / Y g CO2". Reads results/test_predictions_all.csv.gz (columns: grid, day, j, y, pred, clim, persist). No jargon on the main screen; honest note in a collapsed section.
- [x] B2 [done by HM-Claude, B please review wording and fix anything wrong] Rewrite README.md in the Veritas template for the new global/household framing (numbers come from results/multigrid_summary.csv once A2 lands; until then leave TODO markers, never invent numbers)
- [x] B3 [done by HM-Claude, B please review] Update CREDITS.md (add Energy-Charts, NESO Carbon Intensity API, EIA CISO/ERCOT) and submission/FORM_ANSWERS.md (title, pitch, what we added)
- [ ] B4 Notebook: add a short multi-grid section once A2 lands, execute it, commit with outputs
- [ ] B5 Record the 2-minute video using docs/VIDEO_SCRIPT.md (human step)

## Shared / human-only
- [ ] S1 Everyone: confirm names, school, emails on the form (Harshal Mahadik, Aarush Gutha, Sidharth Mantri, TJHSST; emails still needed)
- [ ] S2 Run the notebook in Colab once (needs a Google login)
- [ ] S3 Open every link in incognito, then submit the form (one person submits)

## Requests (add a line: who -> who: what)
- 

## Results landed (A2/A4), numbers B should use (full tables in results/multigrid_summary.csv and results/household_impact.csv)
Model = gradient boosting predicting the change from the recent same-hour average (we first tried predicting the level directly: results/multigrid_summary_direct.csv; California hourly error was 44.1 vs 34.9 persistence, the change-target version fixed it to 34.6). Test = all of 2026, train 2023-2025. % cleaner than starting at midnight, 4-hour job:
- 24h delay, model / simple hour-of-week rule / perfect hindsight: California 54.7/51.7/55.6; Texas 29.7/29.3/32.0; Virginia 6.9/3.0/8.1; Germany 46.5/46.4/48.8; Great Britain 28.8/3.8/35.1
- Honest story: shifting to cleaner hours helps everywhere; in sunny/gas grids (CA, TX, DE) a simple "run at midday" rule is nearly as good as the ML forecast for same-day shifting (model minus rule is within a few g/kWh, CI crosses 0 in TX and DE at 24h). With 3 days of slack the model beats the rule in all five grids (CIs below zero). In Great Britain (wind) the forecast matters at every delay, but NESO's own official forecast beats ours by about 4-6 g/kWh.
- Household EV (3,000 kWh/yr, assumption), 24h delay: roughly 73 kg CO2/yr Virginia, 104 GB, 301 Texas, 361 California, 508 Germany (95% ranges in the csv).
- Savings are vs starting at MIDNIGHT, a deliberately naive baseline; say so.

## Notes
- Data contract for the app: `results/test_predictions_all.csv.gz` will have columns `grid` (pjm/ciso/erco/de/gb), `day` (local date of job release), `j` (hours after local midnight, 0..75), `y` (actual gCO2/kWh), `pred` (model forecast), `clim` (hour-of-week average), `persist` (repeat latest same-hour values). Until A2 lands, B can develop against `results/test_predictions.csv.gz` (Virginia only, same columns without `grid`).
- Signal caveat that must stay in all text: average emissions of the whole grid, not marginal and not specific to one town.
