"""05: special relativity of lfphys.core.relativity: the sign convention of wigner_rotation_angle (only |theta| is
tested), and the conditioning of gamma near beta = 1. Usage: python3 05_relativity.py
"""
import argparse
import math

argparse.ArgumentParser(description=__doc__).parse_args()

import mpmath as mp
import numpy as np

from lfphys.core import relativity as R
from lfphys.core.constants import C

print("=== Wigner rotation: what the returned theta means geometrically ===")
u = np.array([0.5, 0.0]) * C     # F1 moves along +x in the lab
v = np.array([0.0, 0.5]) * C     # F2 moves along +y in F1  (u x v along +z)
th = R.wigner_rotation_angle(u, v, C)
lam = R.boost_matrix(v, C) @ R.boost_matrix(u, C)          # lab -> F2
inv = np.linalg.inv(lam)
w = inv[1:, 0] / inv[0, 0] * C
Rm = lam @ np.linalg.inv(R.boost_matrix(w, C))            # lab->F2 = Rm . B(w)
# F2's spatial x axis, expressed in the frame W reached by the single boost B(w): W-coords = Rm^-1 (0, 1, 0)
ex = np.linalg.solve(Rm, np.array([0.0, 1.0, 0.0]))
ang = math.atan2(ex[2], ex[1])
print(f"returned theta = {th:+.6f} rad;  F2 x-axis seen in W is at angle {ang:+.6f} rad "
      f"({'counter-clockwise' if ang > 0 else 'clockwise'})")
print("docstring: 'R a rotation of the spatial axes by theta (counter-clockwise positive)'")
print("=> the axes are rotated by -theta: the returned sign is opposite to the documented one" if
      abs(ang + th) < 1e-12 else "=> consistent")
# small-velocity limit: |theta| ~ |u x v|/(2c^2), sign
th_s = R.wigner_rotation_angle(np.array([1e-3, 0]) * C, np.array([0, 2e-3]) * C, C)
print(f"small velocities, u x v = +z: theta = {th_s:+.3e} (|u x v|/2c^2 = 1.0e-06)")

print("\n=== gamma(beta) = 1/sqrt(1 - beta^2) near beta = 1 (mpmath 40 digits as reference) ===")
mp.mp.dps = 40
for k in (6, 8, 10, 12, 14):
    b = 1.0 - 10.0 ** (-k)
    ref = 1 / mp.sqrt(1 - mp.mpf(b) ** 2)
    alt = 1.0 / math.sqrt((1.0 - b) * (1.0 + b))
    print(f"beta = 1 - 1e-{k}: gamma rel. err {float(abs(R.gamma(b) / ref - 1)):.1e}  "
          f"(with (1-b)(1+b): {float(abs(alt / ref - 1)):.1e})")
