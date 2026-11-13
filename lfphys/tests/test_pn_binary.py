# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Post-Newtonian two-body motion (lfphys.core.gravity.pn_binary), each part against an independent route:

* the coefficients against a second transcription (Kidder 1995, grouped differently from Blanchet 2014);
* conservation of the 2PN energy and angular momentum: the residual along the equations of motion scales as c^-6
  (a wrong 1PN or 2PN coefficient would leave a residual of a lower order);
* gauge-invariant closed forms of the theory (Blanchet 2014): the periastron advance K(eps, j) and the mean motion
  n(eps, j) (Eq. (348)), the circular frequency (Eq. (228)) and energy E(x) (Eq. (232)), measured on integrated orbits;
* radiation reaction: on circular orbits against Eq. (226); averaged over Kepler ellipses against the quadrupole
  fluxes of Peters & Mathews (exact at 2.5PN, also in a second gauge, Kidder's); at 3.5PN against the 1PN eccentric
  flux of Blanchet 2014 Eqs. (358)-(359);
* the two integrators against each other; the step API (exact restart, splitting).

Tolerances: where the theory fixes the order of the first neglected term, the tests check that order (the slope of
the residual, or its shrinking under halving of the PN parameter); a wrong coefficient changes the order by one,
which these tests separate by a wide margin.
"""

import math

import numpy as np
import pytest

from lfphys.core.gravity import pn_binary as P

NUS = (0.25, 0.1, 0.01)


def _I0(e):
    return (1.0 + 73.0 / 24.0 * e**2 + 37.0 / 96.0 * e**4) / (1.0 - e * e) ** 3.5


def _I1(e, nu):
    """Blanchet 2014 Eq. (359b)."""
    e2 = e * e
    return (-1247.0 / 336.0 - 35.0 / 12.0 * nu + e2 * (10475.0 / 672.0 - 1081.0 / 36.0 * nu)
            + e2**2 * (10043.0 / 384.0 - 311.0 / 12.0 * nu) + e2**3 * (2179.0 / 1792.0 - 851.0 / 576.0 * nu)) \
        / (1.0 - e2) ** 4.5


def _kidder_a(x, v, nu, rr=True):
    """Kidder 1995 Eqs. (2.2a, b, d, f) as printed there (m = 1): a second transcription, grouped differently from
    Blanchet's A, B; its radiation-reaction term is in a different gauge (Iyer-Will alpha = 4, beta = 5)."""
    r = np.linalg.norm(x)
    n = x / r
    rd = float(n @ v)
    v2 = float(v @ v)
    m_r = 1.0 / r
    a = -n / r**2
    a = a - (1.0 / r**2) * (n * ((1 + 3 * nu) * v2 - 2 * (2 + nu) * m_r - 1.5 * nu * rd**2) - 2 * (2 - nu) * rd * v)
    a = a - (1.0 / r**2) * (n * (0.75 * (12 + 29 * nu) * m_r**2 + nu * (3 - 4 * nu) * v2**2
                                 + 15.0 / 8.0 * nu * (1 - 3 * nu) * rd**4 - 1.5 * nu * (3 - 4 * nu) * v2 * rd**2
                                 - 0.5 * nu * (13 - 4 * nu) * m_r * v2 - (2 + 25 * nu + 2 * nu**2) * m_r * rd**2)
                            - 0.5 * rd * v * (nu * (15 + 4 * nu) * v2 - (4 + 41 * nu + 8 * nu**2) * m_r
                                              - 3 * nu * (3 + 2 * nu) * rd**2))
    if rr:
        a = a + 1.6 * nu / r**3 * (rd * n * (18 * v2 + 2.0 / 3.0 * m_r - 25 * rd**2)
                                   - v * (6 * v2 - 2 * m_r - 15 * rd**2))
    return a


def test_coefficients_agree_with_a_second_transcription():
    rng = np.random.default_rng(7)
    for nu in NUS:
        for _ in range(20):
            r = rng.uniform(10.0, 200.0)
            x = r * np.array([1.0, 0.0, 0.0])
            v = math.sqrt(1.0 / r) * rng.uniform(0.3, 1.4) * np.array([rng.normal(), rng.normal(), 0.0])
            mine = P.acceleration(x, v, nu, (1, 2))
            ref = _kidder_a(x, v, nu, rr=False)
            # both sum terms of size up to |a_N| = 1/r^2 in float64: agreement to a few ulp of that
            assert np.max(np.abs(mine - ref)) <= 1e-14 / r**2


def test_newtonian_limit_and_vectorisation():
    x = np.array([[10.0, 0, 0], [0, 20.0, 0]])
    v = np.array([[0, 0.3, 0], [-0.2, 0, 0.1]])
    a = P.acceleration(x, v, 0.2, ())
    assert np.allclose(a, -x / np.linalg.norm(x, axis=1)[:, None] ** 3, rtol=0, atol=1e-17)
    full = P.acceleration(x, v, 0.2)
    for k in range(2):
        assert np.array_equal(full[k], P.acceleration(x[k], v[k], 0.2))
    with pytest.raises(ValueError):
        P.acceleration(x, v, 0.2, (1, 3))


def _slope(fun, eps_values):
    vals = [fun(e) for e in eps_values]
    return [math.log(vals[k] / vals[k + 1]) / math.log(eps_values[k] / eps_values[k + 1]) for k in range(len(vals) - 1)]


@pytest.mark.parametrize("nu", NUS)
@pytest.mark.parametrize("order", [1, 2])
def test_energy_and_angular_momentum_are_conserved_to_their_order(nu, order):
    """dE/dt and dJ/dt along the conservative equations of the same order: relative residual O(eps^(order + 1))
    with eps = m/r (complex-step derivatives, exact to rounding). The slope must be order + 1 within 0.05 (the next
    term shifts it by O(eps), measured 0.005 at eps = 4e-3); a wrong coefficient at the order lowers it by 1."""
    orders = (1,) if order == 1 else (1, 2)
    shapes = [(0.8, 0.5), (1.2, 1.0), (1.0, 2.0), (1.3, 2.7), (0.6, 1.4)]

    def worst(eps, which):
        out = 0.0
        for f, ang in shapes:
            x = np.array([1.0 / eps, 0.0, 0.0])
            v = f * math.sqrt(eps) * np.array([math.cos(ang), math.sin(ang), 0.0])
            a = P.acceleration(x, v, nu, orders)
            if which == "E":
                d = abs(P.rate_along(lambda X, V: P.energy(X, V, nu, order), x, v, a)) / eps**2.5
            else:
                d = np.linalg.norm(P.rate_along(lambda X, V: P.angular_momentum(X, V, nu, order), x, v, a)) / eps
            out = max(out, d)
        return out

    for which in ("E", "J"):
        for s in _slope(lambda e: worst(e, which), [4e-3, 2e-3, 1e-3]):
            assert abs(s - (order + 1)) < 0.05, (which, s)


def test_conserved_quantities_repeat_at_every_periapsis():
    """Along an integrated 2PN orbit E and J are functions of (r, rdot, v^2), hence equal at every periapsis: their
    spread over 8 radial periods is the integrator's error (rtol 1e-13), no secular change. Within an orbit E_2PN
    is not exact; its excursion is O(eps^3) of |E| (the 3PN remainder): slope 3 within 0.1 when eps halves
    (measured 2.97 between eps = 0.008 and 0.004; 2.75 between 0.016 and 0.008, where O(eps^4) still shows)."""
    nu, j = 0.2, 0.75
    swing = []
    for eps in (0.008, 0.004):
        st = P.state_from_invariants(eps, j, nu)
        Pr = 2 * math.pi / P.mean_motion(eps, j, nu)
        out = P.integrate(st, 8.5 * Pr, nu, orders=(1, 2), rtol=1e-13, n_out=2000)
        assert len(out["t_peri"]) == 8
        E = [float(P.energy(*out["at"](t), nu)) for t in out["t_peri"]]
        J = [float(np.linalg.norm(P.angular_momentum(*out["at"](t), nu))) for t in out["t_peri"]]
        assert np.ptp(E) / abs(E[0]) < 1e-11 and np.ptp(J) / J[0] < 1e-11
        Es = P.energy(out["x"], out["v"], nu)
        swing.append(np.ptp(Es) / abs(Es[0]))
    assert abs(math.log2(swing[0] / swing[1]) - 3.0) < 0.1


@pytest.mark.parametrize("nu", [0.25, 0.1])
@pytest.mark.parametrize("j", [0.95, 0.75, 0.5])
def test_periastron_advance_and_mean_motion_are_gauge_invariant_closed_forms(nu, j):
    """Integrated 2PN orbits with prescribed eps, j: the angle of return to periastron and the radial period against
    Blanchet 2014 Eq. (348b, a) at 2PN. The residual is O(eps^3) (3PN, absent from the equations of motion): D =
    residual / eps^3 converges as eps halves, its changes shrinking by about 2 (next term O(eps^4)); an error at
    1PN or 2PN would make D grow like 1/eps^2 or 1/eps."""
    Ds = {"K": [], "n": []}
    for eps in (4e-3, 2e-3, 1e-3):
        st = P.state_from_invariants(eps, j, nu)
        gi = P.gauge_invariants(st["x"], st["v"], nu)
        assert gi["eps"] == pytest.approx(eps, rel=1e-13) and gi["j"] == pytest.approx(j, rel=1e-13)
        res = P.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=())
        Ds["K"].append((res["Phi"] / (2 * math.pi) - P.periastron_K(eps, j, nu)) / eps**3)
        Ds["n"].append(((2 * math.pi / res["P_r"]) / P.mean_motion(eps, j, nu) - 1.0) / eps**3)
    for key, D in Ds.items():
        d1, d2 = D[1] - D[0], D[2] - D[1]
        assert abs(d2) <= 0.75 * abs(d1) + 0.05, (key, D)
        # the 2PN terms are resolved: at eps = 1e-3 the residual is far below them
        if key == "K":
            K2 = P.periastron_K(1e-3, j, nu) - 1.0 - 3e-3 / j
            assert abs(D[2]) * 1e-9 < 0.05 * K2


