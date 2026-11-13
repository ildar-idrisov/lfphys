# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Kerr-Newman: neutral test bodies, light rays and clocks around a charged rotating black hole (plan P15.1).

Units G = c = M = 1 (and the Gaussian-type geometrized charge: Q enters the metric as Q^2), spin a = chi, charge q,
chi >= 0, chi^2 + q^2 < 1 (a hole, not the extremal limit). Boyer-Lindquist coordinates (t, r, theta, phi),
Sigma = r^2 + a^2 cos^2 theta, Delta = r^2 - 2 r + a^2 + q^2 (Adamo & Newman 2014, Scholarpedia 9, 31791,
arXiv:1410.6626, "AN14", the definitions under Eq. 2.19). The metric is ``kerr_geodesics.metric(r, theta, chi, q)``.

ONLY NEUTRAL test particles and photons: the hole's electromagnetic field acts on charged bodies, which are not
modelled here; a neutral body or photon follows a geodesic, and the charge acts on it only through the geometry.

Motion. With E = -p_t, L = p_phi, mu^2 = 1 (timelike, p = u per unit rest mass; tau the proper time) or 0 (null),
the Hamilton-Jacobi equation separates (Carter 1968; with the charge: Hackmann & Xu 2013, PRD 87, 124030, "HX13",
Eqs. 11-16 at particle charge e = 0):

    (dtheta/dlambda)^2 = Theta = K - mu^2 a^2 cos^2 theta - W^2 / sin^2 theta,   W = L - a E sin^2 theta,
    (dr/dlambda)^2     = R     = P^2 - (mu^2 r^2 + K) Delta,                     P = (r^2 + a^2) E - a L,
    dphi/dlambda = a P / Delta + W / sin^2 theta,      dt/dlambda = (r^2 + a^2) P / Delta + a W,

in Mino time lambda (dtau = Sigma dlambda). K is Carter's constant in the form of HX13 (K = Q_C + (L - a E)^2,
Q_C = p_theta^2 + cos^2 theta [a^2 (mu^2 - E^2) + L^2 / sin^2 theta], AN14 Eq. 3.3). The state is integrated in the
Hamiltonian form of the separated Hamiltonian K_sep = (1/2)[Delta p_r^2 - P^2/Delta + mu^2 r^2]
+ (1/2)[p_theta^2 + W^2/sin^2 theta + mu^2 a^2 cos^2 theta] (= 0 on shell; Sigma times the geodesic Hamiltonian plus
mu^2 Sigma / 2): dr/dlambda = Delta p_r, dtheta/dlambda = p_theta, dp_r/dlambda = -d/dr of the first bracket,
dp_theta/dlambda = -d/dtheta of the second. Its two brackets are separately constant (= -K/2 and K/2), so the radial
and polar parts conserve their own energies; the mass shell mu^2 = -N/Sigma (N = Delta p_r^2 + p_theta^2 - P^2/Delta +
W^2/sin^2 theta) and K are monitored, E and L are exact (cyclic coordinates). Each body carries the budget of their
drift (review B6-G7): every accepted step may change K and mu^2 by at most sqrt(6) sum_k |dQ/dy_k| rtol scale_k (the
step's weighted RMS error is <= rtol, so each scaled component's error is <= sqrt(6) rtol; the gradient at the step's
end, analytic, ``_grad``), summed over the body's steps (``constants()["budget_K"]``, ``["budget_mu2"]``): linear in
the steps and growing as 1/Delta near the horizon, where the shell's terms P^2/Delta do. The accounting costs 12-14 %
of the integration (100 / 300 bodies: 0.41 / 0.44 ms per unit M of world time against 0.36 / 0.39 without it).

The independent variable is the distant observer's coordinate time t (the playground's world time): dy/dt =
(dy/dlambda) / (dt/dlambda) for y = (r, theta, phi, p_r, p_theta, tau). Each body has its own adaptive step
(Dormand-Prince 8(5,3): the DOP853 tableau of SciPy, ``scipy.integrate.DOP853.A, B, E3, E5``, used unmodified as a
library; the combined error estimate of Hairer & Wanner, err = |h| e5 / sqrt(d (e5 + 0.01 e3)) with e5, e3 the
squared scaled 5th- and 3rd-order estimates, as in the Apache-2.0 Hipparchus DormandPrince853Integrator), all bodies
advanced together (vectorized), landing exactly on the requested t. ``rtol`` is the local error per step relative to
each component's scale (r: r; theta, phi: 1 rad; p_r: |p_r| + |P|/Delta; p_theta: |p_theta| + sqrt(K); tau:
max(|tau|, r)). Events: capture - BL time t never reaches the horizon (r - r_+ ~ exp(-kappa t)); a body is captured
when r <= r_+ + ``capture_eps`` (located to 1e-12 by redoing the step), the event reports t, the proper time there and
the proper time of the crossing itself (dtau/dr = -Sigma/sqrt(R) is finite at r_+; first-order extrapolation, error
O(capture_eps^2)); escape - r >= ``r_escape``. Captured and escaped bodies stop.

Initial states: from a position and the 3-velocity v (|v| < 1) measured by the local zero-angular-momentum observer
(ZAMO; Bardeen, Press & Teukolsky 1972 for Kerr; here from the Kerr-Newman metric): lapse alpha = sqrt(Sigma Delta /
A), frame dragging omega = -g_t phi / g_phi phi = a (2 r - q^2) / A, cylindrical radius varpi = sqrt(A / Sigma)
sin theta, A = (r^2 + a^2)^2 - a^2 Delta sin^2 theta; tetrad e_t = (d_t + omega d_phi)/alpha, e_r = sqrt(Delta/Sigma)
d_r, e_theta = d_theta / sqrt(Sigma), e_phi = d_phi / varpi. Then gamma = 1/sqrt(1 - v^2), E - omega L = alpha gamma,
L = varpi gamma v_phi, p_r = gamma v_r sqrt(Sigma/Delta), p_theta = gamma v_theta sqrt(Sigma); a photon of direction
n and local frequency nu: the same with gamma -> nu, gamma v -> nu n. Positions may be given in the drawing
coordinates of ``kerr_null.cartesian`` (oblate spheroidal: x + i y = sqrt(r^2 + a^2) sin theta e^{i phi},
z = r cos theta); their coordinate directions are orthogonal, and the ZAMO's spatial legs are identified with them
(``zamo_axes``). The momentum's components in the ZAMO's frame and back (``zamo_frame_momentum``,
``momentum_from_frame``: gamma and gamma v given directly, no 1 - v^2 to round near the horizon).

Geometry for drawing (exact where stated): horizons r_pm = 1 pm sqrt(1 - a^2 - q^2) (AN14 Eq. 3.18), ergosurface
r_E(theta) = 1 + sqrt(1 - a^2 cos^2 theta - q^2) (AN14 Eq. 3.23); equatorial circular orbits from the metric:
Omega_pm = pm s / (r^2 pm a s), s = sqrt(r - q^2) (the geodesic condition g_tt' + 2 g_t phi' Omega + g_phi phi'
Omega^2 = 0), dtau/dt = sqrt(-(g_tt + 2 g_t phi Omega + g_phi phi Omega^2)), E = -(g_tt + g_t phi Omega) u^t,
L = (g_t phi + g_phi phi Omega) u^t; the circular photon orbits where dtau/dt = 0 and the ISCO where R'' = 0 along
the circular family - NUMERICAL roots (bracketed Brent, to round-off); closed forms only in the limits (Kerr:
Bardeen-Press-Teukolsky; Reissner-Nordstrom: photon sphere (3 + sqrt(9 - 8 q^2))/2 (Pugliese, Quevedo & Ruffini
2011, Eq. 36), ISCO the largest root of r^3 - 6 r^2 + 9 q^2 r - 4 q^4 (Morales-Herrera et al. 2024, Eq. 20)), which
the tests compare. Clocks: a ZAMO ticks at dtau/dt = alpha, a static observer (outside the ergosurface) at
sqrt(-g_tt), a circular geodesic at the rate above, a free body by its integrated tau.

