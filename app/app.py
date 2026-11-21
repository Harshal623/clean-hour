"""Clean-Hour: tells you the cleanest time to run a big appliance.

The Replay tab uses real days from 2026 that the model never saw.
The Live tab (Great Britain, Germany) uses today's public forecasts.
Run from the repo root:
    python app/app.py
"""
import importlib.util
import os

import gradio as gr
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
DF = pd.read_csv(
    os.path.join(RES, "test_predictions_all.csv.gz"), parse_dates=["day"]
)
SUM = pd.read_csv(os.path.join(RES, "multigrid_summary.csv"))

REGIONS = {
    "California, USA": "ciso",
    "Texas, USA": "erco",
    "Virginia / Mid-Atlantic, USA": "pjm",
    "Germany": "de",
    "Great Britain": "gb",
}
# label: (hours it runs, kWh per run)
APPLIANCES = {
    "Charge my electric car": (4, 10.0),
    "Run the dishwasher": (2, 1.2),
    "Do laundry (wash + dry)": (3, 3.0),
    "Heat water (boiler / heat pump)": (3, 3.0),
}
WAIT = {
    "Just tonight (up to 12 hours)": 12,
    "Until tomorrow (24 hours)": 24,
    "I'm flexible: up to 3 days": 72,
}

# only days that exist for all five regions
day_sets = [set(DF[DF.grid == g].day) for g in REGIONS.values()]
common = set.intersection(*day_sets)
DAYS = sorted(common)
DAY_LABELS = [d.strftime("%a %d %b %Y") for d in DAYS]


def pick_job(appliance, custom_hours=None, custom_kwh=None):
    """Hours and kWh for the job. Typed numbers beat the dropdown."""
    hours, kwh = APPLIANCES[appliance]
    if custom_hours:
        hours = int(round(custom_hours))
        hours = max(1, min(12, hours))
    if custom_kwh and custom_kwh > 0:
        kwh = float(custom_kwh)
    return hours, kwh


def clock(h):
    h = int(h) % 24
    ampm = "AM" if h < 12 else "PM"
    return f"{(h % 12) or 12} {ampm}"


def when(j, release):
    d = release + pd.Timedelta(hours=int(j))
    return f"{d.strftime('%A, %b')} {d.day} at {clock(d.hour)}"


def day_name(d):
    return f"{d.strftime('%a %b')} {d.day}"


def colour(v, lo, hi):
    """Green for low values, red for high ones."""
    t = 0 if hi <= lo else min(max((v - lo) / (hi - lo), 0), 1)
    red = int(60 + 190 * t)
    green = int(190 - 110 * t)
    return f"rgb({red},{green},80)"


def bar_html(prof, lo, hi, start, hours, nshow, release=None):
    """One row of 24 coloured blocks per day."""
    rows = []
    n_days = int(np.ceil(nshow / 24))
    for d in range(n_days):
        cells = []
        for h in range(24):
            j = d * 24 + h
            if j >= len(prof) or j >= nshow:
                cells.append("<div style='flex:1;height:22px'></div>")
                continue
            chosen = start <= j < start + hours
            border = "3px solid #111" if chosen else "1px solid white"
            cells.append(
                f"<div title='{clock(h)}: {prof[j]:.0f} g CO2 per kWh' "
                f"style='flex:1;height:22px;"
                f"background:{colour(prof[j], lo, hi)};"
                f"border:{border};box-sizing:border-box'></div>"
            )
        name = f"Day {d + 1}"
        if release is not None:
            when_day = release + pd.Timedelta(days=d)
            name += f": {day_name(when_day)}"
        rows.append(
            f"<div style='margin:3px 0'>"
            f"<div style='font-size:12px;color:#555'>{name}</div>"
            f"<div style='display:flex'>{''.join(cells)}</div></div>"
        )
    scale = (
        "<div style='display:flex;justify-content:space-between;"
        "font-size:12px;color:#555;margin-top:2px'>"
        "<span>12 AM</span><span>6 AM</span><span>12 PM</span>"
        "<span>6 PM</span><span>11 PM</span></div>"
    )
    legend = (
        "<div style='font-size:13px;margin-top:8px'>"
        "<span style='color:#2a9d4a'>■</span> cleaner power &nbsp;"
        "<span style='color:#d9534f'>■</span> dirtier power &nbsp; "
        "<b>Black outline</b> = the time we suggest</div>"
    )
    return "".join(rows) + scale + legend