def test_circular_orbits_frequency_and_energy():
    """Circular orbits of the conservative 2PN equations: Omega^2(r) against Eq. (228) (relative residual O(1/r^3),
    3PN) and the energy against the gauge-invariant E(x) of Eq. (232) (relative residual O(x^3))."""
    for nu in NUS:
        def w_res(r):
            vt = P.circular_speed(r, nu, (1, 2))
            return abs((vt / r) ** 2 / P.omega2_circular_harmonic(r, nu) - 1.0)

        def e_res(r):
            vt = P.circular_speed(r, nu, (1, 2))
            x = (vt / r) ** (2.0 / 3.0)
            E = float(P.energy([r, 0, 0], [0, vt, 0], nu))
            return abs(E / P.circular_energy(x, nu) - 1.0)

        for s in _slope(lambda e: w_res(1.0 / e), [8e-3, 4e-3, 2e-3]):
            assert abs(s - 3.0) < 0.1
        for s in _slope(lambda e: e_res(1.0 / e), [4e-3, 2e-3, 1e-3]):
            assert abs(s - 3.0) < 0.1


def test_circular_radiation_reaction_matches_eq_226():
    """On a quasi-circular orbit (radial velocity of Eq. (227a)) the coefficient of v in the acceleration against
    Eq. (226): -(32/5)(nu/r^4)[1 + (1/r)(-743/336 - 11 nu/4)]. The 3.5PN terms (and the 1PN term times the
    radiative rdot) enter the 1/r correction; residual O(1/r^2) relative (slope 2)."""
    for nu in NUS:
        def res(eps):
            r = 1.0 / eps
            vt = P.circular_speed(r, nu)
            rd = P.circular_inspiral_rate(r, nu)
            A, B = P.coefficients(r, rd, vt * vt + rd * rd, nu)
            return abs(B / (P.circular_rr_coefficient(r, nu) * r * r) - 1.0)
        for s in _slope(res, [1e-2, 5e-3, 2.5e-3]):
            assert abs(s - 2.0) < 0.1
        # without the 3.5PN terms the 1PN part of Eq. (226) is missed: residual O(1/r) instead
        r = 400.0
        vt = P.circular_speed(r, nu)
        A, B = P.coefficients(r, 0.0, vt * vt, nu, (1, 2, 2.5))
        assert abs(B / (P.circular_rr_coefficient(r, nu) * r * r) - 1.0) > 0.5 * (743 / 336 + 11 * nu / 4) / r


