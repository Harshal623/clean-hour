# Clean-Hour Finals: 3-minute script, same seven slides

Finals: Saturday, Nov 21, 11:00 AM ET. One presenter, three minutes, then Q&A.
This replaces the spoken part of `docs/` finals script. **The slides do not change.** Same seven slides, same two Colab moments, same order — only the words are shorter.

Spoken length: about 400 words, roughly 2:50 at a calm pace, leaving time for two tab switches.

## Timeline

| Time | Slide | Colab |
|---|---|---|
| 0:00–0:08 | 1 Title | — |
| 0:08–0:33 | 2 Problem and decision | — |
| 0:33–0:56 | 3 Pipeline | — |
| 0:56–1:28 | 4 Model, no peeking | (a) features and training, 8 s |
| 1:28–2:05 | 5 Virginia results | (b) Results chart, 8 s |
| 2:05–2:35 | 6 Better forecast is not a better choice | — |
| 2:35–3:00 | 7 Impact, limits, next steps | — |

## The script

**Slide 1 — 0:00**
Hi, I'm Aarush. With Harshal and Sidharth I built Clean-Hour: a forecast for the cleanest hour to start a job that can wait. We're from Northern Virginia, so that's our place.

**Slide 2 — 0:08**
Electricity isn't equally clean all day. The plants running at 7 PM aren't the ones running at 2 AM, so the same car charge can be much dirtier at one hour than another. Families face this every night, and so does Loudoun County, one of the biggest data-center clusters in the world. Nobody tells them when the clean hour is. Our one decision: when to start a flexible job.

**Slide 3 — 0:33**
Here's the pipeline. Public data: the federal EIA's hourly fuel mix for our grid, PJM, plus weather forecasts for Ashburn. We turn the fuel mix into grams of CO2 per kilowatt-hour. Every evening at 6 PM a gradient-boosting model forecasts that for the next 76 hours — three days of waiting plus a four-hour job. Then we pick the cleanest window inside the time the job may wait, and score it against what really happened.

**Slide 4 — 0:56**
Three design choices. First, only what you'd know at 6 PM: the past week of grid data, demand forecasts, Ashburn weather. Second, we predict how tomorrow differs from that hour's recent average, not the raw level — the level version lost to just repeating yesterday. Third, trained on 2023 through 2025, tested once on all of 2026, never shuffled.

*[Colab tab: scroll to the features and training cell]* Here's the features, the fixed settings, and the 2026 test, in the notebook we submitted. *[Back to slides]*

**Slide 5 — 1:28**
Virginia, a four-hour job, all of 2026. With three days of slack we're 10 percent cleaner than starting at midnight. The hour-of-week rule gets 6, perfect hindsight 12. Every result carries a 95 percent interval from resampling whole weeks. And before you find it: against repeating yesterday we're close at one day and only clearly ahead at three.

*[Colab tab: scroll to the Results chart]* Same result, straight from the notebook. *[Back to slides]*

**Slide 6 — 2:05**
Our biggest surprise: a better forecast isn't automatically a better choice. One early version cut hourly error by 35 percent and picked hours no better. A forecast 20 grams too high at every hour still picks the right hour, but a small miss at the cleanest hour flips the pick. Training a second model to rank hours helped in Virginia and nowhere else. In Britain we beat the simple rule 29 percent to 4, and that gap came from the forecast, not from ranking.

**Slide 7 — 2:35**
Impact: against a 6 PM plug-in, one electric car is about 106 to 139 kilograms of CO2 a year cleaner, and a flexible 10-megawatt batch job avoids about 355 tonnes. That's arithmetic, not a measurement. Limits: worse than midnight on 8.7 percent of days, like January 9th; average, not marginal, emissions; PJM-wide, not Loudoun-only. Next: marginal data, a second test year, a real user test. Shifting when we use power helps — but a better forecast isn't automatically a better choice. Thank you.

## What I cut, and why it holds up

- **The 85 percent capture line.** 10.0 of 12.4 is 81 percent, so the old "about 85" was generous. Saying the three numbers plainly is faster and safe.
- **The California sentence** became six words inside the level-versus-change point.
- **The Q&A is untouched:** every fact cut from the talk is still in the slides or the notebook, so a judge who asks gets it in one sentence.
- **Both Colab visits stayed** but at 8 seconds each: the notebook is what was judged, so it has to appear on screen at least twice.
- **The four protected lines survived:** the near-tie admission, the 20-grams example, January 9th, and the 95 percent interval.

## If you run long

Cut in this order: the ranking sentence on slide 6, the Loudoun sentence on slide 2, the second Colab visit. Never cut slide 6's 20-grams example, the January 9th failure, or the near-tie admission.

## If something breaks

- **Colab won't load or shows blank outputs:** say "the notebook is linked in the submission" and stay on the slides. Nothing in the talk depends on the screen.
- **A number on screen differs from this script:** say what the screen says. The slides are the record.
- **You blank:** Northern Virginia, when to start a flexible job, a better forecast is not a better choice.
