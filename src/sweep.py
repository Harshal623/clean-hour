"""Virginia deep dive: does a forecast beat the hour-of-week average?

Decision moment: 18:00 local time the evening before. The job is
released at local midnight of day D.
Slip = how many hours the job may wait after release.
Split: train 2023-01-01 to 2025-12-31, TEST from 2026-01-01.
Never shuffled. We never fill gaps: a test day with a missing hour
is dropped.
Run from carbon/:  python -I src/sweep.py
"""

import json
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, "src")
from load_data import (
    EF,
    FUELS,
    carbon_intensity,
    load_grid,
    load_weather,
)  # noqa: E402

TZ = "America/New_York"
JOB = 4
SLIPS = [0, 12, 24, 48, 72]
NT = max(SLIPS) + JOB  # target hours needed after release (76)
LAST_REAL = pd.Timestamp(
    "2026-11-14 05:00"
)  # last UTC hour with real EIA fuel data
TEST_START = pd.Timestamp("2026-01-01")
WX = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "cloud_cover",
    "shortwave_radiation",
]
EF_SETS = {
    "IPCC lifecycle (primary)": EF,
    "combustion-only": {
        "coal": 1000,
        "gas": 410,
        "nuclear": 0,
        "oil": 760,
        "hydro": 0,
        "solar": 0,
        "wind": 0,
        "other": 230,
        "unknown": 230,
    },
    "gas-heavy (gas 600, coal 900)": {**EF, "gas": 600, "coal": 900},
    "'other' fuel = 0": {**EF, "other": 0},
    "'other' fuel = 600": {**EF, "other": 600},
}


def load_all():
    g = load_grid().loc[:LAST_REAL]
    w = load_weather(None, None)
    full = pd.date_range(g.index.min(), g.index.max(), freq="h")
    g = g.reindex(full)  # missing hours become NaN (flagged, never filled)
    w = w.reindex(full)
    return g, w


def build_rows(g, w, ci, with_test=True):
    """One row per decision day and target hour."""
    s = ci.reindex(g.index).values
    dfc = g["demand_fcst"].values
    dom = g["dom_demand"].values
    wx = {c: w[c].values for c in WX}
    idx = g.index
    local = idx.tz_localize("UTC").tz_convert(TZ)
    # decision hours: end-of-hour label == local 18:00
    dec_pos = np.where((local.hour == 18) & (local.minute == 0))[0]
    rows = []
    j = np.arange(NT)
    for d in dec_pos:
        if d < 24 * 8 or d + 7 + NT > len(s):
            continue
        p = d + 7 + j  # hour ending release+(j+1)
        if np.isnan(s[d]):
            continue
        k24 = np.ceil((p - d) / 24).astype(int)
        k168 = np.ceil((p - d) / 168).astype(int)
        r = pd.DataFrame({"lead": p - d})
        tl = local[p]
        r["hour"] = tl.hour.values
        r["dow"] = tl.dayofweek.values
        r["month"] = tl.month.values
        r["ci_same_hr"] = s[p - 24 * k24]
        r["ci_same_hr_wk"] = s[p - 168 * k168]
        hod = np.stack([s[p - 24 * k24 - 24 * m] for m in range(7)])
        with np.errstate(all="ignore"):
            r["ci_hod_mean7d"] = np.nanmean(hod, axis=0)
            r["ci_mean24"] = np.nanmean(s[d - 23 : d + 1])
            r["ci_mean7d"] = np.nanmean(s[d - 167 : d + 1])
        r["ci_last"] = s[d]
        r["dem_fcst"] = dfc[p]
        r["dom_dem_same_hr"] = dom[p - 24 * k24]
        for c in WX:
            r[c] = wx[c][p]
        r["y"] = s[p]
        r["day"] = (
            local[d + 6].tz_localize(None).normalize()
        )  # local calendar day D (naive)
        r["j"] = j
        rows.append(r)
    return pd.concat(rows, ignore_index=True)


def best_start(profile, slip):
    """Pick the start hour (0..slip) with the lowest 4-hour average."""
    c = np.convolve(
        profile, np.ones(JOB) / JOB, mode="valid"
    )  # c[i] = mean of profile[i:i+4]
    return int(
        np.nanargmin(c[: slip + 1])
    )  # windows touching a missing hour (NaN) are ignored


def window_cost(y, start):
    return y[start : start + JOB].mean()


def fit(tr, feats, seed=0):
    m = HistGradientBoostingRegressor(
        max_iter=400,
        learning_rate=0.05,
        max_depth=5,
        min_samples_leaf=100,
        l2_regularization=1.0,
        early_stopping=True,
        validation_fraction=0.1,
        random_state=seed,
    )
    return m.fit(tr[feats], tr["y"])


