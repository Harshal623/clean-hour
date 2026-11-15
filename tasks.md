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
- [ ] A1 Load 5 grids (src/grids.py)
- [ ] A2 Multi-grid evaluation: model vs persistence vs hour-of-week climatology vs perfect foresight; 95% CIs; GB also vs NESO's own forecast (src/multigrid.py -> results/multigrid_summary.csv, results/test_predictions_all.csv.gz)
- [ ] A3 Failure analysis per grid + emission-factor sensitivity
- [ ] A4 Household impact numbers (kg CO2 per year for an EV / dishwasher) with honest ranges -> results/household_impact.csv

## Person B (teammate's Claude): product + writing
Owns: app/, README.md, CREDITS.md, docs/VIDEO_SCRIPT.md, submission/, notebooks/
- [ ] B1 Rebuild app/app.py as a simple household app: pick your region, pick an appliance (EV 4h, dishwasher 2h, laundry 2h, water heater 3h), pick how long it can wait (tonight / within a day / within 3 days), pick a day. Output a big plain-English answer, a green-to-red hourly colour bar, and "you save about X% / Y g CO2". Reads results/test_predictions_all.csv.gz (columns: grid, day, j, y, pred, clim, persist). No jargon on the main screen; honest note in a collapsed section.
- [ ] B2 Rewrite README.md in the Veritas template for the new global/household framing (numbers come from results/multigrid_summary.csv once A2 lands; until then leave TODO markers, never invent numbers)
- [ ] B3 Update CREDITS.md (add Energy-Charts, NESO Carbon Intensity API, EIA CISO/ERCOT) and submission/FORM_ANSWERS.md (title, pitch, what we added)
- [ ] B4 Notebook: add a short multi-grid section once A2 lands, execute it, commit with outputs
- [ ] B5 Record the 2-minute video using docs/VIDEO_SCRIPT.md (human step)

## Shared / human-only
- [ ] S1 Everyone: confirm names, school, emails on the form (Harshal Mahadik, Aarush Gutha, Sidharth Mantri, TJHSST; emails still needed)
- [ ] S2 Run the notebook in Colab once (needs a Google login)
- [ ] S3 Open every link in incognito, then submit the form (one person submits)

## Requests (add a line: who -> who: what)
- 

## Notes
- Data contract for the app: `results/test_predictions_all.csv.gz` will have columns `grid` (pjm/ciso/erco/de/gb), `day` (local date of job release), `j` (hours after local midnight, 0..75), `y` (actual gCO2/kWh), `pred` (model forecast), `clim` (hour-of-week average), `persist` (repeat latest same-hour values). Until A2 lands, B can develop against `results/test_predictions.csv.gz` (Virginia only, same columns without `grid`).
- Signal caveat that must stay in all text: average emissions of the whole grid, not marginal and not specific to one town.
