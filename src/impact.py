"""Household impact: kg CO2/year saved by shifting a flexible load vs starting at local midnight.
Uses the held-out 2026 test days per grid. Run from carbon/: python -I -W ignore src/impact.py
Assumed annual loads (our assumptions, easy to change): EV 3,000 kWh/yr; laundry+dishwasher 400 kWh/yr.
"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "src")
from grids import GRIDS
from multigrid import run_grid
from sweep import block_boot

LOADS = {"EV charging (3,000 kWh/yr)": 3000, "Laundry + dishwasher (400 kWh/yr)": 400}
rows = []
for key in GRIDS:
    S, te, costs, mae, n = run_grid(key)
    for slip in [24, 72]:
        for who in ["model", "climatology", "oracle"]:
            d = (costs[f"immediate_{slip}"] - costs[f"{who}_{slip}"]).values  # g/kWh saved per day
            lo, hi = block_boot(-d, n=3000)
            for load, kwh in LOADS.items():
                rows.append({"grid": key, "name": GRIDS[key][0], "delay_h": slip, "strategy": who, "load": load,
                             "g_per_kwh_saved": d.mean(), "kg_per_year": d.mean() * kwh / 1000,
                             "kg_per_year_lo": -hi * kwh / 1000, "kg_per_year_hi": -lo * kwh / 1000})
df = pd.DataFrame(rows).round(2)
df.to_csv("results/household_impact.csv", index=False)
print(df[(df.strategy == "model") & df.load.str.startswith("EV")].to_string(index=False))