def evaluate(data, feats_full, feats_hist, label=""):
    tr = data[data.day < TEST_START]
    te = data[data.day >= TEST_START]
    # drop test days with any missing target hour (NO interpolation)
    ok = te.groupby("day")["y"].apply(
        lambda v: v.notna().all() and len(v) == NT
    )
    n_all_days = te.day.nunique()
    te = te[te.day.isin(ok[ok].index)].copy()
    tr = tr.dropna(subset=["y"])
    m_full = fit(tr, feats_full)
    m_hist = fit(tr, feats_hist)
    te["pred"] = m_full.predict(te[feats_full])
    te["pred_hist"] = m_hist.predict(te[feats_hist])
    # climatology: mean CI by (day-of-week, hour) from TRAIN only
    clim = tr.groupby(["dow", "hour"])["y"].mean()
    te["clim"] = clim.reindex(
        pd.MultiIndex.from_frame(te[["dow", "hour"]])
    ).values
    te["persist"] = te["ci_same_hr"]
    return tr, te, n_all_days


def per_day_costs(te):
    out = []
    for day, grp in te.groupby("day"):
        grp = grp.sort_values("j")
        y = grp["y"].values
        rec = {"day": day}
        for slip in SLIPS:
            rec[f"immediate_{slip}"] = window_cost(y, 0)
            rec[f"persistence_{slip}"] = window_cost(
                y, best_start(grp["persist"].values, slip)
            )
            rec[f"climatology_{slip}"] = window_cost(
                y, best_start(grp["clim"].values, slip)
            )
            rec[f"model_{slip}"] = window_cost(
                y, best_start(grp["pred"].values, slip)
            )
            rec[f"model_hist_{slip}"] = window_cost(
                y, best_start(grp["pred_hist"].values, slip)
            )
            rec[f"oracle_{slip}"] = window_cost(y, best_start(y, slip))
        out.append(rec)
    return pd.DataFrame(out).set_index("day")


