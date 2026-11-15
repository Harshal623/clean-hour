"""Live mode: cleanest time in the next 48 hours for Great Britain, from NESO's official forecast.

Why NESO's forecast and not ours: in our 2026 tests NESO's own forecast beat our model in Britain by about
4 to 6 g/kWh (see README), so the live tab uses theirs. No key needed. Falls back to a friendly message offline.
Source: https://carbonintensity.org.uk/  (API: /intensity/{from}/fw48h)
"""
import json
import urllib.request

import numpy as np
import pandas as pd

APPLIANCES = {"Charge my electric car": (4, 10.0), "Run the dishwasher": (2, 1.2),
              "Do laundry (wash + dry)": (3, 3.0), "Heat water (boiler / heat pump)": (3, 3.0)}
WAIT = {"Up to 12 hours": 12, "Up to 24 hours": 24, "Up to 36 hours": 36}


def fetch_forecast(now=None, timeout=10):
    now = now or pd.Timestamp.now(tz="UTC")
    start = now.floor("30min").strftime("%Y-%m-%dT%H:%MZ")
    url = f"https://api.carbonintensity.org.uk/intensity/{start}/fw48h"
    d = json.loads(urllib.request.urlopen(url, timeout=timeout).read())["data"]
    s = pd.Series({pd.Timestamp(r["from"]): r["intensity"]["forecast"] for r in d}).sort_index()
    s = s.dropna()
    h = s.resample("h").mean().dropna()  # hourly mean, label = hour start (UTC)
    return h.iloc[:48]


def _colour(v, lo, hi):
    t = 0 if hi <= lo else min(max((v - lo) / (hi - lo), 0), 1)
    return f"rgb({int(60 + 190 * t)},{int(190 - 110 * t)},80)"


def _label(ts):
    t = ts.tz_convert("Europe/London")
    return f"{t.strftime('%A')} at {(t.hour % 12) or 12} {'AM' if t.hour < 12 else 'PM'}"


def advise_live(appliance, wait, series=None):
    try:
        h = series if series is not None else fetch_forecast()
    except Exception as e:  # offline, rate limit, API change
        return ("<div style='padding:14px;border-radius:10px;background:#fff4e5;border:1px solid #f0c987'>"
                "Live data is not available right now (no internet or the Great Britain feed is down). "
                "Use the Replay tab, which works offline.</div>")
    L, kwh = APPLIANCES[appliance]
    slip = WAIT[wait]
    v = h.values
    if len(v) < L + 2:
        return "<div>Not enough forecast hours yet. Try again in a few minutes.</div>"
    c = np.convolve(v, np.ones(L) / L, mode="valid")[:slip + 1]
    st = int(c.argmin())
    gain = 100 * (c[0] - c[st]) / c[0]
    if gain < 3:
        head, sub = "No clear winner: start whenever suits you", "The forecast sees almost no difference in the next hours."
        st = 0
    else:
        head = f"Start {_label(h.index[st])}"
        sub = (f"The forecast says that is about <b>{gain:.0f}% cleaner</b> than starting now "
               f"(about {(c[0] - c[st]) * kwh:,.0f} grams of CO2 less for {kwh:g} kWh).")
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    cells = []
    for i, (ts, x) in enumerate(h.items()):
        chosen = st <= i < st + L
        border = "3px solid #111" if chosen else "1px solid white"
        cells.append(f"<div title='{_label(ts)}: {x:.0f} g CO2 per kWh' style='flex:1;min-width:8px;height:26px;"
                     f"background:{_colour(x, lo, hi)};border:{border};box-sizing:border-box'></div>")
    return (f"<div style='padding:18px;border-radius:12px;background:#eaf6ee;border:1px solid #bfe3c9'>"
            f"<div style='font-size:28px;font-weight:700;color:#14532d'>{head}</div>"
            f"<div style='font-size:16px;margin-top:6px'>{sub}</div></div>"
            f"<h4 style='margin:16px 0 4px'>The next {len(h)} hours (Great Britain, official NESO forecast)</h4>"
            f"<div style='display:flex'>{''.join(cells)}</div>"
            f"<div style='font-size:13px;margin-top:8px'><span style='color:#2a9d4a'>■</span> cleaner &nbsp;"
            f"<span style='color:#d9534f'>■</span> dirtier &nbsp; <b>Black outline</b> = suggested time. "
            f"Hover a block for the hour. Forecasts change; check again before you start.</div>")
