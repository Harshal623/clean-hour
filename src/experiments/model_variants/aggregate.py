"""Aggregate raw variant runs into one table and apply the pre-set kill rule.

Kill rule (set before any 2026 scoring): a variant is a WIN in a grid only if (a) it beat the baseline settings on 2025-H2 validation
by more than 0.1 g/kWh (so it was selected without the test), and (b) its 2026 test cost minus the baseline's cost has a 95% 7-day
block-bootstrap interval entirely below zero at BOTH 24 h and 72 h. Overall WIN needs >= 3 of 5 grids. Otherwise TIE (no grid is
significantly worse) or LOSS (a grid is significantly worse at either delay). Run: python -I -W ignore src/experiments/model_variants/aggregate.py
"""
import glob
import json

import pandas as pd

NAMES = {"pjm": "Virginia", "ciso": "California", "erco": "Texas", "de": "Germany", "gb": "Great Britain"}
rows = []
for f in sorted(glob.glob("results/experiments/model_variants/raw/*.json")):
    d = json.load(open(f))
    t24, t72 = d["test"]["24"], d["test"]["72"]
    win = bool(d["adopted_on_validation"] and t24["hi"] < 0 and t72["hi"] < 0)
    worse = bool(t24["lo"] > 0 or t72["lo"] > 0)
    rows.append(dict(variant=d["variant"], grid=d["grid"], region=NAMES[d["grid"]],
                     adopted_on_validation=d["adopted_on_validation"], test_days=d["test_days"],
                     base_24=t24["base"], var_24=t24["variant"], diff_24=t24["diff"], lo_24=t24["lo"], hi_24=t24["hi"],
                     base_72=t72["base"], var_72=t72["variant"], diff_72=t72["diff"], lo_72=t72["lo"], hi_72=t72["hi"],
                     grid_win=win, significantly_worse=worse))
R = pd.DataFrame(rows).round(3)
R.to_csv("results/experiments/model_variants/model_variants_summary.csv", index=False)
pd.set_option("display.width", 250)
print(R[["variant", "region", "adopted_on_validation", "diff_24", "lo_24", "hi_24", "diff_72", "lo_72", "hi_72",
         "grid_win", "significantly_worse"]].to_string(index=False))
print()
for v, g in R.groupby("variant"):
    wins, worse = int(g.grid_win.sum()), int(g.significantly_worse.sum())
    verdict = "WIN" if wins >= 3 else ("LOSS" if worse >= 1 else "TIE")
    print(f"{v}: wins in {wins}/5 grids, significantly worse in {worse}/5, adopted on validation in "
          f"{int(g.adopted_on_validation.sum())}/5 -> {verdict}")
