"""Shared harness for model-variant experiments (E10).

Honesty rules baked in: every choice (hyperparameters, blend weights, quantile, adoption of a feature set) is made on
the 2025-H2 VALIDATION months using models trained on 2023 to 2025-H1 only. The 2026 test is scored exactly once per
variant, with the chosen settings refit on 2023-2025. Baseline = the current production model (src/multigrid.py settings).
A variant is only "adopted on validation" if it beats the baseline settings by more than 0.1 g/kWh on validation.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, "src")
from grids import GRIDS, load_grid_data  # noqa: E402
from multigrid import HIST, build_rows_g  # noqa: E402
from sweep import NT, WX, best_start, block_boot, window_cost  # noqa: E402

BASE_PARAMS = dict(max_iter=400, learning_rate=0.05, max_depth=5, min_samples_leaf=100, l2_regularization=1.0,
                   early_stopping=True, validation_fraction=0.1, random_state=0)
VAL_START, TEST_START = pd.Timestamp("2025-07-01"), pd.Timestamp("2026-01-01")
SLIPS = (24, 72)
FUEL_GRIDS = {"pjm", "ciso", "erco", "de"}


def _take(a, idx):
    out = np.full(len(idx), np.nan)
    ok = idx >= 0
    out[ok] = a[idx[ok]]
    return out


def extras_for(g, tz, key):
    """Extra features, same row order as build_rows_g: 14-day same-hour stats and same-hour fuel-share lags."""
    s = g["ci"].values
    local = g.index.tz_localize("UTC").tz_convert(tz)
    sh = {}
    if key in FUEL_GRIDS:
        f = pd.read_csv(f"data/fuel_{key}.csv", index_col=0, parse_dates=True).reindex(g.index)
        tot = f.drop(columns=[c for c in ["unknown"] if c in f]).clip(lower=0).sum(axis=1).replace(0, np.nan)
        for c in ["gas", "coal", "wind", "solar", "nuclear"]:
            sh[c] = (f[c].clip(lower=0) / tot).values
    out, j = [], np.arange(NT)
    for d in np.where((local.hour == 18) & (local.minute == 0))[0]:
        if d < 24 * 8 or d + 7 + NT > len(s) or np.isnan(s[d]):
            continue
        p = d + 7 + j
        base = p - 24 * np.ceil((p - d) / 24).astype(int)
        hod = np.stack([_take(s, base - 24 * m) for m in range(14)])
        with np.errstate(all="ignore"):
            r = pd.DataFrame({"ci_hod_mean14d": np.nanmean(hod, 0), "ci_hod_std14d": np.nanstd(hod, 0),
                              "ci_hod_min7d": np.nanmin(hod[:7], 0)})
        for c, arr in sh.items():
            r[f"{c}_share_lag"] = _take(arr, base)
        out.append(r)
    return pd.concat(out, ignore_index=True)


def prep(key, extras=False):
    name, tz, _ = GRIDS[key]
    g, w = load_grid_data(key)
    data = build_rows_g(g, w, tz)
    feats_hist = list(HIST)
    feats_full = HIST + (["dem_fcst"] if data["dem_fcst"].notna().any() else []) + WX
    if extras:
        ex = extras_for(g, tz, key)
        assert len(ex) == len(data), (len(ex), len(data))
        for c in ex.columns:
            data[c] = ex[c].values
        feats_full = feats_full + [c for c in ex.columns if ex[c].notna().mean() > 0.5]
    full_ok = data.groupby("day")["y"].apply(lambda v: v.notna().all() and len(v) == NT)
    complete = data.day.isin(full_ok[full_ok].index)
    tr_part = data[(data.day < VAL_START) & data.y.notna()]
    full_train = data[(data.day < TEST_START) & data.y.notna()]
    val = data[(data.day >= VAL_START) & (data.day < TEST_START) & complete].copy()
    test = data[(data.day >= TEST_START) & complete].copy()
    return dict(key=key, tr_part=tr_part, full_train=full_train, val=val, test=test,
                feats_hist=feats_hist, feats_full=feats_full)


def fit_delta_p(tr, feats, loss=None, quantile=None, **over):
    t = tr.copy()
    t["y"] = t["y"] - t["ci_hod_mean7d"].fillna(t["ci_same_hr"])
    p = {**BASE_PARAMS, **over}
    if loss:
        p["loss"] = loss
        p["quantile"] = quantile
    return HistGradientBoostingRegressor(**p).fit(t[feats], t["y"])


def predict_delta_p(m, d, feats):
    return m.predict(d[feats]) + d["ci_hod_mean7d"].fillna(d["ci_same_hr"]).values


def day_costs(d, col, slips=SLIPS):
    rows = {}
    for day, grp in d.groupby("day"):
        grp = grp.sort_values("j")
        y = grp["y"].values
        v = grp[col].values
        r = {}
        for s in slips:
            r[f"c{s}"] = window_cost(y, best_start(v, s))
            r[f"i{s}"] = window_cost(y, 0)
        rows[day] = r
    return pd.DataFrame(rows).T


def val_score(c):
    """Decision metric used for every choice: mean chosen-window g/kWh averaged over 24 h and 72 h slack."""
    return float((c["c24"].mean() + c["c72"].mean()) / 2)


def compare(c_var, c_base):
    out = {}
    for s in SLIPS:
        diff = (c_var[f"c{s}"] - c_base[f"c{s}"]).values.astype(float)
        lo, hi = block_boot(diff, n=3000)
        out[str(s)] = dict(base=float(c_base[f"c{s}"].mean()), variant=float(c_var[f"c{s}"].mean()),
                           diff=float(diff.mean()), lo=float(lo), hi=float(hi))
    return out


def baseline(P):
    m = fit_delta_p(P["full_train"], P["feats_full"])
    P["test"]["base_pred"] = predict_delta_p(m, P["test"], P["feats_full"])
    mv = fit_delta_p(P["tr_part"], P["feats_full"])
    P["val"]["base_pred"] = predict_delta_p(mv, P["val"], P["feats_full"])
    return day_costs(P["test"], "base_pred"), day_costs(P["val"], "base_pred")
