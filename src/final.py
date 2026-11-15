"""Final analysis: model vs persistence CI, the 'unsure, run now' rule, failure cases, figures.
Needs results/test_predictions.pkl from sweep.py. Run from carbon/:  python -I -W ignore src/final.py
"""
import json
import sys

import joblib
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "src")
from load_data import carbon_intensity  # noqa: E402
from sweep import (JOB, NT, SLIPS, TEST_START, WX, best_start, block_boot, build_rows, fit,  # noqa: E402
                   load_all, window_cost)

VAL_START = pd.Timestamp("2025-07-01")


def choose_start(profile, slip, tau):
    """Return (start, acted). Slip only if predicted saving vs starting now exceeds tau g/kWh."""
    c = np.convolve(profile, np.ones(JOB) / JOB, mode="valid")[:slip + 1]
    st = int(np.argmin(c))
    if c[0] - c[st] < tau:
        return 0, False
    return st, True


def eval_tau(df, col, slip, tau):
    tot, acted, harm = [], 0, 0
    for _, grp in df.groupby("day"):
        grp = grp.sort_values("j")
        y = grp["y"].values
        st, a = choose_start(grp[col].values, slip, tau)
        tot.append(window_cost(y, st))
        acted += a
        harm += window_cost(y, st) > window_cost(y, 0) + 1e-9
    n = len(tot)
    return np.mean(tot), acted / n, harm / n


