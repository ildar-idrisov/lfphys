# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Linear (Stokes) drag of a sphere and the closed forms of a flight with linear drag (plan M1; design
``lfphys/sources/explore_2026-11-14_design.md`` §4).

**Stokes's law.** A sphere of diameter d moving slowly at v through a fluid of dynamic viscosity mu feels

    F = -3 pi mu d v      (Stokes 1851, art. 42, eq. (126): "-F = 6 pi mu' rho a V", mu' = mu/rho, a the radius),

the exact force of the steady creeping (Stokes) flow, valid while the Reynolds number Re = rho |v| d / mu is small.
Its first correction (Oseen) multiplies it by (1 + 3 Re / 16) (Veysey & Goldenfeld, Rev. Mod. Phys. 79, 883 (2007),
eq. (39): C_D = (6 pi / R)[1 + 3R/8 + O(R^2)] with R = U a / nu = Re / 2), so the law's relative error is about
3 Re / 16 (``oseen_error``): 1.9 % at Re = 0.1, 19 % at Re = 1. The flight reports its Reynolds number along the path
(``Flight.reynolds``), and a world states the largest. The unsteady forces and the buoyancy are not included. The added
mass and the buoyancy are of order R = rho_fluid / rho_body (1.5e-4 for steel in air, 1.2e-3 for water in air).
Basset's history force is larger, of order sqrt(R), while the body accelerates: in the Maxey–Riley equation of a sphere
in the Stokes regime released from rest (Maxey & Riley, Phys. Fluids 26, 883 (1983), not read; the history term
6 a^2 sqrt(pi mu rho_fluid) int (dv/ds) / sqrt(t - s) ds, a the radius), in units of tau_p = m / (6 pi mu a) and
g tau_p, (1 + R/2) dv/dt = (1 - R) - v - 1.197 sqrt(R) int_0^t (dv/ds) / sqrt(t - s) ds; at t = tau_p it lowers the
speed by 1.4 % for steel and 3.9 % for a water droplet in air, as much as Oseen's error, and decays as t^(-1/2) towards
the terminal speed (review R-E F3; computed by product integration, converged in the step, and repeated by
tests/test_mechanics_projectile.py).

A linear drag F = -b v with b given directly (``LinearDrag(b)``) is the same equation; its physical basis is then the
caller's (it is used here as the reference problem with closed forms).

**Closed forms** (k = b / m, tau = 1 / k, the vertical last, g along -e_vert):

    v(t) = v0 e^{-t/tau} - g tau (1 - e^{-t/tau}) e_vert,
    r(t) = r0 + v0 tau (1 - e^{-t/tau}) - g tau [t - tau (1 - e^{-t/tau})] e_vert;

the apex at t_a = tau ln(1 + vy0 / (g tau)); the landing from a height h on y = y0 - h: with s = T / tau,
c = (vy0 + g tau) / (g tau), h' = h / (g tau^2), the landing condition h' + c (1 - e^{-s}) - s = 0 has the solution

    T = tau [c + h' + W0(-c e^{-(c + h')})]

(W0 the principal branch of Lambert's W; for h = 0 the other branch gives the start, s = 0). Derived for the design
(Appendix A) and checked there against DOP853 to 5e-15–8e-13; the tests repeat it. It holds for any c, also c <= 0 (a
launch downwards at or beyond the terminal speed: the argument of W0 is then >= 0; c = 0 is uniform motion at v_t, T =
h / v_t). The closed form alone loses digits when the drag is weak (s << 1): near the branch point W ~ -1 + sqrt(2 (1 +
e z)), and 1 + e z = O(s^2) is formed from terms of order 1, so a rounding of z moves s by ~1e-16 / s, a relative error
~1e-16 / s^2 (review R-E F2: 1e-8 at s = 1.4e-4, the Stokes drag of a 20 mm steel ball in air). So the root is polished
by Newton's method on

    f(s) = h' + c1 (1 - e^{-s}) - (s - (1 - e^{-s})),   f'(s) = c1 e^{-s} - (1 - e^{-s}),   c1 = c - 1 = vy0 / (g tau),

whose terms are formed without cancellation (c1 directly, the last bracket by its series): f is concave for c > 0 and
convex for c < 0, decreasing at the landing, so Newton's iterates from the right (c > 0) or the left (c < 0) of the root
converge monotonically; the start is W's value, or k T_vacuum (the vacuum landing time, longer than the flight with
drag for c > 0, shorter for c < 0) when W's value is not on the descending branch. Measured against a 50-digit
bisection: <= 8e-16 relative from s = 1e-5 to 10 (W alone: up to 7e-7; tests).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