def _kepler_average(fun, a, e, n=256):
    """(1/P) int fun dt over a Kepler ellipse (m = 1) by the trapezoidal rule in the eccentric anomaly (periodic,
    analytic: converges geometrically)."""
    u = 2 * math.pi * np.arange(n) / n
    r = a * (1 - e * np.cos(u))
    x = np.stack([a * (np.cos(u) - e), a * math.sqrt(1 - e * e) * np.sin(u), 0 * u], axis=1)
    nmean = a**-1.5
    v = np.stack([-a * np.sin(u), a * math.sqrt(1 - e * e) * np.cos(u), 0 * u], axis=1) * (nmean * a / r)[:, None]
    vals = np.array([fun(x[k], v[k]) for k in range(n)])
    w = (r / a)
    return np.sum(vals * (w if vals.ndim == 1 else w[:, None]), axis=0) / n


@pytest.mark.parametrize("e", [0.0, 0.3, 0.6171340, 0.9])
def test_averaged_reaction_equals_peters_mathews_in_two_gauges(e):
    """The 2.5PN reaction averaged over a Kepler ellipse: <v . a_RR> and <(x x a_RR)_z> equal the Peters-Mathews
    losses -(32/5)(nu/a^5) f(e) and -(32/5)(nu/a^(7/2))(1 + 7e^2/8)/(1 - e^2)^2 per reduced mass (m = 1). Exact
    (the instantaneous balance differs by total derivatives only); the harmonic-gauge term of the engine and Kidder's
    term in another gauge give the same averages; and averaged_dissipation (an integrated orbit) agrees."""
    nu, a = 0.2, 50.0
    dE_ref = -6.4 * nu / a**5 * _I0(e)
    dJ_ref = -6.4 * nu / a**3.5 * (1 + 0.875 * e * e) / (1 - e * e) ** 2
    nn = 64 if e < 0.7 else 1024
    for rr in ("harmonic", "kidder"):
        def f(x, v):
            if rr == "harmonic":
                ar = P.perturbation(x, v, nu, (2.5,))
            else:
                ar = _kidder_a(x, v, nu) - _kidder_a(x, v, nu, rr=False)
            return np.array([float(v @ ar), float(np.cross(x, ar)[2])])
        dE, dJ = _kepler_average(f, a, e, nn)
        assert dE == pytest.approx(dE_ref, rel=1e-12) and dJ == pytest.approx(dJ_ref, rel=1e-12)
    if e > 0.0:
        res = P.averaged_dissipation(P.periapsis_state(a, e), nu, conservative=(), dissipative=(2.5,), order=0)
        assert res["dE"] == pytest.approx(dE_ref, rel=1e-9) and res["dJ"] == pytest.approx(dJ_ref, rel=1e-9)


@pytest.mark.parametrize("nu", [0.25, 0.1])
@pytest.mark.parametrize("j", [0.95, 0.75, 0.5])
def test_reaction_at_3p5pn_gives_the_1pn_eccentric_flux(nu, j):
    """With the 2PN orbit and the 2.5PN + 3.5PN reaction, the averaged loss of E_2PN against the instantaneous flux
    of Blanchet 2014 Eqs. (358)-(359) to 1PN, -(32/5) nu x^5 [I0(e_t) + x I1(e_t)] per reduced mass, with x and e_t
    from eps, j (Eqs. (350), (346e)). D = (ratio - 1)/x - I1/I0 must vanish linearly in x (it halves with eps; the
    2PN flux and the 4.5PN reaction are absent); a wrong 3.5PN coefficient would leave D finite."""
    D = []
    for eps in (2e-3, 1e-3, 5e-4):
        st = P.state_from_invariants(eps, j, nu)
        res = P.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=(2.5, 3.5), order=2)
        x = P.x_parameter(eps, j, nu, order=1)  # the 1PN map, consistent with a 1PN flux
        et = P.time_eccentricity(eps, j, nu)
        ratio = res["dE"] / (-6.4 * nu * x**5 * _I0(et))
        D.append((ratio - 1.0) / x - _I1(et, nu) / _I0(et))
    for k in range(2):
        assert 0.2 <= D[k + 1] / D[k] <= 0.7, D
    assert abs(D[-1]) < 0.1 * max(abs(_I1(math.sqrt(1 - j), nu) / _I0(math.sqrt(1 - j))), 0.5)


