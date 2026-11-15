"""E1: does "train for the decision, not the number" transfer beyond Virginia?

Sidharth's decision stacker (src/experiments/decision_stack.py) was built on Virginia only. Here the same
recipe, with the same fixed configuration, is applied to all five grids.

Recipe: a small second-stage model learns the SHAPE of the next 76 hours (each hour minus that day's mean)
from the first-stage forecasts (full model, history-only model), persistence, hour-of-week average,
calendar and weather. Rolling origin: to score month m (May..Nov 2026) it trains only on 2026 days
before m. Jan-Apr 2026 is never scored. First-stage models were trained on 2023-2025 only.

Run from the repo root (needs results/test_predictions_all_ext.csv.gz from src/multigrid.py):
    python -I -W ignore src/experiments/decision_focused_grids/run.py
Kill rule (set before running): the stacker "wins" in a grid only if stacker minus first model has a 95%
block-bootstrap interval entirely below zero at 24 h and at 72 h. Overall WIN needs >= 3 of 5 grids.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, "src/experiments")
from decision_stack import JOB, SLIPS, add_feats, best_start, block_boot  # noqa: E402

OUT = "results/experiments/decision_focused_grids"
NAMES = {"pjm": "Virginia", "ciso": "California", "erco": "Texas", "de": "Germany", "gb": "Great Britain"}
FEATS = ["j", "hod", "dow", "weekend", "pred_dev", "pred_hist_dev", "clim_dev", "persist_dev",
         "pred_minus_persist", "temperature_2m", "wind_speed_10m", "shortwave_radiation", "cloud_cover"]
METHODS = {"persistence": "persist", "climatology": "clim", "model": "pred",
           "model_history_only": "pred_hist", "average of 3 (no training)": "avg3", "decision stacker": "stack"}


def run_grid(te):
    te = te.copy()
    te["persist"] = te["persist"].fillna(te["pred"])  # one or two missing-hour rows
    te = add_feats(te)
    te["stack"] = np.nan
    te["avg3"] = (te["pred_dev"] + te["pred_hist_dev"] + te["persist_dev"]) / 3
    for m in range(5, 12):
        start = pd.Timestamp(f"2026-{m:02d}-01")
        tr = te[te.day < start]
        sc = te[(te.day >= start) & (te.day < start + pd.offsets.MonthBegin(1))]
        if sc.empty:
            continue
        mdl = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=4,
                                            min_samples_leaf=50, l2_regularization=1.0, random_state=0)
        mdl.fit(tr[FEATS], tr["y_dev"])
        te.loc[sc.index, "stack"] = mdl.predict(sc[FEATS])
    ev = te[(te.day >= "2026-05-01") & te["stack"].notna()]
    rows = []
    for day, g in ev.groupby("day"):
        g = g.sort_values("j")
        if len(g) < 76:
            continue
        y = g["y"].values
        r = {"day": day, "immediate": y[:JOB].mean()}
        for slip in SLIPS:
            r[f"oracle_{slip}"] = y[best_start(y, slip):][:JOB].mean()
            for n, c in METHODS.items():
                s = best_start(g[c].values, slip)
                r[f"{n}_{slip}"] = y[s:s + JOB].mean()
        rows.append(r)
    return pd.DataFrame(rows).set_index("day")


def main():
    df = pd.read_csv("results/test_predictions_all_ext.csv.gz", parse_dates=["day"])
    out, wins = [], {}
    for g, grp in df.groupby("grid"):
        dc = run_grid(grp.drop(columns="grid"))
        for slip in SLIPS:
            imm, orc = dc["immediate"].mean(), dc[f"oracle_{slip}"].mean()
            for n in METHODS:
                v = dc[f"{n}_{slip}"].mean()
                d_m = (dc[f"{n}_{slip}"] - dc[f"model_{slip}"]).values
                d_p = (dc[f"{n}_{slip}"] - dc[f"persistence_{slip}"]).values
                lo_m, hi_m = block_boot(d_m)
                lo_p, hi_p = block_boot(d_p)
                out.append({"grid": g, "region": NAMES[g], "days": len(dc), "slip_h": slip, "method": n,
                            "g_per_kWh": v, "saved_vs_midnight_pct": 100 * (imm - v) / imm,
                            "captures_pct_of_perfect": 100 * (imm - v) / (imm - orc),
                            "minus_model": d_m.mean(), "mm_lo": lo_m, "mm_hi": hi_m,
                            "minus_persistence": d_p.mean(), "mp_lo": lo_p, "mp_hi": hi_p})
    res = pd.DataFrame(out).round(3)
    res.to_csv(f"{OUT}/decision_focused_grids.csv", index=False)
    pd.set_option("display.width", 250)
    st = res[res.method == "decision stacker"]
    print("Decision stacker vs first model, scored May-Nov 2026 (g/kWh; negative = stacker better)")
    print(st[st.slip_h.isin([24, 72])][["region", "days", "slip_h", "captures_pct_of_perfect", "minus_model",
                                         "mm_lo", "mm_hi", "minus_persistence", "mp_lo", "mp_hi"]].to_string(index=False))
    cap = res[res.method.isin(["model", "persistence", "decision stacker"]) & res.slip_h.isin([24, 72])]
    print("\nShare of the perfect-foresight saving captured (%):")
    print(cap.pivot_table(index=["region", "slip_h"], columns="method", values="captures_pct_of_perfect").round(1))
    ok = st[st.slip_h.isin([24, 72])].groupby("grid").apply(lambda x: bool((x.mm_hi < 0).all()), include_groups=False)
    print("\nGrids where stacker beats first model with interval below zero at 24h AND 72h:",
          [NAMES[k] for k, v in ok.items() if v], f"({int(ok.sum())} of 5; need >= 3 for WIN)")
    return res


if __name__ == "__main__":
    main()
