# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Post-Newtonian (PN) motion of a binary of two non-spinning compact bodies in its centre-of-mass frame.

Units: G = c = 1 and the total mass m = m1 + m2 = 1, so lengths are in G m / c^2, times in G m / c^3, velocities in c;
nu = m1 m2 / m^2 (0 < nu <= 1/4) is the symmetric mass ratio and mu = nu m the reduced mass. ``mass_units(gm)``
gives the SI scales. The state is the relative orbit in harmonic coordinates: x = y1 - y2, v = dx/dt (3-vectors),
r = |x|, n = x / r, rdot = n . v.

Equations of motion (Blanchet, Living Rev. Relativ. 17, 2 (2014), Eqs. (219)-(220); the same coefficients in the 2024
edition, Living Rev. Relativ. 27, 4, Eqs. (357)-(359); 1PN and 2PN also Kidder, Phys. Rev. D 52, 821 (1995),
Eq. (2.2)), standard harmonic gauge:

    a = -(m / r^2) [(1 + A) n + B v],   A = A_1PN + A_2PN + A_2.5PN + A_3.5PN,   B likewise.

Included orders (``orders``, default all four): 1PN and 2PN (conservative), 2.5PN and 3.5PN (radiation reaction, the
leading term and its 1PN correction, in the harmonic gauge; the 3.5PN term carries no gauge constant). Left out:
3PN (conservative, with the gauge logarithms ln(r / r0'')), 4PN and above, the 4PN tail (hereditary), spins, tides.
So the conservative dynamics is accurate to relative O(v^6/c^6) (the first missing term is 3PN) and the dissipative
dynamics to relative 1PN beyond its leading order (4.5PN missing); the hereditary tail term of radiation reaction
(relative 1.5PN of the dissipative part) is absent, as in every local PN equation of motion at this order.

Conserved quantities of the conservative part (Kidder 1995, Eqs. (2.7a, b, d), (2.9b, d), spin terms dropped), per
reduced mass: E / mu (``energy``) and J / mu (``angular_momentum``), to 1PN or 2PN. Along the 2PN equations of motion
dE/dt and dJ/dt vanish up to O(c^-6) (tested by the scaling of the residual).

Integration (``integrate``, ``step``): two routes, both error-controlled DOP853 (scipy), on the relative orbit in
the scaled units (the two-body problem reduced to one body, numbers of order one):
* ``"cartesian"`` -- the state (x, v): robust in strong fields and for eccentric orbits;
* ``"elements"`` -- variation of constants: the Newtonian part is solved exactly by the osculating Kepler orbit and
  only the PN perturbation f = a + n/r^2 (formed without the Newtonian term) is integrated, through the exact
  equations of the angular momentum h = x x v and of the Laplace-Runge-Lenz vector A = v x h / m - n,
  dh/dt = x x f, dA/dt = (f x h + v x (x x f)) / m, and of the true longitude, dtheta/dt = h / r^2. As in Encke's
  method the variables are the changes from the start (h - h0, A - A0, and theta minus the initial mean motion), so
  the error control acts on the changes themselves: a perturbation of 1e-12 of the orbit per period (PSR B1913+16)
  is integrated to 1e-11 of itself, which the Cartesian route cannot do in double precision. The orbit stays in its
  initial plane (no spins: a lies in the span of n and v).
Both routes are tested against each other and against the closed forms below. A run that reaches ``r_stop`` ends
exactly there (Newton steps on the event time, each redoing the last step); a start not above r_stop is refused, a
plunge without r_stop ends with a message naming it; a Cartesian run whose radiation reaction is below its
resolution warns (``PrecisionWarning``). Initial data: ``state_from_invariants`` (prescribed gauge-invariant eps, j:
the turning points as bracketed roots of the effective potential at fixed J, ``turning_points``; refusals as
``NoOrbit`` with a reason), ``circular_state`` (circular, or quasi-circular with the engine's own adiabatic radial
velocity, optionally refined by eccentricity reduction), ``periapsis_state`` (Newtonian osculating a, e: not a PN
orbit with that a, e). ``averaged_dissipation`` gives the secular losses of E and J over one radial period, to first
order in the radiation reaction.

