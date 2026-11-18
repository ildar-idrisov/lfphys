# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The air's force on a spinning smooth sphere: the Magnus lift and the spin's increase of the drag, from measured data
(design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §10, §11 item 39; sources and their checks in
``lfphys/sources/s03_forces_2026-11-18.md``).

**The force.** A sphere of diameter D = 2R spinning at omega in a fluid at rest, moving at v, feels besides its drag a
lift normal to v (the Magnus force)

    F_L = (1/2) rho C_L(S, Re) A |v|^2 (omega_perp x v) / (|omega_perp| |v|),     A = pi D^2 / 4,

omega_perp the spin's part normal to v, S = R |omega_perp| / |v| the spin ratio, Re = rho |v| D / mu; and its drag
coefficient grows with the spin, C_D(S, Re) = f(S) C_D(Re) with C_D(Re) the standard curve of a smooth sphere
(``drag_quadratic.cd_standard``, Morrison 2016).

**The data** (both checked on their texts, 2026-11-18):

* Zhou, Zhang & Xu, "Experiments on the Drag and Lift Coefficients of a Spinning Sphere", Water 14, 2593 (2022), CC BY
  4.0: glass spheres of 2.5–8 mm released on a track (their "orbit") 50 mm above a water tank, "the velocities and
  spin speeds of settled spheres were obtained by adjusting the release height of spheres on the orbit"; their speed,
  direction and spin filmed at 400 frames per second, the coefficients from the force balance of the steady motion; Table 2 (22 runs, Re 610–3472, Rr = D Omega / u = 2S from 0.149 to 3.471) and the correlations fitted
  to them and to earlier data for 0 < Re < 3500:
    eq. (8):  C_L = 0.365 (1 + e^(2.229 - 6.5 Rr))^-1 + [Rr - 0.365 (1 + e^(2.229 - 6.5 Rr))^-1] e^(-0.075 (0.5 Rr)^0.4 Re^0.71)
              (0 < Rr < 12; R^2 = 0.873);
    eq. (17): C_DOmega / C_D = 0.989 + 0.482 Rr - 0.093 Rr^2   (0 < Rr < 2.5; R^2 = 0.86);
    eq. (18): C_DOmega / C_D = 2.117 Rr^-0.33                  (2.5 < Rr < 25; R^2 = 0.823).
* Muto, Tsubokura & Oshima, "Negative Magnus lift on a rotating sphere at around the critical Reynolds number", Phys.
  Fluids 24, 014102 (2012), Table I: large-eddy simulations at Re = 1.0·10^4 with the spin parameter Gamma = 0.2 and
  1.0: C_D 0.474 and 0.661, the lift C_Lz 0.167 and 0.301 (means; standard deviations of the fluctuations 0.029 and
  0.096). The paper defines Gamma both as "the ratio of the circumferential velocity to the incoming flow velocity"
  (= S) and by the formula D_p omega / U_0 (= 2S); its drag values agree with Zhou's eq. (17) applied to the standard
  curve for Gamma = S (1.207 and 1.684 times the curve's 0.3926 against 1.167 and 1.581) and not for Gamma = 2S (1.093
  and 1.378), so Gamma = S is used here (a check, not a statement of the paper).

So the model is Zhou's eq. (8) for C_L and eq. (17)–(18) for the drag's factor, on Morrison's curve. Measured at Re
610–3472 and cross-checked at 10^4 by the simulation: its domain here is Re <= 10^4 (S03's chute: 2.0·10^3–6.2·10^3,
S from 1 at the launch to 0.3), S <= 6 (Rr <= 12). **The stated uncertainty** (``LIFT_BAND``, ``DRAG_BAND``): the
spread of the checked values around the model in S03's domain (Re >= 2·10^3, 0.25 <= S <= 1.05: Zhou's runs 7, 9,
10, 12, 13, 19–22 and Muto's Gamma = 1.0): C_L from 0.825 to 1.230 times the model (Muto's 0.301 at Re 10^4 and Zhou's
run 19, 0.449 at Re 2070), the drag's factor from 0.917 to 1.084 times; between Re 3472 and 10^4 no measurement exists
(the simulation's 0.301 at S = 1 is the only value there), so a world shows the band's effect as the uncertainty of
its results. Zhou's coefficients come from a balance of the steady motion (their spheres' drag without spin is 5–20 %
above the standard curve: included in the band through their runs, not corrected).

