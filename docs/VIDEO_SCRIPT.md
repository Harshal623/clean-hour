# 2-minute demo script (screen recording + voice-over)

0:00-0:15 PROBLEM
"Electricity isn't equally clean all day. If you charge your car or run the dishwasher at midnight, you often use much dirtier power than if you waited a few hours. But nobody tells you when. We built Clean-Hour for five grids on three continents."

0:15-1:15 DEMO (python app/app.py)
- Choose California, "Charge my electric car", "Until tomorrow". Read the card: "Start ... at 2 PM, about 44% cleaner than starting at midnight." Point at the green-to-red strip and the black outline.
- Open "What actually happened": "Following the advice cut CO2 by X%; the best possible was Y%."
- Switch to Great Britain, then Germany. "Wind-driven Britain: the forecast really matters. Sunny Germany: a simple rule is almost as good for same-day shifting."
- Switch to "up to 3 days": "More slack means more savings, and now the forecast clearly wins everywhere."
- Open "How accurate is this?": show the honest numbers.

1:15-1:45 HOW IT WORKS
"Public grid data from the US, Germany and Britain, January 2023 to November 2026. We turn the fuel mix into grams of CO2 per kWh, and train gradient boosting on 2023-2025. We test on every day of 2026, never shuffled, against four baselines. Our first model was worse than persistence in California, we fixed it by predicting the change, and we report both. Limits: this is the regional average, not marginal, and Britain's official forecast beats ours."

1:45-2:00 NEXT
"Next: run it live, add more countries, and add marginal emissions. Takeaway: shifting helps everywhere; a forecast matters most when you can wait more than a day."
