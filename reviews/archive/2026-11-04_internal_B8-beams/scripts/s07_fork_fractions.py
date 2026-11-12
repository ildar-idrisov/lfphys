"""s07: the fork hologram's power fractions in v16 (viz.py:464-466, information checks) against references.

v16's reference is |c_m|^2 / sum_{|j|<=40} |c_j|^2. For the default binary hologram with period 2.5 lambda the orders
|m| >= 3 are evanescent (sin theta_3 = 3 lambda / Lambda = 1.2), so the light that propagates is in m = 0, +-1 only.
Measured here, on v16's own Fork object: the power in discs of growing radius around each order, the ratio P_0/P_1
(independent of the normalisation; the thin-mask value is c_0^2/c_1^2 = pi^2/4 = 2.467), the power just behind the mask
(z = 0) and at the end plane, and the reference with the propagating orders only.
"""
import math
import sys

import numpy as np

for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys"):
    sys.path.insert(0, p)
from lfphys.core.optics import beams_generation as GEN  # noqa: E402
from lfphys.theories.approx import beams_paraxial as PX  # noqa: E402
from v16_optical_vortices.engine import apparatus as A  # noqa: E402

lam, w0, period, l = 1.0, 4.0, 2.5, 1
k = 2 * math.pi / lam
for kind in ("binary", "amplitude"):
    # v16's z_end (viz.py:_init_fork)
    zr = PX.rayleigh(k, w0)
    s = lam / period
    tan = s / math.sqrt(1 - s * s)
    q = tan * tan - (4.5 * w0 / zr) ** 2
    z_end = 1.25 * 4.5 * w0 / math.sqrt(q)
    f = A.Fork(l, w0, lam, period, kind, z_end)
    out, U = f.orders(z_end)
    X, Y = np.meshgrid(f.x, f.x, indexing="ij")
    tot = float(np.sum(np.abs(U) ** 2))
    tot0 = float(np.sum(np.abs(f.U0) ** 2))
    gauss = float(np.sum(np.exp(-2 * (X * X + Y * Y) / w0 ** 2)))
    c = {m: GEN.fork_order_coefficient(kind, m) for m in range(-40, 41)}
    prop = [m for m in c if abs(m * lam / period) < 1]
    v16_ref = {m: c[m] ** 2 / sum(v ** 2 for v in c.values()) for m in (-1, 0, 1)}
    prop_ref = {m: c[m] ** 2 / sum(c[j] ** 2 for j in prop) for m in (-1, 0, 1)}
    w_z = float(PX.params(z_end, k, w0)[0])
    print(f"--- {kind}: z_end = {z_end:.1f}, w(z) = {w_z:.2f}, grid dx = {f.dx:.3f}, propagating orders {sorted(prop)}")
    print(f"  power behind the mask / incident Gaussian = {tot0 / gauss:.4f} (thin mask: sum_j c_j^2 = "
          f"{sum(v ** 2 for v in c.values()):.4f});  in the window at z_end / incident = {tot / gauss:.4f} (propagating "
          f"orders: {sum(c[j] ** 2 for j in prop):.4f})")
    print(f"  v16 reference {[round(v16_ref[m], 4) for m in (-1, 0, 1)]};  propagating-only reference "
          f"{[round(prop_ref[m], 4) for m in (-1, 0, 1)]};  v16 measured (2.5 w) {[round(o[3], 4) for o in out]}")
    for rad in (1.3, 2.5, 4.0, 6.0):
        P = []
        for m in (-1, 0, 1):
            xm = GEN.order_position(m, period, k, z_end)
            P.append(float(np.sum(np.abs(U[(X - xm) ** 2 + Y ** 2 <= (rad * w_z) ** 2]) ** 2)) / gauss)
        print(f"  disc {rad:3.1f} w(z): P_-1, P_0, P_+1 / incident = {P[0]:.4f}, {P[1]:.4f}, {P[2]:.4f};  P_0/P_+1 = {P[1] / P[2]:.3f}"
              f"  (thin mask c0^2/c1^2 = {c[0] ** 2 / c[1] ** 2:.3f})")
