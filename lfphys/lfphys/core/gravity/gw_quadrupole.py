# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Gravitational waves of a slow source by Einstein's quadrupole formula: the waveforms h+, hx seen from a chosen
direction, and the energy and angular momentum the waves carry, computed from a trajectory.

Formulas (Blanchet, Living Rev. Relativ. 17, 2 (2014), Eqs. (2)-(5), (69)), G = c = 1:

    h_ij^TT = (2 / R) P_ijab(N) d^2 Q_ab / dt^2,       Q_ij = sum_A m_A (y_A^i y_A^j - delta_ij y_A^2 / 3),
    h+ = (1/2)(P_i P_j - Q_i Q_j) h_ij^TT,   hx = (1/2)(P_i Q_j + P_j Q_i) h_ij^TT,
    dE/dt = (1/5) dddQ_ab dddQ_ab,           dJ_i/dt = (2/5) eps_iab ddQ_ac dddQ_bc,

with N the direction from the source to the observer at distance R, P_ijab = P_ia P_jb - P_ij P_ab / 2,
P_ij = delta_ij - N_i N_j, and (N, P, Q) a right-handed orthonormal triad. For a binary in its centre-of-mass frame
the Newtonian quadrupole is mu x^i x^j (relative orbit x, reduced mass mu), so its derivatives follow from the
relative position x, velocity v, acceleration a and jerk j of the computed trajectory:

    d^2(x x)/dt^2 = 2 v v + x a + a x,     d^3(x x)/dt^3 = 3 (v a + a v) + x j + j x.

The energy flux per solid angle is R^2 (dh+/dt^2 + dhx/dt^2) / (16 pi) (h_ij h_ij = 2 (h+^2 + hx^2) for a TT wave):
``flux_over_sphere`` integrates it over the directions by a product rule exact for the quartic dependence on N, and
the result equals the quadrupole luminosity (the energy balance of the waveforms; tested).

