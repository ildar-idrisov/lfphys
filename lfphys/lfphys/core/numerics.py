# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Numerical tools shared by the engine (no physics): bracketed root finding on monotone functions, composite
Gauss-Legendre panels, Hankel asymptotics."""

from __future__ import annotations

import math

import numpy as np
from scipy import optimize

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": T("Numerical tools"),
    "statement": T("Root finding of a monotonic function with bracket doubling (brentq), composite Gauss–Legendre "
                   "quadratures."),
    "validity": T("mathematics; the accuracy is stated in each function"),
    "basis": [],
    "conflicts": [],
}

class Lost(Exception):
    pass


def moving_root(dt_of, t0, t_from, wl):
    """Arrival at a moving receiver: the root of F(t) = t0 + dt(x_R(t)) - t for t > max(t0, t_from).
    F is strictly decreasing for a subluminal receiver (review 2026-10-22 R1: a fixed-point iteration cannot
    converge for receivers faster than ~0.6c); a doubling bracket and brentq always converge. Returns t or None
    (the front has already passed the start, or the image is lost on the way)."""
    lo = max(t0, t_from)

    def F(t):
        d = dt_of(wl.pos(t))
        if d is None:
            raise Lost
        return t0 + d - t

    try:
        f_lo = F(lo)
        if f_lo <= 0.0:
            return None  # strict: an arrival at exactly the start time was the past (R2)
        step = f_lo
        hi = lo + step
        for _ in range(400):
            f_hi = F(hi)
            if f_hi <= 0.0:
                break
            lo = hi
            step *= 2.0
            hi = lo + step
        else:
            return None
        return optimize.brentq(F, lo, hi, xtol=1e-15 * max(1.0, abs(hi)), rtol=1e-15, maxiter=500)
    except Lost:
        return None




def gl_panels(a: float, b: float, panels: int, order: int = 32):
    """Nodes and weights of a composite Gauss-Legendre rule: ``panels`` equal panels of ``order`` nodes on [a, b]."""
    t, w = np.polynomial.legendre.leggauss(order)
    edges = np.linspace(a, b, panels + 1)
    h = 0.5 * (edges[1:] - edges[:-1])
    mid = 0.5 * (edges[1:] + edges[:-1])
    return (mid[:, None] + h[:, None] * t[None, :]).ravel(), (h[:, None] * w[None, :]).ravel()
