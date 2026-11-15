# PLAN_GAMECHANGER: how to make this a genuinely strong model before 11:59 PM ET

Written 2026-11-15 16:30 ET, after reading every file in `src/`, `app/`, `results/`, all nine
`docs/experiments/*.md`, the two open experiment branches, the brief PDF and the published rubric.
Audience: any coding agent (or human) picking this up. **Read section 0 and section 1 before touching code.**

---

## 0. TL;DR for the agent

1. **The submission is already technically sound; the model is not the bottleneck it looks like.**
   Eleven experiments have already been run and they cluster within ±1–3 g/kWh. Do not re-run them (§3, "closed doors").
2. **Three verified moves are still open and are worth real points.** In priority order:
   - **H1 — 3× the training history (2016–2022).** EIA-930 CSVs exist back to 2016 (verified: 2015 is an HTML
     soft-404). 33.9k hours → ~96k hours. No new pipeline, only config + cache invalidation. ~60–90 min.
   - **H2 — GB forecast fusion.** Their model loses to NESO's own forecast by 5.8 g/kWh (`85.52` vs `79.75` at 24 h).
     Blending the two should match or beat the national operator. ~30 min, near-certain win, great headline.
   - **G1 — retarget the model at the fuel mix instead of the scalar CI** (§5). The only architecture change that
     adds information rather than re-fitting it, and it makes marginal emissions computable for free.
3. **Do not chase the Virginia point forecast.** Perfect foresight at 24 h is `324.68` vs model `329.10`. The entire
   remaining headroom in the headline place is **4.4 g/kWh (1.3%)**. A "much better model" there is arithmetically
   impossible. Anyone claiming otherwise is wrong or leaking. Say this out loud in the write-up (§2).
4. **The real game-changers are a different quantity, a different decision and a generalization proof**, not a better
   regression: marginal emissions (§7), risk-aware advice with calibrated probabilities (§8), zero-shot transfer to a
   grid nobody trained on (§6), and an 11-year regime test (§4). All are defensible, all fit in tonight.
5. **Integrity gate:** the rules limit all project work to Nov 14–15. Anything you train after 23:59 tonight may not be
   presented as part of the submission. If you cannot finish it in-window, write it into `docs/experiments/` as a
   protocol with no results, and say so. Judges score an honest protocol higher than an out-of-window result.

---

## 1. Where the project actually stands (assessment)

**What it is.** `Clean-Hour` forecasts hourly grid carbon intensity (gCO2/kWh) for five grids — PJM/Virginia, CAISO,
ERCOT, Germany, Great Britain — from a 18:00-local decision point the evening before, then picks the cleanest 4-hour
window for a flexible job under 12/24/48/72 h of allowed delay. It compares four baselines (start at midnight,
persistence, hour-of-week climatology, perfect hindsight), reports 95% block-bootstrap intervals, and converts the
forecast into household kg CO2/yr and a data-center tonne/day figure. There is a Gradio app (2026 replay + a live GB/DE
tab), two executed notebooks, a leakage audit, and a failure analysis.

**How good is it, honestly?** This is well above the level of a typical high-school hackathon submission, and the
reason is not the model — it is the evaluation discipline. Leakage audit, fixed splits, pre-registered kill rules,
negative results kept in the repo, a documented model bug (the direct-target version lost to persistence in
California), a stated boundary condition on its own novel finding. That is what "technical execution" and "testing and
honesty" reward, and most teams will not have it.

**Where it is weak:**