def block_boot(diff, block=7, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(diff)
    nb = int(np.ceil(len(x) / block))
    starts = np.arange(len(x) - block + 1)
    means = np.empty(n)
    for i in range(n):
        st = rng.choice(starts, nb)
        means[i] = np.concatenate([x[a : a + block] for a in st])[
            : len(x)
        ].mean()
    return np.percentile(means, [2.5, 97.5])


def summarize(costs):
    rows = []
    for slip in SLIPS:
        imm = costs[f"immediate_{slip}"].mean()
        rec = {"slip_h": slip, "immediate": imm}
        for s in [
            "persistence",
            "climatology",
            "model",
            "model_hist",
            "oracle",
        ]:
            v = costs[f"{s}_{slip}"].mean()
            rec[s] = v
            rec[f"{s}_%saved"] = 100 * (imm - v) / imm
        d = (costs[f"model_{slip}"] - costs[f"climatology_{slip}"]).values
        lo, hi = block_boot(d)
        rec["model-clim_mean"] = d.mean()
        rec["ci95_lo"], rec["ci95_hi"] = lo, hi
        rec["model_beats_clim_%days"] = 100 * (d < 0).mean()
        dh = (
            costs[f"model_hist_{slip}"] - costs[f"climatology_{slip}"]
        ).values
        rec["hist-clim_mean"] = dh.mean()
        rec["hist_ci95_lo"], rec["hist_ci95_hi"] = block_boot(dh)
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    g, w = load_all()
    ci = carbon_intensity(g)
    print(
        "last real EIA hour (UTC):",
        g.index.max(),
        "| hours:",
        len(g),
        "| truly missing CI hours:",
        int(ci.isna().sum()),
    )
    data = build_rows(g, w, ci)
    data["day"] = pd.to_datetime(data["day"])
    feats_hist = [
        "lead",
        "hour",
        "dow",
        "month",
        "ci_same_hr",
        "ci_same_hr_wk",
        "ci_hod_mean7d",
        "ci_mean24",
        "ci_mean7d",
        "ci_last",
    ]
    feats_full = feats_hist + ["dem_fcst", "dom_dem_same_hr"] + WX
    tr, te, n_all = evaluate(data, feats_full, feats_hist)
    print(
        f"train days {tr.day.nunique()} | "
        f"test days kept {te.day.nunique()} of {n_all}"
        f" (dropped {n_all - te.day.nunique()} with missing target hours)"
        f" | test {te.day.min().date()} -> {te.day.max().date()}"
    )
    # hourly MAE overall and by lead bucket
    for name, col in [
        ("persistence", "persist"),
        ("climatology", "clim"),
        ("model (full)", "pred"),
        ("model (history only)", "pred_hist"),
    ]:
        print(
            f"hourly MAE {name:22s} {np.abs(te['y']-te[col]).mean():6.2f}",
            "| lead<=24h:",
            round(np.abs(te["y"] - te[col])[te.lead <= 24 + 6].mean(), 2),
        )
    costs = per_day_costs(te)
    S = summarize(costs)
    pd.set_option("display.width", 250)
    print("\nMean gCO2/kWh of chosen 4h window, TEST (lower = better):")
    print(
        S[
            [
                "slip_h",
                "immediate",
                "persistence",
                "climatology",
                "model",
                "model_hist",
                "oracle",
            ]
        ]
        .round(2)
        .to_string(index=False)
    )
    print("\n% saved vs run-immediately:")
    print(
        S[
            [
                "slip_h",
                "persistence_%saved",
                "climatology_%saved",
                "model_%saved",
                "model_hist_%saved",
                "oracle_%saved",
            ]
        ]
        .round(2)
        .to_string(index=False)
    )
    print(
        "\nModel minus climatology (g/kWh, negative = model better),"
        " block-bootstrap 95% CI:"
    )
    print(
        S[
            [
                "slip_h",
                "model-clim_mean",
                "ci95_lo",
                "ci95_hi",
                "model_beats_clim_%days",
                "hist-clim_mean",
                "hist_ci95_lo",
                "hist_ci95_hi",
            ]
        ]
        .round(2)
        .to_string(index=False)
    )

    # breakdowns at slip 24 and 72
    costs["season"] = costs.index.month.map(
        lambda m: {
            12: "DJF",
            1: "DJF",
            2: "DJF",
            3: "MAM",
            4: "MAM",
            5: "MAM",
            6: "JJA",
            7: "JJA",
            8: "JJA",
        }.get(m, "SON")
    )
    costs["daytype"] = np.where(
        costs.index.dayofweek >= 5, "weekend", "weekday"
    )
    bd = {}
    for slip in [24, 72]:
        for key in ["season", "daytype"]:
            t = costs.groupby(key).apply(
                lambda x: pd.Series(
                    {
                        "days": len(x),
                        "immediate": x[f"immediate_{slip}"].mean(),
                        "climatology": x[f"climatology_{slip}"].mean(),
                        "model": x[f"model_{slip}"].mean(),
                        "oracle": x[f"oracle_{slip}"].mean(),
                        "model-clim": (
                            x[f"model_{slip}"] - x[f"climatology_{slip}"]
                        ).mean(),
                    }
                ),
                include_groups=False,
            )
            print(f"\nslip {slip}h by {key}:\n", t.round(2).to_string())
            bd[f"slip{slip}_{key}"] = (
                t.round(3).reset_index().to_dict("records")
            )

    # emission-factor sensitivity (retrain per EF set)
    sens = []
    for name, ef in EF_SETS.items():
        ci2 = carbon_intensity(g, ef)
        d2 = build_rows(g, w, ci2)
        d2["day"] = pd.to_datetime(d2["day"])
        _, te2, _ = evaluate(d2, feats_full, feats_hist)
        c2 = per_day_costs(te2)
        S2 = summarize(c2).set_index("slip_h")
        for slip in [24, 72]:
            sens.append(
                {
                    "ef_set": name,
                    "slip_h": slip,
                    "oracle_%saved": round(S2.loc[slip, "oracle_%saved"], 2),
                    "clim_%saved": round(
                        S2.loc[slip, "climatology_%saved"], 2
                    ),
                    "model_%saved": round(S2.loc[slip, "model_%saved"], 2),
                    "model-clim": round(S2.loc[slip, "model-clim_mean"], 2),
                    "ci_lo": round(S2.loc[slip, "ci95_lo"], 2),
                    "ci_hi": round(S2.loc[slip, "ci95_hi"], 2),
                }
            )
    sens = pd.DataFrame(sens)
    print("\nEmission-factor sensitivity:\n", sens.to_string(index=False))

    S.round(4).to_csv("results/sweep_summary.csv", index=False)
    sens.to_csv("results/ef_sensitivity.csv", index=False)
    costs.to_csv("results/per_day_costs.csv")
    json.dump(bd, open("results/breakdowns.json", "w"), indent=1, default=str)
    te.to_pickle("results/test_predictions.pkl")


if __name__ == "__main__":
    main()
