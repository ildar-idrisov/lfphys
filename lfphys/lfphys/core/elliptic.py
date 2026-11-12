# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Elliptic integrals and Jacobi elliptic functions for array code on the CPU (NumPy) or the GPU (CuPy).

Conventions: the parameter m (= k^2), as in DLMF chapter 19 and 22 and in Gralla & Lupsasca (2020):
F(phi|m) = int_0^phi dt / sqrt(1 - m sin^2 t), K(m) = F(pi/2|m), Pi(n|m) = int_0^{pi/2} dt / ((1 - n sin^2 t)
sqrt(1 - m sin^2 t)).

* ``rf(x, y, z, xp)``: Carlson's R_F by the duplication method (DLMF 19.36(i)): duplications until every
  |Z_j| = |1 - x_j/A| <= 1/100, then the polynomial of degree 7 of DLMF Eq. 19.36.1. The truncation error is of order
  |Z|^8 ~ 1e-16 (Carlson 1995, Eq. 2.2 with (3r)^(-1/8), DLMF note under 19.36.1); every step is elementwise, so the
  same code runs on NumPy and CuPy arrays.
* ``ellipf(phi, m, xp)`` = sin(phi) R_F(cos^2 phi, 1 - m sin^2 phi, 1) for |phi| <= pi/2 (DLMF 19.25.5), the second
  argument evaluated as cos^2 phi + (1 - m) sin^2 phi (no cancellation as m -> 1, phi -> pi/2), extended to
  every real phi by F(phi + j pi|m) = F(phi|m) + 2 j K(m) (DLMF 19.2.10); valid for m < 1 and for m >= 1 where
  m sin^2 phi < 1. ``ellipk(m, xp)`` = R_F(0, 1 - m, 1) (DLMF 19.25.1), any m < 1.
* ``ellipj(u, m, xp)``: sn, cn, dn. For 0 <= m <= 1 the arithmetic-geometric mean (Abramowitz & Stegun 16.4), run
  to convergence (SciPy's and CuPy's Cephes ``ellipj`` stops after eight iterations and uses a first-order expansion
  in 1 - m above m = 1 - 1e-10, whose error grows with u: 1.8e-7 in sn at m = 1 - 1e-11, u = 20, measured against
  mpmath; the photon rings live exactly there, k -> 1); for m < 0 the imaginary-modulus transformation
  DLMF 22.17.5-8: with mu = -m/(1 - m) and v = u sqrt(1 - m), sn(u|m) = sn(v|mu) / (sqrt(1 - m) dn(v|mu)),
  cn(u|m) = cn(v|mu)/dn(v|mu), dn(u|m) = 1/dn(v|mu).
* ``ellippi(n, m)``: complete Pi(n|m) = K(m) + (n/3) R_J(0, 1 - m, 1, 1 - n) (DLMF 19.25.2; CPU, SciPy's ``elliprj``).

The tests compare every function with mpmath at 30 digits and SciPy's own ``elliprf``/``ellipkinc``.
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": "Эллиптические интегралы и функции Якоби (CPU и GPU)",
    "statement": "R_F Карлсона удвоением (DLMF 19.36), F(φ|m) и K(m) для любого m < 1, sn, cn, dn при любом "
                 "вещественном m (m < 0 — преобразованием DLMF 22.17), полный Π(n|m) через R_J; одни и те же "
                 "поэлементные формулы на NumPy и CuPy.",
    "validity": "математика; относительная ошибка ~1e-15 (тесты против mpmath)",
    "basis": ["NIST DLMF §19.2, §19.25, §19.36, §22.17", "Carlson, Numer. Algorithms 10, 13 (1995)"],
    "conflicts": [],
}

_RF_STOP = 0.01  # |Z_j| at which the degree-7 polynomial is accurate to ~1e-16 (|Z|^8)


