# 2-minute demo script (screen recording + voice-over)

0:00-0:15 PROBLEM
"Loudoun County has the biggest data-center cluster in the world, running AI jobs all day. The grid's carbon intensity changes every hour. If an operator can delay a flexible 4-hour job, when should it run?"

0:15-1:15 DEMO (python app/app.py)
- Open the app. Pick a 2026 test day, delay = 24 h. "Input: last week of carbon intensity, demand and weather forecasts, decided at 6 pm the night before."
- Click Recommend. Point at the plot: black = actual, green = our forecast, orange dotted = hour-of-week average. Shaded window = recommendation. Read the saving.
- Switch the delay to 72 h, then to 0: "With no slack there is nothing to optimize."
- Raise the "unsure" threshold: "If the forecast promises little, it says run now."
- Show results/savings_by_slip.png: "The model beats the hour-of-week average by about 12 g/kWh, with a confidence interval below zero. Against 'repeat yesterday' it is a tie at 12-24 hours. It wins only with 2-3 days of slack."

1:15-1:45 HOW IT WORKS
"EIA grid data, Jan 2023 to Nov 2026. Fuel mix becomes carbon intensity. Gradient boosting, trained 2023-2025, tested on all of 2026, never shuffled. Baselines: run now, persistence, climatology, perfect foresight. Limits: this is PJM-wide average emissions, not Loudoun-only and not marginal."

1:45-2:00 NEXT
"Next: PJM marginal emission rates and real day-ahead weather forecasts. Honest takeaway: the forecast matters mostly when jobs can wait two days or more."
