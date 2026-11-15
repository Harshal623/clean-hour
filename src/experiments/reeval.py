"""Re-check the reported 2026 test numbers from the saved predictions, and add accuracy views
the write-up was missing. Needs only results/test_predictions.csv.gz (no raw data, no retraining).

Adds:
  1. Forecast accuracy: MAE, RMSE and skill vs persistence, overall and by forecast horizon.
  2. Ranking accuracy: does the forecast put the hours of each day in the right ORDER?
     (the scheduler only needs the order, not the level)
  3. Share of the perfect-foresight saving each method captures.
  4. A forward check inside 2026: blend model and persistence with a weight chosen on
     Jan-Apr 2026 only, scored on May-Nov 2026 only. Secondary analysis, labelled as such.
Run from the repo root:  python -I src/experiments/reeval.py
"""
import json

import numpy as np
import pandas as pd

JOB, SLIPS = 4, [12, 24, 48, 72]
OUT = "results/experiments"
M = {"persistence": "persist", "climatology": "clim", "model": "pred", "model_history_only": "pred_hist"}


def best_start(p, slip):
    c = np.convolve(p, np.ones(JOB) / JOB, mode="valid")
    return int(np.argmin(c[:slip + 1]))


def cost(y, st):
    return y[st:st + JOB].mean()


def day_costs(te, cols):
    rows = []
    for day, g in te.groupby("day"):
        g = g.sort_values("j")
        y = g["y"].values
        r = {"day": day, "immediate": cost(y, 0)}
        for slip in SLIPS:
            r[f"oracle_{slip}"] = cost(y, best_start(y, slip))
            for name, c in cols.items():
                r[f"{name}_{slip}"] = cost(y, best_start(g[c].values, slip))
        rows.append(r)
    return pd.DataFrame(rows).set_index("day")


def block_boot(x, block=7, n=5000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    nb = int(np.ceil(len(x) / block))
    starts = np.arange(len(x) - block + 1)
    m = [np.concatenate([x[a:a + block] for a in rng.choice(starts, nb)])[:len(x)].mean() for _ in range(n)]
    return np.percentile(m, [2.5, 97.5])


def main():
    te = pd.read_csv("results/test_predictions.csv.gz", parse_dates=["day"])
    print(f"test rows {len(te)} | days {te.day.nunique()} | {te.day.min().date()} -> {te.day.max().date()}")

    # 1) hourly accuracy by horizon. j = hours after local midnight of day D; decision is 18:00 on D-1,
    #    so j=0..23 is 'tomorrow' (6-30 h ahead), 24..47 the day after, 48..75 the third day.
    te["horizon"] = pd.cut(te.j, [-1, 23, 47, 75], labels=["day 1 (6-30 h)", "day 2 (30-54 h)", "day 3 (54-82 h)"])
    acc = []
    for name, c in M.items():
        e = te["y"] - te[c]
        for h, eh in [("all", e)] + [(h, e[te.horizon == h]) for h in te.horizon.cat.categories]:
            acc.append({"method": name, "horizon": h, "MAE": np.abs(eh).mean(), "RMSE": np.sqrt((eh ** 2).mean()),
                        "bias": -eh.mean()})
    acc = pd.DataFrame(acc)
    pm = acc[acc.method == "persistence"].set_index("horizon")["MAE"]
    acc["skill_vs_persistence_%"] = 100 * (1 - acc["MAE"] / acc["horizon"].map(pm))
    print("\nHourly forecast accuracy, gCO2/kWh (2026 test):")
    print(acc.round(2).to_string(index=False))

    # 2) ranking accuracy inside each day's first 24 h (what 'pick the cleanest window' needs)
    rk = []
    for day, g in te[te.j < 24].groupby("day"):
        r = {"day": day}
        yr = g["y"].rank().values
        for name, c in M.items():
            r[name] = np.corrcoef(yr, g[c].rank().values)[0, 1]
            r[f"{name}_top4"] = len(set(g.nsmallest(4, "y").j) & set(g.nsmallest(4, c).j)) / 4
        rk.append(r)
    rk = pd.DataFrame(rk)
    rank_tab = pd.DataFrame({"method": list(M),
                             "spearman_mean": [rk[n].mean() for n in M],
                             "cleanest4_hit_rate_%": [100 * rk[f"{n}_top4"].mean() for n in M]})
    print("\nRanking accuracy, tomorrow's 24 hours (higher is better):")
    print(rank_tab.round(3).to_string(index=False))

    # 3) scheduling metric, reproduced, plus share of perfect-foresight saving captured
    dc = day_costs(te, M)
    sched = []
    for slip in SLIPS:
        imm, orc = dc["immediate"].mean(), dc[f"oracle_{slip}"].mean()
        r = {"slip_h": slip, "run_now": imm, "perfect": orc}
        for n in M:
            v = dc[f"{n}_{slip}"].mean()
            r[n] = v
            r[f"{n}_captures_%"] = 100 * (imm - v) / (imm - orc)
        sched.append(r)
    sched = pd.DataFrame(sched)
    print("\nMean gCO2/kWh of chosen 4-h window, and % of the perfect-foresight saving captured:")
    print(sched.round(1).to_string(index=False))

    # 4) forward check inside 2026 (secondary): blend weight chosen on Jan-Apr, scored on May-Nov
    cut = pd.Timestamp("2026-05-01")
    ws = np.round(np.arange(0, 1.01, 0.1), 1)
    for w in ws:
        te[f"blend_{w}"] = w * te["pred"] + (1 - w) * te["persist"]
    te["model_avg"] = 0.5 * (te["pred"] + te["pred_hist"])
    cols = {f"blend_{w}": f"blend_{w}" for w in ws}
    cols["model_avg"] = "model_avg"
    cols.update(M)
    early = day_costs(te[te.day < cut], cols)
    late = day_costs(te[te.day >= cut], cols)
    fwd = []
    for slip in SLIPS:
        w_best = min(ws, key=lambda w: early[f"blend_{w}_{slip}"].mean())
        d = late[f"blend_{w_best}_{slip}"] - late[f"model_{slip}"]
        lo, hi = block_boot(d.values)
        dp = late[f"blend_{w_best}_{slip}"] - late[f"persistence_{slip}"]
        lo2, hi2 = block_boot(dp.values)
        fwd.append({"slip_h": slip, "w_model_chosen_on_JanApr": w_best,
                    "MayNov_model": late[f"model_{slip}"].mean(),
                    "MayNov_persistence": late[f"persistence_{slip}"].mean(),
                    "MayNov_blend": late[f"blend_{w_best}_{slip}"].mean(),
                    "MayNov_model_avg": late[f"model_avg_{slip}"].mean(),
                    "blend_minus_model": d.mean(), "ci_lo": lo, "ci_hi": hi,
                    "blend_minus_persist": dp.mean(), "ci2_lo": lo2, "ci2_hi": hi2,
                    "MayNov_days": len(late)})
    fwd = pd.DataFrame(fwd)
    print("\nForward check (weight chosen Jan-Apr 2026, scored May-Nov 2026 only):")
    print(fwd.round(2).to_string(index=False))

    acc.round(3).to_csv(f"{OUT}/accuracy_by_horizon.csv", index=False)
    rank_tab.round(4).to_csv(f"{OUT}/ranking_accuracy.csv", index=False)
    sched.round(3).to_csv(f"{OUT}/scheduling_capture.csv", index=False)
    fwd.round(3).to_csv(f"{OUT}/forward_blend_check.csv", index=False)


if __name__ == "__main__":
    main()
