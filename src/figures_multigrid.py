"""Headline figure: % cleaner than starting at midnight, per region. Run: python -I -W ignore src/figures_multigrid.py"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
S = pd.read_csv("results/multigrid_summary.csv")
order = ["ciso", "de", "erco", "gb", "pjm"]
names = {"ciso": "California", "de": "Germany", "erco": "Texas", "gb": "Great Britain", "pjm": "Virginia"}
fig, axs = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
for ax, sl in zip(axs, [24, 72]):
    d = S[S.slip_h == sl].set_index("grid").loc[order]
    x = np.arange(len(order)); w = 0.27
    for i, (c, lab, col) in enumerate([("climatology_pct_saved", "simple average-week rule", "#d9822b"),
                                       ("model_pct_saved", "our forecast", "#1f6f5c"),
                                       ("oracle_pct_saved", "perfect hindsight", "#444")]):
        ax.bar(x + (i - 1) * w, d[c], w, label=lab, color=col)
    ax.set_xticks(x); ax.set_xticklabels([names[g] for g in order])
    ax.set_title(f"Job can wait {sl} hours" if sl < 72 else "Job can wait 3 days")
    ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("% cleaner than starting at midnight"); axs[0].legend(frameon=False, fontsize=8)
fig.suptitle("Test 2026: shifting helps everywhere; the forecast matters most with more time to wait", y=1.0)
fig.tight_layout(); fig.savefig("results/multigrid_savings.png", dpi=130)
