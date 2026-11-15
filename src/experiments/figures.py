"""Two figures for the write-up, from files already in results/ (run reeval.py and
decision_stack.py first). Run from the repo root:  python -I src/experiments/figures.py"""
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

OUT = "results/experiments"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"  # categorical slots 1-3
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "font.size": 10})

# 1) share of the perfect-foresight saving captured, May-Nov 2026 (held-out months)
d = pd.read_csv(f"{OUT}/decision_stack.csv")
fig, ax = plt.subplots(figsize=(7.2, 4))
for name, lab, col, mk in [("persistence", "repeat yesterday", S2, "s"),
                           ("model", "original model", S1, "o"),
                           ("decision stacker", "decision-trained model (new)", S3, "D")]:
    r = d[d.method == name]
    ax.plot(r.slip_h, r["captures_%_of_perfect"], color=col, lw=2, marker=mk, ms=8,
            markeredgecolor=SURF, markeredgewidth=2, label=lab)
    last = r.iloc[-1]
    ax.annotate(f"{last['captures_%_of_perfect']:.0f}%", (last.slip_h, last["captures_%_of_perfect"]),
                xytext=(8, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
ax.set_xticks([12, 24, 48, 72]); ax.set_xticklabels(["12 h", "24 h", "48 h", "72 h"])
ax.set_xlim(8, 80); ax.set_ylim(40, 100)
ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("how long the 4-hour job may wait"); ax.set_ylabel("% of the best possible CO2 saving")
ax.set_title("Held-out months (May-Nov 2026): how close each method gets to perfect foresight",
             fontsize=10, color=INK, loc="left")
ax.legend(frameon=False, fontsize=9, loc="lower left")
fig.tight_layout(); fig.savefig(f"{OUT}/capture_vs_flexibility.png", dpi=140); plt.close(fig)

# 2) when are the clean hours? actual 2026 PJM average intensity by hour of day x month
te = pd.read_csv("results/test_predictions.csv.gz", parse_dates=["day"])
t = te[te.j < 24].assign(month=lambda x: x.day.dt.month, hod=lambda x: x.j)
piv = t.pivot_table(index="hod", columns="month", values="y", aggfunc="mean")
cmap = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
fig, ax = plt.subplots(figsize=(7.2, 4.6))
im = ax.imshow(piv.values, aspect="auto", cmap=cmap, origin="upper")
ax.set_xticks(range(piv.shape[1]))
ax.set_xticklabels([pd.Timestamp(2026, m, 1).strftime("%b") for m in piv.columns])
ax.set_yticks(range(0, 24, 3)); ax.set_yticklabels([f"{h:02d}:00" for h in range(0, 24, 3)])
ax.set_ylabel("local hour"); ax.spines[:].set_visible(False)
for m in range(piv.shape[1]):  # mark the cleanest hour of each month
    h = int(np.nanargmin(piv.values[:, m]))
    ax.plot(m, h, marker="o", ms=7, mfc=SURF, mec=INK, mew=1.2)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
cb.set_label("gCO2/kWh (darker = dirtier)", color=INK2); cb.outline.set_visible(False)
ax.set_title("Virginia/PJM grid, 2026: average carbon intensity by hour (circle = cleanest hour)",
             fontsize=10, color=INK, loc="left")
fig.tight_layout(); fig.savefig(f"{OUT}/clean_hours_heatmap.png", dpi=140); plt.close(fig)
print(piv.round(0).to_string())
