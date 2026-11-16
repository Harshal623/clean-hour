"""Clean-Hour: a simple app that tells you the cleanest time to run a big appliance.

Replays real days from 2026 (the model never saw them). Run from the repo root:
    python app/app.py
"""
import os

import gradio as gr
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
DF = pd.read_csv(os.path.join(RES, "test_predictions_all.csv.gz"), parse_dates=["day"])
SUM = pd.read_csv(os.path.join(RES, "multigrid_summary.csv"))

REGIONS = {
    "California, USA": "ciso", "Texas, USA": "erco", "Virginia / Mid-Atlantic, USA": "pjm",
    "Germany": "de", "Great Britain": "gb",
}
APPLIANCES = {  # label: (hours it runs, kWh per run)
    "Charge my electric car": (4, 10.0),
    "Run the dishwasher": (2, 1.2),
    "Do laundry (wash + dry)": (3, 3.0),
    "Heat water (boiler / heat pump)": (3, 3.0),
}
WAIT = {"Just tonight (up to 12 hours)": 12, "Until tomorrow (24 hours)": 24, "I'm flexible: up to 3 days": 72}
_common = set.intersection(*[set(DF[DF.grid == g].day) for g in REGIONS.values()])
DAYS = sorted(_common)
DAY_LABELS = [d.strftime("%a %d %b %Y") for d in DAYS]


def clock(h):
    h = int(h) % 24
    return f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"


def when(j, release):
    d = release + pd.Timedelta(hours=int(j))
    return f"{d.strftime('%A, %b')} {d.day} at {clock(d.hour)}"


def when_end(j, release):
    """End time: just the clock if it is the same date as the start, else the full date."""
    return when(j, release)


def day_name(d):
    return f"{d.strftime('%a %b')} {d.day}"


def colour(v, lo, hi):
    t = 0 if hi <= lo else min(max((v - lo) / (hi - lo), 0), 1)
    r, g = int(60 + 190 * t), int(190 - 110 * t)  # green -> red
    return f"rgb({r},{g},80)"


def bar_html(prof, lo, hi, start, L, nshow, release=None):
    rows = []
    n_days = int(np.ceil(nshow / 24))
    for d in range(n_days):
        cells = []
        for h in range(24):
            j = d * 24 + h
            if j >= len(prof) or j >= nshow:
                cells.append("<div style='flex:1;height:22px'></div>")
                continue
            chosen = start <= j < start + L
            border = "3px solid #111" if chosen else "1px solid white"
            cells.append(f"<div title='{clock(h)}: {prof[j]:.0f} g CO2 per kWh' style='flex:1;height:22px;"
                         f"background:{colour(prof[j], lo, hi)};border:{border};box-sizing:border-box'></div>")
        label = f"Day {d + 1}" + (f": {day_name(release + pd.Timedelta(days=d))}" if release is not None else "")
        rows.append(f"<div style='margin:3px 0'><div style='font-size:12px;color:#555'>{label}</div>"
                    f"<div style='display:flex'>{''.join(cells)}</div></div>")
    scale = ("<div style='display:flex;justify-content:space-between;font-size:12px;color:#555;margin-top:2px'>"
             "<span>12 AM</span><span>6 AM</span><span>12 PM</span><span>6 PM</span><span>11 PM</span></div>")
    legend = ("<div style='font-size:13px;margin-top:8px'><span style='color:#2a9d4a'>■</span> cleaner power &nbsp;"
              "<span style='color:#d9534f'>■</span> dirtier power &nbsp; <b>Black outline</b> = the time we suggest</div>")
    return "".join(rows) + scale + legend


