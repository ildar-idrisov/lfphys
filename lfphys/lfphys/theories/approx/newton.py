# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Newtonian gravity of slow bodies: exact Kepler orbits about a central mass (an approximation of general relativity
for v << c and GM/(c^2 r) << 1; the relative corrections are of that order, e.g. the periapsis advance 6 pi GM /
(c^2 p) per orbit).

A body with position r0 and velocity v0 (unbound, E = v^2/2 - mu/r > 0) moves on a hyperbola
    r(theta) = p / (1 + e cos theta),   p = h^2/mu,  e = sqrt(1 + 2 E h^2 / mu^2),
with the time from periapsis  t = sqrt(a^3/mu) (e sinh H - H),  a = mu/(2E),
    tanh(H/2) = sqrt((e-1)/(e+1)) tan(theta/2).
Radial motion (h = 0) is integrated by quadrature of dt = dr / sqrt(2E + 2 mu/r).

``integrate_body`` integrates bound or unbound bodies (DOP853), checked against the exact conic.

Light as Newtonian corpuscles (Soldner 1804: half the measured deflection at every impact parameter) is not an
approximation but a refuted alternative: ``lfphys.theories.alternatives.newton_light`` (it uses the Kepler
crossings of this module; review 2026-10-23, E9).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate


ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": "Ньютоново тяготение медленных тел: орбиты Кеплера",
    "statement": "Движение тела в поле −GM r/r³: точные гиперболы и эллипсы Кеплера, численное интегрирование "
                 "с проверкой по коническому сечению.",
    "validity": "слабое поле и малые скорости: поправки порядка GM/(c²r) и v²/c² (смещение перицентра "
                "6πGM/(c²p) за оборот — 43″ в столетие у Меркурия)",
    "basis": ["Kepler/Newton"],
    "conflicts": ["lfphys.core.gravity.orbits: ОТО даёт прецессию перицентра и неустойчивость внутри 6GM/c²"],
}


def _elements(r0, v0, mu):
    r = math.hypot(*r0)
    v2 = float(v0 @ v0)
    h = float(r0[0] * v0[1] - r0[1] * v0[0])
    E = 0.5 * v2 - mu / r
    evec = ((v2 - mu / r) * r0 - float(r0 @ v0) * v0) / mu
    e = math.hypot(*evec)
    return r, h, E, evec, e


def crossings(r0, v0, mu, rT, r_abs):
    """All (t, position) with t > 0 where the orbit reaches radius rT before being absorbed (r < r_abs).
    Orbit must be unbound (E > 0)."""
    r0 = np.asarray(r0, float)
    v0 = np.asarray(v0, float)
    r, h, E, evec, e = _elements(r0, v0, mu)
    if E <= 0:
        raise ValueError("bound corpuscle orbit (E <= 0)")
    rdot = float(r0 @ v0) / r
    if abs(h) < 1e-14 * r * math.sqrt(float(v0 @ v0)):
        return _radial(r, rdot, E, mu, rT, r_abs, r0 / r)
    em1 = (2.0 * E * h * h / (mu * mu)) / (e + 1.0)  # e - 1 without cancellation
    if em1 < 1e-3:
        # nearly radial: the conic formulas lose precision as e -> 1 (review probe O); quadrature in r instead
        return _crossings_quad(r0, v0, mu, rT, r_abs, r, rdot, h, E)
    flip = h < 0
    if flip:  # mirror y so that the motion is counter-clockwise
        r0 = r0 * np.array([1.0, -1.0])
        v0 = v0 * np.array([1.0, -1.0])
        evec = evec * np.array([1.0, -1.0])
        h = -h
    p = h * h / mu
    a = mu / (2.0 * E)
    om = math.atan2(evec[1], evec[0])
    th0 = _wrap(math.atan2(r0[1], r0[0]) - om)
    th_inf = math.acos(-1.0 / e)
    k = math.sqrt((e - 1.0) / (e + 1.0))
    n = math.sqrt(a**3 / mu)

    def t_of(th):
        H = 2.0 * math.atanh(k * math.tan(0.5 * th))
        return n * (e * math.sinh(H) - H)

    r_peri = p / (1.0 + e)
    out = []
    c = (p / rT - 1.0) / e
    if abs(c) > 1.0:
        return out
    thT = math.acos(c)
    for th in (-thT, thT):
        if th <= th0 + 1e-10 or abs(th) >= th_inf:
            continue  # behind (or at) the start along the motion
        if th0 < 0 < th and r_peri < r_abs:
            continue  # absorbed at periapsis before reaching it
        dt = t_of(th) - t_of(th0)
        if dt <= 0:
            continue
        ang = th + om
        pos = rT * np.array([math.cos(ang), math.sin(ang)])
        if flip:
            pos = pos * np.array([1.0, -1.0])
        out.append((dt, pos, th > 0))  # th > 0: past periapsis, moving outward
    out.sort(key=lambda x: x[0])
    return out


