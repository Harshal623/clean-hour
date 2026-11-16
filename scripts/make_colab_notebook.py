"""Build notebooks/clean_hour_colab.ipynb, a notebook that needs nothing else.

STOP: the notebook that ships today is the self-contained version (bundled data,
write-up inline) and was NOT produced by this script. Running this overwrites it
with the older 27-cell version and loses the bundled data, so do not run it during
the submission window. Kept for reference only.

The notebook carries its own data (a small bundle of public data), all
of our code (pasted with %%writefile), and the write-up. Nobody has to
open GitHub to read or run it.
Run again after changing any source file or result:
    python scripts/make_colab_notebook.py
"""
import base64
import io
import lzma
import tarfile

import nbformat as nbf
import pandas as pd

FILES = [
    ("src/load_data.py", "Virginia data and emission factors"),
    ("src/grids.py", "All five grids, plus weather"),
    ("src/sweep.py", "Shared helpers: features, window picking, bootstrap"),
    ("src/multigrid.py", "Train the model and run the tests"),
    ("app/live.py", "Live tab: Great Britain and Germany"),
    ("app/app.py", "The app people use"),
]
GRIDS = ["pjm", "ciso", "erco", "de", "gb"]
NAMES = {
    "pjm": "Virginia / Mid-Atlantic",
    "ciso": "California",
    "erco": "Texas",
    "de": "Germany",
    "gb": "Great Britain",
}

cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text, hidden=False):
    cell = nbf.v4.new_code_cell(text)
    if hidden:
        cell.metadata["cellView"] = "form"
    cells.append(cell)


def source_cell(path):
    text = open(path, encoding="utf-8").read().rstrip("\n")
    code(f"%%writefile {path}\n{text}")


def data_bundle(parts=5):
    """Pack the ten small data files into text we can paste in a cell."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for g in GRIDS:
            for kind in ("grid", "weather"):
                name = f"{kind}_{g}.csv"
                tar.add(f"data/{name}", arcname=name)
    packed = lzma.compress(buf.getvalue(), preset=9 | lzma.PRESET_EXTREME)
    text = base64.b64encode(packed).decode()
    size = -(-len(text) // parts)
    return [text[i : i + size] for i in range(0, len(text), size)]


def results_table():
    """Markdown table from the saved results, so text and code agree."""
    s = pd.read_csv("results/multigrid_summary.csv")
    lines = [
        "| Region | Job can wait | Start at midnight | Our advice "
        "| % cleaner | Simple rule % | Perfect hindsight % |",
        "|---|---|---|---|---|---|---|",
    ]
    for slip, label in [(24, "24 hours"), (72, "3 days")]:
        for g in ["pjm", "ciso", "erco", "de", "gb"]:
            r = s[(s.grid == g) & (s.slip_h == slip)].iloc[0]
            lines.append(
                f"| {NAMES[g]} | {label} | {r.immediate:.0f} g | "
                f"{r.model:.0f} g | {r.model_pct_saved:.1f}% | "
                f"{r.climatology_pct_saved:.1f}% | "
                f"{r.oracle_pct_saved:.1f}% |"
            )
    return "\n".join(lines)


md(
    """# Clean-Hour: when is electricity cleanest?
**Track: Climate** (AI + Climate)

**One-sentence pitch.** Clean-Hour forecasts when Northern Virginia's
power grid is cleanest, so families and Loudoun's data centers can start
flexible jobs at cleaner hours, and it tests honestly where a forecast
beats simple rules and whether the method works on four other grids.

**This notebook is the whole submission.** It holds the write-up, all of
our code, the data it needs, the tests, and the app. You do not need
anything else. Click Runtime, then Run all. It takes about 10 minutes on
Colab's free CPU (most of it is training). Team names, schools and
emails are on the submission form, not here."""
)

md(
    """## The problem
Electricity is not equally clean all day. The power plants running at
7 PM are not the ones running at 2 AM, so the same appliance can cause
very different CO2 depending on when it starts. Northern Virginia hosts
one of the world's biggest clusters of data centers, which run flexible
jobs (AI training, backups, video processing) that could start at almost
any hour. Families have the same choice with an electric car, a
dishwasher or laundry. Nobody tells them when the grid is cleanest.

