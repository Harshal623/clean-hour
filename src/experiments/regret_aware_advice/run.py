"""E2: can the tool say "unsure, run now" on the risky days? (24 h of slack, 4-hour job)

The earlier "unsure" rule (predicted saving below a threshold) gave no gain. Here we add AGREEMENT between three
independent forecasts (full model, history-only model, persistence): act only if the predicted saving is big
enough AND the three forecasts pick start times within +-3 hours of each other.
Threshold tuned on Jan-Apr 2026 only; scored once on May-Nov 2026 (rolling nothing else). First-stage models
were trained on 2023-2025. Metrics: harmful days (chosen window dirtier than starting at midnight), mean
g/kWh, share of days acted on. Kill rule (set before running): WIN only if harmful days drop with a 95% block-bootstrap
interval below zero AND mean cost rises by < 0.5 g/kWh, in at least 3 of 5 grids.
Run from repo root: python -I -W ignore src/experiments/regret_aware_advice/run.py
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "src/experiments")
from decision_stack import JOB, best_start, block_boot  # noqa: E402

SLIP = 24
OUT = "results/experiments/regret_aware_advice"
NAMES = {"pjm": "Virginia", "ciso": "California", "erco": "Texas", "de": "Germany", "gb": "Great Britain"}


def day_table(df):
    rows = []
    for day, g in df.groupby("day"):
        g = g.sort_values("j")
        if len(g) < 76:
            continue
        y = g.y.values
        win = lambda a: np.convolve(a, np.ones(JOB) / JOB, mode="valid")
        cy = win(y)
        p = {n: g[c].fillna(g["pred"]).values for n, c in [("m", "pred"), ("h", "pred_hist"), ("p", "persist")]}
        starts = {n: best_start(v, SLIP) for n, v in p.items()}
        cm = win(p["m"])[:SLIP + 1]
        rows.append(dict(day=day, now=cy[0], chosen=cy[starts["m"]], pred_saving=cm[0] - cm[starts["m"]],
                         spread=max(starts.values()) - min(starts.values()), best=cy[best_start(y, SLIP)]))
    return pd.DataFrame(rows).set_index("day")


def apply(t, tau, tol):
    act = (t.pred_saving >= tau) & (t.spread <= tol)
    cost = np.where(act, t.chosen, t.now)
    return act, cost


def main():
    df = pd.read_csv("results/test_predictions_all_ext.csv.gz", parse_dates=["day"])
    out = []
    for g, grp in df.groupby("grid"):
        t = day_table(grp.drop(columns="grid"))
        tune, test = t[t.index < "2026-05-01"], t[t.index >= "2026-05-01"]
        best, grid_ = None, [(tau, tol) for tau in [0, 3, 6, 10, 15, 20] for tol in [1, 3, 6, 100]]
        base_cost = tune.chosen.mean()
        for tau, tol in grid_:
            act, cost = apply(tune, tau, tol)
            harm = (cost > tune.now + 1e-9).mean()
            # prefer fewest harmful days, subject to cost within 0.5 g/kWh of always acting
            if cost.mean() <= base_cost + 0.5 and (best is None or harm < best[0] - 1e-9):
                best = (harm, tau, tol)
        _, tau, tol = best
        act, cost = apply(test, tau, tol)
        harm_base = (test.chosen > test.now + 1e-9).astype(float).values
        harm_new = (cost > test.now.values + 1e-9).astype(float)
        d_h = harm_new - harm_base
        lo, hi = block_boot(d_h)
        d_c = cost - test.chosen.values
        clo, chi = block_boot(d_c)
        out.append(dict(grid=g, region=NAMES[g], tune_days=len(tune), test_days=len(test), tau=tau, tol_h=tol,
                        acts_pct=100 * act.mean(), harmful_always_pct=100 * harm_base.mean(),
                        harmful_with_rule_pct=100 * harm_new.mean(), harmful_change_pp=100 * d_h.mean(),
                        harm_lo_pp=100 * lo, harm_hi_pp=100 * hi, cost_always=test.chosen.mean(),
                        cost_with_rule=cost.mean(), cost_change=d_c.mean(), cost_lo=clo, cost_hi=chi,
                        now=test.now.mean(), best=test.best.mean()))
    R = pd.DataFrame(out).round(2)
    R.to_csv(f"{OUT}/regret_aware_advice.csv", index=False)
    pd.set_option("display.width", 250)
    print(R[["region", "tune_days", "test_days", "tau", "tol_h", "acts_pct", "harmful_always_pct",
             "harmful_with_rule_pct", "harm_lo_pp", "harm_hi_pp", "cost_always", "cost_with_rule", "cost_change",
             "cost_lo", "cost_hi"]].to_string(index=False))
    win = ((R.harm_hi_pp < 0) & (R.cost_change < 0.5)).sum()
    print(f"\nGrids where harmful days fall (interval < 0) with cost rise < 0.5 g/kWh: {int(win)} of 5 (need >= 3)")


if __name__ == "__main__":
    main()
