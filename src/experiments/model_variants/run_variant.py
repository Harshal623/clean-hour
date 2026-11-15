"""Usage: python -I -W ignore src/experiments/model_variants/run_variant.py VARIANT GRID
VARIANT in v1 (hyperparameter sweep), v2 (extended features), v3 (validation-fit blend), v4 (quantile loss).
Writes results/experiments/model_variants/raw/<variant>_<grid>.json
"""
import itertools
import json
import random
import sys
import time

import numpy as np

sys.path.insert(0, "src/experiments/model_variants")
from common import baseline, compare, day_costs, fit_delta_p, predict_delta_p, prep, val_score  # noqa: E402

RAW = "results/experiments/model_variants/raw"


def v1(key):
    P = prep(key)
    cb_test, cb_val = baseline(P)
    base_val = val_score(cb_val)
    grid = list(itertools.product([3, 5, 7], [0.03, 0.05, 0.1], [50, 100, 300]))
    random.Random(0).shuffle(grid)
    rows = []
    for depth, lr, leaf in grid[:15]:
        m = fit_delta_p(P["tr_part"], P["feats_full"], max_depth=depth, learning_rate=lr, min_samples_leaf=leaf)
        P["val"]["p"] = predict_delta_p(m, P["val"], P["feats_full"])
        rows.append(dict(max_depth=depth, learning_rate=lr, min_samples_leaf=leaf,
                         val=val_score(day_costs(P["val"], "p"))))
        print(key, rows[-1], flush=True)
    best = min(rows, key=lambda r: r["val"])
    adopt = best["val"] < base_val - 0.1
    chosen = dict(max_depth=best["max_depth"], learning_rate=best["learning_rate"],
                  min_samples_leaf=best["min_samples_leaf"]) if adopt else {}
    m = fit_delta_p(P["full_train"], P["feats_full"], **chosen)
    P["test"]["p"] = predict_delta_p(m, P["test"], P["feats_full"])
    return dict(variant="v1_hpo", grid=key, val_baseline=base_val, val_best=best, adopted_on_validation=bool(adopt),
                chosen=chosen, val_table=rows, test=compare(day_costs(P["test"], "p"), cb_test),
                test_days=len(cb_test))


def v2(key):
    P0 = prep(key)
    cb_test, cb_val = baseline(P0)
    P = prep(key, extras=True)
    m = fit_delta_p(P["tr_part"], P["feats_full"])
    P["val"]["p"] = predict_delta_p(m, P["val"], P["feats_full"])
    val_var = val_score(day_costs(P["val"], "p"))
    m = fit_delta_p(P["full_train"], P["feats_full"])
    P["test"]["p"] = predict_delta_p(m, P["test"], P["feats_full"])
    return dict(variant="v2_features", grid=key, val_baseline=val_score(cb_val), val_variant=val_var,
                adopted_on_validation=bool(val_var < val_score(cb_val) - 0.1), n_features=len(P["feats_full"]),
                features_added=[f for f in P["feats_full"] if f not in P0["feats_full"]],
                test=compare(day_costs(P["test"], "p"), cb_test), test_days=len(cb_test))


def v3(key):
    P = prep(key)
    cb_test, cb_val = baseline(P)
    m_v = fit_delta_p(P["tr_part"], P["feats_full"])
    h_v = fit_delta_p(P["tr_part"], P["feats_hist"])
    V = P["val"]
    V["m"], V["h"] = predict_delta_p(m_v, V, P["feats_full"]), predict_delta_p(h_v, V, P["feats_hist"])
    V["p"] = V["ci_same_hr"].fillna(V["m"])
    best = None
    for wm in np.arange(0, 1.01, 0.1):
        for wh in np.arange(0, 1.01 - wm, 0.1):
            wp = 1 - wm - wh
            V["b"] = wm * V["m"] + wh * V["h"] + wp * V["p"]
            s = val_score(day_costs(V, "b"))
            if best is None or s < best[0]:
                best = (s, wm, wh, wp)
    s, wm, wh, wp = best
    adopt = s < val_score(cb_val) - 0.1
    m_t = fit_delta_p(P["full_train"], P["feats_full"])
    h_t = fit_delta_p(P["full_train"], P["feats_hist"])
    T = P["test"]
    T["m"], T["h"] = predict_delta_p(m_t, T, P["feats_full"]), predict_delta_p(h_t, T, P["feats_hist"])
    T["p"] = T["ci_same_hr"].fillna(T["m"])
    wm, wh, wp = (wm, wh, wp) if adopt else (1.0, 0.0, 0.0)
    T["b"] = wm * T["m"] + wh * T["h"] + wp * T["p"]
    return dict(variant="v3_blend", grid=key, val_baseline=val_score(cb_val), val_blend=s,
                weights_fit_on_validation=dict(model=round(float(wm), 2), history_only=round(float(wh), 2),
                                               persistence=round(float(wp), 2)),
                adopted_on_validation=bool(adopt), test=compare(day_costs(T, "b"), cb_test), test_days=len(cb_test))


def v4(key):
    P = prep(key)
    cb_test, cb_val = baseline(P)
    rows = []
    for q in [0.5, 0.75, 0.9]:
        m = fit_delta_p(P["tr_part"], P["feats_full"], loss="quantile", quantile=q)
        P["val"]["p"] = predict_delta_p(m, P["val"], P["feats_full"])
        rows.append(dict(quantile=q, val=val_score(day_costs(P["val"], "p"))))
        print(key, rows[-1], flush=True)
    best = min(rows, key=lambda r: r["val"])
    adopt = best["val"] < val_score(cb_val) - 0.1
    if adopt:
        m = fit_delta_p(P["full_train"], P["feats_full"], loss="quantile", quantile=best["quantile"])
    else:
        m = fit_delta_p(P["full_train"], P["feats_full"])
    P["test"]["p"] = predict_delta_p(m, P["test"], P["feats_full"])
    return dict(variant="v4_quantile", grid=key, val_baseline=val_score(cb_val), val_table=rows,
                adopted_on_validation=bool(adopt),
                quantile_used=best["quantile"] if adopt else "baseline (squared loss)",
                test=compare(day_costs(P["test"], "p"), cb_test), test_days=len(cb_test))


if __name__ == "__main__":
    var, key = sys.argv[1], sys.argv[2]
    t = time.time()
    res = {"v1": v1, "v2": v2, "v3": v3, "v4": v4}[var](key)
    res["seconds"] = round(time.time() - t)
    json.dump(res, open(f"{RAW}/{var}_{key}.json", "w"), indent=1)
    print("DONE", var, key, res["seconds"], "s", flush=True)