from lfphys.i18n import T

from .. import data

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Linear (Stokes) drag of a sphere"),
    "statement": T("Stokes's law F = −3πμ·d·v for a sphere of diameter d in a fluid of viscosity μ (or a linear drag "
                   "F = −b·v with b given), as a declared force of the point-body flight; the Reynolds number ρ|v|d/μ "
                   "along the path; the closed forms of the flight with linear drag: x(t), y(t), the apex time and the "
                   "landing time from a height by Lambert's W; the air's density and viscosity from lfphys.core.data."),
    "validity": T("creeping flow: Re = ρ|v|d/μ ≲ 1; the law's relative error is about 3·Re/16 (Oseen's correction): "
                  "1.9 % at Re = 0.1, 19 % at Re = 1 — the run reports its Reynolds number; steady drag only: no added "
                  "mass and no buoyancy (of order ρ_fluid/ρ_body) and no Basset history force (of order "
                  "√(ρ_fluid/ρ_body) while the body accelerates: about 1.4 % of the speed for steel and 4 % for water "
                  "droplets in air one relaxation time after release, fading towards the terminal speed); a sphere far "
                  "from walls"),
    "basis": [T("Stokes, Trans. Cambridge Philos. Soc. 9, part II, [8] (1851), art. 42, eq. (126)"),
              T("Oseen, Ark. Mat. Astron. Fys. 6, no. 29 (1910); the drag correction 3·Re/16 as stated by Veysey & "
                "Goldenfeld, Rev. Mod. Phys. 79, 883 (2007), eq. (39)"),
              T("Lambert's W: Corless et al., Adv. Comput. Math. 5, 329 (1996) (scipy.special.lambertw)")],
    "conflicts": [],
}

#: the Reynolds number up to which a world may call the drag "Stokes" (the law's error ~ 3 Re / 16 there: 19 %)
STOKES_RE_MAX = 1.0


def oseen_error(re):
    """The relative size of Oseen's first correction to Stokes's law, 3 Re / 16: the law's error estimate."""
    return 3.0 * np.asarray(re, float) / 16.0


def air(T_C: float = 20.0, p: float = data.P_ATM) -> dict:
    """Dry air at T_C (deg C) and p (Pa): rho, mu, nu with the source (``lfphys.core.data.fluid_properties``; the U.S.
    Standard Atmosphere 1976 formulas). At 20 C and 101325 Pa: rho = 1.2041 kg/m^3, mu = 1.8134e-5 Pa s."""
    return data.fluid_properties("air", T_C, p)


class LinearDrag:
    """F = -b v (a declared force of ``fly``). With ``rho``, ``mu`` and ``diameter`` it also gives the Reynolds number
    rho |v| d / mu."""

    def __init__(self, b: float, *, rho: float | None = None, mu: float | None = None, diameter: float | None = None):
        if not (math.isfinite(b) and b >= 0):
            raise ValueError(T("the drag coefficient b must be finite and ≥ 0 (given {b})", b=float(b)))
        for v in (rho, mu, diameter):
            if v is not None and not (math.isfinite(v) and v > 0):
                raise ValueError(T("the fluid's density and viscosity and the diameter must be > 0"))
        self.b, self.rho, self.mu, self.diameter = float(b), rho, mu, diameter
        self.label = T("linear drag")

    @classmethod
    def stokes(cls, diameter: float, medium: dict | None = None) -> "LinearDrag":
        """Stokes's law for a sphere of the given diameter (m) in a medium {rho, mu} (default: air at 20 C)."""
        if not (math.isfinite(diameter) and diameter > 0):
            raise ValueError(T("the sphere's diameter must be > 0 (given {d} m)", d=float(diameter)))
        med = air() if medium is None else medium
        out = cls(3.0 * math.pi * med["mu"] * diameter, rho=med["rho"], mu=med["mu"], diameter=diameter)
        out.label = T("Stokes drag")
        return out

    def force(self, t, r, v):
        return -self.b * np.asarray(v, float)

    def k(self, mass: float) -> float:
        """b / m, 1/s."""
        return self.b / mass

    def tau(self, mass: float) -> float:
        """m / b, s: the relaxation time."""
        return mass / self.b

    def terminal_speed(self, mass: float, g: float) -> float:
        """m g / b (Stokes: m g / (3 pi mu d))."""
        return mass * g / self.b

    def reynolds(self, speed):
        if self.rho is None or self.mu is None or self.diameter is None:
            raise ValueError(T("the Reynolds number needs the fluid's density, viscosity and the diameter"))
        return self.rho * np.asarray(speed, float) * self.diameter / self.mu


