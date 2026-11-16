# 2-minute demo video: timeline, clicks and words (version 2)

Structure from the brief: problem 15 s, demo 60 s, how it works 30 s, next steps 15 s. One screen recording with a voice-over, one take is fine. About 252 spoken words (roughly 1:45 of speech), leaving time for the clicks. Aim to finish at 1:55.

**Round 1 is judged blind.** Do not say or show names or the school. The browser address bar for GitHub shows a username, so record the page content only (hide the address bar, or zoom the page so it is cropped out).

## Timeline at a glance

| Time | Screen | What you do |
|---|---|---|
| 0:00-0:18 | App, top of page | Say the problem. No clicks. |
| 0:18-0:40 | App, Virginia default | Read the card, open the hindsight bar |
| 0:40-0:52 | App, custom run time | Type 2 in the run-time box |
| 0:52-1:10 | App, red then 3-day | Pick Thu 05 Mar, "Just tonight", then "up to 3 days" |
| 1:10-1:20 | App, failure day | Pick Fri 09 Jan, show it backfired |
| 1:20-1:30 | App, Live tab | Click Find the cleanest time now |
| 1:30-1:50 | Notebook page | Scroll the code, stop on the results chart |
| 1:50-2:00 | Same page | Say the limit and the takeaway |

## Setup before you hit record
1. In a terminal at the repo root run `python app/app.py` and open http://127.0.0.1:7860 in Chrome. Zoom to 125%.
2. Stay on the first tab, "Replay". Check the starting screen: region "Virginia / Mid-Atlantic, USA", appliance "Charge my electric car", wait "Until tomorrow (24 hours)", day "Fri 01 May 2026". The card should read **Start Friday, May 1 at 12 PM**, "about 12% cleaner".
3. Leave the run-time box empty.
4. Open a second Chrome tab with the notebook on GitHub: `https://github.com/Harshal623/clean-hour/blob/main/notebooks/clean_hour_colab.ipynb`. Scroll to the top so it is ready. (Do not run it on camera, it takes about 10 minutes.)
5. Close other tabs, turn off notifications, go back to the app tab, scroll to the top.

## 0:00-0:18 The problem
**Screen:** app, top of page. Do not click.
**Say:** "We live next to Loudoun County, one of the biggest data center clusters in the world. The grid is dirtier at some hours than others, so the same EV charge can cause very different CO2. Nobody tells families when it's cleanest. Clean-Hour does."

## 0:18-0:40 The answer (Virginia, 24 hours)
**Screen:** circle the mouse over the three inputs, then the green card, then slide along the colored strip.
**Say:** "A Northern Virginia family plugs in the car, and it can wait until tomorrow. Clean-Hour says: start Friday, May 1 at noon, about 12 percent cleaner than midnight."
**Click:** the bar "What actually happened? (hindsight check)".
**Say:** "And the check: on this real 2026 day, the advice cut CO2 by 11 percent, the best possible."

## 0:40-0:52 Your own run time
**Click:** the box "Or type your own run time" and type `2`.
**Say:** "Not an EV? Type any run time. For a two-hour job: start at 1 PM, 13 percent cleaner."
**Screen check:** the card should read **Start Friday, May 1 at 1 PM**, with "(2-hour job)" in the time-frame line. Clear the box before the next step.

## 0:52-1:10 Green, red and waiting longer
**Click:** the day box, type `05 Mar`, press Enter. Click "Just tonight (up to 12 hours)".
**Say:** "On March 5th the power is dirty all night, so it says red: wait longer."
**Click:** "I'm flexible: up to 3 days".
**Say:** "With three days it picks Saturday at 2 AM, and the real saving was 14 percent."
(Green case, if you want it: Sat 10 Jan with "Just tonight" says green, start whenever you like. Skip it if short on time.)

## 1:10-1:20 Where it fails
**Click:** the day box, type `09 Jan`, press Enter (keep "up to 3 days").
**Say:** "It isn't always right. On January 9th it backfired: 12 percent dirtier. That's rare, about 2 percent of days compared with charging at 6 PM."
**Screen:** the hindsight bar stays open and says "This time the advice backfired".

## 1:20-1:30 Live
**Click:** the tab "Live: Great Britain and Germany", then "Find the cleanest time now".
**Say:** "The Live tab does the same with today's official forecasts for Britain and Germany."
(The result depends on the live forecast, so do not quote its numbers.)

## 1:30-1:50 How it works
**Screen:** switch to the notebook tab, scroll down through the code cells, slow down at the chart under "4. Results".
**Say:** "All our code is in one notebook. We train on 2023 to 2025 and test on every day of 2026, never shuffled. With three days of slack we're 10 percent cleaner than midnight; a simple rule gets 6, perfect hindsight 12."

## 1:50-2:00 Limit and takeaway
**Screen:** stay on the chart.
**Say:** "One limit: this is the grid average, not the exact plant that ramps up. Next: live Virginia data and a real family test. Shifting helps, but a better forecast isn't automatically a better choice."

## If you run long
Cut in this order: the green-case line, the Live tab (1:20-1:30), then the custom run-time moment. Never cut the failure day, judges reward honesty.

## After recording
- Under 2:00. Upload to YouTube as Unlisted (or Drive with "anyone with the link can view") and open the link in an incognito window.
- Paste the link into the form's "Demo Video Link".

## What was checked (Nov 15, 8:30 PM)
Every number above was read from the running app code: May 1 gives 12% predicted and 11% actual at 24 h; a 2-hour job starts at 1 PM with 13% predicted; Mar 5 with "Just tonight" is red, and with 3 days says Start Saturday, Mar 7 at 2 AM with 14% actual; Jan 9 with 3 days says 12% dirtier; the Virginia 3-day scorecard shows 10% (advice), 6% (simple rule) and 12% (perfect hindsight). The "about 2 percent of days" figure comes from `results/experiments/plug_in_baseline.csv` (2.3% of days worse than a 6 PM plug-in at 72 h) and is spoken, not shown.
