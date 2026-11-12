# B3 review, check 10 (follows check 2): a convergence sequence of v11's Bohm integration on the full "narrow" preset.
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# The same world (same seed, same starts, n_bohm = 400) is run with the Bohm sub-step criterion |v| 2dt > m (sub-steps
# up to the cap) for m = one grid step (the default, cap 64), 1/2 (cap 128), 1/4 (cap 256), 1/8 (cap 512), and finally
# with the wave's dt halved as well and m = 1/8 (the reference R). For each, the particles' fates, slits and hit
# positions are compared with R: if the default were converged, every refinement would change the hits by much less
# than a fringe. Results are saved (out/c10_*.npz) and printed.
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c10_v11_bohm_sequence.py \
#     > reviews/archive/2026-10-28_internal_B3/out/c10_v11_bohm_sequence.txt
import sys
import time

import numpy as np
from harness import Harness

import v11_double_slit_2d.viz as VZ
from lfphys.theories.interpretations import bohm

V = "v11_double_slit_2d"
PRESET = sys.argv[1] if len(sys.argv) > 1 else "narrow"
PARAMS = {"n_bohm": 400, "n_tracks": 10}
ORIG = bohm.advance_ensemble
OUT = "/lf/reviews/archive/2026-10-28_internal_B3/out"


def run(frac, cap, dt_e0):
    def adv(grid, snaps, X, h, H=None, order=8, xp=None, max_disp=None, max_sub=64):
        return ORIG(grid, snaps, X, h, H, order, xp, max_disp=min(grid.d) * frac, max_sub=cap)
    VZ.bohm.advance_ensemble = adv
    VZ.DT_E0 = dt_e0
    t0 = time.time()
    h = Harness(V, PRESET, PARAMS, seed=11)
    tu = h.sim.tunit
    while not h.sim.done and h.sim.tau < 400:
        h.run_to(h.sim.t + 2.0 * tu)
    s = h.sim
    VZ.bohm.advance_ensemble = ORIG
    VZ.DT_E0 = 0.1
    print(f"m = {frac:g} grid step, cap {cap}, E0 dt = {dt_e0:g}: {time.time() - t0:.0f} s, max sub-steps {s.max_sub}, "
          f"screen {(s.fate == 1).sum()}, back {(s.fate == 2).sum()}, side {(s.fate == 3).sum()}", flush=True)
    return {"fate": s.fate.copy(), "slit": s.slit.copy(), "hit": s.hit_x.copy(), "L": s.geo.L, "w": s.geo.w,
            "d": s.geo.d}


runs = {}
for key, (frac, cap, dte) in {"m1": (1.0, 64, 0.1), "m1/2": (0.5, 128, 0.1), "m1/4": (0.25, 256, 0.1),
                              "m1/8": (0.125, 512, 0.1), "R": (0.125, 512, 0.05)}.items():
    runs[key] = run(frac, cap, dte)
    np.savez(f"{OUT}/c10_{key.replace('/', '_')}.npz", **{k: v for k, v in runs[key].items() if isinstance(v, np.ndarray)})
R = runs["R"]
period = (R["L"] - 0.5 * R["w"]) / R["d"]
print(f"\nagainst R (E0 dt = 0.05, m = 1/8): fringe period near the axis {period:.3g} lambda")
for key in ("m1", "m1/2", "m1/4", "m1/8"):
    X = runs[key]
    both = (X["fate"] == 1) & (R["fate"] == 1)
    dx = np.abs(X["hit"][both] - R["hit"][both])
    print(f"  {key:5s}: fate differs {int((X['fate'] != R['fate']).sum()):3d}; slit differs "
          f"{int(((X['slit'] != R['slit']) & (X['slit'] > 0) & (R['slit'] > 0)).sum())}; on screen in both {int(both.sum())}: "
          f"|dx| median {np.median(dx):.1e}, 90% {np.percentile(dx, 90):.1e}, max {dx.max():.2e} lambda; "
          f"> period/10: {int((dx > period / 10).sum())}, > period/2: {int((dx > period / 2).sum())}")