| Weakness | Evidence | Consequence |
|---|---|---|
| Model is conventional and small | `HistGradientBoostingRegressor`, 12 features, 33.9k hours, one model per grid | Reads as "a tutorial model applied well", not model depth. Hurts *Originality* and *Technical execution* at finals. |
| Training history is short | 2023-01-01 → 2025-12-31 only (~3 y) | Regime sensitivity is untested; the "2026 only" test gets criticised. |
| Target is a scalar, not the system | Predicts CI directly; V2 added fuel-share *lags* but never forecast the mix | Throws away physics; average-only, never marginal; EF sensitivity needs a full retrain per factor set. |
| One test year | 311–314 test days | Wide intervals; every claim carries "one-year measurement". |
| Saturated in 3 of 5 grids | CA/DE/ERCO capture 93–98% of the perfect saving at 24 h (98.3 / 95.3 / 92.7) | No headroom by construction; the multi-grid table reads as "the ML model barely matters". |
| GB loses to the incumbent | model `85.52` vs NESO `79.75` | The one comparison a judge will remember. |

**Estimated Round 1 score today (my read, 100 pts):** technical execution 26–28/30, originality 15–17/20, impact
15–17/20, testing and honesty 14–15/15, communication 11–13/15 (README ~1,700 words against a "one page" ask; video
still missing). **≈ 81–90.** Finalist-tier. The cheapest remaining points are the video and the one-page framing; the
points that make it *win* are model depth and one clean new result. That is what this plan buys.

---

## 2. The headroom map (do the arithmetic first)

Virginia, 4 h job, 2026 test, gCO2/kWh of the chosen window:

| Delay | Midnight | Persistence | Hour-of-week | Model | Perfect | Model's remaining gap to perfect |
|---|---|---|---|---|---|---|
| 12 h | 353.37 | 329.81 | 342.86 | 329.21 | 325.54 | **3.7** |
| 24 h | 353.37 | 330.59 | 342.62 | 329.10 | 324.68 | **4.4** |
| 48 h | 353.37 | 330.59 | 337.15 | 323.09 | 315.79 | **7.3** |
| 72 h | 353.37 | 330.59 | 331.01 | 318.12 | 309.72 | **8.4** |

Read that last column carefully. **A model that predicted the future perfectly would move the headline by 1.3% at
24 h.** PJM average intensity is flat (hourly sd ≈ 34 g/kWh) and the model already captures ~85% of what is
recoverable. Therefore:

- Every "improve the model" task must state which **g/kWh of this column** it is attacking, or it is decoration.
- Whole-grid rankings are already solved in CA/DE/ERCO (93–98% of the perfect saving captured at 24 h).
  There, gains must come from a different **quantity**
  (marginal, §7), a different **decision** (§8), or **generalization** (§6) — not a better forecast.
- The honest headline for the write-up is **not** "our model saves X% more". It is: *in the flattest grid, the
  remaining headroom is tiny, and we can show exactly where a forecast still matters and where it cannot* — plus the
  "better forecast ≠ better choice" boundary condition they already found. Judges reward this; inflated claims get
  caught by "if your results look too good to be true, test data has usually leaked".

---

## 3. Closed doors — do NOT re-run these

Each has a pre-registered kill rule and a documented verdict. Re-running them is the single most likely way an agent
wastes the remaining hours.

| Already tried | Where | Verdict | Do not repeat as |
|---|---|---|---|
| Per-grid hyperparameter search (15 configs) | `model-variants.md` (V1) | TIE (0/5 grids significant) | "tune the GBM" |
| Extra features: 14-day same-hour stats + fuel-share lags | V2 | TIE (all diffs < 1 g/kWh) | "add fuel-mix lags" |
| Validation-fit blend of full/history-only/persistence | V3 | TIE (helps 24 h only) | "ensemble the existing models" |
| Quantile (conservative) point loss | V4 | LOSS (worse in GB at 72 h) | "quantile loss" |
| Decision stacker (rank hours) | `decision-focused-grids.md` | TIE overall, **WIN in Virginia only** | "train for ranking" as a general claim |
| PyTorch HorizonTransformer + ListNet decision loss | `origin/exp/torch-transformer` | TIE overall; **WIN in VA (4/4 delays, −1.0 to −2.6 g/kWh) and ERCO-mse (4/4)** | "build a Transformer" — already built, unmerged |
| Uncertainty/agreement abstention | `regret-aware-advice.md` | LOSS (1/5 grids) | "add an 'unsure' threshold" |
| Marginal-emissions proxy (season × 6 h constant shares) | `estimated-marginal.md` | MIXED (agrees VA/CA, flips TX/DE) | "estimate marginal emissions" the same coarse way |
| Emission-factor sensitivity (5 sets) | `ef_sensitivity*.csv` | Robust (−11.9 to −20.2 g/kWh) | "check the EFs again" |
| Train 2023-24 / test 2025 | `year-robustness.md` | WIN, same pattern | "add a robustness year" — extend it instead (§4) |

