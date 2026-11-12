# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Special relativity and gravity of the core, each against an independent route."""

import math

import numpy as np
import pytest
from scipy import integrate

from lfphys.core import relativity as R
from lfphys.core.constants import C, GM_SUN, R_SUN
from lfphys.core.gravity import kerr, orbits
from lfphys.core.gravity import schwarzschild as S
from lfphys.theories.alternatives import scalar_tensor
from lfphys.theories.approx import ppn

ETA = np.diag([1.0, -1.0, -1.0])
rng = np.random.default_rng(1)


# --- special relativity ---------------------------------------------------------------------------------
@pytest.mark.parametrize("v", [(0.3, 0.0), (0.0, -0.7), (0.5, 0.6), (-0.9, 0.1)])
def test_boost_preserves_the_metric_and_inverts(v):
    v = np.array(v) * C
    M = R.boost_matrix(v, C)
    assert np.allclose(M.T @ ETA @ M, ETA, atol=1e-13)
    assert np.allclose(R.boost_matrix(-v, C) @ M, np.eye(3), atol=1e-13)


def test_velocity_addition_collinear_and_subluminal():
    u, v = 0.7 * C, 0.8 * C
    w = R.compose_velocities(np.array([u, 0.0]), np.array([v, 0.0]), C)
    assert w[0] == pytest.approx((u + v) / (1 + u * v / C**2), rel=1e-15)
    for _ in range(50):
        a, b = rng.uniform(-0.99, 0.99, 2) * C / math.sqrt(2), rng.uniform(-0.99, 0.99, 2) * C / math.sqrt(2)
        assert np.linalg.norm(R.compose_velocities(a, b, C)) < C


def test_velocity_addition_matches_composed_boosts():
    """Velocity of F2 (moving with u' in F1, F1 with v in the lab) from the matrix product."""
    for _ in range(20):
        v = rng.uniform(-0.6, 0.6, 2) * C
        u = rng.uniform(-0.6, 0.6, 2) * C
        lam_inv = np.linalg.inv(R.boost_matrix(u, C) @ R.boost_matrix(v, C))
        w = lam_inv[1:, 0] / lam_inv[0, 0] * C
        assert np.allclose(R.compose_velocities(u, v, C), w, rtol=1e-12, atol=1e-6)


def test_emitted_light_has_speed_c_and_aberrates():
    n = np.stack([np.cos(np.linspace(0, 2 * math.pi, 37)), np.sin(np.linspace(0, 2 * math.pi, 37))], axis=1)
    vel = R.emit_velocities(n, np.array([0.6 * C, 0.0]), C)
    assert np.allclose(np.linalg.norm(vel, axis=1), C, rtol=1e-14)
    # light emitted at 90 deg in the source frame moves at cos(theta) = beta in the lab
    d = R.aberrate(np.array([[0.0, 1.0]]), np.array([0.6 * C, 0.0]), C)[0]
    assert d[0] == pytest.approx(0.6, rel=1e-14)


def test_doppler_limits():
    b = 0.6
    assert R.doppler_factor(b, 1.0) == pytest.approx(math.sqrt((1 + b) / (1 - b)), rel=1e-15)
    assert R.doppler_factor(b, 0.0) == pytest.approx(math.sqrt(1 - b * b), rel=1e-15)  # transverse: 1/gamma


@pytest.mark.parametrize("bu,bv,phi", [(0.5, 0.5, 90.0), (0.9, 0.3, 60.0), (0.2, 0.8, 135.0), (0.99, 0.99, 90.0)])
def test_wigner_rotation_closed_form(bu, bv, phi):
    """F1 moves along x with bu; F2 moves in F1 at angle phi with bv. |theta| from the closed form
    tan(theta/2) = sin(phi)/(k + cos(phi)), k^2 = (gu+1)(gv+1)/((gu-1)(gv-1)); swapping the order flips the sign."""
    u = np.array([bu, 0.0]) * C
    v = bv * C * np.array([math.cos(math.radians(phi)), math.sin(math.radians(phi))])
    th = R.wigner_rotation_angle(u, v, C)
    gu, gv = R.gamma(bu), R.gamma(bv)
    k = math.sqrt((gu + 1) * (gv + 1) / ((gu - 1) * (gv - 1)))
    ref = 2 * math.atan(math.sin(math.radians(phi)) / (k + math.cos(math.radians(phi))))
    assert abs(th) == pytest.approx(ref, rel=1e-10)