def main():
    g, w = load_all()
    ci = carbon_intensity(g)
    data = build_rows(g, w, ci)
    data["day"] = pd.to_datetime(data["day"])
    feats_hist = ["lead", "hour", "dow", "month", "ci_same_hr", "ci_same_hr_wk",
                  "ci_hod_mean7d", "ci_mean24", "ci_mean7d", "ci_last"]
    feats = feats_hist + ["dem_fcst", "dom_dem_same_hr"] + WX
    te = pd.read_pickle("results/test_predictions.pkl")
    costs = pd.read_csv("results/per_day_costs.csv", index_col=0, parse_dates=True)

    # 1) model vs persistence, paired block bootstrap (the stricter comparison at short slips)
    print("Model minus PERSISTENCE (g/kWh, negative = model better), block-bootstrap 95% CI")
    pers = {}
    for slip in SLIPS[1:]:
        d = (costs[f"model_{slip}"] - costs[f"persistence_{slip}"]).values
        lo, hi = block_boot(d)
        dh = (costs[f"model_hist_{slip}"] - costs[f"persistence_{slip}"]).values
        l2, h2 = block_boot(dh)
        pers[slip] = dict(mean=d.mean(), lo=lo, hi=hi, pct_days=100 * (d < 0).mean(),
                          hist_mean=dh.mean(), hist_lo=l2, hist_hi=h2)
        print(f"  slip {slip:2d}h full: {d.mean():+6.2f} [{lo:+6.2f},{hi:+6.2f}] better on "
              f"{100*(d<0).mean():.0f}% of days | history-only: {dh.mean():+6.2f} [{l2:+6.2f},{h2:+6.2f}]")

    # 2) 'unsure, run now' threshold: tuned on VALIDATION (2025-H2), applied once to TEST
    tr_early = data[(data.day < VAL_START) & data.y.notna()]
    va = data[(data.day >= VAL_START) & (data.day < TEST_START)]
    va = va[va.groupby("day")["y"].transform(lambda v: v.notna().all() and len(v) == NT)].copy()
    m_early = fit(tr_early, feats)
    va["pred"] = m_early.predict(va[feats])
    taus = [0, 2, 4, 6, 8, 10, 15, 20]
    abst = {}
    print("\n'Unsure, run now' rule. tau tuned on val (2025-07..12), then applied to test.")
    for slip in [24, 72]:
        best = None
        rows = []
        for t in taus:
            c, a, h = eval_tau(va, "pred", slip, t)
            rows.append((t, c, a, h))
            if best is None or c < best[1] - 1e-9:
                best = (t, c)
        # choose smallest tau within 0.3 g/kWh of the best val cost (prefer abstaining more)
        tau = max(t for t, c, a, h in rows if c <= best[1] + 0.3)
        c0, a0, h0 = eval_tau(te, "pred", slip, 0)
        c1, a1, h1 = eval_tau(te, "pred", slip, tau)
        abst[slip] = dict(tau=tau, cost_no_abstain=c0, acted0=a0, harm0=h0,
                          cost_abstain=c1, acted=a1, harm=h1)
        print(f"  slip {slip}h: tau={tau} g/kWh | TEST no-abstain cost {c0:.2f}, acts {100*a0:.0f}% days, "
              f"worse-than-immediate {100*h0:.0f}% | with-abstain cost {c1:.2f}, acts {100*a1:.0f}%, "
              f"worse-than-immediate {100*h1:.0f}%")

    # 3) failure analysis: 3 worst days at slip 24 (model cost minus oracle cost)
    slip = 24
    rg = (costs[f"model_{slip}"] - costs[f"oracle_{slip}"]).sort_values(ascending=False)
    fails = []
    print(f"\nWorst model days at slip {slip}h (regret = chosen minus best possible window):")
    for day in rg.index[:3]:
        grp = te[te.day == day].sort_values("j")
        y, p = grp["y"].values, grp["pred"].values
        st_m, st_o = best_start(p, slip), best_start(y, slip)
        info = dict(day=str(day.date()), regret=round(float(rg[day]), 1), model_start=st_m,
                    oracle_start=st_o,
                    chosen_ci=round(float(window_cost(y, st_m)), 1), best_ci=round(float(window_cost(y, st_o)), 1),
                    immediate_ci=round(float(window_cost(y, 0)), 1),
                    mean_temp=round(float(grp["temperature_2m"].iloc[:30].mean()), 1),
                    mean_wind=round(float(grp["wind_speed_10m"].iloc[:30].mean()), 1),
                    pred_mae=round(float(np.abs(y - p).mean()), 1))
        fails.append(info)
        print("  ", info)

    # 4) figures
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
    S = pd.read_csv("results/sweep_summary.csv")
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(S) - 1) ; wd = 0.2
    for i, (c, lab, col) in enumerate([("persistence_%saved", "persistence", "#9aa5b1"),
                                       ("climatology_%saved", "climatology (hour-of-week)", "#d9822b"),
                                       ("model_%saved", "model", "#1f6f5c"),
                                       ("oracle_%saved", "perfect foresight", "#333")]):
        ax.bar(x + (i - 1.5) * wd, S[c].iloc[1:], wd, label=lab, color=col)
    ax.set_xticks(x); ax.set_xticklabels([f"{s}h" for s in S.slip_h.iloc[1:]])
    ax.set_xlabel("how long the job may be delayed"); ax.set_ylabel("% CO2 saved vs run-immediately")
    ax.set_title("Test 2026: carbon saved by a 4-hour flexible job"); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig("results/savings_by_slip.png", dpi=130); plt.close(fig)

    fig, axs = plt.subplots(1, 3, figsize=(13, 3.4), sharey=True)
    for a, f in zip(axs, fails):
        grp = te[te.day == pd.Timestamp(f["day"])].sort_values("j").iloc[:48]
        a.plot(grp["j"], grp["y"], color="#222", label="actual")
        a.plot(grp["j"], grp["pred"], color="#1f6f5c", label="model")
        a.plot(grp["j"], grp["clim"], color="#d9822b", ls=":", label="climatology")
        a.axvspan(f["model_start"], f["model_start"] + JOB, color="#1f6f5c", alpha=.15)
        a.axvspan(f["oracle_start"], f["oracle_start"] + JOB, color="#333", alpha=.12)
        a.set_title(f"{f['day']} (regret {f['regret']} g/kWh)", fontsize=9); a.set_xlabel("hours after midnight")
    axs[0].set_ylabel("gCO2/kWh"); axs[0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig("results/failure_days.png", dpi=130); plt.close(fig)

    # 5) save the final model (trained on 2023-2025 only) for the demo
    tr = data[(data.day < TEST_START) & data.y.notna()]
    joblib.dump({"model": fit(tr, feats), "feats": feats}, "results/final_model.joblib")
    json.dump({"vs_persistence": pers, "abstain": abst, "failures": fails},
              open("results/final_summary.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
