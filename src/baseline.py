"""Carbon-aware scheduling: forecast tomorrow's hourly grid carbon intensity (PJM, serving
Loudoun/Dominion), pick the cleanest 4-hour window, and measure gCO2/kWh vs simple rules.

Decision moment: 18:00 local on day D-1. Job: a 4-hour flexible batch (e.g. AI training chunk)
that must run inside local day D.
Splits (by time, never shuffled): train 2023-01..2025-06, val 2025-07..2025-12, TEST 2026-01..end.
Run from carbon/:  python -I src/baseline.py
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

sys.path.insert(0, "src")
from load_data import carbon_intensity, load_grid, load_weather  # noqa: E402

JOB_H = 4
TZ = "America/New_York"


def build():
    g = load_grid()
    w = load_weather(None, None)
    ci = carbon_intensity(g)
    df = pd.concat([ci, g[["demand", "demand_fcst", "dom_demand"]], w], axis=1, sort=True)
    df = df.loc[df.index.intersection(w.index)]
    df.index = df.index.tz_localize("UTC").tz_convert(TZ)  # end-of-hour, local clock
    df = df[~df.index.duplicated()].asfreq("h")
    df["ci"] = df["ci"].interpolate(limit=3)
    df["demand_fcst"] = df["demand_fcst"].fillna(df["demand"])
    df["dom_demand"] = df["dom_demand"].interpolate(limit=3)
    return df


def rows_for_day(df, day):
    """Feature rows for the 24 target hours of local `day`, known as of 18:00 on day-1."""
    t0 = pd.Timestamp(day, tz=TZ)
    decision = t0 - pd.Timedelta(hours=6)  # 18:00 previous day
    hist = df.loc[:decision, "ci"]
    if len(hist) < 24 * 8:
        return None
    idx = pd.date_range(t0 + pd.Timedelta(hours=1), periods=24, freq="h")  # hour ends 01..24
    if not set(idx).issubset(df.index):
        return None
    r = pd.DataFrame(index=idx)
    r["hour"] = np.arange(24)
    r["dow"] = t0.dayofweek
    r["month"] = t0.month
    last24 = hist.iloc[-24:].values  # from 19:00 D-2 .. 18:00 D-1 -> offset to target hour
    # target hour h (0..23) is (h+6) hours after decision. Use value 24h earlier when known,
    # else the last known same-clock-hour (yesterday's value).
    r["ci_yday"] = [hist.get(idx[h] - pd.Timedelta(hours=24), np.nan) if
                    idx[h] - pd.Timedelta(hours=24) <= decision else
                    hist.get(idx[h] - pd.Timedelta(hours=48), np.nan) for h in range(24)]
    r["ci_wk"] = [hist.get(idx[h] - pd.Timedelta(hours=24 * 7), np.nan) for h in range(24)]
    r["ci_last"] = hist.iloc[-1]
    r["ci_mean24"] = last24.mean()
    r["ci_mean7d"] = hist.iloc[-168:].mean()
    r["dem_fcst"] = df.loc[idx, "demand_fcst"].values
    r["dom_dem_yday"] = [df["dom_demand"].get(idx[h] - pd.Timedelta(hours=24), np.nan) if
                         idx[h] - pd.Timedelta(hours=24) <= decision else np.nan for h in range(24)]
    for c in ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "cloud_cover",
              "shortwave_radiation"]:
        r[c] = df.loc[idx, c].values
    r["y"] = df.loc[idx, "ci"].values
    r["day"] = pd.Timestamp(day)
    return r


def best_window(profile):
    s = pd.Series(profile).rolling(JOB_H).mean().iloc[JOB_H - 1:]  # mean CI of each 4h window
    return int(s.values.argmin())  # start hour 0..20


def main():
    df = build()
    first = df.index.min().tz_localize(None).normalize()
    last = df.index.max().tz_localize(None).normalize()
    days = pd.date_range(first + pd.Timedelta(days=9), last - pd.Timedelta(days=1), freq="D")
    parts = [rows_for_day(df, d) for d in days]
    data = pd.concat([p for p in parts if p is not None]).dropna(subset=["y", "ci_yday"])
    data["day"] = pd.to_datetime(data["day"])
    tr = data[data.day < "2025-07-01"]
    va = data[(data.day >= "2025-07-01") & (data.day < "2026-01-01")]
    te = data[data.day >= "2026-01-01"]
    print("train/val/test days:", tr.day.nunique(), va.day.nunique(), te.day.nunique(),
          "| test range", te.day.min().date(), "->", te.day.max().date())
    feats = [c for c in data.columns if c not in ("y", "day")]

    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=4,
                                      random_state=0)
    m.fit(tr[feats], tr["y"])
    print("val MAE   model:", round(mean_absolute_error(va["y"], m.predict(va[feats])), 2),
          "| persistence:", round(mean_absolute_error(va["y"], va["ci_yday"]), 2))
    # refit on train+val for the final test (hyperparameters were not tuned on test)
    tv = pd.concat([tr, va])
    m.fit(tv[feats], tv["y"])
    te = te.assign(pred=m.predict(te[feats]))
    # seasonal-hour climatology baseline: mean CI by (month, hour) from train+val
    clim = tv.groupby(["month", "hour"])["y"].mean()
    te["clim"] = [clim.loc[(a, b)] for a, b in zip(te["month"], te["hour"])]

    mae = {"persistence (same hour yesterday)": mean_absolute_error(te["y"], te["ci_yday"]),
           "same hour last week": mean_absolute_error(te["y"], te["ci_wk"].fillna(te["ci_yday"])),
           "month x hour climatology": mean_absolute_error(te["y"], te["clim"]),
           "gradient boosting": mean_absolute_error(te["y"], te["pred"])}
    print("\nHourly MAE (gCO2/kWh), TEST:")
    for k, v in mae.items():
        print(f"  {k:36s} {v:6.2f}")

    # ---- scheduling decision ----
    res = {k: [] for k in ["run at midnight (naive)", "run 2-6am (night rule)", "persistence",
                            "climatology", "model", "oracle"]}
    for d, grp in te.groupby("day"):
        grp = grp.sort_values("hour")
        if len(grp) != 24:
            continue
        y = grp["y"].values
        def cost(start):
            return y[start:start + JOB_H].mean()
        res["run at midnight (naive)"].append(cost(0))
        res["run 2-6am (night rule)"].append(cost(2))
        res["persistence"].append(cost(best_window(grp["ci_yday"].values)))
        res["climatology"].append(cost(best_window(grp["clim"].values)))
        res["model"].append(cost(best_window(grp["pred"].values)))
        res["oracle"].append(cost(best_window(y)))
    out = {k: float(np.mean(v)) for k, v in res.items()}
    n = len(res["oracle"])
    print(f"\nScheduling, TEST days={n}: mean gCO2/kWh of the chosen 4h window")
    naive = out["run at midnight (naive)"]
    for k, v in out.items():
        print(f"  {k:26s} {v:7.2f}   vs naive {100*(v-naive)/naive:+5.1f}%")
    ora, nv = out["oracle"], naive
    share = (nv - out["model"]) / (nv - ora)
    print(f"  model captures {100*share:.0f}% of the oracle's possible saving")
    diff = np.array(res["model"]) - np.array(res["persistence"])
    print(f"  model vs persistence: mean {diff.mean():+.2f} g/kWh, model better on "
          f"{(diff<0).mean()*100:.0f}% of days")
    json.dump({"hourly_mae": mae, "schedule_gco2_kwh": out, "test_days": n},
              open("results_baseline.json", "w"), indent=2)


if __name__ == "__main__":
    main()
