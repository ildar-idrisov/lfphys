# B3 review, check 8: the Terrell rotation of a cube, measured in the tracer's image against its closed form (an
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# independent reference: the engine's tests check Penrose's circle for spheres, emission times and D, not the shape
# of a box). A cube of side L moving along +x at beta, far away (distance R = 2000 L) and seen when its retarded
# direction is perpendicular to its velocity: in the far-field limit its image is that of the cube at rest turned by
# arcsin(beta) — the face towards the observer of apparent width L / gamma and the trailing face of width beta L, the
# leading face hidden (Terrell 1959; Weisskopf, Physics Today 13 (9), 24 (1960)). Measured on the row of directions
# through the cube's middle, sampled every 2e-9 rad; corrections O(L / R) = 5e-4.
# Run (from engine/):
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys light-funnel-viz \
#     python3 reviews/archive/2026-10-28_internal_B3/c08_raytrace_terrell.py > reviews/archive/2026-10-28_internal_B3/out/c08_raytrace_terrell.txt
import math

import numpy as np

from lfphys.core import backend as B
from lfphys.core import raytrace as RT

B.configure({"kernels": {RT.KERNEL: {"device": "cpu"}}})
L, R = 1.0, 2000.0
temps = (9500.0, 3600.0, 5000.0, 5000.0, 2600.0, 6500.0)  # +x leading, -x trailing, +-y, +z far, -z facing
for beta in (0.0, 0.5, 0.9, 0.99):
    g = 1.0 / math.sqrt(1 - beta * beta)
    # the centre's light reaches the observer (origin, t = 0) from (0, 0, R): emitted at t = -R, so c0 = (beta R, 0, R)
    cube = RT.Box((beta * R, 0.0, R), (L / 2, L / 2, L / 2), (beta, 0.0, 0.0), temps=temps, alt=1.0, cells=1)
    th = 2.0 * L / R
    n = 2000001
    a = np.linspace(-th, th, n)
    d = np.stack([np.sin(a), np.zeros(n), np.cos(a)], -1)
    r = RT.trace_directions(RT.Scene([cube]), RT.Observer(0.0, (0.0, 0.0, 0.0)), d)
    da = a[1] - a[0]
    widths = {T: float(np.sum(r["T_rest"] == T)) * da * R for T in set(temps)}
    front, trail, lead = widths.get(6500.0, 0.0), widths.get(3600.0, 0.0), widths.get(9500.0, 0.0)
    print(f"beta = {beta:4.2f}: facing face {front:.6f} L (closed form 1/gamma = {1 / g:.6f}), trailing face "
          f"{trail:.6f} L (beta = {beta:.6f}), leading face {lead:.6f} L (0); total {front + trail:.6f} "
          f"(beta + 1/gamma = {beta + 1 / g:.6f})")
