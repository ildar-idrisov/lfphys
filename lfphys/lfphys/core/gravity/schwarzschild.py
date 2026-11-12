# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Exact light connections in the Schwarzschild exterior by quadrature (independent of the RK fans in light.py).

For a null geodesic with impact parameter b (E = 1, L = b) in the equatorial plane,

    dphi/dr = +- b / (r^2 sqrt(g)),     c dt/dr = +- 1 / (f sqrt(g)),     g(r) = 1 - f b^2 / r^2,  f = 1 - rs/r.

g = P(r)/r^3 with P(r) = r^3 - b^2 r + b^2 rs. For b > b_c = (3 sqrt 3 / 2) rs the largest root r_tp of P is the
turning point and P = (r - r_tp) Q(r), Q = r^2 + r_tp r + r_tp^2 - b^2 > 0 for r >= r_tp; the substitution
r = r_tp + s^2 removes the square-root singularity:

    dphi = 2 b ds / sqrt(r Q),          c dt = 2 r^{3/2} ds / (f sqrt(Q)).

For b <= b_c (no turning point outside the photon sphere) the substitution u = ln r is used.

``connect(P1, P2)`` finds the geodesics from a static point P1 to a static point P2 that sweep the angle
Delta (counter-clockwise) or 2 pi - Delta (clockwise): the primary and the secondary image. Rays that would pass
below the absorbing radius (body surface or horizon) do not exist. Both coordinate travel time and the local
directions of emission and arrival (static orthonormal frames) are returned.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from scipy import integrate, optimize

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Шварцшильд: нулевые геодезические",
    "statement": "Свет вне сферически-симметричного тела в ОТО: орбиты с прицельным параметром b, отклонение, время "
                 "прихода, соединение двух точек геодезическими (первичный и вторичный образ) — точные квадратуры.",
    "validity": "вне тела (r > R), невращающееся тело; вращение — lfphys.core.gravity.kerr",
    "basis": ["Schwarzschild 1916",
              "отклонение радиоволн Солнцем (VLBI): γ − 1 = (−1.6 ± 1.5)·10⁻⁴ (Lambert & Le Poncin-Lafitte 2009, "
              "по Will 2014)",
              "Cassini (доплеровский сдвиг частоты, относят к задержке Шапиро): γ − 1 = (2.1 ± 2.3)·10⁻⁵ "
              "(Bertotti, Iess, Tortora 2003)"],
    "conflicts": [],
}

_Q = dict(epsabs=0.0, epsrel=1e-13, limit=400)
SQ3 = math.sqrt(3.0)


def b_crit(rs: float) -> float:
    return 1.5 * SQ3 * rs


def turning_point(b: float, rs: float) -> float:
    """Largest root of r^3 - b^2 r + b^2 rs (requires b >= b_c)."""
    if rs == 0.0:
        return b
    x = -1.5 * SQ3 * rs / b
    x = max(-1.0, min(1.0, x))
    return (2.0 * b / SQ3) * math.cos(math.acos(x) / 3.0)


def b_of_turning(r_tp: float, rs: float) -> float:
    """Impact parameter whose turning point is r_tp: b = r / sqrt(f)."""
    return r_tp / math.sqrt(1.0 - rs / r_tp)


def _pieces(a: float, b: float, ratio: float = 4.0):
    """Split [a, b] (0 < a < b) geometrically so that quad sees moderate ranges."""
    pts = [a]
    while pts[-1] * ratio < b:
        pts.append(pts[-1] * ratio)
    pts.append(b)
    return list(zip(pts[:-1], pts[1:]))


