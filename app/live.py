"""Live mode: cleanest time in the next 48 hours, from public forecasts.

Great Britain: NESO's official carbon forecast
  https://carbonintensity.org.uk/  (route /intensity/{from}/fw48h)
  We use their forecast, not ours, because it beat our model there
  in the 2026 tests (by about 4 to 6 g/kWh).
Germany: Energy-Charts (Fraunhofer ISE) renewable-share forecast
  https://api.energy-charts.info/ren_share_forecast
  This is the share of power from wind and sun, not grams of CO2,
  so for Germany we pick the hours with the most renewables and we
  never quote grams.
No keys needed. If something fails (offline, API change) we show a
friendly message instead of crashing.
"""
import json
import urllib.request

import numpy as np
import pandas as pd

APPLIANCES = {
    "Charge my electric car": (4, 10.0),
    "Run the dishwasher": (2, 1.2),
    "Do laundry (wash + dry)": (3, 3.0),
    "Heat water (boiler / heat pump)": (3, 3.0),
}
WAIT = {"Up to 12 hours": 12, "Up to 24 hours": 24, "Up to 36 hours": 36}
REGIONS = ["Great Britain", "Germany"]
TZ = {"Great Britain": "Europe/London", "Germany": "Europe/Berlin"}

# What counts as "usual" for the green / red message.
# Great Britain: app.py sets this to the median 2026 intensity.
# Germany: half of the power from renewables.
# If it is not set we use the median of the forecast on screen.
TYPICAL = {"Great Britain": None, "Germany": 50.0}


def pick_job(appliance, custom_hours=None, custom_kwh=None):
    """Hours and kWh for the job. Typed numbers beat the dropdown."""
    hours, kwh = APPLIANCES[appliance]
    if custom_hours:
        hours = int(round(custom_hours))
        hours = max(1, min(12, hours))
    if custom_kwh and custom_kwh > 0:
        kwh = float(custom_kwh)
    return hours, kwh


def fetch_forecast(now=None, timeout=10):
    """Great Britain: hourly forecast in g CO2 per kWh (UTC hour start)."""
    now = now or pd.Timestamp.now(tz="UTC")
    start = now.floor("30min").strftime("%Y-%m-%dT%H:%MZ")
    url = f"https://api.carbonintensity.org.uk/intensity/{start}/fw48h"
    raw = urllib.request.urlopen(url, timeout=timeout).read()
    rows = json.loads(raw)["data"]
    s = pd.Series(
        {pd.Timestamp(r["from"]): r["intensity"]["forecast"] for r in rows}
    )
    s = s.sort_index().dropna()
    return s.resample("h").mean().dropna().iloc[:48]


def fetch_germany(now=None, timeout=10):
    """Germany: hourly forecast renewable share in % (UTC hour start)."""
    now = now or pd.Timestamp.now(tz="UTC")
    url = "https://api.energy-charts.info/ren_share_forecast?country=de"
    d = json.loads(urllib.request.urlopen(url, timeout=timeout).read())
    times = pd.to_datetime(d["unix_seconds"], unit="s", utc=True)
    s = pd.Series(d["ren_share"], index=times, dtype=float).dropna()
    h = s.resample("h").mean().dropna()
    return h[h.index >= now.floor("h")].iloc[:48]


def colour(v, lo, hi):
    """Green for low values, red for high ones."""
    t = 0 if hi <= lo else min(max((v - lo) / (hi - lo), 0), 1)
    red = int(60 + 190 * t)
    green = int(190 - 110 * t)
    return f"rgb({red},{green},80)"


def label(ts, region="Great Britain"):
    t = ts.tz_convert(TZ[region])
    clock = (t.hour % 12) or 12
    ampm = "AM" if t.hour < 12 else "PM"
    return f"{t.strftime('%A, %b')} {t.day} at {clock} {ampm}"


def card_html(head, sub, frame, bg, border, text):
    sub = sub.replace("<b>", f"<b style='color:{text}'>")
    return (
        f"<div style='padding:18px;border-radius:12px;"
        f"background:{bg};border:1px solid {border}'>"
        f"<div style='font-size:28px;font-weight:700;color:{text}'>"
        f"{head}</div>"
        f"<div style='font-size:16px;margin-top:6px;color:#1f2937'>"
        f"{sub}</div>"
        f"<div style='font-size:13px;margin-top:6px;color:#374151'>"
        f"Your time frame: {frame}.</div></div>"
    )


