"""E11: a decision-focused Transformer in PyTorch. Can a neural net trained to CHOOSE hours beat our gradient boosting?

Question
    Our production model (scikit-learn gradient boosting) predicts each hour on its own. Sidharth's stacker showed that
    training for the ranking of hours helps in Virginia. Here we build that idea into one neural network:
    - It sees all 76 future hours at once (a Transformer encoder, so every hour can attend to every other hour),
      instead of predicting each hour separately.
    - It is trained with a decision loss: a differentiable "soft choice" of the cleanest 4-hour window
      (ListNet-style cross-entropy over window starts at 12, 24 and 72 h of slack), added to the usual Huber loss.

Variants (both are 3-seed ensembles, same features as the production model, no new data):
    transformer_mse       Huber loss on the hourly level only (the plain neural-net version)
    transformer_decision  Huber loss + decision loss (lambda = 1.0, fixed before looking at 2026)
    blend                 50/50 average of production GBM and transformer_decision (no fitting)

Honest protocol (fixed before scoring 2026)
    1. Train on 2023-01-01..2025-06-30, validate on 2025-07-01..2025-12-31 to pick the number of epochs
       (early stopping on validation decision regret at 24 h).
    2. Refit on all of 2023-2025 for that many epochs. Score ONCE on every complete 2026 day.
    3. Same 2026 days, same scoring code and same 7-day block bootstrap as src/multigrid.py.
       The production GBM forecasts come from results/test_predictions_all.csv.gz (saved, not retrained).
    Kill rule: WIN in a grid if transformer_decision minus GBM has a 95% interval entirely below zero at BOTH 24 h and
    72 h. Overall WIN needs >= 3 of 5 grids. LOSS if it is significantly worse at 24 h in >= 3 grids. Otherwise TIE.

Run from the repo root after the data is cached (python -I src/grids.py):
    python -I -W ignore src/experiments/torch_transformer/run.py            # all five grids
    python -I -W ignore src/experiments/torch_transformer/run.py pjm        # Virginia only (fast check)
Uses a GPU if one is available; also runs on CPU (a few minutes per grid).
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, "src")
from multigrid import HIST  # noqa: E402
from sweep import JOB, NT, TEST_START, WX, best_start, block_boot  # noqa: E402

OUT = "results/experiments/torch_transformer"
NAMES = {"pjm": "Virginia", "ciso": "California", "erco": "Texas", "de": "Germany", "gb": "Great Britain"}
VAL_START = pd.Timestamp("2025-07-01")
SLIPS = [12, 24, 48, 72]
LOSS_SLIPS = [12, 24, 72]
SEEDS = [0, 1, 2]
LAMBDA = 1.0   # weight of the decision loss (fixed in advance, not tuned on 2026)
TAU = 0.1      # softness of the window choice, in units of the grid's carbon std
MAX_EPOCHS, PATIENCE, BATCH = 80, 10, 64
DEV = "cuda" if torch.cuda.is_available() else "cpu"


# ---------------------------------------------------------------- data: one row per decision day, 76 hours each
def to_days(data, feats):
    d = data.sort_values(["day", "j"])
    cnt = d.groupby("day").size()
    keep = cnt[cnt == NT].index
    d = d[d.day.isin(keep)]
    n = len(keep)
    X = d[feats].to_numpy(float).reshape(n, NT, len(feats))
    base = d["ci_hod_mean7d"].fillna(d["ci_same_hr"]).fillna(d["ci_mean7d"]).to_numpy(float).reshape(n, NT)
    y = d["y"].to_numpy(float).reshape(n, NT)
    return pd.DatetimeIndex(keep), X, base, y


class Scaler:
    """Standardise each feature with TRAINING statistics only; missing inputs become 0 (the training mean)."""
    def __init__(self, X, y, base):
        flat = X.reshape(-1, X.shape[-1])
        self.mu, self.sd = np.nanmean(flat, 0), np.nanstd(flat, 0) + 1e-6
        self.scale = float(np.nanstd(y - base))
    def x(self, X):
        return np.nan_to_num((X - self.mu) / self.sd, nan=0.0).astype(np.float32)


# ---------------------------------------------------------------- model
class HorizonTransformer(nn.Module):
    """Each of the 76 future hours is a token; self-attention lets the forecast for one hour use the others."""
    def __init__(self, n_feat, d=64, heads=4, layers=2, drop=0.1):
        super().__init__()
        self.inp = nn.Sequential(nn.Linear(n_feat, d), nn.GELU(), nn.Linear(d, d))
        self.pos = nn.Parameter(torch.zeros(1, NT, d))
        layer = nn.TransformerEncoderLayer(d, heads, 4 * d, drop, batch_first=True, norm_first=True)
        self.enc = nn.TransformerEncoder(layer, layers)
        self.head = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, 1))
        nn.init.normal_(self.pos, std=0.02)

    def forward(self, x):                      # x: (batch, 76, features)
        return self.head(self.enc(self.inp(x) + self.pos)).squeeze(-1)   # (batch, 76) change from base


def windows(v):
    """Mean of every 4-hour window: (batch, 76) -> (batch, 73). NaN stays NaN."""
    return F.avg_pool1d(v.unsqueeze(1), JOB, stride=1).squeeze(1)


def decision_loss(pred_lvl, y_lvl):
    """ListNet cross-entropy between the true and predicted 'soft choice' of start hour, averaged over slips."""
    wp, wt = windows(pred_lvl), windows(y_lvl)
    out = 0.0
    for slip in LOSS_SLIPS:
        p, t = wp[:, :slip + 1], wt[:, :slip + 1]
        ok = ~torch.isnan(t)
        t_logit = torch.where(ok, -t / TAU, torch.full_like(t, -1e9))
        p_logit = torch.where(ok, -p / TAU, torch.full_like(p, -1e9))
        out = out + -(F.softmax(t_logit, 1) * F.log_softmax(p_logit, 1)).sum(1).mean()
    return out / len(LOSS_SLIPS)


def regret(pred_lvl, y, slip=24):
    """Average g/kWh lost versus perfect hindsight when choosing with pred (used for early stopping only)."""
    r = []
    for p, t in zip(pred_lvl, y):
        if np.isnan(t[:slip + JOB]).any():
            continue
        r.append(t[best_start(p, slip):][:JOB].mean() - t[best_start(t, slip):][:JOB].mean())
    return float(np.mean(r))


def train_one(Xtr, dtr, ytr_n, lam, seed, epochs, Xva=None, va=None):
    """dtr = (y - base)/scale target; ytr_n = y/scale (for the decision loss). Returns model and best epoch."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    m = HorizonTransformer(Xtr.shape[-1]).to(DEV)
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    X, D, Y = (torch.tensor(a, dtype=torch.float32, device=DEV) for a in (Xtr, dtr, ytr_n))
    B = Y - D  # base / scale
    best, best_ep, bad, state = np.inf, epochs, 0, None
    for ep in range(1, epochs + 1):
        m.train()
        for idx in torch.randperm(len(X), device=DEV).split(BATCH):
            out = m(X[idx])
            ok = ~torch.isnan(D[idx])
            loss = F.huber_loss(out[ok], D[idx][ok], delta=1.0)
            if lam > 0:
                loss = loss + lam * decision_loss(out + B[idx], Y[idx])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(m.parameters(), 1.0)
            opt.step()
        sched.step()
        if va is not None:  # early stopping on validation decision regret (never on 2026)
            r = regret(va["base"] + predict(m, Xva) * va["scale"], va["y"])
            if r < best - 1e-4:
                best, best_ep, bad = r, ep, 0
                state = {k: v.detach().clone() for k, v in m.state_dict().items()}
            else:
                bad += 1
                if bad >= PATIENCE:
                    break
    if state is not None:
        m.load_state_dict(state)
    return m, best_ep, best


