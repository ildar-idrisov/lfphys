# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The rotating Earth as the frame of a flight: the WGS 84 normal gravity and the Coriolis force (design
``lfphys/sources/explore_EX2_2026-11-18_design.md`` §10, §11 item 42).

**The normal gravity.** WGS 84 (NIMA TR8350.2, 3rd ed., 4 July 1997, Amendment 1 of 3 January 2000; checked on its
text 2026-11-18, ``lfphys/sources/s03_forces_2026-11-18.md``): the magnitude of the gradient of the normal potential
on the ellipsoid, the closed formula of Somigliana, eq. (4-1),

    gamma(phi) = gamma_e (1 + k sin^2 phi) / sqrt(1 - e^2 sin^2 phi),      k = b gamma_p / (a gamma_e) - 1,

phi the geodetic latitude, and above the ellipsoid at a small geodetic height h its Taylor series, eq. (4-3),

    gamma_h = gamma [1 - (2 / a)(1 + f + m - 2 f sin^2 phi) h + (3 / a^2) h^2],      m = omega^2 a^2 b / GM.

The constants are the standard's own (Tables 3.1, 3.3, 3.4): a = 6378137.0 m, 1/f = 298.257223563, GM =
3986004.418e8 m^3/s^2, omega = 7292115e-11 rad/s; gamma_e = 9.7803253359 m/s^2, gamma_p = 9.8321849378 m/s^2, k =
0.00193185265241, e^2 = 6.69437999014e-3, m = 0.00344978650684, b = 6356752.3142 m. The normal gravity is the gravity
of the rotating ellipsoid: the centrifugal acceleration is part of it, so a flight in the Earth's frame adds to it only
the Coriolis force. It is the gravity of a model Earth: a real place's gravity differs from it by the anomaly (tens of
mGal, ~1e-5 relative; up to ~3e-4 in high mountains), which a world states as a set-up value. The standard gravity g_n
= 9.80665 m/s^2 (the engine's default) equals the normal gravity on the ellipsoid at 45.50° (``latitude_for_gravity``).

**The Coriolis force.** In the frame rotating with the Earth (angular velocity Omega, |Omega| = omega) a body of mass m
moving at v feels F = -2 m Omega x v; the centrifugal force is in the normal gravity above. At geodetic latitude phi
the local (east, north, up) components of Omega are omega (0, cos phi, sin phi). A flight's 3-D coordinates are the
engine's (x, z, y) with the vertical last (``core.mechanics.particle``); here x points along the azimuth A (clockwise
from north: 0 north, 90° east), z to the LEFT of it and y up, so that (x, z, y) is a right-handed triple (x × z = y)
and the cross product is taken in that order of components:

    Omega = omega (cos phi cos A, cos phi sin A, sin phi)          (x, z, y)

(``omega_vector``). A 2-D flight (x, y) in the vertical plane of the azimuth gets the force's part in that plane,
F = 2 m Omega_z (-v_y, v_x) with Omega_z = omega cos phi sin A: normal to the velocity, so it does no work (the Eötvös
effect: a throw to the east is lighter, to the west heavier); the part normal to the plane, F_z = -2 m (Omega_y v_x -
Omega_x v_y) (to the right of the throw in the northern hemisphere), moves the body out of the plane: ``sideways``
computes that offset by its own first-order equation along the planar flight. Its feedback into the plane is of order
(Omega T)^2 (5e-8 for a 3-s flight): the 3-D flight with the whole force and the planar flight with the sideways
offset agree to that order (tests).

