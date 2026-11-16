# Clean-Hour: when is Northern Virginia's electricity cleanest?

**Track:** Climate
**Team:** Harshal Mahadik, Aarush Gutha, Sidharth Mantri (TJHSST)
**Code:** https://github.com/Harshal623/clean-hour (details in README; PyTorch notebook with GPU outputs in `src/experiments/torch_transformer/colab.ipynb`)

**Main takeaway:** a model that predicts grid carbon better is not automatically better at choosing the cleanest hours.

## The problem
The power plants running at 7 PM are not the ones running at 2 AM, so the same EV charge causes different CO2 depending on when it starts. A Northern Virginia family plugging in at 6 PM has no way to know which hours are cleanest. Neither do the data centers next door in Loudoun County, whose batch jobs could often wait.

## What we built
**User and moment:** a Northern Virginia family at 6 PM, deciding when to charge the car. (The same forecast serves a Loudoun data center lead scheduling tomorrow's batch jobs.)
**In:** the appliance, how long it can wait (12 h, 24 h or 3 days), and a day.
**Out:** one answer, for example "Start Friday, May 1 at 12 PM, about 12% cleaner than starting at midnight" (or "Green: start whenever" / "Red: wait longer" when no hour stands out), a green-to-red strip of the coming hours, and a hindsight check of what really happened.

## What we added
Our own idea, place (Northern Virginia, PJM grid) and data (EIA-930 fuel mix, demand forecasts, archived weather forecasts for Ashburn). Our own questions: is a better forecast a better choice of hours, and does the method hold up on four other grids?

## How it works
**Data:** hourly PJM fuel mix, Jan 2023 to Nov 2026 (about 34,000 hours), converted to grams of CO2 per kWh with IPCC emission factors. Missing hours are never filled. Weather inputs are archived forecasts, not observations, so nothing leaks from the future.
**Models:** scikit-learn gradient boosting, made at 6 PM for the next 76 hours. Then a 2-layer Transformer in PyTorch, trained on a free Colab GPU, that looks at all 76 hours at once.
**Split:** train 2023-2025, test every day of 2026, never shuffled. Intervals are 95% block bootstrap.

## Results (Virginia, 2026 test, 4-hour job, g CO2 per kWh, lower is better)
| Job can wait | Start at midnight | Tomorrow = today (persistence) | Gradient boosting | Perfect hindsight |
|---|---|---|---|---|
| 24 h | 353.4 | 330.6 | 329.1 | 324.7 |
| 72 h | 353.4 | 330.6 | 318.1 | 309.7 |

- **Against what the family would really do** (charge the moment they plug in at 6 PM), following the app is 9.7% cleaner with one day of slack and 12.7% with three (46 g/kWh [42, 50]). The Transformer reaches 13.4%. Perfect hindsight would get 15.0%, so we capture most of what the grid allows.
- With 3 days of slack the model beats persistence by 12.5 g/kWh [-15.3, -9.5]. With 24 hours it is nearly tied (-1.5 [-2.8, -0.2]).
- Our first model cut hourly error by 35% versus persistence, yet picked hours no better. That is the takeaway above.
- The Transformer picks better: it captures 89% of the best possible saving at 24 h, versus 84% for gradient boosting (-1.3 g/kWh [-2.1, -0.7]). By our pre-set rule it is a tie overall: it clearly won only in Virginia and Texas.
- Impact: versus charging at 6 PM, an EV saves about 106 kg CO2 a year with one day of slack and 139 kg with three (assuming 3,000 kWh). A 10 MW flexible data center load would avoid about 1 tonne a day (arithmetic only).

**Where it fails:** compared with charging at 6 PM, the advice backfired on 4.5% of days with one day of slack and 2.3% with three. Against midnight it was 8%, usually by little (median loss 4 g/kWh). On Jan 9, 2026 the app said "Start Saturday at 1 AM" and that turned out 12% dirtier than midnight, because the fuel mix shifted overnight. Virginia's grid is also the flattest of the five we tested, so the ceiling is low; the same method saves 33-53% in Texas, Germany, Britain and California (`results/experiments/plug_in_baseline.csv`). Our signal is the PJM-wide average, not Loudoun-specific and not marginal emissions. No user test yet.

## What we'd do next
1. Switch to PJM's marginal emission rates and live forecasts, so the app works tonight instead of replaying 2026.
2. Test it with one real family and one data center operator.

## Sources
EIA-930, Energy-Charts (Fraunhofer ISE), NESO Carbon Intensity API, Open-Meteo, IPCC AR5 emission factors, scikit-learn, PyTorch, Google Colab, pandas, Gradio. AI tools: Claude (Anthropic) and Perplexity. Links: `CREDITS.md`.