@torch.no_grad()
def predict(m, X):
    m.eval()
    return m(torch.tensor(X, dtype=torch.float32, device=DEV)).cpu().numpy()


def fit_variant(name, lam, tr, te_X, feats):
    """Pick epochs on 2025 H2, refit on 2023-2025, return the 3-seed ensemble forecast for the test days."""
    sub = tr[tr.day < VAL_START]
    val = tr[tr.day >= VAL_START]
    _, Xs, bs, ys = to_days(sub, feats)
    _, Xv, bv, yv = to_days(val, feats)
    _, Xa, ba, ya = to_days(tr, feats)
    sc = Scaler(Xs, ys, bs)
    eps, vals = [], []
    for seed in SEEDS:
        _, ep, r = train_one(sc.x(Xs), (ys - bs) / sc.scale, ys / sc.scale, lam, seed, MAX_EPOCHS,
                             sc.x(Xv), {"base": bv, "y": yv, "scale": sc.scale})
        eps.append(ep)
        vals.append(r)
    n_ep = int(np.median(eps))
    sc = Scaler(Xa, ya, ba)  # refit scaler on all training years
    preds = []
    for seed in SEEDS:
        m, _, _ = train_one(sc.x(Xa), (ya - ba) / sc.scale, ya / sc.scale, lam, seed, n_ep)
        preds.append(predict(m, sc.x(te_X)) * sc.scale)
    log = {"variant": name, "epochs_per_seed": eps, "epochs_used": n_ep,
           "val_regret_24h_g_per_kwh": [round(v, 2) for v in vals]}
    return np.mean(preds, 0), log


