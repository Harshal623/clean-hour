"""Live mode: cleanest time in the next 48 hours, from official public forecasts.

Great Britain: NESO's official carbon-intensity forecast (https://carbonintensity.org.uk/, /intensity/{from}/fw48h).
  We use theirs, not ours, because NESO's forecast beat our model there in 2026 tests (about 4 to 6 g/kWh).
Germany: Energy-Charts (Fraunhofer ISE) renewable-share forecast (https://api.energy-charts.info/ren_share_forecast).
  This is a forecast of the renewable SHARE of electricity load, not of carbon intensity, so for Germany we
  recommend the hours with the highest forecast renewable share and do not quote grams of CO2.
No keys needed. Any failure (offline, API change) shows a friendly message; the Replay tab is untouched.
"""
import json
import urllib.request

import numpy as np
import pandas as pd

APPLIANCES = {"Charge my electric car": (4, 10.0), "Run the dishwasher": (2, 1.2),
              "Do laundry (wash + dry)": (3, 3.0), "Heat water (boiler / heat pump)": (3, 3.0)}
WAIT = {"Up to 12 hours": 12, "Up to 24 hours": 24, "Up to 36 hours": 36}
REGIONS = ["Great Britain", "Germany"]
TZ = {"Great Britain": "Europe/London", "Germany": "Europe/Berlin"}


def fetch_forecast(now=None, timeout=10):
    """Great Britain: hourly forecast carbon intensity (g/kWh), label = hour start (UTC)."""
    now = now or pd.Timestamp.now(tz="UTC")
    start = now.floor("30min").strftime("%Y-%m-%dT%H:%MZ")
    url = f"https://api.carbonintensity.org.uk/intensity/{start}/fw48h"
    d = json.loads(urllib.request.urlopen(url, timeout=timeout).read())["data"]
    s = pd.Series({pd.Timestamp(r["from"]): r["intensity"]["forecast"] for r in d}).sort_index().dropna()
    return s.resample("h").mean().dropna().iloc[:48]


def fetch_germany(now=None, timeout=10):
    """Germany: hourly forecast renewable share of load (%), label = hour start (UTC), from now on."""
    now = now or pd.Timestamp.now(tz="UTC")
    d = json.loads(urllib.request.urlopen("https://api.energy-charts.info/ren_share_forecast?country=de",
                                          timeout=timeout).read())
    idx = pd.to_datetime(d["unix_seconds"], unit="s", utc=True)
    s = pd.Series(d["ren_share"], index=idx, dtype=float).dropna()
    h = s.resample("h").mean().dropna()
    return h[h.index >= now.floor("h")].iloc[:48]


def _colour(v, lo, hi):
    t = 0 if hi <= lo else min(max((v - lo) / (hi - lo), 0), 1)
    return f"rgb({int(60 + 190 * t)},{int(190 - 110 * t)},80)"


def _label(ts, region="Great Britain"):
    t = ts.tz_convert(TZ[region])
    return f"{t.strftime('%A')} at {(t.hour % 12) or 12} {'AM' if t.hour < 12 else 'PM'}"


def advise_live(appliance, wait, region="Great Britain", series=None):
    try:
        if series is not None:
            h = series
        else:
            h = fetch_germany() if region == "Germany" else fetch_forecast()
    except Exception:  # offline, rate limit, API change
        return ("<div style='padding:14px;border-radius:10px;background:#fff4e5;border:1px solid #f0c987'>"
                f"Live data is not available right now (no internet or the {region} feed is down). "
                "Use the Replay tab, which works offline.</div>")
    L, kwh = APPLIANCES[appliance]
    slip = WAIT[wait]
    share_mode = region == "Germany"
    metric = (100 - h.values) if share_mode else h.values  # lower = cleaner
    if len(metric) < L + 2:
        return "<div>Not enough forecast hours yet. Try again in a few minutes.</div>"
    c = np.convolve(metric, np.ones(L) / L, mode="valid")[:slip + 1]
    st = int(c.argmin())
    if share_mode:
        now_share = h.values[:L].mean()
        best_share = h.values[st:st + L].mean()
        gain = best_share - now_share  # percentage points more renewable
        ok = gain >= 3
    else:
        gain = 100 * (c[0] - c[st]) / c[0]
        ok = gain >= 3
    if not ok:
        head, sub = "No clear winner: start whenever suits you", "The forecast sees almost no difference in the next hours."
        st = 0
    else:
        head = f"Start {_label(h.index[st], region)}"
        if share_mode:
            sub = (f"The forecast renewable share is about <b>{best_share:.0f}%</b> then, versus about "
                   f"<b>{now_share:.0f}%</b> if you start now. More wind and sun means cleaner power.")
        else:
            sub = (f"The forecast says that is about <b>{gain:.0f}% cleaner</b> than starting now "
                   f"(about {(c[0] - c[st]) * kwh:,.0f} grams of CO2 less for {kwh:g} kWh).")
    lo, hi = np.percentile(metric, 5), np.percentile(metric, 95)
    unit = "% renewable" if share_mode else "g CO2 per kWh"
    cells = []
    for i, (ts, x) in enumerate(h.items()):
        chosen = st <= i < st + L
        border = "3px solid #111" if chosen else "1px solid white"
        val = (100 - x) if share_mode else x
        cells.append(f"<div title='{_label(ts, region)}: {x:.0f} {unit}' style='flex:1;min-width:8px;height:26px;"
                     f"background:{_colour(val, lo, hi)};border:{border};box-sizing:border-box'></div>")
    source = "Fraunhofer ISE Energy-Charts renewable-share forecast" if share_mode else "official NESO forecast"
    return (f"<div style='padding:18px;border-radius:12px;background:#eaf6ee;border:1px solid #bfe3c9'>"
            f"<div style='font-size:28px;font-weight:700;color:#14532d'>{head}</div>"
            f"<div style='font-size:16px;margin-top:6px'>{sub}</div></div>"
            f"<h4 style='margin:16px 0 4px'>The next {len(h)} hours ({region}, {source})</h4>"
            f"<div style='display:flex'>{''.join(cells)}</div>"
            f"<div style='font-size:13px;margin-top:8px'><span style='color:#2a9d4a'>■</span> cleaner &nbsp;"
            f"<span style='color:#d9534f'>■</span> dirtier &nbsp; <b>Black outline</b> = suggested time. "
            f"Hover a block for the hour. Forecasts change; check again before you start.</div>")
