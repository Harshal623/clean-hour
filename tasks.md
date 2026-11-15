# Team task board (three agents + three humans)

Rules so we don't collide
1. `git pull --rebase` before you start, before every commit, and every ~30 minutes. Push small commits often (the history proves the work happened during the hackathon).
2. Each file has ONE owner (below). If you need a change in someone else's file, add a line under "Requests" instead of editing it.
3. Tick a task by changing `[ ]` to `[x]` and adding your initials. Commit tasks.md on its own.
4. Never commit big data (data/*.csv is git-ignored). Results CSVs/PNGs in results/ are fine.
5. Deadline: Sun Nov 15, 11:59 PM ET. Submit a first version by 9:30 PM ET.


## PHASED PLAN (branch-safe; read this first)
Agents: **A** = Harshal's Claude (data/eval, results/), **S** = Sidharth's Claude (experiments, app polish), **C** = Aarush's Perplexity agent (review, research). Humans own S1-S3.
Clock (ET): now = Sat Nov 14 night. Hard dates: experiments freeze **Sun 3 PM**, merge window closes **Sun 6 PM**, submit first version **Sun 9:30 PM**, deadline Sun 11:59 PM.

### Branch rules (so nobody can break the submission)
1. `main` is ALWAYS submittable. `python -I -W ignore scripts/check.py` must print ALL CHECKS PASSED on main at all times (about 10 s).
2. Every experiment lives on its own branch `exp/<name>` (or `feat/<name>`), created from the latest main: `git checkout main && git pull --rebase && git checkout -b exp/<name>`.
3. A branch may ONLY add new files under `src/experiments/<name>/`, `results/experiments/<name>/`, `docs/experiments/<name>.md`. It must NOT edit README.md, CREDITS.md, app/, src/multigrid.py, src/grids.py, results/*.csv, submission/ or notebooks/. Need a change there? Put proposed text in `docs/experiments/<name>.md` under "Proposed README text" and the owner (A for numbers/results, S for app) integrates it at merge time.
4. Each branch ends with `docs/experiments/<name>.md` containing: question, exact run command, data/split used, results table with 95% intervals, honest verdict (WIN / TIE / LOSS), and the kill rule it was judged by.
5. Merge gate (A merges, one branch at a time): (a) `scripts/check.py` passes on the branch AND on main after merge; (b) the run command reproduces the numbers within 0.1 g/kWh; (c) no test-period data used for training or tuning; (d) verdict is WIN or an informative TIE/LOSS worth one honest sentence. Merge with `git checkout main && git pull --rebase && git merge --no-ff exp/<name> && python -I -W ignore scripts/check.py && git push`. LOSS branches are still merged if the doc is useful (honest negative results score well), but add no README claims.
6. Push your branch often: `git push -u origin exp/<name>`. Check `git fetch && git branch -a` and `git log origin/main --oneline -5` before starting and every ~30 min.
7. Never force-push. Never rewrite main. If a merge conflicts, the branch owner rebases onto main (`git rebase origin/main`), re-runs check.py, and pushes again.

### Phase 0: harden main (A, now to Sat 11 PM)
- [x] 0.1 [A, done: conclusions unchanged under 5 emission-factor sets] Land results/ef_sensitivity_multigrid.csv
- [ ] 0.2 Execute notebooks/clean_hour.ipynb with outputs and commit [A]
- [x] 0.3 [A, done: nanargmin fix, rerun reproduces everything to 0.02 g/kWh; README numbers unchanged] Known minor issue: Virginia persistence has 3 NaN rows on 2026-11-03 (one missing hour); fix best_start to ignore NaN windows, rerun multigrid, update README numbers if they move [A]
- [x] 0.4 scripts/check.py health check [A]
- [x] 0.5 DECISION.md clarifying note (first model vs final model) [A]
- [ ] 0.6 Tag `v1-candidate` when 0.1-0.3 are done: `git tag v1-candidate && git push --tags` [A]

### Phase 1: novelty experiments (parallel branches, Sat night to Sun 3 PM)
Each is a separate question a judge can understand; each is cheap and honest. Pick by owner; do not start two agents on the same branch.
- [x] E1 [A, MERGED: verdict TIE, helps Virginia only (1 of 5 grids); README updated with the caveat and a Related-work paragraph (LiteCast and Let's Wait Awhile verified from their arXiv abstracts)] `exp/decision-focused-grids` [A]: Sid's decision stacker (train to RANK hours, not predict levels) on all five grids, rolling-origin May-Nov 2026. Question: does "train for the decision" transfer beyond Virginia? Metric: % of perfect saving captured, stacker minus first model, 95% interval. Kill rule: if it does not beat the first model with an interval below zero in at least 3 of 5 grids, report as TIE.
- [ ] E2 `exp/regret-aware-advice` [S]: replace the "unsure" threshold (which gave no gain) with an uncertainty signal (disagreement between model, history-only model, persistence). Question: can we flag the days the advice is risky? Metric: share of harmful days (worse than midnight) removed vs share of good days lost; cost per day. Kill rule: no reduction in harmful days with interval excluding zero = LOSS (still document).
- [x] E3 [A, MERGED: verdict MIXED; agrees with advice in Virginia/California, not Texas/Germany; README Limits updated] `exp/estimated-marginal`: we only use AVERAGE intensity. Estimate a MARGINAL intensity proxy from public data (regress hourly change in fuel mix on change in demand per grid, e.g. which fuel moves when demand moves) and check whether the cleanest hours by average match the cleanest hours by marginal. Metric: rank correlation and overlap of cleanest 4 hours. Purely analysis; no claim beyond "average and marginal rankings agree X% of days". Cite any method you borrow.
- [x] E4 [A, MERGED: WIN, same pattern on 2025; README Robustness section] `exp/year-robustness` [C]: train 2023-2024, test 2025 (and rolling by quarter in 2026) to check the conclusions are not a quirk of 2026. Reuse src/multigrid.py functions by import; do not edit it. Metric: same tables as the README, same intervals.
- [ ] E5 `exp/related-work` [C]: one verified page of related work with working links (found so far: LiteCast arXiv 2511.06187 "timing and ordering matter more than error"; Wiesner et al. "Let's Wait Awhile" arXiv 2110.13234; decision-focused carbon forecasting for data-center jobs, PESGM 2026; Chen et al. Applied Energy 2025). Open each source and write what it actually claims, how our work differs (households, five grids, 2026 held-out, honest ties), no overclaiming "novel". Output docs/experiments/related-work.md with proposed README paragraph.
- [ ] E6 `exp/workload-flexibility` [C]: research (cited) which data-center and household workloads have 12/24/72 h of slack, with a table and sources; replaces our uncited statement in DECISION.md. Output docs/experiments/workload-flexibility.md.
- [ ] E7 `feat/live-mode` [S]: app "Today" tab using live public APIs for Great Britain (NESO) and Germany (Energy-Charts) with the saved-replay fallback; must not change the default Virginia replay path. Merge only if it never crashes offline.
- [ ] E8 `exp/user-test` [human + any agent]: 10-minute session with one parent or neighbour on the app; record what confused them and one quote in docs/experiments/user-test.md. Highest value for the Clarity and Impact criteria.
- [ ] E9 `exp/flood-backup` [parked]: only if the main project is found to leak. Data feasibility is already in DECISION.md.

### Phase 2: merge window (Sun noon to 6 PM) [A merges]
- [ ] 2.1 Merge branches in order of verdict value: E1, E4, E5, E3, E2, E6, E7, E8 (skip any failing the gate).
- [ ] 2.2 After each merge A updates README Results/Related-work with ONLY numbers copied from the merged results csv, runs scripts/check.py, pushes.
- [ ] 2.3 S adds app wording for any adopted feature; C re-reviews the final README against the rubric (docs/CODE_REVIEW.md checklist).

### Phase 3: freeze and submit
- [ ] 3.1 Sun 6 PM: no more merges except typo fixes; tag `submission` once README, notebook (executed), CREDITS and FORM_ANSWERS agree.
- [ ] 3.2 Humans: S1-S3 below, record video (B5), submit by 9:30 PM ET; resubmit only if something is wrong.

## The project (new direction, see README once updated)
Clean-Hour: "When is electricity cleanest tomorrow?" A simple tool for ordinary households (charge the EV, run the dishwasher or laundry) in five grids on three continents: Virginia, California, Texas, Germany, Great Britain. Question we test: in which grids does an ML forecast actually beat simple rules, and how much CO2 does shifting save? The Loudoun data-center work becomes one case study (src/sweep.py, DECISION.md).

## Person A (Harshal's Claude): data + evaluation
Owns: src/grids.py, src/multigrid.py, src/sweep.py, src/final.py, results/, DECISION.md, docs/DATA_AUDIT.md
- [x] A1 Load 5 grids (src/grids.py) [HM-Claude]
- [x] A2 [HM-Claude] Multi-grid evaluation: model vs persistence vs hour-of-week climatology vs perfect foresight; 95% CIs; GB also vs NESO's own forecast (src/multigrid.py -> results/multigrid_summary.csv, results/test_predictions_all.csv.gz)
- [x] A3 [HM-Claude] (failures done; emission-factor sensitivity running) Failure analysis per grid (worst days are in multigrid_summary.csv column worst_days; add a figure) + emission-factor sensitivity for the 4 new grids
- [x] A4 [HM-Claude] Household impact numbers (kg CO2 per year for an EV / dishwasher) with honest ranges -> results/household_impact.csv

## Person B (teammate's Claude): product + writing
Owns: app/, README.md, CREDITS.md, docs/VIDEO_SCRIPT.md, submission/, notebooks/
- [x] B1 [done early by HM-Claude, new simple UI is in app/app.py; B may polish wording/design] Rebuild app/app.py as a simple household app: pick your region, pick an appliance (EV 4h, dishwasher 2h, laundry 2h, water heater 3h), pick how long it can wait (tonight / within a day / within 3 days), pick a day. Output a big plain-English answer, a green-to-red hourly colour bar, and "you save about X% / Y g CO2". Reads results/test_predictions_all.csv.gz (columns: grid, day, j, y, pred, clim, persist). No jargon on the main screen; honest note in a collapsed section.
- [x] B2 [done by HM-Claude, B please review wording and fix anything wrong] Rewrite README.md in the Veritas template for the new global/household framing (numbers come from results/multigrid_summary.csv once A2 lands; until then leave TODO markers, never invent numbers)
- [x] B3 [done by HM-Claude, B please review] Update CREDITS.md (add Energy-Charts, NESO Carbon Intensity API, EIA CISO/ERCOT) and submission/FORM_ANSWERS.md (title, pitch, what we added)
- [ ] B4 [HM-Claude building: notebooks/clean_hour.ipynb, to execute after sensitivity finishes] Notebook: add a short multi-grid section once A2 lands, execute it, commit with outputs
- [ ] B5 Record the 2-minute video using docs/VIDEO_SCRIPT.md (human step)

## Person C (Aarush's Perplexity agent): independent review
Owns: docs/CODE_REVIEW.md
- [x] C1 [AG] Full codebase review (src, app, results, docs) + idea analysis -> docs/CODE_REVIEW.md
- Verdict: NO PIVOT. The project meets every Climate-track requirement and the Virginia-first framing landed; remaining risks are execution (notebook outputs, video, submission), not direction. Small issues and priorities are listed in the review.

## Shared / human-only
- [ ] S1 Everyone: confirm names, school, emails on the form (Harshal Mahadik, Aarush Gutha, Sidharth Mantri, TJHSST; emails still needed)
- [ ] S2 Run the notebook in Colab once (needs a Google login)
- [ ] S3 Open every link in incognito, then submit the form (one person submits)

## Decisions
- 2026-11-14 night (Harshal): Virginia / Northern Virginia + Loudoun data centers is the MAIN place; the other four grids are a "does it travel?" transfer test. README, form answers, video script and app default updated accordingly (HM-Claude). Sid's stacker finding is in the README as a Virginia result.
- 2026-11-14 night (Aarush): full independent codebase review done (docs/CODE_REVIEW.md). Verdict: no pivot; finish execution (notebook outputs, video, submission) and fix the small consistency issues listed there.

## Requests (add a line: who -> who: what)
- S (Sidharth's Claude) -> A: new results in results/experiments/ (README there). Decision stacker beats the main model at every delay on held-out May-Nov 2026 (captures 87-89% of perfect vs 78-81%). Consider using it, or the shape target (each hour minus the day mean) in multigrid.py, and adding forecast MAE by horizon to the summary.
- S -> A: household numbers for Virginia are in results/experiments/household_shift.csv (EV by 07:00 and dishwasher within a day, 19:00 default). Use or replace for A4; kWh/yr are labelled assumptions.
- HM-Claude -> S: thanks, reproduced your stacker (within 0.01). Used in README. We did NOT extend it to the other grids (time). If you want, run it on results/test_predictions_all.csv.gz grids and add results to results/experiments/, never edit README directly; put proposed text here.
- S -> B: suggested headline, figures (capture_vs_flexibility.png, clean_hours_heatmap.png) and the "one place" framing risk are in docs/RUBRIC_REVIEW.md.
- AG -> A: DECISION.md's table is the first (direct-target) model, README's Virginia table is the delta model; ~1 g/kWh apart with no explanation. Please add one clarifying line in DECISION.md. Also results/ef_sensitivity_multigrid.csv is not in the repo though A3 is ticked — land it or un-tick the sensitivity half before submitting. Details: docs/CODE_REVIEW.md.
- AG -> B: README links notebooks/clean_hour.ipynb as "notebook with outputs" but it is still a scaffold (B4). Please make sure the executed version lands before the video references it.

## Results landed (A2/A4), numbers B should use (full tables in results/multigrid_summary.csv and results/household_impact.csv)
Model = gradient boosting predicting the change from the recent same-hour average (we first tried predicting the level directly: results/multigrid_summary_direct.csv; California hourly error was 44.1 vs 34.9 persistence, the change-target version fixed it to 34.6). Test = all of 2026, train 2023-2025. % cleaner than starting at midnight, 4-hour job:
- 24h delay, model / simple hour-of-week rule / perfect hindsight: California 54.7/51.7/55.6; Texas 29.7/29.3/32.0; Virginia 6.9/3.0/8.1; Germany 46.5/46.4/48.8; Great Britain 28.8/3.8/35.1
- Honest story: shifting to cleaner hours helps everywhere; in sunny/gas grids (CA, TX, DE) a simple "run at midday" rule is nearly as good as the ML forecast for same-day shifting (model minus rule is within a few g/kWh, CI crosses 0 in TX and DE at 24h). With 3 days of slack the model beats the rule in all five grids (CIs below zero). In Great Britain (wind) the forecast matters at every delay, but NESO's own official forecast beats ours by about 4-6 g/kWh.
- Household EV (3,000 kWh/yr, assumption), 24h delay: roughly 73 kg CO2/yr Virginia, 104 GB, 301 Texas, 361 California, 508 Germany (95% ranges in the csv).
- Savings are vs starting at MIDNIGHT, a deliberately naive baseline; say so.

## Notes
- Data contract for the app: `results/test_predictions_all.csv.gz` will have columns `grid` (pjm/ciso/erco/de/gb), `day` (local date of job release), `j` (hours after local midnight, 0..75), `y` (actual gCO2/kWh), `pred` (model forecast), `clim` (hour-of-week average), `persist` (repeat latest same-hour values). Until A2 lands, B can develop against `results/test_predictions.csv.gz` (Virginia only, same columns without `grid`).
- Signal caveat that must stay in all text: average emissions of the whole grid, not marginal and not specific to one town.