**The spin** is the caller's: a constant vector, or a function of time. The spin's decay in flight needs the torque of
the air, for which no checked data was found (``s03_forces``); for S03's chute an estimate with a skin friction
coefficient of 0.1 on the whole surface at the largest relative speed (about three times a laminar boundary layer's
1.33/sqrt(Re) at Re 2·10^3) puts the loss below 7 % over the flight, and a loss of 7 % moves the range by at most
0.01 mm (the model's C_L hardly depends on S above S = 0.6: 0.364 at 0.6, 0.365 at 1): the world states it.

Coordinates: as ``core.mechanics.particle`` — 2-D (x, y), 3-D (x, z, y), the vertical last; (x, z, y) is a
right-handed triple (``core.mechanics.earth_frame``: z to the left of x). In 2-D the spin is a number omega_z about z:
positive is topspin for a motion along +x (a ball rolling along +x on the ground spins at omega_z = v / R > 0), and the
lift is sign(omega_z) (1/2) rho C_L A |v| (v_y, -v_x).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T

from ...core import data
from . import drag_quadratic as dq

ABOUT = {
    "layer": "theories", "kind": "model",
    "title": T("The Magnus force and the spin's drag of a smooth sphere, from measured data"),
    "statement": T("The lift of a spinning smooth sphere F = ½·ρ·C_L(S, Re)·A·v² normal to the velocity and the spin "
                   "axis, and its drag coefficient C_D(S, Re) = f(S)·C_D(Re) on the standard drag curve, as declared "
                   "forces of the point-body flight; C_L and f from the measurements of Zhou, Zhang & Xu (2022) at "
                   "Re 600–3500, cross-checked at Re 10⁴ against the simulations of Muto et al. (2012); the stated "
                   "uncertainty band of both from the spread of those data."),
    "validity": T("a smooth sphere with a given spin (constant or a given function of time: the spin's decay is not "
                  "computed) in a fluid at rest, Re ≤ 10⁴ and S ≤ 6; measured at Re 600–3500, between 3500 and 10⁴ "
                  "only one simulated value (S = 1): the model's C_L carries a band of −17.5 % / +23 % and the drag's "
                  "factor −8.3 % / +8.4 % (the data's spread around it at Re ≥ 2000 and S 0.25–1.05); the measured "
                  "coefficients come from a steady force balance"),
    "basis": ["Zhou, Zhang & Xu, Water 14, 2593 (2022), Table 2 and eqs. (8), (17), (18) (CC BY 4.0)",
              "Muto, Tsubokura & Oshima, Phys. Fluids 24, 014102 (2012), Table I",
              T("the standard drag curve: Morrison (2016), through lfphys.theories.models.drag_quadratic")],
    "conflicts": [T("a measured correlation, not a law: the lift of a spinning sphere has no closed form at these "
                    "Reynolds numbers; at higher Re (about 10⁵) the lift can even reverse (the inverse Magnus effect), "
                    "which this model does not describe"),
                  T("at Re 10⁴ a large-eddy simulation gives C_L = 0.301 at S = 1 (Muto et al. 2012), 18 % below "
                    "the model's 0.365: inside its band, the only value between Re 3500 and 10⁴")],
}

#: Zhou, Zhang & Xu (2022), Table 2: (No., D mm, u_s m/s, Omega rad/s, Rr, Re, C_LOmega, C_DOmega), as printed
ZHOU_2022_TABLE2 = (
    (1, 2.5, 0.262, 38.380, 0.366, 655.0, 0.212, 0.627), (2, 2.5, 0.244, 59.890, 0.614, 610.0, 0.349, 0.677),
    (3, 4.0, 0.374, 13.956, 0.149, 1496.0, 0.132, 0.502), (4, 4.0, 0.361, 20.350, 0.225, 1444.0, 0.098, 0.550),
    (5, 4.0, 0.311, 65.130, 0.838, 1244.0, 0.364, 0.657), (6, 4.0, 0.315, 77.920, 0.989, 1260.0, 0.339, 0.648),
    (7, 6.0, 0.417, 34.889, 0.502, 2502.0, 0.261, 0.570), (8, 6.0, 0.386, 223.290, 3.471, 2316.0, 0.318, 0.657),
    (9, 6.0, 0.385, 90.250, 1.406, 2310.0, 0.379, 0.629), (10, 6.0, 0.379, 90.250, 1.429, 2274.0, 0.378, 0.657),
    (11, 6.0, 0.376, 185.140, 2.954, 2256.0, 0.331, 0.697), (12, 6.0, 0.376, 90.250, 1.440, 2256.0, 0.376, 0.674),
    (13, 6.0, 0.374, 87.220, 1.399, 2244.0, 0.393, 0.672), (14, 6.0, 0.366, 195.380, 3.203, 2196.0, 0.402, 0.708),
    (15, 6.0, 0.366, 163.280, 2.677, 2196.0, 0.325, 0.745), (16, 6.0, 0.359, 177.930, 2.974, 2154.0, 0.356, 0.768),
    (17, 6.0, 0.358, 167.470, 2.807, 2148.0, 0.329, 0.783), (18, 6.0, 0.353, 186.660, 3.173, 2118.0, 0.371, 0.792),
    (19, 6.0, 0.345, 115.336, 2.006, 2070.0, 0.449, 0.800), (20, 8.0, 0.434, 103.980, 1.917, 3472.0, 0.358, 0.682),
    (21, 8.0, 0.428, 104.670, 1.956, 3424.0, 0.353, 0.709), (22, 8.0, 0.419, 98.640, 1.883, 3352.0, 0.353, 0.750),
)
#: the water of Zhou's runs: Re = u D / nu with nu = 1.0e-6 m^2/s (the table's Re reproduce it to its digits)
ZHOU_NU = 1.0e-6
#: Muto, Tsubokura & Oshima (2012), Table I at Re = 1.0e4: (Gamma, C_D mean, C_Lz mean, C_Lz s.d.); Gamma read as S
MUTO_2012_RE1E4 = ((0.2, 0.474, 0.167, 0.029), (1.0, 0.661, 0.301, 0.096))
MUTO_RE = 1.0e4
#: the model's domain
RE_MAX = 1.0e4
S_MAX = 6.0
#: S03's domain, where the band is taken: Re >= 2e3, 0.25 <= S <= 1.05
BAND_DOMAIN = {"re_min": 2.0e3, "s_min": 0.25, "s_max": 1.05}


def _check(S, re):
    S = np.asarray(S, float)
    re = np.asarray(re, float)
    if np.any(~np.isfinite(S)) or np.any(S < 0) or np.any(S > S_MAX) or np.any(~np.isfinite(re)) \
            or np.any(re <= 0) or np.any(re > RE_MAX):
        raise ValueError(T("the spinning sphere's data cover 0 < Re ≤ {re:.3g} and 0 ≤ S ≤ {s:.3g}", re=RE_MAX,
                           s=S_MAX))
    return S, re


def cl_zhou(S, re):
    """C_L of a spinning smooth sphere, Zhou, Zhang & Xu (2022) eq. (8) with Rr = 2S (S the spin ratio R omega / v)."""
    S, re = _check(S, re)
    Rr = 2.0 * S
    base = 0.365 / (1.0 + np.exp(2.229 - 6.5 * Rr))
    return base + (Rr - base) * np.exp(-0.075 * (0.5 * Rr) ** 0.4 * re ** 0.71)


def drag_factor(S):
    """C_D(spinning) / C_D(not spinning), Zhou, Zhang & Xu (2022): eq. (17) for Rr = 2S < 2.5, eq. (18) above (Rr up
    to 25 there; here S <= 6). At S = 0 it is eq. (17)'s intercept 0.989 (a fit: within its scatter)."""
    S, _ = _check(S, 1.0)
    Rr = 2.0 * S
    return np.where(Rr < 2.5, 0.989 + 0.482 * Rr - 0.093 * Rr * Rr, 2.117 * np.maximum(Rr, 2.5) ** -0.33)


def _band_points():
    """The checked values in S03's domain and the model's value at each: (source, S, Re, C_L measured, C_L model,
    drag factor measured, drag factor model)."""
    out = []
    for row in ZHOU_2022_TABLE2:
        n, D, u, Om, Rr, re, cl, cd = row
        S = Rr / 2.0
        if re >= BAND_DOMAIN["re_min"] and BAND_DOMAIN["s_min"] <= S <= BAND_DOMAIN["s_max"]:
            cd0 = 24.0 / re + 2.5 / math.sqrt(re) + 0.4  # Zhou's eq. (16): their own non-spinning drag
            out.append((f"Zhou 2022 run {n}", S, re, cl, float(cl_zhou(S, re)), cd / cd0, float(drag_factor(S))))
    for G, cd, cl, _ in MUTO_2012_RE1E4:
        if BAND_DOMAIN["s_min"] <= G <= BAND_DOMAIN["s_max"]:
            out.append((f"Muto 2012 Gamma {G}", G, MUTO_RE, cl, float(cl_zhou(G, MUTO_RE)),
                        cd / float(dq.cd_standard(MUTO_RE)), float(drag_factor(G))))
    return out


def _band():
    pts = _band_points()
    lift = [p[3] / p[4] for p in pts]
    drag = [p[5] / p[6] for p in pts]
    return (min(lift), max(lift)), (min(drag), max(drag))


#: the stated uncertainty: (low, high) factors on the model's C_L and on its drag factor (module docstring)
LIFT_BAND, DRAG_BAND = _band()
EDGES = ("central", "low", "high")


def _edge(edge: str, band) -> float:
    if edge not in EDGES:
        raise ValueError(T("the edge of the band must be central, low or high"))
    return 1.0 if edge == "central" else (band[0] if edge == "low" else band[1])


def cl_band(S, re) -> tuple:
    """(low, model, high) C_L at (S, Re): the model and its stated band."""
    c = cl_zhou(S, re)
    return LIFT_BAND[0] * c, c, LIFT_BAND[1] * c


def _medium(medium):
    med = data.fluid_properties("air", 20.0) if medium is None else medium
    if isinstance(med, dict):
        return float(med["rho"]), float(med["mu"])
    return float(med.rho), float(med.mu)


def _spin(omega, t, dim):
    w = omega(t) if callable(omega) else omega
    w = np.asarray(w, float)
    if dim == 2:
        return float(w) if w.ndim == 0 else float(w.reshape(-1)[0])
    if w.shape != (3,):
        raise ValueError(T("a 3-D flight needs the spin as a vector of 3 components (x, z, y)"))
    return w


class Magnus:
    """The Magnus lift of a smooth sphere of the given diameter spinning at ``omega`` (rad/s; 2-D: a number about z,
    positive = topspin for a motion along +x; 3-D: a vector (x, z, y); or a function of t returning either) in a fluid
    at rest (``medium``: dict or object with rho and mu; default air at 20 °C): a declared force of ``fly``. ``edge``:
    "central" (the model), "low" or "high" (the band's edges)."""

    def __init__(self, diameter: float, omega, medium=None, edge: str = "central"):
        if not (math.isfinite(diameter) and diameter > 0):
            raise ValueError(T("the sphere's diameter must be > 0 (given {d} m)", d=float(diameter)))
        self.diameter = float(diameter)
        self.rho, self.mu = _medium(medium)
        self.area = math.pi * diameter * diameter / 4.0
        self.omega = omega
        self.factor = _edge(edge, LIFT_BAND)
        self.edge = edge
        self.label = T("Magnus force")

    def reynolds(self, speed):
        return self.rho * np.asarray(speed, float) * self.diameter / self.mu

    def spin_ratio(self, t, v) -> float:
        """S = R |omega_perp| / |v| at time t and velocity v."""
        v = np.asarray(v, float)
        sp = math.sqrt(float(v @ v))
        if sp == 0.0:
            return math.inf
        w = _spin(self.omega, t, v.size)
        if v.size == 2:
            return 0.5 * self.diameter * abs(w) / sp
        wp = w - (w @ v) * v / (sp * sp)
        return 0.5 * self.diameter * float(np.linalg.norm(wp)) / sp

    def force(self, t, r, v):
        v = np.asarray(v, float)
        sp = math.sqrt(float(v @ v))
        if sp == 0.0:
            return np.zeros_like(v)
        w = _spin(self.omega, t, v.size)
        q = 0.5 * self.rho * self.area * sp
        if v.size == 2:
            if w == 0.0:
                return np.zeros(2)
            S = 0.5 * self.diameter * abs(w) / sp
            cl = self.factor * float(cl_zhou(S, self.reynolds(sp)))
            return math.copysign(1.0, w) * q * cl * np.array([v[1], -v[0]])
        wp = w - (w @ v) * v / (sp * sp)
        nw = float(np.linalg.norm(wp))
        if nw <= 1e-12 * float(np.linalg.norm(w)):  # a spin along the velocity (to round-off): no lift
            return np.zeros(3)
        S = 0.5 * self.diameter * nw / sp
        cl = self.factor * float(cl_zhou(S, self.reynolds(sp)))
        return q * cl * np.cross(wp, v) / nw


class SpinDrag:
    """The drag of a spinning smooth sphere, F = -(1/2) rho f(S) C_D(Re) A |v| v (``drag_factor`` on the standard
    curve ``drag_quadratic.cd_standard``): a declared force of ``fly`` in place of ``drag_quadratic.CurveDrag`` for a
    spinning ball; the spin as for ``Magnus``. ``edge`` scales f by the band's edges."""

    def __init__(self, diameter: float, omega, medium=None, edge: str = "central"):
        if not (math.isfinite(diameter) and diameter > 0):
            raise ValueError(T("the sphere's diameter must be > 0 (given {d} m)", d=float(diameter)))
        self.diameter = float(diameter)
        self.rho, self.mu = _medium(medium)
        self.area = math.pi * diameter * diameter / 4.0
        self.omega = omega
        self.factor = _edge(edge, DRAG_BAND)
        self.edge = edge
        self.label = T("quadratic drag of a spinning sphere")

    def reynolds(self, speed):
        return self.rho * np.asarray(speed, float) * self.diameter / self.mu

    def cd(self, t, v) -> float:
        """The drag coefficient at time t and velocity v."""
        v = np.asarray(v, float)
        sp = math.sqrt(float(v @ v))
        w = _spin(self.omega, t, v.size)
        if v.size == 2:
            wn = abs(w)
        else:
            wn = float(np.linalg.norm(w - (w @ v) * v / (sp * sp)))
        S = 0.5 * self.diameter * wn / sp
        return self.factor * float(drag_factor(S)) * float(dq.cd_standard(self.reynolds(sp)))

    def force(self, t, r, v):
        v = np.asarray(v, float)
        sp = math.sqrt(float(v @ v))
        if sp == 0.0:
            return np.zeros_like(v)
        return -0.5 * self.rho * self.cd(t, v) * self.area * sp * v