What an observer sees (``trace_sky``, ``look_directions``): for each pixel of a pinhole camera at (r_o, theta_o) -
the local ZAMO's frame, or a frame moving with a ZAMO-measured velocity (aberration and Doppler by
``core.lorentz.aberrate``) - the arriving light ray is traced back (p -> -p, Mino time, the same vectorized DOP853)
until it is captured (the shadow) or reaches r_far = 1e9 M, where it is taken as straight (bending left < 2 M/r_far):
its direction there is the source's place on the celestial sphere; with each ray its Bardeen constants (lambda, eta)
and nu_inf/nu_obs. Measured: far observer (r = 1e4) sky directions = the exact sweep quadrature to 1e-11 (rtol
1e-10); the Reissner-Nordstrom shadow seen from r = 30 = its closed form sin psi = b_c sqrt(f)/r to 2e-12; Kerr shadow
edges on Bardeen's curve to the decision resolution (1.6e-12 relative). Cost ~0.4 ms per ray (64 x 48 pixels: 1.3 s
on the CPU); rays within ~steps rtol of the critical curve are decided only to that resolution, rays still orbiting
after ``max_steps`` are reported "undecided".
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T
from lfphys import i18n
from lfphys.codes import coded

from . import kerr_null

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": T("Kerr–Newman: test bodies, light rays and clocks near a charged rotating black hole"),
    "statement": T("The Kerr–Newman metric (mass, spin a, charge q) in Boyer–Lindquist coordinates: horizons, "
                   "ergosurface, circular equatorial orbits (Ω, E, L, clock rate), photon orbits and the ISCO; the "
                   "tetrad of the zero-angular-momentum observer (ZAMO): initial conditions from the velocity or the "
                   "ray direction it measures; Hamilton's geodesic equations (Carter's separated form) for many "
                   "bodies and photons at once, stepped in the distant observer's time t, with the proper time of "
                   "every body; conserved E, L, Carter constant K and the mass shell; events: capture by the horizon "
                   "(with the proper time of the crossing) and escape beyond a given radius; the observer's camera (a "
                   "ZAMO or a moving one): for every pixel the ray is traced back to the shadow or to a direction on "
                   "the celestial sphere, with the ray's Bardeen constants and the frequency shift."),
    "validity": T("vacuum (electrovacuum) solution of GR, a² + q² < M², exterior r > r₊; only neutral test bodies and "
                  "photons (charged particles acted on by the hole's field are not modelled); test-body approximation "
                  "(body mass ≪ M, no back-reaction); geometric optics for light. The error is the local tolerance "
                  "rtol per step (DOP853); the drift of K and of the mass shell is shown; circular photon orbits and "
                  "the ISCO are numerical roots (closed forms only in the Kerr and Reissner–Nordström limits)"),
    "basis": ["Newman et al., J. Math. Phys. 6, 918 (1965)",
              "Adamo & Newman, Scholarpedia 9, 31791 (2014), arXiv:1410.6626: Eqs. (2.19), (3.3), (3.18), (3.23)",
              "Carter, Phys. Rev. 174, 1559 (1968)",
              "Hackmann & Xu, Phys. Rev. D 87, 124030 (2013), Eqs. (11)-(16)",
              "Bardeen, Press & Teukolsky, ApJ 178, 347 (1972): ZAMO",
              "Pugliese, Quevedo & Ruffini, Phys. Rev. D 83, 104052 (2011), Eq. (36)",
              "Morales-Herrera et al., Eur. Phys. J. C 84, 525 (2024), Eq. (20)",
              "Keeton & Petters, Phys. Rev. D 72, 104006 (2005), Eqs. (2), (53)",
              T("Gralla & Lupsasca, Phys. Rev. D 101, 044031 (2020), eq. (55): the distant observer's screen (checks)"),
              T("Hairer, Nørsett & Wanner, Solving ODE I (DOP853; SciPy's table)")],
    "conflicts": [],
}

ACTIVE, CAPTURED, ESCAPED = 0, 1, 2
_STATUS = {ACTIVE: "active", CAPTURED: "captured", ESCAPED: "escaped"}
_FORMAT = "lfphys.kerr_newman.geodesics/1"


def _chk(chi, q):
    if not (chi >= 0.0 and chi * chi + q * q < 1.0):
        raise coded(ValueError(T("the hole needs a ≥ 0 and a² + Q² < 1 (a black hole, not the extremal limit)")),
                    "kn.no_horizon")


# --- geometry ------------------------------------------------------------------------------------------------------
def horizons(chi: float, q: float = 0.0) -> tuple[float, float]:
    """(r_+, r_-) = 1 +- sqrt(1 - a^2 - q^2) (AN14 Eq. 3.18)."""
    _chk(chi, q)
    s = math.sqrt(1.0 - chi * chi - q * q)
    return 1.0 + s, 1.0 - s


def ergosurface(theta, chi: float, q: float = 0.0):
    """Outer stationary-limit surface r_E(theta) = 1 + sqrt(1 - a^2 cos^2 theta - q^2) (AN14 Eq. 3.23)."""
    _chk(chi, q)
    return 1.0 + np.sqrt(1.0 - (chi * np.cos(theta)) ** 2 - q * q)


def zamo(r, theta, chi: float, q: float = 0.0) -> dict:
    """ZAMO quantities at (r, theta): alpha (lapse = its clock rate dtau/dt), omega (frame dragging), varpi, Sigma,
    Delta, A."""
    a = chi
    r = np.asarray(r, float)
    s2 = np.sin(theta) ** 2
    sig = r * r + a * a * np.cos(theta) ** 2
    dl = r * r - 2.0 * r + a * a + q * q
    A = (r * r + a * a) ** 2 - a * a * dl * s2
    return {"alpha": np.sqrt(sig * dl / A), "omega": a * (2.0 * r - q * q) / A, "varpi": np.sqrt(A / sig * s2),
            "Sigma": sig, "Delta": dl, "A": A}


def static_clock_rate(r, theta, chi: float, q: float = 0.0):
    """dtau/dt of an observer at rest in Boyer-Lindquist coordinates, sqrt(-g_tt) (NaN inside the ergosurface)."""
    r = np.asarray(r, float)
    sig = r * r + chi * chi * np.cos(theta) ** 2
    g = 1.0 - (2.0 * r - q * q) / sig
    return np.where(g > 0.0, np.sqrt(np.where(g > 0.0, g, 1.0)), np.nan)


def _equatorial_metric(r, chi, q):
    a = chi
    m2 = 2.0 * r - q * q
    return -(1.0 - m2 / (r * r)), -a * m2 / (r * r), r * r + a * a + a * a * m2 / (r * r)


