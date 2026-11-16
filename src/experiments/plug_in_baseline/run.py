"""E12: savings against a realistic default (charge the moment you plug in at 6 PM), and how often advice backfires.

Why: our headline baseline, "start at midnight", is deliberately naive and already a fairly clean hour. Our user is a
family that plugs in at 6 PM. What they would do without the app is start charging right then (18:00-22:00, close to the
dirtiest hours of the day). This script re-scores the SAME saved 2026 forecasts against that default. No model is
retrained and nothing is tuned: it only changes what we compare against.

For each 2026 test day D (forecast made at 18:00 on D-1):
  default  = actual carbon of 18:00-22:00 on D-1 (start charging on plug-in)
  advice   = actual carbon of the 4-hour window the forecast picks, starting between 00:00 on D and 00:00 + slack
Methods: production GBM, the app as shipped (GBM + its "no clear winner below 3%" rule), the PyTorch Transformer
(plain version, E11), persistence, and perfect hindsight. 95% intervals: 7-day block bootstrap (src/sweep.py).

Run from the repo root (no downloads needed):  python -I -W ignore src/experiments/plug_in_baseline/run.py
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from sweep import block_boot  # noqa: E402

L = 4  # hours the job runs
NAMES = {"pjm": "Virginia", "ciso": "California", "erco": "Texas", "de": "Germany", "gb": "Great Britain"}
P = pd.read_csv("results/test_predictions_all.csv.gz", parse_dates=["day"])
T = pd.read_csv("results/experiments/torch_transformer/predictions.csv.gz", parse_dates=["day"])


def win(a):
    return np.convolve(a, np.ones(L) / L, mode="valid")


out = []
for g, name in NAMES.items():
    d = P[P.grid == g].sort_values(["day", "j"])
    Y = {k: v.y.values for k, v in d.groupby("day")}
    PR = {k: v.pred.values for k, v in d.groupby("day")}
    PE = {k: np.nan_to_num(v.persist.values, nan=1e9) for k, v in d.groupby("day")}
    TR = {k: v.transformer_mse.values for k, v in T[T.grid == g].sort_values(["day", "j"]).groupby("day")}
    for slip in [24, 72]:
        rows = []
        for day in sorted(Y):
            prev = day - pd.Timedelta(days=1)
            if prev not in Y or day not in TR:
                continue
            y = Y[day]
            cy, cp = win(y), win(PR[day])[:slip + 1]
            s = int(cp.argmin())
            s_app = 0 if 100 * (cp[0] - cp[s]) / cp[0] < 3 else s  # the app's existing rule
            rows.append({"plug_in_6pm": Y[prev][18:22].mean(), "midnight": cy[0],
                         "gbm": cy[s], "app_as_shipped": cy[s_app],
                         "transformer": cy[int(win(TR[day])[:slip + 1].argmin())],
                         "persistence": cy[int(win(PE[day])[:slip + 1].argmin())],
                         "perfect_hindsight": cy[:slip + 1].min()})
        R = pd.DataFrame(rows)
        for m in ["persistence", "gbm", "app_as_shipped", "transformer", "perfect_hindsight"]:
            dd = (R[m] - R.plug_in_6pm).values
            lo, hi = block_boot(dd, n=3000)
            out.append({"region": name, "slack_h": slip, "method": m, "days": len(R),
                        "plug_in_6pm_g": R.plug_in_6pm.mean(), "advice_g": R[m].mean(),
                        "pct_cleaner_vs_6pm": 100 * (R.plug_in_6pm.mean() - R[m].mean()) / R.plug_in_6pm.mean(),
                        "g_saved_vs_6pm": -dd.mean(), "lo": -hi, "hi": -lo,
                        "pct_days_worse_than_6pm": 100 * (R[m] > R.plug_in_6pm + 1e-9).mean(),
                        "pct_cleaner_vs_midnight": 100 * (R.midnight.mean() - R[m].mean()) / R.midnight.mean(),
                        "pct_days_worse_than_midnight": 100 * (R[m] > R.midnight + 1e-9).mean(),
                        "ev_kg_per_year_3000kwh": 3 * (R.plug_in_6pm.mean() - R[m].mean())})
S = pd.DataFrame(out).round(2)
S.to_csv("results/experiments/plug_in_baseline.csv", index=False)
print(S[S.region == "Virginia"].drop(columns=["region", "days", "plug_in_6pm_g"]).to_string(index=False))
for col in ["pct_cleaner_vs_6pm", "pct_days_worse_than_6pm"]:
    print(f"\n24 h, {col}:")
    print(S[S.slack_h == 24].pivot(index="region", columns="method", values=col).round(1).to_string())
