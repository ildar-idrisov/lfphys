# B3 review, check 3: v11's grid error. The run measures the time-step error of the screen pattern (a companion run
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# with 2 dt) but no grid error, and the model itself depends on the grid (the wall's edges are smoothed over one grid
# step, apparatus.plate: eps = h). Here the same world is run on the three grids the schema offers (coarse lambda/5,
# normal lambda/6, fine lambda/8) and the normalised screen patterns are compared at the fine grid's x by cubic-spline
# interpolation (its own error ~h^4 P''''/384 < 1e-4 of the peak here), and also at the x the grids share exactly.
# Reported: max |P_h - P_fine| / peak for each h, the fractions (screen, back, side), the fringe visibility, and the
# run's own time_step estimate for comparison.
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c03_v11_grid_convergence.py [preset] [small|full] \
#     > reviews/archive/2026-10-28_internal_B3/out/c03_v11_grid_<preset>_<size>.txt
import sys
import time

import numpy as np
from scipy.interpolate import CubicSpline
from harness import Harness

from v11_double_slit_2d.engine import apparatus as AP

V = "v11_double_slit_2d"
PRESET = sys.argv[1] if len(sys.argv) > 1 else "narrow"
SIZE = sys.argv[2] if len(sys.argv) > 2 else "small"
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "n_bohm": 100, "n_tracks": 10}
BASE = SMALL if SIZE == "small" else {"n_bohm": 100, "n_tracks": 10}

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
    c = h.checks()
    period = (s.geo.L - 0.5 * s.geo.w) / s.geo.d
    vis = AP.fringes(x, dens, period)[0]
    out[grid] = (x, dens, res["fractions"], c["time_step"]["value"], vis, s.g.shape)
    print(f"{grid}: grid {s.g.shape}, h = lambda/{1 / s.g.d[0]:.3g}, {time.time() - t0:.0f} s on {s.prop.device}; "
          f"fractions {res['fractions']}; time_step check {c['time_step']['value']:.2e}; visibility {vis:.4f}",
          flush=True)

xf, Pf = out["fine"][0], out["fine"][1]
pk = Pf.max()
for grid in ("coarse", "normal"):
    x, P = out[grid][0], out[grid][1]
    lo, hi = max(x[0], xf[0]), min(x[-1], xf[-1])
    xx = xf[(xf >= lo) & (xf <= hi)]
    d = CubicSpline(x, P)(xx) - CubicSpline(xf, Pf)(xx)
    common = np.isin(np.round(xf * 120).astype(int), np.round(x * 120).astype(int))
    xc = np.round(xf[common] * 120).astype(int)
    Pc = P[np.searchsorted(np.round(x * 120).astype(int), xc)]
    dc = Pc - Pf[common]
    fr = {k: out[grid][2][k] - out["fine"][2][k] for k in ("screen", "back", "side")}
    print(f"{grid} vs fine: max |P - P_fine| / peak = {np.max(np.abs(d)) / pk:.3e} (spline), "
          f"{np.max(np.abs(dc)) / pk:.3e} at the {int(common.sum())} shared x; fractions differ by "
          + ", ".join(f"{k} {v:+.2e}" for k, v in fr.items())
          + f"; visibility {out[grid][4] - out['fine'][4]:+.2e}; the run's time_step estimate: {out[grid][3]:.2e}")
