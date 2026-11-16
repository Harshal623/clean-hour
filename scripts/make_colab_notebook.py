"""Build notebooks/clean_hour_colab.ipynb.

Every project file is pasted into the notebook with %%writefile, so
all of the code is visible in Colab and is exactly what runs.
Run again after changing any source file:
    python scripts/make_colab_notebook.py
Then execute it so the outputs are real:
    python -m nbconvert --to notebook --execute --inplace notebooks/clean_hour_colab.ipynb
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
AI + Climate track. [GitHub repo](https://github.com/Harshal623/clean-hour)

**The idea.** Power plants burn more coal and gas at some hours than
others, so the same EV charge or dishwasher run can emit very different
CO2 depending on when it starts. We forecast the carbon intensity of a
regional power grid (grams of CO2 per kWh) and recommend the cleanest
window for a flexible job.

**Our user.** A Northern Virginia family at 6 PM, deciding when to
charge the car, on the PJM grid. A Loudoun data-center lead with batch
work to schedule is the same forecast.

**The test.** We train on 2023 to 2025 and test on every day of 2026.
The model never sees 2026 while training, and at 6 PM it only uses what
was known then. Nothing is shuffled. We compare against simple rules and
against perfect hindsight.

**What is in this notebook.** The pipeline that produces our headline
numbers, in the order it runs: four source files, then the training run,
then the app. Our extra experiments live in `src/experiments/` with
write-ups in `docs/experiments/`: a PyTorch Transformer on a Colab GPU,
a decision-trained second stage, a 6 PM plug-in baseline, an estimated
marginal-emissions check and a year-robustness test.

**Honest limits.** The signal is the average emissions of a whole
regional grid, not the marginal plant and not one town. Savings are
measured against starting at midnight (the 6 PM comparison is in
`results/experiments/plug_in_baseline.csv`). This is a backtest on past
days, not a live forecast; the Live tab uses the official forecasters.

**How to use it.** Click Runtime, then Run all. Training takes about a
minute on a laptop and a few minutes on Colab's free CPU. To skip it, set
`RETRAIN = False` in section 3 and the saved results are used instead.""")

md(
    "## 1. Setup\nGet the repo (it holds the small data files) and install what the "
    "app needs. Gradio is pinned because the app was built and tested against 4.44."
)
code("""import os
import subprocess
import sys

in_colab = "google.colab" in sys.modules

if not os.path.exists("data/compact"):
    if os.path.basename(os.getcwd()) == "notebooks":
        os.chdir("..")
    else:
        repo = "https://github.com/Harshal623/clean-hour.git"
        clone = subprocess.run(["git", "clone", "-q", repo], capture_output=True, text=True)
        if clone.returncode or not os.path.isdir("clean-hour"):
            raise SystemExit("Could not clone the repo:\\n" + clone.stderr[-1500:])
        os.chdir("clean-hour")

install = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q",
     "numpy", "pandas", "scikit-learn", "matplotlib",
     "gradio==4.44.1", "huggingface_hub<1.0"],
    capture_output=True, text=True,
)
if install.returncode:
    raise SystemExit("pip install failed:\\n" + install.stderr[-2000:])

os.makedirs("src", exist_ok=True)
os.makedirs("app", exist_ok=True)
print("Setup complete:", "Google Colab" if in_colab else "local run")""")

md("""## 2. The code
Each cell below writes one file and shows it. Read them top to
bottom. Data comes from public sources (EIA, NESO, Energy-Charts,
Open-Meteo). A small copy of the hourly data is bundled in
`data/compact/`, so you do not need to download hundreds of MB; it is
rebuilt from the raw caches with `scripts/make_compact_data.py`.""")
for path, what in FILES[:4]:
    md(f"### `{path}`: {what}")
    source_cell(path)

md("""## 3. Train and test
This runs `src/multigrid.py`. For each grid it trains on 2023 to 2025,
predicts every 2026 day, picks the cleanest window, and scores it
against the baselines. It prints tables with 95% confidence intervals
and saves the results used by the app.

If training fails we stop here on purpose: the later cells read
`results/`, so continuing would show the repo's saved numbers as if they
had just been recomputed.""")
code("""RETRAIN = True   # False = skip training and use the saved results

if RETRAIN:
    run = subprocess.run(
        [sys.executable, "-W", "ignore", "src/multigrid.py"],
        capture_output=True,
        text=True,
    )
    lines = run.stdout.strip().splitlines()
    print("\\n".join(lines[:12]))        # per-grid headlines: days kept, error, table
    print("   ...")
    print("\\n".join(lines[-60:]))       # the comparison tables and intervals
    if run.returncode != 0:
        print(run.stderr[-3000:])
        raise SystemExit("Training failed; see the traceback above. Not continuing, "
                         "because the cells below would show saved results, not this run.")
else:
    print("Skipped. Using the saved results in results/.")""")

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
- Virginia's grid is flat, so its savings are the smallest. Perfect
  hindsight would only add 1.3% at 24 hours, which is why we do not
  claim a large saving there.
- A negative "model minus climatology" means the model chose cleaner
  windows than the simple rule.

**Rerunning this notebook.** It is deterministic: the same code and the
same bundled data gave the same numbers in two runs. The last digit can
still move by up to about 2 g/kWh between machines, because the
gradient-boosting split depends on the scikit-learn version. The numbers
in `results/` and the README come from one such run.""")

md("""## 5. One example
A single input and what comes out, using the saved 2026 forecasts. We
show one day where the advice helped and one where it backfired, because
the tool is not always right: against a 6 PM plug-in it was worse on
4.5% of days.""")
code("""P = pd.read_csv("results/test_predictions_all.csv.gz")
P["day"] = pd.to_datetime(P["day"])


def recommend(grid, day, hours=4, wait=24, kwh=10.0, label=""):
    d = P[(P.grid == grid) & (P.day == pd.Timestamp(day))].sort_values("j")
    forecast, actual = d.pred.values, d.y.values

    def window_mean(a):
        return np.convolve(a, np.ones(hours) / hours, mode="valid")

    start = int(np.argmin(window_mean(forecast)[: wait + 1]))
    now_cost = window_mean(actual)[0]
    chosen = window_mean(actual)[start]
    saved = (now_cost - chosen) * kwh
    print(f"{label}{grid} {day}: {hours}-hour job, can wait {wait} hours")
    print(f"  advice: start {start} h after midnight")
    print(f"  midnight start {now_cost:.0f} g/kWh, our window {chosen:.0f} g/kWh")
    verdict = "less CO2 than midnight" if saved > 0 else "more CO2 than midnight"
    print(f"  CO2 avoided: {saved:+,.0f} g for {kwh:g} kWh ({verdict})")
    print()


recommend("pjm", "2026-02-04", hours=4, wait=24, kwh=10, label="HELPED: ")
recommend("pjm", "2026-01-09", hours=4, wait=24, kwh=10, label="BACKFIRED: ")""")

md("""## 6. The app
Two more files. The app has a Replay tab (days from 2026) and a Live
tab for Great Britain and Germany. You can pick an appliance or type
your own run time in hours.""")
for path, what in FILES[4:]:
    md(f"### `{path}`: {what}")
    source_cell(path)

code("""import importlib.util
import warnings

warnings.filterwarnings("ignore")   # gradio pulls a tqdm/ipywidgets warning we do not need
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