References computed here (closed forms of the theory, for checks; Blanchet 2014): the 2PN circular-orbit frequency in
harmonic coordinates, Eq. (228); the gauge-invariant circular energy E(x), Eq. (232); the gauge-invariant mean motion
n(eps, j) and periastron advance K(eps, j), Eqs. (348a, b) and the frequency parameter x(eps, j), Eq. (350), with
eps = -2E/(mu c^2), j = -2E J^2/(mu^3 G^2 m^2) (Eq. (345)); the 1PN time eccentricity e_t, Eq. (346e); the
radiation-reaction force on circular orbits, Eq. (226), and the circular inspiral rate dr/dt, Eq. (227a).
"""

from __future__ import annotations

import functools
import math

import numpy as np
from scipy import integrate as _si
from scipy.optimize import brentq

from lfphys.i18n import T

from ..constants import C

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": T("The two-body problem in GR: post-Newtonian equations of motion with radiation reaction"),
    "statement": T("The relative motion of two non-spinning compact bodies in the centre-of-mass frame (harmonic "
                   "coordinates): conservative 1PN and 2PN corrections, 2.5PN and 3.5PN radiation reaction; the "
                   "conserved 1PN/2PN energy and angular momentum; initial data from invariants (turning points as "
                   "roots of the effective potential, refused with a reason when there is no orbit) and "
                   "quasi-circular data with their own inspiral velocity; integration in Cartesian variables or by "
                   "variation of constants (osculating elements, for weak perturbations); a step-by-step API; the "
                   "Einstein delay γ of a binary pulsar."),
    "validity": T("slow motion and weak field, v²/c² ~ GM/(c²r) ≪ 1: the dropped conservative 3PN term gives a "
                  "relative error O((v/c)⁶), the dissipative part is exact to relative 1PN (no 4.5PN and no 4PN tail "
                  "term); point masses without spins or tides; the radiation reaction (2.5PN + 3.5PN, harmonic gauge) "
                  "is exact to relative 1PN; its remainder (−35.5 x² at small x: no 4.5PN reaction) cancels it at r = "
                  "9.10–9.12 GM/c² for any mass ratio, and closer in the orbit gains energy; the remainder equals the "
                  "1PN correction at r = 10.6 (q = 1) … 13.0 (q = 0.05), reaction_validity_radius (review B6-gravity "
                  "G1); this is the most complete form of the two-body problem in the engine, which has no full GR "
                  "solution (numerical relativity)"),
    "basis": ["Blanchet, Living Rev. Relativ. 17, 2 (2014), Eqs. (219)-(220), (226)-(232), (345)-(353)",
              "Blanchet, Living Rev. Relativ. 27, 4 (2024), Eqs. (357)-(359)",
              "Kidder, Phys. Rev. D 52, 821 (1995), Eqs. (2.2), (2.7), (2.9)",
              T("PSR B1913+16: Weisberg & Huang, ApJ 829, 55 (2016) (orbital decay, periastron advance)")],
    "conflicts": [],
}

ORDERS = (1, 2, 2.5, 3.5)
_ALLOWED = (1, 2, 2.5, 3.5)


def _orders(orders) -> tuple:
    o = tuple(sorted(set(float(k) for k in orders)))
    bad = [k for k in o if k not in _ALLOWED]
    if bad:
        raise ValueError(f"PN orders must be among {_ALLOWED}, got {bad}")
    return o


def mass_units(gm: float) -> dict:
    """SI scales of the scaled units for a total mass with G m = gm (m^3 s^-2): length G m / c^2 (m), time
    G m / c^3 (s), velocity c (m/s), energy per reduced mass c^2 (J/kg), angular momentum per reduced mass G m / c
    (m^2/s)."""
    return {"length": gm / C**2, "time": gm / C**3, "velocity": C, "energy_per_mu": C**2, "J_per_mu": gm / C}


def symmetric_mass_ratio(m1: float, m2: float) -> float:
    """nu = m1 m2 / (m1 + m2)^2 (any common mass unit)."""
    return m1 * m2 / (m1 + m2) ** 2


# --- the equations of motion -----------------------------------------------------------------------------------

def coefficients(r, rdot, v2, nu: float, orders=ORDERS):
    """(A, B) of a = -(1/r^2)[(1 + A) n + B v] (G = c = m = 1), summed over ``orders``; Blanchet 2014 Eq. (220)
    (1/c^2, 1/c^4, 1/c^5, 1/c^7 terms), identical to Blanchet 2024 Eqs. (358a-c, e), (359a-c, e). Works with numpy
    arrays and with complex values (complex-step derivatives)."""
    o = _orders(orders)
    g = 1.0 / r
    rd2 = rdot * rdot
    A = 0.0 * r
    B = 0.0 * r
    if 1 in o:
        A = A + (-1.5 * rd2 * nu + v2 + 3.0 * nu * v2 - g * (4.0 + 2.0 * nu))
        B = B + (-4.0 * rdot + 2.0 * rdot * nu)
    if 2 in o:
        A = A + (15.0 / 8.0 * rd2 * rd2 * nu - 45.0 / 8.0 * rd2 * rd2 * nu**2 - 4.5 * rd2 * nu * v2
                 + 6.0 * rd2 * nu**2 * v2 + 3.0 * nu * v2 * v2 - 4.0 * nu**2 * v2 * v2
                 + g * (-2.0 * rd2 - 25.0 * rd2 * nu - 2.0 * rd2 * nu**2 - 6.5 * nu * v2 + 2.0 * nu**2 * v2)
                 + g * g * (9.0 + 87.0 / 4.0 * nu))
        B = B + (4.5 * rd2 * rdot * nu + 3.0 * rd2 * rdot * nu**2 - 7.5 * rdot * nu * v2 - 2.0 * rdot * nu**2 * v2
                 + g * (2.0 * rdot + 20.5 * rdot * nu + 4.0 * rdot * nu**2))
    if 2.5 in o:
        A = A + 1.6 * g * nu * rdot * (-17.0 / 3.0 * g - 3.0 * v2)
        B = B + 1.6 * g * nu * (3.0 * g + v2)
    if 3.5 in o:
        A = A + g * nu * rdot * (g * g * (3956.0 / 35.0 + 184.0 / 5.0 * nu)
                                 + g * v2 * (692.0 / 35.0 - 724.0 / 15.0 * nu)
                                 + v2 * v2 * (366.0 / 35.0 + 12.0 * nu)
                                 + g * rd2 * (294.0 / 5.0 + 376.0 / 5.0 * nu)
                                 - v2 * rd2 * (114.0 + 12.0 * nu) + 112.0 * rd2 * rd2)
        B = B + g * nu * (g * g * (-1060.0 / 21.0 - 104.0 / 5.0 * nu)
                          + g * v2 * (164.0 / 21.0 + 148.0 / 5.0 * nu)
                          + v2 * v2 * (-626.0 / 35.0 - 12.0 / 5.0 * nu)
                          + g * rd2 * (-82.0 / 3.0 - 848.0 / 15.0 * nu)
                          + v2 * rd2 * (678.0 / 5.0 + 12.0 / 5.0 * nu) - 120.0 * rd2 * rd2)
    return A, B


def _kin(x, v):
    """r, n, rdot, v^2 of states (..., 3); complex-safe (no abs)."""
    x = np.asarray(x)
    v = np.asarray(v)
    r = np.sqrt(np.sum(x * x, axis=-1))
    n = x / r[..., None]
    rdot = np.sum(n * v, axis=-1)
    v2 = np.sum(v * v, axis=-1)
    return r, n, rdot, v2


def perturbation(x, v, nu: float, orders=ORDERS):
    """The PN acceleration beyond Newton, f = a + n / r^2 = -(1/r^2)(A n + B v) (no cancellation: the Newtonian
    term is never formed). Shape (..., 3); complex-safe."""
    r, n, rdot, v2 = _kin(x, v)
    A, B = coefficients(r, rdot, v2, nu, orders)
    return -(A[..., None] * n + B[..., None] * np.asarray(v)) / (r * r)[..., None]


def acceleration(x, v, nu: float, orders=ORDERS):
    """Relative acceleration a = dv/dt (G = c = m = 1), shape (..., 3); ``orders=()`` gives Newton."""
    r, n, rdot, v2 = _kin(x, v)
    A, B = coefficients(r, rdot, v2, nu, orders)
    return -((1.0 + A)[..., None] * n + B[..., None] * np.asarray(v)) / (r * r)[..., None]


def jerk(x, v, nu: float, orders=ORDERS):
    """da/dt along the motion, (d a/d x) v + (d a/d v) a, by a complex step (exact to rounding)."""
    a = acceleration(np.asarray(x, float), np.asarray(v, float), nu, orders)
    return directional(lambda X, V: acceleration(X, V, nu, orders), x, v, v, a)


# --- conserved energy and angular momentum (Kidder 1995) -------------------------------------------------------

def energy(x, v, nu: float, order: int = 2, newtonian: bool = True):
    """E / mu (G = c = m = 1): Newton + 1PN (+ 2PN), Kidder 1995 Eqs. (2.7a, b, d) with eta = nu. Complex-safe.
    ``newtonian=False`` returns the PN terms alone, without forming them as a difference of two energies (their
    change per orbit is then resolved to rounding of the PN terms themselves, not of E)."""
    r, n, rdot, v2 = _kin(x, v)
    g = 1.0 / r
    rd2 = rdot * rdot
    E = (0.5 * v2 - g) if newtonian else 0.0 * r
    if order >= 1:
        E = E + (3.0 / 8.0 * (1.0 - 3.0 * nu) * v2 * v2 + 0.5 * (3.0 + nu) * v2 * g + 0.5 * nu * g * rd2
                 + 0.5 * g * g)
    if order >= 2:
        E = E + (5.0 / 16.0 * (1.0 - 7.0 * nu + 13.0 * nu**2) * v2**3
                 - 3.0 / 8.0 * nu * (1.0 - 3.0 * nu) * g * rd2 * rd2
                 + 1.0 / 8.0 * (21.0 - 23.0 * nu - 27.0 * nu**2) * g * v2 * v2
                 + 1.0 / 8.0 * (14.0 - 55.0 * nu + 4.0 * nu**2) * g * g * v2
                 + 1.0 / 4.0 * nu * (1.0 - 15.0 * nu) * g * v2 * rd2
                 - 1.0 / 4.0 * (2.0 + 15.0 * nu) * g**3
                 + 1.0 / 8.0 * (4.0 + 69.0 * nu + 12.0 * nu**2) * g * g * rd2)
    if order > 2:
        raise ValueError("energy: order 0, 1 or 2")
    return E


def angular_momentum(x, v, nu: float, order: int = 2):
    """J / mu (G = c = m = 1), a vector: (x x v)[1 + 1PN (+ 2PN)], Kidder 1995 Eqs. (2.9b, d). Complex-safe."""
    x = np.asarray(x)
    v = np.asarray(v)
    r, n, rdot, v2 = _kin(x, v)
    g = 1.0 / r
    rd2 = rdot * rdot
    f = 1.0 + 0.0 * r
    if order >= 1:
        f = f + 0.5 * v2 * (1.0 - 3.0 * nu) + (3.0 + nu) * g
    if order >= 2:
        f = f + (3.0 / 8.0 * (1.0 - 7.0 * nu + 13.0 * nu**2) * v2 * v2 - 0.5 * nu * (2.0 + 5.0 * nu) * g * rd2
                 + 0.5 * (7.0 - 10.0 * nu - 9.0 * nu**2) * g * v2 + 0.25 * (14.0 - 41.0 * nu + 4.0 * nu**2) * g * g)
    if order > 2:
        raise ValueError("angular_momentum: order 0, 1 or 2")
    return np.cross(x, v) * f[..., None]


def directional(fn, x, v, dx, dv):
    """The derivative of fn(x, v) in the direction (dx, dv), by a complex step (exact to rounding; fn must be
    complex-safe). Scalar or vector fn, single states (3,) or arrays (..., 3)."""
    x = np.asarray(x, float)
    v = np.asarray(v, float)
    dx = np.asarray(dx, float)
    dv = np.asarray(dv, float)
    sx = np.sqrt(np.sum(x * x, axis=-1) + np.sum(v * v, axis=-1))
    sd = np.sqrt(np.sum(dx * dx, axis=-1) + np.sum(dv * dv, axis=-1)) + 1e-300
    h = 1e-20 * sx / sd
    hh = h[..., None] if np.ndim(h) else h
    val = fn(x + 1j * hh * dx, v + 1j * hh * dv)
    return val.imag / (hh if np.ndim(val) > np.ndim(h) else h)


def rate_along(fn, x, v, a):
    """d fn(x, v)/dt for the motion dx/dt = v, dv/dt = a. With a the conservative acceleration this is the residual
    of a conservation law."""
    return directional(fn, x, v, v, a)


def gauge_invariants(x, v, nu: float, order: int = 2) -> dict:
    """eps = -2E/mu and j = -2E J^2/mu^3 (G = c = m = 1; Blanchet 2014 Eq. (345)) from the conserved 2PN (or 1PN)
    energy and angular momentum of a state."""
    E = float(energy(x, v, nu, order))
    J = float(np.linalg.norm(angular_momentum(x, v, nu, order)))
    return {"E": E, "J": J, "eps": -2.0 * E, "j": -2.0 * E * J * J}


# --- references: closed forms of the theory (Blanchet 2014) ----------------------------------------------------

def omega2_circular_harmonic(r: float, nu: float) -> float:
    """Omega^2 of a circular orbit of harmonic radius r at 2PN, Blanchet 2014 Eq. (228) (m = 1, gamma = 1/r)."""
    g = 1.0 / r
    return g**3 * (1.0 + (-3.0 + nu) * g + (6.0 + 41.0 / 4.0 * nu + nu * nu) * g * g)


def circular_energy(x: float, nu: float) -> float:
    """E / mu of a circular orbit in terms of the gauge-invariant x = (m Omega)^(2/3), to 2PN, Blanchet 2014
    Eq. (232) truncated after x^2: -(x/2)[1 + (-3/4 - nu/12) x + (-27/8 + 19 nu/8 - nu^2/24) x^2]."""
    return -0.5 * x * (1.0 + (-0.75 - nu / 12.0) * x + (-27.0 / 8.0 + 19.0 / 8.0 * nu - nu * nu / 24.0) * x * x)


def mean_motion(eps: float, j: float, nu: float) -> float:
    """Radial mean motion n = 2 pi / P_r (G = c = m = 1) to 2PN in the gauge-invariant eps, j; Blanchet 2014
    Eq. (348a) truncated after eps^2."""
    c2 = 555.0 + 30.0 * nu + 11.0 * nu * nu + 192.0 / math.sqrt(j) * (-5.0 + 2.0 * nu)
    return eps**1.5 * (1.0 + eps / 8.0 * (-15.0 + nu) + eps * eps / 128.0 * c2)


def periastron_K(eps: float, j: float, nu: float) -> float:
    """K = Phi / (2 pi), Phi the angle of return to periastron, to 2PN; Blanchet 2014 Eq. (348b) truncated after
    eps^2: 1 + 3 eps / j + (eps^2/4)[(3/j)(-5 + 2 nu) + (15/j^2)(7 - 2 nu)]."""
    return 1.0 + 3.0 * eps / j + eps * eps / 4.0 * (3.0 / j * (-5.0 + 2.0 * nu) + 15.0 / (j * j) * (7.0 - 2.0 * nu))


def x_parameter(eps: float, j: float, nu: float, order: int = 2) -> float:
    """x = (m Omega)^(2/3) with Omega = K n, Blanchet 2014 Eq. (350) to 1PN or (default) 2PN:
    x / eps = 1 + eps (-5/4 + nu/12 + 2/j) + eps^2 [5/2 + 5 nu/24 + nu^2/18 + (-5 + 2 nu)/sqrt(j)
    + (1/j)(-5 + 7 nu/6 + (1/j)(33/2 - 5 nu))]. Consistent with (348a, b): (K n)^(2/3) / eps equals it up to O(eps^3)
    (test)."""
    c1 = -1.25 + nu / 12.0 + 2.0 / j
    c2 = (2.5 + 5.0 / 24.0 * nu + nu * nu / 18.0 + (-5.0 + 2.0 * nu) / math.sqrt(j)
          + (1.0 / j) * (-5.0 + 7.0 / 6.0 * nu + (1.0 / j) * (16.5 - 5.0 * nu))) if order >= 2 else 0.0
    return eps * (1.0 + eps * c1 + eps * eps * c2)


def time_eccentricity(eps: float, j: float, nu: float) -> float:
    """e_t to 1PN: sqrt(1 - j) + eps [-8 + 8 nu + j (17 - 7 nu)] / (8 sqrt(1 - j)), Blanchet 2014 Eq. (346e)."""
    s = math.sqrt(1.0 - j)
    return s + eps * (-8.0 + 8.0 * nu + j * (17.0 - 7.0 * nu)) / (8.0 * s)


def circular_inspiral_rate(r: float, nu: float, with_3p5: bool = True) -> float:
    """dr/dt of a quasi-circular inspiral in harmonic coordinates: -(64/5) nu / r^3 [1 + (1/r)(-1751/336 - 7 nu/4)],
    Blanchet 2014 Eq. (227a) (the bracket's 1PN term only with the 3.5PN reaction)."""
    c1 = (-1751.0 / 336.0 - 7.0 / 4.0 * nu) / r if with_3p5 else 0.0
    return -12.8 * nu / r**3 * (1.0 + c1)


def circular_rr_coefficient(r: float, nu: float) -> float:
    """The radiation-reaction force on a circular orbit, a_RR = -(32/5)(nu / r^4)[1 + (1/r)(-743/336 - 11 nu/4)] v,
    Blanchet 2014 Eq. (226): returns the coefficient of -v."""
    return 6.4 * nu / r**4 * (1.0 + (-743.0 / 336.0 - 11.0 / 4.0 * nu) / r)


# --- the two bodies --------------------------------------------------------------------------------------------------

def body_positions(x, v, nu: float, order: int = 1):
    """Positions of body 1 (the heavier, X1 = m1/m >= 1/2) and body 2 in the centre-of-mass frame from the relative
    x, v: y1 = (X2 + nu Delta P) x, y2 = (-X1 + nu Delta P) x with Delta = X1 - X2 and P = (v^2/2 - m/(2r)) / c^2 at
    1PN (Blanchet 2014 Eqs. (216a, b), (217a) to 1/c^2; Q v enters at 2PN). The 1PN term is what makes the 1PN mass
    dipole sum_A m_A (1 + v_A^2/2 - m_B/(2r)) y_A vanish (test); the omitted terms are of relative size
    nu |Delta| (v/c)^4. ``order=0``: Newtonian (y1 = X2 x, y2 = -X1 x). Complex-safe (body velocities by
    ``directional``)."""
    x = np.asarray(x)
    v = np.asarray(v)
    X1 = 0.5 * (1.0 + math.sqrt(max(1.0 - 4.0 * nu, 0.0)))
    X2 = 1.0 - X1
    D = X1 - X2
    if order == 0:
        Pc = 0.0 * np.sum(x, axis=-1)
    elif order == 1:
        r = np.sqrt(np.sum(x * x, axis=-1))
        Pc = 0.5 * np.sum(v * v, axis=-1) - 0.5 / r
    else:
        raise ValueError("body_positions: order 0 or 1")
    k = (nu * D * Pc)[..., None] if np.ndim(Pc) else nu * D * Pc
    return (X2 + k) * x, (-X1 + k) * x


# --- the Einstein delay of a binary pulsar -------------------------------------------------------------------------

def einstein_gamma(gm1: float, gm2: float, pb: float, e: float, c: float = C) -> float:
    """gamma (s), the amplitude of the periodic part of t - tau of body 1 (the pulsar; body 2 its companion):
    e (P_b / 2 pi)^(1/3) G m2 (G m1 + 2 G m2) (G M)^(-4/3) / c^2 (Weisberg & Huang 2016 Eq. (17); Damour & Deruelle
    1986). SI arguments (G m in m^3 s^-2, P_b in s) as in ``lfphys.theories.approx.peters_mathews``, which uses it to
    weigh binaries. Derivation (and test): along a Kepler orbit the 1PN clock rate gives t - tau =
    int (v1^2/2 + G m2/r) dt / c^2 with v1 = (m2/M) v; with dt = r du/(n a) its periodic part is
    e G m2 (m1 + 2 m2) sin u / (M n a c^2), u the eccentric anomaly. It is in the core because it is the engine's only
    form of the Einstein delay (LAYERS.md §1; review B5, N10); its relative error is O(G M / (c^2 a)) (higher-order
    timing terms)."""
    return e * (pb / (2.0 * math.pi)) ** (1.0 / 3.0) * gm2 * (gm1 + 2.0 * gm2) * (gm1 + gm2) ** (-4.0 / 3.0) / c**2


# --- initial states -----------------------------------------------------------------------------------------------

def state(t: float, x, v) -> dict:
    """A state as plain data: {"t": float, "x": float64[3], "v": float64[3]} (relative orbit, scaled units)."""
    x = np.array(x, dtype=float).reshape(3)
    v = np.array(v, dtype=float).reshape(3)
    return {"t": float(t), "x": x, "v": v}


def newtonian_elements(x, v) -> dict:
    """Osculating Kepler elements of a state (m = 1): a, e, p, h (vector x x v), A (Laplace-Runge-Lenz vector
    v x h - n), E (= v^2/2 - 1/r). These are the Newtonian elements of the instantaneous position and velocity, not
    elements of the PN orbit."""
    x = np.asarray(x, float)
    v = np.asarray(v, float)
    r = math.sqrt(float(x @ x))
    h = np.cross(x, v)
    A = np.cross(v, h) - x / r
    E = 0.5 * float(v @ v) - 1.0 / r
    e = float(np.linalg.norm(A))
    p = float(h @ h)
    a = -0.5 / E if E < 0 else math.inf
    return {"a": a, "e": e, "p": p, "h": h, "A": A, "E": E}


def periapsis_state(a: float, e: float, t: float = 0.0) -> dict:
    """The state at periapsis of the Newtonian orbit with semi-major axis a (in G m / c^2) and eccentricity e,
    motion counter-clockwise in the xy-plane: its osculating Newtonian elements are a, e, but as initial data of the
    PN motion it is NOT an orbit with that a and e. The PN corrections at the periapsis grow like 1/(1 - e)^2: for
    nu = 1/4 the PN orbit is unbound for e = 0.7 when a < 82 (e = 0.3: a < 12), at e = 0.3, a = 24 it has half the
    Newtonian binding and time eccentricity 0.58, and even at a = 600 it is 2 % less bound (review B5, N5). For a PN
    orbit of prescribed energy and angular momentum use ``state_from_invariants``; for (quasi-)circular orbits
    ``circular_state``."""
    rp = a * (1.0 - e)
    return state(t, [rp, 0.0, 0.0], [0.0, math.sqrt((1.0 + e) / rp), 0.0])


class NoOrbit(ValueError):
    """No orbit of the PN equations with the requested data. ``reason``: "invalid" (eps <= 0 or j <= 0),
    "above_circular" (j above the circular value for this energy: no orbit), "plunge" (the bound region reaches the
    floor r_min: no periapsis, the orbit falls in), "pn_breakdown" (a turning point of E and J that the equations
    of motion do not have: their truncation is not small there), "no_circular" (no circular orbit at this radius or
    energy), "unresolved" (a numerical check failed; the message says which)."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


def _jz(r, v, nu, order):
    """J_z / mu of the state x = (r, 0, 0), v = (0, v, 0) (rdot = 0); arrays and complex values allowed."""
    r = np.asarray(r)
    v = np.asarray(v)
    z = 0.0 * r * v
    return angular_momentum(np.stack([r + z, z, z], -1), np.stack([z, v + z, z], -1), nu, order)[..., 2]


def tangential_speed(r, J: float, nu: float, order: int = 2):
    """The speed v of a turning point (rdot = 0) at radius r with J / mu = J: J_z(r, v) = J. J_z = r v f(r, v) with
    f >= 1 increasing in v (all coefficients of Kidder Eq. (2.9b, d) at rdot = 0 are positive for nu <= 1/4), so the
    root is unique in (0, J/r] and Newton's method from v = J/r converges monotonically (J_z is convex in v).
    Vectorised over r; derivatives by a complex step."""
    r = np.asarray(r, float)
    v = J / r
    polish = 0
    for _ in range(200):
        h = 1e-30 * v
        F = _jz(r, v + 1j * h, nu, order)
        dv = (F.real - J) / (F.imag / h)
        v = v - dv
        if np.all(np.abs(dv) <= 1e-14 * np.abs(v)):
            polish += 1  # quadratic convergence: two more steps reach rounding (they may oscillate at 1 ulp)
            if polish > 2:
                return v
    raise NoOrbit("unresolved", "tangential_speed: Newton's method did not converge")  # pragma: no cover


def turning_function(r, eps: float, j: float, nu: float, order: int = 2):
    """G(r) = E(r, v_t(r)) / mu + eps / 2 at fixed J / mu = sqrt(j / eps) (G = c = m = 1): the effective potential at
    fixed angular momentum minus the energy. Its zeros are the turning points of every orbit with these
    invariants; G < 0 where the orbit can be."""
    r = np.atleast_1d(np.asarray(r, float))
    v = tangential_speed(r, math.sqrt(j / eps), nu, order)
    z = 0.0 * r
    return energy(np.stack([r, z, z], -1), np.stack([z, v, z], -1), nu, order) + 0.5 * eps


def turning_points(eps: float, j: float, nu: float, order: int = 2, r_min: float = 2.0) -> dict:
    """Periapsis and apoapsis radii (harmonic) of the PN orbit with the gauge-invariant eps = -2E/mu and
    j = -2E J^2/mu^3 (Blanchet 2014 Eq. (345); E, J the conserved quantities of ``order``) as the zeros of
    ``turning_function`` bracketing the outermost region where G < 0 (a geometric grid of 600 radii from r_min to
    beyond the Newtonian apoapsis, then Brent's method; a well narrower than the grid is found by minimising G).
    Returns dict(r_p, r_a, r_c (the minimum of G in the well)); raises NoOrbit with reason "above_circular" (G > 0
    everywhere: j exceeds the circular value), "no_circular" (G > 0 everywhere and no circular orbit has this
    energy), "plunge" (G < 0 down to r_min: no inner turning point above r_min; the dict is then attached as
    ``.partial`` with r_p = None), "invalid" or "unresolved" (G < 0 out to 4^6 times the Newtonian scale)."""
    from scipy import optimize
    if not (eps > 0.0 and j > 0.0 and math.isfinite(eps) and math.isfinite(j)):
        raise NoOrbit("invalid", f"turning_points: need eps > 0 and j > 0 (bound orbits), got eps={eps}, j={j}")

    def G(r):
        return float(turning_function(r, eps, j, nu, order)[0])

    r_hi = 4.0 / eps
    for _ in range(6):
        rr = np.geomspace(r_min, r_hi, 600)
        g = turning_function(rr, eps, j, nu, order)
        if g[-1] > 0.0:
            break
        r_hi *= 4.0
    else:
        raise NoOrbit("unresolved", f"turning_points: G < 0 out to r = {r_hi:.3g} (eps={eps}, j={j})")
    kw = dict(xtol=1e-300, rtol=8.9e-16, maxiter=300)
    neg = np.nonzero(g < 0.0)[0]
    if neg.size == 0:
        # a well narrower than the grid: minimise G around the outermost interior grid minimum
        loc = [i for i in range(1, len(rr) - 1) if g[i] <= g[i - 1] and g[i] <= g[i + 1]]
        if loc:
            m = loc[-1]
            res = optimize.minimize_scalar(G, bounds=(rr[m - 1], rr[m + 1]), method="bounded",
                                           options={"xatol": 1e-13 * rr[m]})
            if res.fun < 0.0:
                r_c = float(res.x)
                return {"r_p": optimize.brentq(G, rr[m - 1], r_c, **kw),
                        "r_a": optimize.brentq(G, r_c, rr[m + 1], **kw), "r_c": r_c}
        try:
            jc = j_circular(eps, nu, order)
        except NoOrbit as err:
            raise NoOrbit("no_circular", f"no orbit with eps={eps:g}, j={j:g} (G = E_eff(r; J) + eps/2 > 0 "
                          f"everywhere above r_min = {r_min:g}); {err}") from None
        raise NoOrbit("above_circular", f"no orbit with eps={eps:g}, j={j:g}: j exceeds the circular value "
                      f"j_circ(eps) = {jc:.10g} (G = E_eff(r; J) + eps/2 > 0 everywhere)")
    k = int(neg[-1])
    r_a = optimize.brentq(G, rr[k], rr[k + 1], **kw)
    pos_in = np.nonzero(g[:k] > 0.0)[0]
    # the well's minimum (between the inner edge and r_a)
    lo = int(pos_in[-1]) + 1 if pos_in.size else 0
    m = lo + int(np.argmin(g[lo:k + 1]))
    res = optimize.minimize_scalar(G, bounds=(rr[max(m - 1, 0)], rr[min(m + 1, k + 1)]), method="bounded",
                                   options={"xatol": 1e-13 * rr[m]})
    r_c = float(res.x)
    if not pos_in.size:
        err = NoOrbit("plunge", f"no bound orbit with eps={eps:g}, j={j:g} above r_min = {r_min:g}: the region allowed "
                      f"by E and J reaches r_min (no periapsis; the orbit falls in from its apoapsis r_a = {r_a:.6g})")
        err.partial = {"r_p": None, "r_a": r_a, "r_c": r_c}
        raise err
    i = int(pos_in[-1])
    return {"r_p": optimize.brentq(G, rr[i], rr[i + 1], **kw), "r_a": r_a, "r_c": r_c}


def state_from_invariants(eps: float, j: float, nu: float, order: int = 2, t: float = 0.0, at: str = "periapsis",
                          r_min: float = 2.0) -> dict:
    """The state at the periapsis (or ``at="apoapsis"``) of the PN orbit whose conserved E and J (``order`` 1 or
    2, Kidder 1995) give the gauge-invariant eps = -2E/mu and j = -2E J^2/mu^3 (Blanchet 2014 Eq. (345)); xy-plane,
    counter-clockwise, x = (r, 0, 0), v = (0, v_t, 0). The turning points are bracketed roots of the effective
    potential at fixed J (``turning_points``), so the solve is global (no starting guess). Range: eps > 0 and
    0 < j <= j_circ(eps), the circular value of this energy (``j_circular``; above 1 by about eps (9 + nu)/4, so
    orbits of small eccentricity are included; Newtonian orbits have j = 1 - e^2 <= 1). Checks before returning: the
    state's own eps and j equal the requested ones to 1e-11 (measured ~1e-15), rdot = 0, and the radial acceleration
    of the conservative equations of motion has the sign of the requested turning point (> 0 at a periapsis).
    Raises NoOrbit (a ValueError) with ``reason`` "invalid", "above_circular", "plunge" (no periapsis above r_min;
    ``at="apoapsis"`` still returns the apoapsis of such a plunging orbit), "pn_breakdown" (the turning point of E
    and J is not one of the equations of motion: their truncation is not small there) or "unresolved". States with
    r_p below ~10 G m/c^2 are outside the reliable PN domain (validity of the module)."""
    if at not in ("periapsis", "apoapsis"):
        raise ValueError("state_from_invariants: at = 'periapsis' or 'apoapsis'")
    try:
        tp = turning_points(eps, j, nu, order, r_min)
    except NoOrbit as err:
        if at == "apoapsis" and err.reason == "plunge":
            tp = err.partial
        else:
            raise
    r = tp["r_p"] if at == "periapsis" else tp["r_a"]
    v = float(tangential_speed(np.array([r]), math.sqrt(j / eps), nu, order)[0])
    st = state(t, [r, 0.0, 0.0], [0.0, v, 0.0])
    gi = gauge_invariants(st["x"], st["v"], nu, order)
    if not (abs(gi["eps"] / eps - 1.0) <= 1e-11 and abs(gi["j"] / j - 1.0) <= 1e-11):
        raise NoOrbit("unresolved", f"state_from_invariants: the state's invariants (eps={gi['eps']:.15g}, "
                      f"j={gi['j']:.15g}) differ from the requested ones")
    cons = (1,) if order == 1 else (1, 2)
    a = acceleration(st["x"], st["v"], nu, cons)
    rdd = (float(st["v"] @ st["v"]) + float(st["x"] @ a)) / r
    if (rdd <= 0.0) if at == "periapsis" else (rdd >= 0.0):
        if tp["r_p"] is not None and (tp["r_a"] - tp["r_p"]) < 1e-3 * tp["r_c"]:
            raise NoOrbit("unresolved", f"state_from_invariants: the turning point r = {r:.10g} is not a {at} of the "
                          "conservative equations of motion within their truncation (a nearly circular orbit: use "
                          "circular_state)")
        raise NoOrbit("pn_breakdown", f"no {at} with eps={eps:g}, j={j:g}: the turning point r = {r:.6g} of the "
                      f"conserved E and J is not a {at} of the equations of motion (radial acceleration "
                      f"{rdd:.3g}): their O(c^-6) truncation is not small there, the PN orbit is not defined")
    return st


def circular_speed(r: float, nu: float, orders=ORDERS) -> float:
    """Speed of the circular orbit of harmonic radius r under the conservative part of ``orders`` (rdot = 0):
    v^2 r = 1 + A(r, 0, v^2). At rdot = 0, A is a polynomial of degree <= 2 in w = v^2 (Blanchet Eq. (220a)); its
    coefficients are read off exactly from three evaluations and the root continuous with Newton's w = 1/r is taken
    (the stable form of the quadratic formula). Raises NoOrbit("no_circular") where it does not exist (the 2PN
    circular sequence ends at r ~ 2.6 for nu = 1/4)."""
    o = tuple(k for k in _orders(orders) if k in (1, 2))
    if not (r > 0.0 and math.isfinite(r)):
        raise NoOrbit("no_circular", f"circular_speed: r must be positive, got {r}")
    w1, w2 = 1.0 / r, 2.0 / r
    A0 = float(coefficients(r, 0.0, 0.0, nu, o)[0])
    Aa = float(coefficients(r, 0.0, w1, nu, o)[0])
    Ab = float(coefficients(r, 0.0, w2, nu, o)[0])
    A2 = (Ab - 2.0 * Aa + A0) / (2.0 * w1 * w1)  # exact for the quadratic, up to rounding
    A1 = (Aa - A0) / w1 - A2 * w1
    b, c = r - A1, 1.0 + A0  # A2 w^2 - b w + c = 0
    disc = b * b - 4.0 * A2 * c
    if not (b > 0.0 and c > 0.0 and disc >= 0.0):
        raise NoOrbit("no_circular", f"circular_speed: no circular orbit at r = {r:g} for nu = {nu:g} under the "
                      f"orders {o} (v^2 r = 1 + A has no positive root continuous with Newton's)")
    w = 2.0 * c / (b + math.sqrt(disc))
    return math.sqrt(w)


def circular_invariants(r: float, nu: float, order: int = 2) -> dict:
    """eps and j (Eq. (345)) of the circular orbit of harmonic radius r under the conservative equations of
    ``order`` (1: 1PN, 2: 1PN + 2PN), with E and J of the same order."""
    o = (1,) if order == 1 else (1, 2)
    v = circular_speed(r, nu, o)
    return gauge_invariants([r, 0.0, 0.0], [0.0, v, 0.0], nu, order)


def j_circular(eps: float, nu: float, order: int = 2) -> float:
    """j of the circular orbit with energy eps (the largest j of any orbit with this energy, up to the O(c^-6)
    difference between the equations of motion and their conserved E, J): eps_circ(r) = eps solved by Brent's
    method in ln r."""
    from scipy import optimize
    pk = circular_binding_peak(nu, order)
    if not 0.0 < eps < pk["eps"]:
        raise NoOrbit("no_circular", f"j_circular: the circular sequence has no orbit with eps = {eps:g} (its binding "
                      f"peaks at eps = {pk['eps']:.6g}, r = {pk['r']:.6g})")

    def f(lr):
        return circular_invariants(math.exp(lr), nu, order)["eps"] / eps - 1.0
    lr = optimize.brentq(f, math.log(pk["r"]), math.log(max(3.0 / eps, 2.0 * pk["r"])), xtol=1e-15, rtol=8.9e-16)
    return circular_invariants(math.exp(lr), nu, order)["j"]


def circular_binding_peak(nu: float, order: int = 2) -> dict:
    """The circular orbit of largest binding eps along the circular sequence of the truncated equations (the PN
    analogue of an innermost stable circular orbit; for nu = 1/4 at 2PN: r ~ 8, eps ~ 0.087): dict(r, eps, j)."""
    from scipy import optimize
    res = optimize.minimize_scalar(lambda q: -circular_invariants(q, nu, order)["eps"], bounds=(4.0, 40.0),
                                   method="bounded", options={"xatol": 1e-10})
    ci = circular_invariants(float(res.x), nu, order)
    return {"r": float(res.x), "eps": ci["eps"], "j": ci["j"]}


def _energy_order(o) -> int:
    return 2 if 2 in o else (1 if 1 in o else 0)


def adiabatic_radial_velocity(r: float, nu: float, orders=ORDERS) -> float:
    """dr/dt of the adiabatic inspiral through the circular orbit of radius r, from the engine's own equations:
    vr = (dE/dt)_RR / (dE_circ/dr), the rate of E (the conserved energy of the conservative orders) under the
    radiation-reaction terms of ``orders`` at the circular state (complex-step derivative) over the slope of E along
    the circular sequence of ``circular_speed`` (4th-order central difference, step 1e-3 r: relative error ~1e-12).
    Unlike the re-expanded Eq. (227a) it stays consistent with the equations of motion in strong field (at r = 10,
    nu = 1/4 it is 0.49 of Eq. (227a))."""
    o = _orders(orders)
    rr = tuple(k for k in o if k in (2.5, 3.5))
    if not rr:
        return 0.0
    eo = _energy_order(o)
    vt = circular_speed(r, nu, o)
    x, v = np.array([r, 0.0, 0.0]), np.array([0.0, vt, 0.0])
    zero = np.zeros(3)
    dE = float(directional(lambda X, V: energy(X, V, nu, eo), x, v, zero, perturbation(x, v, nu, rr)))

    def Ec(q):
        return float(energy([q, 0.0, 0.0], [0.0, circular_speed(q, nu, o), 0.0], nu, eo))
    h = 1e-3 * r
    dEdr = (-Ec(r + 2 * h) + 8.0 * Ec(r + h) - 8.0 * Ec(r - h) + Ec(r - 2 * h)) / (12.0 * h)
    return dE / dEdr


def _reduce_eccentricity(st: dict, nu: float, o) -> dict:
    """One eccentricity-reduction step: follow the start for three orbits, fit the radial velocity as a smooth
    quadratic trend plus Bc cos(kappa t) + Bs sin(kappa t) (kappa = Omega / K, K the circular periastron factor of
    Blanchet Eq. (353) to 2PN), and remove the oscillation: an excess radial velocity d vr shows as Bc = d vr, an
    excess tangential speed d vt as Bs = 2 K d vt (epicycles)."""
    r0 = float(np.linalg.norm(st["x"]))
    Om = float(st["v"][1]) / r0
    xx = Om ** (2.0 / 3.0)
    K = 1.0 + 3.0 * xx + (13.5 - 7.0 * nu) * xx * xx
    kap = Om / K
    T = 3.0 * 2.0 * math.pi / Om
    out = integrate(st, float(st["t"]) + T, nu, orders=o, n_out=3000, rtol=1e-12)
    t = out["t"] - float(st["t"])
    rd = np.sum(out["x"] * out["v"], axis=1) / np.linalg.norm(out["x"], axis=1)
    B = np.column_stack([np.ones_like(t), t, t * t, np.cos(kap * t), np.sin(kap * t)])
    c, *_ = np.linalg.lstsq(B, rd, rcond=None)
    v = np.array(st["v"], float)
    v[0] -= c[3]
    v[1] -= c[4] / (2.0 * K)
    return state(st["t"], st["x"], v)


def circular_state(r: float, nu: float, orders=ORDERS, t: float = 0.0, quasi: bool = True,
                   reduce_eccentricity: int = 0) -> dict:
    """A circular orbit of harmonic radius r in the xy-plane (tangential speed ``circular_speed``). With ``quasi``
    and radiation reaction among ``orders`` the start gets the radial velocity of the engine's own adiabatic inspiral
    (``adiabatic_radial_velocity``), which removes most of the eccentricity a purely circular start would get; each
    of ``reduce_eccentricity`` further steps follows the start for three orbits and removes the measured radial
    oscillation. Residual eccentricity (radial oscillation / r over three orbits, nu = 1/4, all orders; tests):
    r = 40: circular 3.6e-4, quasi 3.6e-7, one reduction 1e-8; r = 20: 1.8e-3, 1.5e-5, 9e-7; r = 15: 2.9e-3, 7.5e-5,
    1.2e-5; r = 12: 2.5e-3, 1.5e-4, 7e-5; r = 10: 1.9e-3, 2.9e-4, 1.5e-4 (the inspiral itself is no longer
    adiabatic there). The re-expanded Eq. (227a) used before gave 2.6e-3 at r = 10, more than a circular start."""
    o = _orders(orders)
    vt = circular_speed(r, nu, o)
    vr = adiabatic_radial_velocity(r, nu, o) if quasi else 0.0
    st = state(t, [r, 0.0, 0.0], [vr, vt, 0.0])
    if quasi and vr != 0.0:
        for _ in range(int(reduce_eccentricity)):
            st = _reduce_eccentricity(st, nu, o)
    return st


# --- integration ----------------------------------------------------------------------------------------------------

class _Cartesian:
    """y = (x, v) in the scaled units."""

    def __init__(self, st, nu, orders):
        self.nu, self.orders = nu, orders
        self.y0 = np.concatenate([st["x"], st["v"]])
        r0 = float(np.linalg.norm(st["x"]))
        vs = max(float(np.linalg.norm(st["v"])), math.sqrt(1.0 / r0))
        self.scale = np.array([r0] * 3 + [vs] * 3)

    def rhs(self, t, y):
        return np.concatenate([y[3:], acceleration(y[:3], y[3:], self.nu, self.orders)])

    def xv(self, y):
        y = np.asarray(y)
        return y[:3], y[3:]


class _Elements:
    """Variation of constants in the orbital plane: y = (h - h0, A - A0 (2), phi), theta = theta0 + n0 (t - t0) + phi,
    with h the z-component of x x v and A the Laplace-Runge-Lenz vector (m = 1)."""

    def __init__(self, st, nu, orders):
        self.nu, self.orders = nu, orders
        x, v = st["x"], st["v"]
        hv = np.cross(x, v)
        hn = float(np.linalg.norm(hv))
        if hn == 0.0:
            raise ValueError("elements: radial motion (h = 0) has no orbital plane; use 'cartesian'")
        self.ez = hv / hn
        self.e1 = x / float(np.linalg.norm(x))
        self.e2 = np.cross(self.ez, self.e1)
        X, Y = float(x @ self.e1), float(x @ self.e2)
        VX, VY = float(v @ self.e1), float(v @ self.e2)
        r = math.hypot(X, Y)
        self.h0 = X * VY - Y * VX
        self.A0 = np.array([VY * self.h0 - X / r, -VX * self.h0 - Y / r])
        self.theta0 = math.atan2(Y, X)
        E = 0.5 * (VX * VX + VY * VY) - 1.0 / r
        self.n0 = (-2.0 * E) ** 1.5 if E < 0 else 0.0
        self.t0 = float(st["t"])
        self.y0 = np.zeros(4)
        self.scale = np.array([abs(self.h0), 1.0, 1.0, 1.0])

    def planar(self, t, y):
        h = self.h0 + y[0]
        Ax, Ay = self.A0[0] + y[1], self.A0[1] + y[2]
        th = self.theta0 + self.n0 * (t - self.t0) + y[3]
        c, s = math.cos(th), math.sin(th)
        r = h * h / (1.0 + Ax * c + Ay * s)
        return h, Ax, Ay, c, s, r

    def rhs(self, t, y):
        h, Ax, Ay, c, s, r = self.planar(t, y)
        X, Y = r * c, r * s
        VX, VY = -(Ay + s) / h, (Ax + c) / h
        f = perturbation(np.array([X, Y, 0.0]), np.array([VX, VY, 0.0]), self.nu, self.orders)
        fx, fy = float(f[0]), float(f[1])
        L = X * fy - Y * fx  # (x x f)_z
        return np.array([L, h * fy + L * VY, -h * fx - L * VX, h / (r * r) - self.n0])

    def xv(self, y, t):
        h, Ax, Ay, c, s, r = self.planar(t, y)
        X, Y = r * c, r * s
        VX, VY = -(Ay + s) / h, (Ax + c) / h
        return X * self.e1 + Y * self.e2, VX * self.e1 + VY * self.e2

    def elements(self, y) -> dict:
        """h - h0, A - A0 and the cancellation-free change of the osculating semi-major axis a = h^2/(1 - A^2)."""
        dh, dA = y[0], np.array([y[1], y[2]])
        A = self.A0 + dA
        A02 = float(self.A0 @ self.A0)
        A2 = float(A @ A)
        dh2 = dh * (2.0 * self.h0 + dh)
        dA2 = float(dA @ (2.0 * self.A0 + dA))
        a0 = self.h0**2 / (1.0 - A02)
        da = (dh2 * (1.0 - A02) + self.h0**2 * dA2) / ((1.0 - A2) * (1.0 - A02))
        return {"dh": dh, "dA": dA, "a0": a0, "da": da, "e": math.sqrt(A2)}


def _system(st, nu, orders, method):
    if method == "cartesian":
        return _Cartesian(st, nu, orders)
    if method == "elements":
        return _Elements(st, nu, orders)
    raise ValueError("method: 'cartesian' or 'elements'")


class PrecisionWarning(UserWarning):
    """The chosen integration route cannot resolve the requested effect in double precision."""


def _check_start(st, nu, orders, method, rtol, r_stop):
    x0, v0 = np.asarray(st["x"], float), np.asarray(st["v"], float)
    r0 = float(np.linalg.norm(x0))
    if r_stop is not None and not r0 > r_stop:
        raise ValueError(f"pn_binary: the start r = {r0:.6g} is not above r_stop = {r_stop:.6g}")
    rr = tuple(k for k in orders if k in (2.5, 3.5))
    if method == "cartesian" and rr:
        # relative change of the orbit per period by the reaction, against what a Cartesian run resolves (review B5,
        # N12: for PSR B1913+16, 1.6e-12 per orbit, the Cartesian route gave Pb_dot 96 % off)
        per_orbit = 2.0 * math.pi * float(np.linalg.norm(perturbation(x0, v0, nu, rr))) * r0 * r0
        if per_orbit < 1e3 * rtol:
            import warnings
            warnings.warn(f"pn_binary: the radiation reaction changes this orbit by ~{per_orbit:.1e} per period, "
                          f"below what the Cartesian route resolves at rtol = {rtol:g} (~1e3 rtol); use "
                          "method='elements'", PrecisionWarning, stacklevel=4)


def _solve(st, dt, nu, orders, method, rtol, r_stop):
    """One error-controlled DOP853 run from st over dt; returns (system, scipy solution, (t, y) -> (x, v))."""
    _check_start(st, nu, orders, method, rtol, r_stop)
    sysm = _system(st, nu, orders, method)
    t0 = float(st["t"])
    if method == "cartesian":
        def xv(t, y):
            return sysm.xv(y)
        atol = 1e-3 * rtol * sysm.scale
    else:
        def xv(t, y):
            return sysm.xv(y, t)
        # the variables are the changes caused by the perturbation f: their absolute floor is 1e-3 rtol of the
        # relative perturbation |f| r^2 at the start (so a weak perturbation is still resolved to rtol)
        x0, v0 = np.asarray(st["x"], float), np.asarray(st["v"], float)
        r0 = float(np.linalg.norm(x0))
        ep = float(np.linalg.norm(perturbation(x0, v0, nu, orders))) * r0 * r0 if orders else 0.0
        ep = max(ep, 1e-300)
        atol = 1e-3 * rtol * np.array([ep * abs(sysm.h0), ep, ep, 1.0])

    def peri(t, y):
        x, v = xv(t, y)
        return float(x @ v)
    peri.direction = 1

    def apo(t, y):
        x, v = xv(t, y)
        return float(x @ v)
    apo.direction = -1
    events = [peri, apo]
    if r_stop is not None:
        def stop(t, y):
            x, _ = xv(t, y)
            return float(np.linalg.norm(x)) - r_stop
        stop.terminal = True
        stop.direction = -1
        events.append(stop)
    sol = _si.solve_ivp(sysm.rhs, (t0, t0 + dt), sysm.y0, method="DOP853", rtol=rtol, atol=atol,
                        dense_output=True, events=events)
    if sol.status < 0:
        x_end, _ = xv(float(sol.t[-1]), sol.y[:, -1])
        raise RuntimeError(f"pn_binary: the integration stopped at t = {float(sol.t[-1]):.6g}, "
                           f"r = {float(np.linalg.norm(x_end)):.4g} G m/c^2 ({sol.message}): the orbit plunges and "
                           "the PN equations break down; pass r_stop (e.g. 6) to end the run there")
    if sol.status == 1 and len(sol.t) >= 2:
        # stopped at r_stop: the event is located on the interpolant, less accurate than the steps; Newton steps on
        # the event time (dr/dt = x.v/r), each redoing the last step exactly, give the final state the integrator's
        # accuracy at r = r_stop
        tb, yb, te = float(sol.t[-2]), sol.y[:, -2], float(sol.t[-1])
        for _ in range(3):
            y = _si.solve_ivp(sysm.rhs, (tb, te), yb, method="DOP853", rtol=rtol, atol=atol).y[:, -1]
            x, v = xv(te, y)
            r = float(np.linalg.norm(x))
            te = te - (r - r_stop) / (float(x @ v) / r)
        sol.t[-1] = te
        sol.y[:, -1] = _si.solve_ivp(sysm.rhs, (tb, te), yb, method="DOP853", rtol=rtol, atol=atol).y[:, -1]
    return sysm, sol, xv


def _after(times, t0):
    """Event times strictly after the start (a start exactly at a turning point is not an event of the run)."""
    te = np.asarray(times, float)
    return te[te > t0 + 1e-12 * max(1.0, abs(t0))]


def step(st: dict, dt: float, nu: float, orders=ORDERS, method: str = "cartesian", rtol: float = 1e-12,
         r_stop: float | None = None) -> tuple[dict, dict]:
    """Advance a state by dt (scaled units; dt > 0). Returns (new state, info), info = {"status": "running" or
    "r_stop" (the separation fell to r_stop: the new state is there), "t_peri", "t_apo": the periapsis and apoapsis
    times inside the step}. The result depends only on the arguments, so a saved state restarts bit for bit;
    splitting dt into several steps changes the result only at the level of the error tolerance."""
    if not dt > 0.0:
        raise ValueError("step: dt must be positive")
    o = _orders(orders)
    t0 = float(st["t"])
    sysm, sol, xv = _solve(st, dt, nu, o, method, rtol, r_stop)
    t1 = float(sol.t[-1])
    x, v = xv(t1, sol.y[:, -1])
    stopped = r_stop is not None and sol.t_events[2].size > 0
    return state(t1, x, v), {"status": "r_stop" if stopped else "running",
                             "t_peri": _after(sol.t_events[0], t0), "t_apo": _after(sol.t_events[1], t0)}


def integrate(st: dict, t_end: float, nu: float, orders=ORDERS, method: str = "cartesian", n_out: int = 2000,
              rtol: float = 1e-12, r_stop: float | None = None) -> dict:
    """Whole-run integration from st to the time t_end (scaled units). Returns dict(t, x (n, 3), v (n, 3), t_peri,
    t_apo, status, end (the final state), at (a callable: t -> (x, v) on the dense solution)); with
    ``method="elements"`` also "elements": the osculating changes at each periapsis passage (dicts with dh, dA,
    a0, da (the cancellation-free change of the osculating semi-major axis), e, t)."""
    o = _orders(orders)
    t0 = float(st["t"])
    sysm, sol, xv = _solve(st, t_end - t0, nu, o, method, rtol, r_stop)
    t = np.linspace(t0, float(sol.t[-1]), n_out)
    Y = sol.sol(t)
    X = np.empty((n_out, 3))
    V = np.empty((n_out, 3))
    for k in range(n_out):
        X[k], V[k] = xv(t[k], Y[:, k])
    tp, ta = _after(sol.t_events[0], t0), _after(sol.t_events[1], t0)
    stopped = r_stop is not None and sol.t_events[2].size > 0
    xe, ve = xv(float(sol.t[-1]), sol.y[:, -1])
    out = {"t": t, "x": X, "v": V, "t_peri": tp, "t_apo": ta, "status": "r_stop" if stopped else "running",
           "end": state(float(sol.t[-1]), xe, ve), "at": lambda tt: xv(tt, sol.sol(tt))}
    if method == "elements":
        out["elements"] = [dict(sysm.elements(sol.sol(tk)), t=float(tk)) for tk in tp]
    return out


def averaged_dissipation(st: dict, nu: float, conservative=(1, 2), dissipative=(2.5, 3.5), order: int = 2,
                         rtol: float = 1e-13) -> dict:
    """Secular rates of E/mu and of J/mu (its component along the orbit's normal) caused by the dissipative terms,
    to first order in them: the conservative orbit through st is followed from a periapsis to the next, and
    (dE/dv) . a_diss, (dJ/dv) . a_diss are integrated along it (complex-step derivatives) and divided by the radial
    period P_r. Over a radial period the conservative change of E and J (functions of r, rdot, v^2, periodic there)
    cancels, so these are the orbit-averaged losses. Returns dict(dE, dJ, P_r, Phi), Phi the angle swept from
    periapsis to periapsis (2 pi K)."""
    cons = _orders(conservative)
    diss = _orders(dissipative)
    x0, v0 = np.asarray(st["x"], float), np.asarray(st["v"], float)
    ez = np.cross(x0, v0)
    ez = ez / np.linalg.norm(ez)
    zero = np.zeros(3)

    def Ef(x, v):
        return energy(x, v, nu, order)

    def Jf(x, v):
        return np.sum(angular_momentum(x, v, nu, order) * ez, axis=-1)

    def rhs(t, y):
        x, v = y[:3], y[3:6]
        a = acceleration(x, v, nu, cons)
        ad = perturbation(x, v, nu, diss) if diss else zero
        dphi = float(np.cross(x, v) @ ez) / float(x @ x)
        return np.concatenate([v, a, [directional(Ef, x, v, zero, ad), directional(Jf, x, v, zero, ad), dphi]])

    def peri(t, y):
        return float(y[:3] @ y[3:6])
    peri.direction = 1

    gi = gauge_invariants(x0, v0, nu, min(order, 2))
    if gi["eps"] <= 0.0:
        raise ValueError("averaged_dissipation: unbound orbit")
    # the search window from the PN radial period (Eq. (348a)), not the Newtonian one: PN orbits started from
    # Newtonian data can be much wider
    span = (0.0, 1.5 * 2.0 * math.pi / mean_motion(gi["eps"], max(gi["j"], 1e-3), nu))
    r0 = float(np.linalg.norm(x0))
    scale = np.array([r0] * 3 + [max(float(np.linalg.norm(v0)), r0**-0.5)] * 3 + [1.0, 1.0, 1.0])
    y0 = np.concatenate([x0, v0, [0.0, 0.0, 0.0]])
    kw = dict(method="DOP853", rtol=rtol, atol=1e-3 * rtol * scale, events=peri, dense_output=True)
    s1 = _si.solve_ivp(lambda t, y: np.concatenate([y[3:6], acceleration(y[:3], y[3:6], nu, cons), zero]),
                       span, y0, **kw)
    t_first = [t for t in s1.t_events[0] if t > 0.0]
    if not t_first:
        raise ValueError("averaged_dissipation: no periapsis within 1.5 radial periods")
    yp = s1.sol(t_first[0])
    yp[6:] = 0.0
    s2 = _si.solve_ivp(rhs, span, yp, **kw)
    t_next = [t for t in s2.t_events[0] if t > 1e-6 * span[1]]
    if not t_next:
        raise ValueError("averaged_dissipation: no second periapsis")
    Pr = float(t_next[0])
    yend = s2.sol(Pr)
    return {"dE": float(yend[6]) / Pr, "dJ": float(yend[7]) / Pr, "P_r": Pr, "Phi": float(yend[8])}


# --- where the truncated radiation reaction stops being an ordered series (review B6-gravity G1) ---------------
def flux_c1(nu):
    """The 1PN coefficient of the circular-orbit energy flux in x = (m Omega)^(2/3), Blanchet 2014 Eq. (314):
    F = (32/5) nu^2 x^5 [1 + c1 x + ...], c1 = -1247/336 - 35 nu / 12."""
    return -1247.0 / 336.0 - 35.0 / 12.0 * nu


def reaction_on_circle(r, nu, orders=ORDERS):
    """(D / F_N, x) on the circular state of harmonic radius r (``circular_state``): D = -nu dE_2PN/dt
    along the equations of ``orders`` (on a circular state the conservative part leaves the energy unchanged - its
    rate is odd in rdot - so D is the work of the radiation reaction alone), F_N = (32/5) nu^2 x^5, x = (m Omega)^(2/3)
    of the state (review B6-G1)."""
    st = circular_state(r, nu, orders, quasi=False)
    x, v = st["x"], st["v"]
    a = acceleration(x, v, nu, orders)
    D = -nu * float(rate_along(lambda X, V: energy(X, V, nu, 2), x, v, a))
    xx = (float(np.linalg.norm(np.cross(x, v))) / (r * r)) ** (2.0 / 3.0)
    return D / (6.4 * nu * nu * xx ** 5), xx


@functools.lru_cache(maxsize=256)
def reaction_validity_radius(nu):
    """The separation (harmonic, G m/c^2) below which the radiation reaction of the full equations (2.5PN + 3.5PN,
    harmonic gauge) is no longer an ordered series (review B6-G1): its remainder against the 1PN flux,
    |D - F_1PN|, exceeds the 1PN correction it carries, |F_1PN - F_N| = |c1| x F_N - the first neglected order is
    larger than the last kept one. Inside, that remainder (-35.5 x^2 for small x: the 2PN-relative reaction the
    equations lack) cancels the reaction at r = 9.10-9.12 for every nu and the orbit gains energy. The outermost root
    of |D - F_1PN| - |F_1PN - F_N| on circular states between 40 and 9.5 (scanned, then Brent): 10.59 at q = 1, 11.69
    at q = 0.25, 13.01 at q = 0.05."""
    nu = float(nu)
    c1 = flux_c1(nu)

    def h(r):
        d, xx = reaction_on_circle(r, nu)
        return abs(d - (1.0 + c1 * xx)) - abs(c1) * xx
    rs = np.geomspace(40.0, 9.5, 60)
    hs = [h(r) for r in rs]
    for k in range(1, len(rs)):
        if hs[k - 1] < 0.0 <= hs[k]:
            return float(brentq(h, rs[k], rs[k - 1], xtol=1e-9))
    raise RuntimeError(f"reaction_validity_radius: no crossing between 40 and 9.5 for nu = {nu}")  # pragma: no cover
