# E11: a decision-focused Transformer in PyTorch (branch exp/torch-transformer)

Owner: S (Sidharth's Claude). Verdict by the kill rule: **TIE** (the decision-trained Transformer wins in Virginia only and
is significantly worse nowhere). Run on a Colab GPU (CUDA, torch 2.14.1) on Nov 15, 2026. The rebuilt 2026 data matched the
saved test set to within 0.05 g/kWh (rounding) in all five grids.

## Why this experiment
- The brief's **Advanced** level is "PyTorch or Hugging Face Transformers, with a free GPU on Colab or Kaggle". Until
  now the project used only scikit-learn.
- It tests our main takeaway inside one model. Sidharth's stacker showed that training for the *choice* of hours helps
  in Virginia, but it is a second model bolted on top. Here the choice is built into the training loss of one network.

## Question
Our production model predicts each hour on its own. Can a neural network that sees all 76 future hours at once, and is
trained to choose the cleanest 4-hour window, pick cleaner hours than gradient boosting on 2026 data it never saw?

## Model (`src/experiments/torch_transformer/run.py`)
- **Input:** the same 18:00 features as the production model (last week of carbon, demand forecast, weather forecasts,
  calendar), one token per future hour (76 tokens). No new data.
- **Network:** 2-layer Transformer encoder (64 wide, 4 attention heads) with learned position embeddings. Self-attention
  lets the forecast for 3 AM use what the model expects at 1 AM and 5 AM. It predicts the change from the recent
  same-hour average, like the production model.
- **Decision loss:** the 4-hour window averages are turned into a "soft choice" of start hour (softmax over starts, temperature 0.1 of the grid's
  carbon spread). Training minimises the cross-entropy between the true and predicted soft choice at 12, 24 and 72 h of
  slack (ListNet style), plus a Huber loss on the hourly values.
- **Variants:** `transformer_mse` (Huber loss only), `transformer_decision` (Huber loss plus decision loss, lambda = 1.0),
  and `blend` (a 50/50 average of the production model and `transformer_decision`, with nothing fitted). Each is a 3-seed ensemble.

## Run
Colab, T4 GPU, Run all: `src/experiments/torch_transformer/colab.ipynb`. Locally:
`python -I src/grids.py` then `python -I -W ignore src/experiments/torch_transformer/run.py` (needs `pip install torch`).

## Data and split (fixed before scoring 2026)
Train 2023-01-01 to 2025-06-30, validate 2025-07-01 to 2025-12-31 to choose the number of epochs (early stopping on
validation decision regret at 24 h), refit on 2023-2025, score once on every complete 2026 day. The production
forecasts are read from `results/test_predictions_all.csv.gz`, not retrained, and the script checks that the rebuilt
2026 data matches the saved test set. Scoring and the 7-day block bootstrap are the same as in `src/multigrid.py`.

## Kill rule (set before running)
WIN in a grid if `transformer_decision` minus the production model has a 95% interval entirely below zero at both 24 h
and 72 h. Overall WIN needs at least 3 of 5 grids. LOSS if it is significantly worse at 24 h in at least 3 grids.
Otherwise TIE. A TIE or LOSS is still reported in one honest sentence.

## Results (2026 held-out test, 311-314 days per grid; full table in `results/experiments/torch_transformer/summary.csv`)
% of the best possible saving captured (higher is better), then Transformer minus production model in g/kWh of the chosen
window, with 95% 7-day block-bootstrap intervals (negative = the Transformer picks cleaner hours).

