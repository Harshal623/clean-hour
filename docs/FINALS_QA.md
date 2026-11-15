# FINALS_QA: Nov 21, 11:00 AM ET

Finals are 70% of the final ranking: demo and clarity 30, technical depth 30, impact 20, Q&A 20. Rehearse more than you model.

## The 90-second live demo

Use only the Replay tab, which reads committed results and needs no internet: input, answer, hindsight check, one transfer grid. Keep the local video file open as a fallback if screen sharing dies. Narrate the decision, not the widgets.

## Ten questions, with answers that are already true of the repo

1. Why average emissions and not marginal? Marginal is the right quantity. WattTime is the standard source, and its historical and forecast MOER endpoints are subscriber-only; research access needs an approved noncommercial agreement with a six-month term, which we could not get inside 48 hours. Electricity Maps withdrew its marginal product in 2025 over concerns about how verifiable marginal signals are. So we used PJM-wide average intensity, said so on every page, and built a marginal proxy as a sensitivity test: the advice agrees on 68.8% of Virginia days and 89.8% of California days, but not in Texas or Germany, where the benefit could be smaller.
2. Is the gain real or noise? 95% intervals from a 7-day block bootstrap. Against the simple hour-of-week rule it is -13.5 [-15.9, -11.4] g/kWh at 24 h. Against repeat-yesterday it is small: -1.5 [-2.8, -0.2] at 24 h and a near tie at 12 h. We report both.
3. Who is this for? A family deciding at 18:00 the evening before whether to charge the car or run the dishwasher, and a Loudoun operator with a four-hour flexible batch job. One forecast, two users.
4. Where could leakage creep in? Every feature is available at 18:00 the evening before, the climatology uses 2023-2025 only, the abstention threshold was tuned on 2025 H2, and the test is 2026, touched once, with days with missing hours dropped and never filled. The ranking model trains on Jan-Apr 2026 and is scored May-Nov 2026; we say that in the README.
5. Why not use an existing API? For Britain we do: NESO's official forecast beats ours by 4-6 g/kWh and we print it. There is no public hourly carbon-intensity forecast for PJM, because EIA-930 is historical actuals and PJM's marginal data needs an account, so the forecast has to be built.
6. What is genuinely new? Training the model to rank hours instead of predicting levels: 87-89% of the perfect saving against 78-81% in Virginia. And the boundary condition: that gain disappeared in California, Texas, Germany and Britain, so it is a flat-grid effect rather than a general improvement. Most teams stop at mean absolute error; we show that error is not the decision.
7. Do products already do this? Yes, in other markets: WattTime marginal data sit behind Toyota and BMW charging features and Nest thermostats, over a billion devices. What is missing in Virginia is the evaluated, open version, and the question of whether forecast quality even changes the choice, which is what we tested.
8. Impact, honestly? 73 kg CO2 a year for an electric car, about 10% of a dishwasher's emissions, roughly a tonne a day for a 10 MW flexible batch. And on 8% of days our advice was worse than starting at midnight.
9. What would you do with a month? Apply for WattTime noncommercial MOER access, rebuild the decision metric on marginal data, add a second year, and run the user test with ten families rather than one.
10. Biggest weakness? Virginia is the flattest grid we tested: 8.1% headroom against midnight at 24 h, and we capture 6.9% of it. The honest pitch is worth doing and smaller than the headlines suggest.

Repeat three things in every answer: one place (Northern Virginia), one decision (when to start a flexible job), one finding (a better forecast is not automatically a better choice of hours).

## Sources to have open

- Judging criteria: https://highschoolhackathon.org/judges
- WattTime API and access terms: https://docs.watttime.org/ and https://watttime.org/noncommercial-agreement
- WattTime on a billion devices: https://watttime.org/news-and-insights/more-than-one-billion-smart-devices-now-using-marginal-emissions-data-to-slash-power-grid-pollution-with-watttimes-aer
- Electricity Maps on why it dropped marginal signals: https://app.electricitymaps.com/developer-hub/api/getting-started