**Who it is for and when.** A Northern Virginia household in the
evening, deciding when to start something tomorrow, or within three
days. A data-center operations lead could use it the same way.

## What we built
- **In:** the region, how long the job runs (pick an appliance or type
  your own run time), and how long it can wait.
- **Out:** one plain answer such as "Start Friday, May 1 at 12 PM, about
  12% cleaner than starting at midnight". If no hour is much better it
  says green (start whenever) or red (wait longer). It also shows a
  colored strip of the coming hours and a check of what really happened.
- **Under the hood:** a gradient-boosting forecast of the grid's hourly
  carbon intensity (grams of CO2 per kWh), made at 6 PM the evening
  before from the last week of grid data, demand forecasts and weather
  forecasts. We pick the 4-hour window with the lowest forecast.

## What we added
This is our own idea, not one of the suggested projects.
- **Our own place and user:** Northern Virginia homes and the Loudoun
  data-center corridor.
- **Our own data:** five grids on three continents (Virginia, California,
  Texas, Germany, Great Britain) from four public sources, plus a weather
  forecast archive for each.
- **Our own questions:** how long must a job be able to wait before a
  forecast beats simple rules? Does the method hold up on other grids?
  We tried tuning, extra features, a blend and quantile loss, and report
  that none of them beat the model we kept.

## The test (how we avoid cheating)
We train on 2023 to 2025 and test on every day of 2026. The model never
sees 2026 while training. For each test day it only uses what was known
at 6 PM the evening before. Nothing is shuffled, and days with a missing
hour are dropped, never filled in. We compare four things: starting at
midnight, "repeat yesterday" (persistence), the average for that hour of
the week (a simple rule), and perfect hindsight (a ceiling).

**Honest limits.** This is a backtest on past days, not a live forecast.
The signal is the average emissions of a whole regional grid, not the
marginal plant and not one town. Savings are measured against starting
at midnight. Results for 2026 differ from 2025, so read percentages as
one-year measurements."""
)

md("## 1. Setup\nCreate folders, install Gradio, and unpack the data.")
code(
    """import base64
import io
import lzma
import os
import subprocess
import sys
import tarfile