def test_wigner_rotation_small_velocities_is_thomas():
    """For small u, v: theta ~ |u x v| / (2 c^2)."""
    u = np.array([1e-3, 0.0]) * C
    v = np.array([0.0, 2e-3]) * C
    th = R.wigner_rotation_angle(u, v, C)
    assert abs(th) == pytest.approx(1e-3 * 2e-3 / 2, rel=1e-5)


# --- Schwarzschild orbits ---------------------------------------------------------------------------------
def f_cubic(u, e, l):
    return 2 * u**3 - u**2 + 2 * u / l**2 + (e * e - 1) / l**2


@pytest.mark.parametrize("r", [4.5, 6.0, 10.0, 100.0])
def test_circular_orbits_are_double_roots_and_isco_triple(r):
    """f(u) = f'(u) = 0 at u = M/r (analytic f' = 6u^2 - 2u + 2/l^2, f'' = 12u - 2); f'' = 0 only at r = 6M."""
    e, l = orbits.circular(r)
    u = 1.0 / r
    assert abs(f_cubic(u, e, l)) < 1e-14
    assert abs(6 * u * u - 2 * u + 2 / l**2) < 1e-14
    assert (abs(12 * u - 2) < 1e-15) == (r == 6.0)


@pytest.mark.parametrize("ra,rp", [(30.0, 12.0), (1e3, 200.0), (60.0, 9.0)])
def test_periapsis_advance_elliptic_vs_quadrature(ra, rp):
    u1, u2 = 1 / ra, 1 / rp
    u3 = 0.5 - u1 - u2
    exact = orbits.advance_from_turning(u1, u2)

    def integrand(chi):
        u = u1 + (u2 - u1) * math.sin(chi) ** 2
        return 2 * (u2 - u1) * math.sin(chi) * math.cos(chi) / math.sqrt(2 * (u - u1) * (u2 - u) * (u3 - u))
    half, _ = integrate.quad(integrand, 0, math.pi / 2, epsabs=0, epsrel=1e-13, limit=200)
    assert exact == pytest.approx(2 * half - 2 * math.pi, rel=1e-9)


def test_periapsis_advance_weak_field_limit():
    """Exact advance -> 6 pi M / p as p -> infinity (first post-Newtonian order)."""
    for p in (1e4, 1e6):
        ecc = 0.3
        ra, rp = p / (1 - ecc), p / (1 + ecc)
        ratio = orbits.advance_from_turning(1 / ra, 1 / rp) / orbits.advance_weak_field(p)
        assert ratio == pytest.approx(1.0, abs=10.0 / p)


def test_integrated_orbit_matches_elliptic_advance():
    ra, rp = 40.0, 14.0
    u1, u2 = 1 / ra, 1 / rp
    u3 = 0.5 - u1 - u2
    # e, l from the turning points: f = 2(u-u1)(u-u2)(u-u3) -> 2/l^2 = 2(u1u2 + u1u3 + u2u3), (e^2-1)/l^2 = -2u1u2u3
    l = 1 / math.sqrt(u1 * u2 + u1 * u3 + u2 * u3)
    e = math.sqrt(1 - 2 * u1 * u2 * u3 * l * l)
    adv = orbits.periapsis_advance(e, l)
    o = orbits.integrate_orbit(e, l, u2 * (1 - 1e-12), -1.0, 4 * math.pi + 2 * adv + 1.0, n_out=200001)
    r = o["r"]
    i_min = [i for i in range(1, len(r) - 1) if r[i] < r[i - 1] and r[i] <= r[i + 1]]
    dphi = o["phi"][i_min[0]]  # first return to periapsis
    assert dphi - 2 * math.pi == pytest.approx(adv, abs=3e-4)  # sampling limited (dphi grid 6e-5)
    assert r.min() == pytest.approx(rp, rel=1e-6) and r.max() == pytest.approx(ra, rel=1e-6)


def test_radial_infall_proper_time_is_the_cycloid():
    r0 = 20.0
    e = math.sqrt(1 - 2 / r0)
    o = orbits.integrate_radial(e, r0 * (1 - 1e-12), -1.0, 1e4, n_out=4001)
    eta = math.acos(4 / r0 - 1)  # r = r0 (1 + cos eta) / 2 reaches 2M
    tau_ref = math.sqrt(r0**3 / 8) * (eta + math.sin(eta))
    assert o["status"] == "horizon"
    assert o["tau"][-1] == pytest.approx(tau_ref, rel=1e-5)