def advise_live(
    appliance,
    wait,
    region="Great Britain",
    custom_hours=None,
    custom_kwh=None,
    series=None,
):
    try:
        if series is not None:
            h = series
        elif region == "Germany":
            h = fetch_germany()
        else:
            h = fetch_forecast()
    except Exception:  # offline, rate limit, API change
        return (
            "<div style='padding:14px;border-radius:10px;"
            "background:#fff4e5;border:1px solid #f0c987;color:#1f2937'>"
            f"Live data is not available right now (no internet or the "
            f"{region} feed is down). Use the Replay tab, which works "
            "offline.</div>"
        )

    hours, kwh = pick_job(appliance, custom_hours, custom_kwh)
    slip = WAIT[wait]
    share_mode = region == "Germany"
    # lower is cleaner, so flip the renewable share
    metric = (100 - h.values) if share_mode else h.values
    if len(metric) < hours + 2:
        return "<div>Not enough forecast yet. Try again in a minute.</div>"

    window = np.convolve(metric, np.ones(hours) / hours, mode="valid")
    window = window[: slip + 1]
    best = int(window.argmin())

    if share_mode:
        share_now = h.values[:hours].mean()
        share_best = h.values[best : best + hours].mean()
        gain = share_best - share_now  # points of renewable share
    else:
        gain = 100 * (window[0] - window[best]) / window[0]
    moved = gain >= 3

    last = min(len(h) - 1, slip)
    frame = f"{label(h.index[0], region)} to {label(h.index[last], region)}"
    bg, border, text = "#eaf6ee", "#bfe3c9", "#14532d"

    if not moved:
        best = 0
        usual = TYPICAL.get(region)
        if usual is None:
            usual = float(np.median(h.values))
        if share_mode:
            is_green = h.values[:hours].mean() >= usual
        else:
            is_green = window[0] <= usual
        if is_green:
            head = "Green: start whenever you like within your time frame"
            sub = (
                f"Power looks cleaner than usual all through {frame}, "
                "and no hour is much better than another."
            )
        else:
            bg, border, text = "#fdecea", "#f1b7b1", "#8a1c13"
            head = "Red: if you can, wait longer"
            sub = (
                f"Power looks dirtier than usual across {frame} and no "
                "hour is much cleaner. Pick a longer wait if you can, "
                "or start now if it cannot wait."
            )
    else:
        head = f"Start {label(h.index[best], region)}"
        if share_mode:
            sub = (
                f"The forecast renewable share is about "
                f"<b>{share_best:.0f}%</b> then, versus about "
                f"<b>{share_now:.0f}%</b> if you start now. "
                "More wind and sun means cleaner power."
            )
        else:
            saved = (window[0] - window[best]) * kwh
            sub = (
                f"The forecast says that is about <b>{gain:.0f}% "
                f"cleaner</b> than starting now (about {saved:,.0f} "
                f"grams of CO2 less for {kwh:g} kWh)."
            )

    lo, hi = np.percentile(metric, 5), np.percentile(metric, 95)
    unit = "% renewable" if share_mode else "g CO2 per kWh"
    cells = []
    for i, (ts, x) in enumerate(h.items()):
        chosen = best <= i < best + hours
        border_css = "3px solid #111" if chosen else "1px solid white"
        shade = (100 - x) if share_mode else x
        cells.append(
            f"<div title='{label(ts, region)}: {x:.0f} {unit}' "
            f"style='flex:1;min-width:8px;height:26px;"
            f"background:{colour(shade, lo, hi)};"
            f"border:{border_css};box-sizing:border-box'></div>"
        )

    source = "official NESO forecast"
    if share_mode:
        source = "Fraunhofer ISE Energy-Charts renewable-share forecast"
    return (
        card_html(head, sub, frame, bg, border, text)
        + f"<h4 style='margin:16px 0 4px'>The next {len(h)} hours "
        f"({region}, {source}), {hours}-hour job</h4>"
        + f"<div style='display:flex'>{''.join(cells)}</div>"
        + "<div style='font-size:13px;margin-top:8px'>"
        "<span style='color:#2a9d4a'>■</span> cleaner &nbsp;"
        "<span style='color:#d9534f'>■</span> dirtier &nbsp; "
        "<b>Black outline</b> = suggested time. Hover a block for "
        "the hour. Forecasts change, so check again before you start."
        "</div>"
    )