def circular_orbit(r, chi: float, q: float = 0.0, prograde: bool = True) -> dict:
    """Equatorial circular geodesic at radius r: Omega = dphi/dt, dtau_dt (NaN where no timelike orbit), E, L per unit
    mass, u_t (= dt/dtau). From the metric: Omega = +-s/(r^2 +- a s), s = sqrt(r - q^2)."""
    _chk(chi, q)
    a = chi
    r = np.asarray(r, float)
    sg = 1.0 if prograde else -1.0
    s = np.sqrt(r - q * q)
    om = sg * s / (r * r + sg * a * s)
    gtt, gtp, gpp = _equatorial_metric(r, chi, q)
    n = -(gtt + 2.0 * gtp * om + gpp * om * om)
    ok = n > 0.0
    ut = np.where(ok, 1.0 / np.sqrt(np.where(ok, n, 1.0)), np.nan)
    return {"Omega": om, "dtau_dt": np.where(ok, np.sqrt(np.where(ok, n, 1.0)), np.nan), "u_t": ut,
            "E": -(gtt + gtp * om) * ut, "L": (gtp + gpp * om) * ut, "norm": n}


def photon_orbit(chi: float, q: float = 0.0, prograde: bool = True) -> float:
    """Radius of the equatorial circular photon orbit: the root of -(g_tt + 2 g_t phi Omega + g_phi phi Omega^2) = 0
    on the circular family above the horizon (numerical, Brent to round-off)."""
    from scipy.optimize import brentq
    rp = horizons(chi, q)[0]

    def f(r):
        return float(circular_orbit(r, chi, q, prograde)["norm"])
    lo, hi = rp * (1.0 + 1e-12), 5.0
    rs = np.linspace(lo, hi, 400)
    fs = np.array([f(x) for x in rs])
    k = np.flatnonzero((fs[:-1] <= 0.0) & (fs[1:] > 0.0))
    if len(k) == 0:
        raise coded(ValueError(T("no circular photon orbit found")), "kn.no_photon_orbit")
    i = k[-1]
    return brentq(f, rs[i], rs[i + 1], xtol=1e-15, rtol=8.9e-16, maxiter=200)


def _rpp(r, chi, q, prograde):
    """R''(r) of the equatorial radial potential R = P^2 - Delta (r^2 + (L - a E)^2) at the circular orbit's E, L."""
    a = chi
    c = circular_orbit(r, chi, q, prograde)
    E, L = c["E"], c["L"]
    P = (r * r + a * a) * E - a * L
    dl = r * r - 2.0 * r + a * a + q * q
    k0 = (L - a * E) ** 2
    return 2.0 * (2.0 * r * E) ** 2 + 4.0 * P * E - 2.0 * (r * r + k0) - 4.0 * r * (2.0 * r - 2.0) - 2.0 * dl


def isco(chi: float, q: float = 0.0, prograde: bool = True) -> float:
    """Innermost stable circular orbit: R'' = 0 along the circular family (numerical, Brent to round-off)."""
    from scipy.optimize import brentq
    lo = photon_orbit(chi, q, prograde) * (1.0 + 1e-9)
    rs = np.geomspace(lo, 20.0, 600)
    fs = np.array([float(_rpp(x, chi, q, prograde)) for x in rs])
    ok = np.isfinite(fs)
    k = np.flatnonzero(ok[:-1] & ok[1:] & (fs[:-1] > 0.0) & (fs[1:] <= 0.0))
    if len(k) == 0:
        raise coded(ValueError(T("no ISCO found")), "kn.no_isco")
    i = k[-1]
    return brentq(lambda x: float(_rpp(x, chi, q, prograde)), rs[i], rs[i + 1], xtol=1e-15, rtol=8.9e-16,
                  maxiter=200)


def cartesian(r, theta, phi, chi: float):
    """Drawing coordinates (``kerr_null.cartesian``): x + i y = sqrt(r^2 + a^2) sin theta e^{i phi}, z = r cos theta."""
    return kerr_null.cartesian(r, theta, phi, chi)


def from_cartesian(x, y, z, chi: float):
    """Inverse of ``cartesian``: (r, theta, phi); r^2 = [w + sqrt(w^2 + 4 a^2 z^2)]/2, w = x^2 + y^2 + z^2 - a^2."""
    x, y, z = (np.asarray(u, float) for u in (x, y, z))
    a2 = chi * chi
    w = x * x + y * y + z * z - a2
    r2 = 0.5 * (w + np.sqrt(w * w + 4.0 * a2 * z * z))
    r = np.sqrt(r2)
    with np.errstate(invalid="ignore", divide="ignore"):
        ct = np.clip(np.where(r > 0, z / r, 0.0), -1.0, 1.0)
    return r, np.arccos(ct), np.arctan2(y, x)


def zamo_axes(r, theta, phi, chi: float) -> np.ndarray:
    """Unit vectors (rows: r-hat, theta-hat, phi-hat) in drawing coordinates of the coordinate directions at a point:
    the ZAMO's spatial legs as drawn (orthonormal: oblate spheroidal coordinates are orthogonal)."""
    ra = math.sqrt(r * r + chi * chi)
    st, ct, sp, cp = math.sin(theta), math.cos(theta), math.sin(phi), math.cos(phi)
    er = np.array([r / ra * st * cp, r / ra * st * sp, ct])
    et = np.array([ra * ct * cp, ra * ct * sp, -r * st])
    ep = np.array([-sp, cp, 0.0])
    return np.stack([er / np.linalg.norm(er), et / np.linalg.norm(et), ep])


def surface(r_of_theta, chi: float, n_theta: int = 33, n_phi: int = 64):
    """Grid (x, y, z), each (n_theta, n_phi), of the surface r = r_of_theta(theta) in drawing coordinates."""
    th = np.linspace(0.0, math.pi, n_theta)
    ph = np.linspace(0.0, 2.0 * math.pi, n_phi)
    T, P = np.meshgrid(th, ph, indexing="ij")
    R = np.broadcast_to(np.asarray(r_of_theta(T), float), T.shape)
    return cartesian(R, T, P, chi)


# --- initial momenta -----------------------------------------------------------------------------------------------
def momentum_from_zamo(r, theta, chi: float, q: float, v=None, n=None, nu: float = 1.0) -> np.ndarray:
    """Covariant (p_t, p_r, p_theta, p_phi) of a body with ZAMO-measured 3-velocity v = (v_r, v_theta, v_phi), |v| < 1
    (per unit rest mass), or of a photon of ZAMO direction n (normalized here) and local frequency nu."""
    _chk(chi, q)
    if math.sin(theta) < 1e-9:
        raise coded(ValueError(T("on the symmetry axis the Boyer–Lindquist frame is singular: place the body off "
                                 "the axis")), "kn.on_axis")
    z = zamo(r, theta, chi, q)
    if z["Delta"] <= 0.0:
        raise coded(ValueError(T("inside the horizon")), "gr.inside_horizon")
    if (v is None) == (n is None):
        raise ValueError("give either v (a body) or n (a photon)")
    if v is not None:
        v = np.asarray(v, float).reshape(3)
        vv = float(v @ v)
        if not vv < 1.0:
            raise coded(ValueError(T("the local speed |v| must be below c")), "kn.superluminal")
        g = 1.0 / math.sqrt(1.0 - vv)
        pt_hat, sp = g, g * v
    else:
        n = np.asarray(n, float).reshape(3)
        nn = math.sqrt(float(n @ n))
        if nn == 0.0:
            raise coded(ValueError(T("a photon needs a non-zero direction")), "kn.zero_direction")
        pt_hat, sp = float(nu), float(nu) * n / nn
    sig, dl = float(z["Sigma"]), float(z["Delta"])
    L = float(z["varpi"]) * sp[2]
    E = float(z["alpha"]) * pt_hat + float(z["omega"]) * L
    return np.array([-E, sp[0] * math.sqrt(sig / dl), sp[1] * math.sqrt(sig), L])


