# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Special relativity in 2+1 dimensions (lab coordinates (ct, x, y)): boosts, proper time, aberration, velocity
composition, Doppler factor, Thomas-Wigner rotation.

Everything here is exact: closed forms of the Lorentz group, evaluated in float64. Tests compare each function with
an independent construction (matrix products, composition of boosts, limits) in ``lfphys/tests``.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Special relativity"),
    "statement": T("Lorentz invariance: the speed of light is the same in all inertial frames; Lorentz "
                   "transformations, proper time, aberration, velocity composition, the Doppler effect, the "
                   "Thomas–Wigner rotation."),
    "validity": T("flat spacetime; gravity is in lfphys.core.gravity"),
    "basis": ["Einstein, Ann. Phys. 17, 891 (1905)",
              T("tests of the isotropy of c (Michelson–Morley, Kennedy–Thorndike) and of time dilation "
                "(Ives–Stilwell, muons in storage rings): no violation found")],
    "conflicts": [],
}


def gamma(beta: float) -> float:
    """1/sqrt(1 - beta^2), written as 1/sqrt((1 - |beta|)(1 + |beta|)): full precision up to beta -> 1 (the form
    1 - beta^2 loses up to 3e-10 relative near beta = 1 - 1e-8; review 2026-10-23, E14)."""
    b = abs(float(beta))
    if b >= 1.0:
        raise ValueError("|v| >= c")
    return 1.0 / math.sqrt((1.0 - b) * (1.0 + b))


def boost_matrix(v, c: float) -> np.ndarray:
    """3x3 matrix mapping lab (ct, x, y) to the coordinates (ct', x', y') of an inertial frame moving with lab
    velocity ``v`` (origins coincide): the Lorentz boost."""
    v = np.asarray(v, dtype=float)
    b = v / c
    b2 = float(b @ b)
    if b2 >= 1.0:
        raise ValueError("|v| >= c: no inertial frame moves at or faster than light (SR)")
    M = np.eye(3)
    g = 1.0 / np.sqrt(1.0 - b2)
    M[0, 0] = g
    M[0, 1:] = -g * b
    M[1:, 0] = -g * b
    if b2 > 0:
        M[1:, 1:] = np.eye(2) + (g - 1.0) * np.outer(b, b) / b2
    return M


def clock_rate_flat(v, c: float) -> float:
    """dtau/dt of a clock moving with lab velocity v."""
    b2 = float(np.dot(v, v)) / c**2
    if b2 >= 1.0:
        raise ValueError("|v| >= c")
    return float(np.sqrt(1.0 - b2))


def metric_clock_rate(c: float, rs: float, pos, vel) -> float:
    """dtau/dt along a worldline: flat (rs = 0) dtau/dt = sqrt(1 - v^2/c^2); Schwarzschild exterior (rs > 0, lab =
    Schwarzschild coordinates drawn as x = r cos(phi), y = r sin(phi))
    dtau/dt = sqrt(f - (v_r^2/f + v_t^2)/c^2), f = 1 - rs/r (v_r, v_t: coordinate velocities)."""
    vel = np.asarray(vel, dtype=float)
    c2 = c**2
    if rs > 0.0:
        pos = np.asarray(pos, dtype=float)
        r = float(np.hypot(*pos))
        f = 1.0 - rs / r
        if f <= 0:
            raise ValueError("clock inside the horizon")
        rhat = pos / r
        vr = float(vel @ rhat)
        vt2 = float(vel @ vel) - vr * vr
        q = f - (vr * vr / f + vt2) / c2
    else:
        q = 1.0 - float(vel @ vel) / c2
    if q <= 0:
        raise ValueError("worldline is not timelike (moves at or faster than local light)")
    return math.sqrt(q)


def emit_velocities(directions_rest, v_source, c: float) -> np.ndarray:
    """Lab velocities of light emitted along unit ``directions_rest`` given in the source's rest frame: Lorentz
    transformation of the null direction (aberration; the speed stays c)."""
    n = np.asarray(directions_rest, dtype=float)
    v = np.asarray(v_source, dtype=float)
    if not np.any(v):
        return c * n
    Minv = boost_matrix(-v, c)  # source frame -> lab
    k = np.concatenate([np.ones((n.shape[0], 1)), n], axis=1) @ Minv.T
    return c * k[:, 1:] / k[:, :1]


def aberrate(n_rest, v, c: float) -> np.ndarray:
    """Unit directions, in the frame where the source moves with velocity ``v``, of light emitted along ``n_rest``
    in the source frame."""
    d = emit_velocities(n_rest, v, c) / c
    return d / np.linalg.norm(d, axis=1)[:, None]


def compose_velocities(u, v, c: float) -> np.ndarray:
    """Velocity, in the lab, of an object moving with velocity ``u`` in a frame that moves with lab velocity ``v``
    (Einstein addition, general directions): w = [u_par + v + u_perp / gamma_v] / (1 + u.v/c^2)."""
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    v2 = float(v @ v)
    if v2 == 0.0:
        return u.copy()
    g = gamma(math.sqrt(v2) / c)
    u_par = (u @ v) / v2 * v
    u_perp = u - u_par
    return (u_par + v + u_perp / g) / (1.0 + float(u @ v) / c**2)


def rapidity(beta: float) -> float:
    return math.atanh(beta)


def doppler_factor(beta: float, cos_theta_lab: float) -> float:
    """nu_received / nu_emitted for a source moving with speed beta c; theta_lab is the angle between the source's
    velocity and the direction from the source to the receiver, measured in the receiver's (lab) frame:
    nu_r / nu_e = 1 / (gamma (1 - beta cos theta))."""
    return 1.0 / (gamma(beta) * (1.0 - beta * cos_theta_lab))


def wigner_rotation_angle(u, v, c: float) -> float:
    """Thomas-Wigner rotation. Frame F1 moves with velocity u in the lab, frame F2 with velocity v in F1. The Lorentz
    transformation lab -> F2 is B(v) B(u) = R(theta) B(w), with w the velocity of F2 in the lab and R acting on
    coordinates, R = [[cos theta, -sin theta], [sin theta, cos theta]] in the x-y block: the components of a fixed
    vector turn counter-clockwise by theta, i.e. the axes of F2, seen from the frame reached by the single boost
    B(w), are turned by -theta (clockwise for theta > 0). For u along x and v along y (u x v along +z) theta > 0,
    ~ |u x v| / (2 c^2) for small speeds: the axes turn clockwise, opposite to the turn of the velocity (the sense of
    Thomas precession). (Docstring corrected: review 2026-10-23, E6.) Computed from the matrices themselves
    (exact to round-off); the closed form tan(theta/2) = sin(phi) / (k + cos(phi)),
    k^2 = (gamma_u + 1)(gamma_v + 1) / ((gamma_u - 1)(gamma_v - 1)), is checked in the tests."""
    lam = boost_matrix(v, c) @ boost_matrix(u, c)
    inv = np.linalg.inv(lam)
    w = inv[1:, 0] / inv[0, 0] * c  # lab velocity of the origin of F2
    R = lam @ np.linalg.inv(boost_matrix(w, c))
    return float(math.atan2(R[2, 1] - R[1, 2], R[1, 1] + R[2, 2]))
