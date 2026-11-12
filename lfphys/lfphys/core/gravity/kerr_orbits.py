# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Generic bound timelike geodesics of Kerr: eccentric, inclined orbits in Mino time (plan P7).

Units G = c = M = 1 and mu = 1 (constants per unit mass), spin chi = a in [0, 1). An orbit is labelled by the
semi-latus rectum p, the eccentricity e (periapsis p/(1 + e), apoapsis p/(1 - e)) and x = cos(theta_inc), the
inclination with x > 0 prograde and x < 0 retrograde (theta_inc = pi/2 - theta_min for a prograde orbit; theta_min
is the turning point of the polar motion, cos^2 theta_min = 1 - x^2), as in Schmidt 2002 and Fujita & Hikida 2009.

* Constants (Schmidt 2002, CQG 19, 2743, App. B, Eqs. B.4-B.22, checked on the rendered pages): with z^2 = 1 - x^2
  (Schmidt's z_- = cos theta_-), f(r) = r^4 + a^2 [r (r + 2) + z^2 Delta], g = 2 a r, h = r (r - 2) +
  z^2 Delta/(1 - z^2), d = (r^2 + a^2 z^2) Delta at the periapsis and the apoapsis (or f, g, h, d and their
  derivatives at r = p when e = 0); kappa, epsilon, rho, eta, sigma the 2 x 2 determinants (B.19-B.21);
  E^2 = [kappa rho + 2 epsilon sigma -+ 2 sqrt(sigma (sigma epsilon^2 + rho epsilon kappa - eta kappa^2))]/
  (rho^2 + 4 eta sigma), the lower energy prograde (x > 0); L from eliminating the L^2 terms of (B.17):
  rho E^2 - 2 sigma E L - kappa = 0; Q = z^2 [a^2 (1 - E^2) + L^2/(1 - z^2)] (B.4). Polar orbits (x = 0, L = 0):
  R(r) = 0 at both turning points is linear in (E^2, Q) and solved directly. a = 0: the Schwarzschild closed forms
  E^2 = ((p - 2)^2 - 4 e^2)/(p (p - 3 - e^2)), L^2 = p^2/(p - 3 - e^2), L_z = x L, Q = (1 - x^2) L^2.
* Motion in Mino time lambda (Fujita & Hikida 2009, CQG 26, 135002, Eqs. 10-15, 26, and their cos theta solution):
  R(r) = (1 - E^2)(r1 - r)(r - r2)(r - r3)(r - r4), r1 = p/(1 - e), r2 = p/(1 + e), r3 + r4 = 2/(1 - E^2) - (r1 + r2),
  r3 r4 = a^2 Q/((1 - E^2) r1 r2); Theta(z = cos^2 theta) = beta (z_- - z)(z_+ - z), beta = a^2 (1 - E^2);
  r(lambda) = [r3 (r1 - r2) sn^2 - r2 (r1 - r3)]/[(r1 - r2) sn^2 - (r1 - r3)], sn = sn(K_r q_r/pi | k_r^2),
  cos theta(lambda) = sqrt(z_-) sn(2 K_th (q_th + pi/2)/pi | k_th^2), q_r = Upsilon_r lambda + q_r0,
  q_th = Upsilon_th lambda + q_th0 (q_r0 = 0: periapsis; q_th0 = 0: theta_min, as in KerrGeoPy),
  k_r^2 = (r1 - r2)(r3 - r4)/((r1 - r3)(r2 - r4)), k_th^2 = z_-/z_+;
  Upsilon_r = pi sqrt((1 - E^2)(r1 - r3)(r2 - r4))/(2 K(k_r^2)), Upsilon_th = pi sqrt(beta z_+)/(2 K(k_th^2)).
  The turning points are passed exactly (sn^2 oscillates); the constants are parameters.
* Gamma = <dt/dlambda> and Upsilon_phi = <dphi/dlambda> (Fujita & Hikida 2009 Eq. 21, written with |L_z|-free
  theta-averages: <L/sin^2 theta> = L Pi(z_-|k_th^2)/K(k_th^2), <cos^2 theta> = z_+ (K - E)/K); the second route
  averages dt/dlambda and dphi/dlambda over the two phases by the trapezoid rule (exponentially convergent for
  these analytic periodic functions; FH Sec. 3.4 compares the same way). Omega_i = Upsilon_i/Gamma.
* t(lambda), phi(lambda): integrals of the smooth functions dt/dlambda = T_r(r) + T_th(theta) + a L and
  dphi/dlambda = Phi_r(r) + Phi_th(theta) - a E (FH Eqs. 1-2) along the closed form, by Gauss-Legendre panels;
  ``KerrOrbit.advance`` steps the state (lambda, t, phi) - plain floats, saved and restored exactly.
"""

from __future__ import annotations

import math

import numpy as np

from .. import elliptic as EL
from . import kerr

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Общие орбиты Керра: эксцентричные и наклонные (время Мино)",
    "statement": "Связанные времениподобные геодезические Керра по (p, e, x = cos ι): E, L_z, Q (Шмидт 2002), "
                 "корни потенциалов, r(λ) и θ(λ) в функциях Якоби (Фудзита–Хикида 2009; точки поворота — точно), "
                 "основные частоты Υ_r, Υ_θ, Υ_φ, Γ и Ω_r, Ω_θ, Ω_φ, t(λ) и φ(λ) квадратурой; пошаговое "
                 "продвижение орбиты с сохранением состояния.",
    "validity": "пробная частица в вакуумном решении ОТО, 0 ≤ a < M; устойчивые связанные орбиты (p выше "
                "сепаратрисы), 0 ≤ e < 1; без излучения (геодезическое движение)",
    "basis": ["Schmidt, Class. Quantum Grav. 19, 2743 (2002), App. B",
              "Fujita & Hikida, Class. Quantum Grav. 26, 135002 (2009)",
              "Drasco & Hughes, Phys. Rev. D 69, 044015 (2004)"],
    "conflicts": [],
}


def _chk(chi, p, e, x):
    if not 0.0 <= chi < 1.0:
        raise ValueError("spin chi must be in [0, 1)")
    if not 0.0 <= e < 1.0:
        raise ValueError("eccentricity e must be in [0, 1)")
    if not -1.0 <= x <= 1.0:
        raise ValueError("x = cos(inclination) must be in [-1, 1]")
    if p <= 0.0:
        raise ValueError("p > 0")


def _fghd(r, a, z2):
    dl = r * r - 2.0 * r + a * a
    f = r ** 4 + a * a * (r * (r + 2.0) + z2 * dl)
    g = 2.0 * a * r
    h = r * (r - 2.0) + z2 / (1.0 - z2) * dl
    d = (r * r + a * a * z2) * dl
    return f, g, h, d


def _fghd_prime(r, a, z2):
    f = 4.0 * r ** 3 + 2.0 * a * a * ((1.0 + z2) * r + (1.0 - z2))
    g = 2.0 * a
    h = 2.0 * (r - 1.0) / (1.0 - z2)
    d = 2.0 * (2.0 * r - 3.0) * r * r + 2.0 * a * a * ((1.0 + z2) * r - z2)
    return f, g, h, d


def schmidt_constants(chi, p, e, x):
    """(E, L_z, Q) of the bound orbit (p, e, x) by the closed form of Schmidt 2002 App. B (polar and Schwarzschild
    cases closed separately). Plain ``math`` on scalars (the tests bound its rounding by a running error analysis).
    The elimination cancels large terms (the 2 x 2 determinants) for nearly polar orbits and at large p: L and Q
    lose up to ~1e-9 relative at p = 30, x = 0.05 and 13 % at p = 1e6 (measured 2026-10-29); ``constants`` polishes
    them by Newton steps on the defining equations."""
    _chk(chi, p, e, x)
    a = chi
    if a == 0.0:
        den = p - 3.0 - e * e
        if den <= 0.0:
            raise ValueError("not a bound orbit (p <= 3 + e^2)")
        E = math.sqrt(((p - 2.0) ** 2 - 4.0 * e * e) / (p * den))
        L = p / math.sqrt(den)
        return E, x * L, (1.0 - x * x) * L * L
    if x == 0.0:  # polar: L = 0, R(r) = E^2 [(r^2+a^2)^2 - a^2 Delta] - Delta Q - Delta r^2 = 0 (linear in E^2, Q)
        if e > 0.0:
            ra, rb = p / (1.0 + e), p / (1.0 - e)
            dla, dlb = ra * ra - 2.0 * ra + a * a, rb * rb - 2.0 * rb + a * a
            c1a, c1b = (ra * ra + a * a) ** 2 - a * a * dla, (rb * rb + a * a) ** 2 - a * a * dlb
            # [c1a, -dla; c1b, -dlb] (E^2, Q) = (dla ra^2, dlb rb^2)
            det = -c1a * dlb + c1b * dla
            E2 = (-(dla * ra * ra) * dlb + (dlb * rb * rb) * dla) / det
            Q = (c1a * dlb * rb * rb - c1b * dla * ra * ra) / det
        else:  # R = R' = 0 at r = p
            r = p
            dl, dlp = r * r - 2.0 * r + a * a, 2.0 * r - 2.0
            c1, c1p = (r * r + a * a) ** 2 - a * a * dl, 4.0 * r * (r * r + a * a) - a * a * dlp
            # c1 E^2 - dl Q = dl r^2 ; c1p E^2 - dlp Q = dlp r^2 + 2 r dl
            rhs1, rhs2 = dl * r * r, dlp * r * r + 2.0 * r * dl
            det = -c1 * dlp + c1p * dl
            E2 = (-rhs1 * dlp + rhs2 * dl) / det
            Q = (c1 * rhs2 - c1p * rhs1) / det
        return math.sqrt(E2), 0.0, Q
    z2 = 1.0 - x * x
    if e > 0.0:
        f1, g1, h1, d1 = _fghd(p / (1.0 + e), a, z2)
        f2, g2, h2, d2 = _fghd(p / (1.0 - e), a, z2)
    else:
        f1, g1, h1, d1 = _fghd(p, a, z2)
        f2, g2, h2, d2 = _fghd_prime(p, a, z2)
    kappa = d1 * h2 - h1 * d2
    eps = d1 * g2 - g1 * d2
    rho = f1 * h2 - h1 * f2
    eta = f1 * g2 - g1 * f2
    sigma = g1 * h2 - h1 * g2
    s = 1.0 if x > 0.0 else -1.0  # prograde: the lower energy
    root = math.sqrt(sigma * (sigma * eps * eps + rho * eps * kappa - eta * kappa * kappa))
    E2 = (kappa * rho + 2.0 * eps * sigma - s * 2.0 * root) / (rho * rho + 4.0 * eta * sigma)
    E = math.sqrt(E2)
    L = (rho * E2 - kappa) / (2.0 * sigma * E)
    Q = z2 * (a * a * (1.0 - E2) + L * L / (1.0 - z2))
    return E, L, Q


def _residual(chi, p, e, x, E, L, Q):
    """The defining equations F = (R(r_p), R(r_a) or R'(p), theta equation) and their Jacobian d F/d(E, L, Q)."""
    a = chi

    def RdR(r):
        dl = r * r - 2.0 * r + a * a
        P = E * (r * r + a * a) - a * L
        W = L - a * E
        R = P * P - dl * (r * r + W * W + Q)
        J = (2.0 * P * (r * r + a * a) + 2.0 * a * dl * W, -2.0 * a * P - 2.0 * dl * W, -dl)
        S = P * P + abs(dl) * (r * r + W * W + abs(Q))  # the size of the cancelling terms
        return R, J, S

    def dRdr(r):
        dl, dlp = r * r - 2.0 * r + a * a, 2.0 * r - 2.0
        P = E * (r * r + a * a) - a * L
        W = L - a * E
        Rp = 2.0 * P * 2.0 * r * E - dlp * (r * r + W * W + Q) - 2.0 * r * dl
        J = (2.0 * (r * r + a * a) * 2.0 * r * E + 4.0 * r * P + 2.0 * a * dlp * W, -4.0 * a * r * E - 2.0 * dlp * W,
             -dlp)
        S = abs(4.0 * P * r * E) + abs(dlp) * (r * r + W * W + abs(Q)) + abs(2.0 * r * dl)
        return Rp, J, S
    if e > 0.0:
        f1, j1, s1 = RdR(p / (1.0 + e))
        f2, j2, s2 = RdR(p / (1.0 - e))
    else:
        f1, j1, s1 = RdR(p)
        f2, j2, s2 = dRdr(p)
    if x == 0.0:
        f3, j3, s3 = L, (0.0, 1.0, 0.0), abs(L)
    else:
        z2 = 1.0 - x * x
        f3 = Q - z2 * (a * a * (1.0 - E * E) + L * L / (x * x))
        j3 = (2.0 * z2 * a * a * E, -2.0 * z2 * L / (x * x), 1.0)
        s3 = abs(Q) + z2 * (a * a * (1.0 + E * E) + L * L / (x * x))
    return (f1, f2, f3), (j1, j2, j3), (s1, s2, s3)


def _solve3(J, F):
    """J d = F by Cramer's rule (plain arithmetic)."""
    (a, b, c), (d, e, f), (g, h, i) = J
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    x0 = (F[0] * (e * i - f * h) - b * (F[1] * i - f * F[2]) + c * (F[1] * h - e * F[2])) / det
    x1 = (a * (F[1] * i - f * F[2]) - F[0] * (d * i - f * g) + c * (d * F[2] - F[1] * g)) / det
    x2 = (a * (e * F[2] - F[1] * h) - b * (d * F[2] - F[1] * g) + F[0] * (d * h - e * g)) / det
    return x0, x1, x2


def constants(chi, p, e, x, polish=True):
    """(E, L_z, Q) of the bound orbit (p, e, x): Schmidt's closed form, then (``polish``) Newton steps on the
    defining equations R(r_p) = R(r_a) = 0 (R = R' = 0 at e = 0) and Theta(theta_min) = 0 until the step is below
    the round-off: the result is then as accurate as the equations are conditioned (tests: against 40-digit
    solutions, with the bound |J^-1| (round-off of F))."""
    E, L, Q = schmidt_constants(chi, p, e, x)
    if not polish or chi == 0.0:
        return E, L, Q
    for _ in range(12):
        F, J, _ = _residual(chi, p, e, x, E, L, Q)
        dE, dL, dQ = _solve3(J, F)
        E, L, Q = E - dE, L - dL, Q - dQ
        if abs(dE) <= 2.0 ** -52 * abs(E) and abs(dL) <= 2.0 ** -52 * max(abs(L), 1e-300) and \
                abs(dQ) <= 2.0 ** -52 * max(abs(Q), 1e-300):
            break
    if x == 0.0:
        L = 0.0
    if x in (1.0, -1.0):
        Q = 0.0
    return E, L, Q


def radial_potential(r, E, L, Q, chi, mu2=1.0):
    a = chi
    dl = r * r - 2.0 * r + a * a
    return (E * (r * r + a * a) - a * L) ** 2 - dl * (mu2 * r * r + (L - a * E) ** 2 + Q)


def radial_roots(chi, p, e, E, Q):
    """r1 (apoapsis) >= r2 (periapsis) > r3 >= r4 (Fujita & Hikida Eq. 11)."""
    a = chi
    r1, r2 = p / (1.0 - e), p / (1.0 + e)
    one_m = 1.0 - E * E
    s = 2.0 / one_m - (r1 + r2)
    prod = a * a * Q / (one_m * r1 * r2)
    r3 = 0.5 * (s + math.sqrt(max(s * s - 4.0 * prod, 0.0)))
    r4 = prod / r3 if r3 != 0.0 else 0.0
    return r1, r2, r3, r4


def polar_roots(chi, E, L, Q):
    """(z_-, beta z_+) with beta = a^2 (1 - E^2): roots of Q - (Q + beta + L^2) z + beta z^2 = 0 in z = cos^2 theta;
    beta z_+ stays finite as a -> 0."""
    a = chi
    beta = a * a * (1.0 - E * E)
    b = Q + beta + L * L
    disc = math.sqrt(max(b * b - 4.0 * beta * Q, 0.0))
    bzp = 0.5 * (b + disc)  # beta z_+
    zm = Q / bzp if bzp > 0.0 else 0.0  # z_- z_+ = Q/beta -> z_- = Q/(beta z_+)
    return zm, bzp


class KerrOrbit:
    """A bound geodesic (p, e, x) of the Kerr black hole with spin chi, with initial Mino phases (q_r0: 0 at
    periapsis; q_th0: 0 at theta_min) and t0, phi0 at lambda = 0. ``r(lam)``, ``theta(lam)`` closed form;
    ``frequencies()``; ``t_phi(lam)``; step-wise ``advance(dlam)`` of the state ``(lam, t, phi)``."""

    def __init__(self, chi, p, e, x, q_r0=0.0, q_th0=0.0, t0=0.0, phi0=0.0, consts=None):
        _chk(chi, p, e, x)
        self.chi, self.a, self.p, self.e, self.x = float(chi), float(chi), float(p), float(e), float(x)
        self.E, self.L, self.Q = constants(chi, p, e, x) if consts is None else (float(c) for c in consts)
        a, E, L, Q = self.a, self.E, self.L, self.Q
        self.r1, self.r2, self.r3, self.r4 = radial_roots(chi, p, e, E, Q)
        if not self.r3 < self.r2:
            raise ValueError("not a stable bound orbit (r3 >= periapsis: at or inside the separatrix)")
        self.zm, self.bzp = polar_roots(chi, E, L, Q)
        self.polar = (L == 0.0 and Q > 0.0)  # passes over the poles (z_- = 1)
        r1, r2, r3, r4 = self.r1, self.r2, self.r3, self.r4
        self.mr = (r1 - r2) * (r3 - r4) / ((r1 - r3) * (r2 - r4))
        self.Kr = float(EL.ellipk(self.mr))
        self.ups_r = math.pi * math.sqrt((1.0 - E * E) * (r1 - r3) * (r2 - r4)) / (2.0 * self.Kr)
        beta = a * a * (1.0 - E * E)
        self.mth = (self.zm * beta / self.bzp) if self.bzp > 0.0 else 0.0  # z_-/z_+
        self.Kth = float(EL.ellipk(self.mth))
        self.ups_th = math.pi * math.sqrt(self.bzp) / (2.0 * self.Kth)
        self.q_r0, self.q_th0 = float(q_r0), float(q_th0)
        self.lam, self.t, self.phi = 0.0, float(t0), float(phi0)

    @classmethod
    def from_constants(cls, chi, p, e, E, L, Q, **kw):
        """The orbit with turning points p/(1 -+ e) and the given constants (e.g. perturbed ones; the x label is
        recomputed from z_- = cos^2 theta_min)."""
        zm, _ = polar_roots(chi, E, L, Q)
        x = math.copysign(math.sqrt(max(0.0, 1.0 - zm)), L) if L != 0.0 else 0.0
        return cls(chi, p, e, x, consts=(E, L, Q), **kw)

    # closed forms
    def r(self, lam):
        q = self.ups_r * np.asarray(lam, float) + self.q_r0
        sn, _, _ = EL.ellipj(self.Kr * q / math.pi, self.mr)
        s2 = sn * sn
        r1, r2, r3 = self.r1, self.r2, self.r3
        return (r3 * (r1 - r2) * s2 - r2 * (r1 - r3)) / ((r1 - r2) * s2 - (r1 - r3))

    def cos_theta(self, lam):
        q = self.ups_th * np.asarray(lam, float) + self.q_th0
        sn, _, _ = EL.ellipj(2.0 * self.Kth * (q + 0.5 * math.pi) / math.pi, self.mth)
        return math.sqrt(self.zm) * sn

    def theta(self, lam):
        """Boyer-Lindquist theta in [0, pi]; for a polar orbit (L = 0) the orbit passes over the poles and theta is
        continued through them (atan2(cn, sn): it leaves [0, pi], equivalent to theta -> -theta, phi -> phi + pi,
        as a Boyer-Lindquist integrator does), so that (theta, phi) stays continuous."""
        if not self.polar:
            return np.arccos(np.clip(self.cos_theta(lam), -1.0, 1.0))
        q = self.ups_th * np.asarray(lam, float) + self.q_th0
        sn, cn, _ = EL.ellipj(2.0 * self.Kth * (q + 0.5 * math.pi) / math.pi, self.mth)
        return np.arctan2(cn, math.sqrt(self.zm) * sn)

    # the separated rates (Fujita & Hikida Eq. 1-2)
    def dt_dlam(self, r, c):
        a, E, L = self.a, self.E, self.L
        dl = r * r - 2.0 * r + a * a
        P = E * (r * r + a * a) - a * L
        return (r * r + a * a) / dl * P - a * a * E * (1.0 - c * c) + a * L

    def dphi_dlam(self, r, c):
        a, E, L = self.a, self.E, self.L
        dl = r * r - 2.0 * r + a * a
        P = E * (r * r + a * a) - a * L
        return a / dl * P + (L / (1.0 - c * c) if L != 0.0 else 0.0) - a * E

    def frequencies(self, method="closed"):
        """Mino frequencies Upsilon_r, Upsilon_theta, Upsilon_phi, Gamma and the coordinate-time ones
        Omega_i = Upsilon_i/Gamma. ``method``: "closed" (Fujita & Hikida Eq. 21 with complete Pi) or
        "average" (trapezoid rule over the two Mino phases, N = 128 points each)."""
        a, E, L = self.a, self.E, self.L
        if method == "average":
            def avg(f, phase_to_lam):
                """Trapezoid mean over one period, the points doubled until two results agree to 2 ulp (spectral
                convergence for these analytic periodic functions; nearly polar orbits need many points)."""
                prev = None
                for k in range(6, 18):
                    n = 2 ** k
                    v = float(np.mean(f(phase_to_lam(2.0 * math.pi * np.arange(n) / n))))
                    if prev is not None and abs(v - prev) <= 4.4e-16 * abs(v):
                        return v
                    prev = v
                return v
            to_r = lambda q: (q - self.q_r0) / self.ups_r  # noqa: E731
            to_t = lambda q: (q - self.q_th0) / self.ups_th  # noqa: E731

            def dlr(lm):
                rr = self.r(lm)
                return rr, rr * rr - 2.0 * rr + a * a, E * (rr * rr + a * a) - a * L
            Tr = avg(lambda lm: (lambda rr, dl, P: (rr * rr + a * a) / dl * P)(*dlr(lm)), to_r)
            Pr = avg(lambda lm: (lambda rr, dl, P: a / dl * P)(*dlr(lm)), to_r)
            Tth = avg(lambda lm: -a * a * E * (1.0 - self.cos_theta(lm) ** 2), to_t)
            Pth = avg(lambda lm: L / (1.0 - self.cos_theta(lm) ** 2), to_t) if L != 0.0 else 0.0
            gam = Tr + Tth + a * L
            ups_phi = Pr + Pth - a * E
        else:
            r1, r2, r3, r4 = self.r1, self.r2, self.r3, self.r4
            K, mr = self.Kr, self.mr
            Er = float(EL.ellipe(mr))
            hr = (r1 - r2) / (r1 - r3)
            Pih = float(EL.ellippi(hr, mr))
            rp = 1.0 + math.sqrt(1.0 - a * a)
            rm = 1.0 - math.sqrt(1.0 - a * a)
            # <T_r> (Fujita & Hikida Eq. 21, the radial braces, divided by K: 2 Upsilon_r/(pi sqrt(...)) = 1/K)
            brace = (0.5 * E * ((r3 * (r1 + r2 + r3) - r1 * r2) * K + (r2 - r3) * (r1 + r2 + r3 + r4) * Pih
                                + (r1 - r3) * (r2 - r4) * Er)
                     + 2.0 * E * (r3 * K + (r2 - r3) * Pih))
            # the horizon terms (also at a = 0, where r_- = 0 and T_r keeps 8 E/(r - 2))
            terms_t, terms_p = [], []
            for rpm in (rp, rm):
                h = (r1 - r2) * (r3 - rpm) / ((r1 - r3) * (r2 - rpm))
                J = K - (r2 - r3) / (r2 - rpm) * float(EL.ellippi(h, mr))
                terms_t.append(((4.0 * E - a * L) * rpm - 2.0 * a * a * E) / (r3 - rpm) * J)
                terms_p.append((2.0 * E * rpm - a * L) / (r3 - rpm) * J)
            brace += 2.0 / (rp - rm) * (terms_t[0] - terms_t[1])
            phi_r = a / (rp - rm) * (terms_p[0] - terms_p[1]) / K
            Kth, mth = self.Kth, self.mth
            if a > 0.0:
                Eth = float(EL.ellipe(mth))
                zp_a2 = self.bzp / (1.0 - E * E)  # a^2 z_+
                cos2_avg_a2 = zp_a2 * (Kth - Eth) / Kth  # a^2 <cos^2 theta>
            else:
                cos2_avg_a2 = 0.0
            gam = 4.0 * E + cos2_avg_a2 * E + brace / K
            ups_phi = (L * float(EL.ellippi(self.zm, mth)) / Kth if L != 0.0 else 0.0) + phi_r
        out = {"Upsilon_r": self.ups_r, "Upsilon_theta": self.ups_th, "Upsilon_phi": float(ups_phi),
               "Gamma": float(gam)}
        out.update({"Omega_r": self.ups_r / out["Gamma"], "Omega_theta": self.ups_th / out["Gamma"],
                    "Omega_phi": out["Upsilon_phi"] / out["Gamma"]})
        return out

    # positions in coordinate time and azimuth
    def _integrate(self, lam0, lam1, nodes=24):
        """int_{lam0}^{lam1} (dt/dlam, dphi/dlam) by composite Gauss-Legendre (``nodes`` per panel), the panels
        halved until two results agree to 1e-14 relative (the integrands are analytic in lambda; nearly polar orbits
        have a sharp peak of L/sin^2 theta that needs short panels)."""
        if lam1 == lam0:
            return 0.0, 0.0
        per = 2.0 * math.pi / max(self.ups_r, self.ups_th)
        n = max(1, int(math.ceil(abs(lam1 - lam0) / (per / 8.0))))
        x, w = np.polynomial.legendre.leggauss(nodes)

        def quad(n):
            edges = np.linspace(lam0, lam1, n + 1)
            mid = 0.5 * (edges[:-1] + edges[1:])
            half = 0.5 * (edges[1:] - edges[:-1])
            lq = (mid[:, None] + half[:, None] * x[None, :]).ravel()
            rr = self.r(lq)
            cc = self.cos_theta(lq)
            ww = (half[:, None] * w[None, :]).ravel()
            return float(np.sum(self.dt_dlam(rr, cc) * ww)), float(np.sum(self.dphi_dlam(rr, cc) * ww))
        prev = quad(n)
        for _ in range(12):
            n *= 2
            cur = quad(n)
            if abs(cur[0] - prev[0]) <= 1e-14 * max(abs(cur[0]), 1.0) and \
                    abs(cur[1] - prev[1]) <= 1e-14 * max(abs(cur[1]), 1.0):
                return cur
            prev = cur
        return cur

    def advance(self, dlam):
        """Advance the state by dlam in Mino time; returns (lam, t, r, theta, phi) after the step."""
        dt, dphi = self._integrate(self.lam, self.lam + dlam)
        self.lam += dlam
        self.t += dt
        self.phi += dphi
        return self.lam, self.t, float(self.r(self.lam)), float(self.theta(self.lam)), self.phi

    def trajectory(self, lams):
        """(t, r, theta, phi) at the increasing Mino times ``lams`` (from the current state)."""
        lams = np.asarray(lams, float)
        t = np.empty_like(lams)
        ph = np.empty_like(lams)
        lt, tt, pp = self.lam, self.t, self.phi
        for i, l in enumerate(lams):
            dt, dp = self._integrate(lt, l)
            tt, pp, lt = tt + dt, pp + dp, l
            t[i], ph[i] = tt, pp
        return t, self.r(lams), self.theta(lams), ph

    def momentum(self, lam):
        """Covariant momentum (p_t, p_r, p_theta, p_phi) at lambda: dr/dlambda = Delta p_r, dtheta/dlambda = p_theta
        (central differences of the closed forms, h = 1e-6: relative error ~1e-10)."""
        a = self.a
        r = float(self.r(lam))
        h = 1e-6
        drdl = (float(self.r(lam + h)) - float(self.r(lam - h))) / (2 * h)
        dthdl = (float(self.theta(lam + h)) - float(self.theta(lam - h))) / (2 * h)
        dl = r * r - 2.0 * r + a * a
        return np.array([-self.E, drdl / dl, dthdl, self.L])

    def state(self) -> dict:
        return {"chi": self.chi, "p": self.p, "e": self.e, "x": self.x, "q_r0": self.q_r0, "q_th0": self.q_th0,
                "lam": self.lam, "t": self.t, "phi": self.phi, "E": self.E, "L": self.L, "Q": self.Q}

    @classmethod
    def from_state(cls, st: dict) -> "KerrOrbit":
        o = cls(st["chi"], st["p"], st["e"], st["x"], st["q_r0"], st["q_th0"], consts=(st["E"], st["L"], st["Q"]))
        o.lam, o.t, o.phi = float(st["lam"]), float(st["t"]), float(st["phi"])
        return o
