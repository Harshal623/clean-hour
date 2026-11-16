# 2-minute demo video: exact clicks and words

Follows the brief's structure: problem 15 s, demo 60 s, how it works 30 s, next steps 15 s. Screen recording with voice-over, one take. Round 1 is judged blind, so do not say or show names or the school.

## Setup before you hit record
1. In a terminal at the repo root: `python app/app.py`. Open the local link (http://127.0.0.1:7860) in Chrome.
2. Zoom the page to 125% (Cmd and +). Stay on the first tab, "Replay".
3. Check the starting screen: region "Virginia / Mid-Atlantic, USA", appliance "Charge my electric car", wait "Until tomorrow (24 hours)", day "Fri 01 May 2026". The green card should read **Start Friday at 12 PM**.
4. Open a second Chrome tab with the results chart: https://github.com/Harshal623/clean-hour/blob/main/results/experiments/torch_transformer/capture_24h.png
5. Close other tabs and turn off notifications. Go back to the app tab and scroll to the top.

## 0:00-0:15 The problem
**Screen:** app, top of page. Do not click.
**Say:** "We live next to Loudoun County, one of the biggest clusters of data centers in the world. The power plants running at 7 PM aren't the ones running at 2 AM, so the same EV charge can cause very different CO2. Nobody tells a family when the grid is cleanest. Clean-Hour does."

## 0:15-1:15 The demo
**Move 1 (0:15).** Circle the mouse over the three inputs, then over the green card.
**Say:** "A Northern Virginia family plugs in the car at 6 PM, and it can wait until tomorrow. Clean-Hour says: start Friday, May 1 at noon, about 12% cleaner than midnight."

**Move 2 (0:27).** Slide the mouse along the colored strip and stop on the black outline. Say: "Green is cleaner." (optional)

**Move 3 (0:33).** Click the bar "What actually happened that day? (hindsight check)".
**Say:** "This is a real day from 2026 that the model never saw. Following the advice cut CO2 by 11%, which was the best possible."

**Move 4 (0:43).** Scroll up. Click "I'm flexible: up to 3 days". Point at the card (Start Sunday at 12 PM).
**Say:** "If the car can wait three days, it picks Sunday at noon, and the real saving was 35%."

**Move 5 (0:52).** Click the day box, type `09 Jan`, press Enter (Fri 09 Jan 2026). Point at the hindsight text showing -12%.
**Say:** "Here's where it fails. On January 9th it said Saturday at 1 AM, and that was actually 12% dirtier. The fuel mix shifted overnight. That's rare: compared with charging at 6 PM, the advice backfires on about 2% of days."

**Move 6 (1:05).** Click "How accurate is this? (honest numbers)".
**Say:** "Across every day of 2026, that's 10% cleaner than midnight, and 13% cleaner than charging the moment you plug in at 6. Even perfect hindsight only gets 15."

## 1:15-1:45 How it works
**Screen:** switch to the chart tab at 1:15. Point at the Virginia bars when you mention them.
**Say:** "We train on public grid data from 2023 to 2025 and test on 2026, never shuffled. With three days of slack we clearly beat the 'tomorrow equals today' baseline. With one day it's nearly a tie. Our surprise: a model with lower error did not pick better hours. So we trained a Transformer in PyTorch that sees all 76 hours at once. In Virginia it captures 89% of the best possible saving, up from 84."

## 1:45-2:00 One limit and next steps
**Screen:** stay on the chart.
**Say:** "One limit: this is the regional grid average, not the exact plant that ramps up. Next: live data, and a test with a real family and a data center operator. The takeaway: a better forecast is not automatically a better choice."

## After recording
- Keep it under 2:00 (the script is about 290 spoken words). If you run long, cut Move 6.
- Upload to YouTube as Unlisted (or Drive with "anyone with the link can view"), then open the link in an incognito window.
- Paste the link into the form.

Numbers in this script were checked against the app and the results files on Nov 15: May 1 gives 12% predicted and 11% actual at 24 h, 35% actual at 3 days; Jan 9 gives -12% at 3 days; the Virginia scorecard at 3 days shows 353, 318 (10%), 331 (6%) and 310 (12%). The 6 PM numbers (12.7%, rounded to 13; 15.0% for hindsight; 2.3% of days) are in `results/experiments/plug_in_baseline.csv` and are spoken, not shown on screen.