def card_html(head, sub, frame, bg, border, text):
    # bold text needs its own colour or the dark theme makes it white
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


def advise(region, appliance, wait, day_label, custom_hours=None,
           custom_kwh=None):
    g = REGIONS[region]
    hours, kwh = pick_job(appliance, custom_hours, custom_kwh)
    day = DAYS[DAY_LABELS.index(day_label)]
    d = DF[(DF.grid == g) & (DF.day == day)].sort_values("j")
    actual, forecast = d.y.values, d.pred.values

    def windows(a):
        # average of every window of this many hours
        return np.convolve(a, np.ones(hours) / hours, mode="valid")

    # we only have 76 hours of data, so long jobs can't wait the full 3 days
    slip = min(WAIT[wait], len(windows(forecast)) - 1)
    nshow = min(slip + hours, len(forecast))

    w_pred = windows(forecast)[: slip + 1]
    w_act = windows(actual)
    start = int(w_pred.argmin())
    now_pred, now_act = w_pred[0], w_act[0]
    gain_pred = 100 * (now_pred - w_pred[start]) / now_pred
    best = int(w_act[: slip + 1].argmin())
    gain_act = 100 * (now_act - w_act[start]) / now_act
    gain_best = 100 * (now_act - w_act[best]) / now_act
    grams = (now_act - w_act[start]) * kwh

    release = pd.Timestamp(day)
    typical = float(DF[DF.grid == g].clim.median())  # usual g/kWh here
    frame = f"{when(0, release)} to {when(slip, release)}"
    moved = gain_pred >= 3

    bg, border, text = "#eaf6ee", "#bfe3c9", "#14532d"
    if moved:
        end = start + hours
        head = f"Start {when(start, release)}"
        sub = (
            f"It will run until about {when(end, release)}. We expect "
            f"that to be about <b>{gain_pred:.0f}% cleaner</b> than "
            "starting at midnight."
        )
        if w_pred[start] > typical:
            sub += (
                " Heads-up: even this is dirtier than usual for your "
                "region, so if you can wait longer, choose the 3-day "
                "option."
            )
    else:
        start = 0
        if now_pred <= typical:
            head = "Green: start whenever you like within your time frame"
            sub = (
                "Power is cleaner than usual all through your time "
                "frame, and no hour is much better than another."
            )
        else:
            bg, border, text = "#fdecea", "#f1b7b1", "#8a1c13"
            head = "Red: if you can, wait longer"
            sub = (
                f"Power is dirtier than usual across your whole time "
                f"frame ({frame}) and no hour is much cleaner. Pick a "
                "longer wait (up to 3 days) to give the tool a cleaner "
                "window, or start now if it cannot wait."
            )
    frame += f" ({hours}-hour job)"
    card = card_html(head, sub, frame, bg, border, text)

    lo = np.percentile(forecast[:nshow], 5)
    hi = np.percentile(forecast[:nshow], 95)
    n_days = int(np.ceil(nshow / 24))
    strip = (
        f"<h4 style='margin:16px 0 4px'>The forecast for the next "
        f"{n_days} day(s)</h4>"
        + bar_html(forecast, lo, hi, start, hours, nshow, release)
    )

    if moved and gain_act < 0:
        outcome = (
            "This time the advice backfired: the run came out "
            f"<b>{-gain_act:.0f}% dirtier</b> than starting at midnight "
            f"(perfect hindsight would have been {gain_best:.0f}% "
            f"cleaner). For a {kwh:g} kWh job that is about "
            f"<b>{-grams:,.0f} grams of CO2</b> extra."
        )
    elif moved:
        outcome = (
            f"Following the advice cut the CO2 of this run by "
            f"<b>{gain_act:.0f}%</b> compared with starting at midnight "
            f"(the best possible choice, with perfect hindsight, was "
            f"{gain_best:.0f}%). For a {kwh:g} kWh job that is about "
            f"<b>{grams:,.0f} grams of CO2</b> avoided."
        )
    else:
        outcome = (
            "The advice was to start right away, so there is no saving "
            "to report. With perfect hindsight the best choice in this "
            f"window would have been {gain_best:.0f}% cleaner than "
            "midnight."
        )
    looked_back = (
        "<h4 style='margin:16px 0 4px'>What actually happened</h4>"
        f"<div style='font-size:15px'>{outcome}</div>"
        + bar_html(actual, lo, hi, start, hours, nshow, release)
    )
    return card + strip, looked_back


