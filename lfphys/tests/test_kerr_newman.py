# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Kerr-Newman test bodies, rays and clocks (lfphys.core.gravity.kerr_newman, plan P15.1) against independent routes.

* q = 0: the closed-form Kerr routes - generic bound orbits (``kerr_orbits.KerrOrbit``: Jacobi functions in Mino
  time), null geodesics (``kerr_null.NullRay``), the Bardeen-Press-Teukolsky closed forms (``kerr``);
* q != 0: the Mino-time Hamiltonian route of ``kerr_geodesics`` (SciPy's DOP853 on a different Hamiltonian form,
  with the charge) and, at a = 0 (Reissner-Nordstrom), closed forms: horizons, the photon sphere (Pugliese et al. 2011,
  Eq. 36), the ISCO cubic (Morales-Herrera et al. 2024, Eq. 20), circular clocks, the light deflection as an exact
  quadrature and its weak-field series (Keeton & Petters 2005, Eq. 53), radial infall and escape times by quadrature
  and the tortoise coordinate.

Tolerances: an integrated run's error is bounded by the x2 rule against a companion 100 times stricter (DOP853 is
eighth order: the companion is >= 100 times more accurate); closed forms add their own rounding (written out per
test); conserved quantities drift by at most the sum over accepted steps of the local error allowed per step,
sqrt(6) rtol |grad| . scale (the step's weighted RMS error is <= rtol).
"""

import json
import math

import numpy as np
import pytest
from scipy import integrate as si
from scipy.optimize import brentq

from lfphys.core.gravity import kerr, kerr_geodesics as KG, kerr_newman as KNW, kerr_null as KNL, kerr_orbits as KO

U = 2.0 ** -53
CASES = [(0.9, 0.0), (0.0, 0.6), (0.5, 0.5), (0.3, 0.9), (0.95, 0.2), (0.0, 0.0), (0.7, 0.7)]


# --- geometry ----------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("chi,q", CASES)
def test_photon_orbits_and_isco_for_several_spins_and_charges(chi, q):
    """photon_orbit and isco run for any (a, q) (regression: SciPy's brentq needs rtol >= 4 u, review of B6) and
    agree with independent routes: the photon orbit with the root of the critical-constants condition (R = R' = 0 at
    eta = 0): r^2 - 3 r + 2 a^2 + 2 q^2 = -+ 2 a sqrt(Delta) (prograde: minus), squared-free; the ISCO with the
    minimum of the circular orbits' energy E(r) (central differences change sign across it). Tolerance of the roots:
    Brent's xtol + rtol |r| for each route plus the rounding of the residuals divided by their slopes."""
    for prograde in (True, False):
        r_ph = KNW.photon_orbit(chi, q, prograde)
        s = -1.0 if prograde else 1.0

        def F(r):
            dl = r * r - 2 * r + chi * chi + q * q
            return r * r - 3 * r + 2 * chi * chi + 2 * q * q - s * 2 * chi * math.sqrt(dl)
        rp = KNW.horizons(chi, q)[0]
        rs = np.linspace(rp * (1 + 1e-9), 4.5, 2000)
        fs = np.array([F(x) for x in rs])
        k = np.flatnonzero(np.sign(fs[:-1]) != np.sign(fs[1:]))[-1]
        r2 = brentq(F, rs[k], rs[k + 1], xtol=1e-15, rtol=8.9e-16)
        h = 1e-6
        slope = abs(F(r2 + h) - F(r2 - h)) / (2 * h)
        tol = 2 * (1e-15 + 8.9e-16 * r2) + 32 * U * (r2 * r2 + 3 * r2 + 4) / slope
        assert abs(r_ph - r2) <= tol, (prograde, r_ph, r2)
        r_i = KNW.isco(chi, q, prograde)
        dE = lambda r: (float(KNW.circular_orbit(r + 1e-6, chi, q, prograde)["E"])  # noqa: E731
                        - float(KNW.circular_orbit(r - 1e-6, chi, q, prograde)["E"])) / 2e-6
        assert dE(r_i * (1 - 1e-3)) < 0.0 < dE(r_i * (1 + 1e-3)), (prograde, r_i)
        assert r_ph < r_i
    if q == 0.0:
        for prograde in (True, False):
            assert abs(KNW.photon_orbit(chi, 0.0, prograde) - kerr.photon_orbit(chi, prograde)) <= 1e-13
            assert abs(KNW.isco(chi, 0.0, prograde) - kerr.isco(chi, prograde)) <= 1e-12 * kerr.isco(chi, prograde)
    if chi == 0.0:
        # Pugliese, Quevedo & Ruffini 2011, Eq. (36); Morales-Herrera et al. 2024, Eq. (20) (M = 1)
        assert abs(KNW.photon_orbit(0.0, q) - (3 + math.sqrt(9 - 8 * q * q)) / 2) <= 1e-14
        roots = np.roots([1.0, -6.0, 9 * q * q, -4 * q ** 4])
        rc = max(z.real for z in roots if abs(z.imag) < 1e-9)
        for _ in range(3):
            rc -= (rc ** 3 - 6 * rc ** 2 + 9 * q * q * rc - 4 * q ** 4) / (3 * rc ** 2 - 12 * rc + 9 * q * q)
        assert abs(KNW.isco(0.0, q) - rc) <= 1e-12 * rc


@pytest.mark.parametrize("chi,q", CASES[:5])
def test_horizons_ergosurface_zamo_and_clocks_against_the_metric(chi, q):
    """Delta(r_pm) = 0, g_tt(r_E) = 0 (kerr_geodesics.metric with the charge), the ZAMO lapse alpha^2 = -1/g^tt,
    omega = -g_t phi / g_phi phi, varpi^2 = g_phi phi, the static clock sqrt(-g_tt); the ZAMO tetrad built from them
    is orthonormal; all to 64 u of the terms."""
    rp, rm = KNW.horizons(chi, q)
    for r in (rp, rm):
        assert abs(r * r - 2 * r + chi * chi + q * q) <= 8 * U * (r * r + 2 * r + 1)
    for th in (0.3, 1.0, math.pi / 2):
        rE = float(KNW.ergosurface(th, chi, q))
        g = KG.metric(rE, th, chi, q)
        assert abs(g[0, 0]) <= 64 * U * (1 + 2 * rE / rE ** 2 + q * q / rE ** 2)
        for r in (rE * 1.3, 5.0, 30.0):
            z = KNW.zamo(r, th, chi, q)
            g = KG.metric(r, th, chi, q)
            gi = KG.inverse_metric(r, th, chi, q)
            assert float(z["alpha"]) ** 2 == pytest.approx(-1.0 / gi[0, 0], rel=64 * U)
            assert float(z["omega"]) == pytest.approx(-g[0, 3] / g[3, 3], rel=64 * U, abs=1e-300)
            assert float(z["varpi"]) ** 2 == pytest.approx(g[3, 3], rel=64 * U)
            if -g[0, 0] > 0:
                assert float(KNW.static_clock_rate(r, th, chi, q)) == pytest.approx(math.sqrt(-g[0, 0]), rel=64 * U)
            # tetrad e_t = (d_t + omega d_phi)/alpha, e_r = sqrt(Delta/Sigma) d_r, e_th = d_th/sqrt(Sigma),
            # e_phi = d_phi/varpi
            E = np.zeros((4, 4))
            E[0, 0], E[0, 3] = 1 / float(z["alpha"]), float(z["omega"]) / float(z["alpha"])
            E[1, 1] = math.sqrt(float(z["Delta"]) / float(z["Sigma"]))
            E[2, 2] = 1 / math.sqrt(float(z["Sigma"]))
            E[3, 3] = 1 / float(z["varpi"])
            eta = E @ g @ E.T
            assert np.max(np.abs(eta - np.diag([-1, 1, 1, 1]))) <= 256 * U * (1 + r)


def test_zamo_initial_states_and_coordinates_round_trip():
    """A body with ZAMO velocity v: -p.p = 1, and the ZAMO measures v back; a photon: -p.p = 0 and |v| = 1; the
    drawing coordinates invert; the ZAMO axes in drawing space are orthonormal."""
    chi, q = 0.8, 0.4
    g = KNW.Geodesics(chi, q)
    v = np.array([0.2, -0.3, 0.5])
    kb = g.add_body(6.0, 1.1, 0.4, v=v)
    kp = g.add_photon(7.0, 2.0, -1.0, n=[-1.0, 0.2, 0.3])
    c = g.constants()
    assert abs(c["mu2"][0] - 1) <= 64 * U and abs(c["mu2"][1]) <= 64 * U * 10
    zv = g.zamo_velocity()
    assert np.max(np.abs(zv[0] - v)) <= 64 * U
    assert abs(np.linalg.norm(zv[1]) - 1) <= 64 * U
    assert g.is_photon().tolist() == [False, True] and g.keys == [kb, kp]
    r, th, ph = 3.7, 0.9, 2.5
    x, y, z = KNW.cartesian(r, th, ph, chi)
    r2, th2, ph2 = KNW.from_cartesian(x, y, z, chi)
    assert abs(r2 - r) <= 16 * U * r and abs(th2 - th) <= 1e-14 and abs(ph2 - ph) <= 1e-15
    ax = KNW.zamo_axes(r, th, ph, chi)
    assert np.max(np.abs(ax @ ax.T - np.eye(3))) <= 16 * U
    with pytest.raises(ValueError):
        g.add_body(KNW.horizons(chi, q)[0] + 1e-6, 1.0, 0.0)
    with pytest.raises(ValueError):
        g.add_body(5.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        KNW.Geodesics(0.8, 0.6)
    with pytest.raises(ValueError):
        g.add_body(5.0, 1.0, 0.0, v=(0.6, 0.6, 0.6))


def test_zamo_frame_momentum_and_back():
    """``zamo_frame_momentum`` and ``momentum_from_frame`` (review LB1-physics P5, P6) invert each other; the frame
    components are gamma (1, v) of the velocity given to ``momentum_from_zamo`` (and nu (1, n) of a photon) and agree
    with ``Geodesics.zamo_velocity`` (an independent route through E, L, p_r, p_theta); the frame energy's square minus
    the momentum's is the mass shell (1, 0); a body with gamma = 300 at 1e-3 above the horizon comes back with its
    gamma, which a velocity |v| = 1 - 5.6e-6 would carry only to ~eps gamma^2 = 2e-11."""
    chi, q = 0.8, 0.4
    r, th = 3.1, 1.2
    v = np.array([0.3, -0.2, 0.6])
    gam = 1 / math.sqrt(1 - v @ v)
    p = KNW.momentum_from_zamo(r, th, chi, q, v=v)
    h = KNW.zamo_frame_momentum(r, th, chi, q, p)
    assert np.max(np.abs(h - gam * np.array([1.0, *v]))) <= 16 * U * gam
    assert abs(h[0] ** 2 - h[1:] @ h[1:] - 1.0) <= 32 * U * gam * gam
    assert np.max(np.abs(KNW.momentum_from_frame(r, th, chi, q, h) - p)) <= 16 * U * np.max(np.abs(p))
    n = np.array([-0.6, 0.0, 0.8])
    pp = KNW.momentum_from_zamo(r, th, chi, q, n=n, nu=2.5)
    hp = KNW.zamo_frame_momentum(r, th, chi, q, pp)
    assert np.max(np.abs(hp - 2.5 * np.array([1.0, *n]))) <= 32 * U
    g = KNW.Geodesics(chi, q)
    g.add_body(r, th, 0.3, v=v)
    assert np.max(np.abs(g.zamo_velocity()[0] - h[1:] / h[0])) <= 32 * U
    rp = KNW.horizons(chi, q)[0] + 1e-3
    hh = np.array([math.sqrt(1 + 300.0 ** 2 - 1), -math.sqrt(300.0 ** 2 - 1), 0.0, 0.0])
    back = KNW.zamo_frame_momentum(rp, th, chi, q, KNW.momentum_from_frame(rp, th, chi, q, hh))
    assert np.max(np.abs(back - hh)) <= 1e-12 * 300.0
    with pytest.raises(ValueError):
        KNW.momentum_from_frame(r, th, chi, q, [-1.0, 0.0, 0.0, 0.0])
    with pytest.raises(ValueError):
        KNW.momentum_from_frame(r, 0.0, chi, q, [1.0, 0.0, 0.0, 0.0])
    with pytest.raises(ValueError):
        KNW.zamo_frame_momentum(1.0, th, chi, q, p)


def test_rescale_proper_time_reads_the_same_clocks_in_another_unit():
    """``Geodesics.rescale_proper_time`` (review LB1-physics P12: a core function tested only through p01): the proper
    times are multiplied by the factor (exactly) and nothing else changes; continued, the rescaled bodies move as the
    unscaled ones and their clocks advance by the same proper time in units of M (tau_B(t) - f tau_A(t0) = tau_A(t) -
    tau_A(t0)). Not bit for bit after advancing: the step control scales tau's error by max(|tau|, r), so the steps
    differ; both runs are DOP853 at rtol 1e-10 of the same tau-independent orbits (all active), held here to 1e-9
    (measured 3e-14 in position, 5e-12 in momentum, 2e-13 in the clocks; a rescale that moved a body would be off by
    O(1)). Refused: a factor that is not a finite number > 0."""
    def two():
        g = KNW.Geodesics(0.6, 0.2)
        g.add_body(7.0, 1.3, 0.2, v=[0.05, 0.02, 0.33])
        g.add_body(9.0, 1.6, 1.0, v=[-0.1, 0.0, 0.25])
        g.add_photon(12.0, 1.4, 0.0, n=[1.0, 0.1, 0.05], key="ray")
        g.advance(20.0)
        return g
    a, b = two(), two()
    tau0 = a.proper_time()
    f = 0.37
    b.rescale_proper_time(f)
    assert np.array_equal(b.bl(), a.bl()) and np.array_equal(b.momenta(), a.momenta())
    assert np.array_equal(b.proper_time(), tau0 * f)
    a.advance(60.0)
    b.advance(60.0)
    assert a.status() == ["active"] * 3
    assert np.max(np.abs(b.bl() - a.bl())) <= 1e-9 * np.max(np.abs(a.bl()))
    assert np.max(np.abs(b.momenta() - a.momenta())) <= 1e-9 * np.max(np.abs(a.momenta()))
    d = (b.proper_time() - f * tau0) - (a.proper_time() - tau0)
    assert np.max(np.abs(d)) <= 1e-9 * np.max(np.abs(a.proper_time()))
    for bad in (0.0, -1.0, math.inf, math.nan):
        with pytest.raises(ValueError):
            b.rescale_proper_time(bad)


@pytest.mark.parametrize("chi,q", [(0.0, 0.7), (0.9, 0.0), (0.5, 0.6), (0.6, -0.3)])
def test_circular_orbits_from_the_metric(chi, q):
    """circular_orbit's E, L make the equatorial radial potential R = P^2 - Delta (r^2 + (L - a E)^2) and R' vanish
    (an independent route from the Omega formula); Kerr: E, L of Bardeen-Press-Teukolsky (kerr.circular_e_l) and
    dtau/dt = E - Omega L with Omega = 1/(r^{3/2} + a); Reissner-Nordstrom: dtau/dt = sqrt(1 - 3/r + 2 q^2/r^2)
    (Pugliese et al. 2011, Eqs. 11-12 with u^t = E/f)."""
    for r in (4.5, 7.0, 20.0):
        for prograde in (True, False):
            c = KNW.circular_orbit(r, chi, q, prograde)
            if not np.isfinite(c["dtau_dt"]):
                continue
            E, L = float(c["E"]), float(c["L"])
            a = chi
            dl = r * r - 2 * r + a * a + q * q
            P = (r * r + a * a) * E - a * L
            R = P * P - dl * (r * r + (L - a * E) ** 2)
            Rp = 4 * r * E * P - (2 * r - 2) * (r * r + (L - a * E) ** 2) - 2 * r * dl
            scale = P * P + dl * (r * r + (L - a * E) ** 2)
            assert abs(R) <= 256 * U * scale and abs(Rp) <= 256 * U * scale / r
            if q == 0.0:
                e0, l0 = kerr.circular_e_l(r, chi, prograde)
                assert E == pytest.approx(e0, rel=64 * U) and L == pytest.approx(l0, rel=64 * U)
                om = (1.0 if prograde else -1.0) / (r ** 1.5 + (1.0 if prograde else -1.0) * chi)
                assert float(c["dtau_dt"]) == pytest.approx(e0 - om * l0, rel=256 * U)
            if chi == 0.0:
                assert float(c["dtau_dt"]) == pytest.approx(math.sqrt(1 - 3 / r + 2 * q * q / r ** 2), rel=64 * U)


# --- dynamics ------------------------------------------------------------------------------------------------------------
def _companion_pair(chi, q, add, rtol=1e-10):
    g = KNW.Geodesics(chi, q, rtol=rtol)
    gc = KNW.Geodesics(chi, q, rtol=rtol / 100)
    add(g)
    add(gc)
    return g, gc


def test_kerr_generic_orbit_against_the_closed_form():
    """q = 0: a generic inclined eccentric orbit (chi 0.9, p 6, e 0.7, inclination 20 deg; Fujita & Hikida 2009,
    Table 3) started at periapsis and theta_min (p_r = p_theta = 0: the closed form's exact start) against
    KerrOrbit's Jacobi-function solution at its coordinate times: x2 rule (companion rtol/100) + the closed form's
    error (its t and phi quadrature: 24 against 48 Gauss nodes per interval, x2) + 1e-12 relative for its Jacobi
    functions (measured 3e-12 in test_kerr_orbits)."""
    chi, p, e, x = 0.9, 6.0, 0.7, math.cos(math.radians(20))
    o = KO.KerrOrbit(chi, p, e, x)
    r0, th0 = float(o.r(0.0)), float(o.theta(0.0))

    def add(g):
        g.add_state(r0, th0, 0.0, [-o.E, 0.0, 0.0, o.L], 1.0)
    g, gc = _companion_pair(chi, 0.0, add)
    lams = np.array([0.5, 2.0, 7.0, 15.0])
    t, r, th, ph = o.trajectory(lams)
    o2 = KO.KerrOrbit(chi, p, e, x)
    t2, ph2 = np.empty(4), np.empty(4)
    lt, tt, pp = 0.0, 0.0, 0.0
    for i, lam in enumerate(lams):
        dt_, dp_ = o2._integrate(lt, lam, nodes=48)
        tt, pp, lt = tt + dt_, pp + dp_, lam
        t2[i], ph2[i] = tt, pp
    # the closed form's error in t (e_cf_t) moves the compared point by e_cf_t times the coordinate-time rates
    # |dr/dt|, |dtheta/dt|, |dphi/dt| (finite differences over a Mino-time interval of 1e-4, doubled; review B6-G18:
    # they were Mino-time rates, 30-110 times larger)
    tb, rb, thb, phb = o.trajectory(lams + 1e-4)
    for i, ti in enumerate(t):
        g.advance(ti)
        gc.advance(ti)
        y, yc = g.bl()[0], gc.bl()[0]
        rate = 2 * np.abs([rb[i] - r[i], thb[i] - th[i], phb[i] - ph[i]]) / abs(tb[i] - ti)
        e_cf_t = 2 * abs(ti - t2[i])
        assert abs(y[0] - r[i]) <= 2 * abs(y[0] - yc[0]) + 1e-12 * r[i] + e_cf_t * rate[0], (i, y[0], r[i])
        assert abs(y[1] - th[i]) <= 2 * abs(y[1] - yc[1]) + 1e-12 + e_cf_t * rate[1], (i, y[1], th[i])
        assert abs(y[2] - ph[i]) <= 2 * abs(y[2] - yc[2]) + 2 * abs(ph[i] - ph2[i]) + 1e-12 * (1 + abs(ph[i])) \
            + e_cf_t * rate[2], (i, y[2], ph[i])
    c = g.constants()
    assert abs(c["Q_C"][0] - o.Q) <= 1e-9 * max(1.0, o.Q)


def test_kerr_photon_against_the_closed_form_ray():
    """q = 0: a photon (lambda 2.5, eta 20, chi 0.7) from r0 = 15 inwards against kerr_null.NullRay's Jacobi
    functions (r, theta) and quadratures (t, phi; 16 against 32 nodes, x2) at the ray's coordinate times."""
    chi, lam, eta = 0.7, 2.5, 20.0
    r0, th0 = 15.0, 1.2
    ray = KNL.NullRay(chi, lam, eta, r0, th0, -1.0, 1.0)
    p0 = KG.null_momentum(r0, th0, lam, eta, chi, -1.0, 1.0)

    def add(g):
        g.add_state(r0, th0, 0.0, p0, 0.0)
    g, gc = _companion_pair(chi, 0.0, add)
    taus = np.array([0.05, 0.12, 0.2, 0.3])
    path = ray.path(taus)
    path2 = ray.path(taus, nodes=32)
    for i, ti in enumerate(path["t"]):
        g.advance(ti)
        gc.advance(ti)
        y, yc = g.bl()[0], gc.bl()[0]
        e_t = 2 * abs(ti - path2["t"][i])
        assert abs(y[0] - path["r"][i]) <= 2 * abs(y[0] - yc[0]) + 1e-11 * path["r"][i] + 2 * e_t, (i, y, path["r"][i])
        assert abs(y[1] - path["theta"][i]) <= 2 * abs(y[1] - yc[1]) + 1e-11 + e_t
        assert abs(y[2] - path["phi"][i]) <= 2 * abs(y[2] - yc[2]) + 2 * abs(path["phi"][i] - path2["phi"][i]) \
            + 1e-11 * (1 + abs(path["phi"][i])) + e_t
    c = g.constants()
    assert abs(c["Q_C"][0] - eta) <= 1e-9 * (eta + lam * lam) and abs(c["mu2"][0]) <= 1e-9 * (eta + lam * lam)


@pytest.mark.parametrize("photon", [False, True])
def test_kerr_newman_against_the_mino_time_route(photon):
    """q != 0: the integrator in coordinate time against kerr_geodesics.integrate (Mino time, SciPy's DOP853, the
    off-shell Hamiltonian form, with the charge) stopped at the same coordinate times: x2 rules of both (their
    companions 100 times stricter). Negative control: the reference without the charge differs by far more."""
    chi, q = 0.6, 0.5
    if photon:
        p0 = KNW.momentum_from_zamo(9.0, 1.3, chi, q, n=[-0.8, 0.3, 0.5])
        x0, mu2 = [0.0, 9.0, 1.3, 0.2], 0.0
    else:
        p0 = KNW.momentum_from_zamo(8.0, 1.2, chi, q, v=[0.1, 0.05, 0.35])
        x0, mu2 = [0.0, 8.0, 1.2, 0.3], 1.0

    def add(g):
        g.add_state(x0[1], x0[2], x0[3], p0, mu2)
    g, gc = _companion_pair(chi, q, add)
    ts = [10.0, 50.0, 120.0] if not photon else [5.0, 9.0, 13.0]

    def ref(t, rtol, qq):
        def ev(lam, y):
            return y[0] - t
        ev.terminal = True
        sol = KG.integrate(chi, x0, p0, 1e4, rtol=rtol, atol=rtol * 1e-2, events=[ev], q=qq)
        return sol.y_events[0][0][1:4]
    for t in ts:
        g.advance(t)
        gc.advance(t)
        y, yc = g.bl()[0], gc.bl()[0]
        r1, r2 = ref(t, 1e-11, q), ref(t, 1e-13, q)
        tol = 2 * np.abs(y - yc) + 2 * np.abs(r1 - r2) + 64 * U * (1 + np.abs(y))
        assert np.all(np.abs(y - r2) <= tol), (t, y, r2, tol)
        assert np.max(np.abs(ref(t, 1e-13, 0.0) - r2)) > 1e3 * np.max(tol)


def test_conserved_quantities_drift_within_the_local_error_budget():
    """Over 20 orbits of an inclined eccentric KN orbit: E and L exact (constants of the state), Carter's K and the
    mass shell drift by at most steps x sqrt(6) rtol max(|grad K| . scale) along the path (the gradient by central
    differences at sampled states)."""
    chi, q = 0.7, 0.4
    g = KNW.Geodesics(chi, q, rtol=1e-10)
    g.add_body(10.0, 1.0, 0.0, v=[0.05, 0.12, 0.3])
    E0, L0 = g.constants()["E"][0], g.constants()["L"][0]
    worst = np.zeros(2)
    for t in np.linspace(0, 20 * 2 * math.pi * 12 ** 1.5, 41)[1:]:
        g.advance(t)
        y = g._y.copy()
        c = g._c
        sc = g._scale(y, y, c)

        def KM(yy):
            m2, K, _ = g._shell(yy, c)
            return np.array([K[0], m2[0]])
        grad = np.zeros(2)
        for k in range(6):
            d = np.zeros_like(y)
            d[0, k] = 1e-7 * max(abs(y[0, k]), 1.0)
            grad += np.abs(KM(y + d) - KM(y - d)) / (2 * d[0, k]) * sc[0, k]
        worst = np.maximum(worst, grad)
    c = g.constants()
    assert c["E"][0] == E0 and c["L"][0] == L0
    bound = c["steps"][0] * math.sqrt(6) * worst
    assert abs(c["dK"][0]) <= bound[0], (c["dK"][0], bound)
    assert abs(c["dmu2"][0]) <= bound[1], (c["dmu2"][0], bound)


def test_drift_budgets_hold_to_the_horizon_and_catch_a_wrong_force():
    """Review B6-G7: each body's budgets of K and mu^2 (summed over its accepted steps from the analytic gradient,
    ``Geodesics._grad``) hold at every sampled time of a fall to the capture radius, where the shell's terms grow as
    1/Delta (the playground's former tolerance 10 rtol sqrt(steps) failed there: checked below), and along an inclined
    orbit; their evaluation's rounding adds 16 u of the terms (K: its terms are >= 0, so 16 u K; mu^2: 16 u
    shell_scale). The gradient against central differences (h and h/2: their difference bounds the truncation, x2
    rule, plus the rounding 4 u |terms| / h). Negative control: a relative error of 1e-6 in dp_r/dlambda or in
    dp_theta/dlambda (a wrong force) exceeds the budgets within 300 M (measured x14.5 and x67; 1e-7: x1.45, x6.7)."""
    g = KNW.Geodesics(0.9, 0.3)
    g.add_body(8.0, 1.2, 0.3, v=(0.1, 0.05, 0.35))
    g.add_photon(9.0, 1.3, 0.2, n=[-0.8, 0.3, 0.5])
    y, c = g._y.copy(), g._c
    an = g._grad(y, c)

    def fd(h):
        out = [np.zeros_like(y), np.zeros_like(y)]
        for k in range(6):
            d = np.zeros_like(y)
            d[:, k] = h * np.maximum(np.abs(y[:, k]), 1.0)
            mp, Kp, sp = g._shell(y + d, c)
            mm, Km, _ = g._shell(y - d, c)
            out[0][:, k] = (Kp - Km) / (2 * d[:, k])
            out[1][:, k] = (mp - mm) / (2 * d[:, k])
        return out, sp
    (f1, s1), (f2, _) = fd(1e-5), fd(5e-6)
    terms = np.stack([np.abs(g._shell(y, c)[1]), g._shell(y, c)[2]])  # K's and the shell's term scales
    for j in range(2):
        tol = 2 * np.abs(f1[j] - f2[j]) + 4 * U * terms[j][:, None] / (5e-6 * np.maximum(np.abs(y), 1.0))
        assert np.all(np.abs(an[j] - f2[j]) <= tol), (j, an[j] - f2[j], tol)

    def worst(chi, q, r0, th, ph, v, t_end, dt):
        g = KNW.Geodesics(chi, q, rtol=1e-10, capture_eps=1e-4, r_escape=2e3)
        g.add_body(r0, th, ph, v=v, key="b")
        t, w, old = 0.0, 0.0, 0.0
        while g.status()[0] == "active" and t < t_end:
            t += dt
            g.advance(t)
            if g.status()[0] != "active":
                break
            cc = g.constants()
            w = max(w, abs(cc["dmu2"][0]) / (cc["budget_mu2"][0] + 16 * U * cc["shell_scale"][0]),
                    abs(cc["dK"][0]) / (cc["budget_K"][0] + 16 * U * abs(cc["K"][0])))
            old = max(old, abs(cc["dmu2"][0]) / (10 * g.rtol * math.sqrt(max(cc["steps"][0], 1))))
        return w, old, g.status()[0]
    for chi, q in ((0.9, 0.0), (0.9, 0.4), (0.0, 0.0)):  # the preset's falling body (review r05c)
        w, old, st = worst(chi, q, 12.0, math.pi / 2, math.radians(200), (0.0, 0.0, 0.1), 1e9, 0.05)
        assert st == "captured" and w <= 1.0 and old > 1.0, (chi, q, w, old)
    w, _, st = worst(0.9, 0.3, 8.0, math.radians(70), 0.0, (0.0, 0.08, 0.42), 3000.0, 100.0)
    assert st == "active" and w <= 1.0, w
    orig = KNW.rhs_mino
    for comp in (3, 4):
        def bad(y, E, L, mu2, chi, q, comp=comp):
            d, T = orig(y, E, L, mu2, chi, q)
            d = d.copy()
            d[:, comp] *= 1.0 + 1e-6
            return d, T
        KNW.rhs_mino = bad
        try:
            w, _, _ = worst(0.9, 0.3, 8.0, math.radians(70), 0.0, (0.0, 0.08, 0.42), 300.0, 10.0)
        finally:
            KNW.rhs_mino = orig
        assert w > 1.0, (comp, w)


def test_a_saved_captured_or_escaped_body_is_added_as_it_was():
    """Review B6-G11: a captured body's saved state lies at r_+ + capture_eps up to the event's location (below it by
    rounding): it is added with status "captured" (not advanced, its proper time kept), an active start there is
    refused as before, a state under the horizon always; the status survives a state_dict round trip. A saved state
    carries its drift accounting (K at the original start, the budgets): near the horizon the integration's own
    shell drift (here ~4e-9 of the shell's terms) is far above the 1e-9 check of a new start, within the budget;
    without the budget the same state is refused (control), and the reloaded body's checks equal the original's."""
    g = KNW.Geodesics(0.9, 0.0, rtol=1e-10, capture_eps=1e-4)
    g.add_body(12.0, math.pi / 2, 0.0, v=(0.0, 0.0, 0.1), key="f")
    g.advance(200.0)
    assert g.status() == ["captured"]
    r, th, ph = g.bl()[0]
    p, tau = g.momenta()[0], float(g.proper_time()[0])
    c = g.constants()
    saved = dict(tau=tau, K0=float(c["K0"][0]),
                 budget=(float(c["budget_K"][0]), float(c["budget_mu2"][0])))
    h = KNW.Geodesics(0.9, 0.0, rtol=1e-10, capture_eps=1e-4, t=200.0)
    with pytest.raises(ValueError, match="mass shell"):
        h.add_state(r, th, ph, p, 1.0, key="f", tau=tau, status="captured")
    h.add_state(r, th, ph, p, 1.0, key="f", status="captured", **saved)
    h.add_body(10.0, math.pi / 2, 0.0, v=(0.0, 0.0, 0.3), key="o")
    h.advance(250.0)
    assert h.status() == ["captured", "active"] and np.array_equal(h.bl()[0], g.bl()[0])
    assert float(h.proper_time()[0]) == tau
    ch = h.constants()
    for k in ("dK", "dmu2", "budget_K", "budget_mu2"):
        assert ch[k][0] == c[k][0], k
    if r < h.r_plus + h.capture_eps:  # the located event is at most rounding below the capture radius
        with pytest.raises(ValueError):
            h.add_state(r, th, ph, p, 1.0, key="f2", **saved)
    with pytest.raises(ValueError):
        h.add_state(h.r_plus * (1 - 1e-9), th, ph, p, 1.0, key="f3", status="captured", **saved)
    k = KNW.Geodesics.from_state_dict(json.loads(json.dumps(h.state_dict())))
    assert k.status() == h.status()


@pytest.mark.parametrize("chi,q", [(0.0, 0.7), (0.9, 0.0), (0.5, 0.6)])
def test_proper_time_on_circular_orbits(chi, q):
    """A body started on the circular orbit (ZAMO velocity varpi (Omega - omega)/alpha along phi) stays at r and
    its proper time after 10 orbits equals T dtau/dt of circular_orbit (x2 rule; closed forms in the Kerr and RN
    limits are tested above)."""
    r = 9.0
    co = KNW.circular_orbit(r, chi, q)
    z = KNW.zamo(r, math.pi / 2, chi, q)
    vphi = float(z["varpi"]) * (float(co["Omega"]) - float(z["omega"])) / float(z["alpha"])

    def add(g):
        g.add_body(r, math.pi / 2, 0.0, v=(0.0, 0.0, vphi))
    g, gc = _companion_pair(chi, q, add, rtol=1e-11)
    T = 10 * 2 * math.pi / float(co["Omega"])
    g.advance(T)
    gc.advance(T)
    tau, tauc = g.proper_time()[0], gc.proper_time()[0]
    ref = T * float(co["dtau_dt"])
    assert abs(tau - ref) <= 2 * abs(tau - tauc) + 64 * U * T, (tau, ref)
    assert abs(g.bl()[0, 0] - r) <= 2 * abs(g.bl()[0, 0] - gc.bl()[0, 0]) + 64 * U * r * 10


def test_radial_infall_capture_and_proper_time_of_crossing():
    """Schwarzschild: a body falls from rest at r0 = 10; the capture event at r_+ + capture_eps reports the proper
    time there and of the crossing, against the cycloid tau(r) = sqrt(r0^3/8) (eta + sin eta), r = r0 (1 + cos eta)/2
    (x2 rule; the crossing's first-order extrapolation over capture_eps adds at most capture_eps^2 / 2 times
    max |d^2 tau/dr^2| on [r_+, r_+ + capture_eps]: dtau/dr = -(E^2 - f)^(-1/2), so d^2 tau/dr^2 = -f' (E^2 - f)^(-3/2)
    / 2, 0.35 at the horizon here; review B6-G18: a constant 1e3 stood for it). Reissner-Nordstrom (q = 0.6): the
    same against the quadrature tau = int dr / sqrt(E^2 - f), E^2 = f(r0), f = 1 - 2/r + q^2/r^2."""
    for q in (0.0, 0.6):
        def add(g):
            g.add_body(10.0, math.pi / 2, 0.0)
        g = KNW.Geodesics(0.0, q, rtol=1e-11, capture_eps=1e-6)
        gc = KNW.Geodesics(0.0, q, rtol=1e-13, capture_eps=1e-6)
        add(g)
        add(gc)
        ev, evc = g.advance(300.0), gc.advance(300.0)
        assert len(ev) == 1 and ev[0]["kind"] == "captured" and g.status() == ["captured"]
        rp = KNW.horizons(0.0, q)[0]
        assert abs(ev[0]["r"] - (rp + 1e-6)) <= 1e-12 * rp

        def tau_ref(r):
            if q == 0.0:
                et = math.acos(2 * r / 10.0 - 1)
                return math.sqrt(1000.0 / 8) * (et + math.sin(et))
            f = lambda x: 1 - 2 / x + q * q / x ** 2  # noqa: E731
            E2 = f(10.0)
            # x = 10 - s^2 removes the turning point's 1/sqrt at r0
            val, err = si.quad(lambda s: 2 * s / math.sqrt((E2 - f(10.0 - s * s))), 0.0, math.sqrt(10.0 - r),
                               epsabs=0, epsrel=1e-13, limit=200)
            return val
        for key, r in (("tau", ev[0]["r"]), ("tau_horizon", rp)):
            tol = 2 * abs(ev[0][key] - evc[0][key]) + 1e-11 * ev[0][key]
            if key == "tau_horizon":
                f = lambda x: 1 - 2 / x + q * q / x ** 2  # noqa: E731
                fp = lambda x: 2 / x ** 2 - 2 * q * q / x ** 3  # noqa: E731
                # |tau''| changes by O(capture_eps) relative over the interval: its larger end value, +0.1 %
                tpp = 1.001 * max(0.5 * fp(x) / (f(10.0) - f(x)) ** 1.5 for x in (rp, rp + 1e-6))
                tol += 1e-12 * 10 + 0.5 * (1e-6) ** 2 * tpp
            assert abs(ev[0][key] - tau_ref(r)) <= tol, (q, key, ev[0][key], tau_ref(r))


def test_outgoing_photon_escape_time():
    """Reissner-Nordstrom (q = 0.5): a radially outgoing photon from r0 = 5 reaches r_escape = 300 at the
    tortoise-coordinate time t = r*(300) - r*(5), r* = r + r_+^2/(r_+ - r_-) ln(r - r_+) - r_-^2/(r_+ - r_-) ln(r - r_-)
    (dr*/dr = 1/f); the escape event (located to 1e-12 r) within the x2 rule."""
    q = 0.5
    rp, rm = KNW.horizons(0.0, q)

    def rstar(r):
        return r + rp * rp / (rp - rm) * math.log(r - rp) - rm * rm / (rp - rm) * math.log(r - rm)

    def add(g):
        g.add_photon(5.0, math.pi / 2, 0.0, n=[1.0, 0.0, 0.0])
    g = KNW.Geodesics(0.0, q, rtol=1e-11, r_escape=300.0)
    gc = KNW.Geodesics(0.0, q, rtol=1e-13, r_escape=300.0)
    add(g)
    add(gc)
    ev, evc = g.advance(1e3), gc.advance(1e3)
    assert ev[0]["kind"] == "escaped" and ev[0]["photon"]
    ref = rstar(300.0) - rstar(5.0)
    assert abs(ev[0]["t"] - ref) <= 2 * abs(ev[0]["t"] - evc[0]["t"]) + 1e-12 * 300 + 64 * U * ref


def _rn_deflection_quad(b, q, r_out=math.inf):
    """Exact swept angle of a RN ray with impact parameter b from r_out in to r_min and out to r_out:
    2 int_{r_min}^{r_out} b dr / (r^2 sqrt(1 - b^2 f(r)/r^2)), r = r_min + s^2 (smooth integrand), and its error."""
    rmin = max(z.real for z in np.roots([1.0, 0.0, -b * b, 2 * b * b, -q * q * b * b]) if abs(z.imag) < 1e-9)
    for _ in range(3):
        F = rmin ** 4 - b * b * (rmin ** 2 - 2 * rmin + q * q)
        rmin -= F / (4 * rmin ** 3 - b * b * (2 * rmin - 2))

    def g(s):
        if s == 0.0:
            return _g0(rmin, b, q)
        r = rmin + s * s
        h = 1.0 - b * b * (1.0 - 2.0 / r + q * q / (r * r)) / (r * r)
        return 2 * s * b / (r * r * math.sqrt(h))
    up = math.sqrt(r_out - rmin) if math.isfinite(r_out) else math.inf
    if math.isfinite(up):
        val, err = si.quad(g, 0.0, up, epsabs=0.0, epsrel=1e-13, limit=400)
    else:
        v1, e1 = si.quad(g, 0.0, 1.0, epsabs=0.0, epsrel=1e-13, limit=400)
        v2, e2 = si.quad(g, 1.0, math.inf, epsabs=0.0, epsrel=1e-13, limit=400)
        val, err = v1 + v2, e1 + e2
    return 2 * val, 2 * err


def _g0(rmin, b, q):
    """The integrand's limit at s = 0: 2 b / (r_min^2 sqrt(h'(r_min))), h = 1 - b^2 f/r^2."""
    r = rmin
    hp = b * b * (2.0 / r ** 3 - 6.0 / r ** 4 + 4.0 * q * q / r ** 5)
    return 2 * b / (r * r * math.sqrt(hp))


def test_rn_light_deflection_quadrature_and_weak_field_series():
    """(1) A photon with impact parameter b = 20 (q = 0.6) sent in from r0 = 400 and caught on its way out at r0:
    its swept angle phi against the exact quadrature over the same range (x2 rule + the quadrature's error + the
    event's location 1e-12 r0 |dphi/dr|). (2) The weak-field series of Keeton & Petters (2005), Eq. (53):
    alpha = 4/b + (5 - q^2) (3 pi/4)/b^2 + (128/3 - 16 q^2)/b^3 + O(b^-4) against the exact quadrature from
    infinity: the residual falls as b^-4 (slope between b = 100 and 400 within 0.15 of 4). Negative control: the
    Schwarzschild coefficients (q dropped) leave a residual falling only as b^-2."""
    q = 0.6
    b, r0 = 20.0, 400.0
    f0 = 1 - 2 / r0 + q * q / r0 ** 2
    sinpsi = b * math.sqrt(f0) / r0

    def add(g):
        g.add_photon(r0, math.pi / 2, 0.0, n=[-math.sqrt(1 - sinpsi ** 2), 0.0, sinpsi])
    g = KNW.Geodesics(0.0, q, rtol=1e-11, r_escape=r0)
    gc = KNW.Geodesics(0.0, q, rtol=1e-13, r_escape=r0)
    add(g)
    add(gc)
    ev, evc = g.advance(5e3), gc.advance(5e3)
    assert ev[0]["kind"] == "escaped"
    ref, err = _rn_deflection_quad(b, q, r0)
    dphidr = b / (r0 * r0 * math.sqrt(1 - b * b * f0 / r0 ** 2))
    assert abs(ev[0]["phi"] - ref) <= 2 * abs(ev[0]["phi"] - evc[0]["phi"]) + 2 * err + 1e-12 * r0 * dphidr * 2

    def series(bb, qq):
        return 4 / bb + (5 - qq * qq) * 0.75 * math.pi / bb ** 2 + (128 / 3 - 16 * qq * qq) / bb ** 3

    res = {}
    for bb in (100.0, 400.0):
        alpha, e = _rn_deflection_quad(bb, q)
        alpha -= math.pi
        res[bb] = (abs(alpha - series(bb, q)), abs(alpha - series(bb, 0.0)), e)
        assert res[bb][2] < 1e-2 * res[bb][0]  # the slope then moves by <= (2e-2)/ln 4 = 0.015
    slope = math.log(res[100.0][0] / res[400.0][0]) / math.log(4.0)
    slope0 = math.log(res[100.0][1] / res[400.0][1]) / math.log(4.0)
    assert abs(slope - 4.0) <= 0.15, slope
    assert abs(slope0 - 2.0) <= 0.15, slope0


def test_state_dict_restores_bit_identically_and_companion():
    """Save (through JSON), restore, continue: bit-identical; a companion (rtol/100) from the same state."""
    g = KNW.Geodesics(0.7, 0.3, rtol=1e-10, r_escape=50.0)
    g.add_body(8.0, 1.2, 0.3, v=[0.1, 0.05, 0.35])
    g.add_photon(9.0, 1.3, 0.2, n=[0.8, 0.3, 0.5], key="ray")
    g.add_body(4.0, 1.5, 0.0, v=[-0.5, 0.0, 0.0], key="faller")
    g.advance(7.3)
    d = json.loads(json.dumps(g.state_dict()))
    h = KNW.Geodesics.from_state_dict(d)
    ea, eb = g.advance(80.0), h.advance(80.0)
    assert ea == eb and {e["key"] for e in ea} == {"ray", "faller"}
    assert np.array_equal(g._y, h._y) and g.status() == h.status()
    c = g.clone(rtol=1e-12)
    assert c.rtol == 1e-12 and np.array_equal(c._y, g._y)
    g.remove("ray")
    assert g.keys == [0, "faller"]


# --- the camera ------------------------------------------------------------------------------------------------------
def test_far_observer_sees_the_sky_almost_undistorted():
    """An observer at r = 1e4 (a = 0, q = 0 and 0.5) looking outwards at psi = 20, 50, 80 deg from the radial: the
    sky direction of each ray equals the exact sweep int_{r_o}^inf b dr / (r^2 sqrt(1 - b^2 f/r^2)),
    b = r_o sin psi / sqrt(f(r_o)), within the x2 rule (rtol 1e-10 against 1e-12) + the straight-line remainder beyond
    r_far (2 M / r_far) + the quadrature's error; the distortion phi_inf - psi is of order M/b (below the full
    weak-field deflection 4 M/b; measured 3.5e-5 .. 1.7e-4) and the rays stay in the equatorial plane."""
    r_o = 1e4
    psis = np.radians([20.0, 50.0, 80.0])
    look = np.stack([np.cos(psis), np.zeros(3), np.sin(psis)], 1)
    for q in (0.0, 0.5):
        o = KNW.trace_sky(0.0, q, r_o, math.pi / 2, look)
        o2 = KNW.trace_sky(0.0, q, r_o, math.pi / 2, look, rtol=1e-12)
        assert o["escaped"].all()

        def f(r):
            return 1 - 2 / r + q * q / r ** 2
        for i, ps in enumerate(psis):
            b = r_o * math.sin(ps) / math.sqrt(f(r_o))
            ref, err = si.quad(lambda r: b / (r * r * math.sqrt(1 - b * b * f(r) / r ** 2)), r_o, math.inf,
                               epsabs=0, epsrel=1e-13, limit=200)
            tol = 2 * abs(o["phi_inf"][i] - o2["phi_inf"][i]) + 2 / 1e9 + err + 64 * U
            assert abs(o["phi_inf"][i] - ref) <= tol, (q, ps, o["phi_inf"][i], ref)
            assert 0.0 < o["phi_inf"][i] - ps < 4 / b
            assert abs(o["theta_inf"][i] - math.pi / 2) <= 1e-12


def _edge(trace, lo, hi, rounds=6, n=48):
    """The capture boundary in a 1-parameter family of rays: zoom rounds of n rays between lo (captured) and hi
    (escaped). Returns (lo, hi, the traced outputs at lo and hi)."""
    for _ in range(rounds):
        ps = np.linspace(lo, hi, n)
        o = trace(ps)
        assert not o["undecided"].any()
        cap = o["captured"]
        k = int(np.flatnonzero(~cap)[0])
        lo, hi = ps[k - 1], ps[k]
    o = trace(np.array([lo, hi]))
    return lo, hi, o


@pytest.mark.parametrize("q", [0.0, 0.6])
def test_shadow_size_seen_from_a_finite_distance_reissner_nordstrom(q):
    """a = 0, observer at r_o = 30: the shadow's angular radius psi_sh (the capture boundary of rays looking at
    angle psi from the hole) obeys sin psi_sh = b_c sqrt(f(r_o)) / r_o with the critical impact parameter
    b_c = r_ph^2 / sqrt(Delta(r_ph)), r_ph = (3 + sqrt(9 - 8 q^2))/2 (Pugliese et al. 2011, Eq. 36): q = 0 gives
    b_c = sqrt(27). Tolerance: the bracket's width + the x2 rule (rtol 1e-10 against 1e-12)."""
    r_o = 30.0

    def trace(rtol):
        return lambda ps: KNW.trace_sky(0.0, q, r_o, math.pi / 2, np.stack([-np.cos(ps), 0 * ps, np.sin(ps)], 1),
                                        rtol=rtol)
    lo, hi, _ = _edge(trace(1e-10), 0.05, 0.6)
    lo2, hi2, _ = _edge(trace(1e-12), 0.05, 0.6)
    rph = (3 + math.sqrt(9 - 8 * q * q)) / 2
    bc = rph ** 2 / math.sqrt(rph ** 2 - 2 * rph + q * q)
    if q == 0.0:
        assert bc == pytest.approx(math.sqrt(27.0), rel=4 * U)
    ref = math.asin(bc * math.sqrt(1 - 2 / r_o + q * q / r_o ** 2) / r_o)
    edge, edge2 = 0.5 * (lo + hi), 0.5 * (lo2 + hi2)
    assert abs(edge - ref) <= (hi - lo) + (hi2 - lo2) + 2 * abs(edge - edge2) + 64 * U, (edge, ref)


@pytest.mark.parametrize("chi,theta_o_deg,dirs", [(0.9, 60.0, (0.0, 120.0, 240.0)), (0.5, 89.0, (70.0, 180.0))])
def test_kerr_shadow_edge_lies_on_bardeens_curve(chi, theta_o_deg, dirs):
    """q = 0, observer at r_o = 1e3: along several directions on the camera's screen the capture boundary is found;
    the boundary rays' constants, mapped to the distant observer's screen (alpha = -lambda/sin theta_o,
    |beta| = sqrt(Theta(theta_o)); GL-b Eq. 55, ``kerr_null.constants_to_screen``), lie on Bardeen's critical curve:
    its distance from the centre along their screen angle (``kerr_null.critical_radius_at``) is within the bracket's
    two radii, widened by the decision's resolution: a ray at relative distance d from the curve orbits ~ln(1/d)/gamma
    half-orbits before its fate shows, and the accumulated per-step error of its radial constant, steps sqrt(6) rtol,
    decides it below that (widening rho steps sqrt(6) rtol / 2; rtol 1e-12; measured misses <= 1.6e-12 relative).
    (The comparison in (lambda, eta) is ill-conditioned where the curve crosses beta = 0: there the same edge differs
    by 3e-8 in eta.)"""
    r_o, th = 1e3, math.radians(theta_o_deg)
    rtol = 1e-12

    def screen(lam, eta):
        Th = eta + chi * chi * math.cos(th) ** 2 - lam * lam / math.tan(th) ** 2
        al, be = -lam / math.sin(th), math.sqrt(max(Th, 0.0))
        return math.atan2(be, al), math.hypot(al, be)
    for chi_dir in np.radians(dirs):
        def trace(ps, cd=chi_dir):
            d = np.stack([-np.cos(ps), np.sin(ps) * np.sin(cd), np.sin(ps) * np.cos(cd)], 1)
            return KNW.trace_sky(chi, 0.0, r_o, th, d, rtol=rtol)
        lo, hi, o = _edge(trace, 1e-3, 2e-2, n=32)
        (a0, r0), (a1, r1) = screen(o["lam"][0], o["eta"][0]), screen(o["lam"][1], o["eta"][1])
        ang, rlo, rhi = 0.5 * (a0 + a1), min(r0, r1), max(r0, r1)
        crit = KNL.critical_radius_at(chi, th, ang)[0]
        widen = crit * int(o["steps"].max()) * math.sqrt(6) * rtol / 2 + 64 * U * crit
        assert rlo - widen <= crit <= rhi + widen, (math.degrees(chi_dir), rlo, rhi, crit, widen)


def test_moving_observer_sees_the_aberrated_sky():
    """An observer moving with v = 0.5 along phi-hat relative to the ZAMO at r = 1e4 (a = 0): the ray it sees along
    look direction d is the ray the ZAMO sees along the aberrated direction (core.lorentz.aberrate), and its E
    (= nu_inf / nu_obs) is the ZAMO's E times aberrate's Doppler factor D = nu_ZAMO / nu_obs (review B6-G18: the text
    said "divided by")."""
    from lfphys.core.lorentz import aberrate
    d = np.array([[0.3, 0.1, 0.9]]) / np.linalg.norm([0.3, 0.1, 0.9])
    v = np.array([0.0, 0.0, 0.5])
    om = KNW.trace_sky(0.0, 0.0, 1e4, 1.0, d, v_obs=v)
    om2 = KNW.trace_sky(0.0, 0.0, 1e4, 1.0, d, v_obs=v, rtol=1e-12)
    kz, D = aberrate(-d, v)
    oz = KNW.trace_sky(0.0, 0.0, 1e4, 1.0, -kz)
    for k in ("phi_inf", "theta_inf"):  # two runs from starts equal to round-off: within both runs' errors (x2)
        assert abs(om[k][0] - oz[k][0]) <= 4 * abs(om[k][0] - om2[k][0]) + 64 * U, k
    assert om["E"][0] == pytest.approx(oz["E"][0] * float(D[0]), rel=64 * U)
