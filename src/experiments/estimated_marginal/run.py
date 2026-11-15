"""E3: does shifting to the cleanest hours by AVERAGE intensity also help when judged by an estimated MARGINAL intensity?

Critics of average-emission scheduling say the right signal is the marginal plant (what changes when load
changes). Public data has no marginal rates for our grids (PJM's need an account), so we ESTIMATE a coarse
proxy with a net-load regression, in the spirit of Hawkes (2010) / Siler-Evans et al. (2012): in each
(6-hour block x season) group, regress the hourly change of each dispatchable fuel on the hourly change in
net load (generation minus wind minus solar); the slopes say which fuels move when load moves. Marginal
intensity = sum(slope x emission factor). Fitted on 2023-2025 only; evaluated on 2026 days.
This is a COARSE proxy (a daily shape per block and season), not a dispatch model.

Run from repo root (needs data/fuel_<grid>.csv from src/grids.py and results/test_predictions_all_ext.csv.gz):
    python -I -W ignore src/experiments/estimated_marginal/run.py
Britain is excluded (NESO publishes intensity, not fuel mix, in our pipeline).
"""
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "src")
from load_data import EF  # noqa: E402
from grids import GRIDS  # noqa: E402

OUT = "results/experiments/estimated_marginal"
DISPATCH = ["coal", "gas", "oil", "hydro", "nuclear", "other"]
SEASON = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}
JOB = 4


def mef_table(key):
    f = pd.read_csv(f"data/fuel_{key}.csv", index_col=0, parse_dates=True)
    f = f.reindex(pd.date_range(f.index.min().ceil("h"), f.index.max(), freq="h")).fillna(0)
    f = f.drop(columns=[c for c in ["unknown"] if c in f])
    loc = f.index.tz_localize("UTC").tz_convert(GRIDS[key][1])
    total = f.sum(axis=1)
    net = total - f.get("wind", 0) - f.get("solar", 0)
    d = pd.DataFrame({"dN": net.diff().values}, index=f.index)
    for c in DISPATCH:
        d[c] = f[c].diff().values if c in f else 0.0
    d["block"] = loc.hour // 6
    d["season"] = [SEASON[m] for m in loc.month]
    d["year"] = loc.year
    d = d.iloc[1:].dropna()
    tr = d[d.year <= 2025]
    rows = []
    for (s, b), g in tr.groupby(["season", "block"]):
        x = g["dN"].values
        beta = {}
        for c in DISPATCH:
            v = np.cov(x, g[c].values)[0, 1] / np.var(x) if np.var(x) > 0 else 0.0
            beta[c] = max(v, 0.0)  # fuels cannot have negative marginal share in this simple proxy
        tot = sum(beta.values()) or 1.0
        mef = sum(beta[c] / tot * EF[c] for c in DISPATCH)
        rows.append({"season": s, "block": b, "mef": mef, **{f"share_{c}": beta[c] / tot for c in DISPATCH}})
    return pd.DataFrame(rows)


def best_start(p, slip):
    c = np.convolve(p, np.ones(JOB) / JOB, mode="valid")
    return int(np.nanargmin(c[:slip + 1]))


def main():
    ext = pd.read_csv("results/test_predictions_all_ext.csv.gz", parse_dates=["day"])
    res, prof = [], {}
    for key in ["pjm", "ciso", "erco", "de"]:
        tab = mef_table(key).set_index(["season", "block"])
        prof[key] = tab
        rows = []
        for day, g in ext[ext.grid == key].groupby("day"):
            g = g.sort_values("j")
            if len(g) < 76:
                continue
            season = SEASON[day.month]
            mef = np.array([tab.loc[(SEASON[(day + pd.Timedelta(hours=int(j))).month], (int(j) % 24) // 6), "mef"]
                            for j in g.j])
            y = g.y.values
            s_avg, s_mef = best_start(y, 24), best_start(mef, 24)
            rows.append(dict(avg_mid=y[:JOB].mean(), avg_by_avg=y[s_avg:s_avg + JOB].mean(),
                             avg_by_mef=y[s_mef:s_mef + JOB].mean(), mef_mid=mef[:JOB].mean(),
                             mef_by_avg=mef[s_avg:s_avg + JOB].mean(), mef_by_mef=mef[s_mef:s_mef + JOB].mean(),
                             same_window=abs(s_avg - s_mef) <= 1))
        r = pd.DataFrame(rows)
        n = len(r)
        res.append(dict(grid=key, region={"pjm": "Virginia", "ciso": "California", "erco": "Texas", "de": "Germany"}[key],
                        days=n, mean_est_marginal=float(np.mean([tab.mef.mean()])),
                        avg_saved_by_avg_rule=r.avg_mid.mean() - r.avg_by_avg.mean(),
                        est_marginal_saved_by_avg_rule=r.mef_mid.mean() - r.mef_by_avg.mean(),
                        est_marginal_saved_by_marginal_rule=r.mef_mid.mean() - r.mef_by_mef.mean(),
                        avg_saved_by_marginal_rule=r.avg_mid.mean() - r.avg_by_mef.mean(),
                        pct_days_avg_rule_lowers_est_marginal=100 * float((r.mef_by_avg < r.mef_mid - 1e-9).mean()),
                        pct_days_similar_window=100 * float(r.same_window.mean())))
    R = pd.DataFrame(res).round(1)
    R.to_csv(f"{OUT}/marginal_agreement.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.to_string(index=False))
    for k, t in prof.items():
        print(k, "estimated marginal intensity by season x 6h block (gCO2/kWh):")
        print(t.mef.unstack().round(0).to_string())
    fig, axs = plt.subplots(1, 4, figsize=(14, 3.2), sharey=True)
    for a, (k, t) in zip(axs, prof.items()):
        for s, lab in enumerate(["Dec-Feb", "Mar-May", "Jun-Aug", "Sep-Nov"]):
            a.plot([0, 6, 12, 18], t.mef.unstack().loc[s].values, marker="o", label=lab)
        a.set_title(k.upper()); a.set_xlabel("local hour block start")
    axs[0].set_ylabel("estimated marginal gCO2/kWh"); axs[0].legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/estimated_marginal_profiles.png", dpi=120)


if __name__ == "__main__":
    main()