**Blocked data sources (verified today, do not spend time):**
- EIA API v2 → HTTP 403, `API_KEY_MISSING`. Needs a free key; nobody has time to wire it.
- PJM Data Miner (`da_hrl_lmps`, day-ahead LMP) → returns a login HTML page without a subscription key.
- EIA-930 2015 six-month CSV → returns an HTML 404 page with status 200. **Always check first bytes, not status.**
- OpenAQ → needs a key. Not needed here.

**Verified-available data (tested today):** EIA-930 six-month CSVs **2016 → 2026**, NESO carbon intensity from
**2018**, Energy-Charts DE from **2015**, Open-Meteo historical-forecast API back to at least **2019**.

---

## 4. H1 — Triple the training history (do this first)

**Why it is game-changing.** It is the only change that adds *information* at zero methodological cost, and it is
exactly the "train a strong model for a long time" ask: **33,912 hours → ~96,000 hours** per EIA grid. It converts
"2026 was one year" into "the same conclusion holds across five market regimes" (2020 demand collapse, 2021 gas
spike, 2022 coal-to-gas shift, 2023–26 solar build-out). At finals, "we trained on eleven years and five grids" is a
one-sentence technical-depth answer that no other high-school team will have.

**Protocol (pre-register before running).**
1. Extend loaders; rebuild all caches from scratch.
2. Train 2016–2025, test all of 2026 (unchanged test period, so the headline stays comparable).
3. Also produce a **5-fold expanding-window backtest**: test 2022, 2023, 2024, 2025, 2026 (each with only prior years
   in training). Report per-fold deltas and a Diebold–Mariano test alongside the block bootstrap.
4. **Kill rule:** adopted only if the model-minus-climatology interval stays below zero at 24 h *and* 72 h in ≥ 4 of 5
   grids across ≥ 4 of 5 folds, *and* the 2026 Virginia decision cost improves or ties. If it does not, it is still a
   WIN-grade result as a robustness table — report it and change no README numbers.

**Implementation notes (all verified).**
- `src/load_data.py`: `HALVES` starts at 2023. Replace with a generated list for **2016–2026**. Guard the first
  bytes: raise if the response does not start with `"Balancing Authority"` (2015-style soft-404 trap).
- `src/grids.py`:
  - `load_weather_at(...)` is called with `start="2023-01-01"` → `"2016-01-01"`.
  - `load_de()` loops `range(2023, 2027)` → `range(2016, 2027)`, and its end-date clamp stays.
  - `load_gb()` starts at `t0 = 2023-01-01` → `2018-01-01` (14-day chunks ≈ 230 requests, ~3–4 min).
  - `load_eia_multi()` inherits the new `HALVES`, so CISO/ERCO extend automatically.
- **Invalidate caches** or nothing reloads: `rm -f data/grid_*.csv data/fuel_*.csv data/weather_*.csv data/pjm_hourly.csv`.
- Then: `python3 src/grids.py` (see §10 — *not* `python -I`), `python3 -W ignore src/multigrid.py`.
- Expect ~1.5M training rows across grids; `HistGradientBoostingRegressor` still fits in ~1–3 min per grid. This is a
  download-and-rerun job, not a compute job.