def test_secular_decay_matches_peters_orbit_by_orbit():
    """Newton + 2.5PN integrated (Cartesian route): the osculating a and e at successive periapses change per orbit
    as Peters' averages at the mean elements predict. With eps_rr = |Delta a / a| per orbit, first-order averaging
    makes the per-orbit change exact to first order in the reaction (the drift of the elements within the orbit is
    taken by the mean elements), so the residual is second order: measured 0.55-1.6 eps_rr^2 over the three cases
    (eps_rr = 3.6e-4 ... 5.6e-3). Bound 3 eps_rr^2 (review B5, N7: was eps_rr, 1e4 x the measurement): a first-order
    error (a wrong Peters coefficient or reaction term) of relative size above 3 eps_rr ~ 1e-3 ... 2e-2 fails."""
    from lfphys.theories.approx import peters_mathews as PM
    nu = 0.25
    X1 = X2 = 0.5  # G m1, G m2 in units of m (c = 1): X1 X2 = nu

    def rates(a, e):
        return float(PM.da_dt(X1, X2, a, e, c=1.0)), float(PM.de_dt(X1, X2, a, e, c=1.0))

    for a, e in ((100.0, 0.3), (100.0, 0.7), (50.0, 0.5)):
        out = P.integrate(P.periapsis_state(a, e), 6.5 * 2 * math.pi * a**1.5, nu, orders=(2.5,), rtol=1e-13,
                          n_out=10)
        els = [P.newtonian_elements(*out["at"](t)) for t in out["t_peri"]]
        A = np.array([el["a"] for el in els])
        E = np.array([el["e"] for el in els])
        assert len(A) >= 5
        eps_rr = abs(rates(a, e)[0] * 2 * math.pi * a**1.5 / a)
        for k in range(len(A) - 1):
            am, em = 0.5 * (A[k] + A[k + 1]), 0.5 * (E[k] + E[k + 1])
            Pk = 2 * math.pi * am**1.5
            ra, re = rates(am, em)
            assert abs((A[k + 1] - A[k]) / (ra * Pk) - 1) < 3.0 * eps_rr**2
            assert abs((E[k + 1] - E[k]) / (re * Pk) - 1) < 3.0 * eps_rr**2


def test_two_integrators_agree():
    """Cartesian and variation-of-constants routes, all orders, a strong-field eccentric orbit: the positions after
    five periods agree to 1e-9 of the orbit's size (both at rtol 1e-12)."""
    nu = 0.25
    st = P.periapsis_state(60.0, 0.5)
    T = 5 * 2 * math.pi * 60.0**1.5
    xc = P.integrate(st, T, nu, method="cartesian", n_out=60)["x"]
    xe = P.integrate(st, T, nu, method="elements", n_out=60)["x"]
    assert np.max(np.linalg.norm(xc - xe, axis=1)) < 1e-9 * 60.0


def test_step_api_restarts_exactly_and_splits_within_tolerance():
    nu = 0.2
    st = P.circular_state(30.0, nu)
    s1, i1 = P.step(st, 500.0, nu)
    s1b, _ = P.step({"t": st["t"], "x": st["x"].copy(), "v": st["v"].copy()}, 500.0, nu)
    assert np.array_equal(s1["x"], s1b["x"]) and np.array_equal(s1["v"], s1b["v"]) and s1["t"] == s1b["t"]
    # a state saved as text (repr of floats) restores bit for bit
    saved = {"t": repr(s1["t"]), "x": [repr(float(z)) for z in s1["x"]], "v": [repr(float(z)) for z in s1["v"]]}
    back = P.state(float(saved["t"]), [float(z) for z in saved["x"]], [float(z) for z in saved["v"]])
    assert np.array_equal(back["x"], s1["x"]) and np.array_equal(back["v"], s1["v"])
    s2, _ = P.step(back, 500.0, nu)
    whole = P.integrate(st, 1000.0, nu, n_out=3)["end"]
    assert s2["t"] == pytest.approx(1000.0, abs=1e-9)
    assert np.linalg.norm(s2["x"] - whole["x"]) < 1e-9 * 30.0
    for meth in ("cartesian", "elements"):
        a1, _ = P.step(st, 300.0, nu, method=meth)
        a2, _ = P.step(a1, 300.0, nu, method=meth)
        b, _ = P.step(st, 600.0, nu, method=meth)
        assert np.linalg.norm(a2["x"] - b["x"]) < 1e-9 * 30.0


def test_quasi_circular_inspiral_follows_eq_227a_and_stops():
    """Quasi-circular inspirals from r0 to r_stop = 3 r0 / 4: the time taken against the integral of dr/dt of
    Eq. (227a) (harmonic radius). With the 3.5PN terms the relative difference is O(1/r^2) (the 2PN correction of
    the rate is absent): halving the radii raises it by about 4 (measured 5.9 for 40 -> 30 against 20 -> 15, the
    O(1/r^3) term still visible); without them the 1PN part of the rate is missed, an O(1/r) difference that only
    doubles (measured 2.2). The run stops at r_stop and reports it."""
    from scipy import integrate as si
    nu = 0.25
    d = {}
    for orders in ((1, 2, 2.5, 3.5), (1, 2, 2.5)):
        for r0 in (40.0, 20.0):
            r1 = 0.75 * r0
            out = P.integrate(P.circular_state(r0, nu, orders), 1e12, nu, orders=orders, r_stop=r1, n_out=10)
            assert out["status"] == "r_stop"
            assert np.linalg.norm(out["end"]["x"]) == pytest.approx(r1, rel=1e-9)
            t_ref = si.quad(lambda r: 1.0 / P.circular_inspiral_rate(r, nu, 3.5 in orders), r0, r1, epsrel=1e-12)[0]
            d[orders, r0] = out["end"]["t"] / t_ref - 1.0
    full, part = (1, 2, 2.5, 3.5), (1, 2, 2.5)
    assert d[full, 20.0] / d[full, 40.0] > 3.0
    assert 1.5 < d[part, 20.0] / d[part, 40.0] < 3.0
    assert abs(d[full, 40.0]) < 0.2 * abs(d[part, 40.0])


