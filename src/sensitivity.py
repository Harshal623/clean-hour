"""Emission-factor sensitivity for the four grids whose carbon intensity we compute from fuel mix
(Great Britain uses NESO's official values, so it is excluded). Retrains per factor set.
Run from carbon/: python -I -W ignore src/sensitivity.py"""
import sys
import pandas as pd
sys.path.insert(0, "src")
from load_data import carbon_intensity
from multigrid import run_grid
from sweep import EF_SETS

rows = []
for key in ["pjm", "ciso", "erco", "de"]:
    fuel = pd.read_csv(f"data/fuel_{key}.csv", index_col=0, parse_dates=True)
    for name, ef in EF_SETS.items():
        ci = carbon_intensity(fuel, ef)
        S, te, costs, mae, n = run_grid(key, ci_override=ci)
        for _, r in S[S.slip_h.isin([24, 72])].iterrows():
            rows.append(dict(grid=key, ef_set=name, slip_h=int(r.slip_h), model_pct_saved=r.model_pct_saved,
                             climatology_pct_saved=r.climatology_pct_saved, oracle_pct_saved=r.oracle_pct_saved,
                             model_minus_clim=r.model_minus_climatology, lo=r.model_minus_climatology_lo,
                             hi=r.model_minus_climatology_hi))
        print(key, name, "done", flush=True)
df = pd.DataFrame(rows).round(2)
df.to_csv("results/ef_sensitivity_multigrid.csv", index=False)
print(df.to_string(index=False))