- **Risk:** older EIA files have 27 generation columns with `Hydropower and Pumped Storage` instead of the 2024
  split — `_pick()` already coalesces stems, and 2019 parsed cleanly in a spot check. Look for a step change at the
  2024 schema boundary anyway; `docs/DATA_AUDIT.md` §2 is the template for reporting it.
- **Deliverable:** `docs/experiments/long-history.md` with the ledger row, the 5-fold table, and a proposed README
  sentence. Numbers into `results/experiments/long_history/`.

---

## 5. G1 — Model the fuel mix, not the carbon number

**Why it is game-changing.** Carbon intensity is a deterministic function of something simpler and more predictable
than itself. Nuclear is near-constant, solar and wind are weather-driven, and gas/coal fill the residual of demand
minus must-run. Predicting the mix:
- gives the model the right inductive bias (one shared "net load → dispatchable share" structure instead of 12
  memorised columns),
- makes **carbon intensity under any emission-factor set** a post-hoc multiplication (§7 becomes free, and the EF
  sensitivity stops needing five retrains),
- makes **marginal** emissions computable by construction,
- produces an interpretable demo ("tomorrow at 14:00 we expect 41% solar, which is why the answer is 14:00").

**Protocol.**
1. New `src/fuelmix.py`: build per-grid hourly MW per fuel from the already-cached `data/fuel_<grid>.csv`
   (PJM/CISO/ERCO/DE exist). For GB, try NESO's `generation` endpoint for a fuel mix (verify the endpoint before
   relying on it); if unavailable, exclude GB and say so.
2. Two model variants, same split as production:
   - **(a) direct**: predict each fuel's *share* 76 h ahead; reconcile to sum 1 (clip ≥ 0, renormalise);
     `CI = Σ share_f × EF_f`.
   - **(b) physics-first**: forecast net load (demand − wind − solar) and VRE separately, then split the residual
     across gas/coal with a learned (or lagged-share) rule.
3. Report hourly MAE **and** the decision metric against the production model, with the same bootstrap.
4. **Kill rule:** WIN needs variant (a) or (b) to beat production by an interval below zero at both 24 h and 72 h in
   ≥ 3 of 4 fuel-mix grids (GB excluded). Any single grid significantly worse → LOSS, keep production.
5. **Deliverable:** `docs/experiments/fuelmix-target.md`, `results/experiments/fuelmix/`, and if it wins,
   `src/multigrid.py` gains a `MODE = "fuelmix"` branch with production untouched as default.

**Effort:** 2–3 h including a first run. **Risk:** medium (share models can be worse for coal/gas switching on cold
snaps); the kill rule protects you, and a documented LOSS with an interpretable failure is worth points under
"testing and honesty".

---

## 6. G2 — Zero-shot transfer to a grid nobody trained on

**Why it is game-changing.** The current "does it travel?" test retrains on each grid. A real generalization claim is
*no training at all*: train on four grids (or four years of one grid) and forecast a fifth that the model has never
seen. It answers the brief's own suggested question ("test whether your model still works on data from a different
source") better than any team that only re-runs the tutorial, and it is nearly free — EIA-930 already contains every
US balancing authority in the file they download.

**Protocol.**
1. Pick 2–3 unseen BAs with clean data and different mixes, e.g. `MISO`, `ISNE`, `NYIS`, `SWPP` (verify column
   presence and coverage 2016–2026 in the same six-month files).
2. **Leave-one-grid-out** on the existing five: train on 4, score the 5th, rotate. Report per-grid degradation vs the
   grid-specific model.
3. **Cold-start** on the unseen BAs: shared model with a grid-ID embedding; for the unseen BA use a *learned
   embedding inferred from its first 7 days only* (or the mean embedding, stated plainly).
4. **Kill rule:** no accuracy claim unless the unseen BA beats persistence and climatology at 24 h and 72 h. If it
   only ties persistence, that is the honest finding — and it is still a better transfer result than "we retrained
   per grid".