def integrals(b: float, ra: float, rb: float, rs: float, c: float, rtp: float | None = None):
    """(Delta phi, Delta t) along a monotonic stretch ra -> rb (ra < rb) with impact parameter b.
    ``rtp``: the turning point (<= ra) if b > b_c; then the s-substitution is used."""
    if rb <= ra:
        return 0.0, 0.0
    if rtp is not None:
        def r_of(s):
            return rtp + s * s

        def dphi(s):
            r = r_of(s)
            Q = r * r + rtp * r + rtp * rtp - b * b
            return 2.0 * b / math.sqrt(r * Q)

        def dct(s):
            r = r_of(s)
            Q = r * r + rtp * r + rtp * rtp - b * b
            f = 1.0 - rs / r
            return 2.0 * r**1.5 / (f * math.sqrt(Q))

        phi = ct = 0.0
        # near b_c the integrand peaks at s ~ sqrt(Q(r_tp)) (Q(r_tp) = 3 r_tp^2 - b^2 -> 0): break points on a
        # geometric ladder towards s = 0 let quad resolve the logarithmic peak
        q0 = max(3.0 * rtp * rtp - b * b, 0.0)
        for x0, x1 in _pieces(max(ra, rtp), rb):
            s0 = math.sqrt(max(x0 - rtp, 0.0))
            s1 = math.sqrt(x1 - rtp)
            if s1 <= s0:
                continue
            pts = None
            if s0 == 0.0 and q0 < 1e-2 * rtp * rtp:
                pts = [s1 * 10.0 ** (-k) for k in range(1, 14)]
            kw = dict(_Q, points=pts) if pts else _Q
            phi += integrate.quad(dphi, s0, s1, **kw)[0]
            ct += integrate.quad(dct, s0, s1, **kw)[0]
        return phi, ct / c

    def g(r):
        return 1.0 - (1.0 - rs / r) * b * b / (r * r)

    def dphi_u(u):
        r = math.exp(u)
        return b / (r * math.sqrt(g(r)))

    def dct_u(u):
        r = math.exp(u)
        return r / ((1.0 - rs / r) * math.sqrt(g(r)))

    phi = ct = 0.0
    for x0, x1 in _pieces(ra, rb):
        u0, u1 = math.log(x0), math.log(x1)
        if b > 0:
            phi += integrate.quad(dphi_u, u0, u1, **_Q)[0]
        ct += integrate.quad(dct_u, u0, u1, **_Q)[0]
    return phi, ct / c


def _polar(P):
    return float(math.hypot(P[0], P[1])), float(math.atan2(P[1], P[0]))


class _Family:
    """Rays from radius r1 towards radius r2; branches parametrised by b (see module docstring)."""

    def __init__(self, r1, r2, rs, c, r_abs):
        self.r1, self.r2, self.rs, self.c, self.r_abs = r1, r2, rs, c, r_abs
        self.bc = b_crit(rs)
        self.b_tan1 = b_of_turning(r1, rs)
        # smallest b that still turns above the absorber
        b_abs = b_of_turning(r_abs, rs) if r_abs > 1.5 * rs else self.bc
        self.b_lo = max(self.bc, b_abs)
        self.lo_open = self.b_lo == self.bc  # Phi -> infinity there
        self.cache = {}

    def _rtp(self, b):
        return turning_point(b, self.rs) if b > self.bc else None

    def direct(self, b):
        """No turning point between: (phi, t) from min(r1,r2) to max(r1,r2)."""
        ra, rb = min(self.r1, self.r2), max(self.r1, self.r2)
        rtp = self._rtp(b)
        if rtp is not None and rtp > ra * (1 + 1e-15):
            return None
        return integrals(b, ra, rb, self.rs, self.c, rtp)

    def turned(self, rtp):
        """Ingoing from r1, turning at r_tp, then out to r2 (or in-out to r2 < r1 second crossing). Parametrised by the
        turning point (well conditioned near b_c, review R19); returns (phi, t, b)."""
        if rtp < self.r_abs or rtp > min(self.r1, self.r2) * (1 + 1e-15):
            return None
        b = b_of_turning(rtp, self.rs)
        p1, t1 = integrals(b, rtp, self.r1, self.rs, self.c, rtp)
        p2, t2 = integrals(b, rtp, self.r2, self.rs, self.c, rtp)
        return p1 + p2, t1 + t2, b


def connect(P1, P2, rs: float, c: float, r_abs: float):
    """Null geodesics from static point P1 to static point P2 (Schwarzschild coordinates as x-y).

    Returns a list of images (dicts), sorted by travel time:
    side (+1 ccw, -1 cw), b, branch, dt, emit_dir (unit, local static frame at P1, Cartesian components),
    arrive_dir (unit propagation direction at P2, local static frame)."""
    r1, f1 = _polar(P1)
    r2, f2 = _polar(P2)
    if min(r1, r2) <= max(r_abs, 1.5 * rs if rs > 0 else 0.0):
        return []
    fam = _Family(r1, r2, rs, c, r_abs)
    delta = (f2 - f1) % (2.0 * math.pi)
    out = []
    for side, theta in ((+1, delta), (-1, 2.0 * math.pi - delta)):
        img = _solve_side(fam, theta)
        if img is None:
            continue
        b, branch, dt = img
        out.append(_image(P1, P2, r1, r2, rs, side, b, branch, dt))
    # the two sides are distinct (mirror) paths even when they take equal time (a symmetric lens)
    return sorted(out, key=lambda d: d["dt"])


