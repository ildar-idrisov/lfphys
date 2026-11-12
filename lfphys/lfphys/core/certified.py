# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Certified evaluations in Arb ball arithmetic (python-flint): rigorous enclosures of the quantities the core
computes in float64, for references and tests. A ball [m +/- r] contains the exact value of the expression for the
given (binary64, converted exactly) inputs; where a root or an integral enters, Arb's rigorous integration and a
Newton refinement with a residual ball are used. Optional dependency: python-flint (pinned 0.9.0 in the Docker image).

Two kinds of certificate (relabelled after the review of 2026-10-23, E12):

Independent routes (a second way to the physics, not a re-evaluation of the float formula):
* light deflection in Schwarzschild: the defining integral, made regular by u = u0 (1 - s^2) and integrated
  rigorously, with the turning point u0 enclosed by an interval Newton step (its radius kept);
* Kerr: the radial potential R, R', R'' at the ISCO from the closed forms (all must contain 0: the closed forms are
  checked against the defining conditions);
* Hankel functions: J + iY from Arb's Bessel functions (the core uses scipy below 1e4 and an asymptotic series above);
* paraxial slit amplitude: the defining Fresnel integral, integrated rigorously (the core uses Fresnel functions);
* Klein-Nishina: the closed form and the rigorous integral of dsigma/dOmega.

Float-evaluation certificates (the same closed form as the float code, in ball arithmetic: they certify the float
evaluation, e.g. the cancellation of the weak-field periapsis advance, not the physics; the physics is checked by
other tests, e.g. the advance against the defining quadrature and the Dirac levels against the Sommerfeld expansion
and the measured 1S-2S frequency):
* periapsis advance (the elliptic integral K), Dirac levels (infinite nuclear mass), rectangular-barrier
  transmission.