| Region | Slack | Persistence / GBM / Transformer / Transformer + decision loss | Transformer + decision minus GBM | Transformer minus GBM |
|---|---|---|---|---|
| Virginia | 24 h | 79.4 / 84.3 / 89.0 / 87.9 | -1.04 [-1.93, -0.29] | -1.34 [-2.07, -0.67] |
| Virginia | 72 h | 52.2 / 80.8 / 86.6 / 84.9 | -1.80 [-3.50, -0.41] | -2.56 [-4.09, -1.11] |
| California | 24 h | 97.6 / 98.3 / 98.3 / 98.5 | -0.16 [-0.47, +0.08] | +0.05 [-0.27, +0.33] |
| California | 72 h | 85.6 / 93.1 / 93.2 / 93.5 | -0.65 [-2.57, +1.08] | -0.20 [-1.89, +1.34] |
| Texas | 24 h | 91.9 / 92.7 / 94.6 / 92.5 | +0.18 [-1.33, +1.62] | -2.12 [-4.16, -0.42] |
| Texas | 72 h | 73.4 / 86.7 / 90.6 / 90.0 | -4.43 [-7.92, -1.18] | -5.29 [-7.80, -2.28] |
| Germany | 24 h | 92.6 / 95.3 / 96.5 / 96.5 | -2.15 [-3.86, -0.01] | -2.14 [-3.88, -0.20] |
| Germany | 72 h | 79.2 / 91.2 / 92.0 / 91.6 | -0.81 [-4.07, +3.84] | -1.52 [-5.13, +1.88] |
| Great Britain | 24 h | 63.5 / 82.0 / 85.0 / 82.2 | -0.07 [-1.21, +0.96] | -1.27 [-2.52, -0.37] |
| Great Britain | 72 h | 44.3 / 82.1 / 83.5 / 80.9 | +0.72 [-1.54, +2.94] | -0.88 [-2.45, +0.70] |

Hourly error (MAE, g/kWh) in Virginia: persistence 21.5, GBM 14.2, Transformer 13.5, Transformer + decision loss 14.4.
Figure: `results/experiments/torch_transformer/capture_24h.png` (24 h and 72 h panels).

## Honest reading
- **Verdict (pre-registered): TIE.** The decision-trained Transformer beats the production model at both 24 h and 72 h
  only in Virginia (1 of 5 grids; a WIN needed 3). It is never significantly worse at 24 h in any grid.
- **Virginia, our main place:** a single PyTorch model now captures 88-89% of the best possible saving at 24 h, up from
  84% for gradient boosting, scored on all of 2026. Sidharth's earlier stacker reached a similar level, but it needed a
  second model and could only be scored on May-Nov 2026. Here no 2026 month is used for training.
- **Surprise (exploratory, because this was not the pre-registered variant):** the plain Transformer, with no decision
  loss, did at least as well as the decision-trained one. It beat the production model at both delays in Virginia and
  Texas, and at 24 h in Germany and Britain. Our reading is that most of the gain comes from seeing all 76 hours at once
  (attention), not from the decision loss. The decision loss lowered validation regret in 4 of 5 grids, but it raised
  hourly error and added nothing on 2026. That fits the project's theme from the other side: a loss aimed at the choice
  does not automatically produce better choices either.
- **Where it fails (24 h, decision Transformer):** Virginia's worst days were 2026-09-27, 02-18 and 01-09 (39-40 g/kWh
  above the best window). The advice was worse than starting at midnight on 8.4% of days, the same rate as the
  production model. Germany (144 g/kWh on 2026-01-08) and Texas (122 on 01-23) fail hardest in winter, when wind swings
  are large and the evening forecast misses them.
- **Limits:** about 1,000 training days per grid is small for a neural net, so results vary by seed (validation regret
  ranged from 3.1 to 3.8 g/kWh across seeds in Virginia), and we average 3 seeds. Same signal caveat as the main project:
  PJM-wide average emissions, not Loudoun-specific and not marginal.

## Proposed README / write-up text (A integrates)
- How it works: "We also trained a 2-layer Transformer in PyTorch on a free Colab GPU. It sees all 76 future hours at
  once, and one version adds a decision loss (a soft choice of the cleanest window)."
- Results: "In Virginia the Transformer captured 88-89% of the best possible saving at 24 h versus 84% for gradient
  boosting (decision version: -1.0 g/kWh [-1.9, -0.3]; plain version: -1.3 [-2.1, -0.7]). By our pre-set rule that is a
  TIE overall, because it won only in Virginia. The plain Transformer, with no decision loss, did just as well, so the
  gain seems to come from looking at the next three days all at once rather than from the special loss."

## Proposed CREDITS line
- PyTorch (https://pytorch.org/), Transformer encoder layers; ListNet ranking loss idea from Cao et al., "Learning to
  Rank: From Pairwise Approach to Listwise Approach", ICML 2007. Trained on a free Google Colab T4 GPU.
