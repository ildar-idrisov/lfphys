# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Fields and radiation of moving point charges (plan P1, batch B8), SI units.

**Liénard–Wiechert fields.** A charge q on a worldline r(t') with velocity v = c beta and acceleration a = c beta_dot
produces at the field point x and time t (Fitzpatrick, Classical Electromagnetism, eqs. 12.293–12.297; Jackson,
Classical Electrodynamics, 3rd ed., eqs. 14.13–14.14):

    E = q/(4 pi eps0) [ (n - beta) / (gamma^2 kappa^3 R^2) ]_ret                    (velocity, generalised Coulomb)
      + q/(4 pi eps0 c) [ n x ((n - beta) x beta_dot) / (kappa^3 R) ]_ret          (acceleration, radiation)
    B = n x E / c,     kappa = 1 - n . beta,   R n = x - r(t_ret),

evaluated at the retarded time t_ret, the root of c (t - t') = |x - r(t')|. The potentials are
phi = q / (4 pi eps0 kappa R), A = phi beta / c (Lorenz gauge). Gaussian units: q^2/(4 pi eps0) -> e^2 and B = n x E.

**The retarded time** is solved for the delay tau = t - t': g(tau) = c tau - |x - r(t - tau)| has g' = c - n . v > 0
for a subluminal worldline, so the root is unique. g is a difference of numbers of size c tau, and its rounding error
is bounded by B = 4 eps (c |tau| + |x| + |r|) + eps |v| |t'| (eps = 2.2e-16, twice the unit roundoff: twice the
errors of t' = t - tau, of r(t'), of x - r, of its norm and of the difference; the last term because t' is itself
rounded, so the worldline is evaluated at a time known to ulp(t')). The root is bracketed (g(0) <= 0, the upper end
doubled, inside the worldline's domain, until g > B: a sign change below B is rounding, not a root) and found by
Newton steps kept inside the bracket (bisection when a step leaves it), until |g| <= B or the bracket is at ulp(t),
then one more Newton step. The delay is thus resolved to 2 B / g' (the returned bound) and no better: a point far
from the origin (|x|, |r| >> c tau) keeps the absolute accuracy B, and near a horizon (g' -> 0) the uncertainty grows;
``retarded_time(..., full=True)`` returns the bound with the time. Where g stays within B and a doubling of the
bracket cannot lift it out (beyond the horizon of hyperbolic motion, or within B of it; a charge coming at the point
so close to c that 1 - n . beta is lost: from gamma ~ 2e7) no retarded time is returned: the points are
refused (listed) or, with on_fail="nan", get NaN. Hyperbolic motion has the closed form (below), used by default. A worldline is a callable
object (``Worldline``: position, velocity, acceleration, a time domain), built from formulas (``FunctionWorldline``;
closed forms ``uniform``, ``circular``, ``harmonic``, ``hyperbolic``) or from samples (``SampledWorldline``: quintic
Hermite pieces when r, v, a are sampled, a quintic spline through the positions otherwise; ``interpolation_error``
measures the error by rebuilding the interpolant from every third sample and comparing at the dropped samples, scaled
to the full sampling by the order of the method). A ``FunctionWorldline`` given positions only differentiates them
numerically with a step it must be given (the step, or the motion's time scale T: steps eps^(1/5) T for v and
eps^(1/6) T for a); its error estimate includes the rounding, and ``fields`` refuses such a worldline where the
estimated derivative errors would change the field by more than its ``rtol`` (1e-6).

**Hyperbolic motion, closed-form retarded time** (mine): with a = c^2/g, Z' = (x - r0) . e + a, the transverse
distance rho, B = c (t - t0) and the rapidity eta of the retarded point (c t' = a sinh eta, Z'(t') = a cosh eta), the
light-cone condition is 2 Z' a cosh eta - 2 B a sinh eta = rho^2 + Z'^2 - B^2 + a^2 =: D, a quadratic in u = e^eta whose
retarded root is u = 2 a (Z' + B) / (D + sqrt(D^2 - 4 a^2 (Z'^2 - B^2))) (D^2 - 4 a^2 (Z'^2 - B^2) = (rho^2 + Z'^2 -
B^2 - a^2)^2 + 4 a^2 rho^2 >= 0); it exists if and only if Z' + B > 0 (the field point lies before the past horizon
Z' + c (t - t0) = 0 of the motion, i.e. in the causal future of the worldline). Rounding: Z' + B is known to
2 eps (|Z| + a + |B|); a point within that of the horizon is refused. The result is polished by Newton steps on g where
g exceeds its rounding (a weakly accelerated charge, a >> rho: the closed form loses digits there).

**Radiated power.** Larmor (non-relativistic): P = q^2 a^2 / (6 pi eps0 c^3). Liénard: P = q^2 gamma^6 / (6 pi eps0 c)
[beta_dot^2 - (beta x beta_dot)^2] (Fitzpatrick 12.309, 12.327). Angular distribution (Fitzpatrick 12.337–12.338;
Jackson 14.38):

    dP/dOmega = q^2 / (16 pi^2 eps0 c) |n x ((n - beta) x beta_dot)|^2 / kappa^5     per unit RETARDED time (emitter),
    dP/dOmega = q^2 / (16 pi^2 eps0 c) |n x ((n - beta) x beta_dot)|^2 / kappa^6     per unit OBSERVER time,

the first integrating over the sphere to Liénard's P (energy lost by the charge per unit of its time t'), the second
being R^2 S . n at the observer (dt/dt' = kappa). Heaviside's field of a uniformly moving charge (from its PRESENT
position R_p, angle psi between R_p and v): E = q/(4 pi eps0) (1 - beta^2) R_p / (R_p^3 (1 - beta^2 sin^2 psi)^(3/2)),
B = v x E / c^2 (Fitzpatrick 12.299), a closed-form reference.

**Synchrotron radiation** (ultrarelativistic circular motion, radius rho; X-ray Data Booklet §2.1; PDG "Electromagnetic
relations" 7.12–7.14; the gamma >> 1 limit of Schott's harmonics below, which are exact at any beta < 1: the harmonic
power P_m / omega0 approaches it as 1/gamma^2, tested): critical
frequency omega_c = (3/2) gamma^3 c / rho; F(x) = x int_x^inf K_{5/3}(t) dt, G(x) =
x K_{2/3}(x); the spectrum dP/domega = (P / omega_c) S(omega / omega_c), S = 9 sqrt(3) / (8 pi) F, int S = 1, and its
two polarisation components (sigma: in the orbit plane, pi: perpendicular to it) (9 sqrt(3) / (16 pi)) (F +- G);
the angular-spectral distribution (the K_{2/3} and K_{1/3} terms of the booklet's eq. 1, as power per unit frequency
per unit vertical angle, averaged over the orbit). F is computed from int_x^inf K_nu(t) dt = int_0^inf
exp(-x cosh u) cosh(nu u) / cosh u du by composite Gauss–Legendre (relative error < 1e-13, tested against mpmath).
Non-relativistic to relativistic cyclotron harmonics (Schott, Electromagnetic Radiation, 1912, eq. 128 and the
power R_j): dP_m/dOmega = q^2 omega0^2 m^2 / (8 pi^2 eps0 c) [cot^2 theta J_m^2(m beta sin theta) + beta^2
J_m'^2(m beta sin theta)], P_m = q^2 c beta / (2 pi eps0 rho^2) [m beta^2 J'_{2m}(2 m beta) - m^2 (1 - beta^2)
int_0^beta J_{2m}(2 m x) dx] (Gaussian in the source: q^2/(4 pi eps0) -> e^2), exact for any beta < 1; their sum is
Liénard's power.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy import constants as sc
from scipy import special

from ...i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Fields and radiation of moving point charges"),
    "statement": T("The Liénard–Wiechert fields (the velocity and radiation parts) and potentials of a charge on a "
                   "given worldline with the exact solution for the retarded time; the Larmor and Liénard power, the "
                   "angular distribution (per unit of retarded and per unit of observed time); the field of a "
                   "uniformly moving charge (Heaviside); synchrotron radiation: the critical frequency, F(x), G(x), "
                   "the spectrum and the two polarisations, the angular and spectral distribution; the harmonics of "
                   "cyclotron radiation (Schott)."),
    "validity": T("classical electrodynamics of a point charge in vacuum, a subluminal worldline; the radiation "
                  "reaction on the motion is not included (the worldline is given); the synchrotron spectrum through "
                  "F(x) is the ultrarelativistic limit (γ ≫ 1), Schott's harmonics are exact at any β < 1. Double "
                  "precision: β is passed as a number, and 1 − β², 1 − n·β lose digits, so the relative error of the "
                  "fields and of Liénard's power is of order 1e-16·γ² (measured: ~4e-8 at γ = 1e4, ~1e-4 at γ = 1e6, "
                  "~1e-2 at γ = 1e7); the retarded time is resolved to the round-off of g = cτ − R, "
                  "~4ε(cτ + |x| + |r|) + ε|v||t′| (far from the origin and near the horizon the accuracy drops; the "
                  "estimate is returned)"),
    "basis": [T("Fitzpatrick, Classical Electromagnetism (lectures, eqs. 12.203–12.358)"),
              T("Jackson, Classical Electrodynamics, 3rd ed., ch. 14"),
              "X-ray Data Booklet (LBNL), §2.1 (K.-J. Kim)",
              T("PDG, Electromagnetic relations, eqs. 7.10–7.19"),
              T("Schott, Electromagnetic Radiation (Cambridge, 1912), eqs. 128–130")],
    "conflicts": [T("this module itself: synchrotron_F, synchrotron_G, synchrotron_spectrum, "
                    "synchrotron_angular_spectrum are the limit γ ≫ 1 (a continuous spectrum) of Schott's harmonics "
                    "harmonic_power / harmonic_angular_power, which are exact at any β < 1; they differ by order 1/γ² "
                    "(measured: 4e-3 at γ = 10 and 1e-3 at γ = 20 at ω_c); both paths are given for comparison")],
}

C = sc.c
EPS0 = sc.epsilon_0
MU0 = sc.mu_0
K_E = 1.0 / (4.0 * math.pi * EPS0)  # Coulomb constant
EPS = float(np.finfo(float).eps)  # 2.2e-16

_GL_X, _GL_W = np.polynomial.legendre.leggauss(24)


# --- worldlines -------------------------------------------------------------------------------------------------------
class Worldline:
    """A subluminal worldline: ``state(t)`` returns positions, velocities and accelerations, each of shape t.shape +
    (3,), for times inside ``domain`` = (t_min, t_max)."""
    domain = (-math.inf, math.inf)

    def state(self, t):
        raise NotImplementedError

    def position(self, t):
        return self.state(t)[0]


class FunctionWorldline(Worldline):
    """From callables r(t), v(t), a(t) (vectorised over an array t, returning t.shape + (3,)). v and a may be None:
    they are then taken by central differences with Richardson extrapolation (error O(h^4)), and a step is required
    (review B8 C2: a fixed default step of 1e-3 s was 100 % wrong for nanosecond motion, silently): either ``h``
    (seconds, used for v and a) or ``timescale`` T, the time over which the motion changes (e.g. 1/omega of an orbit),
    giving the steps that balance the truncation error h^4 |r^(5)| / 30 (v), h^4 |r^(6)| / 90 (a) against the rounding
    1.5 e_r / h (v), 5.7 e_r / h^2 (a) for |r^(n)| ~ |r| / T^n: h_v = (45 eps / 4)^(1/5) T ~ 1.2e-3 T, h_a = (256
    eps)^(1/6) T ~ 6e-3 T. ``derivative_errors`` estimates both errors per time (the truncation from the difference to
    the step 2h, the rounding from e_r = 2 eps (|r| + |v| |t|): the time t +- h is itself rounded); ``fields`` refuses
    the worldline where they would change the field by more than ``rtol``."""

    def __init__(self, r: Callable, v: Callable | None = None, a: Callable | None = None,
                 domain=(-math.inf, math.inf), h: float | None = None, timescale: float | None = None,
                 rtol: float = 1e-6):
        self.r, self.v, self.a = r, v, a
        self.domain = tuple(domain)
        if (v is None or a is None) and h is None and timescale is None:
            raise ValueError("FunctionWorldline: v or a is taken by finite differences — give the step h (s) or the "
                             "time scale of the motion (timescale, s)")
        if h is not None and not h > 0 or timescale is not None and not timescale > 0:
            raise ValueError("FunctionWorldline: h > 0, timescale > 0")
        self.h, self.timescale, self.rtol = h, timescale, float(rtol)

    @property
    def numerical(self) -> bool:
        """True when v or a is taken by finite differences."""
        return self.v is None or self.a is None

    def _steps(self):
        if self.h is not None:
            return self.h, self.h
        T = self.timescale
        return (45 * EPS / 4) ** 0.2 * T, (256 * EPS) ** (1 / 6) * T

    def state(self, t):
        t = np.asarray(t, float)
        r = np.asarray(self.r(t), float)
        if self.numerical:
            hv, ha = self._steps()
        v = np.asarray(self.v(t), float) if self.v is not None else self._diff_v(t, hv)
        a = np.asarray(self.a(t), float) if self.a is not None else self._diff_a(t, ha)
        return r, v, a

    def _diff_v(self, t, h):
        f = self.r
        d1 = (f(t + h) - f(t - h)) / (2 * h)
        d2 = (f(t + 2 * h) - f(t - 2 * h)) / (4 * h)
        return (4 * d1 - d2) / 3

    def _diff_a(self, t, h):
        f = self.r
        f0 = f(t)
        d1 = (f(t + h) - 2 * f0 + f(t - h)) / (h * h)
        d2 = (f(t + 2 * h) - 2 * f0 + f(t - 2 * h)) / (4 * h * h)
        return (4 * d1 - d2) / 3

    def derivative_errors(self, t):
        """Per time: estimated errors (m/s, m/s^2) of v and a as used by ``state`` (0 for a given callable): the
        truncation 2 |D(h) - D(2h)| / 15 (the leading h^4 term, doubled for the next order) plus the rounding 1.5 e_r / h
        (v), 5.7 e_r / h^2 (a), e_r = 2 eps (|r| + |v| |t|) the error of one evaluation of r (its argument t +- h is
        rounded to ulp(t)). A step comparable with the time scale of the motion aliases it, and no estimate from the
        samples can see that: the step must resolve the motion (``timescale`` chooses it)."""
        t = np.asarray(t, float)
        r = np.asarray(self.r(t), float)
        ev = np.zeros(t.shape)
        ea = np.zeros(t.shape)
        if not self.numerical:
            return ev, ea
        hv, ha = self._steps()
        vv = np.asarray(self.v(t), float) if self.v is not None else self._diff_v(t, hv)
        e_r = 2 * EPS * (np.linalg.norm(r, axis=-1) + np.linalg.norm(vv, axis=-1) * np.abs(t))
        if self.v is None:
            ev = 2 * np.linalg.norm(self._diff_v(t, hv) - self._diff_v(t, 2 * hv), axis=-1) / 15 + 1.5 * e_r / hv
        if self.a is None:
            ea = 2 * np.linalg.norm(self._diff_a(t, ha) - self._diff_a(t, 2 * ha), axis=-1) / 15 + 5.7 * e_r / (ha * ha)
        return ev, ea

    def derivative_error(self, t):
        """The largest estimated errors over the times t: {'v': m/s, 'a': m/s^2} (``derivative_errors``)."""
        ev, ea = self.derivative_errors(t)
        return {"v": float(np.max(ev)) if ev.size else 0.0, "a": float(np.max(ea)) if ea.size else 0.0}


def _vec(v):
    return np.asarray(v, float).reshape(3)


def uniform(r0, v, t0: float = 0.0) -> FunctionWorldline:
    """r(t) = r0 + v (t - t0)."""
    r0, v = _vec(r0), _vec(v)
    if np.linalg.norm(v) >= C:
        raise ValueError("uniform: |v| < c")
    return FunctionWorldline(lambda t: r0 + v * (np.asarray(t, float)[..., None] - t0),
                             lambda t: np.broadcast_to(v, np.shape(t) + (3,)).copy(),
                             lambda t: np.zeros(np.shape(t) + (3,)))


def circular(radius: float, omega: float, center=(0.0, 0.0, 0.0), phase: float = 0.0) -> FunctionWorldline:
    """Uniform circular motion in the plane z = center_z: r = center + R (cos(w t + phase), sin(w t + phase), 0)."""
    cen = _vec(center)
    if abs(omega) * radius >= C:
        raise ValueError("circular: speed |omega| R < c")

    def r(t):
        p = omega * np.asarray(t, float) + phase
        return cen + radius * np.stack([np.cos(p), np.sin(p), np.zeros_like(p)], axis=-1)

    def v(t):
        p = omega * np.asarray(t, float) + phase
        return radius * omega * np.stack([-np.sin(p), np.cos(p), np.zeros_like(p)], axis=-1)

    def a(t):
        p = omega * np.asarray(t, float) + phase
        return -radius * omega * omega * np.stack([np.cos(p), np.sin(p), np.zeros_like(p)], axis=-1)

    return FunctionWorldline(r, v, a)


def harmonic(amplitude, omega: float, center=(0.0, 0.0, 0.0)) -> FunctionWorldline:
    """Linear oscillation r = center + A sin(omega t) (A a vector)."""
    A, cen = _vec(amplitude), _vec(center)
    if np.linalg.norm(A) * abs(omega) >= C:
        raise ValueError("harmonic: peak speed |A| omega < c")
    return FunctionWorldline(lambda t: cen + A * np.sin(omega * np.asarray(t, float))[..., None],
                             lambda t: A * (omega * np.cos(omega * np.asarray(t, float)))[..., None],
                             lambda t: A * (-omega * omega * np.sin(omega * np.asarray(t, float)))[..., None])


def hyperbolic(g: float, direction=(0.0, 0.0, 1.0), r0=(0.0, 0.0, 0.0), t0: float = 0.0) -> FunctionWorldline:
    """Uniformly accelerated (hyperbolic) motion with proper acceleration g along a unit direction, at rest at r0 at
    t = t0: x(t) = (c^2/g)(sqrt(1 + (g s/c)^2) - 1), v = g s / sqrt(1 + (g s/c)^2), a = g / (1 + (g s/c)^2)^(3/2),
    s = t - t0. Its retarded time has a closed form (``HyperbolicWorldline.retarded_closed``), which
    ``retarded_time`` uses; a field point at or beyond the past horizon Z' + c (t - t0) = 0 has none."""
    return HyperbolicWorldline(g, direction, r0, t0)


class HyperbolicWorldline(FunctionWorldline):
    """Hyperbolic motion (``hyperbolic``) with its closed-form retarded time (module docstring)."""

    def __init__(self, g: float, direction=(0.0, 0.0, 1.0), r0=(0.0, 0.0, 0.0), t0: float = 0.0):
        if not g > 0:
            raise ValueError("hyperbolic: proper acceleration g > 0")
        e = _vec(direction)
        e = e / np.linalg.norm(e)
        r0 = _vec(r0)
        self.g, self.e, self.r0, self.t0 = float(g), e, r0, float(t0)

        def w(t):
            return g * (np.asarray(t, float) - t0) / C

        # (c^2/g)(sqrt(1 + w^2) - 1) = (c^2/g) w^2 / (sqrt(1 + w^2) + 1): no cancellation for small w
        super().__init__(lambda t: r0 + e * ((C * C / g) * w(t) ** 2 / (np.sqrt(1 + w(t) ** 2) + 1))[..., None],
                         lambda t: e * (C * w(t) / np.sqrt(1 + w(t) ** 2))[..., None],
                         lambda t: e * (g / (1 + w(t) ** 2) ** 1.5)[..., None])

    def retarded_closed(self, x, t):
        """Closed-form retarded times for points x (N, 3) at times t (N,): (t_ret, error bound (s), fail code) with
        code 0 (found) or 1 (the point is beyond the past horizon, or within the rounding of Z' + c (t - t0) of it)."""
        a = C * C / self.g
        X = x - self.r0
        Zr = X @ self.e
        perp = X - Zr[:, None] * self.e
        rho2 = np.einsum("ij,ij->i", perp, perp)
        A = Zr + a
        B = C * (t - self.t0)
        apb, amb = A + B, A - B
        d_apb = 2 * EPS * (np.abs(Zr) + a + np.abs(B)) + EPS * (np.linalg.norm(x, axis=-1) + np.linalg.norm(self.r0))
        code = np.where(apb > d_apb, 0, 1)
        Q = amb * apb
        D = rho2 + Q + a * a
        disc = np.sqrt((rho2 + Q - a * a) ** 2 + 4 * a * a * rho2)
        with np.errstate(divide="ignore", invalid="ignore"):
            # D + disc >= 2 a^2 > 0; for D < 0 (then Q < 0 and Z' - B < 0) by the conjugate, free of cancellation
            u = np.where(D >= 0, 2 * a * apb / (D + disc), (disc - D) / (-2 * a * np.where(amb < 0, amb, -1.0)))
            eta = np.log(np.where(code == 0, u, 1.0))
        s = (a / C) * np.sinh(eta)
        tr = self.t0 + s
        # d eta / d(Z' + B) ~ 1 / (Z' + B): the horizon distance's rounding, and a few eps in eta
        err = (a / C) * np.cosh(eta) * (d_apb / np.where(code == 0, apb, 1.0) + 8 * EPS) + 2 * np.spacing(np.abs(t))
        return np.where(code == 0, tr, np.nan), np.where(code == 0, err, np.nan), code


class SampledWorldline(Worldline):
    """A worldline from samples t_i (increasing), r_i (N, 3), optionally v_i and a_i.

    * r, v, a given: quintic Hermite on every interval (exact for quintic motion; error O(h^6) in r, O(h^5) in v,
      O(h^4) in a);
    * r and v: cubic Hermite (O(h^4), O(h^3), O(h^2));
    * r only: a quintic interpolating spline (scipy.interpolate.make_interp_spline, k = 5; O(h^6), O(h^5), O(h^4)).
    ``interpolation_error()`` measures the error: the same interpolant rebuilt from every third sample is compared
    with the dropped samples (r, and v, a where given; for positions only, r), and scaled to the full sampling by
    3^-p with the order p of the method (the measured coarse error is also returned)."""

    def __init__(self, t, r, v=None, a=None):
        t = np.asarray(t, float)
        if t.ndim != 1 or len(t) < 6 or np.any(np.diff(t) <= 0):
            raise ValueError("SampledWorldline: at least 6 strictly increasing times")
        self.t = t
        self.r = np.asarray(r, float).reshape(len(t), 3)
        self.v = None if v is None else np.asarray(v, float).reshape(len(t), 3)
        self.a = None if a is None else np.asarray(a, float).reshape(len(t), 3)
        if self.a is not None and self.v is None:
            raise ValueError("SampledWorldline: a sampled acceleration needs the sampled velocity")
        self.domain = (float(t[0]), float(t[-1]))
        self.kind = "quintic Hermite" if self.a is not None else "cubic Hermite" if self.v is not None \
            else "quintic spline"
        self._spl = None
        if self.v is None:
            from scipy.interpolate import make_interp_spline
            self._spl = make_interp_spline(t, self.r, k=5)

    def state(self, t):
        t = np.asarray(t, float)
        lo, hi = self.domain
        if np.any((t < lo - 1e-12 * max(1.0, abs(lo))) | (t > hi + 1e-12 * max(1.0, abs(hi)))):
            raise ValueError("SampledWorldline: time outside the sampled domain")
        if self._spl is not None:
            return self._spl(t), self._spl(t, 1), self._spl(t, 2)
        tf = t.ravel()
        i = np.clip(np.searchsorted(self.t, tf, side="right") - 1, 0, len(self.t) - 2)
        h = (self.t[i + 1] - self.t[i])[:, None]
        s = ((tf - self.t[i]) / h[:, 0])[:, None]
        p0, p1 = self.r[i], self.r[i + 1]
        v0, v1 = self.v[i] * h, self.v[i + 1] * h
        if self.a is not None:
            a0, a1 = self.a[i] * h * h, self.a[i + 1] * h * h
            s2, s3, s4, s5 = s * s, s ** 3, s ** 4, s ** 5
            H = [1 - 10 * s3 + 15 * s4 - 6 * s5, s - 6 * s3 + 8 * s4 - 3 * s5, 0.5 * (s2 - 3 * s3 + 3 * s4 - s5),
                 0.5 * (s3 - 2 * s4 + s5), -4 * s3 + 7 * s4 - 3 * s5, 10 * s3 - 15 * s4 + 6 * s5]
            dH = [-30 * s2 + 60 * s3 - 30 * s4, 1 - 18 * s2 + 32 * s3 - 15 * s4, 0.5 * (2 * s - 9 * s2 + 12 * s3 - 5 * s4),
                  0.5 * (3 * s2 - 8 * s3 + 5 * s4), -12 * s2 + 28 * s3 - 15 * s4, 30 * s2 - 60 * s3 + 30 * s4]
            ddH = [-60 * s + 180 * s2 - 120 * s3, -36 * s + 96 * s2 - 60 * s3, 0.5 * (2 - 18 * s + 36 * s2 - 20 * s3),
                   0.5 * (6 * s - 24 * s2 + 20 * s3), -24 * s + 84 * s2 - 60 * s3, 60 * s - 180 * s2 + 120 * s3]
            coef = [p0, v0, a0, a1, v1, p1]
        else:
            s2, s3 = s * s, s ** 3
            H = [1 - 3 * s2 + 2 * s3, s - 2 * s2 + s3, -s2 + s3, 3 * s2 - 2 * s3]
            dH = [-6 * s + 6 * s2, 1 - 4 * s + 3 * s2, -2 * s + 3 * s2, 6 * s - 6 * s2]
            ddH = [-6 + 12 * s, -4 + 6 * s, -2 + 6 * s, 6 - 12 * s]
            coef = [p0, v0, v1, p1]
        r = sum(Hk * ck for Hk, ck in zip(H, coef))
        v = sum(Hk * ck for Hk, ck in zip(dH, coef)) / h
        a = sum(Hk * ck for Hk, ck in zip(ddH, coef)) / (h * h)
        shp = t.shape + (3,)
        return r.reshape(shp), v.reshape(shp), a.reshape(shp)

    def interpolation_error(self) -> dict:
        """Estimated maximum interpolation errors of r, v, a (and the measured errors of the coarse interpolant,
        ``coarse``): the interpolant rebuilt from every third sample is compared with the dropped samples (at a third
        and two thirds of its intervals, where the errors of r, v and a all are near their maxima; at the midpoints
        those of v would vanish by symmetry) and scaled by 3^-p with the order p of each."""
        keep = slice(0, None, 3)
        tk = self.t[keep]
        if len(tk) < 6:
            raise ValueError("interpolation_error: needs at least 16 samples")
        coarse_wl = SampledWorldline(tk, self.r[keep], None if self.v is None else self.v[keep],
                                     None if self.a is None else self.a[keep])
        drop = np.setdiff1d(np.arange(len(self.t)), np.arange(len(self.t))[keep])
        drop = drop[(self.t[drop] > tk[0]) & (self.t[drop] < tk[-1])]
        r, v, a = coarse_wl.state(self.t[drop])
        orders = {"quintic Hermite": (6, 5, 4), "cubic Hermite": (4, 3, 2), "quintic spline": (6, 5, 4)}[self.kind]
        coarse = {"r": float(np.max(np.linalg.norm(r - self.r[drop], axis=-1)))}
        if self.v is not None:
            coarse["v"] = float(np.max(np.linalg.norm(v - self.v[drop], axis=-1)))
        if self.a is not None:
            coarse["a"] = float(np.max(np.linalg.norm(a - self.a[drop], axis=-1)))
        est = {k: val / 3.0 ** orders["rva".index(k)] for k, val in coarse.items()}
        return {"estimate": est, "coarse": coarse, "method": self.kind, "orders": orders}


@dataclass(frozen=True)
class Charge:
    """A point charge q (C) on a worldline."""
    q: float
    worldline: Worldline


# --- retarded time ----------------------------------------------------------------------------------------------------
_FAIL = {1: "no retarded time resolved: g = c tau - R stays within its rounding error where its slope can no longer "
            "lift it out (the point is beyond a horizon of the worldline, e.g. of hyperbolic motion, or within the "
            "rounding of one; or the charge moves so close to c that 1 - n.beta is lost in double precision, from "
            "gamma ~ 2e7), or g stays negative (the worldline is not subluminal)",
         2: "the retarded time lies before the worldline's domain",
         3: "the retarded time lies after the worldline's domain",
         4: "the worldline is not subluminal there"}


def _g_eval(worldline, x, t, tau):
    """g(tau) = c tau - |x - r(t - tau)|, its slope g' = c - n . v, its rounding bound B (module docstring) and |v|^2
    for the points x (m, 3), t (m,)."""
    tp = t - tau
    r, v, _ = worldline.state(tp)
    d = x - r
    R = np.linalg.norm(d, axis=-1)
    n = d / np.where(R > 0, R, 1.0)[:, None]
    vv = np.einsum("ij,ij->i", v, v)
    B = 4 * EPS * (C * np.abs(tau) + np.linalg.norm(x, axis=-1) + np.linalg.norm(r, axis=-1)) + EPS * np.sqrt(vv) * np.abs(tp)
    return C * tau - R, C - np.einsum("ij,ij->i", n, v), B, vv


def _retarded_solve(worldline, x, t, max_iter):
    """The bracketed Newton solution for points x (N, 3), t (N,): (t_ret, error bound, fail code) (module docstring)."""
    N = len(t)
    t_min, t_max = worldline.domain
    tau = np.zeros(N)
    err = np.zeros(N)
    code = np.zeros(N, int)
    lo = np.maximum(0.0, t - t_max) if math.isfinite(t_max) else np.zeros(N)
    cap = t - t_min if math.isfinite(t_min) else np.full(N, math.inf)
    code[lo > cap] = 2
    act = np.nonzero(code == 0)[0]
    # the lower end: g(lo) <= 0 (lo = 0: g = -R), above its rounding the root is after the domain
    gl, dgl, Bl, vv = _g_eval(worldline, x[act], t[act], lo[act])
    code[act[vv > C * C * (1 + 1e-15)]] = 4
    code[act[(gl > Bl) & (code[act] == 0)]] = 3
    at_lo = act[(np.abs(gl) <= Bl) & (code[act] == 0)]
    tau[at_lo] = lo[at_lo]
    err[at_lo] = (Bl / np.maximum(dgl, 1e-300))[np.isin(act, at_lo)]
    R_lo = np.zeros(N)
    R_lo[act] = C * lo[act] - gl
    done = code != 0
    done[at_lo] = True
    # the upper end: doubled inside the domain until g > B; g within B where its slope cannot lift it above B: refused
    hi = lo + np.maximum(R_lo / C, 4 * np.spacing(np.maximum(lo, 1e-300)))
    act = np.nonzero(~done)[0]
    for _ in range(64):
        if act.size == 0:
            break
        h = np.minimum(hi[act], cap[act])
        hi[act] = h
        gh, dgh, Bh, vv = _g_eval(worldline, x[act], t[act], h)
        sup = vv > C * C * (1 + 1e-15)
        code[act[sup]] = 4
        ok = (gh > Bh) & ~sup
        noise = (np.abs(gh) <= Bh) & ~ok & ~sup
        stuck = noise & (dgh * (h - lo[act]) <= 2 * Bh)  # a doubling cannot lift g out of its rounding band
        at_cap = (h >= cap[act]) & ~ok & ~sup
        root_cap = at_cap & noise  # the root is at the domain's start, within rounding
        tau[act[root_cap]] = h[root_cap]
        err[act[root_cap]] = (Bh / np.maximum(dgh, 1e-300))[root_cap]
        code[act[at_cap & ~noise]] = 2
        code[act[stuck & ~at_cap]] = 1
        fin = ok | sup | at_cap | stuck
        done[act[root_cap]] = True
        act_next = act[~fin]
        hi[act_next] = lo[act_next] + 2 * (hi[act_next] - lo[act_next])
        act = act_next
    code[act] = 1
    # Newton steps inside [lo, hi] (bisection when a step leaves it), until |g| <= B or the bracket is at ulp(t)
    act = np.nonzero((code == 0) & ~done)[0]
    lo_b, hi_b = lo.copy(), hi.copy()
    tt = hi.copy()
    for _ in range(max_iter):
        if act.size == 0:
            break
        ta = tt[act]
        gv, dg, Bv, vv = _g_eval(worldline, x[act], t[act], ta)
        sup = (vv > C * C * (1 + 1e-15)) | ~(dg > 0)
        code[act[sup]] = 4
        conv = (np.abs(gv) <= Bv) & ~sup
        pos = gv > 0
        hi_b[act] = np.where(pos, ta, hi_b[act])
        lo_b[act] = np.where(pos, lo_b[act], ta)
        width = hi_b[act] - lo_b[act]
        conv |= (width <= 4 * np.spacing(np.maximum(np.abs(t[act]), hi_b[act]))) & ~sup
        with np.errstate(divide="ignore", invalid="ignore"):
            new = ta - gv / dg
        # converged: one more Newton step where it stays in the bracket (quadratic convergence takes the root from
        # within B / g' to the actual rounding of g; the step is itself at most B / g', so the bound is 2 B / g')
        stepped = (new > lo_b[act]) & (new < hi_b[act]) & np.isfinite(new)
        last = np.where(stepped, new, ta)
        tau[act[conv]] = last[conv]
        err[act[conv]] = (np.where(stepped, 2.0, 1.0) * Bv / np.maximum(dg, 1e-300))[conv]
        outside = (new <= lo_b[act]) | (new >= hi_b[act]) | ~np.isfinite(new)
        new = np.where(outside, 0.5 * (lo_b[act] + hi_b[act]), new)
        tt[act] = new
        act = act[~(conv | sup)]
    code[act] = 1  # not reached for a subluminal worldline (bisection halves the bracket each step)
    ok = code == 0
    tr = np.where(ok, t - tau, np.nan)
    err = np.where(ok, err + np.spacing(np.abs(t)), np.nan)  # t - tau is rounded to ulp(t)
    return tr, err, code


def retarded_time(worldline: Worldline, x, t, max_iter: int = 200, full: bool = False, on_fail: str = "raise",
                  closed_form: bool = True):
    """t_ret (array of x.shape[:-1] broadcast with t): the unique root of c (t - t') = |x - r(t')| for a subluminal
    worldline, resolved to the rounding of g (module docstring). full=True returns (t_ret, err) with err a bound on
    |t_ret - exact| from that rounding (the closed form's own for hyperbolic motion). Points with no resolved root
    (beyond a horizon or within rounding of one, outside the worldline's domain, superluminal) are refused:
    on_fail='raise' raises ValueError listing them (one point never aborts the others silently: all are checked),
    on_fail='nan' gives them NaN. closed_form=False forces the general solver on a hyperbolic worldline."""
    if on_fail not in ("raise", "nan"):
        raise ValueError("retarded_time: on_fail = 'raise' or 'nan'")
    x = np.asarray(x, float)
    t = np.asarray(t, float)
    shape = np.broadcast_shapes(x.shape[:-1], t.shape)
    xf = np.broadcast_to(x, shape + (3,)).reshape(-1, 3)
    tf = np.broadcast_to(t, shape).ravel()
    if closed_form and isinstance(worldline, HyperbolicWorldline):
        tr, err, code = worldline.retarded_closed(xf, tf)
        tr, err = _polish(worldline, xf, tf, tr, err, code)
    else:
        tr, err, code = _retarded_solve(worldline, xf, tf, max_iter)
    if np.any(code != 0) and on_fail == "raise":
        bad = np.nonzero(code != 0)[0]
        lines = [f"{np.sum(code == c)} point(s): {_FAIL[c]}" for c in sorted(set(code[bad].tolist()))]
        ex = ", ".join(f"#{i} x = {np.array2string(xf[i], precision=6)}, t = {tf[i]:.9g}" for i in bad[:5])
        raise ValueError(f"retarded_time: {len(bad)} of {len(tf)} points refused — " + "; ".join(lines)
                         + f"; e.g. {ex}")
    tr = tr.reshape(shape)
    return (tr, err.reshape(shape)) if full else tr


def _polish(worldline, x, t, tr, err, code):
    """Newton steps on g after the closed form, where g exceeds its rounding (the closed form loses digits for a weakly
    accelerated charge near it); the bound is then the last step plus B / g'."""
    ok = np.nonzero(code == 0)[0]
    if ok.size == 0:
        return tr, err
    tau = t[ok] - tr[ok]
    e = err[ok]
    for _ in range(4):
        gv, dg, Bv, _ = _g_eval(worldline, x[ok], t[ok], tau)
        big = np.abs(gv) > Bv
        if not np.any(big):
            break
        with np.errstate(divide="ignore", invalid="ignore"):
            step = np.where(big & (dg > 0), gv / dg, 0.0)
        tau = tau - step
        e = np.where(big, np.abs(step) + Bv / np.maximum(dg, 1e-300), e)
    tr = tr.copy()
    err = err.copy()
    tr[ok] = t[ok] - tau
    err[ok] = e + np.spacing(np.abs(t[ok]))
    return tr, err


def _retarded(worldline, x, t, on_fail="raise"):
    """Retarded quantities: t_ret, R_vec, R, n, beta, beta_dot, err (the bound on t_ret); NaN where refused
    (on_fail='nan')."""
    x = np.asarray(x, float)
    t = np.asarray(t, float)
    shape = np.broadcast_shapes(x.shape[:-1], t.shape)
    xb = np.broadcast_to(x, shape + (3,))
    tb = np.broadcast_to(t, shape)
    tr, err = retarded_time(worldline, xb, tb, full=True, on_fail=on_fail)
    good = np.isfinite(tr)
    r = np.full(shape + (3,), np.nan)
    v = np.full(shape + (3,), np.nan)
    a = np.full(shape + (3,), np.nan)
    if np.all(good):
        r, v, a = worldline.state(tr)
    elif np.any(good):
        r[good], v[good], a[good] = worldline.state(tr[good])
    d = xb - r
    R = np.linalg.norm(d, axis=-1)
    n = d / R[..., None]
    return tr, d, R, n, v / C, a / C, err


def _check_derivatives(worldline, tr, R, n, b, bd, Ev, Ea):
    """Refuse a finite-difference worldline where its estimated derivative errors (dv, da) would change the field by
    more than its rtol: the velocity part changes by about (dv/c)(3/kappa + 2 gamma^2) of itself (its kappa^-3 and
    gamma^-2 factors), the acceleration part by (dv/c)(3/kappa) of itself plus the field of an acceleration da,
    q/(4 pi eps0 c^2) |n - beta| da / (kappa^3 R)."""
    if not (isinstance(worldline, FunctionWorldline) and worldline.numerical):
        return
    good = np.isfinite(tr)
    ev, ea = (np.zeros(tr.shape) for _ in range(2))
    if np.any(good):
        ev[good], ea[good] = worldline.derivative_errors(tr[good])
    kap = 1.0 - np.einsum("...i,...i->...", n, b)
    g2 = 1.0 - np.einsum("...i,...i->...", b, b)
    sens = ev / C * (3 / kap + 2 / g2)
    dE = np.linalg.norm(Ev, axis=-1) * sens + np.linalg.norm(Ea, axis=-1) * ev / C * 3 / kap \
        + K_E * np.linalg.norm(n - b, axis=-1) * ea / (C * C * kap ** 3 * R)
    rel = dE / np.maximum(np.linalg.norm(Ev + Ea, axis=-1), 1e-300)
    worst = float(np.nanmax(rel)) if np.any(good) else 0.0
    if worst > worldline.rtol:
        raise ValueError(f"fields: the worldline's finite-difference derivatives are not accurate enough here: "
                         f"estimated field error {worst:.2e} > rtol {worldline.rtol:.1e} (dv up to "
                         f"{float(np.nanmax(ev)):.3g} m/s, da up to {float(np.nanmax(ea)):.3g} m/s^2) — give v and a, "
                         "or a better step / time scale")


# --- fields and potentials ----------------------------------------------------------------------------------------------
def fields(charges, x, t, parts: bool = False, on_fail: str = "raise"):
    """E (V/m) and B (T) at points x (..., 3) and times t (broadcast), summed over the charges (a Charge or a sequence of
    them). parts=True returns a dict with the velocity (generalised Coulomb) and acceleration (radiation) parts:
    E_vel, E_acc, B_vel, B_acc, their sums E, B, and per charge the retarded times 't_ret' and their bounds 't_err'
    (``retarded_time``). Points with no retarded time are refused (on_fail='raise', listed) or NaN (on_fail='nan'); a
    finite-difference worldline is refused where its derivative errors would change the field by more than its rtol.
    Double precision: relative error ~1e-16 gamma^2 (beta enters as a float; module ABOUT)."""
    if isinstance(charges, Charge):
        charges = [charges]
    out = None
    tret, terr = [], []
    for ch in charges:
        tr, _, R, n, b, bd, err = _retarded(ch.worldline, x, t, on_fail)
        kap = 1.0 - np.einsum("...i,...i->...", n, b)
        g2 = 1.0 - np.einsum("...i,...i->...", b, b)  # 1/gamma^2
        nb = n - b
        Ev = ch.q * K_E * nb * (g2 / (kap ** 3 * R * R))[..., None]
        Ea = ch.q * K_E / C * np.cross(n, np.cross(nb, bd)) / (kap ** 3 * R)[..., None]
        _check_derivatives(ch.worldline, tr, R, n, b, bd, Ev / ch.q if ch.q else Ev, Ea / ch.q if ch.q else Ea)
        part = {"E_vel": Ev, "E_acc": Ea, "B_vel": np.cross(n, Ev) / C, "B_acc": np.cross(n, Ea) / C}
        tret.append(tr)
        terr.append(err)
        if out is None:
            out = part
        else:
            for k in out:
                out[k] = out[k] + part[k]
    out["E"] = out["E_vel"] + out["E_acc"]
    out["B"] = out["B_vel"] + out["B_acc"]
    if parts:
        out["t_ret"], out["t_err"] = tret, terr
        return out
    return out["E"], out["B"]


def potentials(charges, x, t, on_fail: str = "raise"):
    """Liénard–Wiechert potentials (Lorenz gauge): phi (V) and A (T m) at x, t, summed over the charges (refusals as in
    ``fields``)."""
    if isinstance(charges, Charge):
        charges = [charges]
    phi = A = 0.0
    for ch in charges:
        _, _, R, n, b, _, _ = _retarded(ch.worldline, x, t, on_fail)
        kap = 1.0 - np.einsum("...i,...i->...", n, b)
        p = ch.q * K_E / (kap * R)
        phi = phi + p
        A = A + p[..., None] * b / C
    return phi, A


def heaviside_field(q: float, r_present, v, x):
    """Closed-form field of a charge in uniform motion (velocity v) whose PRESENT position (at the time of the field) is
    r_present: E = q/(4 pi eps0) (1 - beta^2) R / (R^3 (1 - beta^2 sin^2 psi)^(3/2)), B = v x E / c^2."""
    v = _vec(v)
    d = np.asarray(x, float) - _vec(r_present)
    R = np.linalg.norm(d, axis=-1)
    b2 = float(v @ v) / C ** 2
    cos_psi = (d @ v) / (R * math.sqrt(float(v @ v))) if b2 > 0 else np.zeros_like(R)
    sin2 = 1.0 - cos_psi ** 2
    E = q * K_E * (1 - b2) * d / (R ** 3 * (1 - b2 * sin2) ** 1.5)[..., None]
    B = np.cross(v, E) / C ** 2
    return E, B


# --- radiated power -----------------------------------------------------------------------------------------------------
def larmor_power(q: float, a) -> float:
    """Larmor: P = q^2 |a|^2 / (6 pi eps0 c^3) (W)."""
    a = np.asarray(a, float)
    return q * q * np.einsum("...i,...i->...", a, a) / (6 * math.pi * EPS0 * C ** 3)


def lienard_power(q: float, v, a):
    """Liénard: P = q^2 gamma^6 / (6 pi eps0 c) [beta_dot^2 - (beta x beta_dot)^2] (W), per unit retarded time."""
    b = np.asarray(v, float) / C
    bd = np.asarray(a, float) / C
    g2 = 1.0 / (1.0 - np.einsum("...i,...i->...", b, b))
    cr = np.cross(b, bd)
    return q * q * g2 ** 3 * (np.einsum("...i,...i->...", bd, bd) - np.einsum("...i,...i->...", cr, cr)) \
        / (6 * math.pi * EPS0 * C)


def angular_power(q: float, v, a, n, per: str = "retarded"):
    """dP/dOmega (W/sr) in the directions n (unit vectors, (..., 3)) for velocity v and acceleration a at the
    retarded time: per="retarded" (energy per unit retarded time, integrates to Liénard's P) or "observer" (per unit
    observer time: R^2 S . n at the observer)."""
    if per not in ("retarded", "observer"):
        raise ValueError("angular_power: per = 'retarded' or 'observer'")
    n = np.asarray(n, float)
    b = np.asarray(v, float) / C
    bd = np.asarray(a, float) / C
    kap = 1.0 - np.einsum("...i,...i->...", n, b)
    w = np.cross(n, np.cross(n - b, bd))
    num = np.einsum("...i,...i->...", w, w)
    return q * q / (16 * math.pi ** 2 * EPS0 * C) * num / kap ** (5 if per == "retarded" else 6)


# --- synchrotron radiation -----------------------------------------------------------------------------------------------
def critical_frequency(gamma: float, rho: float) -> float:
    """omega_c = (3/2) gamma^3 c / rho (rad/s), the frequency that nominally divides the radiated power into halves
    (X-ray Data Booklet §2.1): the fraction below it is 0.5000052565 (the gamma >> 1 spectrum; mpmath and the test)."""
    return 1.5 * gamma ** 3 * C / rho


def bessel_k_tail(nu: float, x):
    """int_x^inf K_nu(t) dt = int_0^inf exp(-x cosh u) cosh(nu u) / cosh u du, x > 0, by composite Gauss–Legendre
    (24 nodes per panel, panels of width <= min(0.5, sqrt(2/x)/2), cut where the integrand is below 1e-18 of its
    value at u = 0, the factor exp(-x) taken out)."""
    xs = np.atleast_1d(np.asarray(x, float))
    out = np.empty(xs.shape)
    for i, xi in enumerate(xs.ravel()):
        if not xi > 0:
            raise ValueError("bessel_k_tail: x > 0")
        # integrand / exp(-x) = exp(-x (cosh u - 1)) cosh(nu u)/cosh u ; find U with log of it < -41.5
        U = 1.0
        while xi * (math.cosh(U) - 1) - (abs(nu) - 1) * U - math.log(2) < 41.5:
            U *= 1.5
        width = min(0.5, 0.5 * math.sqrt(2.0 / xi))
        npan = max(4, int(math.ceil(U / width)))
        e = np.linspace(0.0, U, npan + 1)
        lo, hi = e[:-1, None], e[1:, None]
        u = 0.5 * (hi - lo) * _GL_X[None, :] + 0.5 * (hi + lo)
        f = np.exp(-xi * (np.cosh(u) - 1.0)) * np.cosh(nu * u) / np.cosh(u)
        out.flat[i] = math.exp(-xi) * float(np.sum(0.5 * (hi - lo) * _GL_W[None, :] * f))
    return out.reshape(np.shape(x)) if np.ndim(x) else float(out[0])


def synchrotron_F(x):
    """F(x) = x int_x^inf K_{5/3}(t) dt (int_0^inf F dx = 8 pi / (9 sqrt 3))."""
    x = np.asarray(x, float)
    return x * bessel_k_tail(5.0 / 3.0, x)


def synchrotron_G(x):
    """G(x) = x K_{2/3}(x)."""
    x = np.asarray(x, float)
    return x * special.kv(2.0 / 3.0, x)


def synchrotron_power(q: float, gamma: float, rho: float) -> float:
    """Liénard's power for uniform circular motion of radius rho: q^2 c beta^4 gamma^4 / (6 pi eps0 rho^2) (W)."""
    beta2 = 1.0 - 1.0 / gamma ** 2
    return q * q * C * beta2 ** 2 * gamma ** 4 / (6 * math.pi * EPS0 * rho ** 2)


def synchrotron_spectrum(q: float, gamma: float, rho: float, omega, component: str = "total"):
    """dP/domega (W per rad/s) of a charge on a circle of radius rho, averaged over the orbit: (P / omega_c)
    (9 sqrt 3 / 8 pi) F(omega / omega_c) for the total, (9 sqrt 3 / 16 pi)(F +- G) for the sigma (+, field in the
    orbit plane) and pi (-) components; the ultrarelativistic limit (relative corrections O(1/gamma^2))."""
    wc = critical_frequency(gamma, rho)
    P = synchrotron_power(q, gamma, rho)
    y = np.asarray(omega, float) / wc
    F = synchrotron_F(y)
    if component == "total":
        S = 9 * math.sqrt(3) / (8 * math.pi) * F
    elif component in ("sigma", "pi"):
        G = synchrotron_G(y)
        S = 9 * math.sqrt(3) / (16 * math.pi) * (F + G if component == "sigma" else F - G)
    else:
        raise ValueError("synchrotron_spectrum: component total | sigma | pi")
    return P / wc * S


def synchrotron_angular_spectrum(q: float, gamma: float, rho: float, omega, psi):
    """d^2P/(domega dpsi) (W per rad/s per rad of vertical angle psi, measured from the orbit plane), averaged over the
    orbit, as (sigma, pi): the X-ray Data Booklet's eq. (1) turned into power for one charge,

        d^2P/(domega dpsi) = 3 q^2 gamma^2 beta / (16 pi^3 eps0 rho) y^2 (1 + X^2)^2 [K_{2/3}^2(xi), X^2/(1 + X^2)
        K_{1/3}^2(xi)],   y = omega/omega_c, X = gamma psi, xi = y (1 + X^2)^(3/2) / 2,

    (photon number per relative bandwidth times hbar omega / omega, the booklet's I/e = beta c / (2 pi rho) for one
    charge, times 2 pi of orbit angle). Ultrarelativistic (small-angle) limit."""
    wc = critical_frequency(gamma, rho)
    beta = math.sqrt(1.0 - 1.0 / gamma ** 2)
    y = np.asarray(omega, float) / wc
    X = gamma * np.asarray(psi, float)
    y, X = np.broadcast_arrays(y, X)
    xi = 0.5 * y * (1 + X * X) ** 1.5
    pref = 3 * q * q * gamma ** 2 * beta / (16 * math.pi ** 3 * EPS0 * rho) * y * y * (1 + X * X) ** 2
    with np.errstate(over="ignore", invalid="ignore"):
        k23 = special.kv(2.0 / 3.0, xi)
        k13 = special.kv(1.0 / 3.0, xi)
    sig = np.where(xi > 700, 0.0, pref * k23 ** 2)
    pi_ = np.where(xi > 700, 0.0, pref * X * X / (1 + X * X) * k13 ** 2)
    return sig, pi_


# --- cyclotron harmonics (Schott) ------------------------------------------------------------------------------------------
def harmonic_angular_power(q: float, beta: float, rho: float, m: int, theta):
    """dP_m/dOmega (W/sr) of the m-th harmonic of a charge on a circle (radius rho, speed beta c), averaged over the
    orbit, at polar angle theta from the orbit's axis (Schott 1912, eq. 128, in SI):
    q^2 omega0^2 m^2 / (8 pi^2 eps0 c) [cot^2 theta J_m^2(m beta sin theta) + beta^2 J_m'^2(m beta sin theta)]."""
    if not 0 < beta < 1:
        raise ValueError("harmonic_angular_power: 0 < beta < 1")
    w0 = beta * C / rho
    th = np.asarray(theta, float)
    s, c = np.sin(th), np.cos(th)
    z = m * beta * s
    Jm = special.jv(m, z)
    with np.errstate(divide="ignore", invalid="ignore"):
        cot2J2 = np.where(s != 0, (c / np.where(s != 0, s, 1.0)) ** 2 * Jm ** 2, 0.0)
    if m == 1:  # J_1(z)/sin(theta) -> beta/2 at the poles
        cot2J2 = np.where(s != 0, cot2J2, (beta / 2) ** 2)
    return q * q * w0 * w0 * m * m / (8 * math.pi ** 2 * EPS0 * C) * (cot2J2 + beta ** 2 * special.jvp(m, z) ** 2)


def harmonic_power(q: float, beta: float, rho: float, m: int) -> float:
    """P_m (W): q^2 c beta / (2 pi eps0 rho^2) [m beta^2 J'_{2m}(2 m beta) - m^2 (1 - beta^2) int_0^beta J_{2m}(2 m x)
    dx] (Schott 1912, the power of the j-th harmonic, in SI); the integral by 64-node Gauss–Legendre on panels of at
    most a quarter oscillation."""
    if not 0 < beta < 1:
        raise ValueError("harmonic_power: 0 < beta < 1")
    npan = max(2, int(math.ceil(2 * m * beta / (math.pi / 2))))
    xg, wg = np.polynomial.legendre.leggauss(64)
    e = np.linspace(0.0, beta, npan + 1)
    lo, hi = e[:-1, None], e[1:, None]
    xx = 0.5 * (hi - lo) * xg[None, :] + 0.5 * (hi + lo)
    integral = float(np.sum(0.5 * (hi - lo) * wg[None, :] * special.jv(2 * m, 2 * m * xx)))
    return q * q * C * beta / (2 * math.pi * EPS0 * rho ** 2) * (
        m * beta ** 2 * special.jvp(2 * m, 2 * m * beta) - m * m * (1 - beta ** 2) * integral)


__all__ = ["Worldline", "FunctionWorldline", "SampledWorldline", "Charge", "uniform", "circular", "harmonic",
           "hyperbolic", "retarded_time", "fields", "potentials", "heaviside_field", "larmor_power", "lienard_power",
           "angular_power", "critical_frequency", "bessel_k_tail", "synchrotron_F", "synchrotron_G",
           "synchrotron_power", "synchrotron_spectrum", "synchrotron_angular_spectrum", "harmonic_angular_power",
           "harmonic_power"]
