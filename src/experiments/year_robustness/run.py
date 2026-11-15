"""E4: are the conclusions a quirk of 2026? Train 2023-2024, test ALL of 2025 (never shuffled).

Same recipe and fixed settings as src/multigrid.py (change-target gradient boosting, hour-of-week average from
the training years only, persistence, perfect hindsight); only the split changes.
Run from repo root: python -I -W ignore src/experiments/year_robustness/run.py
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from grids import GRIDS, load_grid_data  # noqa: E402
from multigrid import HIST, build_rows_g, fit_delta, predict_delta  # noqa: E402
from sweep import NT, SLIPS, WX, best_start, block_boot, window_cost  # noqa: E402

TRAIN_END, TEST_START, TEST_END = pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01"), pd.Timestamp("2026-01-01")
OUT = "results/experiments/year_robustness"


def run(key):
    name, tz, _ = GRIDS[key]
    g, w = load_grid_data(key)
    data = build_rows_g(g, w, tz)
    feats = HIST + (["dem_fcst"] if data["dem_fcst"].notna().any() else []) + WX
    tr = data[(data.day < TRAIN_END) & data.y.notna()]
    te = data[(data.day >= TEST_START) & (data.day < TEST_END)]
    ok = te.groupby("day")["y"].apply(lambda v: v.notna().all() and len(v) == NT)
    te = te[te.day.isin(ok[ok].index)].copy()
    te["pred"] = predict_delta(fit_delta(tr, feats), te, feats)
    clim = tr.groupby(["dow", "hour"])["y"].mean()
    te["clim"] = clim.reindex(pd.MultiIndex.from_frame(te[["dow", "hour"]])).values
    te["persist"] = te["ci_same_hr"]
    recs = {}
    for day, grp in te.groupby("day"):
        grp = grp.sort_values("j"); y = grp.y.values; r = {}
        for slip in SLIPS[1:]:
            r[f"imm_{slip}"] = window_cost(y, 0)
            r[f"oracle_{slip}"] = window_cost(y, best_start(y, slip))
            for n, c in [("persistence", "persist"), ("climatology", "clim"), ("model", "pred")]:
                r[f"{n}_{slip}"] = window_cost(y, best_start(grp[c].values, slip))
        recs[day] = r
    c = pd.DataFrame(recs).T
    rows = []
    for slip in SLIPS[1:]:
        imm = c[f"imm_{slip}"].mean()
        row = {"grid": key, "region": name, "test_year": 2025, "days": len(c), "slip_h": slip, "immediate": imm}
        for n in ["persistence", "climatology", "model", "oracle"]:
            row[n] = c[f"{n}_{slip}"].mean(); row[f"{n}_pct_saved"] = 100 * (imm - row[n]) / imm
        for b in ["climatology", "persistence"]:
            d = (c[f"model_{slip}"] - c[f"{b}_{slip}"]).values.astype(float)
            lo, hi = block_boot(d, n=3000)
            row[f"model_minus_{b}"], row[f"model_minus_{b}_lo"], row[f"model_minus_{b}_hi"] = d.mean(), lo, hi
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    res = pd.concat([run(k) for k in GRIDS]).round(2)
    res.to_csv(f"{OUT}/year_robustness_2025.csv", index=False)
    pd.set_option("display.width", 250)
    for sl in (24, 72):
        print(f"--- test = 2025, slip {sl} h")
        print(res[res.slip_h == sl][["region", "days", "immediate", "persistence", "climatology", "model", "oracle",
                                      "model_pct_saved", "model_minus_climatology", "model_minus_climatology_lo",
                                      "model_minus_climatology_hi", "model_minus_persistence",
                                      "model_minus_persistence_lo", "model_minus_persistence_hi"]].to_string(index=False))