5. **Deliverable:** `docs/experiments/zero-shot.md` + a single table: grid, trained-on, 24 h model/clim/persist/oracle.

**Effort:** 1.5–2 h with H1 done (data already local). **Risk:** low; even a negative result is a strong slide.

---

## 7. G3 — Marginal emissions, properly (the quantity the data-center user actually needs)

**Why it is game-changing.** A 10 MW load does not consume "the average"; it moves the marginal plant, which is almost
always gas or coal (their own proxy: VA 466, CA 267, TX 551, DE 635 g/kWh vs averages of ~348/175/311/309). Their
coarse proxy (one constant per season × 6 h block) already **flipped the sign in Texas and Germany**. Resolving that
flip is a genuine research-grade contribution and it changes the product: for an operator, average intensity is the
wrong number, and saying so is exactly the "own question" the brief rewards.

**Protocol.**
1. Upgrade `src/experiments/estimated_marginal/run.py` from season×6 h constants to a **rolling regression**: for each
   hour t, regress Δ(fuel MW) on Δ(net load) over a trailing 90-day window (hour-of-day × season pooled, ridge, negative
   slopes clipped to zero, shares renormalised). Fit only on data before each scoring day.
2. Validate the economic story, not just the fit: the identified marginal fuel should be gas overnight and in
   shoulder months, coal on cold-snap peaks in PJM, and the marginal CI should be *high and volatile* — check it against
   the known merit order. Report where it disagrees with itself.
3. Re-run the full decision (`best_start` over marginal CI instead of average CI) and report: does the cleanest window
   by marginal differ from the cleanest by average, on what share of days, and by how many g/kWh?
4. **Kill rule:** a marginal claim needs a **direction that is stable across ≥ 3 of 4 quarters** in a grid. Unstable →
   report "average and marginal disagree on X% of days; we do not know which is right for this grid" — which is itself
   the honest and useful answer.
5. **Deliverable:** `docs/experiments/marginal-v2.md` + `results/experiments/marginal_v2/`. One sentence in README
   Limits updated only if stable.

**Effort:** 2 h. **Risk:** medium-high (this is the most likely place to find "the effect is not there"). Highest
technical-depth payoff at finals.

---

## 8. G4 — Decide under uncertainty (make the abstention rule work)

**Why it is game-changing.** The tool's weakest user-facing moment is a day when the advice is worse than doing
nothing (8% of Virginia days, 13–15% in Britain). Their two attempts at an "unsure" rule failed because they only had
a point forecast — a threshold on a point forecast cannot know it is wrong. A *calibrated distribution* can: choose the
window minimising expected cost, report the probability it is actually best, and abstain when that probability is low.

**Protocol.**
1. Build a **predictive ensemble**: 5 seeds × {production GBM, HorizonTransformer (already on
   `origin/exp/torch-transformer`)} + the history-only model. Cheap: the transformer is written and 3-seed results
   already exist; add seeds, not architectures (§3 closed door).
2. **Conformalise** the ensemble spread on 2025-H2 only: produce per-window prediction intervals with a guarantee of
   nominal coverage; report empirical coverage on 2026 (must be ≈ 80/95%, or say it failed).
3. Decision rule: pick argmin of the ensemble mean; abstain to "run now" if `P(best window beats now by > margin) < p*`,
   with `p*` and `margin` tuned on Jan–Apr 2026 and scored once on May–Nov 2026 (same protocol as
   `regret-aware-advice.md`, so results are directly comparable).
4. **Kill rule:** reuse E2's — harmful days must fall with an interval below zero *and* mean cost rise < 0.5 g/kWh, in
   ≥ 3 of 5 grids. If it fails again, that is a clean, publishable negative result, and the write-up gets one honest
   sentence plus "we tried twice".
5. **Deliverable:** `docs/experiments/calibrated-abstain.md` with a calibration plot (predicted vs realised coverage)
   and a `harmful_days` table.

