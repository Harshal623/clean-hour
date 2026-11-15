# E11: a decision-focused Transformer in PyTorch (branch exp/torch-transformer)

Owner: S (Sidharth's Claude). Status: **CODE READY, NOT YET RUN ON REAL DATA.** The data hosts are unreachable from
the agent's sandbox, so every number below must come from the Colab GPU run. Nothing here is a result yet.

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

## Results
_Pending the Colab run. Paste from `results/experiments/torch_transformer/summary.csv` and `run_log.json`:_

| Region | Slack | % of perfect saving: persistence / GBM / transformer_mse / transformer_decision | decision minus GBM [95% CI] |
|---|---|---|---|
| Virginia | 24 h | | |
| Virginia | 72 h | | |
| (other grids) | | | |

Verdict: _pending_. Worst days at 24 h: _pending_.

## Proposed README / write-up text (owner fills in the numbers after the run)
- How it works: "We also trained a 2-layer Transformer in PyTorch on a Colab GPU that sees all 76 future hours at
  once and is trained with a decision loss (a soft choice of the cleanest window) instead of only hourly error."
- Results, one sentence, whatever the verdict: "On 2026, the decision-trained Transformer captured X% of the best
  possible saving in Virginia at 24 h versus Y% for gradient boosting (difference Z g/kWh [lo, hi]); verdict: ___."
- If it loses: "The neural network did not beat gradient boosting on about 1,000 training days, so the simpler model stays."

## Proposed CREDITS line
- PyTorch (https://pytorch.org/), Transformer encoder layers; ListNet ranking loss idea from Cao et al., "Learning to
  Rank: From Pairwise Approach to Listwise Approach", ICML 2007. Trained on a free Google Colab T4 GPU.
