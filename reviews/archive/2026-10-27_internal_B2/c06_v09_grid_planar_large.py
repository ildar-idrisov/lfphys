# B2 review, check 6: the planar loops of v09 at rho in [2, 3] with a random plane (c03 restricted; same code otherwise).
# use). Runs each world to its end (space "lab": the closing checks do not depend on the space, and no field volume
# is built) and reports every non-info check that fails, every refusal, and the measured round-off against the bound.
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests light-funnel-viz python3 reviews/2026-10-27_internal_B2/c03_v09_grid.py [N]
import json
import math
import sys
import time

import numpy as np
from harness import Harness

V = "v09_thomas_3d"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
rng = np.random.default_rng(20261027)
loops = ["thomas", "circle", "triangle", "polygon"]  # planar loops only


def failed(h):
    return [(c["id"], c.get("value"), c.get("tol")) for c in h.checks().values() if not c.get("info") and (
        c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


rows = []
t0 = time.time()
for k in range(N):
    p = {"space": "lab", "loop": loops[k % len(loops)], "rho": float(rng.uniform(2.0, 3.0)),
         "turns": int(rng.integers(1, 7)), "sides": int(rng.integers(3, 25)), "alpha": float(rng.uniform(10, 170)),
         "chi": float(rng.uniform(0, 80)), "nth": float(rng.uniform(0, 180)), "nph": float(rng.uniform(0, 360)),
         "accel_g": float(rng.uniform(0.1, 10))}
    try:
        h = Harness(V, None, p)
        h.run_to(h.sim.T_end * 1.0001)
    except AssertionError:
        raise
    except Exception as e:
        rows.append({"p": p, "refused": str(e)[:120]})
        continue
    sim = h.sim
    est, bound = sim._round_est(), sim._round_bound()
    rows.append({"p": p, "failed": failed(h), "errors": h.errors(), "est": est, "bound": bound,
                 "ratio": bound / max(est, 1e-300), "eta_max": sim.eta_max, "pieces": len(sim.pieces)})

bad = [r for r in rows if r.get("failed") or r.get("errors")]
ref = [r for r in rows if "refused" in r]
ok = [r for r in rows if "est" in r]
print(f"{N} worlds in {time.time() - t0:.0f} s: {len(ok)} ran, {len(ref)} refused, {len(bad)} with failed checks/errors")
for r in bad:
    print("FAILED", json.dumps(r["p"]), r.get("failed"), r.get("errors"), f"est={r['est']:.2e} bound={r['bound']:.2e}")
for r in ref:
    print("REFUSED", r["p"]["loop"], f"rho={r['p']['rho']:.3f} turns={r['p']['turns']} chi={r['p']['chi']:.1f}",
          r["refused"])
if ok:
    worst = min(ok, key=lambda r: r["ratio"])
    print(f"smallest bound/est = {worst['ratio']:.2f} at {json.dumps(worst['p'])} (est {worst['est']:.2e})")
    for lp in loops:
        rs = [r for r in ok if r["p"]["loop"] == lp]
        if rs:
            print(f"  {lp:9s} n={len(rs):3d} min bound/est = {min(r['ratio'] for r in rs):9.2f}  "
                  f"max est = {max(r['est'] for r in rs):.2e}")