def zamo_frame_momentum(r, theta, chi: float, q: float, p) -> np.ndarray:
    """The components (p^(t), p^(r), p^(theta), p^(phi)) of the covariant momentum p = (p_t, p_r, p_theta, p_phi) at
    (r, theta) in the local ZAMO's orthonormal frame: the energy and the momentum that observer measures (per unit rest
    mass for a body): p^(t) = (E - omega L) / alpha, p^(r) = p_r sqrt(Delta/Sigma), p^(theta) = p_theta / sqrt(Sigma),
    p^(phi) = L / varpi (E = -p_t, L = p_phi; the tetrad of the module's docstring, BPT 1972 Eqs. 3.9-3.10). The inverse
    of ``momentum_from_frame``; ``Geodesics.zamo_velocity`` is p^(i) / p^(t)."""
    _chk(chi, q)
    if not float(r) * float(r) - 2.0 * float(r) + chi * chi + q * q > 0.0:
        raise coded(ValueError(T("inside the horizon")), "gr.inside_horizon")
    z = zamo(r, theta, chi, q)
    p = np.asarray(p, float).reshape(4)
    E, L = -p[0], p[3]
    sig, dl = float(z["Sigma"]), float(z["Delta"])
    return np.array([(E - float(z["omega"]) * L) / float(z["alpha"]), p[1] * math.sqrt(dl / sig),
                     p[2] / math.sqrt(sig), L / float(z["varpi"])])


def momentum_from_frame(r, theta, chi: float, q: float, p_hat) -> np.ndarray:
    """Covariant (p_t, p_r, p_theta, p_phi) at (r, theta) of the momentum whose components in the local ZAMO's
    orthonormal frame are p_hat = (p^(t), p^(r), p^(theta), p^(phi)): L = varpi p^(phi), E = alpha p^(t) + omega L,
    p_r = p^(r) sqrt(Sigma/Delta), p_theta = p^(theta) sqrt(Sigma) (``momentum_from_zamo`` with gamma and gamma v given
    directly: no 1 - v^2 to round near the horizon). The mass shell p^(t)^2 - |p^(i)|^2 is the caller's."""
    _chk(chi, q)
    if math.sin(theta) < 1e-9:
        raise coded(ValueError(T("on the symmetry axis the Boyer–Lindquist frame is singular: place the body off "
                                 "the axis")), "kn.on_axis")
    if not float(r) * float(r) - 2.0 * float(r) + chi * chi + q * q > 0.0:
        raise coded(ValueError(T("inside the horizon")), "gr.inside_horizon")
    z = zamo(r, theta, chi, q)
    ph = np.asarray(p_hat, float).reshape(4)
    if not ph[0] > 0.0:
        raise ValueError("the frame energy p^(t) must be > 0 (future-directed)")
    sig, dl = float(z["Sigma"]), float(z["Delta"])
    L = float(z["varpi"]) * ph[3]
    E = float(z["alpha"]) * ph[0] + float(z["omega"]) * L
    return np.array([-E, ph[1] * math.sqrt(sig / dl), ph[2] * math.sqrt(sig), L])


# --- the vectorized integrator -------------------------------------------------------------------------------------
_TAB = None


def _tableau():
    """DOP853 (A, B, E3, E5) from SciPy (used unmodified; its 13th error weights are zero)."""
    global _TAB
    if _TAB is None:
        from scipy.integrate import DOP853
        A, B, E3, E5 = (np.asarray(z, float) for z in (DOP853.A, DOP853.B, DOP853.E3, DOP853.E5))
        if A.shape != (12, 12) or B.shape != (12,) or E3[12] != 0.0 or E5[12] != 0.0:
            raise RuntimeError("unexpected DOP853 tableau layout in this SciPy")
        _TAB = (A, B, E3[:12], E5[:12])
    return _TAB


def rhs_mino(y, E, L, mu2, chi, q):
    """d/dlambda (Mino time) of rows y = (r, theta, phi, p_r, p_theta, tau) and dt/dlambda: (dy (n, 6), T (n,))."""
    a = chi
    r, th, pr, pth = y[:, 0], y[:, 1], y[:, 3], y[:, 4]
    s, c = np.sin(th), np.cos(th)
    s2 = s * s
    ra2 = r * r + a * a
    dl = ra2 - 2.0 * r + q * q
    P = ra2 * E - a * L
    W = L - a * E * s2
    Wos2 = W / s2
    T = ra2 * P / dl + a * W
    d = np.empty_like(y)
    d[:, 0] = dl * pr
    d[:, 1] = pth
    d[:, 2] = a * P / dl + Wos2
    d[:, 3] = -0.5 * ((2.0 * r - 2.0) * pr * pr - 4.0 * r * E * P / dl + P * P * (2.0 * r - 2.0) / (dl * dl)
                      + 2.0 * mu2 * r)
    d[:, 4] = c * s * (Wos2 * (2.0 * a * E + Wos2) + mu2 * a * a)  # 2 a E W c/s + W^2 c/s^3 + mu^2 a^2 c s
    d[:, 5] = r * r + a * a * c * c
    return d, T


