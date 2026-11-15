# Full codebase review + idea analysis (Aarush Gutha, Nov 14 night)

Reviewed: every file in src/, app/, results/ (spot-checked numbers against README),
docs/, submission/, notebooks/ scaffolds, and the brief's Climate track rules.

## Verdict: DO NOT PIVOT

The project already satisfies every requirement of the AI + Climate brief, and the
direction was fixed tonight (Virginia/Loudoun as the main place, the other four grids
as a transfer test). A pivot at this point would discard a working, fully evaluated
project with ~24 h to the deadline and restart from zero; the brief itself says a
baseline-complete project still gets scored, and this is well past baseline.

Checklist against the brief:
- One location or region: Northern Virginia / Loudoun corridor (main), transfer test elsewhere. DONE.
- Train on earlier dates, test on later ones, never shuffled: 2023-2025 train, all of 2026 test,
  days with missing hours dropped, never filled. DONE (audited in docs/DATA_AUDIT.md).
- Compare with the persistence baseline: persistence, hour-of-week climatology, midnight start,
  perfect hindsight, plus NESO's official forecast in GB. DONE, with 95% block-bootstrap CIs.
- Explain the decision and who makes it: a household at 18:00 the evening before (or a
  data-center ops lead with flexible batch jobs). DONE, in README and the app.
- AI central to the main job: gradient-boosting carbon-intensity forecast + the
  decision-trained stacker drive every recommendation. DONE.
- Honest results incl. weak ones: ties with persistence at 12-24 h, NESO beating us in GB,
  worst failure days listed, first-version bug kept in the repo. DONE (rule 7).
- "Make it your own" (all three): own user/place, own data, own questions. DONE.

The differentiator judges are unlikely to see elsewhere: "a better hourly forecast is not
automatically a better choice of hours" (stacker captures 87-89% of perfect vs 78-81%),
plus the five-grid transfer test. That is the headline. Keep it.

## What is genuinely strong (keep as is)
- Leakage discipline (src/sweep.py, src/multigrid.py, docs/DATA_AUDIT.md): all features are
  available at the 18:00 decision hour; climatology from train years only; abstain threshold
  tuned on 2025-H2 validation, applied once to test; no interpolation; missing test days dropped.
- The two-version model story (direct vs change-from-recent-average target) with both result
  files kept — that is a real, measured model improvement, which the brief explicitly rewards.
- Data loaders handle the mid-2024 EIA schema split, placeholder future rows, duplicates and
  gaps without silent filling; GB uses the official NESO series instead of our own factors.
- App (app/app.py) reads only committed results, defaults to Virginia, plain-English output,
  hindsight check, honest collapsed caveats. No jargon on the main screen.
- Numbers in README/FORM_ANSWERS reproduce exactly from results/multigrid_summary.csv and
  results/household_impact.csv (I re-checked the Virginia table and household rows tonight).

## Issues found (small, none blocking)
1. DECISION.md's scheduling table (model 330.4/330.3/323.6/318.2) is the FIRST, direct-target
   model from sweep_summary.csv; the README's Virginia table is the delta-target model
   (329.2/329.1/323.1/318.1). Both are correct but a judge comparing the two tables will see
   ~1 g/kWh differences with no explanation. One clarifying sentence in DECISION.md fixes it.
2. Task A3 is ticked, but results/ef_sensitivity_multigrid.csv (emission-factor sensitivity for
   the four non-GB grids) is not in the repo yet — the checkbox says "running". Either land the
   csv before submission or un-tick the sensitivity half.
3. results/final_model.joblib is committed but unused (the app replays saved predictions).
   Harmless; fine to keep, but it should not be described as what the app runs.
4. notebooks/clean_hour.ipynb is a scaffold without outputs (B4 in progress). The README links
   it as "notebook with outputs" — make sure the executed version lands, or the link will 404
   the "results come from the executed notebook" claim on the submission checklist.
5. No user test yet (noted in RUBRIC_REVIEW.md). A 10-minute session with one parent using the
   app plus one quote would close the last rubric gap cheaply.

## If there is spare time before the deadline (in priority order)
1. Land the executed notebook (B4) and the multi-grid EF sensitivity csv.
2. Add the one-line clarification in DECISION.md (issue 1).
3. Record the video (B5) and submit early per the board's 9:30 PM ET plan; resubmit later.
4. The quick user test (issue 5).
5. Optional, only if trivial: mention in the README that the app replays saved forecasts and
   the joblib artifact is the trained model for a future live version.

Do not add new grids, new models or new analyses now. The marginal rubric value is small and
the risk of breaking a consistent, reproducible story is real.