# ---------------------------------------------------------------- one grid
def run_grid(key, data, saved):
    """data: rows from multigrid.build_rows_g; saved: this grid's rows of results/test_predictions_all.csv.gz."""
    feats = HIST + (["dem_fcst"] if data["dem_fcst"].notna().any() else []) + WX
    tr = data[(data.day < TEST_START)]
    te = data[data.day >= TEST_START]
    ok = te.groupby("day")["y"].apply(lambda v: v.notna().all() and len(v) == NT)
    te = te[te.day.isin(ok[ok].index)]
    days, Xt, bt, yt = to_days(te, feats)
    logs = []
    fc = {}
    for name, lam in [("transformer_mse", 0.0), ("transformer_decision", LAMBDA)]:
        t0 = time.time()
        delta, log = fit_variant(name, lam, tr, Xt, feats)
        fc[name] = bt + delta
        log["seconds"] = round(time.time() - t0, 1)
        logs.append(log)
        print(f"  {name}: {log}", flush=True)

    # align with the saved production forecasts (same days, same hours)
    sv = saved.copy()
    sv["day"] = pd.to_datetime(sv["day"])
    sv = sv[sv.day.isin(days)].sort_values(["day", "j"])
    common = pd.DatetimeIndex(sorted(set(days) & set(sv.day.unique())))
    pick = np.isin(days, common)
    sv = sv[sv.day.isin(common)]
    n = len(common)
    gbm = sv["pred"].to_numpy(float).reshape(n, NT)
    y_saved = sv["y"].to_numpy(float).reshape(n, NT)
    y = yt[pick]
    drift = float(np.nanmax(np.abs(y - y_saved)))  # sanity: the rebuilt data must match the saved test set
    methods = {"persistence": sv["persist"].to_numpy(float).reshape(n, NT),
               "climatology": sv["clim"].to_numpy(float).reshape(n, NT),
               "gbm (production)": gbm,
               "transformer_mse": fc["transformer_mse"][pick],
               "transformer_decision": fc["transformer_decision"][pick]}
    methods["blend (gbm + transformer_decision)"] = (gbm + methods["transformer_decision"]) / 2

    rows = []
    for i, day in enumerate(common):
        r = {"day": day, "immediate": y[i, :JOB].mean()}
        for slip in SLIPS:
            r[f"oracle_{slip}"] = y[i, best_start(y[i], slip):][:JOB].mean()
            for nm, p in methods.items():
                r[f"{nm}_{slip}"] = y[i, best_start(p[i], slip):][:JOB].mean()
        rows.append(r)
    costs = pd.DataFrame(rows).set_index("day")
    summ = []
    for slip in SLIPS:
        imm, orc = costs["immediate"].mean(), costs[f"oracle_{slip}"].mean()
        for nm, p in methods.items():
            v = costs[f"{nm}_{slip}"].mean()
            d = (costs[f"{nm}_{slip}"] - costs[f"gbm (production)_{slip}"]).values
            lo, hi = block_boot(d, n=3000) if nm != "gbm (production)" else (0.0, 0.0)
            summ.append({"grid": key, "region": NAMES[key], "slip_h": slip, "method": nm, "test_days": n,
                         "g_per_kwh": v, "pct_saved_vs_midnight": 100 * (imm - v) / imm,
                         "pct_of_perfect_saving": 100 * (imm - v) / (imm - orc),
                         "minus_gbm": d.mean(), "minus_gbm_lo": lo, "minus_gbm_hi": hi,
                         "hourly_mae": float(np.nanmean(np.abs(p - y)))})
    pred_out = pd.DataFrame({"grid": key, "day": np.repeat(common, NT), "j": np.tile(np.arange(NT), n),
                             "y": y.ravel(), "gbm": gbm.ravel(),
                             "transformer_mse": methods["transformer_mse"].ravel(),
                             "transformer_decision": methods["transformer_decision"].ravel()}).round(2)
    reg = (costs["transformer_decision_24"] - costs["oracle_24"]).sort_values(ascending=False)
    worst = [f"{d.date()} ({v:.0f} g/kWh above the best window)" for d, v in reg.head(3).items()]
    worse_than_midnight = 100 * float((costs["transformer_decision_24"] > costs["immediate"] + 1e-9).mean())
    print(f"  failure check (24 h): worst days {worst}; advice worse than midnight on {worse_than_midnight:.1f}% of days")
    return pd.DataFrame(summ), costs.assign(grid=key), pred_out, {"grid": key, "y_max_abs_diff_vs_saved": drift,
                                                                    "worst_days_24h": worst,
                                                                    "pct_days_worse_than_midnight_24h": worse_than_midnight,
                                                                    "variants": logs}


