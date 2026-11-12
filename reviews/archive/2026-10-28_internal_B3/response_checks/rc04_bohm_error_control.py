# Response to B3-4: v11's Bohm integration with error control (Dormand-Prince 5(4), err <= atol + rtol |displacement|)
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# against a refined integration of the same wave (rtol 1e-7: 100 times the default 1e-5), 400 particles.
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/response_checks/rc04_bohm_error_control.py <preset> <tol_factors...>
import sys
import time

import numpy as np
from harness import Harness

import v11_double_slit_2d.viz as VZ
from lfphys.theories.interpretations import bohm

ORIG = bohm.advance_ensemble
PRESET = sys.argv[1]
FACTORS = [float(a) for a in sys.argv[2:]] or [1e-3]


def run(tol_f, disp_f, cap):
    # tol_f: rtol (atol = rtol / 10 of the grid step)
    def adv(grid, snaps, X, h, H=None, order=8, xp=None, rtol=None, atol=None, max_disp=None, max_sub=4096):
        return ORIG(grid, snaps, X, h, H, order, xp, rtol=tol_f, atol=0.1 * tol_f * min(grid.d),
                    max_disp=disp_f * min(grid.d), max_sub=cap)
    VZ.bohm.advance_ensemble = adv
    t0 = time.time()
    h = Harness("v11_double_slit_2d", PRESET, {"n_bohm": 400, "n_tracks": 10}, seed=11)
    while not h.sim.done and h.sim.tau < 400:
        h.run_to(h.sim.t + 2.0 * h.sim.tunit)
    s = h.sim
    VZ.bohm.advance_ensemble = ORIG
    print(f"rtol {tol_f:g}, max_disp {disp_f:g} step, cap {cap}: {time.time() - t0:.0f} s, max sub {s.max_sub}, "
          f"screen {(s.fate == 1).sum()}", flush=True)
    return s.fate.copy(), s.hit_x.copy(), (s.geo.L - 0.5 * s.geo.w) / s.geo.d


R = run(1e-7, 1.0, 16384)
for f in FACTORS:
    X = run(f, 1.0, 4096)
    both = (X[0] == 1) & (R[0] == 1)
    dx = np.abs(X[1][both] - R[1][both])
    print(f"  rtol {f:g}: fates differ {int((X[0] != R[0]).sum())}; |dx| median {np.median(dx):.1e}, 95% "
          f"{np.percentile(dx, 95):.1e}, max {dx.max():.2e} lambda (period {R[2]:.3g})", flush=True)
