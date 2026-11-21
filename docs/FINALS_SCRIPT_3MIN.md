# Clean-Hour Finals: 3-minute script, same seven slides

Finals: Saturday, Nov 21, 11:00 AM ET. One presenter, three minutes, then Q&A.
**The slides do not change.** Same seven slides, same order, same two Colab moments — only the words are shorter.

Spoken length: 408 words — 2:55 at 140 words per minute, 2:43 at 150, leaving 5 to 12 seconds for the two tab switches. If you speak slower than 140, take the first cut in "If you run long".

## Timeline

| Time | Slide | Colab |
|---|---|---|
| 0:00–0:11 | 1 Title | — |
| 0:11–0:37 | 2 Problem and decision | — |
| 0:37–1:03 | 3 Pipeline | — |
| 1:03–1:30 | 4 Model, no peeking | (a) features and training, 8 s |
| 1:30–1:57 | 5 Virginia results | (b) Results chart, 8 s |
| 1:57–2:24 | 6 Better forecast is not a better choice | — |
| 2:24–2:55 | 7 Impact, limits, next steps | — |

## The script

**Slide 1 — 0:00**
Hi, I'm Aarush. With Harshal and Sidharth I built Clean-Hour: a forecast for the cleanest hour to start a job that can wait. We're from Northern Virginia.

**Slide 2 — 0:11**
Electricity isn't equally clean all day: the plants running at 7 PM aren't the ones at 2 AM, so the same car charge can be far dirtier at one hour than another. Families face this nightly, and so does Loudoun County, the biggest data-center cluster in the world. Nobody tells them when the clean hour is. Our decision: when to start a flexible job.

**Slide 3 — 0:37**
The pipeline: the federal EIA's hourly fuel mix for our grid, PJM, plus Ashburn weather forecasts, turned into grams of CO2 per kilowatt-hour. Every evening at 6 PM a gradient-boosting model forecasts that for the next 76 hours — three days of waiting plus a four-hour job. Then we pick the cleanest window and score it against what happened.

**Slide 4 — 1:03**
Three design choices. First, only what you'd know at 6 PM. Second, we predict how tomorrow differs from that hour's recent average, not the raw level — the level version lost to repeating yesterday. Third, trained 2023 to 2025, tested once on all of 2026, never shuffled.

*[Colab tab: features and training cell]* The features and fixed settings, in the notebook we submitted. *[Back to slides]*

**Slide 5 — 1:30**
Virginia, four-hour job, 2026. With three days of slack we're 10 percent cleaner than starting at midnight; the hour-of-week rule gets 6, perfect hindsight 12. Every result carries a 95 percent interval from resampling whole weeks. And before you find it: against repeating yesterday we're close at one day, only clearly ahead at three.

*[Colab tab: Results chart]* Same result, straight from the notebook. *[Back to slides]*

**Slide 6 — 1:57**
Our biggest surprise: a better forecast isn't automatically a better choice. One early version cut hourly error by 35 percent and picked hours no better. A forecast 20 grams too high at every hour still picks the right hour, but a small miss at the cleanest hour flips the pick. Ranking hours helped in Virginia and nowhere else. In Britain we beat the simple rule 29 percent to 4.

**Slide 7 — 2:24**
Impact: against a 6 PM plug-in, one electric car is 106 to 139 kilograms a year cleaner; a flexible 10-megawatt batch job avoids about 355 tonnes. That's arithmetic, not a measurement. Limits: worse than midnight on 8.7 percent of days, like January 9th; average, not marginal, emissions; PJM-wide, not Loudoun-only. Next: marginal data, a second test year, a real user test. Shifting helps — but a better forecast isn't automatically a better choice. Thank you.

## What I cut, and why it holds up

- **The 85 percent capture line.** 10.0 of 12.4 is 81 percent, so "about 85" was generous. Three plain numbers are faster and safe.
- **The California story** became eight words inside the level-versus-change point.
- **The data-center arithmetic** is on the slide; the talk only names the place.
- **Both Colab visits stayed** at 8 seconds each: the notebook is what was judged, so it appears twice.
- **The four protected lines survived:** the near-tie admission, the 20-grams example, January 9th, and the 95 percent interval.

## If you run long

Cut in this order: the ranking sentence on slide 6, the Loudoun clause on slide 2, the second Colab visit. Never cut slide 6's 20-grams example, the January 9th failure, or the near-tie admission.

## If something breaks

- **Colab won't load or shows blank outputs:** say "the notebook is linked in the submission" and stay on the slides. Nothing in the talk depends on the screen.
- **A number on screen differs from this script:** say what the screen says. The slides are the record.
- **You blank:** Northern Virginia, when to start a flexible job, a better forecast is not a better choice.