def test_body_positions_cancel_the_1pn_mass_dipole():
    """Body positions (Blanchet 2014 Eq. (216) with P to 1PN) against the 1PN centre-of-mass condition
    sum_A m_A (1 + v_A^2/2 - m_B/(2r)) y_A = 0: the residual (relative to m r) is O(c^-4), slope 2 in eps = m/r;
    the Newtonian positions leave an O(c^-2) residual (slope 1). Body velocities by a complex step along the
    motion."""
    nu = 0.16  # X1 = 0.8, X2 = 0.2
    X1, X2 = 0.8, 0.2

    def resid(eps, order):
        x = np.array([1.0 / eps, 0.0, 0.0])
        v = math.sqrt(eps) * np.array([0.3, 1.1, 0.0])
        a = P.acceleration(x, v, nu, (1, 2))
        y1, y2 = P.body_positions(x, v, nu, order)
        v1 = P.directional(lambda X, V: P.body_positions(X, V, nu, order)[0], x, v, v, a)
        v2 = P.directional(lambda X, V: P.body_positions(X, V, nu, order)[1], x, v, v, a)
        r = 1.0 / eps
        d = X1 * (1 + 0.5 * v1 @ v1 - 0.5 * X2 / r) * y1 + X2 * (1 + 0.5 * v2 @ v2 - 0.5 * X1 / r) * y2
        return np.linalg.norm(d) / r

    for order, p in ((1, 2.0), (0, 1.0)):
        for s in _slope(lambda e: resid(e, order), [4e-3, 2e-3, 1e-3]):
            assert abs(s - p) < 0.05
    y1, y2 = P.body_positions([10.0, 0, 0], [0, 0.3, 0], nu)
    assert np.allclose(y1 - y2, [10.0, 0, 0], rtol=0, atol=1e-14)


# --- review B5 (2026-10-29): initial data, coefficients, failure modes ------------------------------------------

EPS_GRID = [1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3, 7e-3, 1e-2, 1.5e-2, 2e-2, 3e-2, 5e-2]
J_GRID = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]


@pytest.mark.parametrize("nu", [0.25, 0.1, 0.01])
def test_state_from_invariants_over_the_review_grid(nu):
    """Review B5, E1: on the reviewer's grid (12 eps x 13 j) every cell is either a periapsis state whose own eps, j
    equal the requested ones to 1e-12 (measured <= 3.4e-14), with rdot = 0 and a positive radial acceleration of the
    conservative equations, or a refusal (NoOrbit) with reason "plunge" or "pn_breakdown" (the earlier Newton
    iteration returned r_p ~ 1e36 silently on 9 cells, an apoapsis on 20, false refusals on 31). Measured: 131, 131,
    133 states and 25, 25, 23 refusals for nu = 0.25, 0.1, 0.01; eps = 0.01, j = 0.5 (earlier r_p = 3.3e36) now
    gives r_p = 25.84 (Newtonian estimate (1 - e)/eps = 29.3)."""
    n_ok = 0
    for eps in EPS_GRID:
        for j in J_GRID:
            try:
                st = P.state_from_invariants(eps, j, nu)
            except P.NoOrbit as err:
                assert err.reason in ("plunge", "pn_breakdown"), (eps, j, err.reason, str(err))
                continue
            n_ok += 1
            gi = P.gauge_invariants(st["x"], st["v"], nu)
            assert abs(gi["eps"] / eps - 1) < 1e-12 and abs(gi["j"] / j - 1) < 1e-12, (eps, j, gi)
            assert st["x"] @ st["v"] == 0.0
            a = P.acceleration(st["x"], st["v"], nu, (1, 2))
            assert st["v"] @ st["v"] + st["x"] @ a > 0.0
    assert n_ok >= 130
    st = P.state_from_invariants(0.01, 0.5, nu)
    assert st["x"][0] == pytest.approx({0.25: 25.84, 0.1: 25.75, 0.01: 25.71}[nu], abs=0.01)


def test_state_from_invariants_refusals_and_periapses_are_dynamical():
    """The refusals of the grid (nu = 1/4) checked by the equations of motion: from the apoapsis of the same E and J
    (``at="apoapsis"``) the conservative orbit falls below r = 6 with no periapsis (all 25: r_stop reached,
    no periapsis event). The accepted states (j = 0.1, 0.5, 1.0) are periapses of the equations of motion: over one
    radial period r never falls below r_p (relative 1e-12) and the first turning point is an apoapsis."""
    nu = 0.25
    for eps in EPS_GRID:
        for j in J_GRID:
            try:
                st = P.state_from_invariants(eps, j, nu)
            except P.NoOrbit:
                sa = P.state_from_invariants(eps, j, nu, at="apoapsis")
                ra = float(sa["x"][0])
                out = P.integrate(sa, 4 * math.pi * ra**1.5, nu, orders=(1, 2), r_stop=6.0, n_out=20)
                assert out["status"] == "r_stop" and out["t_peri"].size == 0, (eps, j)
                continue
            if j not in (0.1, 0.5, 1.0):
                continue
            Pr = 2 * math.pi / P.mean_motion(eps, j, nu)
            out = P.integrate(st, Pr, nu, orders=(1, 2), n_out=400, rtol=1e-13)
            r = np.linalg.norm(out["x"], axis=1)
            assert r.min() >= st["x"][0] * (1 - 1e-12), (eps, j)
            assert out["t_apo"].size >= 1 and (out["t_peri"].size == 0 or out["t_apo"][0] < out["t_peri"][0])


