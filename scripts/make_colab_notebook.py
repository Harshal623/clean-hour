"""Build notebooks/clean_hour_colab.ipynb.

Every project file is pasted into the notebook with %%writefile, so
all of the code is visible in Colab and is exactly what runs.
Run again after changing any source file:
    python scripts/make_colab_notebook.py
"""

import nbformat as nbf

FILES = [
    ("src/load_data.py", "Virginia data and emission factors"),
    ("src/grids.py", "All five grids, plus weather"),
    ("src/sweep.py", "Shared helpers: features, window picking, bootstrap"),
    ("src/multigrid.py", "Train the model and run the tests"),
    ("app/live.py", "Live tab: Great Britain and Germany"),
    ("app/app.py", "The app people use"),
]

cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


def source_cell(path):
    text = open(path, encoding="utf-8").read().rstrip("\n")
    code(f"%%writefile {path}\n{text}")


md("""# Clean-Hour: when is electricity cleanest?
AI + Climate track. All of our code is in this notebook, in the order
it runs. [GitHub repo](https://github.com/Harshal623/clean-hour)

**The idea.** Power plants burn more coal and gas at some hours than
others. If a household (or a data center) can delay a job like
charging a car, the best start time can cut its CO2. We forecast the
carbon intensity of a regional power grid (grams of CO2 per kWh) and
pick the cleanest window.

**The test.** We train on 2023 to 2025 and test on every day of 2026.
The model never sees 2026 while training. At 6 PM the evening before,
it only uses what was known then. Nothing is shuffled. We compare
against simple rules and against perfect hindsight.

**Honest limits.** The signal is the average emissions of a whole
regional grid, not the marginal plant and not one town. Savings are
measured against starting at midnight. The results are a backtest on
past days, not a live forecast (the Live tab does use real forecasts,
but from the official forecasters).

**How to use it.** Click Runtime, then Run all. Training takes about
10 minutes on Colab's free CPU. To skip it, set `RETRAIN = False`
in section 3 and the saved results are used instead.""")

md(
    "## 1. Setup\nGet the repo (it holds the small data files) and install Gradio."
)
code("""import os
import subprocess
import sys

if not os.path.exists("data/compact"):
    if os.path.basename(os.getcwd()) == "notebooks":
        os.chdir("..")
    else:
        repo = "https://github.com/Harshal623/clean-hour.git"
        subprocess.run(["git", "clone", "-q", repo], check=False)
        os.chdir("clean-hour")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gradio"])
os.makedirs("src", exist_ok=True)
os.makedirs("app", exist_ok=True)
print("working in", os.getcwd())""")

md("""## 2. The code
Each cell below writes one file and shows it. Read them top to
bottom. Data comes from public sources (EIA, NESO, Energy-Charts,
Open-Meteo). A small copy of the hourly data is bundled in
`data/compact/`, so you do not need to download hundreds of MB.""")
for path, what in FILES[:4]:
    md(f"### `{path}`: {what}")
    source_cell(path)

md("""## 3. Train and test
This runs `src/multigrid.py`. For each grid it trains on 2023 to 2025,
predicts every 2026 day, picks the cleanest window, and scores it
against the baselines. It prints tables with 95% confidence intervals
and saves the results used by the app.""")
code("""RETRAIN = True   # False = skip training and use the saved results

if RETRAIN:
    run = subprocess.run(
        [sys.executable, "-W", "ignore", "src/multigrid.py"],
        capture_output=True,
        text=True,
    )
    print(run.stdout[-6000:])
    if run.returncode:
        print("ERROR:", run.stderr[-2000:])
else:
    print("Skipped. Using results/ from the repo.")""")

md("""## 4. Results
Percent cleaner than starting at midnight for a 4-hour job, when the
job can wait 24 hours and 3 days. "Simple rule" runs at the cleanest
hour of an average week. "Perfect hindsight" knows the future.""")
code("""import matplotlib.pyplot as plt
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
plt.show()""")
code("""# the same numbers as a table, with the 95% intervals
cols = [
    "grid", "slip_h", "immediate", "persistence", "climatology",
    "model", "oracle", "model_pct_saved",
    "model_minus_climatology", "model_minus_climatology_lo",
    "model_minus_climatology_hi",
]
S[S.slip_h.isin([24, 72])][cols].round(1)""")
md("""**Reading it honestly.**
- Shifting helps everywhere, most in solar-rich grids.
- In California, Texas and Germany a simple "run at midday" rule is
  almost as good for same-day shifting. With 3 days of slack the model
  beats the rule in all five grids.
- Britain's official NESO forecast beats ours, so the live tab uses
  theirs.
- Virginia's grid is flat, so its savings are the smallest.
- A negative "model minus climatology" means the model chose cleaner
  windows than the simple rule.""")

md("""## 5. One example
A single input and what comes out, using the saved 2026 forecasts.""")
code("""P = pd.read_csv("results/test_predictions_all.csv.gz")
P["day"] = pd.to_datetime(P["day"])


def recommend(grid, day, hours=4, wait=24, kwh=10.0):
    d = P[(P.grid == grid) & (P.day == pd.Timestamp(day))]
    d = d.sort_values("j")
    forecast, actual = d.pred.values, d.y.values
    avg = lambda a: np.convolve(a, np.ones(hours) / hours, mode="valid")
    start = int(np.argmin(avg(forecast)[: wait + 1]))
    now_cost = avg(actual)[0]
    best_cost = avg(actual)[start]
    saved = (now_cost - best_cost) * kwh
    print(grid, day, f"{hours}-hour job, can wait {wait} hours")
    print(f"  start {start} hours after midnight")
    print(f"  midnight start: {now_cost:.0f} g/kWh, ours: {best_cost:.0f}")
    print(f"  about {saved:,.0f} g of CO2 avoided for {kwh:g} kWh")


day = str(P[P.grid == "pjm"].day.iloc[1000].date())
recommend("pjm", day, hours=4, wait=24, kwh=10)
recommend("gb", day, hours=2, wait=12, kwh=1.2)""")

md("""## 6. The app
Two more files. The app has a Replay tab (days from 2026) and a Live
tab for Great Britain and Germany. You can pick an appliance or type
your own run time in hours.""")
for path, what in FILES[4:]:
    md(f"### `{path}`: {what}")
    source_cell(path)

code("""import importlib.util

spec = importlib.util.spec_from_file_location("clean_hour_app", "app/app.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if "google.colab" in sys.modules:
    mod.app.launch(share=True, debug=False)
else:
    print("Loaded. To run it on your computer:")
    print("    python app/app.py   then open http://127.0.0.1:7860")""")

md("""## 7. Sources and credits
- EIA grid data: https://www.eia.gov/electricity/gridmonitor/
- Energy-Charts (Fraunhofer ISE): https://api.energy-charts.info/
- NESO Carbon Intensity API: https://carbonintensity.org.uk/
- Open-Meteo: https://open-meteo.com/en/docs/historical-forecast-api
- Emission factors: IPCC AR5 WG3 Annex III
  (https://www.ipcc.ch/report/ar5/wg3/). Oil and "other fuels" values
  are our own assumptions.
- Tools: pandas, scikit-learn, matplotlib, Gradio.
- Related work is listed in `README.md` and `CREDITS.md`.
- AI tool: we used Claude Code (Anthropic) to help write and test this
  code. The full list of tools is in `CREDITS.md`, and the team
  reviewed the results and can explain every part.""")

nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata["colab"] = {"name": "clean_hour_colab.ipynb"}
nbf.write(nb, "notebooks/clean_hour_colab.ipynb")
print("wrote notebook with", len(cells), "cells")