def _solve_side(fam: _Family, theta: float):
    """Find b with swept angle == theta along the continuous family; return (b, branch, dt) or None."""
    r1, r2 = fam.r1, fam.r2
    if theta < 1e-14:
        d = fam.direct(0.0)
        return (0.0, "out" if r2 >= r1 else "in", d[1]) if d is not None else None
    if r2 >= r1:
        # branch A: outgoing direct, b in [0, b_tan1]; Phi increasing
        b_top = fam.b_tan1
        phiA_top = fam.direct(b_top * (1 - 1e-15))
        if phiA_top is not None and theta <= phiA_top[0]:
            b = optimize.brentq(lambda bb: fam.direct(bb)[0] - theta, 0.0, b_top * (1 - 1e-15),
                                xtol=1e-14 * b_top, rtol=1e-15, maxiter=200)
            return b, "out", fam.direct(b)[1]
        b_join = b_top
    else:
        # branch C: ingoing direct first crossing, b in [0, b*(r2)]
        b_star = b_of_turning(r2, fam.rs)
        if b_star > fam.b_tan1:
            b_star = fam.b_tan1
        phiC_top = fam.direct(b_star * (1 - 1e-15))
        if phiC_top is not None and theta <= phiC_top[0]:
            b = optimize.brentq(lambda bb: fam.direct(bb)[0] - theta, 0.0, b_star * (1 - 1e-15),
                                xtol=1e-14 * b_star, rtol=1e-15, maxiter=200)
            return b, "in", fam.direct(b)[1]
        b_join = b_star
    # turned branch: turning point from r_join (= r1 or r2) down to the photon sphere or the absorber;
    # Phi increases as the turning point decreases
    if b_join <= fam.b_lo:
        return None
    r_join = r1 if r2 >= r1 else r2
    # 1e-9 above the photon sphere the swept angle already exceeds 2 pi by far (log divergence)
    r_bottom = 1.5 * fam.rs * (1 + 1e-9) if fam.lo_open else max(fam.r_abs, 1.5 * fam.rs * (1 + 1e-9))
    if r_join <= r_bottom:
        return None
    # the bracket end next to the photon sphere only needs the sign of Phi - theta (Phi there is ~20 rad); its
    # quadrature cannot reach 1e-13 and says so - that warning is expected and silenced here only
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", integrate.IntegrationWarning)
        tb = fam.turned(r_bottom)
    if tb is None or theta > tb[0]:
        return None

    def F(rr):
        # brentq probes the bracket end next to the photon sphere too: the same expected warning as above
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", integrate.IntegrationWarning)
            v = fam.turned(rr)
        return (v[0] if v is not None else math.inf) - theta

    r_hi = r_join * (1 - 1e-15)
    if F(r_hi) > 0:  # theta below the join value (numerical edge): take the join
        v = fam.turned(r_hi)
        return v[2], "turned", v[1]
    rr = optimize.brentq(F, r_bottom, r_hi, xtol=1e-15 * r_join, rtol=1e-15, maxiter=300)
    v = fam.turned(rr)
    return v[2], "turned", v[1]


def _image(P1, P2, r1, r2, rs, side, b, branch, dt):
    def local(P, r, outgoing):
        f = 1.0 - rs / r
        s = min(1.0, b * math.sqrt(f) / r)
        cr = math.sqrt(max(0.0, 1.0 - s * s)) * (1.0 if outgoing else -1.0)
        rhat = np.array(P) / r
        phat = np.array([-rhat[1], rhat[0]])
        return cr * rhat + side * s * phat

    emit_out = branch == "out"
    arrive_out = branch in ("out", "turned")
    return {"side": side, "b": b, "branch": branch, "dt": dt,
            "emit_dir": local(P1, r1, emit_out), "arrive_dir": local(P2, r2, arrive_out)}


def deflection_from_quadrature(b: float, rs: float, c: float = 1.0) -> float:
    """Total deflection of a ray from infinity to infinity: 2 * Delta phi(r_tp -> inf) - pi (quadrature,
    used as the reference for the RK fans; ``checks.darwin_deflection`` is the closed form). The subtraction
    2 Delta phi - pi cancels for weak deflection: measured relative error (review 2026-10-23, E14; 40-digit
    reference) <= 1e-14 for 2.6 <= b/rs <= 50, 1.1e-11 at 1e5, 9e-11 at the solar limb (2.4e5), 1.3e-10 at 1e7,
    1.4e-7 at 1e9. For b/rs >> 1e5 use the weak-field series (``lfphys.theories.approx.ppn``) or
    ``lfphys.core.certified.schwarzschild_deflection``."""
    rtp = turning_point(b, rs)
    phi, _ = integrals(b, rtp, rtp * 1e12, rs, c, rtp)
    # tail beyond 1e12 r_tp: dphi ~ b/r^2 dr -> b / R
    phi += b / (rtp * 1e12)
    return 2.0 * phi - math.pi