def _radial(r, rdot, E, mu, rT, r_abs, rhat):
    """Radial unbound motion: outward crossings beyond r, inward crossings above the absorber (review R3: the
    inward case was missing and the quadrature tolerance was refused by scipy)."""
    if rdot >= 0:
        if rT <= r:
            return []
        lo, hi, out = r, rT, True
    else:
        if not (r_abs < rT < r):
            return []
        lo, hi, out = rT, r, False
    dt = integrate.quad(lambda x: 1.0 / math.sqrt(2.0 * E + 2.0 * mu / x), lo, hi, epsabs=0.0, epsrel=1e-13,
                        limit=200)[0]
    return [(dt, rT * rhat, out)]


def _crossings_quad(r0, v0, mu, rT, r_abs, r, rdot, h, E):
    """Crossings of radius rT by quadrature of dt = dr/sqrt(g), dphi = h dr/(r^2 sqrt g), g = 2E + 2mu/r - h^2/r^2,
    with r = r_p + s^2 (r_p periapsis, stable form h^2/(mu + sqrt(mu^2 + 2E h^2))), which keeps the integrands smooth:
    dt = 2 r ds / sqrt(2E (r - r_m)),  dphi = 2 h ds / (r sqrt(2E (r - r_m))),  r_m the negative root."""
    disc = math.sqrt(mu * mu + 2.0 * E * h * h)
    r_p = h * h / (mu + disc)
    r_m = -(mu + disc) / (2.0 * E)
    q = dict(epsabs=0.0, epsrel=1e-12, limit=200)

    def seg(ra, rb):  # ra < rb, both >= r_p
        sa, sb = math.sqrt(max(ra - r_p, 0.0)), math.sqrt(max(rb - r_p, 0.0))
        k = math.sqrt(2.0 * E)
        dt = integrate.quad(lambda x: 2.0 * (r_p + x * x) / (k * math.sqrt(r_p + x * x - r_m)), sa, sb, **q)[0]
        dp = integrate.quad(lambda x: 2.0 * abs(h) / ((r_p + x * x) * k * math.sqrt(r_p + x * x - r_m)), sa, sb, **q)[0]
        return dt, dp

    phi0 = math.atan2(r0[1], r0[0])
    sgn = 1.0 if h > 0 else -1.0
    out = []
    if rdot >= 0:
        if rT > r:
            dt, dp = seg(r, rT)
            out.append((dt, dp, True))
    else:
        if r_abs < rT < r:
            dt, dp = seg(rT, r)
            out.append((dt, dp, False))
        if r_p >= r_abs and rT > r_p:
            dt1, dp1 = seg(r_p, r)
            dt2, dp2 = seg(r_p, rT)
            out.append((dt1 + dt2, dp1 + dp2, True))
    res = []
    for dt, dp, outward in out:
        ang = phi0 + sgn * dp
        res.append((dt, rT * np.array([math.cos(ang), math.sin(ang)]), outward))
    res.sort(key=lambda x: x[0])
    return res


def _wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def integrate_body(r0, v0, gm: float, t_end: float, n_out: int = 2000, r_stop: float = 0.0):
    """A massive body in the Newtonian field -GM r/r^3 (plane), DOP853 with relative tolerance 1e-12; stops at
    r = r_stop (a body's surface). Returns dict(t, x, y, vx, vy, status). The exact conic is the independent check
    (``_elements``)."""
    def rhs(t, y):
        x, yy, vx, vy = y
        r3 = (x * x + yy * yy) ** 1.5
        return [vx, vy, -gm * x / r3, -gm * yy / r3]

    def hit(t, y):
        return math.hypot(y[0], y[1]) - r_stop
    hit.terminal = True
    sol = integrate.solve_ivp(rhs, (0.0, t_end), [r0[0], r0[1], v0[0], v0[1]], method="DOP853", rtol=1e-12,
                              atol=1e-12 * max(1.0, math.hypot(*r0)), dense_output=True,
                              events=hit if r_stop > 0 else None)
    t = np.linspace(0.0, sol.t[-1], n_out)
    Y = sol.sol(t)
    status = "hit" if (r_stop > 0 and sol.t_events[0].size) else "running"
    return {"t": t, "x": Y[0], "y": Y[1], "vx": Y[2], "vy": Y[3], "status": status}


