# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Quadratic drag with a constant drag coefficient, and the hodograph quadrature as its second method (plan M1;
design ``lfphys/sources/explore_2026-11-14_design.md`` §4).

**The model.** F = -(1/2) rho C_d A |v| v, A = pi d^2 / 4, with C_d a constant. The real drag coefficient of a sphere
is a measured function of the Reynolds number Re = rho |v| d / mu (the standard drag curve): 24/Re in creeping flow
(Stokes's law, ``lfphys.core.mechanics.drag``), a slowly varying plateau at 10^3 < Re < 2·10^5, and the drag crisis
near Re ~ 3·10^5 (from 1.5·10^5 to 4·10^5 with the free stream's turbulence and the surface), where it falls to
~0.1. So the constant is a fitted parameter of the plateau, and this is a model, outside the core.

**The constant C_d = 0.47** for a smooth sphere: Hoerner, Fluid-Dynamic Drag (1965), ch. III, p. 3-7 (checked on a scan
of the page, 2026-11-14): "the sphere has a fairly constant drag coefficient (in the order of C_D = 0.47), within the
R'number range between 10^4 and 10^5"; his figure 9 there: 0.47 at R_d = 1.6·10^5 (ARC). The model is used here on
the wider plateau ``RE_RANGE`` = (10^3, 2·10^5). There the measured curve runs from 0.39 to 0.50: Morrison's
correlation of the data (Morrison, "Data Correlation for Drag Coefficient for Sphere", Michigan Tech, 2016, eq. (1);
also Fig. 8.13 of his "An Introduction to Fluid Mechanics", Cambridge 2013), 0.484 at 10^3, 0.392 at 1.4·10^4, 0.426 at
10^5, 0.416 at 2·10^5 (``cd_standard``); the Clift, Grace & Weber (1978) table 5.2 correlations, as transcribed in
Subramanian's course notes (Clarkson University; the book itself not seen), 0.39–0.50 (0.387–0.504). So the constant
0.47 errs by up to +21 % / -7 % on the plateau, relative to the measured value: (0.47 - 0.387) / 0.387 and (0.47 -
0.504) / 0.504 (review R-E F6; before, the sign and the base of (curve - 0.47) / 0.47 were stated). ``validity``
computes, along a flight, the Reynolds range, the share of the drag's work done outside ``RE_RANGE`` and the standard
curve's C_d over the path.

**The second model: the measured curve** (``CurveDrag``). The same force with C_d = ``cd_standard``(Re) taken at the
body's own Reynolds number at every instant (Morrison's correlation, for 0 < Re <= 10^6: it includes the creeping
flow, where it gives Stokes's law, and the drag crisis). A world compares the two models' results (the range, the
optimum angle) to show the constant's model error (review R-E F1, integrator's decision D1). It has no closed form; it
is tested against Radau IIA with the same curve written independently, and, with a constant curve, against
``QuadraticDrag`` and the hodograph.

Not in the model: the drag crisis, rough or felt surfaces (a tennis ball's C_d is its own), the Magnus force of a
spinning ball, the unsteady forces (the added mass, of order rho_air / rho_ball, and the history force) and the
buoyancy (rho_air / rho_ball: 3.3e-3 for a 67 mm ball of 58 g).

**The second method: the hodograph.** With k = rho C_d A / (2 m), u = v_x = v cos(theta) and p = tan(theta) (theta the
velocity's angle above the horizontal), dv_x/dt = -k v v_x and dtheta/dt = -g cos(theta) / v give
du/dtheta = k u^3 / (g cos^3 theta), whose exact first integral is

    1 / u^2 = 1 / u0^2 + (k / g) (F(p0) - F(p)),      F(p) = p sqrt(1 + p^2) + asinh(p)

(= sin(theta)/cos^2(theta) + ln tan(theta/2 + pi/4)); with dp = dtheta / cos^2(theta) the time and the coordinates are
quadratures in p (p decreases monotonically from p0 = tan(theta0) towards -infinity):

    t = (1/g) int_p^p0 u dp,   x = (1/g) int_p^p0 u^2 dp,   y = (1/g) int_p^p0 u^2 p dp.

The landing p_L solves y(p_L) = -h (Brent), the apex is p = 0. This route integrates no differential equation in time
(adaptive Gauss–Kronrod quadrature, scipy.integrate.quad, to 1e-13 relative). The first integral is derived for the
design (from du/dtheta above); it agreed with DOP853 to 1.4e-12 in T and 1.3e-12 in L (design, Appendix A); the tests
repeat it and add Radau IIA.

**The second method in the velocity's angle** (``angle_flight``; design ``explore_EX2_2026-11-18`` §10). With the
real forces (the drag with C_d(Re), or of a spinning ball C_d(Re, S); the buoyancy and the added mass of a body in the
air; forces normal to the velocity in the throw's plane: the Magnus force of a spin normal to the plane and the
Coriolis force's planar part) the hodograph has no first integral, but the equations of the flight written with the
velocity's angle theta as the independent variable stay a short system whose right-hand side is assembled here
independently of ``fly``'s declared forces. With M = m + C_A m_f the inertia, W' = (m - m_f) g the weight less the
buoyancy, D(v) = (1/2) rho C_d A v^2 the drag and N the sum of the normal forces (along n = (-sin theta, cos theta)),

    M dv/dt = -W' sin theta - D,      M v dtheta/dt = N - W' cos theta,

so that, while N < W' cos theta (theta decreases monotonically: always for a topspin, whose Magnus force points to -n,
and for the Coriolis force at S03's scales),

    dt/dtheta = M v / (N - W' cos theta),   dv/dtheta = -(W' sin theta + D) / M dt/dtheta,
    dx/dtheta = v cos theta dt/dtheta,       dy/dtheta = v sin theta dt/dtheta,

integrated by DOP853 in theta from theta_0 down to the landing (y = -h, located by the integrator); the apex is theta
= 0. The normal forces: the Magnus force N = -sign(omega_z) (1/2) rho C_L(S, Re) A v^2 (``theories.models.magnus``'s
2-D convention: omega_z > 0 is topspin), the Coriolis force N = 2 m Omega_z v (``core.mechanics.earth_frame``). With
C_d constant and no other force it is the hodograph (tests: against it, and against DOP853 and Radau IIA in time).

**Vertical motion** (closed forms): up, v(t) = v_t tan(atan(v0/v_t) - g t / v_t), the top at t = (v_t/g) atan(v0/v_t),
h_up = (v_t^2 / 2g) ln(1 + v0^2/v_t^2); down from rest, v(t) = v_t tanh(g t / v_t), the distance (v_t^2/g) ln cosh(g t
/ v_t); v_t = sqrt(g / k).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate, optimize

from lfphys.codes import coded
from lfphys.i18n import T

from ...core import data
from ...core.mechanics.particle import G_STANDARD

ABOUT = {
    "layer": "theories", "kind": "model",
    "title": T("Quadratic air drag with a constant drag coefficient"),
    "statement": T("F = −½·ρ·C_d·A·|v|·v with a constant C_d (0.47 for a smooth sphere), as a declared force of the "
                   "point-body flight; along a flight: the Reynolds number, the share of the drag's work done outside "
                   "the range of the constant C_d, the measured drag curve's C_d for comparison; the second method: "
                   "the exact first integral of the hodograph with the time and the coordinates as quadratures (the "
                   "landing time, the range and the apex without integrating in time); the closed forms of vertical "
                   "motion; the second model: the same force with C_d(Re) from the measured drag curve of a smooth "
                   "sphere (Morrison 2016, 0 < Re ≤ 10⁶) at the body's Reynolds number along the path; the second "
                   "method for the real forces: the flight's equations in its velocity's angle with C_d(Re) or "
                   "C_d(Re, S), the buoyancy, the added mass and forces normal to the velocity (the Magnus force, the "
                   "Coriolis force's planar part)."),
    "validity": T("a sphere at 10³ < Re < 2·10⁵ (below the drag crisis), where the measured C_d runs from 0.39 to "
                  "0.50: the constant 0.47 errs by up to +21 % / −7 % of the measured value; the run reports the share "
                  "of the drag's work done outside this range; the measured curve: 0 < Re ≤ 10⁶, a smooth sphere in "
                  "steady flow, not spinning (a spinning ball: theories.models.magnus), no roughness; the buoyancy and "
                  "the added mass come from the flight's medium; the hodograph and the velocity's angle need a "
                  "horizontal speed > 0, the angle also a monotonic turn of the velocity"),
    "basis": [T("Hoerner, Fluid-Dynamic Drag (1965), ch. III, p. 3-7: C_D ≈ 0.47 for a sphere at Re 10⁴–10⁵"),
              T("Morrison, Data Correlation for Drag Coefficient for Sphere (Michigan Technological University, 2016), "
                "eq. (1); An Introduction to Fluid Mechanics (Cambridge 2013), Fig. 8.13 — the standard drag curve"),
              T("Clift, Grace & Weber, Bubbles, Drops, and Particles (1978), table 5.2 (as transcribed by "
                "Subramanian, Clarkson University course notes)"),
              T("the hodograph's first integral: derived for this engine (design explore 2026-11-14, Appendix A)"),
              T("the flight's equations in the velocity's angle: written for this engine (design explore EX2 "
                "2026-11-18, §10)")],
    "conflicts": [T("the measured drag coefficient of a sphere depends on the Reynolds number (the standard drag "
                    "curve): 24/Re in creeping flow (Stokes's law, lfphys.core.mechanics.drag), the drag crisis near "
                    "Re ≈ 3·10⁵ where C_d falls to about 0.1"),
                  T("rough, seamed or felt balls and spinning balls (the Magnus force) are not described by one "
                    "constant C_d")],
}

#: the smooth sphere's drag coefficient on the plateau (Hoerner 1965, p. 3-7)
CD_SPHERE = 0.47
#: the Reynolds range where the constant is used (the plateau below the drag crisis)
RE_RANGE = (1.0e3, 2.0e5)
#: the measured curve's extremes on RE_RANGE (Morrison 2016 eq. (1) and the Clift-Grace-Weber table, see the docstring)
CD_CURVE_ON_RANGE = (0.387, 0.504)
#: the largest Reynolds number of Morrison's correlation («We do not recommend using equation 1 for Reynolds numbers
#: larger than 10^6»)
RE_CURVE_MAX = 1.0e6


def cd_standard(re):
    """The standard drag curve of a smooth sphere, Morrison's correlation (2016, eq. (1); for Re up to 10^6):
    C_D = 24/Re + 2.6 (Re/5) / (1 + (Re/5)^1.52) + 0.411 (Re/2.63e5)^-7.94 / (1 + (Re/2.63e5)^-8)
          + 0.25 (Re/1e6) / (1 + Re/1e6)."""
    re = np.asarray(re, float)
    if np.any(re <= 0) or np.any(re > RE_CURVE_MAX):
        raise ValueError(T("the drag curve correlation covers 0 < Re ≤ 10⁶"))
    a = re / 2.63e5
    # the third term a^-7.94 / (1 + a^-8) written as a^0.06 / (1 + a^8): the same number, without overflow at small Re
    return 24.0 / re + 2.6 * (re / 5.0) / (1.0 + (re / 5.0) ** 1.52) + 0.411 * a ** 0.06 / (1.0 + a ** 8.0) \
        + 0.25 * (re / 1e6) / (1.0 + re / 1e6)


class QuadraticDrag:
    """F = -(1/2) rho C_d A |v| v, a declared force of ``lfphys.core.mechanics.fly``."""

    def __init__(self, cd: float, area: float, rho: float, *, mu: float | None = None,
                 diameter: float | None = None):
        if not all(math.isfinite(v) and v > 0 for v in (cd, area, rho)):
            raise ValueError(T("the drag coefficient, the area and the density must be > 0"))
        for v in (mu, diameter):
            if v is not None and not (math.isfinite(v) and v > 0):
                raise ValueError(T("the fluid's density and viscosity and the diameter must be > 0"))
        self.cd, self.area, self.rho, self.mu, self.diameter = float(cd), float(area), float(rho), mu, diameter
        self.label = T("quadratic drag")

    @classmethod
    def sphere(cls, diameter: float, medium: dict | None = None, cd: float = CD_SPHERE) -> "QuadraticDrag":
        """A sphere of the given diameter (m) in a medium {rho, mu} (default: air at 20 C, 101325 Pa)."""
        if not (math.isfinite(diameter) and diameter > 0):
            raise ValueError(T("the sphere's diameter must be > 0 (given {d} m)", d=float(diameter)))
        med = data.fluid_properties("air", 20.0) if medium is None else medium
        return cls(cd, math.pi * diameter * diameter / 4.0, med["rho"], mu=med["mu"], diameter=diameter)

    def force(self, t, r, v):
        v = np.asarray(v, float)
        return -0.5 * self.rho * self.cd * self.area * math.sqrt(float(v @ v)) * v

    def k(self, mass: float) -> float:
        """rho C_d A / (2 m), 1/m."""
        return self.rho * self.cd * self.area / (2.0 * mass)

    def terminal_speed(self, mass: float, g: float = G_STANDARD) -> float:
        """sqrt(g / k)."""
        return math.sqrt(g / self.k(mass))

    def reynolds(self, speed):
        if self.mu is None or self.diameter is None:
            raise ValueError(T("the Reynolds number needs the fluid's density, viscosity and the diameter"))
        return self.rho * np.asarray(speed, float) * self.diameter / self.mu


class CurveDrag:
    """F = -(1/2) rho C_d(Re) A |v| v with C_d taken from a drag curve at the body's Reynolds number Re = rho |v| d / mu
    at every instant (default: the standard curve ``cd_standard``, Morrison 2016, 0 < Re <= 10^6): the second model of
    a sphere's air drag, against which the constant C_d is compared. A declared force of ``fly`` with the interface of
    ``QuadraticDrag`` (``force``, ``reynolds``, ``label``) and ``cd_at(speed)``; it has no rate k, since C_d varies.
    At Re << 1 the curve's 24/Re makes it Stokes's law 3 pi mu d v. A speed whose Re is beyond the curve is refused
    (``ValueError``, raised from the integration)."""

    def __init__(self, area: float, rho: float, mu: float, diameter: float, curve=None):
        if not all(math.isfinite(v) and v > 0 for v in (area, rho, mu, diameter)):
            raise ValueError(T("the area, the fluid's density and viscosity and the diameter must be > 0"))
        self.area, self.rho, self.mu, self.diameter = float(area), float(rho), float(mu), float(diameter)
        self.curve = cd_standard if curve is None else curve
        self.label = T("quadratic drag, the measured C_d(Re)")

    @classmethod
    def sphere(cls, diameter: float, medium: dict | None = None, curve=None) -> "CurveDrag":
        """A sphere of the given diameter (m) in a medium {rho, mu} (default: air at 20 C, 101325 Pa)."""
        if not (math.isfinite(diameter) and diameter > 0):
            raise ValueError(T("the sphere's diameter must be > 0 (given {d} m)", d=float(diameter)))
        med = data.fluid_properties("air", 20.0) if medium is None else medium
        return cls(math.pi * diameter * diameter / 4.0, med["rho"], med["mu"], diameter, curve)

    def reynolds(self, speed):
        return self.rho * np.asarray(speed, float) * self.diameter / self.mu

    def cd_at(self, speed):
        """The curve's C_d at the given speed(s) (> 0)."""
        return self.curve(self.reynolds(speed))

    def force(self, t, r, v):
        v = np.asarray(v, float)
        sp = math.sqrt(float(v @ v))
        if sp == 0.0:
            return np.zeros_like(v)
        return -0.5 * self.rho * float(self.cd_at(sp)) * self.area * sp * v


def validity(flight, drag: QuadraticDrag, re_range=RE_RANGE) -> dict:
    """Along a flight with this drag: the Reynolds range, the share of the drag's work done at Re outside ``re_range``
    (the crossings of the range's speeds located on the dense output by Brent's method, the work taken from the carried
    state: exact to the integration's error) and the standard curve's C_d over the path (``cd_standard`` at the
    path's Re, where the correlation applies)."""
    i = next((j for j, f in enumerate(flight.forces) if f is drag), None)
    if i is None:
        raise ValueError(T("this drag is not a force of the flight"))
    lo, hi = (float(re_range[0]), float(re_range[1]))
    T_end = flight.t_end
    ts = np.linspace(0.0, T_end, 4001)
    _, v, W = flight.state(ts)
    re = drag.reynolds(np.linalg.norm(v, axis=1))

    def re_at(t):
        return float(drag.reynolds(np.linalg.norm(flight.state(t)[1])))

    cuts = [0.0]
    for thr in (lo, hi):
        s = np.sign(re - thr)
        for j in np.flatnonzero(s[:-1] * s[1:] < 0):
            cuts.append(optimize.brentq(lambda t: re_at(t) - thr, ts[j], ts[j + 1], xtol=1e-15,
                                        rtol=4.0 * np.finfo(float).eps))
    cuts = sorted(set(cuts + [T_end]))
    W_total = abs(float(flight.state(T_end)[2][i]))
    outside = 0.0
    for a, b in zip(cuts[:-1], cuts[1:]):
        if not (lo <= re_at(0.5 * (a + b)) <= hi):
            outside += abs(float(flight.state(b)[2][i] - flight.state(a)[2][i]))
    ok = (re > 0) & (re <= 1e6)
    curve = cd_standard(re[ok]) if np.any(ok) else np.array([np.nan])
    return {"re_min": float(re.min()), "re_max": float(re.max()), "re_range": (lo, hi),
            "work": W_total, "share_outside": outside / W_total if W_total > 0 else 0.0,
            "cd": drag.cd, "cd_curve_min": float(np.min(curve)), "cd_curve_max": float(np.max(curve))}


# --- closed forms of vertical motion ----------------------------------------------------------------------------------
def vertical_up(t, v0: float, k: float, g: float = G_STANDARD) -> dict:
    """Thrown up at v0 > 0: v(t) and the rise y(t) for 0 <= t <= t_top; also t_top and h_up."""
    vt = math.sqrt(g / k)
    a = math.atan(v0 / vt)
    t = np.asarray(t, float)
    ph = a - g * t / vt
    return {"v": vt * np.tan(ph), "y": (vt * vt / g) * np.log(np.cos(ph) / math.cos(a)),
            "t_top": vt * a / g, "h_up": (vt * vt / (2.0 * g)) * math.log1p((v0 / vt) ** 2)}


def vertical_down(t, k: float, g: float = G_STANDARD) -> dict:
    """Dropped from rest: the downward speed v(t) and the distance fallen."""
    vt = math.sqrt(g / k)
    x = g * np.asarray(t, float) / vt
    return {"v": vt * np.tanh(x), "fallen": (vt * vt / g) * (x + np.log1p(np.exp(-2.0 * x)) - math.log(2.0))}


def fall_time(H: float, k: float, g: float = G_STANDARD) -> float:
    """The time to fall H from rest: (v_t / g) arccosh(exp(g H / v_t^2))."""
    vt = math.sqrt(g / k)
    return (vt / g) * math.acosh(math.exp(g * H / (vt * vt)))


# --- the second method: the hodograph quadrature ---------------------------------------------------------------------
def _F(p):
    return p * math.sqrt(1.0 + p * p) + math.asinh(p)


def hodograph(v0: float, theta0: float, h: float, k: float, g: float = G_STANDARD, epsrel: float = 1e-13) -> dict:
    """The flight with quadratic drag (rate k = rho C_d A / (2 m)) from height h >= 0 at speed v0 and angle theta0
    (radians, |theta0| < pi/2) by the hodograph's first integral: T, L, H, the apex time, the landing speed and
    angle (degrees below the horizontal)."""
    if not (v0 > 0 and abs(theta0) < math.pi / 2 and h >= 0 and k > 0 and g > 0):
        raise ValueError(T("the hodograph needs v0 > 0, |θ0| < 90°, h ≥ 0, k > 0, g > 0"))
    if h == 0 and not theta0 > 0:
        raise coded(ValueError(T("the body starts on the ground and does not move upwards: there is no flight")),
                    "mechanics.no_flight")
    u0 = v0 * math.cos(theta0)
    p0 = math.tan(theta0)
    F0 = _F(p0)
    inv0 = 1.0 / (u0 * u0)

    def u2(p):
        return 1.0 / (inv0 + (k / g) * (F0 - _F(p)))

    def quad(f, a, b):
        if a == b:
            return 0.0
        val, _ = integrate.quad(f, a, b, epsabs=0.0, epsrel=epsrel, limit=400)
        return val

    top = max(p0, 0.0)
    rise = quad(lambda p: u2(p) * p, 0.0, top) / g          # the climb above the launch (0 if p0 <= 0)
    t_rise = quad(lambda p: math.sqrt(u2(p)), 0.0, top) / g
    x_rise = quad(u2, 0.0, top) / g
    start = min(p0, 0.0)  # the descent runs from p = start down to p_L; y(p_L) - y(start) = (1/g) int_pL^start u^2 p dp

    def drop(pL):  # the landing point's height above the ground (zero at the landing)
        return rise + quad(lambda p: u2(p) * p, pL, start) / g + h

    lo = start - 1.0
    while drop(lo) > 0:
        lo = 2.0 * lo - 1.0
        if lo < -1e8:
            raise RuntimeError(T("the hodograph: no landing found"))
    pL = optimize.brentq(drop, lo, start, xtol=1e-15, rtol=4.0 * np.finfo(float).eps, maxiter=200) \
        if drop(start) > 0 else start
    T_ = t_rise + quad(lambda p: math.sqrt(u2(p)), pL, start) / g
    L = x_rise + quad(u2, pL, start) / g
    uL = math.sqrt(u2(pL))
    return {"T": T_, "L": L, "H": h + rise, "t_apex": t_rise if p0 > 0 else None, "p_land": pL,
            "v_land": uL * math.sqrt(1.0 + pL * pL), "angle_land_deg": -math.degrees(math.atan(pL))}


# --- the second method for the real forces: the flight's equations in the velocity's angle -------------------------
def angle_flight(v0: float, theta0: float, h: float, *, mass: float, diameter: float, medium=None, cd=CD_SPHERE,
                 buoyancy: bool = False, added_mass: float = 0.0, spin: float = 0.0, cl=None, omega_z: float = 0.0,
                 g: float = G_STANDARD, rtol: float = 1e-12) -> dict:
    """The flight from height h >= 0 at speed v0 and angle theta0 (radians, |theta0| < pi/2) of a sphere (mass kg,
    diameter m) in a fluid at rest (``medium``: dict or object with rho and mu; default air at 20 °C), by its
    equations in the velocity's angle (module docstring). ``cd``: a constant, or a function cd(re, S) (S the spin
    ratio R |spin| / v, 0 without spin); ``buoyancy``: rho_f V g; ``added_mass``: C_A; ``spin`` (rad/s, the 2-D
    convention of ``magnus``) with ``cl(S, re)`` the lift coefficient; ``omega_z``: the Earth's rotation's component
    normal to the plane (``earth_frame.omega_vector(...)[1]``). Returns T, L, H, the apex time, the landing speed and
    angle (degrees below the horizontal) and the number of right-hand-side evaluations."""
    if not (v0 > 0 and abs(theta0) < math.pi / 2 and h >= 0 and mass > 0 and diameter > 0 and g > 0
            and added_mass >= 0):
        raise ValueError(T("the velocity's angle method needs v0 > 0, |θ0| < 90°, h ≥ 0, a mass and a diameter > 0"))
    if h == 0 and not theta0 > 0:
        raise coded(ValueError(T("the body starts on the ground and does not move upwards: there is no flight")),
                    "mechanics.no_flight")
    med = data.fluid_properties("air", 20.0) if medium is None else medium
    rho, mu = (float(med["rho"]), float(med["mu"])) if isinstance(med, dict) else (float(med.rho), float(med.mu))
    A = math.pi * diameter * diameter / 4.0
    R = 0.5 * diameter
    mf = rho * math.pi * diameter ** 3 / 6.0
    M = mass + added_mass * mf
    Wp = (mass - (mf if buoyancy else 0.0)) * g
    cdf = cd if callable(cd) else (lambda re, S, c=float(cd): c)
    sgn = math.copysign(1.0, spin) if spin != 0.0 else 0.0

    def normal_and_drag(v):
        re = rho * v * diameter / mu
        S = R * abs(spin) / v
        D = 0.5 * rho * float(cdf(re, S)) * A * v * v
        N = 2.0 * mass * omega_z * v
        if sgn != 0.0 and cl is not None:
            N -= sgn * 0.5 * rho * float(cl(S, re)) * A * v * v
        return N, D

    def rhs(th, Y):
        v = Y[0]
        N, D = normal_and_drag(v)
        c, s_ = math.cos(th), math.sin(th)
        den = N - Wp * c
        if not den < 0:
            raise ValueError(T("the velocity's angle does not decrease monotonically: the method does not apply"))
        dt = M * v / den
        return [-(Wp * s_ + D) / M * dt, dt, v * c * dt, v * s_ * dt]

    def land(th, Y):
        return Y[3] + h
    land.terminal, land.direction = True, 0

    th_end = -0.5 * math.pi * (1.0 - 1e-9)
    if h == 0.0:  # from the ground: the landing is the second crossing; start the event past the launch
        land.direction = -1
    sol = integrate.solve_ivp(rhs, (theta0, th_end), [v0, 0.0, 0.0, 0.0], method="DOP853", rtol=rtol,
                              atol=[v0 * rtol, 1e-3 * rtol, 1e-3 * rtol, 1e-3 * rtol], dense_output=True,
                              events=land)
    hits = [k for k, th in enumerate(sol.t_events[0]) if th < theta0 - 1e-15]
    if sol.status < 0 or not hits:
        raise RuntimeError(T("the velocity's angle method found no landing"))
    k = hits[0]
    thL = float(sol.t_events[0][k])
    vL, tL, xL, _ = (float(c) for c in sol.y_events[0][k])
    apex = sol.sol(0.0) if theta0 > 0 else None
    return {"T": tL, "L": xL, "H": h + (float(apex[3]) if apex is not None else 0.0),
            "t_apex": float(apex[1]) if apex is not None else None, "v_land": vL,
            "angle_land_deg": -math.degrees(thL), "nfev": int(sol.nfev)}