"""

from __future__ import annotations

import math

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": "Строгие оценки (шаровая арифметика Arb)",
    "statement": "Гарантированные интервалы для величин ядра: смещение перицентра, отклонение света, условия ISCO "
                 "Керра, функции Ханкеля, амплитуды Френеля, уровни Дирака, сечение Клейна–Нишины, прохождение "
                 "барьера; независимыми путями (строгое интегрирование определений, эллиптические функции Arb).",
    "validity": "входы — двоичные числа (переводятся точно); точность задаётся битами (по умолчанию 256)",
    "basis": ["Johansson, IEEE Trans. Comput. 66, 1281 (2017) (Arb)", "python-flint 0.9.0"],
    "conflicts": [],
}


def _fl(prec: int):
    import flint
    flint.ctx.prec = prec
    return flint


def mid_rad(b) -> tuple[float, float]:
    """(midpoint, radius) of an arb (or the real part of an acb) as floats."""
    try:
        b = b.real
    except AttributeError:
        pass
    return float(b.mid()), float(b.rad())


def periapsis_advance(u_apo: float, u_peri: float, prec: int = 256):
    """4 K(m)/sqrt(2(u3 - u1)) - 2 pi with u3 = 1/2 - u1 - u2 (lfphys.core.gravity.orbits)."""
    f = _fl(prec)
    arb, acb = f.arb, f.acb
    u1, u2 = arb(u_apo), arb(u_peri)
    u3 = arb(1) / 2 - u1 - u2
    m = (u2 - u1) / (u3 - u1)
    K = acb(m).elliptic_k().real
    return 4 * K / (2 * (u3 - u1)).sqrt() - 2 * arb.pi()


def schwarzschild_deflection(b: float, rs: float, prec: int = 128):
    """Total deflection of light with impact parameter b: delta = 2 int_0^{u0} du / sqrt(1/b^2 - u^2 + rs u^3) - pi,
    u0 the turning point, enclosed rigorously (sign change of f and f' != 0 on the ball), so the result is a true
    enclosure for the given b. With f(u) = (u - u0) Q(u), Q = rs u^2 + (rs u0 - 1) u + (rs u0 - 1) u0 and u = u0 (1 - s^2)
    the integrand 2 sqrt(u0) / sqrt(-Q(u)) is regular on [0, 1]; integrated by acb.integral."""
    f = _fl(prec)
    arb, acb = f.arb, f.acb
    B, RS = arb(b), arb(rs)
    # u0: the smallest positive root of rs u^3 - u^2 + 1/b^2, Newton from the float root
    c = [rs, -1.0, 0.0, 1.0 / (b * b)]
    import numpy as np
    roots = np.roots(c)
    u0f = min(r.real for r in roots if abs(r.imag) < 1e-12 * abs(r) and r.real > 0)
    f_ = lambda u: RS * u**3 - u**2 + 1 / (B * B)  # noqa: E731
    df_ = lambda u: 3 * RS * u**2 - 2 * u  # noqa: E731
    u0 = arb(u0f)
    for _ in range(60):  # Newton on midpoints: a point close to the root
        u0 = arb((u0 - f_(u0) / df_(u0)).mid())
    # enclose the root: f changes sign across [m - r, m + r] and f' has no zero there (a unique root inside)
    m = u0.mid()
    r = 4 * abs(f_(arb(m)) / df_(arb(m))).upper() + arb(2) ** (-prec + 8) * abs(arb(m)).upper()
    lo, hi = arb(m) - r, arb(m) + r
    box = arb(m, r)
    if not ((f_(lo) * f_(hi)) < 0 and not df_(box).contains(0)):
        raise ArithmeticError("schwarzschild_deflection: the turning point could not be enclosed")
    u0 = box
    q1 = RS * u0 - 1

    def integrand(s, d):
        u = acb(u0) * (1 - s * s)
        Q = acb(RS) * u * u + acb(q1) * u + acb(q1 * u0)
        return 2 * acb(u0).sqrt() / (-Q).sqrt()
    I = acb.integral(integrand, 0, 1).real
    return 2 * I - arb.pi()


def kerr_isco_residuals(chi: float, prograde: bool = True, prec: int = 256):
    """(r_isco, R, R', R'') in Arb from the closed forms of lfphys.core.gravity.kerr: R, R' and R'' must contain 0."""
    f = _fl(prec)
    arb = f.arb
    x = arb(chi)
    s = 1 if prograde else -1
    third = arb(1) / 3
    z1 = 1 + (1 - x * x) ** third * ((1 + x) ** third + (1 - x) ** third)
    z2 = (3 * x * x + z1 * z1).sqrt()
    r = 3 + z2 - s * ((3 - z1) * (3 + z1 + 2 * z2)).sqrt()
    sr = r.sqrt()
    den = r ** (arb(3) / 4) * (r * sr - 3 * sr + s * 2 * x).sqrt()
    e = (r * sr - 2 * sr + s * x) / den
    l = s * (r * r - s * 2 * x * sr + x * x) / den
    A = e * (r * r + x * x) - x * l
    Bq = r * r + (l - x * e) ** 2
    D = r * r - 2 * r + x * x
    R0 = A * A - D * Bq
    R1 = 2 * A * (2 * e * r) - ((2 * r - 2) * Bq + D * 2 * r)
    R2 = 2 * (2 * e * r) ** 2 + 2 * A * 2 * e - (2 * Bq + 2 * (2 * r - 2) * 2 * r + 2 * D)
    return r, R0, R1, R2


def hankel1(nu: int, x: float, prec: int = 128):
    """H_nu^(1)(x) = J_nu(x) + i Y_nu(x), as an acb ball."""
    f = _fl(prec)
    acb = f.acb
    z = acb(x)
    return z.bessel_j(nu) + acb(0, 1) * z.bessel_y(nu)


def slit_amplitude(x: float, z: float, k: float, e1: float, e2: float, L1: float = math.inf, src: float = 0.0,
                   kappa: float = 0.0, prec: int = 128):
    """The defining paraxial integral int_{e1}^{e2} exp(i [alpha x'^2 + beta x' + gamma0]) dx' (the closed form of
    lfphys.theories.approx.paraxial), integrated rigorously; alpha = k/2 (1/z + 1/L1), beta = beta_src - k x/z + kappa,
    gamma0 = k x_s^2/(2 L1) + k x^2/(2 z)."""
    f = _fl(prec)
    arb, acb = f.arb, f.acb
    K, Z, X = arb(k), arb(z), arb(x)
    if math.isinf(L1):
        alpha = K / (2 * Z)
        beta = K * arb(math.sin(src)) - K * X / Z + arb(kappa)
        gamma0 = K * X * X / (2 * Z)
    else:
        L, S = arb(L1), arb(src)
        alpha = K / 2 * (1 / Z + 1 / L)
        beta = -K * S / L - K * X / Z + arb(kappa)
        gamma0 = K * S * S / (2 * L) + K * X * X / (2 * Z)
    i = acb(0, 1)
    return acb.integral(lambda t, d: (i * (acb(alpha) * t * t + acb(beta) * t + acb(gamma0))).exp(), e1, e2)


def dirac_level(n: int, j: float, alpha: float, mc2: float, Z: int = 1, prec: int = 256):
    f = _fl(prec)
    arb = f.arb
    za = Z * arb(alpha)
    jj = arb(j) + arb(1) / 2
    delta = jj - (jj * jj - za * za).sqrt()
    return arb(mc2) * (1 / (1 + (za / (n - delta)) ** 2).sqrt() - 1)


def klein_nishina_total(E: float, mc2: float, re: float, prec: int = 256):
    """(closed form, rigorous integral of dsigma/dOmega) as arb balls."""
    f = _fl(prec)
    arb, acb = f.arb, f.acb
    x = arb(E) / arb(mc2)
    R = arb(re)
    lg = (1 + 2 * x).log()
    closed = 2 * arb.pi() * R * R * ((1 + x) / x**3 * (2 * x * (1 + x) / (1 + 2 * x) - lg) + lg / (2 * x)
                                     - (1 + 3 * x) / (1 + 2 * x) ** 2)

    def ds(th, d):
        P = 1 / (1 + acb(x) * (1 - th.cos()))
        return 2 * acb(arb.pi()) * th.sin() * acb(R * R) / 2 * P * P * (P + 1 / P - th.sin() ** 2)
    integ = acb.integral(ds, 0, arb.pi()).real
    return closed, integ


def rectangular_barrier(E: float, V0: float, a: float, m: float = 1.0, hbar: float = 1.0, prec: int = 256):
    """T(E) of a rectangular barrier (closed form) in Arb."""
    f = _fl(prec)
    arb = f.arb
    E_, V, A, M, Hb = arb(E), arb(V0), arb(a), arb(m), arb(hbar)
    if E < V0:
        q = (2 * M * (V - E_)).sqrt() / Hb
        return 1 / (1 + V * V * (q * A).sinh() ** 2 / (4 * E_ * (V - E_)))
    q = (2 * M * (E_ - V)).sqrt() / Hb
    return 1 / (1 + V * V * (q * A).sin() ** 2 / (4 * E_ * (E_ - V)))