def _mp_turning(e2m1, l):
    """40-digit roots of f(u) = 2u^3 - u^2 + 2u/l^2 + (e^2 - 1)/l^2 (independent of np.roots)."""
    import mpmath as mp
    mp.mp.dps = 40
    L = mp.mpf(l)
    return sorted(mp.re(z) for z in mp.polyroots([2, -1, 2 / L**2, mp.mpf(e2m1) / L**2], maxsteps=400,
                                                  extraprec=400))


def test_turning_points_from_e2m1_keep_the_weak_field_precision():
    """Review V4-7: formed from e, e^2 - 1 loses ~eps/|e^2 - 1| (Mercury: the periapsis 1.1e-8 off); given directly
    (gamma^2 (v^2 - 2M/r), no cancellation) the roots are exact to rounding."""
    import mpmath as mp
    M = GM_SUN / C**2
    a, ecc = 0.38709893 * 1.495978707e11, 0.20563069
    r0 = a * (1 - ecc) / M
    v = math.sqrt((1 + ecc) / (r0 - 2.0))
    g2 = 1.0 / (1.0 - v * v)
    e, l = orbits.from_local_velocity(r0, 0.0, v)
    em1 = g2 * (v * v - 2.0 / r0)
    mp.mp.dps = 40
    R0, V = mp.mpf(r0), mp.mpf(v)
    G2 = 1 / (1 - V * V)
    U = _mp_turning(G2 * (V * V - 2 / R0), mp.sqrt(G2) * V * R0)
    el = orbits.elements(e, l, em1)
    assert float(el["r_peri"] * U[1]) == pytest.approx(1.0, abs=1e-13)
    assert float(el["r_apo"] * U[0]) == pytest.approx(1.0, abs=1e-13)
    old = orbits.elements(e, l)  # formed from e: the documented loss
    assert abs(float(old["r_peri"] * U[1]) - 1.0) > 1e-9


@pytest.mark.parametrize("eps", [1e-6, 1e-8, 1e-10, 0.0])
def test_nearly_circular_advance_is_the_epicyclic_limit(eps):
    """Engine review E14: np.roots splits the double root of a nearly circular orbit into a complex pair; the advance
    is regular there (limit 2 pi/sqrt(1 - 6M/r) - 2 pi), and elements() must not raise."""
    u1, u2 = 1 / (10 * (1 + eps)), 1 / (10 * (1 - eps))
    u3 = 0.5 - u1 - u2
    l = 1 / math.sqrt(u1 * u2 + u1 * u3 + u2 * u3)
    e = math.sqrt(1 - 2 * u1 * u2 * u3 * l * l)
    limit = 2 * math.pi / math.sqrt(1 - 6 / 10) - 2 * math.pi
    assert orbits.periapsis_advance(e, l) == pytest.approx(limit, rel=1e-6 if eps else 1e-12)
    el = orbits.elements(e, l)
    assert el["r_peri"] == pytest.approx(10.0 * (1 - eps), rel=1e-7) and el["ecc"] <= 2 * eps + 1e-7


@pytest.mark.parametrize("ra,rp", [(30.0, 12.0), (60.0, 9.0), (1e4, 2e3)])
def test_radial_period_quadrature_vs_mpmath(ra, rp):
    """Review V4-11: t and tau of one radial period by the smooth chi-quadrature vs a 30-digit tanh-sinh quadrature
    of dt = e dr/((1 - 2/r) sqrt(R)), dtau = dr/sqrt(R) over [r_peri, r_apo] (endpoint singularities)."""
    import mpmath as mp
    u1, u2 = 1 / ra, 1 / rp
    u3 = 0.5 - u1 - u2
    l = 1 / math.sqrt(u1 * u2 + u1 * u3 + u2 * u3)
    e = math.sqrt(1 - 2 * u1 * u2 * u3 * l * l)
    q = orbits.radial_period(e, l)
    mp.mp.dps = 30
    U1, U2, L = mp.mpf(u1), mp.mpf(u2), mp.mpf(l)
    U3 = mp.mpf(1) / 2 - U1 - U2

    def R(r):
        u = 1 / r
        return abs(2 * L**2 * (u - U1) * (u - U2) * (u - U3))  # abs: rounding at the end points

    tau = 2 * mp.quad(lambda r: 1 / mp.sqrt(R(r)), [1 / U2, 1 / U1])
    t = 2 * mp.quad(lambda r: mp.mpf(e) / ((1 - 2 / r) * mp.sqrt(R(r))), [1 / U2, 1 / U1])
    assert q["tau"] == pytest.approx(float(tau), rel=1e-11)
    assert q["t"] == pytest.approx(float(t), rel=1e-11)