def verdict(S):
    t = S[S.method == "transformer_decision"].set_index(["grid", "slip_h"])
    wins = [g for g in NAMES if g in t.index.get_level_values(0)
            and t.loc[(g, 24), "minus_gbm_hi"] < 0 and t.loc[(g, 72), "minus_gbm_hi"] < 0]
    losses = [g for g in NAMES if g in t.index.get_level_values(0) and t.loc[(g, 24), "minus_gbm_lo"] > 0]
    v = "WIN" if len(wins) >= 3 else ("LOSS" if len(losses) >= 3 else "TIE")
    return v, wins, losses


def main():
    from grids import load_grid_data  # imported here so the module can be tested without data
    from multigrid import build_rows_g
    from grids import GRIDS
    keys = sys.argv[1:] or list(NAMES)
    os.makedirs(OUT, exist_ok=True)
    print("device:", DEV, "| torch", torch.__version__, flush=True)
    saved = pd.read_csv("results/test_predictions_all.csv.gz")
    S, C, P, L = [], [], [], []
    for key in keys:
        print(f"\n=== {NAMES[key]}", flush=True)
        g, w = load_grid_data(key)
        data = build_rows_g(g, w, GRIDS[key][1])
        s, c, p, log = run_grid(key, data, saved[saved.grid == key].drop(columns="grid"))
        if log["y_max_abs_diff_vs_saved"] > 0.5:
            print(f"  WARNING: rebuilt 2026 data differs from the saved test set by up to "
                  f"{log['y_max_abs_diff_vs_saved']:.2f} g/kWh; data was re-downloaded and revised upstream.")
        S.append(s), C.append(c), P.append(p), L.append(log)
        show = s[s.slip_h.isin([24, 72])][["slip_h", "method", "g_per_kwh", "pct_of_perfect_saving", "minus_gbm",
                                           "minus_gbm_lo", "minus_gbm_hi", "hourly_mae"]]
        print(show.round(2).to_string(index=False), flush=True)
    S = pd.concat(S)
    S.to_csv(f"{OUT}/summary.csv", index=False)
    pd.concat(C).to_csv(f"{OUT}/per_day_costs.csv.gz")
    pd.concat(P).to_csv(f"{OUT}/predictions.csv.gz", index=False)
    v, wins, losses = verdict(S)
    json.dump({"verdict": v, "wins": wins, "significantly_worse_24h": losses, "device": DEV,
               "torch": torch.__version__, "lambda": LAMBDA, "tau": TAU, "seeds": SEEDS, "grids": L},
              open(f"{OUT}/run_log.json", "w"), indent=1, default=str)
    print(f"\nVERDICT (kill rule fixed in advance): {v}. Wins: {wins or 'none'}. Significantly worse at 24 h: "
          f"{losses or 'none'}.")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        t = S[S.slip_h == 24].pivot(index="region", columns="method", values="pct_of_perfect_saving")
        cols = ["persistence", "gbm (production)", "transformer_mse", "transformer_decision"]
        ax = t[[c for c in cols if c in t]].plot.bar(figsize=(9, 4), rot=0)
        ax.set_ylabel("% of the best possible saving (24 h slack)")
        ax.set_title("2026 held-out test: does a decision-trained Transformer pick cleaner hours?")
        ax.set_ylim(0, 105)
        ax.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(f"{OUT}/capture_24h.png", dpi=150)
    except Exception as e:  # noqa
        print("figure skipped:", e)


if __name__ == "__main__":
    main()