def advise(region, appliance, wait, day_label):
    g = REGIONS[region]
    L, kwh = APPLIANCES[appliance]
    slip = WAIT[wait]
    day = DAYS[DAY_LABELS.index(day_label)]
    d = DF[(DF.grid == g) & (DF.day == day)].sort_values("j")
    y, p = d.y.values, d.pred.values
    nshow = slip + L

    def win(a):  # mean intensity of every L-hour window
        return np.convolve(a, np.ones(L) / L, mode="valid")

    cp, cy = win(p)[:slip + 1], win(y)
    start = int(cp.argmin())
    now_pred, now_act = cp[0], cy[0]
    gain_pred = 100 * (now_pred - cp[start]) / now_pred
    best = int(cy[:slip + 1].argmin())
    gain_act = 100 * (now_act - cy[start]) / now_act
    gain_best = 100 * (now_act - cy[best]) / now_act
    grams = (now_act - cy[start]) * kwh
    release = pd.Timestamp(day)
    typical = float(DF[DF.grid == g].clim.median())  # the region's usual intensity, g/kWh
    frame_end = release + pd.Timedelta(hours=slip)
    frame = f"{when(0, release)} to {when(slip, release)}"
    moved = gain_pred >= 3
    good_bg, good_bd, good_tx = "#eaf6ee", "#bfe3c9", "#14532d"
    bad_bg, bad_bd, bad_tx = "#fdecea", "#f1b7b1", "#8a1c13"
    bg, bd, tx = good_bg, good_bd, good_tx
    if moved:
        end = start + L
        head = f"Start {when(start, release)}"
        sub = (f"It will run until about {when_end(end, release)}. "
               f"We expect that to be about <b>{gain_pred:.0f}% cleaner</b> than starting at midnight.")
        if cp[start] > typical:
            sub += (" Heads-up: even this is dirtier than usual for your region, so if you can wait longer, "
                    "choose the 3-day option.")
    else:
        start = 0
        if now_pred <= typical:
            head = "Green: start whenever you like within your time frame"
            sub = "Power is cleaner than usual all through your time frame, and no hour is much better than another."
        else:
            bg, bd, tx = bad_bg, bad_bd, bad_tx
            head = "Red: if you can, wait longer"
            sub = (f"Power is dirtier than usual across your whole time frame ({frame}) and no hour is much cleaner. "
                   "Pick a longer wait (up to 3 days) to give the tool a cleaner window, or start now if it cannot wait.")
    lo, hi = np.percentile(p[:nshow], 5), np.percentile(p[:nshow], 95)
    sub_html = sub.replace('<b>', "<b style='color:" + tx + "'>")
    card = (f"<div style='padding:18px;border-radius:12px;background:{bg};border:1px solid {bd}'>"
            f"<div style='font-size:28px;font-weight:700;color:{tx}'>{head}</div>"
            f"<div style='font-size:16px;margin-top:6px;color:#1f2937'>{sub_html}</div>"
            f"<div style='font-size:13px;margin-top:6px;color:#374151'>Your time frame: {frame}.</div></div>")
    forecast = (f"<h4 style='margin:16px 0 4px'>The forecast for the next {int(np.ceil(nshow / 24))} day(s)</h4>"
                + bar_html(p, lo, hi, start, L, nshow, release))
    if moved:
        outcome = (f"Following the advice cut the CO2 of this run by <b>{gain_act:.0f}%</b> compared with starting "
                   f"at midnight (the best possible choice, with perfect hindsight, was {gain_best:.0f}%). "
                   f"For a {kwh:g} kWh job that is about <b>{grams:,.0f} grams of CO2</b> avoided.")
    else:
        outcome = (f"The advice was to start right away, so there is no saving to report; with perfect hindsight "
                   f"the best choice in this window would have been {gain_best:.0f}% cleaner than midnight.")
    looked_back = (f"<h4 style='margin:16px 0 4px'>What actually happened</h4>"
                   f"<div style='font-size:15px'>{outcome}</div>" + bar_html(y, lo, hi, start, L, nshow, release))
    return card + forecast, looked_back


def scorecard(region, wait):
    g = REGIONS[region]
    slip = WAIT[wait]
    r = SUM[(SUM.grid == g) & (SUM.slip_h == slip)].iloc[0]
    return (f"**How good is this in {region}?** We tested on every day of 2026 (days the model never saw), "
            f"for a 4-hour job that can wait {slip} hours.\n\n"
            f"- Starting at midnight: **{r.immediate:.0f}** g CO2 per kWh\n"
            f"- Our advice: **{r.model:.0f}** g (about **{r.model_pct_saved:.0f}% cleaner**)\n"
            f"- A simple rule (\"run at the cleanest hour of an average week\"): {r.climatology:.0f} g "
            f"({r.climatology_pct_saved:.0f}% cleaner)\n"
            f"- Perfect hindsight: {r.oracle:.0f} g ({r.oracle_pct_saved:.0f}% cleaner)\n\n"
            + ("*In this region, the simple rule is almost as good for same-day shifting. "
               "Forecasting matters more the longer you can wait.*" if abs(r.model_minus_climatology) < 5
               else "*Here the forecast clearly beats the simple rule.*"))