A body in a fluid at rest in the Earth's frame (``particle.Medium``): the Coriolis force acts on the body's own mass m
(the design's -2 m Omega x v). The fluid rotates with the Earth (its vorticity is 2 Omega). In the inviscid theory of a
sphere in a weakly rotational flow (Auton, Hunt & Prud'homme, J. Fluid Mech. 197, 241 (1988), as written in
arXiv:0909.4451, eqs. (3), (5)) the fluid's force on the body is, besides the pressure gradient's (the buoyancy, with
the centrifugal part in the normal gravity), the added mass C_A m_f (Du/Dt - dv/dt) and the lift (1/2) rho_f V (u - v)
x omega, u the fluid's velocity. With the fluid at rest in the rotating frame, Du/Dt - dv/dt = -(a_rel + 2 Omega x v)
(inertial accelerations, the centripetal parts equal) and omega = 2 Omega, so the added mass contributes -2 C_A m_f
Omega x v and the lift +m_f Omega x v: for a sphere (C_A = 1/2) they cancel exactly, and the Coriolis force on m alone is
that theory's result (review EX2, R2-E F5: the Coriolis force on M = m + C_A m_f would keep the first term and miss the
second). At the flight's Reynolds numbers (10^3-10^5, with a wake) the lift coefficient of a sphere in a rotating fluid
is not established; the residual 2 (C_L - C_A) m_f Omega x v is of order m_f / m of the Coriolis effect (3e-3 of it
for S03's light ball, 1.5e-4 for its steel ball) and is not included (stated).

**First-order closed forms** (the references of the checks; the second order is (Omega t)^2 smaller):
a body dropped from rest at height h lands to the EAST of the plumb line by x_E = (1/3) omega g t^3 cos phi, t =
sqrt(2 h / g) (``drop_east_drift``); in vacuum a throw's sideways offset is the quadrature of the out-of-plane force
along the vacuum path, z(T) = -2 int_0^T (T - t) (Omega_y v_x(t) - Omega_x v_y(t)) dt (``sideways`` reduces to it).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate, optimize

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("The rotating Earth as a flight's frame: the WGS 84 normal gravity and the Coriolis force"),
    "statement": T("The WGS 84 normal gravity at a geodetic latitude on the ellipsoid (Somigliana's closed formula) "
                   "and above it (the standard's Taylor series in the height), the centrifugal acceleration included; "
                   "the Coriolis force −2m·Ω×v at a latitude and an azimuth as a declared force of the point-body "
                   "flight (in 3-D the whole force, in the vertical plane its part in the plane), the sideways offset "
                   "of a planar flight by its own first-order equation; the first-order closed forms as references "
                   "(the eastward drift of a dropped body (1/3)·Ω·g·t³·cos φ)."),
    "validity": T("a model Earth: the normal gravity of the WGS 84 ellipsoid (a real place differs by its anomaly, "
                  "about 10⁻⁵, up to 3·10⁻⁴ in mountains: a world states its g); the height series for heights small "
                  "against the Earth's radius (here up to 20 km); a uniform field over the flight; the Earth's mean "
                  "rotation rate (its fluctuations, about 10⁻⁸, neglected); the sideways offset of a planar flight to "
                  "first order (its feedback into the plane is of order (Ω·T)², 5·10⁻⁸ for a 3-s flight); a body in "
                  "a fluid: the Coriolis force on the body's own mass (for a sphere the entrained fluid's Coriolis "
                  "term and the lift on the rotating air's vorticity cancel in the inviscid theory of Auton, Hunt & "
                  "Prud'homme 1988; at the flight's Reynolds numbers their residual, of order ρ_fluid/ρ_body of the "
                  "Coriolis effect, is not included)"),
    "basis": [T("Department of Defense World Geodetic System 1984, NIMA TR8350.2, 3rd ed. (1997, Amendment 1 of "
                "2000): Tables 3.1, 3.3 and 3.4, eqs. (4-1) and (4-3)"),
              "Auton, Hunt & Prud'homme, J. Fluid Mech. 197, 241 (1988): the added mass and the lift of a sphere in "
              "a rotational flow",
              T("the Coriolis force in the local frame and the eastward drift (1/3)·Ω·g·t³·sin θ of a dropped body "
                "(θ the colatitude): K. Intriligator, UC San Diego, lecture of 2020-01-17 (after Taylor, Classical "
                "Mechanics, ch. 9)")],
    "conflicts": [],
}

