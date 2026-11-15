"""Failure analysis per grid: the 3 days where the advice was furthest from the best window (24 h delay).
Run from carbon/: python -I -W ignore src/failures.py"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

JOB, SLIP = 4, 24
NAMES = {"ciso": "California", "erco": "Texas", "pjm": "Virginia", "de": "Germany", "gb": "Great Britain"}
df = pd.read_csv("results/test_predictions_all.csv.gz", parse_dates=["day"])


def win(a):
    return np.convolve(a, np.ones(JOB) / JOB, mode="valid")


rows, cases = [], {}
for g, grp_g in df.groupby("grid"):
    recs = []
    for day, d in grp_g.groupby("day"):
        d = d.sort_values("j")
        y, p = d.y.values, d.pred.values
        sm = int(win(p)[:SLIP + 1].argmin()); so = int(win(y)[:SLIP + 1].argmin())
        cy = win(y)
        recs.append(dict(grid=g, day=day, model_start=sm, best_start=so, now=cy[0], chosen=cy[sm], best=cy[so],
                         regret=cy[sm] - cy[so], worse_than_now=cy[sm] > cy[0] + 1e-9,
                         fcst_err=np.abs(y[:SLIP + JOB + 6] - p[:SLIP + JOB + 6]).mean()))
    r = pd.DataFrame(recs)
    cases[g] = r.sort_values("regret", ascending=False).head(3)
    rows.append(dict(grid=g, region=NAMES[g], days=len(r), median_regret=r.regret.median(),
                     p90_regret=r.regret.quantile(.9), pct_within_10g_of_best=100 * (r.regret < 10).mean(),
                     pct_worse_than_midnight=100 * r.worse_than_now.mean(), worst_regret=r.regret.max(),
                     mean_fcst_err_on_worst3=cases[g].fcst_err.mean(), mean_fcst_err_all=r.fcst_err.mean()))
S = pd.DataFrame(rows).round(1)
S.to_csv("results/failure_summary.csv", index=False)
pd.concat(cases.values()).round(1).to_csv("results/failure_days.csv", index=False)
print(S.to_string(index=False))
print(pd.concat(cases.values()).round(1).to_string(index=False))

fig, axs = plt.subplots(5, 3, figsize=(13, 13), sharex=True)
for i, g in enumerate(["ciso", "erco", "pjm", "de", "gb"]):
    for k, (_, c) in enumerate(cases[g].iterrows()):
        d = df[(df.grid == g) & (df.day == c.day)].sort_values("j").iloc[:52]
        a = axs[i, k]
        a.plot(d.j, d.y, color="#222", lw=1.5, label="actual")
        a.plot(d.j, d.pred, color="#1f6f5c", lw=1.5, label="forecast")
        a.plot(d.j, d.clim, color="#d9822b", ls=":", lw=1.2, label="average week")
        a.axvspan(c.model_start, c.model_start + JOB, color="#1f6f5c", alpha=.2)
        a.axvspan(c.best_start, c.best_start + JOB, color="#222", alpha=.12)
        a.set_title(f"{NAMES[g]} {c.day.date()}  (+{c.regret:.0f} g/kWh worse than best)", fontsize=9)
        a.spines[["top", "right"]].set_visible(False)
axs[0, 0].legend(frameon=False, fontsize=8)
for a in axs[-1]:
    a.set_xlabel("hours after midnight")
for a in axs[:, 0]:
    a.set_ylabel("gCO2/kWh")
fig.suptitle("The three worst days per region (green band = our pick, grey band = best possible)", y=0.995)
fig.tight_layout()
fig.savefig("results/failures_by_grid.png", dpi=110)