class Geodesics:
    """Many neutral test bodies and photons in one Kerr-Newman spacetime, advanced in the distant observer's time t.

    Geodesics(chi, q=0.0, *, rtol=1e-10, t=0.0, capture_eps=1e-4, r_escape=1e4)
    """

    def __init__(self, chi: float, q: float = 0.0, *, rtol: float = 1e-10, t: float = 0.0,
                 capture_eps: float = 1e-4, r_escape: float = 1e4):
        _chk(chi, q)
        if not (0.0 < rtol < 1e-2 and capture_eps > 0.0):
            raise ValueError("need 0 < rtol < 1e-2 and capture_eps > 0")
        self.chi, self.q, self.rtol = float(chi), float(q), float(rtol)
        self.capture_eps, self.r_escape = float(capture_eps), float(r_escape)
        self.r_plus = horizons(chi, q)[0]
        if not self.r_escape > self.r_plus + self.capture_eps:
            raise ValueError("r_escape must lie outside the capture radius")
        self._t = float(t)
        self._keys: list = []
        self._y = np.zeros((0, 6))
        self._c = np.zeros((0, 3))       # E, L, mu^2 (nominal)
        self._K0 = np.zeros(0)           # Carter's K at the start (for the drift)
        self._h = np.zeros(0)            # the next step in t of each body
        self._st = np.zeros(0, int)
        self._nst = np.zeros(0, int)     # accepted steps of each body
        self._bud = np.zeros((0, 2))     # the drift budgets of K and mu^2 accumulated over the body's steps
        self._info: dict = {}
        self._next_key = 0
        self._stats = {"steps": 0, "rejected": 0, "rhs_rows": 0}

    # --- bodies --------------------------------------------------------------------------------------------------
    @property
    def t(self) -> float:
        return self._t

    @property
    def keys(self) -> list:
        return list(self._keys)

    @property
    def n(self) -> int:
        return len(self._keys)

    def _row(self, key) -> int:
        try:
            return self._keys.index(key)
        except ValueError:
            raise KeyError(f"no body with key {key!r}") from None

    def add_body(self, r, theta, phi, v=(0.0, 0.0, 0.0), key=None):
        """A timelike body at (r, theta, phi) with ZAMO-measured velocity v; returns its key."""
        p = momentum_from_zamo(r, theta, self.chi, self.q, v=v)
        return self.add_state(r, theta, phi, p, 1.0, key)

    def add_photon(self, r, theta, phi, n, key=None, nu: float = 1.0):
        """A photon at (r, theta, phi) moving along the ZAMO direction n (local frequency nu); returns its key."""
        p = momentum_from_zamo(r, theta, self.chi, self.q, n=n, nu=nu)
        return self.add_state(r, theta, phi, p, 0.0, key)

    def add_state(self, r, theta, phi, p, mu2, key=None, tau=0.0, status="active", K0=None, budget=(0.0, 0.0)):
        """Add a geodesic from its covariant momentum p = (p_t, p_r, p_theta, p_phi) (mu2 = 1: per unit rest mass;
        0: a photon). The mass shell is checked (relative 1e-9 of its terms). A saved state continues its drift
        accounting (review B6-G11): ``K0`` Carter's K at the body's original start and ``budget`` its drift budgets
        (K, mu^2) so far (``constants()``); the shell is then checked to 1e-9 of its terms plus that budget.
        ``status`` "captured" or "escaped" adds a body that has already met that event (it is not advanced) - it must
        lie outside the horizon, not outside the capture radius."""
        r, theta, phi = float(r), float(theta), float(phi)
        p = np.asarray(p, float).reshape(4)
        mu2 = float(mu2)
        codes = {v: k for k, v in _STATUS.items()}
        if status not in codes:
            raise ValueError(f"status must be one of {sorted(codes)}")
        if mu2 not in (0.0, 1.0):
            raise ValueError("mu2 must be 1 (timelike) or 0 (null)")
        if status == "active" and not r > self.r_plus + self.capture_eps:
            raise coded(ValueError(i18n.T("the start must lie outside the capture radius r₊ + ε")), "kn.inside_capture")
        if not r > self.r_plus:
            raise ValueError("a saved state outside the horizon r_+")
        if math.sin(theta) < 1e-9:
            raise ValueError("on the symmetry axis the Boyer-Lindquist frame is singular")
        E, L = -p[0], p[3]
        y = np.array([[r, theta, phi, p[1], p[2], float(tau)]])
        c = np.array([[E, L, mu2]])
        m2, K, scale = self._shell(y, c)
        bud = np.asarray(budget, float).reshape(2)
        if not (np.all(bud >= 0.0) and np.all(np.isfinite(bud))):
            raise ValueError("budget: two finite numbers >= 0")
        if abs(m2[0] - mu2) > 1e-9 * scale[0] + bud[1]:
            raise ValueError(f"momentum off the mass shell: -p.p = {m2[0]!r}, expected {mu2}")
        _, T = rhs_mino(y, c[:, 0], c[:, 1], c[:, 2], self.chi, self.q)
        if not T[0] > 0.0:
            raise ValueError("the momentum is not future-directed")
        if key is None:
            while self._next_key in self._keys:
                self._next_key += 1
            key = self._next_key
            self._next_key += 1
        if isinstance(key, bool) or not isinstance(key, (int, str)) or key in self._keys:
            raise KeyError(f"bad or existing key {key!r}")
        self._keys.append(key)
        self._y = np.vstack([self._y, y])
        self._c = np.vstack([self._c, c])
        self._K0 = np.append(self._K0, K[0] if K0 is None else float(K0))
        self._h = np.append(self._h, self._h0(y, c)[0])
        self._st = np.append(self._st, codes[status])
        self._nst = np.append(self._nst, 0)
        self._bud = np.vstack([self._bud, bud[None]])
        return key

    def remove(self, key):
        i = self._row(key)
        del self._keys[i]
        for name in ("_y", "_c", "_K0", "_h", "_st", "_nst", "_bud"):
            setattr(self, name, np.delete(getattr(self, name), i, axis=0))
        self._info.pop(key, None)

    # --- views ---------------------------------------------------------------------------------------------------
    def bl(self) -> np.ndarray:
        """(n, 3) Boyer-Lindquist r, theta, phi at time t (rows in ``keys`` order)."""
        return self._y[:, :3].copy()

    def cartesian(self) -> np.ndarray:
        """(n, 3) drawing coordinates."""
        return np.stack(cartesian(self._y[:, 0], self._y[:, 1], self._y[:, 2], self.chi), axis=1)

    def proper_time(self) -> np.ndarray:
        """(n,) proper time of each timelike body since its start (for photons: the affine parameter of p)."""
        return self._y[:, 5].copy()

    def status(self) -> list:
        return [_STATUS[int(s)] for s in self._st]

    def is_photon(self) -> np.ndarray:
        return self._c[:, 2] == 0.0

    def momenta(self) -> np.ndarray:
        """(n, 4) covariant momenta (p_t, p_r, p_theta, p_phi)."""
        return np.stack([-self._c[:, 0], self._y[:, 3], self._y[:, 4], self._c[:, 1]], axis=1)

    def zamo_velocity(self) -> np.ndarray:
        """(n, 3) 3-velocity (r-hat, theta-hat, phi-hat) measured by the local ZAMO (|v| = 1 for photons)."""
        y, c = self._y, self._c
        z = zamo(y[:, 0], y[:, 1], self.chi, self.q)
        e = (c[:, 0] - z["omega"] * c[:, 1]) / z["alpha"]
        return np.stack([y[:, 3] * np.sqrt(z["Delta"] / z["Sigma"]), y[:, 4] / np.sqrt(z["Sigma"]),
                         c[:, 1] / z["varpi"]], axis=1) / e[:, None]

    def info(self, key) -> dict:
        """The event a body met (capture or escape), or {}."""
        return dict(self._info.get(key, {}))

    def _shell(self, y, c):
        """(mu^2 = -N/Sigma, Carter's K from the polar part, a scale of the shell's terms) of rows y."""
        a, q = self.chi, self.q
        r, th, pr, pth = y[:, 0], y[:, 1], y[:, 3], y[:, 4]
        E, L, mu2 = c[:, 0], c[:, 1], c[:, 2]
        s2 = np.sin(th) ** 2
        c2 = np.cos(th) ** 2
        dl = r * r - 2.0 * r + a * a + q * q
        P = (r * r + a * a) * E - a * L
        W = L - a * E * s2
        sig = r * r + a * a * c2
        terms = np.stack([dl * pr * pr, pth * pth, P * P / dl, W * W / s2])
        N = terms[0] + terms[1] - terms[2] + terms[3]
        K = pth * pth + W * W / s2 + mu2 * a * a * c2
        return -N / sig, K, np.sum(np.abs(terms), axis=0) / sig

    def constants(self) -> dict:
        """Arrays per body: E, L, K (Carter, HX13 form), Q_C = K - (L - a E)^2, mu2 (-p.p, measured), mu2_nominal,
        K0 (K at the start), dK (K - K0), dmu2 (mu2 - nominal), steps (accepted steps), budget_K and budget_mu2 (the
        most the steps' allowed local errors can have changed K and mu^2: |dK| <= budget_K + the rounding of K's
        evaluation, a few u K; |dmu2| <= budget_mu2 + a few u shell_scale), shell_scale (the sum of the shell's
        |terms| / Sigma)."""
        m2, K, sc = self._shell(self._y, self._c)
        E, L = self._c[:, 0], self._c[:, 1]
        return {"E": E.copy(), "L": L.copy(), "K": K, "Q_C": K - (L - self.chi * E) ** 2, "mu2": m2,
                "mu2_nominal": self._c[:, 2].copy(), "dK": K - self._K0, "dmu2": m2 - self._c[:, 2],
                "steps": self._nst.copy(), "budget_K": self._bud[:, 0].copy(), "budget_mu2": self._bud[:, 1].copy(),
                "shell_scale": sc, "K0": self._K0.copy()}

    def _grad(self, y, c):
        """Analytic gradients of Carter's K and of mu^2 = -N/Sigma (``_shell``) with respect to y = (r, theta, phi,
        p_r, p_theta, tau): (dK (n, 6), dmu2 (n, 6)); tested against central differences."""
        a, q = self.chi, self.q
        r, th, pr, pth = y[:, 0], y[:, 1], y[:, 3], y[:, 4]
        E, L, mu2 = c[:, 0], c[:, 1], c[:, 2]
        s, co = np.sin(th), np.cos(th)
        s2 = s * s
        dl = r * r - 2.0 * r + a * a + q * q
        P = (r * r + a * a) * E - a * L
        W = L - a * E * s2
        sig = r * r + a * a * co * co
        dWs = -4.0 * a * E * W * co / s - 2.0 * W * W * co / (s2 * s)  # d(W^2 / sin^2)/dtheta
        dK = np.zeros_like(y)
        dK[:, 1] = dWs - 2.0 * mu2 * a * a * s * co
        dK[:, 4] = 2.0 * pth
        N = dl * pr * pr + pth * pth - P * P / dl + W * W / s2
        dN = np.zeros_like(y)
        dN[:, 0] = (2.0 * r - 2.0) * pr * pr - 4.0 * r * E * P / dl + P * P * (2.0 * r - 2.0) / (dl * dl)
        dN[:, 1] = dWs
        dN[:, 3] = 2.0 * dl * pr
        dN[:, 4] = 2.0 * pth
        dS = np.zeros_like(y)
        dS[:, 0] = 2.0 * r
        dS[:, 1] = -2.0 * a * a * s * co
        dM = -dN / sig[:, None] + (N / (sig * sig))[:, None] * dS
        return dK, dM

    def _spend(self, rows, y0, y1, c):
        """Add the accepted steps y0 -> y1 of ``rows`` to their drift budgets (see the module docstring)."""
        sc = self._scale(y0, y1, c)
        dK, dM = self._grad(y1, c)
        self._bud[rows, 0] += math.sqrt(6.0) * np.sum(np.abs(dK) * sc, axis=1)
        self._bud[rows, 1] += math.sqrt(6.0) * np.sum(np.abs(dM) * sc, axis=1)

    def diagnostics(self) -> dict:
        c = self.constants()
        d = dict(self._stats)
        d.update({"t": self._t, "n": self.n, "active": int(np.sum(self._st == ACTIVE)),
                  "max_dK_rel": float(np.max(np.abs(c["dK"]) / np.maximum(np.abs(self._K0), 1.0))) if self.n else 0.0,
                  "max_dmu2": float(np.max(np.abs(c["dmu2"]))) if self.n else 0.0})
        return d

    # --- time ----------------------------------------------------------------------------------------------------
    def _f(self, y, c):
        """dy/dt of rows."""
        self._stats["rhs_rows"] += len(y)
        d, T = rhs_mino(y, c[:, 0], c[:, 1], c[:, 2], self.chi, self.q)
        return d / T[:, None]

    def _scale(self, y, yn, c):
        a, q = self.chi, self.q
        r = np.maximum(np.abs(y[:, 0]), np.abs(yn[:, 0]))
        dl = r * r - 2.0 * r + a * a + q * q
        P = np.abs((r * r + a * a) * c[:, 0] - a * c[:, 1])
        K = np.abs(y[:, 4] ** 2 + (c[:, 1] - a * c[:, 0] * np.sin(y[:, 1]) ** 2) ** 2 / np.sin(y[:, 1]) ** 2)
        sc = np.empty_like(y)
        sc[:, 0] = r
        sc[:, 1] = 1.0
        sc[:, 2] = 1.0
        sc[:, 3] = np.maximum(np.abs(y[:, 3]), np.abs(yn[:, 3])) + P / np.abs(dl)
        sc[:, 4] = np.maximum(np.abs(y[:, 4]), np.abs(yn[:, 4])) + np.sqrt(K) + 1e-8 * r  # floor: K = 0 (radial)
        sc[:, 5] = np.maximum(np.maximum(np.abs(y[:, 5]), np.abs(yn[:, 5])), r)
        return self.rtol * sc

    def _h0(self, y, c):
        """First step: 1 % of the time in which a component changes by its own scale (the rule then adapts it)."""
        f = self._f(y, c)
        sc = self._scale(y, y, c) / self.rtol
        d1 = np.sqrt(np.mean((f / sc) ** 2, axis=1))
        h = np.where(d1 > 0, 0.01 / np.where(d1 > 0, d1, 1.0), 1.0)
        return np.minimum(h, 1.0e3)

    def _step(self, y, c, h, k0):
        """One DOP853 step of rows y with per-row h; returns (y_new, err) (err <= 1: accept)."""
        A, B, E3, E5 = _tableau()
        n = len(y)
        K = np.empty((12, n, 6))
        K[0] = k0
        hh = h[:, None]
        for s in range(1, 12):
            K[s] = self._f(y + hh * np.tensordot(A[s, :s], K[:s], axes=(0, 0)), c)
        yn = y + hh * np.tensordot(B, K, axes=(0, 0))
        sc = self._scale(y, yn, c)
        e5 = np.sum((np.tensordot(E5, K, axes=(0, 0)) / sc) ** 2, axis=1)
        e3 = np.sum((np.tensordot(E3, K, axes=(0, 0)) / sc) ** 2, axis=1)
        den = e5 + 0.01 * e3
        err = np.abs(h) * e5 / np.sqrt(6.0 * np.where(den > 0, den, 1.0))
        bad = ~np.all(np.isfinite(yn), axis=1) | (yn[:, 0] <= self.r_plus) | ~np.isfinite(err)
        err = np.where(bad, np.inf, err)
        return yn, err

    def advance(self, t_target) -> list:
        """Advance every active body to the distant observer's time t_target (>= t); returns the events (dicts in
        time order: kind "captured" or "escaped", key, t, tau, r, theta, phi; captures also tau_horizon)."""
        t_target = float(t_target)
        if not t_target >= self._t:
            raise ValueError("time runs forward")
        events = []
        rows = np.flatnonzero(self._st == ACTIVE)
        if len(rows) == 0 or t_target == self._t:
            self._t = t_target
            return events
        y = self._y[rows].copy()
        c = self._c[rows]
        h = self._h[rows].copy()
        ti = np.full(len(rows), self._t)
        go = np.ones(len(rows), bool)
        k0 = self._f(y, c)
        r_cap = self.r_plus + self.capture_eps
        while np.any(go):
            idx = np.flatnonzero(go)
            rem = t_target - ti[idx]
            hs = np.minimum(h[idx], rem)
            land = hs >= rem
            yn, err = self._step(y[idx], c[idx], hs, k0[idx])
            acc = err <= 1.0
            with np.errstate(divide="ignore"):
                fac = np.where(err > 0, 0.9 * err ** (-1.0 / 8.0), 10.0)
            fac = np.clip(fac, 0.2, 10.0)
            self._stats["rejected"] += int(np.sum(~acc))
            # rejected rows: shrink
            rj = idx[~acc]
            h[rj] = hs[~acc] * np.minimum(fac[~acc], 1.0)
            if np.any(h[rj] < 1e-13 * (1.0 + np.abs(ti[rj]))):
                k = self._keys[rows[rj[np.argmin(h[rj])]]]
                raise coded(RuntimeError(T("the integrator's step became too small for body {key}", key=str(k))),
                            "kn.step_underflow")
            ai = idx[acc]
            if len(ai) == 0:
                continue
            ya, hsa, landa = yn[acc], hs[acc], land[acc]
            cap = ya[:, 0] <= r_cap
            esc = ya[:, 0] >= self.r_escape
            ev = cap | esc
            for j in np.flatnonzero(ev):
                g = ai[j]
                target = r_cap if cap[j] else self.r_escape
                ye, he = self._locate(y[g], c[g], k0[g], hsa[j], target)
                self._spend(rows[[g]], y[g][None], ye[None], c[g][None])
                y[g] = ye
                ti[g] = ti[g] + he
                go[g] = False
                kind = CAPTURED if cap[j] else ESCAPED
                self._st[rows[g]] = kind
                events.append(self._event(rows[g], ye, c[g], ti[g], kind))
            ok = ~ev
            g = ai[ok]
            if len(g):
                self._spend(rows[g], y[g], ya[ok], c[g])
            y[g] = ya[ok]
            ti[g] = np.where(landa[ok], t_target, ti[g] + hsa[ok])
            if not landa[ok].all():
                h[g[~landa[ok]]] = hsa[ok][~landa[ok]] * fac[acc][ok][~landa[ok]]
            # a landing step that was cut short keeps the step the rule would have taken
            lg = g[landa[ok]]
            h[lg] = np.maximum(h[lg], hsa[ok][landa[ok]] * fac[acc][ok][landa[ok]]) if len(lg) else h[lg]
            self._nst[rows[g]] += 1
            self._stats["steps"] += len(g)
            if len(g):
                k0[g] = self._f(y[g], c[g])
            go[g[landa[ok]]] = False
        self._y[rows] = y
        self._h[rows] = h
        self._t = t_target
        events.sort(key=lambda e: e["t"])
        return events

    def _locate(self, y0, c0, k00, h_hi, target):
        """Redo the step from y0 with lengths h in (0, h_hi] until r(h) = target (Illinois regula falsi)."""
        y0 = y0[None]
        c0 = c0[None]
        k00 = k00[None]
        lo, g_lo = 0.0, float(y0[0, 0] - target)
        hi = h_hi
        yh, _ = self._step(y0, c0, np.array([hi]), k00)
        g_hi = float(yh[0, 0] - target)
        best = (yh[0], hi)
        side = 0
        for _ in range(60):
            hm = (lo * g_hi - hi * g_lo) / (g_hi - g_lo)
            ym, _ = self._step(y0, c0, np.array([hm]), k00)
            gm = float(ym[0, 0] - target)
            best = (ym[0], hm)
            if abs(gm) <= 1e-12 * abs(target):
                break
            if (gm > 0) == (g_lo > 0):
                lo, g_lo = hm, gm
                if side == -1:
                    g_hi *= 0.5
                side = -1
            else:
                hi, g_hi = hm, gm
                if side == 1:
                    g_lo *= 0.5
                side = 1
        return best

    def _event(self, row, y, c, t, kind):
        key = self._keys[row]
        ev = {"kind": _STATUS[kind], "key": key, "t": float(t), "tau": float(y[5]), "r": float(y[0]),
              "theta": float(y[1]), "phi": float(y[2]), "photon": bool(c[2] == 0.0)}
        if kind == CAPTURED:
            a, q = self.chi, self.q
            r = y[0]
            dl = r * r - 2.0 * r + a * a + q * q
            sig = r * r + a * a * math.cos(y[1]) ** 2
            # dtau/dr = Sigma / (Delta p_r) (Mino: dr = Delta p_r dlambda, dtau = Sigma dlambda); p_r < 0 inbound
            ev["tau_horizon"] = float(y[5] + sig / (dl * y[3]) * (self.r_plus - r))
        self._info[key] = ev
        return ev

    # --- state ---------------------------------------------------------------------------------------------------
    def state_dict(self) -> dict:
        """Plain data; restoring continues bit-identically."""
        return {"format": _FORMAT, "chi": self.chi, "q": self.q, "rtol": self.rtol, "capture_eps": self.capture_eps,
                "r_escape": self.r_escape, "t": self._t, "keys": list(self._keys), "y": self._y.tolist(),
                "c": self._c.tolist(), "K0": self._K0.tolist(), "h": self._h.tolist(), "status": self._st.tolist(),
                "nsteps": self._nst.tolist(), "budget": self._bud.tolist(), "info": {str(i): self._info[k] for i, k in enumerate(self._keys)
                                                       if k in self._info},
                "next_key": self._next_key, "stats": dict(self._stats)}

    @classmethod
    def from_state_dict(cls, d: dict, **overrides) -> "Geodesics":
        """Rebuild; ``overrides`` (rtol, capture_eps, r_escape) make a companion from the same state."""
        if d.get("format") != _FORMAT:
            raise ValueError(f"not an {_FORMAT} state")
        kw = {k: d[k] for k in ("rtol", "capture_eps", "r_escape")}
        kw.update(overrides)
        o = cls(d["chi"], d["q"], t=d["t"], **kw)
        o._keys = list(d["keys"])
        n = len(o._keys)
        o._y = np.array(d["y"], float).reshape(n, 6)
        o._c = np.array(d["c"], float).reshape(n, 3)
        o._K0 = np.array(d["K0"], float).reshape(n)
        o._h = np.array(d["h"], float).reshape(n)
        o._st = np.array(d["status"], int).reshape(n)
        o._nst = np.array(d["nsteps"], int).reshape(n)
        o._bud = np.array(d.get("budget") or [[0.0, 0.0]] * n, float).reshape(n, 2)
        o._info = {o._keys[int(i)]: v for i, v in d["info"].items()}
        o._next_key = int(d["next_key"])
        o._stats = dict(d["stats"])
        if overrides:
            o._h = np.array([o._h0(o._y[i:i + 1], o._c[i:i + 1])[0] for i in range(n)]) if n else o._h
        return o

    def clone(self, **overrides) -> "Geodesics":
        return Geodesics.from_state_dict(self.state_dict(), **overrides)

    def rescale_proper_time(self, factor: float):
        """Multiply every body's proper time (in units of M) by ``factor``: the same clocks read in another unit of
        time, when the mass that sets the units G = c = M = 1 is changed as a change of units (plan P16.1: the hole's
        mass a property of its object; seconds per unit M change by 1/factor). The geodesics do not depend on tau."""
        f = float(factor)
        if not (math.isfinite(f) and f > 0.0):
            raise ValueError("factor must be a finite number > 0")
        self._y[:, 5] *= f


