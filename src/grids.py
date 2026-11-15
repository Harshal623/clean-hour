"""Hourly carbon intensity (gCO2/kWh) for five grids on three continents, plus local weather.

  Virginia/Mid-Atlantic (PJM)  EIA-930 fuel mix x emission factors   (already cached by load_data.py)
  California (CISO)            EIA-930 fuel mix x emission factors
  Texas (ERCOT)                EIA-930 fuel mix x emission factors
  Germany                      Energy-Charts (Fraunhofer ISE) public power x emission factors
  Great Britain                NESO Carbon Intensity API (official actual + NESO's own forecast)
Each loader caches to data/grid_<key>.csv with columns: ci (hourly mean, UTC end-of-hour index),
and optionally demand_fcst. Missing hours stay NaN (never filled).
Run from carbon/:  python -I src/grids.py
"""
import io
import json
import os
import sys
import urllib.request

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from load_data import EF, FUELS, HALVES, URL, _pick, carbon_intensity, load_grid  # noqa: E402

GRIDS = {  # key: name, timezone, weather point (lat, lon)
    "pjm": ("Virginia / Mid-Atlantic (USA)", "America/New_York", (39.04, -77.49)),
    "ciso": ("California (USA)", "America/Los_Angeles", (36.8, -119.8)),
    "erco": ("Texas (USA)", "America/Chicago", (31.0, -97.5)),
    "de": ("Germany", "Europe/Berlin", (51.0, 10.0)),
    "gb": ("Great Britain", "Europe/London", (53.0, -1.5)),
}
LAST = pd.Timestamp("2026-11-13 23:00")  # keep clear of unfinished final days


def _get(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=300).read()
        except Exception as e:  # noqa
            err = e
    raise err


