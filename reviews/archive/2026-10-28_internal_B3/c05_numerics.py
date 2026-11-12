# B3 review, check 5: small numerical claims of schrodinger_nd and v11, recomputed.
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
#  (a) the screen's current by the centred difference of order 16 (v11 FLUX_ORDER): the exact relative error of the
#      difference for a plane wave e^{ikz} against the comment's (8!)^2/17! (k dz)^16 ~ 1e-5 at k dz = pi/3 (lambda/6);
#      and for order 8 (the comment: "lost 2e-3");
#  (b) the absorbing layers of v11 (W = 2 E0 (s/6 lambda)^2): reflection R and leak T from layer_reflection over the
#      normal wavenumbers kn / k0 from 0.05 to 1.2, against the range the run's `absorbers` check covers;
#  (c) the Lagrange stencils of `sample`: max |omega(t)| and max |omega'(t)| for t within half a step of the middle node.
# Run (from engine/):
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c05_numerics.py > reviews/archive/2026-10-28_internal_B3/out/c05_numerics.txt
import math

import numpy as np

from lfphys.core.quantum import schrodinger_nd as S

print("(a) centred first-derivative differences on a plane wave e^{ikz}: relative error |D_h e^{ikz} / (ik e^{ikz}) - 1|")
for order in (8, 16):
    c = S.fd_weights(order)
    h = order // 2
    for frac in (1 / 5, 1 / 6, 1 / 8):
        for kk in (1.0, 1.2, 1.5):  # k / k0, with k0 dz = 2 pi frac
            kd = 2 * math.pi * frac * kk
            D = sum(c[j] * np.exp(1j * kd * (j - h)) for j in range(order + 1)) / (1j * kd)
            lead = math.factorial(h) ** 2 / math.factorial(order + 1) * kd**order
            print(f"  order {order:2d}  dz = lambda/{1 / frac:.0f}  k = {kk:.1f} k0  k dz = {kd:.3f}:  exact error "
                  f"{abs(D - 1):.2e}   leading term {lead:.2e}")

print("\n(b) v11 absorbing layer W = 2 E0 (s / 6 lambda)^2 (lambda = 1, hbar = m = 1, E0 = 2 pi^2):")
k0 = 2 * math.pi
E0 = 0.5 * k0 * k0
kn = k0 * np.array([0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.67 * 0.9, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2])
R, T = S.layer_reflection(kn, 6.0, 2.0 * E0, 1.0, slices=4000)
for a, r, t in zip(kn / k0, R, T):
    print(f"  kn / k0 = {a:.3f}:  R = {r:.2e}  leak T = {t:.2e}")
print("  the run's `absorbers` check covers kn in [0.9, 1.1] k0 and [0.9, 1.1] k0 cos(theta_screen) only")

print("\n(c) the Lagrange stencil of degree 8 about the nearest node (t in [3.5, 4.5]):")
t = np.linspace(3.5, 4.5, 200001)
w = np.ones_like(t)
for j in range(9):
    w = w * (t - j)
dw = np.gradient(w, t)
print(f"  max |omega| = {np.abs(w).max():.4f} (doc: 193.8), max |omega'| = {np.abs(dw).max():.4f} at t = "
      f"{t[np.abs(dw).argmax()]:.4f} (doc: 576)")
