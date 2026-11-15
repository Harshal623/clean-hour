"""Fast project health check (about 10 s). Run from the repo root: python -I -W ignore scripts/check.py
Every branch must pass this before it is merged into main."""
import importlib.util, itertools, os, random, re, sys
import pandas as pd

ok = True
def fail(msg):
    global ok; ok = False; print("FAIL:", msg)

# 1. results exist and are sane
S = pd.read_csv("results/multigrid_summary.csv")
for g in ["pjm", "ciso", "erco", "de", "gb"]:
    if g not in set(S.grid): fail(f"grid {g} missing from multigrid_summary.csv")
if (S.test_days < 300).any(): fail("a grid has fewer than 300 test days")
P = pd.read_csv("results/test_predictions_all.csv.gz")
if P[["y", "pred", "clim"]].isna().any().any(): fail("NaN in y/pred/clim of test_predictions_all")
if P.persist.isna().sum() > 10: fail("too many NaN persist rows")
# 2. README numbers match the csv (Virginia, 24 h)
v = S[(S.grid == "pjm") & (S.slip_h == 24)].iloc[0]
readme = open("README.md", encoding="utf-8").read()
for label, val in [("immediate", v.immediate), ("persistence", v.persistence), ("model", v.model), ("oracle", v.oracle)]:
    if f"{val:.1f}" not in readme: fail(f"README does not contain Virginia 24h {label} = {val:.1f}")
for g, name in [("ciso", "California"), ("gb", "Great Britain")]:
    r = S[(S.grid == g) & (S.slip_h == 24)].iloc[0]
    if f"{r.model_pct_saved:.1f}" not in readme: fail(f"README missing {name} 24h model % saved {r.model_pct_saved:.1f}")
# 3. no leakage markers in the evaluation scripts
for f in ["src/multigrid.py", "src/sweep.py"]:
    t = open(f, encoding="utf-8").read()
    if "train_test_split" in t or "shuffle=True" in t or ".sample(frac" in t: fail(f"{f} may shuffle rows")
# 4. app logic works for every option
sys.argv = ["x"]
spec = importlib.util.spec_from_file_location("appmod", "app/app.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
days = random.Random(1).sample(m.DAY_LABELS, 3); n = 0
for r, a, w, d in itertools.product(m.REGIONS, m.APPLIANCES, m.WAIT, days):
    try: m.advise(r, a, w, d); m.scorecard(r, w); n += 1
    except Exception as e: fail(f"app {r}/{a}/{w}/{d}: {e!r}")
print(f"app combos ok: {n}")
print("ALL CHECKS PASSED" if ok else "CHECKS FAILED"); sys.exit(0 if ok else 1)
