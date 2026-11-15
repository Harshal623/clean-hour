"""Feasibility only: NOAA CO-OPS gauge 8594900 (Washington DC), hourly observed vs predicted tide."""
import json, os, urllib.request
import numpy as np, pandas as pd
ST = "8594900"
FT = 0.3048
MLLW_STND_FT = 4.55
FL = {"NOS minor": 9.49, "NWS minor": 9.85, "NOS moderate": 10.44}  # ft above station datum (NOAA floodlevels API)
def thr_m(v): return (v - MLLW_STND_FT) * FT  # metres above MLLW
def get(product, y):
    f = f"data/flood/{product}_{y}.csv"
    if os.path.exists(f): return pd.read_csv(f, index_col=0, parse_dates=True)
    end = f"{y}1231" if y < 2026 else "20261113"
    u = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
         f"product={'hourly_height' if product=='water_level' else product}&application=hs_hackathon&begin_date={y}0101&end_date={end}"
         f"&datum=MLLW&station={ST}&time_zone=gmt&units=metric{'&interval=h' if product=='predictions' else ''}&format=json")
    d = json.loads(urllib.request.urlopen(u, timeout=180).read())
    rows = d.get("data") or d.get("predictions") or []
    df = pd.DataFrame(rows)
    if df.empty: print(product, y, d.get("error")); return df
    df["t"] = pd.to_datetime(df["t"]); df["v"] = pd.to_numeric(df["v"], errors="coerce")
    df = df.set_index("t")[["v"]]; df.to_csv(f); return df
def events(s, thr, gap_h=12):
    above = s > thr
    ev, last = [], None
    for t in s.index[above.values]:
        if last is None or (t - last) > pd.Timedelta(hours=gap_h): ev.append(t)
        last = t
    return pd.Series(ev, dtype="datetime64[ns]")
if __name__ == "__main__":
    obs = pd.concat([get("water_level", y) for y in range(2015, 2027)])
    pred = pd.concat([get("predictions", y) for y in range(2015, 2027)])
    d = pd.DataFrame({"obs": obs["v"], "pred": pred["v"]}).dropna(subset=["obs"])
    print("hourly rows", len(d), d.index.min(), "->", d.index.max(), "| missing obs share by year:")
    full = pd.date_range("2015-01-01", d.index.max(), freq="h")
    print((1 - d["obs"].reindex(full).notna().groupby(full.year).mean()).round(3).to_dict())
    d["surge"] = d["obs"] - d["pred"]
    print("surge std m:", round(d["surge"].std(), 3), "| max obs m MLLW:", round(d["obs"].max(), 2), d["obs"].idxmax())
    for name, v in FL.items():
        t = thr_m(v)
        e = events(d["obs"], t)
        print(f"\n{name} = {v} ft STND = {t:.3f} m MLLW -> events/yr:", e.groupby(e.dt.year).size().to_dict(),
              "| 2024-2026:", int((e.dt.year >= 2024).sum()))
        ep = events(d["pred"].dropna(), t)
        print("   events from astronomical tide alone/yr:", ep.groupby(ep.dt.year).size().to_dict())
    d.to_csv("data/flood/hourly_2015_2026.csv")