for folder in ("data", "results", "src", "app"):
    os.makedirs(folder, exist_ok=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gradio"])
print("working in", os.getcwd())"""
)

parts = data_bundle()
chunks = ",\n".join(f'    "{p}"' for p in parts)
code(
    "#@title Bundled public data (click Show code to see it)\n"
    "# Hourly carbon intensity and weather for the five grids, from\n"
    "# EIA, Energy-Charts, NESO and Open-Meteo, packed as text.\n"
    f"CHUNKS = [\n{chunks},\n]\n"
    "blob = lzma.decompress(base64.b64decode(''.join(CHUNKS)))\n"
    "tarfile.open(fileobj=io.BytesIO(blob)).extractall('data')\n"
    "print(sorted(os.listdir('data')))",
    hidden=True,
)

md(
    """## 2. The code
Each cell below writes one file and shows it. Read them top to bottom.
The data loaders in `src/grids.py` can also download everything fresh
from the public sources (see the switch in section 3)."""
)
for path, what in FILES[:4]:
    md(f"### `{path}`: {what}")
    source_cell(path)

md(
    """## 3. Train and test
This runs `src/multigrid.py`. For each grid it trains on 2023 to 2025,
predicts every 2026 day, picks the cleanest window, and scores it
against the baselines. It prints tables with 95% confidence intervals
(block bootstrap) and saves what the app needs. About 10 minutes."""
)
code(
    """# Set True to download the raw data again from the public sources.
# That takes a long time (hundreds of MB) and is not needed to check
# our results, because the data is bundled above.
DOWNLOAD_FRESH = False

if DOWNLOAD_FRESH:
    run = subprocess.run(
        [sys.executable, "-W", "ignore", "src/grids.py"],
        capture_output=True,
        text=True,
    )
    print(run.stdout[-2000:], run.stderr[-1000:])"""
)
code(
    """run = subprocess.run(
    [sys.executable, "-W", "ignore", "src/multigrid.py"],
    capture_output=True,
    text=True,
)
print(run.stdout[-6000:])
if run.returncode:
    print("ERROR:", run.stderr[-2000:])"""
)

md(
    """## 4. Results
Percent cleaner than starting at midnight for a 4-hour job, when the job
can wait 24 hours and 3 days. "Simple rule" runs at the cleanest hour of
an average week. "Perfect hindsight" knows the future."""
)
code(
    """import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

S = pd.read_csv("results/multigrid_summary.csv")
names = {
    "ciso": "California",
    "de": "Germany",
    "erco": "Texas",
    "gb": "Great Britain",
    "pjm": "Virginia",
}
order = ["ciso", "de", "erco", "gb", "pjm"]

fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
for ax, slip in zip(axes, [24, 72]):
    d = S[S.slip_h == slip].set_index("grid").loc[order]
    x = np.arange(len(order))
    w = 0.27
    ax.bar(x - w, d.climatology_pct_saved, w, label="simple rule")
    ax.bar(x, d.model_pct_saved, w, label="our forecast")
    ax.bar(x + w, d.oracle_pct_saved, w, label="perfect hindsight")
    ax.set_xticks(x)
    ax.set_xticklabels([names[g] for g in order])
    ax.set_title(f"Job can wait {slip} hours")
axes[0].set_ylabel("% cleaner than starting at midnight")
axes[0].legend(frameon=False)
plt.tight_layout()
plt.show()"""
)
code(
    """# the same numbers as a table, with the 95% intervals
cols = [
    "grid", "slip_h", "immediate", "persistence", "climatology",
    "model", "oracle", "model_pct_saved",
    "model_minus_climatology", "model_minus_climatology_lo",
    "model_minus_climatology_hi",
]
S[S.slip_h.isin([24, 72])][cols].round(1)"""
)
md(
    "**Results from our run (for the write-up).** Grams of CO2 per kWh of "
    "the chosen 4-hour window, and percent cleaner than midnight:\n\n"
    + results_table()
    + """

**What this says, honestly**
- Shifting helps everywhere, most in solar-rich grids, because midnight is
  when power is dirtiest there.
- In California, Texas and Germany a simple "run at midday" rule is almost
  as good as the model for same-day shifting (in Texas and Germany they
  are statistically tied at 24 hours). With 3 days of slack the model beats
  the simple rule in all five grids.
- Britain's official NESO forecast beats ours by about 4 to 6 g/kWh, so
  the live tab uses theirs.
- Virginia's grid is the flattest, so its savings are the smallest.
- A negative "model minus climatology" means the model chose cleaner
  windows than the simple rule."""
)

md(
    """## 5. Where it fails
For every 2026 day we check the model's choice (24 hours of slack)
against the best possible window. "Worse than midnight" counts days when
following the advice was a mistake."""
)
code(
    """P = pd.read_csv("results/test_predictions_all.csv.gz")
P["day"] = pd.to_datetime(P["day"])
HOURS = 4


def avg(a):
    return np.convolve(a, np.ones(HOURS) / HOURS, mode="valid")


rows = []
for grid, g in P.groupby("grid"):
    for day, d in g.groupby("day"):
        d = d.sort_values("j")
        if len(d) < 76:
            continue
        actual = avg(d.y.values)
        pick = int(np.nanargmin(avg(d.pred.fillna(0).values)[:25]))
        best = actual[:25].min()
        rows.append((grid, day, actual[pick] - best, actual[pick] > actual[0]))

F = pd.DataFrame(rows, columns=["grid", "day", "regret", "worse"])
summary = F.groupby("grid").agg(
    days=("day", "count"),
    worse_than_midnight_pct=("worse", lambda x: 100 * x.mean()),
    median_regret=("regret", "median"),
    worst_regret=("regret", "max"),
)
print(summary.round(1))
print()
print("Three worst days per region (g/kWh worse than the best window):")
for grid, g in F.groupby("grid"):
    top = g.sort_values("regret", ascending=False).head(3)
    days = ", ".join(
        f"{d.date()} ({r:.0f})" for d, r in zip(top.day, top.regret)
    )
    print(f"  {names[grid]}: {days}")"""
)
md(
    """Failures cluster in time, mostly January to March, when a shift in
which plants are running after the 6 PM forecast can flip the best hour.
In Great Britain the advice was worse than starting at midnight on
about 15% of days, in Virginia about 8%, in California never."""
)

md("## 6. One input, one output (what a household sees)")
code(
    """def recommend(grid, day, hours=4, wait=24, kwh=10.0):
    d = P[(P.grid == grid) & (P.day == pd.Timestamp(day))]
    d = d.sort_values("j")
    forecast, actual = d.pred.values, d.y.values

    def windows(a):
        return np.convolve(a, np.ones(hours) / hours, mode="valid")

    start = int(np.argmin(windows(forecast)[: wait + 1]))
    now_cost = windows(actual)[0]
    best_cost = windows(actual)[start]
    saved = (now_cost - best_cost) * kwh
    print(grid, day, f"{hours}-hour job, can wait {wait} hours")
    print(f"  start {start} hours after midnight")
    print(f"  midnight start: {now_cost:.0f} g/kWh, ours: {best_cost:.0f}")
    print(f"  about {saved:,.0f} g of CO2 avoided for {kwh:g} kWh")


day = str(P[P.grid == "pjm"].day.iloc[1000].date())
recommend("pjm", day, hours=4, wait=24, kwh=10)
recommend("gb", day, hours=2, wait=12, kwh=1.2)"""
)

md(
    """## 7. The app
Two more files. The app has a Replay tab (days from 2026) and a Live tab
for Great Britain and Germany. Pick an appliance or type your own run
time in hours."""
)
for path, what in FILES[4:]:
    md(f"### `{path}`: {what}")
    source_cell(path)

code(
    """import importlib.util

spec = importlib.util.spec_from_file_location("clean_hour_app", "app/app.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if "google.colab" in sys.modules:
    mod.app.launch(share=True, debug=False)
else:
    print("Loaded. To run it on your computer:")
    print("    python app/app.py   then open http://127.0.0.1:7860")"""
)

md(
    """## 8. What we would do next
1. Run our own model live for Virginia (today only Great Britain and
   Germany use live forecasts, from the official forecasters), and use
   marginal emissions instead of the grid average.
2. Test it with a real family and a data-center operator, and write down
   what confuses them. We have not done a user test yet.

## 9. Sources and credits
**Data (all public)**
- EIA Hourly Electric Grid Monitor: https://www.eia.gov/electricity/gridmonitor/
- Energy-Charts (Fraunhofer ISE): https://api.energy-charts.info/
- NESO Carbon Intensity API: https://carbonintensity.org.uk/
- Open-Meteo historical forecasts: https://open-meteo.com/en/docs/historical-forecast-api

**Method and assumptions**
- Emission factors: IPCC AR5 WG3 Annex III, https://www.ipcc.ch/report/ar5/wg3/
  (coal 820, gas 490, nuclear 12, hydro 24, solar 41, wind 11 gCO2e/kWh).
  Oil (650) and other fuels (230) are our own assumptions. Household
  energy amounts in the app are our assumptions too.
- Libraries: pandas, NumPy, scikit-learn, matplotlib, Gradio.
- No pretrained models. All data is public and contains no personal
  information.

**Related work we read (we do not claim these ideas as new)**
- Wiesner et al., "Let's Wait Awhile", Middleware 2021:
  https://arxiv.org/abs/2110.13234
- Joseph, Savadi, Souza, "LiteCast", arXiv 2511.06187:
  https://arxiv.org/abs/2511.06187
- Radovanovic et al., "Carbon-Aware Computing for Datacenters",
  arXiv 2106.11750: https://arxiv.org/abs/2106.11750
- Sohrabbeig, Ardakanian, Musilek, "Learning to Reduce Data Center Carbon
  Emissions via Forecast-Integrated Workload Scheduling" (University of
  Alberta): https://sites.ualberta.ca/~oardakan/files/PESGM26.pdf
- Chen et al., Applied Energy 397 (2025) 126369:
  https://doi.org/10.1016/j.apenergy.2025.126369

**AI tools.** We used Claude Code (Anthropic) to help write and test this
code and the write-up. The team reviewed the results and can explain
every part of the project.

**Rules.** The work was done during the hackathon window. The AI/ML model
does the main job. We used only public data. The results shown are the
ones we actually got, including the weak ones."""
)

nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata["colab"] = {"name": "clean_hour_colab.ipynb"}
nbf.write(nb, "notebooks/clean_hour_colab.ipynb")
print("wrote notebook with", len(cells), "cells")
