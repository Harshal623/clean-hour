# 2-minute demo script (screen recording + voice-over)

0:00-0:15 PROBLEM
"We live next to Loudoun County, home of one of the world's biggest clusters of data centers. The power plants running at 7 PM are not the ones running at 2 AM, so the same job or appliance can cause very different CO2 depending on when it starts. Nobody tells families or operators when the grid is cleanest. Clean-Hour does."

0:15-1:15 DEMO (python app/app.py)
- App opens on Virginia. Choose "Charge my electric car", "Until tomorrow". Read the card: "Start ... at ..., about X% cleaner than starting at midnight." Point at the green-to-red strip and the black outline.
- Open "What actually happened": "Following the advice cut CO2 by X%; the best possible was Y%."
- Switch to "up to 3 days": "More slack, more savings, and now the forecast clearly beats simple rules."
- Open "How accurate is this?" and read the honest numbers.
- Quick switch to Great Britain and California: "We also tested whether this travels. In sunny California a plain 'run at midday' rule is almost as good; in wind-driven Britain the forecast really matters."

1:15-1:45 HOW IT WORKS
"Public grid data, January 2023 to November 2026. We turn the fuel mix into grams of CO2 per kWh and train gradient boosting on 2023-2025. We test on every day of 2026, never shuffled, against four baselines. Our first model was worse than persistence in California, we fixed it, and we report both. A better forecast was not automatically a better choice, so we trained a second stage to rank hours: in Virginia it captured 91 percent of the best possible saving, up from 85, though it did not help on the other four grids. Limits: this is the PJM-wide average, not Loudoun-only and not marginal."

1:45-2:00 NEXT
"Next: live forecasts, marginal emissions, and a test with a real family and a data-center operator. Takeaway: shifting helps, and the forecast matters most when you can wait more than a day."
