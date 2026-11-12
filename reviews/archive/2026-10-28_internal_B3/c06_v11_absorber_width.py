# B3 review, check 6: v11's absorbing layers beyond the angles its `absorbers` check covers. The layers reflect waves
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# that meet them at grazing incidence (c05 (b): R = 7e-3 at kn = 0.3 k0, 0.07 at 0.2 k0, 0.3 at 0.1 k0), and the
# run's check looks only at kn in [0.9, 1.1] k0 (normal and the screen's widest angle). Here the same world is run with
# the layers 6 lambda wide (the default) and 12 lambda wide (a gentler ramp: smaller reflection at every angle, the
# physical region unchanged) and the screen patterns are compared.
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c06_v11_absorber_width.py [preset] [small|full] \
#     > reviews/archive/2026-10-28_internal_B3/out/c06_v11_absorber_width_<preset>_<size>.txt
import sys
import time

import numpy as np
from harness import Harness

from v11_double_slit_2d.engine import apparatus as AP

V = "v11_double_slit_2d"
PRESET = sys.argv[1] if len(sys.argv) > 1 else "narrow"
SIZE = sys.argv[2] if len(sys.argv) > 2 else "small"
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 100,
         "n_tracks": 10}
BASE = SMALL if SIZE == "small" else {"n_bohm": 100, "n_tracks": 10}

out = {}
for width in (6.0, 12.0):
    AP.ABS_W = width
    t0 = time.time()
    h = Harness(V, PRESET, BASE, seed=3)
    tu = h.sim.tunit
    while not h.sim.done and h.sim.tau < 400:
        h.run_to(h.sim.t + 2.0 * tu)
    s = h.sim
    xs, P = s._pattern(s.flux)
    m = s.on_screen
    res = h.of("result")[-1]
    c = h.checks()
    out[width] = (np.round(xs[m] / s.g.d[0]).astype(int), P[m], res["fractions"])
    print(f"layers {width:g} lambda: grid {s.g.shape}, {time.time() - t0:.0f} s on {s.prop.device}; fractions "
          f"{res['fractions']}; absorbers check R = {c['absorbers']['value']:.2e}; flux_absorbed "
          f"{c['flux_absorbed']['value']:.6f} vs {c['flux_absorbed']['ref']:.6f}", flush=True)

i6, P6, f6 = out[6.0]
i12, P12, f12 = out[12.0]
common = np.intersect1d(i6, i12)
a = P6[np.searchsorted(i6, common)]
b = P12[np.searchsorted(i12, common)]
print(f"same x samples: {len(common)}; max |P_6 - P_12| / peak = {np.max(np.abs(a - b)) / b.max():.3e}; "
      f"screen fraction {f6['screen']:.6f} vs {f12['screen']:.6f}; back {f6['back']:.6f} vs {f12['back']:.6f}")