#: WGS 84 (NIMA TR8350.2, Tables 3.1, 3.3, 3.4): the defining and derived constants used here
WGS84 = {
    "a": 6378137.0,                  # m, semi-major axis (3-1)
    "inv_f": 298.257223563,          # reciprocal of flattening (3-2)
    "GM": 3986004.418e8,             # m^3/s^2 (3-3)
    "omega": 7292115e-11,            # rad/s (3-6)
    "b": 6356752.3142,               # m, semi-minor axis (Table 3.3)
    "e2": 6.69437999014e-3,          # first eccentricity squared (Table 3.3)
    "gamma_e": 9.7803253359,         # m/s^2, normal gravity at the equator (Table 3.4)
    "gamma_p": 9.8321849378,         # m/s^2, normal gravity at the pole (Table 3.4)
    "k": 0.00193185265241,           # normal gravity formula constant (Table 3.4)
    "m": 0.00344978650684,           # omega^2 a^2 b / GM (Table 3.4)
}
#: the Earth's angular velocity, rad/s (WGS 84, eq. (3-6))
OMEGA_EARTH = WGS84["omega"]
#: the largest geodetic height for which the Taylor series (4-3) is used here
H_MAX = 20000.0


def normal_gravity(latitude_deg, height=0.0):
    """The WGS 84 normal gravity (m/s^2) at a geodetic latitude (degrees, -90..90) and a geodetic height (m, |h| <=
    20 km): Somigliana's formula (4-1) on the ellipsoid, the series (4-3) above it. Scalars or arrays."""
    lat = np.asarray(latitude_deg, float)
    h = np.asarray(height, float)
    if not (np.all(np.isfinite(lat)) and np.all(np.abs(lat) <= 90.0)):
        raise ValueError(T("the latitude must be between −90° and 90°"))
    if not (np.all(np.isfinite(h)) and np.all(np.abs(h) <= H_MAX)):
        raise ValueError(T("the height above the ellipsoid must be within ±{h} m", h=H_MAX))
    s2 = np.sin(np.radians(lat)) ** 2
    W = WGS84
    gam = W["gamma_e"] * (1.0 + W["k"] * s2) / np.sqrt(1.0 - W["e2"] * s2)
    f = 1.0 / W["inv_f"]
    a = W["a"]
    out = gam * (1.0 - (2.0 / a) * (1.0 + f + W["m"] - 2.0 * f * s2) * h + 3.0 * h * h / (a * a))
    return float(out) if out.ndim == 0 else out


def latitude_for_gravity(g: float, height: float = 0.0) -> float:
    """The geodetic latitude (degrees, 0..90) where the normal gravity at the given height equals g (Brent's method to
    1e-12 degrees); g must lie between the equator's and the pole's values there."""
    lo, hi = normal_gravity(0.0, height), normal_gravity(90.0, height)
    if not (math.isfinite(g) and lo <= g <= hi):
        raise ValueError(T("g = {g} m/s² is outside the normal gravity's range {lo}–{hi} m/s² at this height",
                           g=float(g), lo=lo, hi=hi))
    return float(optimize.brentq(lambda p: normal_gravity(p, height) - g, 0.0, 90.0, xtol=1e-12, rtol=1e-15))


def omega_vector(latitude_deg: float, azimuth_deg: float, omega: float = OMEGA_EARTH) -> np.ndarray:
    """The Earth's angular velocity in a flight's coordinates (x, z, y): x along the azimuth (degrees clockwise from
    north), z to the left of x, y up: omega (cos phi cos A, cos phi sin A, sin phi)."""
    if not (math.isfinite(latitude_deg) and abs(latitude_deg) <= 90.0 and math.isfinite(azimuth_deg)
            and math.isfinite(omega)):
        raise ValueError(T("the latitude must be between −90° and 90°"))
    p, A = math.radians(latitude_deg), math.radians(azimuth_deg)
    return omega * np.array([math.cos(p) * math.cos(A), math.cos(p) * math.sin(A), math.sin(p)])