def load_eia_multi(bas=("CISO", "ERCO")):
    todo = [b for b in bas if not os.path.exists(f"data/grid_{b.lower()}.csv")]
    if not todo:
        return
    frames = {b: [] for b in todo}
    for y, h in HALVES:
        print("downloading", y, h, flush=True)
        df = pd.read_csv(io.BytesIO(_get(URL.format(y=y, h=h))), low_memory=False)
        for b in todo:
            d = df[df["Balancing Authority"] == b]
            t = pd.to_datetime(d["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p")
            g = pd.DataFrame(index=t)
            for short, stems in FUELS.items():
                g[short] = _pick(d, stems).values
            g["demand_fcst"] = pd.to_numeric(d["Demand Forecast (MW)"], errors="coerce").values
            frames[b].append(g)
    for b in todo:
        g = pd.concat(frames[b]).sort_index()
        g = g[~g.index.duplicated()]
        g = g.loc[:g[list(FUELS)].dropna(how="all").index.max()]  # cut placeholder rows
        out = pd.DataFrame({"ci": carbon_intensity(g), "demand_fcst": g["demand_fcst"]})
        out.index.name = "utc_end_of_hour"
        out.to_csv(f"data/grid_{b.lower()}.csv")
        print(b, out.shape, out.index.min(), "->", out.index.max())


def load_pjm():
    f = "data/grid_pjm.csv"
    if not os.path.exists(f):
        g = load_grid().loc[:"2026-11-14 05:00"]
        out = pd.DataFrame({"ci": carbon_intensity(g), "demand_fcst": g["demand_fcst"]})
        out.index.name = "utc_end_of_hour"
        out.to_csv(f)


DE_MAP = {  # Energy-Charts production type -> our fuel
    "Fossil brown coal / lignite": "coal", "Fossil hard coal": "coal",
    "Fossil coal-derived gas": "coal", "Fossil gas": "gas", "Fossil oil": "oil",
    "Nuclear": "nuclear", "Biomass": "other", "Waste": "other", "Others": "other",
    "Geothermal": "other", "Hydro Run-of-River": "hydro", "Hydro water reservoir": "hydro",
    "Wind offshore": "wind", "Wind onshore": "wind", "Solar": "solar"}


def load_de():
    f = "data/grid_de.csv"
    if os.path.exists(f):
        return
    parts = []
    for y in range(2023, 2027):
        end = f"{y}-12-31" if y < 2026 else "2026-11-13"
        d = json.loads(_get(f"https://api.energy-charts.info/public_power?country=de&start={y}-01-01&end={end}"))
        t = pd.to_datetime(d["unix_seconds"], unit="s")
        g = pd.DataFrame(index=t)
        for pt in d["production_types"]:
            k = DE_MAP.get(pt["name"])
            if k:
                v = pd.to_numeric(pd.Series(pt["data"], index=t), errors="coerce")
                g[k] = g[k].add(v, fill_value=0) if k in g else v
        parts.append(g)
    g = pd.concat(parts)
    g = g[~g.index.duplicated()].sort_index()
    g = g.resample("h", label="right", closed="right").mean()  # end-of-hour, like EIA
    for k in FUELS:
        if k not in g:
            g[k] = 0.0
    out = pd.DataFrame({"ci": carbon_intensity(g)})
    out.index.name = "utc_end_of_hour"
    out.to_csv(f)
    print("DE", out.shape, out.index.min(), "->", out.index.max())


def load_gb():
    f = "data/grid_gb.csv"
    if os.path.exists(f):
        return
    rows, t0 = [], pd.Timestamp("2023-01-01")
    while t0 < LAST:
        t1 = min(t0 + pd.Timedelta(days=13), LAST)
        u = ("https://api.carbonintensity.org.uk/intensity/"
             f"{t0:%Y-%m-%dT%H:%MZ}/{t1:%Y-%m-%dT%H:%MZ}")
        for r in json.loads(_get(u))["data"]:
            rows.append((r["to"], r["intensity"].get("actual"), r["intensity"].get("forecast")))
        t0 = t1
    d = pd.DataFrame(rows, columns=["to", "actual", "neso_forecast"])
    d["to"] = pd.to_datetime(d["to"], utc=True).dt.tz_localize(None)
    d = d.drop_duplicates("to").set_index("to").sort_index()
    h = d.resample("h", label="right", closed="right").mean()
    out = pd.DataFrame({"ci": h["actual"], "neso_forecast": h["neso_forecast"]})
    out.index.name = "utc_end_of_hour"
    out.to_csv(f)
    print("GB", out.shape, out.index.min(), "->", out.index.max())


def load_weather_at(key, lat, lon, start, end):
    f = f"data/weather_{key}.csv"
    if os.path.exists(f):
        return pd.read_csv(f, index_col=0, parse_dates=True)
    v = "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,shortwave_radiation"
    u = ("https://historical-forecast-api.open-meteo.com/v1/forecast?"
         f"latitude={lat}&longitude={lon}&start_date={start}&end_date={end}&hourly={v}&timezone=UTC")
    w = pd.DataFrame(json.loads(_get(u))["hourly"])
    w["time"] = pd.to_datetime(w["time"]) + pd.Timedelta(hours=1)
    w = w.set_index("time")
    w.index.name = "utc_end_of_hour"
    w.to_csv(f)
    return w


def load_grid_data(key):
    """Return (ci DataFrame, weather DataFrame) on a common hourly UTC index, NaN for gaps."""
    g = pd.read_csv(f"data/grid_{key}.csv", index_col=0, parse_dates=True)
    g = g.loc[:min(g.index.max(), LAST)]
    full = pd.date_range(g.index.min().ceil("h"), g.index.max(), freq="h")
    g = g.reindex(full)
    lat, lon = GRIDS[key][2]
    w = load_weather_at(key, lat, lon, "2023-01-01", "2026-11-13").reindex(full)
    return g, w


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    load_pjm()
    load_de()
    load_gb()
    load_eia_multi()
    for k in GRIDS:
        g, w = load_grid_data(k)
        print(f"{k:5s} hours {len(g)}  {g.index.min()} -> {g.index.max()}  missing ci {int(g['ci'].isna().sum())}"
              f"  mean ci {g['ci'].mean():.0f}  std {g['ci'].std():.0f}  weather missing {int(w.isna().any(axis=1).sum())}")
