"""Download + cache hourly Dominion (DOM) grid data and Loudoun weather.

Sources (all free, no key):
  - EIA-930 hourly balancing-authority data (fuel mix, demand, day-ahead demand forecast)
    https://www.eia.gov/electricity/gridmonitor/
  - Open-Meteo historical *forecast* API (weather as it was forecast, avoids leakage)
    https://open-meteo.com/en/docs/historical-forecast-api
Run: python -I src/load_data.py   (from the carbon/ folder)
"""
import io
import os
import urllib.request

import numpy as np
import pandas as pd

BA = "PJM"  # Dominion (DOM) is a zone INSIDE PJM; EIA-930 has no DOM-only fuel mix
LAT, LON = 39.04, -77.49  # Ashburn, Loudoun County VA
HALVES = [(2023, "Jan_Jun"), (2023, "Jul_Dec"), (2024, "Jan_Jun"), (2024, "Jul_Dec"),
          (2025, "Jan_Jun"), (2025, "Jul_Dec"), (2026, "Jan_Jun"), (2026, "Jul_Dec")]
URL = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_{y}_{h}.csv"
SUB_URL = URL.replace("BALANCE", "SUBREGION")
FUELS = {  # short name -> EIA column stems (schema changed mid-2024; storage excluded)
    "coal": ["Coal"], "gas": ["Natural Gas"], "nuclear": ["Nuclear"],
    "oil": ["All Petroleum Products"],
    "hydro": ["Hydropower and Pumped Storage", "Hydropower Excluding Pumped Storage"],
    "solar": ["Solar", "Solar without Integrated Battery Storage",
              "Solar with Integrated Battery Storage"],
    "wind": ["Wind", "Wind without Integrated Battery Storage",
             "Wind with Integrated Battery Storage"],
    "other": ["Other Fuel Sources", "Geothermal"], "unknown": ["Unknown Fuel Sources"]}
# Lifecycle gCO2e/kWh, IPCC AR5 WG3 Annex III medians (Schlomer et al. 2014).
# 'other' and 'unknown' are assumptions (see README); we run a sensitivity check.
EF = {"coal": 820, "gas": 490, "nuclear": 12, "oil": 650, "hydro": 24,
      "solar": 41, "wind": 11, "other": 230, "unknown": 230}


def _pick(df, stems):
    """For each stem: coalesce Adjusted -> Imputed -> raw EIA value; then sum stems."""
    total = None
    for stem in stems:
        base = f"Net Generation (MW) from {stem}"
        cols = [c for c in (f"{base} (Adjusted)", f"{base} (Imputed)", base) if c in df.columns]
        if not cols:
            continue
        s = pd.to_numeric(df[cols[0]], errors="coerce")
        for c in cols[1:]:
            s = s.fillna(pd.to_numeric(df[c], errors="coerce"))
        total = s if total is None else total.add(s, fill_value=0)
    return total if total is not None else pd.Series(np.nan, index=df.index)


def load_grid():
    out = "data/pjm_hourly.csv"
    if os.path.exists(out):
        return pd.read_csv(out, index_col=0, parse_dates=True)
    frames = []
    for y, h in HALVES:
        url = URL.format(y=y, h=h)
        try:
            print("downloading", url)
            raw = urllib.request.urlopen(url, timeout=300).read()
        except Exception as e:  # noqa
            print("  skipped:", e)
            continue
        df = pd.read_csv(io.BytesIO(raw), low_memory=False)
        df = df[df["Balancing Authority"] == BA].copy()
        t = pd.to_datetime(df["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p")
        g = pd.DataFrame(index=t)
        for short, stems in FUELS.items():
            g[short] = _pick(df, stems).values
        g["demand"] = pd.to_numeric(df["Demand (MW) (Adjusted)"].fillna(df["Demand (MW)"]),
                                    errors="coerce").values
        g["demand_fcst"] = pd.to_numeric(df["Demand Forecast (MW)"], errors="coerce").values
        try:  # Dominion-zone demand (the local load signal for Loudoun)
            sr = pd.read_csv(io.BytesIO(urllib.request.urlopen(SUB_URL.format(y=y, h=h),
                                                               timeout=300).read()))
            sr = sr[(sr["Balancing Authority"] == BA) & (sr["Sub-Region"] == "DOM")]
            st = pd.to_datetime(sr["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p")
            g["dom_demand"] = pd.Series(pd.to_numeric(sr["Demand (MW)"]).values, index=st)
        except Exception as e:  # noqa
            print("  no subregion file:", e)
        frames.append(g)
    g = pd.concat(frames).sort_index()
    g = g[~g.index.duplicated()]
    g.index.name = "utc_end_of_hour"
    g.to_csv(out)
    return g


def load_weather(start, end):
    out = "data/loudoun_weather.csv"
    if os.path.exists(out):
        return pd.read_csv(out, index_col=0, parse_dates=True)
    vars_ = "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,shortwave_radiation"
    url = ("https://historical-forecast-api.open-meteo.com/v1/forecast?"
           f"latitude={LAT}&longitude={LON}&start_date={start}&end_date={end}"
           f"&hourly={vars_}&timezone=UTC")
    import json
    d = json.loads(urllib.request.urlopen(url, timeout=300).read())["hourly"]
    w = pd.DataFrame(d)
    w["time"] = pd.to_datetime(w["time"]) + pd.Timedelta(hours=1)  # align to end-of-hour
    w = w.set_index("time")
    w.index.name = "utc_end_of_hour"
    w.to_csv(out)
    return w


def carbon_intensity(g, ef=EF):
    gen = g[list(FUELS)].fillna(0).clip(lower=0)
    tot = gen.sum(axis=1).replace(0, np.nan)
    ci = sum(gen[k] * v for k, v in ef.items()) / tot
    return ci.rename("ci")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    g = load_grid()
    ci = carbon_intensity(g)
    print(g.shape, g.index.min(), "->", g.index.max())
    print("missing share per column:\n", g.isna().mean().round(3).to_string())
    print("carbon intensity gCO2/kWh:", ci.describe().round(1).to_dict())
    w = load_weather(g.index.min().date(), min(g.index.max().date(), pd.Timestamp.today().date() - pd.Timedelta(days=2)))
    print("weather", w.shape, w.index.min(), "->", w.index.max(), w.isna().mean().round(3).to_dict())
