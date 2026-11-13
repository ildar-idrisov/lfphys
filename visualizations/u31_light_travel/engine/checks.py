# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Reference values for the checks panel: closed-form results of accepted physics (and of the declared
modifications), written independently of the engine's numerics. A check compares a quantity the run computed
from its own events with the formula here; the player shows both and the relative difference.

Sources of the formulas (standard results):
* exact Schwarzschild deflection for closest approach P: Darwin, Proc. R. Soc. A 249, 180 (1959), in the form
  alpha = -pi + 4 sqrt(P/Q) [K(k) - F(zeta, k)], Q^2 = (P-2M)(P+6M), k^2 = (Q-P+6M)/(2Q),
  sin^2 zeta = (Q-P+2M)/(Q-P+6M), with M = GM/c^2 (also Bozza, PRD 66, 103001 (2002), eq. (11)-type forms);
* radial light travel time in Schwarzschild coordinates: c t = r2 - r1 + rs ln((r2 - rs)/(r1 - rs));
* critical impact parameter (photon sphere 3M): b_c = 3 sqrt(3) M;
* clock rate on a circular geodesic: dtau/dt = sqrt(1 - 3M/r); static clock: sqrt(1 - 2M/r);
* relativistic Doppler and simultaneity: textbook special relativity;
* ether and ballistic (emission) formulas: Galilean kinematics with the stated light-propagation rule.
"""

from __future__ import annotations

import math

from scipy import special


def darwin_deflection(r0: float, rs: float) -> float:
    M = 0.5 * rs
    P = r0
    Q = math.sqrt((P - 2 * M) * (P + 6 * M))
    m = (Q - P + 6 * M) / (2 * Q)
    s2 = (Q - P + 2 * M) / (Q - P + 6 * M)
    zeta = math.asin(math.sqrt(max(0.0, min(1.0, s2))))
    return -math.pi + 4.0 * math.sqrt(P / Q) * (special.ellipk(m) - special.ellipkinc(zeta, m))


def impact_from_closest(r0: float, rs: float) -> float:
    return r0 / math.sqrt(1.0 - rs / r0)


def b_crit(rs: float) -> float:
    return 1.5 * math.sqrt(3.0) * rs


def radial_light_time(r1: float, r2: float, rs: float, c: float) -> float:
    a, b = min(r1, r2), max(r1, r2)
    return (b - a + (rs * math.log((b - rs) / (a - rs)) if rs > 0 else 0.0)) / c


def static_clock_rate(r: float, rs: float) -> float:
    return math.sqrt(1.0 - rs / r)


def circular_orbit_clock_rate(r: float, rs: float) -> float:
    return math.sqrt(1.0 - 1.5 * rs / r)


def gravitational_period_ratio(r_emit: float, r_recv: float, rs: float) -> float:
    """Received / emitted period for static emitter and receiver."""
    return math.sqrt((1.0 - rs / r_recv) / (1.0 - rs / r_emit))


def gamma(beta: float) -> float:
    return 1.0 / math.sqrt(1.0 - beta * beta)


def simultaneity_offset(v: float, D: float, c: float, kinematics: str) -> float:
    """Lab time at distance D (along v) that an observer at the origin with velocity v calls 'now' at lab t = 0."""
    return v * D / c**2 if kinematics == "SR" else 0.0


def one_way_speed(kinematics: str, sync: str, c: float, v_app: float, s: int, u_src: float = 0.0) -> float:
    """Speed of light measured with a rod along x (rest length L0, clocks at both ends) moving with lab
    velocity v_app; light moves in direction s = +-1 along x; u_src is the x-velocity of the light's source
    (matters only for the emission theory). sync: "einstein" (light exchange inside the apparatus) or "lab"
    (clocks set to lab simultaneity, an operationally unavailable convention)."""
    b = v_app / c
    if kinematics == "SR":
        return c if sync == "einstein" else c / (1.0 + s * b)
    if kinematics == "ether":
        return c * (1.0 - b * b) if sync == "einstein" else c - s * v_app
    if kinematics == "emission":
        return c + s * (u_src - v_app)
    raise ValueError(kinematics)


def round_trip_speed(kinematics: str, c: float, v_app: float, transverse: bool = False) -> float:
    """Two-way speed 2 L0 / (proper round-trip time) for the apparatus's own light (convention-free)."""
    b = v_app / c
    if kinematics in ("SR", "emission"):
        return c
    if kinematics == "ether":
        return c * math.sqrt(1.0 - b * b) if transverse else c * (1.0 - b * b)
    raise ValueError(kinematics)


def doppler_ratio(kinematics: str, s: int, beta_src: float, beta_rcv: float) -> float:
    """Received / emitted frequency for collinear motion along x; light travels in direction s."""
    if kinematics == "SR":
        return gamma(beta_rcv) * (1 - s * beta_rcv) / (gamma(beta_src) * (1 - s * beta_src))
    if kinematics == "ether":
        return (1 - s * beta_rcv) / (1 - s * beta_src)
    if kinematics == "emission":
        return 1 - s * (beta_rcv - beta_src)
    raise ValueError(kinematics)
