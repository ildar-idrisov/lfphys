# B3 review, check 4: what c03's grid dependence of v11 consists of. In v11 the wall's edges are smoothed over one grid
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# step (apparatus.smooth_step(u, eps) with eps = h), so a finer grid is also a different wall. Here the smoothing
# width is held fixed (EPS_FIXED for every grid, by replacing apparatus.smooth_step) and the three grids are compared
# again: what remains is the solver's own discretisation error for one fixed potential; the rest of c03's difference
# is the model's change with h.
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c04_v11_grid_fixed_wall.py [preset] [small|full] [eps] \
#     > reviews/archive/2026-10-28_internal_B3/out/c04_v11_grid_fixed_wall_<preset>_<size>.txt
import sys
import time

import numpy as np
from harness import Harness
from scipy.interpolate import CubicSpline

from v11_double_slit_2d.engine import apparatus as AP

V = "v11_double_slit_2d"
PRESET = sys.argv[1] if len(sys.argv) > 1 else "narrow"
SIZE = sys.argv[2] if len(sys.argv) > 2 else "small"
EPS_FIXED = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "n_bohm": 100, "n_tracks": 10}
BASE = SMALL if SIZE == "small" else {"n_bohm": 100, "n_tracks": 10}
_orig = AP.smooth_step


def fixed_step(u, eps):
    return _orig(u, EPS_FIXED)


AP.smooth_step = fixed_step
print(f"wall edges smoothed over a fixed {EPS_FIXED:g} lambda on every grid")
out = {}
for grid in ("coarse", "normal", "fine"):
    t0 = time.time()
    h = Harness(V, PRESET, {**BASE, "grid": grid}, seed=3)
    tu = h.sim.tunit
    while not h.sim.done and h.sim.tau < 400:
        h.run_to(h.sim.t + 2.0 * tu)
    s = h.sim
    xs, P = s._pattern(s.flux)
    m = s.on_screen
    x, p = xs[m], P[m]
    dens = p / np.trapezoid(p, x)
    res = h.of("result")[-1]
    period = (s.geo.L - 0.5 * s.geo.w) / s.geo.d
    out[grid] = (x, dens, res["fractions"])
    print(f"{grid}: grid {s.g.shape}, {time.time() - t0:.0f} s on {s.prop.device}; fractions {res['fractions']}; "
          f"visibility {AP.fringes(x, dens, period)[0]:.4f}",
          flush=True)

xf, Pf = out["fine"][0], out["fine"][1]
pk = Pf.max()
for grid in ("coarse", "normal"):
    x, P = out[grid][0], out[grid][1]
    lo, hi = max(x[0], xf[0]), min(x[-1], xf[-1])
    xx = xf[(xf >= lo) & (xf <= hi)]
    d = CubicSpline(x, P)(xx) - CubicSpline(xf, Pf)(xx)
    fr = {k: out[grid][2][k] - out["fine"][2][k] for k in ("screen", "back", "side")}
    print(f"{grid} vs fine (fixed wall): max |P - P_fine| / peak = {np.max(np.abs(d)) / pk:.3e}; fractions differ by "
          + ", ".join(f"{k} {v:+.2e}" for k, v in fr.items()))