def test_state_from_invariants_reaches_low_eccentricity_and_refuses_above_circular():
    """Review B5, S6: j runs up to j_circ(eps), the circular value of the energy (above 1: 1 + eps (9 + nu)/4 at 1PN
    from Blanchet Eq. (346e) with e_t = 0; the difference falls as eps^2, slope 2), so orbits of small eccentricity
    are made: j = j_circ (1 - 1e-6) gives an orbit with (r_a - r_p)/(r_a + r_p) ~ 1e-3; j = j_circ (1 + 1e-9) is
    refused as "above_circular" (eps <= 0.01: the E, J potential and the equations of motion agree on j_circ to
    1e-9). Invalid inputs are refused."""
    for nu in (0.25, 0.01):
        d = []
        for eps in (4e-3, 2e-3, 1e-3):
            jc = P.j_circular(eps, nu)
            d.append(abs(jc - (1 + eps * (9 + nu) / 4)))
            st = P.state_from_invariants(eps, jc * (1 - 1e-6), nu)
            tp = P.turning_points(eps, jc * (1 - 1e-6), nu)
            assert (tp["r_a"] - tp["r_p"]) / (tp["r_a"] + tp["r_p"]) < 2e-3
            assert st["x"][0] == pytest.approx(tp["r_p"], rel=1e-15)
            with pytest.raises(P.NoOrbit) as err:
                P.state_from_invariants(eps, jc * (1 + 1e-9), nu)
            assert err.value.reason == "above_circular"
        for k in range(2):
            assert abs(math.log2(d[k] / d[k + 1]) - 2.0) < 0.1
    for bad in ((0.0, 0.5), (-1e-3, 0.5), (1e-3, 0.0), (float("nan"), 0.5)):
        with pytest.raises(P.NoOrbit) as err:
            P.state_from_invariants(*bad, 0.25)
        assert err.value.reason == "invalid"
    pk = P.circular_binding_peak(0.25)
    assert 6.0 < pk["r"] < 9.0 and 0.08 < pk["eps"] < 0.1
    with pytest.raises(P.NoOrbit):
        P.j_circular(1.2 * pk["eps"], 0.25)


def test_circular_speed_is_exact_and_refuses_where_no_circular_orbit_exists():
    """Review B5, N1: v^2 r = 1 + A(r, 0, v^2) holds to rounding; a second route (fixed-point iteration, rate O(1/r))
    gives the same speed for r >= 6; where the 2PN circular sequence has no orbit (r = 2.5 at nu = 1/4) or for an
    invalid r, NoOrbit("no_circular") instead of the earlier silent NaN."""
    for nu in (0.25, 0.1, 0.01):
        for r in (6.0, 10.0, 30.0, 1e3, 1e6):
            for o in ((1,), (1, 2)):
                v = P.circular_speed(r, nu, o)
                A, _ = P.coefficients(r, 0.0, v * v, nu, o)
                assert v * v * r == pytest.approx(1 + float(A), rel=4e-16)
                w = 1.0 / r
                for _ in range(400):
                    w = (1 + float(P.coefficients(r, 0.0, w, nu, o)[0])) / r
                assert v == pytest.approx(math.sqrt(w), rel=1e-15)
    for r in (2.5, 0.0, -1.0, float("nan")):
        with pytest.raises(P.NoOrbit) as err:
            P.circular_speed(r, 0.25)
        assert err.value.reason == "no_circular"


def test_plunge_and_r_stop_are_reported():
    """Review B5, N2: a plunge without r_stop ends with a RuntimeError that names it (not scipy's step-size message);
    a start not above r_stop is refused; from the apoapsis of the same Newtonian orbit the run ends at r_stop."""
    st = P.periapsis_state(20.0, 0.9)  # r_p = 2: the PN equations break down
    with pytest.raises(RuntimeError, match="plunges"):
        P.integrate(st, 1e4, 0.25)
    with pytest.raises(ValueError, match="not above the stopping radius"):
        P.integrate(st, 1e4, 0.25, r_stop=4.0)
    apo = P.state(0.0, [38.0, 0, 0], [0, math.sqrt(0.1 / 38.0), 0])
    out = P.integrate(apo, 1e4, 0.25, r_stop=4.0)
    assert out["status"] == "r_stop" and np.linalg.norm(out["end"]["x"]) == pytest.approx(4.0, rel=1e-9)


def test_cartesian_route_warns_where_it_cannot_resolve_the_reaction():
    """Review B5, N12: for an orbit like PSR B1913+16 (a = 4.67e5 G m/c^2: the reaction changes it by ~1e-12 per
    period) the Cartesian route warns (it gave Pb_dot 96 % off); the elements route and a strong-field Cartesian run
    do not."""
    import warnings
    st = P.periapsis_state(4.67e5, 0.617)
    with pytest.warns(P.PrecisionWarning):
        P.step(st, 10.0, 0.25)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        P.step(st, 10.0, 0.25, method="elements")
        P.step(P.periapsis_state(100.0, 0.3), 10.0, 0.25)
        P.step(st, 10.0, 0.25, orders=(1, 2))


def _residual_eccentricity(st, nu, orbits=3):
    """Radial oscillation of an inspiral over three orbits: r(t) minus a quintic fit of the secular trend, half its
    peak-to-peak range over r0."""
    r0 = float(np.linalg.norm(st["x"]))
    T = orbits * 2 * math.pi * r0**1.5
    out = P.integrate(st, T, nu, n_out=6000, rtol=1e-12)
    r = np.linalg.norm(out["x"], axis=1)
    t = out["t"] / T
    c = np.polyfit(t, r, 5)
    return np.ptp(r - np.polyval(c, t)) / (2 * r0)