def rf(x, y, z, xp=np):
    """Carlson's R_F(x, y, z) for x, y, z >= 0 (at most one zero), elementwise (DLMF 19.36(i))."""
    x = xp.asarray(x, dtype=xp.float64)
    y = xp.asarray(y, dtype=xp.float64)
    z = xp.asarray(z, dtype=xp.float64)
    x, y, z = xp.broadcast_arrays(x, y, z)
    a0 = (x + y + z) / 3.0
    a = a0
    dx, dy = a0 - x, a0 - y  # Z_x = dx / (4^n A_n), Z_y = dy / (4^n A_n): no cancellation (Carlson 1995)
    q = xp.maximum(xp.maximum(xp.abs(dx), xp.abs(dy)), xp.abs(a0 - z))
    f = xp.ones_like(a0)
    # every element stops on its own criterion (frozen afterwards), so a value does not depend on the other
    # elements of the batch: a chunked computation is bit-identical to a whole one
    for _ in range(60):
        act = q * f > _RF_STOP * xp.abs(a)
        if not bool(xp.any(act)):
            break
        sx, sy, sz = xp.sqrt(x), xp.sqrt(y), xp.sqrt(z)
        lam = sx * sy + sy * sz + sz * sx
        x = xp.where(act, (x + lam) * 0.25, x)
        y = xp.where(act, (y + lam) * 0.25, y)
        z = xp.where(act, (z + lam) * 0.25, z)
        a = xp.where(act, (a + lam) * 0.25, a)
        f = xp.where(act, f * 0.25, f)
    X = dx * f / a
    Y = dy * f / a
    Z = -X - Y
    e2 = X * Y - Z * Z
    e3 = X * Y * Z
    poly = (1.0 - e2 / 10.0 + e3 / 14.0 + e2 * e2 / 24.0 - 3.0 * e2 * e3 / 44.0 - 5.0 * e2 ** 3 / 208.0
            + 3.0 * e3 * e3 / 104.0 + e2 * e2 * e3 / 16.0)
    return poly / xp.sqrt(a)


def ellipk(m, xp=np):
    """K(m) for m < 1."""
    m = xp.asarray(m, dtype=xp.float64)
    return rf(xp.zeros_like(m), 1.0 - m, xp.ones_like(m), xp)


def ellipf(phi, m, xp=np):
    """F(phi|m) for any real phi (m < 1; or m >= 1 with m sin^2 phi < 1 and |phi| <= pi/2)."""
    phi = xp.asarray(phi, dtype=xp.float64)
    m = xp.asarray(m, dtype=xp.float64)
    phi, m = xp.broadcast_arrays(phi, m)
    j = xp.rint(phi / math.pi)
    p = phi - j * math.pi  # |p| <= pi/2
    s = xp.sin(p)
    c = xp.cos(p)
    # 1 - m sin^2 phi written as cos^2 phi + (1 - m) sin^2 phi: no cancellation as m -> 1 and phi -> pi/2 (review
    # B5-K11: the plain form lost 2.7e-6 relative at m = 1 - 1e-13, phi = pi/2 - 3e-9)
    f = s * rf(c * c, c * c + (1.0 - m) * s * s, xp.ones_like(p), xp)
    if bool(xp.any(j != 0)):
        safe = xp.where(m < 1.0, m, 0.0)
        f = f + 2.0 * j * xp.where(j != 0, ellipk(safe, xp), 0.0)
    return f


