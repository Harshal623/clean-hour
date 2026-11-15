# Veritas AI Hackathon 2026 submission form: ready-to-paste answers

Form: https://airtable.com/appypCyHN77hElIcS/shrXA5VBFdugmoXl6   Deadline: Sun Nov 15, 11:59 PM ET (submit a first version 2+ hours earlier; resubmit freely).

Project Title
Clean-Hour: Cleaner Hours for Northern Virginia Homes and Loudoun Data Centers

One-Sentence Pitch
Clean-Hour forecasts when Northern Virginia's power grid is cleanest so families and Loudoun's data centers can start flexible jobs at cleaner hours, and we test honestly where a forecast beats simple rules and whether the method works on four other grids.

Track
Climate

Code Link
https://github.com/Harshal623/clean-hour

Write-up Link
https://github.com/Harshal623/clean-hour/blob/main/submission/WRITEUP.md (one page, Veritas template; full detail in README.md)

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
Our own idea, not a suggested project. Own place and user: Northern Virginia homes and the Loudoun data-center corridor (PJM grid). Own data: PJM fuel mix, Dominion-zone demand and a forecast-weather archive for Ashburn. Own questions: how long must a job be able to wait before a forecast beats simple rules; is a better hourly forecast really a better choice of hours (a second-stage model trained to rank hours captured 91% of the best possible saving vs 85% for our final model in Virginia, and we show it does not transfer to the other four grids); and does the method transfer to California, Texas, Germany and Great Britain? We also trained a Transformer in PyTorch on a Colab GPU that sees all 76 future hours at once: in Virginia it captured 89% of the best possible saving at 24 h versus 84% for gradient boosting, and by our pre-set rule it is a tie across the five grids. We report four baselines (start at midnight, persistence, hour-of-week average, perfect hindsight), 95% block-bootstrap intervals, household and data-center impact with stated assumptions, failure days, a model bug we found (first version worse than persistence in California), and a leakage audit. Weak results are reported: for short waits the model is nearly tied with "repeat yesterday", Britain's official NESO forecast beats ours, and the signal is the PJM-wide average, not Loudoun-specific or marginal.

Credits
- EIA Hourly Electric Grid Monitor (EIA-930), PJM, CISO and ERCOT fuel mix and demand: https://www.eia.gov/electricity/gridmonitor/
- Energy-Charts (Fraunhofer ISE) public power API, Germany: https://api.energy-charts.info/
- NESO Carbon Intensity API, Great Britain: https://carbonintensity.org.uk/
- Open-Meteo Historical Forecast API (CC BY 4.0): https://open-meteo.com/en/docs/historical-forecast-api
- IPCC AR5 WG3 Annex III lifecycle emission factors: https://www.ipcc.ch/report/ar5/wg3/ (oil 650 and other 230 gCO2e/kWh are our own assumptions)
- NOAA CO-OPS station 8594900 (feasibility check of a backup idea only): https://tidesandcurrents.noaa.gov/
- scikit-learn: https://scikit-learn.org/ ; pandas; NumPy; Matplotlib; joblib; Gradio: https://www.gradio.app/
- PyTorch: https://pytorch.org/ (Transformer, trained on a free Google Colab T4 GPU); ListNet ranking-loss idea from Cao et al., ICML 2007
- No pretrained models.
- AI tools: Claude Code and Claude chat (Anthropic), for brainstorming, code and drafting; Perplexity, for code review and related-work research. Team reviewed everything.

## Checklist before hitting Submit
- [ ] Open the repo, README and video links in a private/incognito window; confirm they load without signing in.
- [ ] README "Team:" line filled in; every teammate's full name, school and email spelled exactly as for certificates.
- [ ] Notebooks show outputs on GitHub: `notebooks/clean_hour.ipynb` and `src/experiments/torch_transformer/colab.ipynb` (the PyTorch GPU run).
- [ ] Rules checkboxes, check each only if TRUE:
  - [ ] All work done between 12:00 AM ET Nov 14 and 11:59 PM ET Nov 15 and does not extend an earlier project (the repo history starts Nov 14; the archived solar practice project is not part of this submission).
  - [ ] AI/ML does the main job (the gradient boosting and Transformer forecasts drive the decision).
  - [ ] Every dataset, model, library and AI tool is credited and the team can explain every part.
  - [ ] Only public data; no personal information.
  - [ ] Results are the ones actually obtained (numbers in README come from the executed notebook).
  - [ ] Everyone listed contributed.