def test_quasi_circular_start_is_less_eccentric_than_a_circular_one():
    """Review B5, S1: the quasi-circular start (the engine's own adiabatic radial velocity) is less eccentric than a
    circular start and than one with the re-expanded Eq. (227a) at every radius; measured (nu = 1/4) quasi /
    circular = 1e-3 ... 0.15 for r0 = 40 ... 10 (Eq. (227a) at r0 = 10: 2.6e-3, more than circular, 1.9e-3); one
    eccentricity-reduction step lowers it further (r0 = 20: 1.5e-5 -> 9e-7)."""
    nu = 0.25
    for r0 in (20.0, 15.0, 12.0, 10.0):
        vt = P.circular_speed(r0, nu)
        e_circ = _residual_eccentricity(P.state(0, [r0, 0, 0], [0, vt, 0]), nu)
        e_227 = _residual_eccentricity(P.state(0, [r0, 0, 0], [P.circular_inspiral_rate(r0, nu), vt, 0]), nu)
        e_q = _residual_eccentricity(P.circular_state(r0, nu), nu)
        assert e_q < 0.25 * e_circ and e_q < 0.5 * e_227, (r0, e_q, e_circ, e_227)
    e1 = _residual_eccentricity(P.circular_state(20.0, nu, reduce_eccentricity=1), nu)
    assert e1 < 0.2 * _residual_eccentricity(P.circular_state(20.0, nu), nu)


def test_adiabatic_radial_velocity_agrees_with_eq_227a_in_weak_field():
    """The engine's adiabatic rate and Blanchet's Eq. (227a) are the same to 1PN: their ratio differs from 1 by
    O(1/r^2) (slope 2), which is the 2PN of the rate that neither has completely."""
    for nu in (0.25, 0.01):
        def res(eps):
            r = 1.0 / eps
            return abs(P.adiabatic_radial_velocity(r, nu) / P.circular_inspiral_rate(r, nu) - 1.0)
        for s in _slope(res, [4e-3, 2e-3, 1e-3]):
            assert abs(s - 2.0) < 0.1


def _b14_3p5(r, rd, v2, nu):
    """Blanchet 2014 Eq. (220a, b), the 1/c^7 terms, typed in that paper's grouping (powers of G m / r outside;
    the engine's grouping is Blanchet 2024's Eqs. (358e), (359e))."""
    g = 1.0 / r
    rd2 = rd * rd
    A = (g * rd * (366.0 / 35.0 * nu * v2**2 + 12.0 * nu**2 * v2**2 - 114.0 * v2 * nu * rd2 - 12.0 * nu**2 * v2 * rd2
                   + 112.0 * nu * rd2**2)
         + g**2 * rd * (692.0 / 35.0 * nu * v2 - 724.0 / 15.0 * v2 * nu**2 + 294.0 / 5.0 * nu * rd2
                        + 376.0 / 5.0 * nu**2 * rd2)
         + g**3 * rd * (3956.0 / 35.0 * nu + 184.0 / 5.0 * nu**2))
    B = (g * (-626.0 / 35.0 * nu * v2**2 - 12.0 / 5.0 * nu**2 * v2**2 + 678.0 / 5.0 * nu * v2 * rd2
              + 12.0 / 5.0 * nu**2 * v2 * rd2 - 120.0 * nu * rd2**2)
         + g**2 * (164.0 / 21.0 * nu * v2 + 148.0 / 5.0 * nu**2 * v2 - 82.0 / 3.0 * nu * rd2
                   - 848.0 / 15.0 * nu**2 * rd2)
         + g**3 * (-1060.0 / 21.0 * nu - 104.0 / 5.0 * nu**2))
    return A, B


def test_3p5pn_coefficients_agree_with_a_second_transcription():
    """Review B5, S2: every 3.5PN coefficient, against Blanchet 2014's grouping typed independently, at random states
    where all monomials are of comparable size (r ~ 2 ... 20, |rdot| ~ v): agreement to 1e-13 of the largest term.
    A change of any single coefficient by 1/100 of itself or more fails (negative controls in the notes)."""
    rng = np.random.default_rng(35)
    for _ in range(300):
        nu = rng.uniform(0.0, 0.25)
        r = rng.uniform(2.0, 20.0)
        v2 = rng.uniform(0.05, 0.5)
        rd = rng.uniform(-1.0, 1.0) * math.sqrt(v2)
        A, B = P.coefficients(r, rd, v2, nu, (3.5,))
        Ar, Br = _b14_3p5(r, rd, v2, nu)
        scale = (1.0 / r) * nu * (abs(rd) + 1.0) * 200.0 * max(v2, 1.0 / r) ** 2
        assert abs(A - Ar) < 1e-13 * scale and abs(B - Br) < 1e-13 * scale


def test_1pn_coefficient_of_the_circular_inspiral_rate_is_derived():
    """Review B5, S2: the 1PN coefficient of Eq. (227a), -1751/336 - 7 nu/4, derived in exact fractions from three
    other quoted results: E(x) (Blanchet 2014 Eq. (232), -3/4 - nu/12), the circular 1PN flux (Eqs. (358), (359b)
    at e = 0, -1247/336 - 35 nu/12) and gamma(x) (Eq. (231), 1 - nu/3): dx/dt = -F / (dE/dx) gives
    (64/5) nu x^5 [1 + (f1 - 2 e1) x] and r = 1/gamma then (-64/5) nu gamma^3 [1 + (f1 - 2 e1 - 3 g1) gamma]."""
    from fractions import Fraction as Fr
    for nu in (Fr(1, 4), Fr(1, 10), Fr(1, 100), Fr(0)):
        e1 = Fr(-3, 4) - nu / 12
        f1 = Fr(-1247, 336) - Fr(35, 12) * nu
        g1 = 1 - nu / 3
        c = f1 - 2 * e1 - 3 * g1
        assert c == Fr(-1751, 336) - Fr(7, 4) * nu
        nf = float(nu)
        if nf > 0:
            c_engine = P.circular_inspiral_rate(1.0, nf) / (-12.8 * nf) - 1.0  # r = 1: the bracket is 1 + c
            assert c_engine == pytest.approx(float(c), rel=1e-14)


