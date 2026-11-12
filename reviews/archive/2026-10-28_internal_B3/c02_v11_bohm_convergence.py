# B3 review, check 2: are v11's Bohm trajectories converged, particle by particle?
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# The owner asked for «точные траектории Бома в 2D». The run checks the ensemble (Kolmogorov-Smirnov of the hits
# against the flux pattern, the fraction on the screen, no crossing of the axis) but nothing about individual
# trajectories. Here the same world (same seed, same starts) is run with
#   A: the defaults (RK4 over 2 dt, sub-steps when |v| 2dt > one grid step, at most 64, decided at the start of the pair);
#   B: the same wave, finer Bohm integration (sub-steps when |v| 2dt > 1/8 grid step, at most 512);
#   C: the wave with dt/2 (E0 dt = 0.05) and the default Bohm integration;
# and each particle's fate, slit and hit position are compared (A against B: the integrator; A against C: the wave's
# time step as the trajectories feel it).
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c02_v11_bohm_convergence.py [preset] [small|full] \
#     > reviews/archive/2026-10-28_internal_B3/out/c02_v11_bohm_convergence_<preset>.txt
import functools
import sys
import time

import numpy as np
from harness import Harness

import v11_double_slit_2d.viz as VZ
from lfphys.theories.interpretations import bohm

V = "v11_double_slit_2d"
PRESET = sys.argv[1] if len(sys.argv) > 1 else "narrow"
SIZE = sys.argv[2] if len(sys.argv) > 2 else "small"
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 600,
         "n_tracks": 20}
PARAMS = SMALL if SIZE == "small" else {"n_bohm": 1000}
ORIG = bohm.advance_ensemble


def run(variant):
    VZ.DT_E0 = 0.1
    VZ.bohm.advance_ensemble = ORIG
    if variant == "B":
        def fine(grid, snaps, X, h, H=None, order=8, xp=None, max_disp=None, max_sub=64):
            return ORIG(grid, snaps, X, h, H, order, xp, max_disp=min(grid.d) / 8, max_sub=512)
        VZ.bohm.advance_ensemble = fine
    if variant == "C":
        VZ.DT_E0 = 0.05
    t0 = time.time()
    h = Harness(V, PRESET, PARAMS, seed=7)
    tu = h.sim.tunit
    while not h.sim.done and h.sim.tau < 200:
        h.run_to(h.sim.t + 1.0 * tu)
    s = h.sim
    VZ.bohm.advance_ensemble = ORIG
    VZ.DT_E0 = 0.1
    res = h.of("result")[-1]
    print(f"variant {variant}: {time.time() - t0:.0f} s, device {s.prop.device}, max sub-steps {s.max_sub}, "
          f"bohm {res['bohm']}", flush=True)
    return {"fate": s.fate.copy(), "slit": s.slit.copy(), "hit": s.hit_x.copy(), "geo": s.geo,
            "checks": {k: (c.get('value'), c.get('ok')) for k, c in h.checks().items() if k.startswith('bohm') or k in ('no_crossing', 'time_step')}}


A = run("A")
B = run("B")
C = run("C")
geo = A["geo"]
period = (geo.L - 0.5 * geo.w) / geo.d
print(f"\npreset {PRESET} ({SIZE}); fringe period near the axis {period:.3g} lambda; screen half-width {geo.screen_half:.3g}")
for name, X in (("B (finer Bohm sub-steps)", B), ("C (wave dt/2)", C)):
    same_fate = A["fate"] == X["fate"]
    both = (A["fate"] == 1) & (X["fate"] == 1)
    dx = np.abs(A["hit"][both] - X["hit"][both])
    slit_diff = (A["slit"] != X["slit"]) & (A["slit"] > 0) & (X["slit"] > 0)
    print(f"A vs {name}: N = {len(A['fate'])}; fate differs {int((~same_fate).sum())}; slit label differs "
          f"{int(slit_diff.sum())}; both on screen {int(both.sum())}: |dx| median {np.median(dx):.2e}, "
          f"95% {np.percentile(dx, 95):.2e}, max {dx.max():.2e} lambda; |dx| > period/10: {int((dx > period / 10).sum())}, "
          f"> period/2: {int((dx > period / 2).sum())}")
for nm, X in (("A", A), ("B", B), ("C", C)):
    print(nm, X["checks"])