def scorecard(region, wait):
    g = REGIONS[region]
    slip = WAIT[wait]
    r = SUM[(SUM.grid == g) & (SUM.slip_h == slip)].iloc[0]
    if abs(r.model_minus_climatology) < 5:
        note = (
            "*In this region the simple rule is almost as good for "
            "same-day shifting. Forecasting matters more the longer "
            "you can wait.*"
        )
    else:
        note = "*Here the forecast clearly beats the simple rule.*"
    return (
        f"**How good is this in {region}?** We tested on every day of "
        f"2026 (days the model never saw), for a 4-hour job that can "
        f"wait {slip} hours.\n\n"
        f"- Starting at midnight: **{r.immediate:.0f}** g CO2 per kWh\n"
        f"- Our advice: **{r.model:.0f}** g "
        f"(about **{r.model_pct_saved:.0f}% cleaner**)\n"
        f"- A simple rule (\"run at the cleanest hour of an average "
        f"week\"): {r.climatology:.0f} g "
        f"({r.climatology_pct_saved:.0f}% cleaner)\n"
        f"- Perfect hindsight: {r.oracle:.0f} g "
        f"({r.oracle_pct_saved:.0f}% cleaner)\n\n" + note
    )


INTRO = (
    "# 🌍 Clean-Hour\n"
    "### When is electricity cleanest? Run big appliances then.\n"
    "Built for Northern Virginia (home of Loudoun's data centers), "
    "and also tested in California, Texas, Germany and Britain. "
    "Power plants burn more coal and gas at some hours than others. "
    "Pick your region and appliance and we'll tell you the cleanest "
    "time to start it. (This tab replays real days from 2026.)"
)
LIMITS = (
    "- We use the **average** carbon intensity of your region's whole "
    "power grid, not your own electricity company and not the effect "
    "of one extra appliance (marginal emissions).\n"
    "- This tab is a replay of past days. The Live tab uses today's "
    "forecasts for Great Britain and Germany.\n"
    "- Savings are measured against starting at midnight. If you "
    "already run things at midday in a sunny region, you win already.\n"
    "- The accuracy numbers are for a 4-hour job. Other run times use "
    "the same method but were not scored separately.\n"
    "- Prototype for education, not an energy-bill or environmental "
    "guarantee."
)

