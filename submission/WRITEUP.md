# Clean-Hour: cleaner hours for Northern Virginia homes and Loudoun's data centers

**Track:** Climate
**Team:** Harshal Mahadik, Aarush Gutha, Sidharth Mantri (TJHSST)
**Code and notebook:** https://github.com/Harshal623/clean-hour (full details in the README)

**Main takeaway:** a model that predicts grid carbon better is not automatically better at choosing the cleanest hours. Training a second stage to rank hours captured 91% of the best possible saving in Virginia, up from 85%.

## The problem
The power plants running at 7 PM are not the ones running at 2 AM, so the same job can cause very different CO2 depending on when it starts. Northern Virginia hosts one of the world's largest clusters of data centers, and many of their batch jobs (AI training chunks, backups) could wait hours. Families have the same choice with an EV or a dishwasher, but nobody tells either of them when the grid is cleanest.

## What we built
At 6 PM, a Northern Virginia household or a Loudoun data center operations lead enters a job length and how long it can wait (12 h, 24 h or 3 days). Clean-Hour returns one plain answer ("Start Friday at 2 PM, about 44% cleaner than starting at midnight"), a green-to-red strip of the coming hours, and a hindsight check of what really happened that day.

## What we added
Our own idea. Own place and user: Northern Virginia on the PJM grid. Own data: EIA-930 fuel mix and demand forecasts plus archived weather forecasts for Ashburn. Own questions: is a better forecast a better choice of hours, how long must a job be able to wait before a forecast beats simple rules, and does the method transfer to four other grids (California, Texas, Germany, Great Britain)?

## How it works
**Data:** hourly PJM fuel mix, Jan 2023 to Nov 2026, converted to grams of CO2 per kWh with IPCC lifecycle emission factors. Missing hours stay missing and those days are dropped (3 of 314). Weather inputs are archived *forecasts*, not observations, so nothing leaks from tomorrow.
**Model:** scikit-learn gradient boosting predicts tomorrow's change from the recent same-hour average, using the last week of grid data, demand forecasts and weather forecasts. A second-stage model is trained to rank hours rather than predict their level. We also trained a small Transformer in PyTorch on a free Colab GPU that looks at all 76 future hours at once.
**Split:** train 2023-2025, test all 311 days of 2026, never shuffled. 95% intervals come from a 7-day block bootstrap.

## Results (Virginia, 4-hour job, grams CO2 per kWh, lower is better)
| Job can wait | Start at midnight | Tomorrow = today (persistence) | Hour-of-week average | Our model | Perfect hindsight |
|---|---|---|---|---|---|
| 24 h | 353.4 | 330.6 | 342.6 | 329.1 | 324.7 |
| 72 h | 353.4 | 330.6 | 331.0 | 318.1 | 309.7 |

- With 3 days of slack the model beats persistence by 12.5 g/kWh [95% CI -15.3, -9.5]. With 24 hours it is close to persistence (-1.5 [-2.8, -0.2]), which is an honest near tie.
- The ranking stage lifts the share of the best possible saving from 85% to 91% at 24 h (-1.8 g/kWh [-2.5, -1.2], scored May-Nov 2026 because Jan-Apr trained it).
- The PyTorch Transformer did even better in Virginia: 89% of the best possible saving at 24 h vs 84% for gradient boosting (-1.3 g/kWh [-2.1, -0.7]), scored on all of 2026. Across the five grids it won only in Virginia and Texas, so we call it promising, not a replacement (`docs/experiments/torch-transformer.md`).
- Impact: an EV that can wait a day saves about 73 kg CO2 a year. A 10 MW flexible data center load shifted the same way avoids roughly 1 tonne a day (arithmetic, not a measurement).

**Where it fails:** on 8% of days the advice was worse than starting at midnight. The worst was Feb 20, 2026 (43 g/kWh above the best window), after a fuel-mix shift the evening forecast could not see. The ranking trick also did not transfer: in California, Texas, Germany and Britain the first model already captured 85-98% of the best saving, and the second stage tied or lost. It helps where the daily pattern is flattest, which is Virginia. Our signal is the PJM-wide average, not Loudoun-specific and not marginal emissions.

## What we'd do next
1. Switch to PJM's marginal emission rates and live forecasts, so the app works tonight instead of replaying 2026.
2. Test the app with a real family and a data center operator and fix what confuses them.

## Sources
EIA-930, Energy-Charts (Fraunhofer ISE), NESO Carbon Intensity API, Open-Meteo Historical Forecast API, IPCC AR5 emission factors, scikit-learn, PyTorch, pandas, Gradio. AI tools: Claude (Anthropic) and Perplexity. Full list with links: `CREDITS.md`.