**Effort:** 2–3 h. **Risk:** medium. Payoff: a real user-facing feature ("this one is a coin flip, run it whenever")
plus calibration, which is a strong finals answer.

---

## 9. G5 — The long training run (what to do with the GPU)

Only after H1 and G1 land, and only if ≥ 2.5 h remain before 23:00. One script, one result, no exploration.

`src/experiments/bigmodel/run.py` — a single model that combines everything the evidence already supports:

- **Inputs:** 11 years (H1), all 5 grids + 2–3 unseen BAs (§6), richer weather
  (`wind_speed_100m`, `direct_normal_irradiance`, `precipitation`, `surface_pressure`, `snowfall` — new information,
  unlike the fuel-share lags V2 already tried), calendar/holidays, `dem_fcst`, trailing ramp features (`ci` differences
  at −1, −2, −6 h).
- **Targets:** auxiliary fuel-share head (§5) + primary CI head, direct 76-hour multi-output, delta from the 7-day
  same-hour baseline (keep their fix — it is correct).
- **Losses:** Huber on the level + ListNet soft-choice over window starts at 12/24/72 h (the torch branch already has
  this, `LAMBDA = 1.0`, `TAU = 0.1` — reuse, do not re-tune).
- **Ensemble:** 5 seeds, average in *level* space; report spread as the uncertainty input to §8.
- **Compute:** Apple MPS is available (torch 2.8.0, verified); a 76-token, 2-layer, d=64 encoder over ~1.5M rows is
  **minutes per seed**, not hours. Use Colab T4 only if the local run is interrupted. Do not start a multi-hour job at
  21:00 — there is no notification when it finishes.
- **Protocol:** epochs chosen on 2025-H2 only; refit on everything; **score 2026 once**. Same bootstrap, same days.
- **Kill rule:** adopt only if it beats *both* production and the plain HorizonTransformer with an interval below zero
  at 24 h and 72 h in ≥ 3 of 5 grids. Otherwise ship the transformer branch alone (it wins Virginia 4/4).

---

## 10. Operating rules (non-negotiable)

**Environment (this machine differs from the runbook).** `python -I` **breaks**: the dependencies live in
`~/Library/Python/3.9/lib/python/site-packages` (Python 3.9.6), which `-I` ignores, so `scripts/check.py` dies on
`import pandas` (and `gradio` is not installed at all). Use a venv:

```bash
cd repo
python3 -m venv .venv
.venv/bin/pip -q install -r requirements.txt
.venv/bin/python src/grids.py                     # data caches (not `python -I`)
.venv/bin/python -W ignore src/multigrid.py       # headline numbers
.venv/bin/python -W ignore scripts/check.py       # merge gate
```
Pin nothing else; `torch` 2.8.0 (`mps=True`), `lightgbm` 4.6.0 are already present, `xgboost` is not.

**Git.** Same discipline as `tasks.md`: `main` must always print `ALL CHECKS PASSED`; every experiment on
`exp/<name>` created from latest `main`; one model-changing branch at a time; never force-push. A branch that touches
`README.md`, `results/*.csv`, `app/` or `notebooks/` is a **merge-time** change by the owner of those files, not by the
experimenter.

**Numbers.** No number enters `README.md` or `submission/FORM_ANSWERS.md` unless it exists in a committed CSV under
`results/`. `scripts/check.py` enforces four of them; extend it (§12) rather than trusting prose.

**Leakage.** Features at the 18:00 decision hour only; targets strictly later; climatology from train years only;
thresholds tuned on validation, then scored once; no shuffling; no interpolation; drop days with missing target hours.
Any new feature must state its availability at 18:00 in `docs/DATA_AUDIT.md` — especially weather (the Open-Meteo
"historical forecast" archive is mildly optimistic in lead time, already flagged).

**Time.** Clock is the constraint, not compute. Freeze model changes at **21:30 ET**, submit by **22:30**, leave the
last hour for incognito link checks. Each task is timeboxed: if a task exceeds 2× its estimate, write the protocol into
`docs/experiments/` with no results and stop.