@pytest.mark.parametrize("ecc", [0.0, 0.5, 0.9])
def test_advance_series_coefficients(ecc):
    """Review V4-10: the truncation after n terms of 6 pi mu [1 + (18 + e^2)/4 mu + (5/12)(54 + 9 e^2) mu^2] leaves a
    residual ~ mu^n with the next coefficient: residual/mu^n converges as p grows (40-digit exact advance)."""
    import mpmath as mp
    mp.mp.dps = 40

    def exact(p):
        P, E = mp.mpf(p), mp.mpf(ecc)
        u1, u2 = (1 - E) / P, (1 + E) / P
        u3 = mp.mpf(1) / 2 - u1 - u2
        return 4 * mp.ellipk((u2 - u1) / (u3 - u1)) / mp.sqrt(2 * (u3 - u1)) - 2 * mp.pi

    c2, c3 = (18 + ecc**2) / 4, 5 / 12 * (54 + 9 * ecc**2)
    for p in (1e3, 1e4):
        ex = exact(p)
        mu = 1 / p
        r1 = float(orbits.advance_series(p, ecc, 1) / ex - 1)
        r2 = float(orbits.advance_series(p, ecc, 2) / ex - 1)
        r3 = float(orbits.advance_series(p, ecc, 3) / ex - 1)
        assert -r1 / mu == pytest.approx(c2, rel=20 * mu)
        assert -r2 / mu**2 == pytest.approx(c3, rel=20 * mu)
        assert abs(r3) < 200 * mu**3


# --- Kerr ---------------------------------------------------------------------------------------------------
def test_kerr_limits():
    assert kerr.isco(0.0) == pytest.approx(6.0, rel=1e-14) and kerr.photon_orbit(0.0) == pytest.approx(3.0, rel=1e-14)
    assert kerr.marginally_bound(0.0) == pytest.approx(4.0, rel=1e-14)
    assert kerr.isco(1.0) == pytest.approx(1.0, abs=1e-12) and kerr.isco(1.0, False) == pytest.approx(9.0, rel=1e-14)
    assert kerr.photon_orbit(1.0) == pytest.approx(1.0, abs=1e-12) and kerr.photon_orbit(1.0, False) == pytest.approx(4.0, rel=1e-14)
    assert kerr.marginally_bound(1.0, False) == pytest.approx(3 + 2 * math.sqrt(2), rel=1e-14)
    assert kerr.efficiency(0.0) == pytest.approx(1 - math.sqrt(8 / 9), rel=1e-12)
    assert kerr.efficiency(1.0 - 1e-12) == pytest.approx(1 - 1 / math.sqrt(3), abs=1e-3)


@pytest.mark.parametrize("chi", [0.1, 0.5, 0.9, 0.99])
@pytest.mark.parametrize("pro", [True, False])
def test_kerr_closed_forms_satisfy_the_radial_potential(chi, pro):
    """Circular orbits: R = R' = 0; at the ISCO also R'' = 0 (independent of the closed forms)."""
    def derivs(r, e, l, h=1e-4):
        f = lambda x: kerr.radial_potential(x, e, l, chi)  # noqa: E731
        return f(r), (f(r + h) - f(r - h)) / (2 * h), (f(r + h) - 2 * f(r) + f(r - h)) / h**2
    r_isco = kerr.isco(chi, pro)
    for r in (r_isco, r_isco * 1.5, 30.0):
        e, l = kerr.circular_e_l(r, chi, pro)
        R0, R1, R2 = derivs(r, e, l)
        scale = r**4
        assert abs(R0) < 1e-10 * scale and abs(R1) < 1e-6 * scale
        if r == r_isco:
            assert abs(R2) < 1e-4 * scale
    r_ph = kerr.photon_orbit(chi, pro)
    # the circular photon orbit: the circular-orbit energy diverges there
    assert kerr.circular_e_l(r_ph * (1 + 1e-6), chi, pro)[0] > 50.0


# --- weak field (PPN) and Brans-Dicke ------------------------------------------------------------------------
def test_ppn_deflection_at_the_solar_limb_and_exact_gr():
    d = ppn.deflection(GM_SUN, R_SUN)
    assert math.degrees(d) * 3600 == pytest.approx(1.7512, abs=2e-4)
    rs = 2 * GM_SUN / C**2
    exact = S.deflection_from_quadrature(R_SUN, rs, C)  # b = R_sun
    assert exact == pytest.approx(d, rel=1e-5)  # higher orders ~ (15 pi / 16)(rs/b) ~ 1e-5
    assert ppn.deflection(GM_SUN, R_SUN, gamma=0.0) == pytest.approx(d / 2, rel=1e-15)  # Soldner