def stokes_drag(diameter: float, medium: dict | None = None) -> LinearDrag:
    """``LinearDrag.stokes``."""
    return LinearDrag.stokes(diameter, medium)


def _one_minus_exp(s):
    """1 - e^{-s} without cancellation."""
    return -np.expm1(-s)


def _s_minus_one_minus_exp(s):
    """s - (1 - e^{-s}) = s^2/2 - s^3/6 + ..., by its series for s < 0.1 (no cancellation)."""
    s = np.asarray(s, float)
    out = s + np.expm1(-s)
    small = np.abs(s) < 0.1
    if np.any(small):
        x = s[small]
        acc, term = np.zeros_like(x), x.copy()
        for n in range(2, 20):  # term = (-1)^n s^n / n!
            term = -term * x / n
            acc += term
        out = np.where(small, 0.0, out)
        out[small] = -acc
    return out


def linear_drag_state(t, r0, v0, k: float, g: float):
    """Closed form with linear drag F = -m k v: (r(t), v(t)) for t scalar or array (rows)."""
    if not k > 0:
        raise ValueError(T("the drag rate k must be > 0"))
    tau = 1.0 / k
    t = np.asarray(t, float)
    s = (t / tau)[..., None]
    r0, v0 = np.asarray(r0, float), np.asarray(v0, float)
    e = np.zeros_like(r0)
    e[-1] = 1.0
    one = _one_minus_exp(s)
    r = r0 + v0 * tau * one - g * tau * tau * _s_minus_one_minus_exp(s) * e
    v = v0 * (1.0 - one) - g * tau * one * e
    return r, v  # (dim,) for a scalar t, (n, dim) for an array


def _landing_f(s: float, hp: float, c1: float) -> tuple[float, float]:
    """f(s) = h' + c1 (1 - e^{-s}) - (s - (1 - e^{-s})) and f'(s) = c1 e^{-s} - (1 - e^{-s}), without cancellation."""
    one = float(_one_minus_exp(s))
    return hp + c1 * one - float(_s_minus_one_minus_exp(np.array([s]))[0]), c1 * math.exp(-s) - one


def linear_drag_landing_time(h: float, vy0: float, k: float, g: float) -> float:
    """The landing time from a height h >= 0 with the vertical speed vy0 (h = 0 needs vy0 > 0), linear drag rate k:
    T = tau [c + h' + W0(-c e^{-(c + h')})], polished by Newton's method (module docstring; review R-E F2). Any vy0,
    also downwards at or beyond the terminal speed (c <= 0, review R-E F10)."""
    if not (k > 0 and g > 0 and h >= 0) or (h == 0 and not vy0 > 0):
        raise ValueError(T("the landing time needs k > 0, g > 0, h ≥ 0, and an upward speed when h = 0"))
    tau = 1.0 / k
    c1 = vy0 / (g * tau)
    c = 1.0 + c1
    hp = h / (g * tau * tau)
    w = special.lambertw(-c * math.exp(-(c + hp)), 0)
    s = float((c + hp + w).real)
    if not (math.isfinite(s) and s > 0 and _landing_f(s, hp, c1)[1] < 0):  # not on the descending branch
        s = k * (vy0 + math.sqrt(vy0 * vy0 + 2.0 * g * h)) / g if vy0 >= 0 else \
            k * 2.0 * h / (math.sqrt(vy0 * vy0 + 2.0 * g * h) - vy0)  # k T_vacuum
    for _ in range(60):  # quadratic convergence: 1-3 steps from W's value; monotone from k T_vacuum
        f, fp = _landing_f(s, hp, c1)
        if not fp < 0:
            break
        ds = f / fp
        s -= ds
        if abs(ds) <= 2.0 * np.finfo(float).eps * s:
            break
    return tau * s


def linear_drag_apex_time(vy0: float, k: float, g: float) -> float | None:
    """t_a = tau ln(1 + vy0 / (g tau)) for vy0 > 0, else None."""
    if not vy0 > 0:
        return None
    tau = 1.0 / k
    return tau * math.log1p(vy0 / (g * tau))