# --- what an observer sees ---------------------------------------------------------------------------------------
class _Mino(Geodesics):
    """The same integrator with Mino time as the independent variable (rays traced back from a camera)."""

    def _f(self, y, c):
        self._stats["rhs_rows"] += len(y)
        return rhs_mino(y, c[:, 0], c[:, 1], c[:, 2], self.chi, self.q)[0]


def look_directions(width: int, height: int, fov_deg: float, forward=(-1.0, 0.0, 0.0), up=(0.0, -1.0, 0.0)):
    """Unit look directions (height, width, 3) of a pinhole camera in the observer's frame, components along the
    ZAMO's legs (r-hat, theta-hat, phi-hat): pixel (i, j) looks along forward + x tan(fov/2) right + y tan(fov/2) up,
    x, y in [-1, 1] across the width (y scaled by height/width), right = forward x up. Default: towards the hole,
    up = -theta-hat (north)."""
    f = np.asarray(forward, float)
    f = f / np.linalg.norm(f)
    u = np.asarray(up, float)
    u = u - (u @ f) * f
    u = u / np.linalg.norm(u)
    rgt = np.cross(f, u)
    s = math.tan(math.radians(fov_deg) / 2.0)
    x = (np.arange(width) + 0.5) / width * 2.0 - 1.0
    y = ((np.arange(height) + 0.5) / height * 2.0 - 1.0) * height / width
    X, Y = np.meshgrid(x, -y)
    d = f[None, None, :] + s * X[..., None] * rgt[None, None, :] + s * Y[..., None] * u[None, None, :]
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def trace_sky(chi: float, q: float, r_o: float, theta_o: float, look, v_obs=None, *, rtol: float = 1e-10,
              r_far: float = 1e9, capture_eps: float = 1e-6, max_steps: int = 20000) -> dict:
    """What an observer at (r_o, theta_o, phi = 0) sees along the unit look directions ``look`` (n, 3) (its frame: the
    local ZAMO's, or, with ``v_obs`` (its 3-velocity measured by the ZAMO), the boosted frame with the same axes;
    aberration and Doppler by ``core.lorentz.aberrate``). Each arriving ray is traced back (the past-directed null
    geodesic, Mino time, the vectorized DOP853 of ``Geodesics``) until it is captured (r <= r_+ + capture_eps: the
    shadow) or reaches r_far (default 1e9 M; from there the ray is taken as straight: the bending left is < 2 M/r_far):
    its direction there is the source's direction on the celestial sphere. Returns arrays: ``captured``, ``escaped``,
    ``undecided`` (max_steps reached: rays orbiting very close to the photon shell), ``theta_inf``, ``phi_inf`` (the
    sky direction in the hole's polar angles, NaN unless escaped), ``lam`` = L/E, ``eta`` = Q_C/E^2 (Bardeen's
    constants of the ray), ``E`` = nu_inf / nu_obs (the frequency at infinity per observed frequency; its inverse
    the shift seen), ``dK`` (Carter's K at the end minus at the start, a measure of the integration error), ``steps``."""
    _chk(chi, q)
    look = np.atleast_2d(np.asarray(look, float)).reshape(-1, 3)
    look = look / np.linalg.norm(look, axis=1, keepdims=True)
    k_obs = -look  # the arriving photons propagate against the look direction
    if v_obs is not None:
        from ..lorentz import aberrate
        k_z, D = aberrate(k_obs, np.asarray(v_obs, float))
        D = np.asarray(D, float)
    else:
        k_z, D = k_obs, np.ones(len(look))
    z = zamo(r_o, theta_o, chi, q)
    sig, dl = float(z["Sigma"]), float(z["Delta"])
    if dl <= 0.0 or math.sin(theta_o) < 1e-9:
        raise coded(ValueError(T("the observer must be outside the horizon and off the axis")), "kn.observer")
    L = float(z["varpi"]) * D * k_z[:, 2]
    E = float(z["alpha"]) * D + float(z["omega"]) * L
    pr = D * k_z[:, 0] * math.sqrt(sig / dl)
    pth = D * k_z[:, 1] * math.sqrt(sig)
    n = len(look)
    g = _Mino(chi, q, rtol=rtol, capture_eps=capture_eps, r_escape=r_far)
    # the past-directed ray: p -> -p
    y = np.column_stack([np.full(n, float(r_o)), np.full(n, float(theta_o)), np.zeros(n), -pr, -pth, np.zeros(n)])
    c = np.column_stack([-E, -L, np.zeros(n)])
    K0 = g._shell(y, c)[1]
    h = g._h0(y, c)
    k0 = g._f(y, c)
    state = np.zeros(n, int)  # 0 tracing, 1 captured, 2 escaped, 3 undecided
    steps = np.zeros(n, int)
    lam = np.zeros(n)  # Mino time along each ray (the scale of a step's underflow)
    r_cap = g.r_plus + capture_eps
    while True:
        idx = np.flatnonzero(state == 0)
        if len(idx) == 0:
            break
        yn, err = g._step(y[idx], c[idx], h[idx], k0[idx])
        acc = err <= 1.0
        with np.errstate(divide="ignore"):
            fac = np.clip(np.where(err > 0, 0.9 * err ** (-1.0 / 8.0), 10.0), 0.2, 10.0)
        rj = idx[~acc]
        h[rj] = h[rj] * np.minimum(fac[~acc], 1.0)
        state[rj[h[rj] < 1e-15 * lam[rj]]] = 3
        ai = idx[acc]
        y[ai] = yn[acc]
        lam[ai] += h[ai]
        h[ai] = h[ai] * fac[acc]
        steps[ai] += 1
        k0[ai] = g._f(y[ai], c[ai])
        r = y[ai, 0]
        state[ai[r <= r_cap]] = 1
        state[ai[(r >= r_far) & (r > r_cap)]] = 2
        state[ai[(steps[ai] >= max_steps) & (state[ai] == 0)]] = 3
    out = {"captured": state == 1, "escaped": state == 2, "undecided": state == 3, "steps": steps,
           "lam": L / E, "E": E, "dK": g._shell(y, c)[1] - K0}
    Kc = K0 - (L - chi * E) ** 2
    out["eta"] = Kc / (E * E)
    th_inf = np.full(n, np.nan)
    ph_inf = np.full(n, np.nan)
    es = np.flatnonzero(state == 2)
    if len(es):
        ye, ce = y[es], c[es]
        ze = zamo(ye[:, 0], ye[:, 1], chi, q)
        pt_hat = (ce[:, 0] - ze["omega"] * ce[:, 1]) / ze["alpha"]  # E - omega L over alpha, of the traced momentum
        sp = np.stack([ye[:, 3] * np.sqrt(ze["Delta"] / ze["Sigma"]), ye[:, 4] / np.sqrt(ze["Sigma"]),
                       ce[:, 1] / ze["varpi"]], axis=1) / np.abs(pt_hat)[:, None]
        for k, i in enumerate(es):
            ax = zamo_axes(float(ye[k, 0]), float(ye[k, 1]), float(ye[k, 2]), chi)
            v = sp[k] @ ax
            v = v / np.linalg.norm(v)
            th_inf[i] = math.acos(max(-1.0, min(1.0, v[2])))
            ph_inf[i] = math.atan2(v[1], v[0])
    out["theta_inf"], out["phi_inf"] = th_inf, ph_inf
    return out