Convention for (P, Q) (Blanchet 2014 Sec. 9.4): for an orbit in the xy-plane with angular momentum along +z and an
observer at inclination iota and azimuth Phi, N = (sin iota cos Phi, sin iota sin Phi, cos iota), P points to the
ascending node, P = (sin Phi, -cos Phi, 0), and Q = N x P. A circular orbit then gives h+ = -(2 mu M / (R a))
(1 + cos^2 iota) cos 2 psi, hx = -(4 mu M / (R a)) cos iota sin 2 psi (psi the orbital phase from the ascending node),
Blanchet 2014 Eqs. (320), (322a), (323a) at Newtonian order without the memory term.
"""

from __future__ import annotations

import math

import numpy as np

from ..constants import C, G

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Гравитационные волны по квадрупольной формуле: h₊, h× и поток энергии",
    "statement": "Волны медленного источника по формуле Эйнштейна: поляризации h₊, h× для заданного направления "
                 "наблюдения из вычисленной траектории (положение, скорость, ускорение, рывок), светимость и поток "
                 "момента импульса; поток энергии, проинтегрированный по сфере из самих волн, равен квадрупольной "
                 "светимости.",
    "validity": "ведущий порядок по v/c: поправки к амплитуде — относительные O(v/c) для неравных масс (массовый "
                "октуполь, токовый квадруполь) и O(v²/c²); волновая зона R ≫ λ; без хвостов и нелинейной памяти "
                "(у кругового движения память даёт в h₊ постоянный сдвиг −(1/96) sin²i (17 + cos²i) в единицах "
                "2Gμx/(c²R), Blanchet 2014, Eq. (322a)); полнее волновых форм в движке нет",
    "basis": ["Einstein 1918; Landau & Lifshitz (квадрупольная формула)",
              "Blanchet, Living Rev. Relativ. 17, 2 (2014), Eqs. (2)-(5), (69), (320), (322a), (323a)"],
    "conflicts": [],
}


def _stf(T):
    tr = np.trace(T, axis1=-2, axis2=-1)
    return T - tr[..., None, None] * np.eye(3) / 3.0


def _sym(a, b):
    return a[..., :, None] * b[..., None, :] + b[..., :, None] * a[..., None, :]


def newtonian_kinematics(x, v, m: float = 1.0):
    """Acceleration and jerk of the Newtonian relative motion: a = -m x / r^3, j = -(m / r^3)(v - 3 (n.v) n)."""
    x = np.asarray(x, float)
    v = np.asarray(v, float)
    r = np.sqrt(np.sum(x * x, axis=-1))[..., None]
    n = x / r
    rdot = np.sum(n * v, axis=-1)[..., None]
    a = -m * x / r**3
    j = -(m / r**3) * (v - 3.0 * rdot * n)
    return a, j


def quadrupole(x, v, a, j, mu: float):
    """(Q, d^2Q/dt^2, d^3Q/dt^3) of the Newtonian quadrupole mu x x (trace-free), shapes (..., 3, 3)."""
    x, v, a, j = (np.asarray(z, float) for z in (x, v, a, j))
    Q = mu * _stf(x[..., :, None] * x[..., None, :])
    Q2 = mu * _stf(2.0 * v[..., :, None] * v[..., None, :] + _sym(x, a))
    Q3 = mu * _stf(3.0 * _sym(v, a) + _sym(x, j))
    return Q, Q2, Q3


def observer_triad(iota: float, Phi: float):
    """(N, P, Q) for an observer at inclination iota from +z and azimuth Phi; P toward the ascending node of an
    orbit in the xy-plane moving counter-clockwise (Blanchet 2014 Sec. 9.4), Q = N x P."""
    N = np.array([math.sin(iota) * math.cos(Phi), math.sin(iota) * math.sin(Phi), math.cos(iota)])
    P = np.array([math.sin(Phi), -math.cos(Phi), 0.0])
    return N, P, np.cross(N, P)


def tt_projection(T, N):
    """P_ijab T_ab, the transverse-traceless part of a symmetric tensor for the direction N."""
    N = np.asarray(N, float)
    Pm = np.eye(3) - np.outer(N, N)
    PTP = Pm @ T @ Pm
    return PTP - 0.5 * Pm * np.trace(PTP, axis1=-2, axis2=-1)[..., None, None]


def h_tt(Q2, N):
    """R h_ij^TT = 2 P_ijab d^2Q_ab/dt^2 (G = c = 1)."""
    return 2.0 * tt_projection(np.asarray(Q2, float), N)


def polarizations(Q2, P, Q):
    """(R h+, R hx) from d^2Q/dt^2 and the polarization vectors: R h+ = P.Q2.P - Q.Q2.Q, R hx = 2 P.Q2.Q (the TT
    projection is implied: (P P - Q Q) and (P Q + Q P) are themselves transverse and trace-free)."""
    Q2 = np.asarray(Q2, float)
    pq = np.einsum("...ij,i,j->...", Q2, P, P)
    qq = np.einsum("...ij,i,j->...", Q2, Q, Q)
    pqx = np.einsum("...ij,i,j->...", Q2, P, Q)
    return pq - qq, 2.0 * pqx


def luminosity(Q3):
    """dE/dt carried by the waves, (1/5) dddQ_ab dddQ_ab (G = c = 1; Q3 trace-free)."""
    Q3 = np.asarray(Q3, float)
    return 0.2 * np.einsum("...ab,...ab->...", Q3, Q3)


_EPS = np.zeros((3, 3, 3))
_EPS[0, 1, 2] = _EPS[1, 2, 0] = _EPS[2, 0, 1] = 1.0
_EPS[0, 2, 1] = _EPS[2, 1, 0] = _EPS[1, 0, 2] = -1.0


def angular_momentum_flux(Q2, Q3):
    """dJ_i/dt carried by the waves, (2/5) eps_iab ddQ_ac dddQ_bc (G = c = 1)."""
    return 0.4 * np.einsum("iab,...ac,...bc->...i", _EPS, np.asarray(Q2, float), np.asarray(Q3, float))


def sphere_rule(n_mu: int = 6, n_phi: int = 12):
    """Directions and weights on the unit sphere: Gauss-Legendre in cos(theta) times the uniform rule in phi;
    exact for polynomials in N of degree <= min(2 n_mu - 1, n_phi - 1) (the flux density is of degree 4)."""
    mu, w = np.polynomial.legendre.leggauss(n_mu)
    ph = 2.0 * math.pi * np.arange(n_phi) / n_phi
    s = np.sqrt(1.0 - mu * mu)
    N = np.stack([np.outer(s, np.cos(ph)), np.outer(s, np.sin(ph)), np.outer(mu, np.ones(n_phi))], axis=-1)
    W = np.outer(w, np.full(n_phi, 2.0 * math.pi / n_phi))
    return N.reshape(-1, 3), W.reshape(-1)


def _triad_of(N):
    """A transverse pair (P, Q) for a direction N (any orientation works for the flux)."""
    t = np.array([0.0, 0.0, 1.0]) if abs(N[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    P = np.cross(t, N)
    P /= np.linalg.norm(P)
    return P, np.cross(N, P)


def flux_density(Q3, N):
    """dE/(dt dOmega) = R^2 ((dh+/dt)^2 + (dhx/dt)^2) / (16 pi) toward N, with R dh/dt from d^3Q/dt^3."""
    P, Q = _triad_of(np.asarray(N, float))
    hp, hx = polarizations(Q3, P, Q)
    return (hp * hp + hx * hx) / (16.0 * math.pi)


def flux_over_sphere(Q3, n_mu: int = 6, n_phi: int = 12):
    """The energy flux of the waves integrated over all directions (G = c = 1); equals ``luminosity(Q3)``."""
    Ns, W = sphere_rule(n_mu, n_phi)
    return sum(w * flux_density(Q3, N) for N, w in zip(Ns, W))


def binary_waveform(x, v, nu: float, iota: float, Phi: float, a=None, j=None):
    """(R h+ / m, R hx / m) of a binary's relative orbit in units G = c = m = 1 (m the total mass, mu = nu).
    a, j: the acceleration and jerk used in d^2Q/dt^2; by default the Newtonian ones of x, v, which is the consistent
    leading-order quadrupole formula of the computed positions and velocities. Passing the PN acceleration and jerk
    (``pn_binary.acceleration``, ``jerk``) changes the amplitude at O(x) WITHOUT making it 1PN-accurate (the 1PN
    waveform has further terms, Blanchet 2014 Eqs. (322c), (323c)): face-on amplitude relative to 4 nu x,
    x = (m Omega)^(2/3), on 2PN circular orbits, nu = 1/4 — r = 10: default -2.6 %, PN a, j -11.6 %, the 1PN
    waveform -20.0 %; r = 30: -1.3 %, -5.5 %, -6.9 %; r = 100: -0.44 %, -1.8 %, -2.1 % (review B5, N4; test)."""
    if a is None or j is None:
        a, j = newtonian_kinematics(x, v)
    _, Q2, _ = quadrupole(x, v, a, j, nu)
    N, P, Q = observer_triad(iota, Phi)
    return polarizations(Q2, P, Q)


def strain_scale(gm_total: float, distance: float) -> float:
    """h = strain_scale * (R h / m in scaled units): (G m / c^2) / R, with G m in m^3 s^-2 and R in metres."""
    return gm_total / C**2 / distance


def luminosity_scale() -> float:
    """SI watts per unit of the scaled luminosity: c^5 / G."""
    return C**5 / G