with gr.Blocks(title="Clean-Hour") as demo:
    gr.Markdown("# 🌍 Clean-Hour\n### When is electricity cleanest? Run big appliances then.\n"
                "Built for Northern Virginia (home of Loudoun's data centers); also tested in California, Texas, Germany and Britain. "
                "Power plants burn more coal and gas at some hours than others. Pick your region and "
                "appliance and we'll tell you the cleanest time to start it. "
                "(Demo: replays real days from 2026.)")
    with gr.Column(scale=1):
        region = gr.Dropdown(list(REGIONS), value="Virginia / Mid-Atlantic, USA", label="1. Where do you live?")
        appliance = gr.Dropdown(list(APPLIANCES), value="Charge my electric car", label="2. What do you want to run?")
        wait = gr.Radio(list(WAIT), value="Until tomorrow (24 hours)", label="3. How long can it wait?")
        with gr.Row():
            day = gr.Dropdown(DAY_LABELS, value=DAY_LABELS[120], label="4. Pick a day to try (real days from 2026)")
            surprise = gr.Button("🎲 Surprise me", scale=0)
    go = gr.Button("Find the cleanest time", variant="primary", size="lg")
    answer = gr.HTML()
    with gr.Accordion("What actually happened that day? (hindsight check)", open=False):
        hindsight = gr.HTML()
    with gr.Accordion("How accurate is this? (honest numbers)", open=False):
        score = gr.Markdown()
    with gr.Accordion("What this does NOT tell you", open=False):
        gr.Markdown("- We use the **average** carbon intensity of your region's whole power grid, "
                    "not your own electricity company and not the effect of one extra appliance (marginal emissions).\n"
                    "- Past-day replay only. A live version needs live grid data.\n"
                    "- Savings are measured against starting at midnight; if you normally run things at midday "
                    "in a sunny region, you already win.\n"
                    "- Prototype for education, not an energy-bill or environmental guarantee.")

    def update(region, appliance, wait, day_idx):
        a, h = advise(region, appliance, wait, day_idx)
        return a, h, scorecard(region, wait)

    ins = [region, appliance, wait, day]
    outs = [answer, hindsight, score]
    go.click(update, ins, outs)
    for c in (region, appliance, wait):
        c.change(update, ins, outs)
    day.change(update, ins, outs)
    surprise.click(lambda: DAY_LABELS[int(np.random.randint(0, len(DAY_LABELS)))], None, day)
    demo.load(update, ins, outs)

# ---- Live tab (Great Britain, NESO official forecast; falls back gracefully offline) ----
try:
    sys_path_added = False
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("clean_hour_live", os.path.join(HERE, "live.py"))
    _live = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_live)
except Exception:  # live mode must never break the replay app
    _live = None

if _live is not None:
    _live.TYPICAL["Great Britain"] = float(DF[DF.grid == "gb"].y.median())
    with gr.Blocks(title="Clean-Hour live") as live_demo:
        gr.Markdown("### Live: the next 48 hours in Great Britain or Germany\nGreat Britain uses the official National Energy System Operator carbon forecast "
                    "(it beat our own model there in 2026 tests). Germany uses the Fraunhofer ISE renewable-share forecast (more wind and sun = cleaner). Needs internet.")
        with gr.Column():
            l_app = gr.Dropdown(list(_live.APPLIANCES), value="Charge my electric car", label="What do you want to run?")
            l_wait = gr.Radio(list(_live.WAIT), value="Up to 24 hours", label="How long can it wait?")
            l_region = gr.Radio(_live.REGIONS, value="Great Britain", label="Where?")
            l_go = gr.Button("Find the cleanest time now", variant="primary")
            l_out = gr.HTML()
        l_go.click(_live.advise_live, [l_app, l_wait, l_region], l_out)
    app = gr.TabbedInterface([demo, live_demo], ["Replay: Virginia and 4 more regions (tested on 2026)", "Live: Great Britain and Germany"],
                             title=None)
else:
    app = demo

if __name__ == "__main__":
    app.launch(theme=gr.themes.Soft(primary_hue="green"))
