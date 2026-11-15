"""Experiment: train a small second-stage model for the DECISION (which hours are cleanest),
not for the hourly level.

Why: on the 2026 test the main model has much lower hourly error than persistence (MAE 13.8 vs
21.5 g/kWh) but picks the cleanest 4 hours of tomorrow LESS often (51% vs 54%). Its training loss
rewards getting the level right; the scheduler only needs the order of the hours.

How (honest split, no raw data needed): inputs are the saved forecasts of the first-stage models
(trained on 2023-2025, never saw 2026) plus calendar/weather columns in test_predictions.csv.gz.
Target = each hour's carbon intensity minus that day's 76-hour mean (the "shape").
Rolling origin: to score month m (May..Nov 2026), the stacker is trained only on 2026 days
before month m. Jan-Apr 2026 is never scored. Nothing from the future is used.
Run from the repo root:  python -I src/experiments/decision_stack.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

JOB, SLIPS = 4, [12, 24, 48, 72]
OUT = "results/experiments"
BASE = {"persistence": "persist", "climatology": "clim", "model": "pred", "model_history_only": "pred_hist"}


def best_start(p, slip):
    c = np.convolve(p, np.ones(JOB) / JOB, mode="valid")
    return int(np.argmin(c[:slip + 1]))


def block_boot(x, block=7, n=5000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    nb = int(np.ceil(len(x) / block))
    starts = np.arange(len(x) - block + 1)
    m = [np.concatenate([x[a:a + block] for a in rng.choice(starts, nb)])[:len(x)].mean() for _ in range(n)]
    return np.percentile(m, [2.5, 97.5])


def add_feats(te):
    te = te.sort_values(["day", "j"]).copy()
    ts = te["day"] + pd.to_timedelta(te["j"], unit="h")
    te["hod"], te["dow"], te["month"] = ts.dt.hour, ts.dt.dayofweek, ts.dt.month
    te["weekend"] = (te["dow"] >= 5).astype(int)
    for c in ["pred", "pred_hist", "clim", "persist"]:
        te[f"{c}_dev"] = te[c] - te.groupby("day")[c].transform("mean")
    te["pred_minus_persist"] = te["pred"] - te["persist"]
    te["y_dev"] = te["y"] - te.groupby("day")["y"].transform("mean")
    return te


FEATS = ["j", "hod", "dow", "weekend", "pred_dev", "pred_hist_dev", "clim_dev", "persist_dev",
         "pred_minus_persist", "temperature_2m", "wind_speed_10m"]


def main():
    te = add_feats(pd.read_csv("results/test_predictions.csv.gz", parse_dates=["day"]))
    te["stack"] = np.nan
    te["avg3"] = (te["pred_dev"] + te["pred_hist_dev"] + te["persist_dev"]) / 3  # no training at all
    months = range(5, 12)
    for m in months:
        start = pd.Timestamp(f"2026-{m:02d}-01")
        tr = te[te.day < start]
        sc = te[(te.day >= start) & (te.day < start + pd.offsets.MonthBegin(1))]
        mdl = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=4,
                                            min_samples_leaf=50, l2_regularization=1.0, random_state=0)
        mdl.fit(tr[FEATS], tr["y_dev"])
        te.loc[sc.index, "stack"] = mdl.predict(sc[FEATS])
    ev = te[te.day >= "2026-05-01"].copy()
    cols = {**BASE, "average of 3 (no training)": "avg3", "decision stacker": "stack"}

    rows, rk = [], []
    for day, g in ev.groupby("day"):
        y = g["y"].values
        r = {"day": day, "immediate": y[:JOB].mean()}
        for slip in SLIPS:
            r[f"oracle_{slip}"] = y[best_start(y, slip):][:JOB].mean()
            for n, c in cols.items():
                s = best_start(g[c].values, slip)
                r[f"{n}_{slip}"] = y[s:s + JOB].mean()
        rows.append(r)
        g24 = g[g.j < 24]
        k = {"day": day}
        for n, c in cols.items():
            k[n] = np.corrcoef(g24["y"].rank(), g24[c].rank())[0, 1]
            k[f"{n}_top4"] = len(set(g24.nsmallest(4, "y").j) & set(g24.nsmallest(4, c).j)) / 4
        rk.append(k)
    dc = pd.DataFrame(rows).set_index("day")
    rk = pd.DataFrame(rk)

    out = []
    for slip in SLIPS:
        imm, orc = dc["immediate"].mean(), dc[f"oracle_{slip}"].mean()
        for n in cols:
            v = dc[f"{n}_{slip}"].mean()
            d = (dc[f"{n}_{slip}"] - dc[f"persistence_{slip}"]).values
            lo, hi = block_boot(d)
            d2 = (dc[f"{n}_{slip}"] - dc[f"model_{slip}"]).values
            lo2, hi2 = block_boot(d2)
            out.append({"slip_h": slip, "method": n, "g_per_kWh": v, "saved_vs_run_now_%": 100 * (imm - v) / imm,
                        "captures_%_of_perfect": 100 * (imm - v) / (imm - orc),
                        "minus_persistence": d.mean(), "mp_lo": lo, "mp_hi": hi,
                        "minus_model": d2.mean(), "mm_lo": lo2, "mm_hi": hi2})
    out = pd.DataFrame(out)
    rank = pd.DataFrame({"method": list(cols), "spearman_tomorrow": [rk[n].mean() for n in cols],
                         "cleanest4_hit_%": [100 * rk[f"{n}_top4"].mean() for n in cols]})
    pd.set_option("display.width", 250)
    print(f"Scored May-Nov 2026 only: {len(dc)} days (rolling-origin, stacker retrained each month)")
    print(out.round(2).to_string(index=False))
    print(rank.round(3).to_string(index=False))
    out.round(3).to_csv(f"{OUT}/decision_stack.csv", index=False)
    rank.round(4).to_csv(f"{OUT}/decision_stack_ranking.csv", index=False)
    ev[["day", "j", "y", "stack", "avg3"]].round(3).to_csv(f"{OUT}/stack_predictions.csv.gz", index=False)


if __name__ == "__main__":
    main()
