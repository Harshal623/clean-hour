# PLAN_TO_WIN: where the remaining points are

Written 2026-11-15 midday ET from the official sources, not guesses:
- Judging criteria: https://highschoolhackathon.org/judges
- Project briefs: https://drive.google.com/file/d/15tYD48XRmCgWbk1_lLDtc8lebi6qm-4-/view

Code status: every experiment branch in tasks.md is merged, scripts/check.py prints ALL CHECKS PASSED, both notebooks carry outputs (10/10 and 7/7 code cells), v1-candidate is tagged, and all 14 links in README/CREDITS/FORM_ANSWERS return 200 except ipcc.ch (403 to automated requests only). Nothing code-side is left that a human is not required for. The remaining points are in communication, evidence and the live finals.

## 1. Scoring (published)

Round 1, blind, 100 points: technical execution 30, originality 20, impact and track fit 20, testing and honesty 15, communication 15.

Finals, 100 points: demo and clarity 30, technical depth 30, impact 20, Q&A 20.

Final ranking = 30% Round 1 + 70% Finals. Two hours on the video and the live demo outrank any further modelling.

## 2. Banked numbers (enforced by scripts/check.py)

- Virginia, 24 h slack, 4 h job, gCO2/kWh: midnight 353.4, persistence 330.6, hour-of-week 342.6, model 329.1, oracle 324.7. That is 6.9% saved against 8.1% possible.
- Model minus the simple rule at 24 h: -13.5 [-15.9, -11.4]. Minus persistence: -1.5 [-2.8, -0.2] at 24 h, -0.6 [-1.8, +0.5] at 12 h, -12.5 [-15.3, -9.5] at 72 h.
- EV at 3,000 kWh/yr with 24 h slack: 73 kg CO2/yr (64-82). Dishwasher that can wait a day: about 10%. 10 MW for 4 h: about 1 tonne/day, 355 t/yr.
- Already stated weak spots: 8% of days worse than midnight; worst day 2026-02-20 (43 g/kWh worse); Great Britain 28.8% against NESO's 35.1%.

## 3. Gaps ranked by points at risk

1. No demo video. Costs up to 15 communication points and it is the rehearsal for the 30-point finals demo.
2. No user test, and the README says so. The 10-minute script is in docs/experiments/user-test.md.
3. README is about 1,700 words; the brief asks for about one page and one main takeaway. Add the box below under the title and change nothing else.
4. One place. Sentence one and the first 15 s of the video must be Northern Virginia and Loudoun; the other four grids are a transfer test, never the headline.
5. The submission form still has <ADD> for three emails. That is certificate data and unrecoverable after the deadline.
6. Incognito pass on the repo, README and video links before submitting.

Paste-ready box for the top of README.md:

> A forecast that predicts carbon better is not automatically better at choosing the cleanest hours. In Virginia, training a second stage to rank hours captured 91% of the best possible saving against 85% for the plain model; that gain did not transfer to California, Texas, Germany or Britain, and we report where it holds and where it does not.

See docs/RUNBOOK.md for the clock, docs/VIDEO_SHOT_LIST.md for the recording and docs/FINALS_QA.md for the Q&A bank.
