# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Massive bodies in the Schwarzschild exterior: timelike geodesics in the equatorial plane.

Units: geometric internally (G = c = 1, lengths in units of M = GM/c^2); the functions take SI and convert. A body has
specific energy e (E / m c^2) and specific angular momentum l (L / m, in units of M c), conserved:

    (dr/dtau)^2 = e^2 - (1 - 2M/r)(1 + l^2/r^2),    dphi/dtau = l / r^2,    dt/dtau = e / (1 - 2M/r).

With u = M/r the orbit obeys (du/dphi)^2 = f(u) = 2u^3 - u^2 + 2u/l^2 + (e^2 - 1)/l^2 (l in units of M) and
u'' = 1/l^2 - u + 3u^2. For a bound orbit f = 2 (u - u1)(u - u2)(u - u3) with u1 < u2 < u3, and the angle from
apoapsis to periapsis is an elliptic integral:

    Delta phi(apo -> peri) = 2 K(m) / sqrt(2 (u3 - u1)),   m = (u2 - u1) / (u3 - u1),

so the periapsis advances by 4 K(m)/sqrt(2(u3 - u1)) - 2 pi per orbit (exact). Circular orbits: l^2 = r^2/(r - 3),
e^2 = (r - 2)^2 / (r (r - 3)) (r in M); the innermost stable one at r = 6M, the photon sphere at 3M, the marginally
bound orbit at 4M. Initial data from what a static observer measures (local speed v, direction): e = gamma sqrt(1 - 2M/r),
l = gamma v_phi r.
"""

from __future__ import annotations

import math

import mpmath as mp
import numpy as np
from scipy import integrate, special

from ..constants import C

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Орбиты тел в поле Шварцшильда (времениподобные геодезические)",
    "statement": "Сохраняются удельные энергия e и момент l; уравнение орбиты u'' = 1/l² − u + 3u²; смещение "
                 "перицентра — точный эллиптический интеграл; круговые орбиты, ISCO 6M, фотонная сфера 3M, "
                 "собственное и координатное время вдоль орбиты.",
    "validity": "пробное тело вне невращающегося сферического тела (r > R, r > 2M)",
    "basis": ["Schwarzschild 1916", "Hagihara 1931 (эллиптические интегралы геодезических)",
              "смещение перигелия Меркурия 42.98″/век (Will, Living Rev. Relativ. 17, 4 (2014))",
              "пульсар PSR B1913+16 (Weisberg & Huang, ApJ 829, 55 (2016)) проверяет динамику двух тел (1PN с "
              "полной массой, излучение), а не орбиту пробной частицы; она — в core.gravity.pn_binary (с B5)"],
    "conflicts": [],
}


def mass_length(gm: float) -> float:
    """M = GM/c^2 in metres."""
    return gm / C**2


def from_local_velocity(r_over_m: float, v_r: float, v_phi: float) -> tuple[float, float]:
    """(e, l/M) from the velocity measured by the static observer at r (fractions of c): e = gamma sqrt(1 - 2M/r),
    l = gamma v_phi r."""
    v2 = v_r * v_r + v_phi * v_phi
    if v2 >= 1.0:
        raise ValueError("local speed must be below c")
    f = 1.0 - 2.0 / r_over_m
    if f <= 0:
        raise ValueError("inside the horizon")
    g = 1.0 / math.sqrt(1.0 - v2)
    return g * math.sqrt(f), g * v_phi * r_over_m


def circular(r_over_m: float) -> tuple[float, float]:
    """(e, l/M) of the circular geodesic at r (r > 3M)."""
    r = r_over_m
    if r <= 3.0:
        raise ValueError("no circular timelike orbit at r <= 3M")
    return (r - 2.0) / math.sqrt(r * (r - 3.0)), r / math.sqrt(r - 3.0)


def _em1(e: float, em1: float | None) -> float:
    """e^2 - 1, given directly or formed from e. Formed from e it carries an absolute error ~eps, i.e. a relative error
    ~eps/|e^2 - 1| (Mercury: 5.7e-9); pass it directly when it is known without cancellation, e.g. from
    gamma^2 (v^2 - 2M/r) (lfphys.core.gravity.orbit_stream.local_velocity_to_constants)."""
    return (e * e - 1.0) if em1 is None else float(em1)


def turning_points(e: float, l: float, em1: float | None = None) -> np.ndarray:
    """Real roots of f(u) = 2u^3 - u^2 + 2u/l^2 + (e^2 - 1)/l^2, ascending (u = M/r).

    em1 = e^2 - 1 may be given directly (see ``_em1``). A pair that np.roots returns as complex conjugates with an
    imaginary part below 1e-6 of the real part is a double root split by rounding (a nearly circular orbit) and is
    returned as two equal real roots; real roots are polished by safeguarded Newton steps on f."""
    em1 = _em1(e, em1)
    c = (2.0, -1.0, 2.0 / l**2, em1 / l**2)
    with mp.workdps(30):  # the roots of the float-coefficient cubic, exact to the digits kept
        try:
            zs = [complex(z) for z in mp.polyroots([mp.mpf(x) for x in c], maxsteps=200, extraprec=200)]
        except mp.NoConvergence:  # pragma: no cover - fallback
            zs = list(np.roots(c))
    out = [z.real for z in zs if abs(z.imag) <= 1e-6 * abs(z.real)]
    return np.array(sorted(out))


def turning_conditioning(e: float, l: float, em1: float | None = None) -> np.ndarray:
    """For each real turning point u_i: eps-free conditioning S(u_i)/(|f'(u_i)| u_i), S = the sum of |terms| of f.
    A change of the coefficients by a relative eps (their rounding) moves the root by ~eps times this, relative;
    it grows where two turning points come together (near the ISCO, nearly circular orbits)."""
    em1 = _em1(e, em1)
    u = turning_points(e, l, em1)
    out = []
    for i, ui in enumerate(u):
        fp = 2.0 * np.prod([ui - uj for j, uj in enumerate(u) if j != i]) if len(u) == 3 else 0.0
        S = 2.0 * ui**3 + ui * ui + 2.0 * ui / l**2 + abs(em1) / l**2
        out.append(S / (abs(fp) * ui) if fp else math.inf)
    return np.array(out)


def periapsis_advance(e: float, l: float, em1: float | None = None) -> float:
    """Advance of the periapsis per radial period (radians), exact (elliptic integral). Bound orbits only; at a
    double root (circular orbit) the epicyclic limit 2 pi/sqrt(1 - 6M/r) - 2 pi."""
    em1 = _em1(e, em1)
    u = turning_points(e, l, em1)
    if len(u) != 3 or not (u[0] > 0 and em1 < 0.0):
        raise ValueError("not a bound orbit with two turning points")
    return advance_from_turning(u[0], u[1])


def advance_from_turning(u_apo: float, u_peri: float) -> float:
    """The same from the two turning points (u = M/r): the third root is u3 = 1/2 - u_apo - u_peri (the roots of
    f sum to 1/2). u_apo = u_peri (a circular orbit) gives the epicyclic limit."""
    u1, u2 = u_apo, u_peri
    u3 = 0.5 - u1 - u2
    if not (0 < u1 <= u2 < u3):
        raise ValueError("turning points do not bound a stable orbit")
    m = (u2 - u1) / (u3 - u1)
    return 4.0 * special.ellipk(m) / math.sqrt(2.0 * (u3 - u1)) - 2.0 * math.pi


def elements(e: float, l: float, em1: float | None = None) -> dict:
    """Periapsis and apoapsis (in M), the semi-latus rectum p and eccentricity epsilon defined from the turning
    points (u_peri + u_apo = 2/p, epsilon = (u_peri - u_apo)/(u_peri + u_apo))."""
    u = turning_points(e, l, em1)
    if len(u) != 3:
        raise ValueError("not a bound orbit with two turning points")
    u1, u2 = u[0], u[1]
    return {"r_apo": 1.0 / u1, "r_peri": 1.0 / u2, "p": 2.0 / (u1 + u2), "ecc": (u2 - u1) / (u2 + u1)}


def radial_period(e: float, l: float, em1: float | None = None, n: int = 64) -> dict:
    """Coordinate and proper time of one radial period (periapsis to periapsis) of a bound orbit, by quadrature of
    dtau = dr/sqrt(R), dt = e dr/((1 - 2M/r) sqrt(R)) with R = l^2 f(u) = 2 l^2 (u - u1)(u - u2)(u - u3). With
    u = u1 + (u2 - u1) sin^2 chi the integrands are smooth:

        tau_r = 4 int_0^{pi/2} dchi / (u^2 |l| sqrt(2 (u3 - u))),   t_r = the same with e/(1 - 2u),

    evaluated by Gauss-Legendre with n nodes on each of 4 panels (no differential equation)."""
    u = turning_points(e, l, em1)
    if len(u) != 3 or not u[0] > 0:
        raise ValueError("not a bound orbit with two turning points")
    u1, u2 = u[0], u[1]
    u3 = 0.5 - u1 - u2
    x, w = np.polynomial.legendre.leggauss(n)
    edges = np.linspace(0.0, 0.5 * math.pi, 5)
    tau = t = 0.0
    for a, b in zip(edges[:-1], edges[1:]):
        chi = 0.5 * (b - a) * x + 0.5 * (b + a)
        uu = u1 + (u2 - u1) * np.sin(chi) ** 2
        g = 4.0 / (uu * uu * abs(l) * np.sqrt(2.0 * (u3 - uu)))
        tau += 0.5 * (b - a) * float(np.sum(w * g))
        t += 0.5 * (b - a) * float(np.sum(w * g * e / (1.0 - 2.0 * uu)))
    return {"t": t, "tau": tau}


def advance_series(p_over_m: float, ecc: float, order: int = 2) -> float:
    """Weak-field expansion of the exact advance in mu = M/p (p, ecc from the turning points as in ``elements``):
    6 pi mu [1 + (18 + ecc^2)/4 mu + (5/12)(54 + 9 ecc^2) mu^2], truncated after ``order`` terms (1..3). The first
    term is the PPN value at gamma = beta = 1; the coefficients follow from the binomial series of the exact
    chi-integral (tests: the residual of each truncation falls with the next power of mu)."""
    mu = 1.0 / p_over_m
    terms = [1.0, (18.0 + ecc * ecc) / 4.0 * mu, 5.0 / 12.0 * (54.0 + 9.0 * ecc * ecc) * mu * mu]
    if not 1 <= order <= 3:
        raise ValueError("order 1..3")
    return 6.0 * math.pi * mu * sum(terms[:order])


def advance_weak_field(p_over_m: float) -> float:
    """Leading weak-field periapsis advance 6 pi M / p (the textbook formula; a reference, not the engine)."""
    return 6.0 * math.pi / p_over_m


def integrate_orbit(e: float, l: float, u0: float, sign_du: float, phi_max: float, n_out: int = 2000,
                    u_stop: float = 0.5 * (1 - 1e-9), rtol: float = 1e-12):
    """Orbit from u0 = M/r0 with du/dphi of the given sign, integrated in phi (u'' = 1/l^2 - u + 3u^2, DOP853)
    together with t and tau (in units of M/c): dt/dphi = e r^2/(l (1 - 2/r)), dtau/dphi = r^2/l. Stops at the
    horizon (u = 1/2) or at u -> 0 (escape). Returns dict(phi, r, t, tau, status)."""
    if l == 0:
        raise ValueError("radial orbits: use integrate_radial")
    f0 = 2 * u0**3 - u0**2 + 2 * u0 / l**2 + (e * e - 1) / l**2
    du0 = sign_du * math.sqrt(max(f0, 0.0))

    def rhs(phi, y):
        u, w, t, tau = y
        r = 1.0 / u
        return [w, 1.0 / l**2 - u + 3.0 * u * u, e * r * r / (l * (1.0 - 2.0 * u)), r * r / l]

    def hit_horizon(phi, y):
        return y[0] - u_stop
    hit_horizon.terminal = True

    def escape(phi, y):
        return y[0] - 1e-9
    escape.terminal = True

    sol = integrate.solve_ivp(rhs, (0.0, phi_max), [u0, du0, 0.0, 0.0], method="DOP853", rtol=rtol, atol=1e-14,
                              dense_output=True, events=(hit_horizon, escape))
    phi = np.linspace(0.0, sol.t[-1], n_out)
    Y = sol.sol(phi)
    status = "horizon" if sol.t_events[0].size else "escape" if sol.t_events[1].size else "running"
    return {"phi": phi, "r": 1.0 / Y[0], "t": Y[2], "tau": Y[3], "status": status}


def integrate_radial(e: float, r0: float, v_sign: float, tau_max: float, n_out: int = 2000):
    """Radial geodesic (l = 0) from r0 (in M): d^2r/dtau^2 = -1/r^2 (exact in proper time), dt/dtau = e/(1 - 2/r).
    Stops at the horizon (in coordinate time it is reached only asymptotically)."""
    rdot0 = v_sign * math.sqrt(max(e * e - (1.0 - 2.0 / r0), 0.0))

    def rhs(tau, y):
        r, rd, t = y
        return [rd, -1.0 / (r * r), e / (1.0 - 2.0 / r)]

    def hit(tau, y):
        return y[0] - 2.0 * (1 + 1e-6)
    hit.terminal = True
    sol = integrate.solve_ivp(rhs, (0.0, tau_max), [r0, rdot0, 0.0], method="DOP853", rtol=1e-12, atol=1e-14,
                              dense_output=True, events=hit)
    tau = np.linspace(0.0, sol.t[-1], n_out)
    Y = sol.sol(tau)
    return {"tau": tau, "r": Y[0], "t": Y[2], "status": "horizon" if sol.t_events[0].size else "running"}


def to_si(gm: float, r_over_m=None, t_over_m=None):
    """Convert lengths (r/M -> m) and times (t in M/c -> s)."""
    M = mass_length(gm)
    out = []
    if r_over_m is not None:
        out.append(np.asarray(r_over_m) * M)
    if t_over_m is not None:
        out.append(np.asarray(t_over_m) * M / C)
    return out[0] if len(out) == 1 else tuple(out)