def test_mean_motion_periastron_and_x_references_are_mutually_consistent():
    """Review B5, N6: the three transcribed gauge-invariant references, n(eps, j) and K(eps, j) (Blanchet 2014
    Eq. (348a, b)) and x(eps, j) (Eq. (350), now to 2PN), satisfy x = (K n)^(2/3) (Omega = K n, Eq. (349)) up to
    O(eps^3): slope 3. A change of 555 -> 556 in n (or of any 2PN coefficient) leaves an eps^2 residual (slope 2).
    And the engine's circular orbits: x = Omega^(2/3) measured against x(eps, j) of the circular state: slope 3."""
    for nu in (0.25, 0.1, 0.01):
        for j in (0.3, 0.6, 0.9, 1.0):
            def res(eps):
                return abs((P.periastron_K(eps, j, nu) * P.mean_motion(eps, j, nu)) ** (2.0 / 3.0)
                           / P.x_parameter(eps, j, nu) - 1.0)
            for s in _slope(res, [4e-3, 2e-3, 1e-3]):
                assert abs(s - 3.0) < 0.05

        def res_c(eps):
            r = 1.0 / eps
            v = P.circular_speed(r, nu, (1, 2))
            gi = P.circular_invariants(r, nu)
            return abs((v / r) ** (2.0 / 3.0) / P.x_parameter(gi["eps"], gi["j"], nu) - 1.0)
        for s in _slope(res_c, [4e-3, 2e-3, 1e-3]):
            assert abs(s - 3.0) < 0.1


def test_periapsis_state_is_not_a_pn_orbit_with_that_a_e():
    """Review B5, N5 (the numbers in ``periapsis_state``'s docstring): Newtonian periapsis data are far from a PN
    orbit with that a, e. nu = 1/4: e = 0.7 is unbound (eps < 0) at a = 81 and bound at a = 83; e = 0.3, a = 24 has
    2 a eps = 1.03 (Newton: 2) and e_t = 0.58; a = 600 still 2 a eps = 1.962."""
    nu = 0.25

    def gi(a, e):
        st = P.periapsis_state(a, e)
        return P.gauge_invariants(st["x"], st["v"], nu)
    assert gi(81.0, 0.7)["eps"] < 0.0 < gi(83.0, 0.7)["eps"]
    g = gi(24.0, 0.3)
    assert 2 * 24.0 * g["eps"] == pytest.approx(1.03, abs=0.01)
    assert P.time_eccentricity(g["eps"], g["j"], nu) == pytest.approx(0.58, abs=0.01)
    assert 2 * 600.0 * gi(600.0, 0.3)["eps"] == pytest.approx(1.962, abs=0.001)


def test_reference_series_satisfy_x_equals_kn_two_thirds_coefficient_by_coefficient():
    """Review B5, N6 (the negative control 11 nu^2 -> 12 nu^2 in n escaped the slope test: a change of 5e-4 eps^2
    under an eps^3 remainder of ~200 eps^3). n / eps^(3/2), K and x / eps are quadratics in eps, so their
    coefficients are read off exactly from three evaluations (eps = 1, 2, 3), and Eq. (349) x = (K n)^(2/3) must hold
    order by order: c1(x) = (2/3)(n1 + k1), c2(x) = (2/3)(n2 + k2) - (n1^2 + k1^2)/9 + (4/9) n1 k1. Agreement to
    1e-12 (rounding of the extraction); a change of any single coefficient of (348a, b) or (350) by 1/100 of itself
    fails."""
    def coeffs(f):
        y = np.array([f(1.0), f(2.0), f(3.0)])
        return np.linalg.solve(np.array([[1.0, 1, 1], [1, 2, 4], [1, 3, 9]]), y)  # c0 + c1 e + c2 e^2

    for nu in (0.25, 0.16, 0.1, 0.01, 0.0):
        for j in (0.2, 0.5, 0.9, 1.0, 1.05):
            n0, n1, n2 = coeffs(lambda e: P.mean_motion(e, j, nu) / e**1.5)
            k0, k1, k2 = coeffs(lambda e: P.periastron_K(e, j, nu))
            x0, x1, x2 = coeffs(lambda e: P.x_parameter(e, j, nu) / e)
            assert n0 == pytest.approx(1.0, abs=1e-12) and k0 == pytest.approx(1.0, abs=1e-12)
            assert x0 == pytest.approx(1.0, abs=1e-12)
            assert x1 == pytest.approx(2.0 / 3.0 * (n1 + k1), abs=1e-12)
            c2 = 2.0 / 3.0 * (n2 + k2) - (n1 * n1 + k1 * k1) / 9.0 + 4.0 / 9.0 * n1 * k1
            assert x2 == pytest.approx(c2, abs=1e-11 * max(1.0, abs(c2)))


def test_the_truncated_reaction_stops_being_an_ordered_series_close_in():
    """Review B6-gravity G1 (moved here from p01): on circular states the work of the 2.5PN + 3.5PN reaction against the
    Newtonian flux, D/F_N, follows the 1PN flux 1 + c1 x (Blanchet 2014 Eq. 314, c1 = -1247/336 - 35 nu/12) far out,
    its remainder is of the next order (|D/F_N - 1 - c1 x| / x^2 bounded), and it changes sign inside r ~ 9.1 for every
    mass ratio (the orbit would gain energy); the radius where the remainder equals the 1PN correction is 10.59 for
    q = 1 and 13.01 for q = 0.05 (the module's validity)."""
    for q, r_lim in ((1.0, 10.59), (0.05, 13.01)):
        nu = q / (1 + q) ** 2
        assert P.reaction_validity_radius(nu) == pytest.approx(r_lim, abs=0.01)
        d, x = P.reaction_on_circle(9.0, nu)
        assert d < 0  # gains energy inside the cancellation radius
        d, x = P.reaction_on_circle(9.3, nu)
        assert d > 0
        for r in (40.0, 80.0):
            d, x = P.reaction_on_circle(r, nu)
            assert abs(d - (1 + P.flux_c1(nu) * x)) < 60 * x * x
