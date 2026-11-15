"""Gradio demo: pick a 2026 test day and how long the job may slip -> cleanest 4h window.
Everything shown is from the held-out 2026 test set (the model never saw these days).
Run from the repo root:  python app/app.py
"""
import os

import gradio as gr
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DF = pd.read_csv(os.path.join(HERE, "..", "results", "test_predictions.csv.gz"), parse_dates=["day"])
DAYS = sorted(DF.day.dt.strftime("%Y-%m-%d").unique())
JOB = 4


def costs(profile):
    return np.convolve(profile, np.ones(JOB) / JOB, mode="valid")


def run(day, slip, min_saving):
    g = DF[DF.day == pd.Timestamp(day)].sort_values("j")
    slip = int(slip)
    y, p, c, pe = g.y.values, g.pred.values, g.clim.values, g.persist.values
    cp, cy = costs(p)[:slip + 1], costs(y)
    cc, cpe = costs(c)[:slip + 1], costs(pe)[:slip + 1]
    st = int(cp.argmin())
    pred_saving = cp[0] - cp[st]
    unsure = pred_saving < min_saving
    start = 0 if unsure else st
    best = int(cy[:slip + 1].argmin())
    now = cy[0]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    sh = min(len(g), 80)
    ax.plot(g.j[:sh], y[:sh], color="#222", lw=1.6, label="actual")
    ax.plot(g.j[:sh], p[:sh], color="#1f6f5c", lw=1.6, label="model forecast")
    ax.plot(g.j[:sh], c[:sh], color="#d9822b", ls=":", label="climatology")
    ax.axvspan(start, start + JOB, color="#1f6f5c", alpha=.2, label="chosen window")
    ax.axvspan(best, best + JOB, color="#222", alpha=.1, label="best possible")
    ax.set_xlabel("hours after local midnight of the job's release day")
    ax.set_ylabel("gCO2/kWh (PJM average)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=3)
    fig.tight_layout()
    rule = ("UNSURE: forecast saves < %.0f g/kWh, so RUN NOW (hour 0)." % min_saving) if unsure else \
        "Start the job %d h after midnight (%02d:00 local)." % (st, st % 24)
    txt = (f"{rule}\n\nActual intensity of the 4h window (gCO2/kWh):\n"
           f"  run now:            {now:6.1f}\n"
           f"  our choice:         {cy[start]:6.1f}  (saves {100*(now-cy[start])/now:.1f}% vs run now)\n"
           f"  persistence rule:   {cy[int(cpe.argmin())]:6.1f}\n"
           f"  climatology rule:   {cy[int(cc.argmin())]:6.1f}\n"
           f"  perfect foresight:  {cy[best]:6.1f}\n\n"
           f"Model predicted a saving of {pred_saving:.1f} g/kWh; actual saving {now-cy[st]:.1f}.\n"
           "Signal = PJM-wide AVERAGE emissions, not Loudoun-specific, not marginal.")
    return fig, txt


with gr.Blocks(title="Loudoun carbon-aware scheduler") as demo:
    gr.Markdown("# When should a Loudoun data center run its flexible 4-hour job?\n"
                "Decision made at 18:00 the evening before. Test days from 2026 only (never used in training).")
    with gr.Row():
        day = gr.Dropdown(DAYS, value=DAYS[40], label="Job release day (local midnight)")
        slip = gr.Radio([0, 12, 24, 48, 72], value=24, label="How long may the job be delayed (hours)?")
        ms = gr.Slider(0, 20, value=3, step=1, label="'Unsure' threshold: run now if predicted saving is below (g/kWh)")
    btn = gr.Button("Recommend a start time", variant="primary")
    plot, out = gr.Plot(), gr.Textbox(lines=11, label="Result")
    btn.click(run, [day, slip, ms], [plot, out])
    demo.load(run, [day, slip, ms], [plot, out])
    gr.Markdown("Honest note: at 12-24 h of slack the model is statistically tied with the simple 'repeat yesterday' rule; "
                "it clearly beats hour-of-week averages, and beats persistence at 48-72 h. "
                "The 'unsure' threshold gave no measurable gain on 2026 test data.")

if __name__ == "__main__":
    demo.launch()
