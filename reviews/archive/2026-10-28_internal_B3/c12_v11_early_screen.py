# B3 review, check 12: what v11's screen shows before the wave can reach it. In the browser (c09, the "narrow" preset
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# at wave time 2.45, the packet at the plate) the 3-D screen and the panel «Экран» show two bright stripes at the
# screen's edges x = +-screen_half. Here the same world is stepped to that time and the accumulated flux into the screen
# is printed in absolute terms (probability), where it sits, and how it compares with the final pattern; the same for the
# initial packet's tail inside the source-side absorber and at the window's periodic edge.
# Run (from engine/):
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c12_v11_early_screen.py > reviews/archive/2026-10-28_internal_B3/out/c12_v11_early_screen.txt
import math

import numpy as np
from harness import Harness

from v11_double_slit_2d.engine import apparatus as AP

V = "v11_double_slit_2d"
h = Harness(V, "narrow", {"n_bohm": 200, "n_tracks": 10}, seed=5)
s = h.sim
g, geo = s.g, s.geo
x, z = g.axes
print(f"grid {g.shape}, x in [{x[0]:.2f}, {x[-1]:.2f}], z in [{z[0]:.2f}, {z[-1]:.2f}], screen_half {geo.screen_half:.2f}, "
      f"packet centre z = {geo.z_src:.2f}, sigma_z = {geo.sz}; source-side layer z < {geo.z_min + AP.ABS_W:.2f}")
psi0 = s.prop.get(s.psi)
rho0 = g.density(psi0) * g.dV
print(f"initial packet: probability inside the source-side absorber {rho0[:, z < geo.z_min + AP.ABS_W].sum():.2e}; "
      f"|psi|^2 at the first z row / peak {g.density(psi0)[:, 0].max() / g.density(psi0).max():.2e}, "
      f"at the last z row {g.density(psi0)[:, -1].max() / g.density(psi0).max():.2e}")
for tau in (0.5, 1.0, 2.45, 4.0, 6.0):
    s_ = h.sim
    h.run_to(tau * s_.tunit)
    xs, P = s_._pattern(s_.flux)
    m = s_.on_screen
    k = np.argsort(np.abs(P))[::-1][:4]
    scr = h.of("screen")
    print(f"tau = {s_.tau:5.2f}: flux into the screen so far: sum {P.sum():+.2e}, max |P| {np.abs(P).max():.2e} at x = "
          + ", ".join(f"{xs[i]:+.2f} ({P[i]:+.1e})" for i in k)
          + f"; absorbed so far {s_.prop.absorbed().sum():.2e}; 'screen' messages sent {len(scr)}"
          + (f", the last one's peak {scr[-1]['peak']:.2e} (the view draws P / peak)" if scr else ""))
tu = s.tunit
while not h.sim.done and h.sim.tau < 400:
    h.run_to(h.sim.t + 2.0 * tu)
xs, P = h.sim._pattern(h.sim.flux)
print(f"end: tau = {h.sim.tau:.2f}, peak of the final pattern {P.max():.2e}")