class Coriolis:
    """The Coriolis force -2 m Omega x v on a body of mass m (kg) at a geodetic latitude, a flight's x axis along the
    azimuth (degrees clockwise from north): a declared force of ``core.mechanics.fly``. A 3-D flight (x, z, y) gets
    the whole force; a 2-D flight (x, y) its part in the vertical plane, 2 m Omega_z (-v_y, v_x) (its out-of-plane
    part: ``sideways``). It does no work."""

    def __init__(self, mass: float, latitude_deg: float, azimuth_deg: float, omega: float = OMEGA_EARTH):
        if not (math.isfinite(mass) and mass > 0):
            raise ValueError(T("a body needs a finite mass > 0 and a diameter ≥ 0 (given {m} kg, {d} m)",
                               m=float(mass), d=0.0))
        self.mass = float(mass)
        self.latitude, self.azimuth = float(latitude_deg), float(azimuth_deg)
        self.omega = omega_vector(latitude_deg, azimuth_deg, omega)
        self.label = T("Coriolis force")

    def force(self, t, r, v):
        v = np.asarray(v, float)
        Om = self.omega
        if v.size == 3:
            return -2.0 * self.mass * np.cross(Om, v)
        return 2.0 * self.mass * Om[1] * np.array([-v[1], v[0]])

    def out_of_plane(self, v):
        """The force's component along z (to the left) for planar velocities v (n, 2) or (2,), newtons."""
        v = np.asarray(v, float)
        Om = self.omega
        return -2.0 * self.mass * (Om[2] * v[..., 0] - Om[0] * v[..., 1])


def drop_east_drift(h: float, latitude_deg: float, g: float, omega: float = OMEGA_EARTH) -> float:
    """First-order closed form: a body dropped from rest at height h (m) lands (1/3) omega g t^3 cos phi east of the
    plumb line, t = sqrt(2 h / g) (vacuum, uniform g)."""
    if not (h >= 0 and g > 0):
        raise ValueError(T("the drift needs h ≥ 0 and g > 0"))
    t = math.sqrt(2.0 * h / g)
    return omega * g * t ** 3 * math.cos(math.radians(latitude_deg)) / 3.0


def sideways(flight, coriolis: Coriolis, rtol: float = 1e-10) -> dict:
    """The sideways offset of a planar (2-D) flight under the Coriolis force's out-of-plane part, to first order: along
    the computed flight, with M = m + C_A m_f the body's inertia in the medium (m without one),

        M dw/dt = F_z(v(t)) - kappa(t) M w,      dz/dt = w,      kappa = -sum_i (F_i . v) / (M |v|^2),

    w the sideways velocity. kappa is the damping of a sideways motion by the forces along the velocity (exact for a
    drag that opposes v with a magnitude depending on |v|; the forces normal to v in the plane, the Magnus force of a
    spin normal to the plane and the Coriolis force's planar part, do not act on w to first order; buoyancy and added
    mass enter through M). Integrated by DOP853 on the flight's dense output. Returns the offset at the landing
    ``z_land`` (m, positive to the left of the throw), ``right`` = -z_land, and the samples ``t``, ``z``."""
    if flight.dim != 2:
        raise ValueError(T("the sideways offset is computed for a planar (2-D) flight"))
    if not any(f is coriolis for f in flight.forces):
        raise ValueError(T("this Coriolis force is not a force of the flight"))
    M = flight.inertia
    Tend = flight.t_end

    def rhs(t, Y):
        r, v, _ = flight.state(min(t, Tend))
        v2 = float(v @ v)
        tang = 0.0
        if v2 > 0.0:
            for f in flight.forces:
                if f is coriolis:
                    continue
                tang += float(np.asarray(f.force(t, r, v), float) @ v)
        kappa = -tang / (M * v2) if v2 > 0.0 else 0.0
        return [float(coriolis.out_of_plane(v)) / M - kappa * Y[0], Y[0]]

    s = integrate.solve_ivp(rhs, (0.0, Tend), [0.0, 0.0], method="DOP853", rtol=rtol, atol=[1e-16, 1e-16],
                            dense_output=True)
    ts = np.linspace(0.0, Tend, 201)
    z = s.sol(ts)[1]
    return {"z_land": float(s.y[1, -1]), "right": -float(s.y[1, -1]), "w_land": float(s.y[0, -1]),
            "t": ts, "z": z}