def test_ppn_periapsis_is_the_weak_field_limit_of_the_exact_orbit():
    gm = GM_SUN
    M = gm / C**2
    a, ecc = 5.79e10, 0.2056
    rp, ra = a * (1 - ecc), a * (1 + ecc)
    exact = orbits.advance_from_turning(M / ra, M / rp)
    assert exact == pytest.approx(ppn.periapsis_advance(gm, a, ecc), rel=1e-6)


def test_brans_dicke_limit():
    assert scalar_tensor.ppn_gamma(4e4) == pytest.approx(1.0, abs=3e-5)
    assert scalar_tensor.ppn_gamma(1e12) == pytest.approx(1.0, abs=1e-11)


def test_newtonian_body_keeps_energy_and_kepler_period():
    from lfphys.theories.approx import newton
    gm = 1.0
    r0, v0 = (1.0, 0.0), (0.0, 1.2)
    E = 0.5 * 1.2**2 - 1.0
    a = -gm / (2 * E)
    P = 2 * math.pi * math.sqrt(a**3 / gm)
    o = newton.integrate_body(r0, v0, gm, P, n_out=5)
    assert (o["x"][-1], o["y"][-1]) == pytest.approx((1.0, 0.0), abs=1e-9)  # closed orbit after one period
    Ek = 0.5 * (o["vx"] ** 2 + o["vy"] ** 2) - gm / np.hypot(o["x"], o["y"])
    assert np.allclose(Ek, E, rtol=1e-11)


def test_mercury_perihelion_advance_from_the_nasa_elements():
    """Exact GR advance from the NASA elements vs Will 2014 Eq. (65): 42.98 arcsec/century (gamma = beta = 1,
    without the solar quadrupole). The elements are given to 4-5 digits, hence the tolerance."""
    from lfphys.core import data
    M = GM_SUN / C**2
    a, ecc, P = data.MERCURY["a_m"], data.MERCURY["ecc"], data.MERCURY["period_days"]
    dphi = orbits.advance_from_turning(M / (a * (1 + ecc)), M / (a * (1 - ecc)))
    per_century = dphi * 36525.0 / P * 180 / math.pi * 3600
    assert per_century == pytest.approx(data.MERCURY_ADVANCE_GR_ARCSEC_PER_CENTURY, abs=0.02)



@pytest.mark.parametrize("ecc", [0.5, 0.99, 0.999999])
def test_newton_body_keeps_energy_through_a_deep_periapsis(ecc):
    """Levi-Civita regularisation: energy and period of a Kepler ellipse with r_peri down to 1e-6 a (in coordinate
    time the energy error there was ~1e-5 of |E|: review of v04, V4-4)."""
    from lfphys.theories.approx import newton
    gm, a = 1.0, 1.0
    rp = a * (1 - ecc)
    vp = math.sqrt(gm * (1 + ecc) / rp)
    P = 2 * math.pi * math.sqrt(a**3 / gm)
    o = newton.integrate_body_regularized((rp, 0.0), (0.0, vp), gm, 3 * P, n_out=301)
    kin = 0.5 * (o["vx"] ** 2 + o["vy"] ** 2)
    pot = gm / np.hypot(o["x"], o["y"])
    E0 = -gm / (2 * a)
    # evaluating E = v^2/2 - GM/r at a deep periapsis cancels terms ~ GM/r_peri: allow 1e-12 of them
    assert np.all(np.abs(kin - pot - E0) <= 1e-12 * (kin + pot) + 1e-9 * abs(E0))
    # back at the periapsis after each period (samples 100, 200, 300 are t = P, 2P, 3P): the miss, divided by the
    # periapsis speed, is the timing error
    for k in (100, 200, 300):
        assert math.hypot(o["x"][k] - rp, o["y"][k]) / vp < 5e-9 * P

    # the coordinate-time integrator (used by v04) loses the energy at the deep periapsis: the reason for the above
    if ecc > 0.9999:
        c = newton.integrate_body((rp, 0.0), (0.0, vp), gm, 3 * P, n_out=301)
        Ec = 0.5 * (c["vx"] ** 2 + c["vy"] ** 2) - gm / np.hypot(c["x"], c["y"])
        # the energy jump at each periapsis passage stays: compare the typical (median) error along the orbit
        assert np.median(np.abs(Ec - E0)) > 10 * np.median(np.abs(kin - pot - E0))