def _ellipj01(u, m, xp):
    """sn, cn, dn for 0 <= m <= 1 by the arithmetic-geometric mean (Abramowitz & Stegun 16.4; DLMF 22.20(ii)):
    a_0 = 1, b_0 = sqrt(1 - m), c_0 = sqrt(m); a_{n+1} = (a_n + b_n)/2, b_{n+1} = sqrt(a_n b_n),
    c_{n+1} = (a_n - b_n)/2 until c_N/a_N < eps; phi_N = 2^N a_N u, phi_{n-1} = (phi_n + arcsin((c_n/a_n) sin phi_n))/2;
    sn = sin phi_0, cn = cos phi_0, dn = cos phi_0 / cos(phi_1 - phi_0). Unlike Cephes (SciPy, CuPy) there is no cap
    of eight iterations and no first-order expansion near m = 1, whose error grows with u (measured 1.8e-7 in sn at
    m = 1 - 1e-11, u = 20). u is first reduced modulo 4K(m)."""
    one = xp.ones_like(u)
    m = xp.clip(m, 0.0, 1.0)
    at1 = m >= 1.0
    mm = xp.where(at1, 0.5, m)  # m = 1 exactly: sn = tanh, cn = dn = sech (filled in below)
    k4 = 4.0 * ellipk(mm, xp)
    u_red = u - k4 * xp.rint(u / k4)
    a = one
    b = xp.sqrt(1.0 - mm)
    ratios = []
    act = xp.ones(u.shape, dtype=bool)
    # each element stops when its own c_n/a_n < eps; afterwards its ratios are exactly 0 and a, b are frozen, so
    # phi_N = 2^N a u and the halvings are exact: the value does not depend on the other elements of the batch
    for _ in range(64):
        c = (a - b) * 0.5
        a_new, b_new = (a + b) * 0.5, xp.sqrt(a * b)
        rat = xp.where(act, c / a_new, 0.0)
        a = xp.where(act, a_new, a)
        b = xp.where(act, b_new, b)
        ratios.append(rat)
        act = act & (xp.abs(rat) > 2.2e-16)
        if not bool(xp.any(act)):
            break
    phi = u_red * a * (2.0 ** len(ratios))
    prev = phi
    for r in reversed(ratios):
        prev = phi
        phi = 0.5 * (phi + xp.arcsin(xp.clip(r * xp.sin(phi), -1.0, 1.0)))
    sn = xp.sin(phi)
    cn = xp.cos(phi)
    dn = cn / xp.cos(prev - phi)
    if len(ratios) == 0:  # pragma: no cover - m = 0 everywhere
        dn = one
    # dn = sqrt(1 - m sn^2) where the quotient is 0/0 (cn ~ 0)
    dn = xp.where(xp.abs(cn) < 1e-8, xp.sqrt(xp.maximum(cn * cn + (1.0 - mm) * sn * sn, 0.0)), dn)
    if bool(xp.any(at1)):
        sech = 1.0 / xp.cosh(u)
        sn = xp.where(at1, xp.tanh(u), sn)
        cn = xp.where(at1, sech, cn)
        dn = xp.where(at1, sech, dn)
    return sn, cn, dn


def ellipj(u, m, xp=np):
    """Jacobi sn(u|m), cn(u|m), dn(u|m) for any real u and real m <= 1."""
    u = xp.asarray(u, dtype=xp.float64)
    m = xp.asarray(m, dtype=xp.float64)
    u, m = xp.broadcast_arrays(u, m)
    neg = m < 0.0
    if not bool(xp.any(neg)):
        return _ellipj01(u, xp.minimum(m, 1.0), xp)
    s1m = xp.sqrt(1.0 - xp.where(neg, m, 0.0))
    mu = xp.where(neg, -m / (1.0 - xp.where(neg, m, 0.0)), xp.minimum(m, 1.0))
    v = xp.where(neg, u * s1m, u)
    sn, cn, dn = _ellipj01(v, mu, xp)
    sn = xp.where(neg, sn / (s1m * dn), sn)
    cn = xp.where(neg, cn / dn, cn)
    dn = xp.where(neg, 1.0 / dn, dn)
    return sn, cn, dn


def ellippi(n, m):
    """Complete Pi(n|m) for n < 1, m < 1 (CPU): K(m) + (n/3) R_J(0, 1 - m, 1, 1 - n) (DLMF 19.25.2)."""
    from scipy.special import elliprf, elliprj
    n = np.asarray(n, float)
    m = np.asarray(m, float)
    return elliprf(0.0, 1.0 - m, 1.0) + n / 3.0 * elliprj(0.0, 1.0 - m, 1.0, 1.0 - n)


def ellipe(m):
    """Complete E(m) for m < 1 (CPU): 2 R_G(0, 1 - m, 1) (DLMF 19.25.1)."""
    from scipy.special import elliprg
    return 2.0 * elliprg(0.0, 1.0 - np.asarray(m, float), 1.0)