**Integrity.** All work inside Nov 14–15. Do not train anything you will present after 23:59 tonight. Do not describe
a planned experiment in the past tense.

---

## 11. Execution order and time budget (from 16:30 ET)

| # | Task | Wall clock | Cumulative | Points it buys |
|---|---|---|---|---|
| 0 | `python -m venv`, install, rebuild data caches, `check.py` green | 15 min | 16:45 | protects everything |
| 1 | **H1** long history: loaders, 5-fold backtest, ledger doc | 90 min | 18:15 | Technical depth; kills "one year" criticism |
| 2 | **H2** GB forecast fusion (blend own + NESO, tune on 2025-H2, score once) | 25 min | 18:40 | The one incumbent comparison they currently lose |
| 3 | Merge `origin/exp/torch-transformer` (VA 4/4, ERCO-mse 4/4); update README numbers via owner | 30 min | 19:10 | Model depth at finals; 1.0–2.6 g/kWh in VA |
| 4 | **G1** fuel-mix target | 120 min | 21:10 | Originality; unlocks G3 and EF-free sensitivity |
| 5 | **G2** zero-shot transfer (§6) | 60 min | 22:10 | Creativity + impact; "we tested a grid we never trained on" |
| 6 | **G3** marginal v2 | 120 min | — | Technical depth (parallel; only if a second agent is free) |
| 7 | **G4** calibrated abstention | 150 min | — | Impact; fixes the "harmful days" weakness |
| 8 | **G5** big model | 90 min | — | Only if 1–5 all landed and ≥ 2.5 h remain |

**If you have only 90 minutes:** do 0, 1, 2 and merge 3. That is the highest points-per-hour set, and it keeps the
submission's numbers reproducible.
**If you have three hours:** add G1 and G2. Do not start G3–G5 (they need a second agent or a calmer clock).
**Parallelisation:** G3 and G4 are independent of G1 and can run in a second worktree. H1 must finish before G2 and G5.

---

## 12. Hygiene the plan assumes

- `scripts/check.py`: extend the gate to assert that (a) every number in the README's Virginia table matches
  `multigrid_summary.csv` **for every delay**, not just 24 h, and (b) each `docs/experiments/*.md` with a verdict also
  has a matching CSV. Cheap insurance against a judge spotting a stale number.
- `results/experiments/LEGER.md` (new): one row per experiment —
  `date | branch | question | protocol | kill rule | verdict | delta g/kWh [95% CI] | adopted? | doc`.
  This is the artefact that makes "we tried eleven things and here is what happened" credible in a two-minute demo.
- `README.md`: the brief asks for **about one page**. The current draft is ~1,700 words. Keep the takeaway box, the
  Virginia table, one transfer table, one limitations block; move the rest into `docs/`. This is worth more points
  than any single model tweak and costs 20 minutes — but it is the write-up owner's call, not an agent's.
- `submission/FORM_ANSWERS.md` still has `<ADD>` for three emails and a placeholder video link. Those are
  unrecoverable after 23:59 and outrank every modelling task in this document.

---

## 13. What the write-up should say after this plan

Keep the finding they already have — it is the best sentence in the repo — and add the two new legs:

> A better forecast is not automatically a better choice: in Virginia, training the model to rank hours instead of
> predict levels captured 91% of the best possible saving against 85% for the plain model, and that gain appeared only
> in the flattest of five grids.
>
> We then tested the two obvious escapes from that ceiling. More data: eleven years instead of three, across five
> market regimes. Different quantity: marginal instead of average emissions, which is what a data-center load actually
> changes — and which disagrees with the average-based advice on a stated share of days in Texas and Germany. What is
> left is small and we say so: with perfect foresight the Virginia decision would improve by 1.3%.

That is a mature, defensible, and much deeper project than "our model saves 6.9%", and it is the version that survives
a finals Q&A from researchers.
