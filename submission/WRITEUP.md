# Clean-Hour: when is Northern Virginia's electricity cleanest?

**Track:** Climate · **Team:** Harshal Mahadik, Aarush Gutha, Sidharth Mantri (TJHSST)

**One takeaway: a model that predicts grid carbon better is not automatically better at choosing the cleanest hours.**

**Problem.** The plants running at 7 PM are not the ones running at 2 AM, so one EV charge emits different CO2 depending on when it starts. A family plugging in at 6 PM cannot see which hours are cleaner, and Northern Virginia's grid is unusually flat, so the honest saving here is small.

**What we built.** A 6 PM forecast of hourly grid carbon intensity (g CO2 per kWh) for the next 76 hours that answers one question: when should I start this job? Pick an appliance or type a run time, say how long it can wait (12 h / 24 h / 3 days), and get a start time in plain English plus a hindsight check. Live forecasting works tonight for Britain and Germany, whose official forecast feeds are free; the US grids replay 2026 because EIA and PJM need API keys.

**What we added.** Our own place and data (PJM fuel mix and demand from EIA-930, archived Ashburn weather forecasts, never shuffled, leakage-audited) and our own questions: is a better forecast a better choice, and does it survive four other grids?

**How it works.** Gradient boosting forecasts the change from the recent same-hour average; a 2-layer PyTorch Transformer sees all 76 hours at once. Train 2023-2025, test all of 2026, against midnight, "tomorrow = today", hour-of-week and perfect hindsight (95% block-bootstrap intervals).

**Results** (Virginia, 2026, 4-hour job, g CO2 per kWh, lower is better):

| Job can wait | Midnight | Tomorrow = today | Our model | Perfect hindsight |
|---|---|---|---|---|
| 24 h | 353.4 | 330.6 | **329.1** | 324.7 |
| 72 h | 353.4 | 330.6 | **318.1** | 309.7 |

- Against what the family would really do (plug in at 6 PM) the advice is **9.7% cleaner at 24 h and 12.7% at 72 h**; the Transformer reaches 13.4%, perfect hindsight 15.0%. That is about 106-139 kg CO2 a year for an EV.
- **Where a forecast actually matters is wind-driven Britain:** 28.8% saved at 24 h against 3.8% for the simple hour-of-week rule, a 29.9 g/kWh difference [−36.2, −24.3]. In our home grid the whole gap between midnight and perfect hindsight is 8.1%, and we capture 85% of it. We report that rather than quoting a larger number from a grid that is not ours.
- Our first model cut hourly error by 35% versus "tomorrow = today" and still chose no better hours. The Transformer captures 89% of the possible saving versus 84%, but only in Virginia and Texas, so overall it is a tie. The method transfers: 33-53% cleaner at 24 h in the other four grids.

**Where it fails.** Worse than plugging in at 6 PM on 4.5% of days at 24 h and 2.3% at 72 h. On 9 Jan 2026 it recommended 1 AM, which was 12% dirtier than midnight after the fuel mix shifted overnight. Our signal is the PJM-wide average, not marginal and not Loudoun-specific, and no real user has tested it. *This is a prototype, not energy or environmental advice.*

**Next.** Marginal emission rates and live feeds for the US grids, so the home case works tonight too; and one family plus one data-center operator using it for a week.

**Sources.** EIA-930, Energy-Charts, NESO, Open-Meteo, IPCC AR5; scikit-learn, PyTorch, Gradio; Claude and Perplexity. Links in `CREDITS.md`.
