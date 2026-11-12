# Review B8-fdtd, script s07b: the amplification matrix of the Lorentz "Young" scheme exactly as printed by
# Bidegaray-Fesquet (arXiv:math/0506289, Sec. 4.3; U = (c B^{n-1/2}, E^n, P^n/eps0 eps_inf, k J^{n-1/2}/eps0 eps_inf),
# q = 4 lambda^2 sin^2(xi/2), delta = nu k / 2, omega = w1^2 k^2 / 2, alpha = eps_s/eps_inf - 1), against the engine's
# own amplification_radius for the same medium, and its spectral radius as a function of q.
import argparse
import math

import numpy as np

from lfphys.core.em import fdtd as F

argparse.ArgumentParser(description=__doc__).parse_args()


def G_young(q, lam_sign, delta, omega, alpha):
    # pick lambda and xi with 4 lambda^2 sin^2(xi/2) = q: xi = pi, lambda = sqrt(q)/2 (the eigenvalues depend on q only)
    xi = math.pi
    lam = math.sqrt(q) / 2
    e = np.exp(1j * xi)
    d1 = 1 + delta
    return np.array([
        [1, -lam * (e - 1), 0, 0],
        [-lam * (1 - 1 / e), ((1 - q) * d1 - 2 * omega * alpha) / d1, 2 * omega / d1, -(1 - delta) / d1],
        [0, 2 * omega * alpha / d1, (d1 - 2 * omega) / d1, (1 - delta) / d1],
        [0, 2 * omega * alpha / d1, -2 * omega / d1, (1 - delta) / d1]], complex)


dx = 0.05
for S in (0.5, 0.7, 0.9, 0.99):
    dt = S * dx
    for (de, f0, g) in ((1.25, 0.2, 0.1), (1.25, 0.2, 0.0), (1.25, 3.0, 0.1), (5.0, 3.0, 0.0)):
        w1 = 2 * math.pi * f0
        nu = 2 * math.pi * g
        delta, omega, alpha = nu * dt / 2, w1 * w1 * dt * dt / 2, de
        qs = np.linspace(0, 4 * S * S, 401)
        rb = max(np.max(np.abs(np.linalg.eigvals(G_young(q, 1, delta, omega, alpha)))) for q in qs)
        lam = qs / dt ** 2  # curl-curl eigenvalue lam with dt^2 lam = q
        re = F.amplification_radius(F.Medium(poles=[F.Lorentz(de, f0, g)]), dt, lam)
        print(f"S = {S:4.2f}  Lorentz de = {de}, f0 = {f0}, gamma = {g}: rho(Bidegaray's G) = {rb:.12f}   "
              f"rho(engine) = {re:.12f}   (omega = {omega:.4f}, bound 2/(2 eps_s' - 1) = {2 / (2 * (1 + alpha) - 1):.4f})")