def integrate_body_regularized(r0, v0, gm: float, t_end: float, n_out: int = 2000, r_stop: float = 0.0):
    """``integrate_body`` with the Levi-Civita regularisation (same arguments and result).

    Levi-Civita regularisation (Stiefel & Scheifele, Linear and Regular Celestial Mechanics, 1971): with
    x + iy = u^2 and dt = r dtau the Kepler problem becomes the harmonic oscillator u'' = (E/2) u, E the (conserved)
    energy per mass, smooth through any periapsis (a radial orbit bounces through the centre: the regularised
    collision). Integrated by DOP853 (relative tolerance 1e-12); the output times are found on the dense solution by
    inverting t(tau) (monotonic, dt/dtau = r) with two Newton steps. In coordinate time the energy error at a deep
    periapsis (r_peri ~ 1e-6 a) reached ~1e-5 of |E| (review of v04, 2026-10-23, V4-4); here the energy holds to
    1e-9 of |E| and the periapsis timing to 5e-9 of the period at e = 0.999999 (tests). v04 still uses
    ``integrate_body`` (its checks are tuned to it; STATUS.md V19)."""
    r0 = np.asarray(r0, float)
    v0 = np.asarray(v0, float)
    rn = math.hypot(*r0)
    z0 = complex(r0[0], r0[1])
    u0 = np.sqrt(z0)
    p0 = rn * complex(v0[0], v0[1]) / (2.0 * u0)  # du/dtau = r v / (2 u)
    E = 0.5 * float(v0 @ v0) - gm / rn
    half = 0.5 * E

    def rhs(tau, y):
        return [y[2], y[3], half * y[0], half * y[1], y[0] * y[0] + y[1] * y[1]]

    def done(tau, y):
        return y[4] - t_end
    done.terminal = True

    def hit(tau, y):
        return y[0] * y[0] + y[1] * y[1] - r_stop
    hit.terminal = True
    hit.direction = -1
    _, h, _, _, e = _elements(r0, v0, gm)
    r_min = (-gm / (2 * E)) * (1 - e) if E < 0 else (h * h / (gm * (1 + e)) if h != 0 else 0.0)
    r_floor = max(r_min, r_stop, 1e-12 * rn)
    ut, pt = abs(u0), max(abs(p0), math.sqrt(abs(half)) * abs(u0), 1e-300)
    sol = integrate.solve_ivp(rhs, (0.0, 4.0 * t_end / r_floor + 10.0), [u0.real, u0.imag, p0.real, p0.imag, 0.0],
                              method="DOP853", rtol=1e-12, atol=1e-15 * np.array([ut, ut, pt, pt, max(t_end, 1e-300)]),
                              dense_output=True, events=[done, hit] if r_stop > 0 else [done])
    hit_ = r_stop > 0 and sol.t_events[1].size > 0
    t = np.linspace(0.0, min(t_end, float(sol.y[4, -1])), n_out)
    tg_s = np.linspace(0.0, sol.t[-1], max(20 * len(sol.t), 2000))
    sk = np.interp(t, sol.sol(tg_s)[4], tg_s)
    for _ in range(2):
        Y = sol.sol(sk)
        rk = Y[0] ** 2 + Y[1] ** 2
        sk = np.clip(sk - (Y[4] - t) / np.maximum(rk, 1e-300), 0.0, sol.t[-1])
    Y = sol.sol(sk)
    u = Y[0] + 1j * Y[1]
    pu = Y[2] + 1j * Y[3]
    z = u * u
    v = 2.0 * u * pu / np.maximum(np.abs(u) ** 2, 1e-300)  # dz/dt = (dz/dtau) / r
    return {"t": t, "x": z.real, "y": z.imag, "vx": v.real, "vy": v.imag, "status": "hit" if hit_ else "running"}
