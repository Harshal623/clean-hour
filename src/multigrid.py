"""Clean-Hour: does a forecast help a household shift electricity use to cleaner hours, and where?

For each of 5 grids: forecast hourly carbon intensity from 18:00 the day before, pick the cleanest
4-hour window within the allowed delay (0/12/24/48/72 h), and compare with simple rules.
Split: train 2023-01-01..2025-12-31, TEST 2026-01-01..2026-11 (never shuffled). No interpolation:
test days with a missing target hour are dropped.
Run from carbon/:  python -I -W ignore src/multigrid.py
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from grids import GRIDS, load_grid_data  # noqa: E402
from sweep import (JOB, NT, SLIPS, TEST_START, WX, best_start, block_boot, fit,  # noqa: E402
                   window_cost)

HIST = ["lead", "hour", "dow", "month", "ci_same_hr", "ci_same_hr_wk", "ci_hod_mean7d",
        "ci_mean24", "ci_mean7d", "ci_last"]


def build_rows_g(g, w, tz):
    s = g["ci"].values
    dfc = g["demand_fcst"].values if "demand_fcst" in g else np.full(len(g), np.nan)
    neso = g["neso_forecast"].values if "neso_forecast" in g else None
    wx = {c: w[c].values for c in WX}
    local = g.index.tz_localize("UTC").tz_convert(tz)
    dec_pos = np.where((local.hour == 18) & (local.minute == 0))[0]
    out, j = [], np.arange(NT)
    for d in dec_pos:
        if d < 24 * 8 or d + 7 + NT > len(s) or np.isnan(s[d]):
            continue
        p = d + 7 + j
        k24 = np.ceil((p - d) / 24).astype(int)
        k168 = np.ceil((p - d) / 168).astype(int)
        r = pd.DataFrame({"lead": p - d})
        tl = local[p]
        r["hour"], r["dow"], r["month"] = tl.hour.values, tl.dayofweek.values, tl.month.values
        r["ci_same_hr"] = s[p - 24 * k24]
        r["ci_same_hr_wk"] = s[p - 168 * k168]
        hod = np.stack([s[p - 24 * k24 - 24 * m] for m in range(7)])
        with np.errstate(all="ignore"):
            r["ci_hod_mean7d"] = np.nanmean(hod, axis=0)
            r["ci_mean24"] = np.nanmean(s[d - 23:d + 1])
            r["ci_mean7d"] = np.nanmean(s[d - 167:d + 1])
        r["ci_last"] = s[d]
        r["dem_fcst"] = dfc[p]
        for c in WX:
            r[c] = wx[c][p]
        if neso is not None:
            r["neso"] = neso[p]
        r["y"] = s[p]
        r["day"] = local[d + 6].tz_localize(None).normalize()
        r["j"] = j
        out.append(r)
    return pd.concat(out, ignore_index=True)


def fit_delta(tr, feats):
    """Predict the CHANGE from the recent same-hour average (fixes level drift between years)."""
    t = tr.copy()
    base = t["ci_hod_mean7d"].fillna(t["ci_same_hr"])
    t["y"] = t["y"] - base
    return fit(t, feats)


def predict_delta(m, te, feats):
    return m.predict(te[feats]) + te["ci_hod_mean7d"].fillna(te["ci_same_hr"]).values


MODE = "delta"  # "direct" = predict the level itself (first version)


def run_grid(key, ci_override=None):
    name, tz, _ = GRIDS[key]
    g, w = load_grid_data(key)
    if ci_override is not None:  # used by the emission-factor sensitivity check
        g = g.copy()
        g["ci"] = ci_override.reindex(g.index).values
    data = build_rows_g(g, w, tz)
    feats_hist = HIST
    feats_full = HIST + (["dem_fcst"] if data["dem_fcst"].notna().any() else []) + WX
    tr = data[(data.day < TEST_START) & data.y.notna()]
    te = data[data.day >= TEST_START]
    ok = te.groupby("day")["y"].apply(lambda v: v.notna().all() and len(v) == NT)
    n_all = te.day.nunique()
    te = te[te.day.isin(ok[ok].index)].copy()
    if MODE == "delta":
        te["pred"] = predict_delta(fit_delta(tr, feats_full), te, feats_full)
        te["pred_hist"] = predict_delta(fit_delta(tr, feats_hist), te, feats_hist)
    else:
        te["pred"] = fit(tr, feats_full).predict(te[feats_full])
        te["pred_hist"] = fit(tr, feats_hist).predict(te[feats_hist])
    clim = tr.groupby(["dow", "hour"])["y"].mean()
    te["clim"] = clim.reindex(pd.MultiIndex.from_frame(te[["dow", "hour"]])).values
    te["persist"] = te["ci_same_hr"]
    mae = {n: float(np.abs(te["y"] - te[c]).mean()) for n, c in
           [("persistence", "persist"), ("climatology", "clim"), ("model", "pred"),
            ("model_hist", "pred_hist")]}
    rows, per_day = [], {}
    for day, grp in te.groupby("day"):
        grp = grp.sort_values("j")
        y = grp["y"].values
        rec = {"day": day}
        for slip in SLIPS:
            rec[f"immediate_{slip}"] = window_cost(y, 0)
            rec[f"oracle_{slip}"] = window_cost(y, best_start(y, slip))
            for nm, col in [("persistence", "persist"), ("climatology", "clim"),
                            ("model", "pred"), ("model_hist", "pred_hist")]:
                rec[f"{nm}_{slip}"] = window_cost(y, best_start(grp[col].values, slip))
            if "neso" in grp and slip <= 24 and grp["neso"].iloc[:slip + JOB].notna().all():
                rec[f"neso_{slip}"] = window_cost(y, best_start(grp["neso"].values[:slip + JOB], slip))
        per_day[day] = rec
    costs = pd.DataFrame(per_day.values()).set_index("day")
    for slip in SLIPS[1:]:
        imm = costs[f"immediate_{slip}"].mean()
        r = {"grid": key, "name": name, "slip_h": slip, "test_days": len(costs),
             "mean_ci_gco2_kwh": float(te["y"].mean()), "immediate": imm}
        for nm in ["persistence", "climatology", "model", "model_hist", "oracle"]:
            v = costs[f"{nm}_{slip}"].mean()
            r[nm] = v
            r[f"{nm}_pct_saved"] = 100 * (imm - v) / imm
        for a, b in [("model", "climatology"), ("model", "persistence"),
                     ("model_hist", "climatology"), ("model_hist", "persistence")]:
            d = (costs[f"{a}_{slip}"] - costs[f"{b}_{slip}"]).values
            lo, hi = block_boot(d, n=3000)
            r[f"{a}_minus_{b}"], r[f"{a}_minus_{b}_lo"], r[f"{a}_minus_{b}_hi"] = d.mean(), lo, hi
        r["model_beats_clim_pct_days"] = 100 * float((costs[f"model_{slip}"] < costs[f"climatology_{slip}"]).mean())
        if f"neso_{slip}" in costs and costs[f"neso_{slip}"].notna().mean() > 0.8:
            c2 = costs.dropna(subset=[f"neso_{slip}"])
            r["neso"] = c2[f"neso_{slip}"].mean()
            d = (c2[f"model_{slip}"] - c2[f"neso_{slip}"]).values
            lo, hi = block_boot(d, n=3000)
            r["model_minus_neso"], r["model_minus_neso_lo"], r["model_minus_neso_hi"] = d.mean(), lo, hi
        # weekday/weekend and worst days at 24h
        if slip == 24:
            wk = costs.index.dayofweek >= 5
            r["model_minus_clim_weekday"] = (costs.loc[~wk, "model_24"] - costs.loc[~wk, "climatology_24"]).mean()
            r["model_minus_clim_weekend"] = (costs.loc[wk, "model_24"] - costs.loc[wk, "climatology_24"]).mean()
            rg = (costs["model_24"] - costs["oracle_24"]).sort_values(ascending=False)
            r["worst_days"] = ";".join(f"{d.date()}({v:.0f})" for d, v in rg.head(3).items())
            r["pct_days_worse_than_now"] = 100 * float((costs["model_24"] > costs["immediate_24"] + 1e-9).mean())
        rows.append(r)
    return pd.DataFrame(rows), te, costs, mae, n_all


def main():
    global MODE
    if len(sys.argv) > 1:
        MODE = sys.argv[1]
    print("target mode:", MODE)
    summ, allte, maes = [], [], {}
    for key in GRIDS:
        S, te, costs, mae, n_all = run_grid(key)
        print(f"\n=== {GRIDS[key][0]}: test days kept {len(costs)} of {n_all}; "
              f"mean CI {te['y'].mean():.0f}, std {te['y'].std():.0f} g/kWh")
        print("hourly MAE:", {k: round(v, 1) for k, v in mae.items()})
        pd.set_option("display.width", 250)
        print(S[["slip_h", "immediate", "persistence", "climatology", "model", "oracle",
                 "model_pct_saved", "oracle_pct_saved"]].round(1).to_string(index=False))
        print(S[["slip_h", "model_minus_climatology", "model_minus_climatology_lo",
                 "model_minus_climatology_hi", "model_minus_persistence", "model_minus_persistence_lo",
                 "model_minus_persistence_hi", "model_beats_clim_pct_days"]].round(1).to_string(index=False))
        if "model_minus_neso" in S:
            print("vs NESO's own forecast:", S[["slip_h", "neso", "model_minus_neso", "model_minus_neso_lo",
                                                 "model_minus_neso_hi"]].dropna().round(1).to_string(index=False))
        maes[key] = mae
        summ.append(S)
        t = te[["day", "j", "y", "pred", "clim", "persist"]].copy()
        t.insert(0, "grid", key)
        allte.append(t.round(1))
    pd.concat(summ).to_csv("results/multigrid_summary.csv", index=False)
    pd.concat(allte).to_csv("results/test_predictions_all.csv.gz", index=False)
    json.dump(maes, open("results/multigrid_hourly_mae.json", "w"), indent=1)


if __name__ == "__main__":
    main()
