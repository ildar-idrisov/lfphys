# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Exact scalar wave propagation in free space (2-D): the outgoing Green's function (i/4) H0(1)(kr) and the
Rayleigh-Sommerfeld kernel of the first kind for a field given on a line,

    U(x, z) = (i k z / 2) int U(x', 0) H1(1)(k R) / R dx',   R = sqrt((x - x')^2 + z^2),

the exact solution of the Helmholtz equation in z > 0 for given values on z = 0 (every Cartesian component of the
field in a homogeneous medium satisfies it). Approximations enter only through the boundary values (e.g. Kirchhoff,
lfphys.theories.approx.kirchhoff).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Exact propagation of a scalar wave (2-D)"),
    "statement": T("The Green's function (i/4)H₀⁽¹⁾(kr) and the Rayleigh–Sommerfeld kernel of the first kind: an "
                   "exact solution of the Helmholtz equation for given values of the field on a line."),
    "validity": T("homogeneous medium, the field given on a line; Hankel asymptotics with a relative error < 1e-10 at "
                  "kR > 1e4"),
    "basis": [T("Born & Wolf, Principles of Optics, ch. 8.11"), "Abramowitz & Stegun 9.2.5–9.2.10"],
    "conflicts": [],
}


def hankel1(nu: int, x):
    """Hankel H_nu^(1)(x), nu = 0 or 1, for positive real x (vectorised)."""
    x = np.asarray(x, float)
    out = np.empty(x.shape, complex)
    small = x < 1e4
    if np.any(small):
        out[small] = special.hankel1(nu, x[small])
    big = ~small
    if np.any(big):
        xb = x[big]
        mu = 4.0 * nu * nu
        t1 = (mu - 1) / (8 * xb)
        t2 = (mu - 1) * (mu - 9) / (2 * (8 * xb) ** 2)
        t3 = (mu - 1) * (mu - 9) * (mu - 25) / (6 * (8 * xb) ** 3)
        series = 1 + 1j * t1 - t2 - 1j * t3
        # exp(i x) with libm's exact argument reduction, times the constant phase: forming x - (2nu+1)pi/4 first
        # would lose the digits of x below its ulp (relative error 7e-9 at x = 1e8, found by the Arb test)
        out[big] = (np.sqrt(2 / (math.pi * xb)) * np.exp(1j * xb) * complex(math.cos((2 * nu + 1) * math.pi / 4),
                                                                             -math.sin((2 * nu + 1) * math.pi / 4))
                    * series)
    return out




def rs_kernel(k: float, z: float, R):
    """(i k z / 2) H1(1)(k R) / R."""
    return (0.5j * k * z) * hankel1(1, k * np.asarray(R, float)) / R
