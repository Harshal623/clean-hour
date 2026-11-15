"""Household version of the decision, scored on the 2026 test predictions.

Scenario: someone gets home and could start an appliance at 19:00 local on day D.
  - EV, "by morning":         4-hour charge, must finish by 07:00 -> start 19:00..03:00
  - Dishwasher, "within a day": 2-hour run, must finish by 19:00 next day -> start 19:00..17:00
Default = start at 19:00 straight away. The forecasts were issued at 18:00 the DAY BEFORE
(25 h earlier), so this is conservative: a live app would use a fresher forecast.
Output: g/kWh saved vs the default for each method. kWh per year are ASSUMPTIONS, shown as ranges.
Run from the repo root after decision_stack.py:  python -I src/experiments/household_shift.py
"""
import numpy as np
import pandas as pd

OUT = "results/experiments"
SCEN = {"EV, finish by 07:00": (4, 19, 27), "dishwasher, within a day": (2, 19, 41)}
# Annual kWh shifted: our assumptions, stated as ranges (edit here, not in the text).
KWH = {"EV, finish by 07:00": (2500, 4000), "dishwasher, within a day": (150, 300)}


def boot(x, block=7, n=4000, seed=0):
    rng = np.random.default_rng(seed); x = np.asarray(x)
    nb = int(np.ceil(len(x) / block)); st = np.arange(len(x) - block + 1)
    m = [np.concatenate([x[a:a + block] for a in rng.choice(st, nb)])[:len(x)].mean() for _ in range(n)]
    return np.percentile(m, [2.5, 97.5])


def run(df, cols, period):
    out = []
    for sc, (L, a, b) in SCEN.items():
        rec = {c: [] for c in ["default", "perfect", *cols]}
        for _, g in df.groupby("day"):
            y = g.sort_values("j")["y"].values
            win = lambda p: np.convolve(p, np.ones(L) / L, mode="valid")[a:b + 1]
            cy = win(y)
            rec["default"].append(cy[0]); rec["perfect"].append(cy.min())
            for n, c in cols.items():
                rec[n].append(cy[int(np.argmin(win(g.sort_values("j")[c].values)))])
        base = np.array(rec["default"])
        for n in ["perfect", *cols]:
            sv = base - np.array(rec[n]); lo, hi = boot(sv)
            k0, k1 = KWH[sc]
            out.append({"period": period, "scenario": sc, "method": n, "days": len(base),
                        "default_g_per_kWh": base.mean(), "saved_g_per_kWh": sv.mean(), "lo": lo, "hi": hi,
                        "saved_%": 100 * sv.mean() / base.mean(),
                        "kg_per_year_low": sv.mean() * k0 / 1000, "kg_per_year_high": sv.mean() * k1 / 1000,
                        "days_worse_than_default_%": 100 * (sv < -1e-9).mean()})
    return out


def main():
    te = pd.read_csv("results/test_predictions.csv.gz", parse_dates=["day"])
    st = pd.read_csv(f"{OUT}/stack_predictions.csv.gz", parse_dates=["day"])
    base = {"repeat yesterday": "persist", "hour-of-week average": "clim", "original model": "pred"}
    res = run(te, base, "Jan-Nov 2026")
    late = te[te.day >= "2026-05-01"].merge(st[["day", "j", "stack"]], on=["day", "j"])
    res += run(late, {**base, "decision-trained model": "stack"}, "May-Nov 2026")
    r = pd.DataFrame(res)
    pd.set_option("display.width", 250)
    print(r.round(1).to_string(index=False))
    r.round(3).to_csv(f"{OUT}/household_shift.csv", index=False)


if __name__ == "__main__":
    main()
