# Veritas AI Hackathon 2026 submission form: ready-to-paste answers

Form: https://airtable.com/appypCyHN77hElIcS/shrXA5VBFdugmoXl6   Deadline: Sun Nov 15, 11:59 PM ET (submit a first version 2+ hours earlier; resubmit freely).

Project Title
Clean-Hour: A Carbon-Aware Scheduler for Loudoun Data Centers

One-Sentence Pitch
We forecast the carbon intensity of the grid serving Loudoun's data centers and tell an operator when to run a flexible 4-hour AI job, and we test honestly where the forecast beats simple rules (it clearly does against hour-of-week averages, and only at 2-3 days of slack against "repeat yesterday").

Track
Climate

Code Link
https://github.com/Harshal623/loudoun-carbon-scheduler

Write-up Link
https://github.com/Harshal623/loudoun-carbon-scheduler/blob/main/README.md

Demo Video Link
<paste YouTube unlisted or Drive link after recording; script in docs/VIDEO_SCRIPT.md>

Building As
Team of 3

Your Full Name / School / Email (every teammate; one person submits for all)
- Harshal Mahadik, TJHSST, email: <ADD>
- Aarush Gutha, TJHSST, email: <ADD>
- Sidharth Mantri, TJHSST, email: <ADD>
(Confirm the exact spelling and school name as you want it on certificates. Emails were not provided, so type them on the form yourselves.)

New to AI?
<answer truthfully>

What we added beyond the suggested projects (paste in "Anything Else" or write-up field)
Our own idea, not a suggested project. Own user: a Loudoun data-center operations lead. Own data: Dominion-zone demand and a forecast-weather archive for Ashburn on top of EIA-930 PJM fuel mix. Own question: how much scheduling slack (12 to 72 hours) does a forecast need before it beats simple rules? We report baselines (run now, persistence, hour-of-week climatology, perfect foresight), 95% block-bootstrap intervals, season and weekday breakdowns, emission-factor sensitivity, a history-only ablation, and a data-integrity and leakage audit. Weak results are reported: the model is statistically tied with persistence at 12-24 h, the "unsure" rule gave no gain, and the signal is PJM-wide average emissions rather than Loudoun-specific or marginal.

Credits
- EIA Hourly Electric Grid Monitor (EIA-930), PJM fuel mix and Dominion zone demand: https://www.eia.gov/electricity/gridmonitor/
- Open-Meteo Historical Forecast API (CC BY 4.0): https://open-meteo.com/en/docs/historical-forecast-api
- IPCC AR5 WG3 Annex III lifecycle emission factors: https://www.ipcc.ch/report/ar5/wg3/ (oil 650 and other 230 gCO2e/kWh are our own assumptions)
- NOAA CO-OPS station 8594900 (feasibility check of a backup idea only): https://tidesandcurrents.noaa.gov/
- scikit-learn: https://scikit-learn.org/ ; pandas; NumPy; Matplotlib; joblib; Gradio: https://www.gradio.app/
- No pretrained models.
- AI tool: Claude Code (Anthropic), for brainstorming, code and drafting. Team reviewed everything.

## Checklist before hitting Submit
- [ ] Open the repo, README and video links in a private/incognito window; confirm they load without signing in.
- [ ] README "Team:" line filled in; every teammate's full name, school and email spelled exactly as for certificates.
- [ ] Notebook shows outputs on GitHub (it does; re-run `notebooks/loudoun_carbon_scheduler.ipynb` in Colab once to confirm it runs top to bottom).
- [ ] Rules checkboxes, check each only if TRUE:
  - [ ] All work done between 12:00 AM ET Nov 14 and 11:59 PM ET Nov 15 and does not extend an earlier project (the repo history starts Nov 14; the archived solar practice project is not part of this submission).
  - [ ] AI/ML does the main job (gradient boosting forecast drives the decision).
  - [ ] Every dataset, model, library and AI tool is credited and the team can explain every part.
  - [ ] Only public data; no personal information.
  - [ ] Results are the ones actually obtained (numbers in README come from the executed notebook).
  - [ ] Everyone listed contributed.
