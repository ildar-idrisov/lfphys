"""P7 review, check 10b: the Newton iteration of state_from_invariants traced for eps = 0.01, j = 0.5 (nu = 0.25),
re-implemented here line by line from pn_binary.py (same F, same complex-step Jacobian), printing each iterate.

Run: python3 s10b_newton_trace.py
"""
import argparse
import math

import numpy as np

from lfphys.core.gravity import pn_binary as P

argparse.ArgumentParser(description=__doc__).parse_args()
eps, j, nu, order = 0.01, 0.5, 0.25, 2
e = math.sqrt(max(1.0 - j, 0.0))
y = np.array([(1.0 - e) / eps, math.sqrt(eps * (1.0 + e) / (1.0 - e))])


def F(z):
    x = np.array([z[0], 0.0, 0.0])
    v = np.array([0.0, z[1], 0.0])
    E = P.energy(x, v, nu, order)
    J = P.angular_momentum(x, v, nu, order)[2]
    return np.array([-2.0 * E / eps - 1.0, -2.0 * E * J * J / j - 1.0])


for it in range(12):
    f0 = F(y)
    Jm = np.empty((2, 2))
    for k in range(2):
        hk = 1e-30 * abs(y[k])
        yc = y.astype(complex)
        yc[k] += 1j * hk
        Jm[:, k] = F(yc).imag / hk
    dy = np.linalg.solve(Jm, -f0.real)
    print(f"it {it}: r_p={y[0]:.6e} v_p={y[1]:.6e} F={f0.real} det(J)={np.linalg.det(Jm):.3e} step={dy}")
    y = y + dy