with gr.Blocks(title="Clean-Hour", theme=gr.themes.Soft(primary_hue="green")) as demo:
    gr.Markdown(INTRO)
    with gr.Column(scale=1):
        region = gr.Dropdown(
            list(REGIONS),
            value="Virginia / Mid-Atlantic, USA",
            label="1. Where do you live?",
        )
        appliance = gr.Dropdown(
            list(APPLIANCES),
            value="Charge my electric car",
            label="2. What do you want to run?",
        )
        with gr.Row():
            hours_box = gr.Number(
                value=None,
                precision=0,
                minimum=1,
                maximum=12,
                label="Or type your own run time (hours, 1 to 12)",
            )
            kwh_box = gr.Number(
                value=None,
                minimum=0,
                label="Energy it uses (kWh, optional)",
            )
        wait = gr.Radio(
            list(WAIT),
            value="Until tomorrow (24 hours)",
            label="3. How long can it wait?",
        )
        with gr.Row():
            day = gr.Dropdown(
                DAY_LABELS,
                value=DAY_LABELS[120],
                label="4. Pick a day to try (real days from 2026)",
            )
            surprise = gr.Button("🎲 Surprise me", scale=0)
    go = gr.Button("Find the cleanest time", variant="primary", size="lg")
    answer = gr.HTML()
    with gr.Accordion("What actually happened? (hindsight check)", open=False):
        hindsight = gr.HTML()
    with gr.Accordion("How accurate is this? (honest numbers)", open=False):
        score = gr.Markdown()
    with gr.Accordion("What this does NOT tell you", open=False):
        gr.Markdown(LIMITS)

    def update(region, appliance, wait, day, hours, kwh):
        a, h = advise(region, appliance, wait, day, hours, kwh)
        return a, h, scorecard(region, wait)

    inputs = [region, appliance, wait, day, hours_box, kwh_box]
    outputs = [answer, hindsight, score]
    go.click(update, inputs, outputs)
    for box in (region, appliance, wait, day, hours_box, kwh_box):
        box.change(update, inputs, outputs)

    def random_day():
        return DAY_LABELS[int(np.random.randint(0, len(DAY_LABELS)))]

    surprise.click(random_day, None, day)
    demo.load(update, inputs, outputs)

# ---- Live tab: Great Britain and Germany -------------------------------
# If the live code fails to load we still keep the replay tab working.
try:
    spec = importlib.util.spec_from_file_location(
        "clean_hour_live", os.path.join(HERE, "live.py")
    )
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
except Exception:
    live = None

if live is not None:
    live.TYPICAL["Great Britain"] = float(DF[DF.grid == "gb"].y.median())
    with gr.Blocks(title="Clean-Hour live") as live_demo:
        gr.Markdown(
            "### Live: the next 48 hours in Great Britain or Germany\n"
            "Great Britain uses the official National Energy System "
            "Operator carbon forecast (it beat our own model there in "
            "the 2026 tests). Germany uses the Fraunhofer ISE "
            "renewable-share forecast (more wind and sun = cleaner). "
            "Needs internet."
        )
        with gr.Column():
            l_app = gr.Dropdown(
                list(live.APPLIANCES),
                value="Charge my electric car",
                label="What do you want to run?",
            )
            with gr.Row():
                l_hours = gr.Number(
                    value=None,
                    precision=0,
                    minimum=1,
                    maximum=12,
                    label="Or type your own run time (hours, 1 to 12)",
                )
                l_kwh = gr.Number(
                    value=None,
                    minimum=0,
                    label="Energy it uses (kWh, optional)",
                )
            l_wait = gr.Radio(
                list(live.WAIT),
                value="Up to 24 hours",
                label="How long can it wait?",
            )
            l_region = gr.Radio(
                live.REGIONS, value="Great Britain", label="Where?"
            )
            l_go = gr.Button("Find the cleanest time now", variant="primary")
            l_out = gr.HTML()
        l_go.click(
            live.advise_live,
            [l_app, l_wait, l_region, l_hours, l_kwh],
            l_out,
        )
    app = gr.TabbedInterface(
        [demo, live_demo],
        [
            "Replay: Virginia and 4 more regions (tested on 2026)",
            "Live: Great Britain and Germany",
        ],
        title=None,
        theme=gr.themes.Soft(primary_hue="green"),
    )
else:
    app = demo

if __name__ == "__main__":
    app.launch()
