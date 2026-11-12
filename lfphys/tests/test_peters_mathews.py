# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Secular evolution by gravitational radiation (lfphys.theories.approx.peters_mathews) and the binary pulsar
PSR B1913+16 (Weisberg & Huang 2016, values in lfphys.core.data):

* the quoted forms against each other (Blanchet 2014 Eqs. (10)-(13) against Peters' a-forms);
* the secular track: a(e) conserved along the integrated equations; the time to coalescence by Peters' integral
  against the integrated equations, the e0 = 0 closed form, and an Arb enclosure;
* the post-Keplerian parameters: the Einstein delay gamma against a direct integration of the pulsar's clock;
* PSR B1913+16: the masses from <omega_dot> and gamma, the GR orbital decay against the published value, the
  observed / GR ratio, the inclination from Kepler's law; and the decay through the post-Newtonian equations of
  motion of the engine (lfphys.core.gravity.pn_binary), integrated orbit by orbit.
"""

import math

import numpy as np
import pytest
from scipy import integrate

from lfphys.core import data as D
from lfphys.core.constants import C, GM_SUN
from lfphys.core.gravity import pn_binary as P
from lfphys.theories.approx import peters_mathews as PM

GM1, GM2 = 1.44 * GM_SUN, 1.39 * GM_SUN
DAY = 86400.0


def test_quoted_forms_agree():
    """Blanchet 2014 Eq. (11) (dP/dt) and Eq. (12) (de/dt in terms of P) against Peters' a-forms with Kepler's law;
    <dE/dt> from <da/dt> through E = -G m1 m2 / (2a) (Eq. (10a)); <dJ/dt> from <da/dt>, <de/dt> through
    J = m1 m2 sqrt(G a (1 - e^2) / M) (Eq. (10b))."""
    from lfphys.core.constants import G
    M = GM1 + GM2
    for a, e in ((2e9, 0.0), (2e9, 0.617134), (1e8, 0.3), (5e9, 0.9)):
        P_ = PM.orbital_period(M, a)
        assert PM.semi_major_axis(M, P_) == pytest.approx(a, rel=1e-14)
        assert PM.pb_dot(GM1, GM2, P_, e) == pytest.approx(1.5 * P_ / a * float(PM.da_dt(GM1, GM2, a, e)), rel=1e-13)
        de_B = (-608 * math.pi * e / (15 * C**5 * P_) * (2 * math.pi / P_) ** (5 / 3) * GM1 * GM2 * M ** (-1 / 3)
                * (1 + 121 / 304 * e * e) / (1 - e * e) ** 2.5)
        assert float(PM.de_dt(GM1, GM2, a, e)) == pytest.approx(de_B, rel=1e-13, abs=1e-300)
        m1m2 = GM1 * GM2 / G**2
        dE = GM1 * GM2 / G / (2 * a * a) * float(PM.da_dt(GM1, GM2, a, e))
        assert float(PM.energy_loss_rate(GM1, GM2, a, e)) == pytest.approx(dE, rel=1e-13)
        J = m1m2 * math.sqrt(G * a * (1 - e * e) / (M / G))
        dJ = J * (0.5 * float(PM.da_dt(GM1, GM2, a, e)) / a - e * float(PM.de_dt(GM1, GM2, a, e)) / (1 - e * e))
        assert float(PM.angular_momentum_loss_rate(GM1, GM2, a, e)) == pytest.approx(dJ, rel=1e-13)


def test_secular_track_keeps_a_of_e_and_reaches_coalescence():
    """Peters' equations integrated (step API) keep c0 = a (1 - e^2) e^(-12/19) (1 + 121 e^2/304)^(-870/2299)
    (Blanchet Eq. (13)) to the integrator's tolerance; the time to reach a small a plus the circular remainder
    a^4/(4 beta) equals Peters' integral."""
    a0, e0 = 2e9, 0.617134
    st = {"t": 0.0, "a": a0, "e": e0}
    c0 = PM.c0_of(a0, e0)
    T = PM.coalescence_time(GM1, GM2, a0, e0)
    t_chunk = T / 7
    for _ in range(6):
        st, status = PM.evolve(st, t_chunk, GM1, GM2)
        assert status == "running"
        assert PM.c0_of(st["a"], st["e"]) == pytest.approx(c0, rel=100 * 1e-12)  # 100 x the rtol of evolve
    st, status = PM.evolve(st, T, GM1, GM2, a_stop=1e-3 * a0)
    assert status == "a_stop" and st["a"] == pytest.approx(1e-3 * a0, rel=1e-8)
    rest = PM.coalescence_time(GM1, GM2, st["a"], st["e"])
    assert st["t"] + rest == pytest.approx(T, rel=1e-11)  # measured 8e-14
    # restart exactness of the step API
    s1, _ = PM.evolve({"t": 0.0, "a": a0, "e": e0}, 1e15, GM1, GM2)
    s2, _ = PM.evolve({"t": 0.0, "a": a0, "e": e0}, 1e15, GM1, GM2)
    assert s1 == s2


def test_coalescence_time_closed_form_limit_and_certified():
    beta = 12.8 * GM1 * GM2 * (GM1 + GM2) / C**5
    a0 = 1e9
    assert PM.coalescence_time(GM1, GM2, a0, 0.0) == pytest.approx(a0**4 / (4 * beta), rel=1e-15)
    # the e0 -> 0 limit of Peters' integral is the circular closed form, T(e0)/T(0) = 1 + k e0^2 + O(e0^4) with
    # k = -4 - (3480/2299)(121/304) + (48/86)((1181/2299)(121/304) + 3/2) from expanding c0^4 and the integrand
    k2 = -4 - 3480 / 2299 * 121 / 304 + 48 / 86 * (1181 / 2299 * 121 / 304 + 1.5)
    for e0 in (1e-2, 1e-3):
        ratio = PM.coalescence_time(GM1, GM2, a0, e0) / (a0**4 / (4 * beta))
        assert ratio - 1 - k2 * e0 * e0 == pytest.approx(0, abs=10 * e0**4 + 1e-13)
    # circular: the integrated equations reach a = a0/100 at T (1 - 1e-8)
    st, status = PM.evolve({"t": 0.0, "a": a0, "e": 0.0}, 2 * a0**4 / (4 * beta), GM1, GM2, a_stop=0.01 * a0)
    assert st["t"] == pytest.approx(a0**4 / (4 * beta) * (1 - 1e-8), rel=1e-9)
    # Arb: the integral of Peters' formula for PSR B1913+16-like (a0, e0), rigorously
    flint = pytest.importorskip("flint")
    flint.ctx.prec = 128
    arb, acb = flint.arb, flint.acb
    e0 = 0.617134
    k = arb(19) / 48

    def f(s, d):
        e = acb(e0) * s ** acb(k)
        g = 1 + acb(121) / 304 * e * e
        return g ** (acb(1181) / 2299) * (1 - e * e) ** (acb(-3) / 2)
    I = acb.integral(f, arb("1e-60"), 1).real  # the integrand is bounded at 0; the omitted piece is below 1e-59
    c0 = PM.c0_of(a0, e0)
    Tc = arb(12) / 19 * arb(c0) ** 4 / arb(beta) * I * arb(e0) ** (arb(48) / 19) * k
    T = PM.coalescence_time(GM1, GM2, a0, e0)
    assert abs(T - float(Tc.mid())) <= 1e-13 * T + float(Tc.rad())


def test_einstein_delay_from_the_pulsar_clock():
    """gamma (Weisberg & Huang Eq. (17)) against the pulsar's proper time integrated along a Kepler orbit:
    t - tau = int (v1^2/2 + G m2 / r) dt / c^2 with v1 = (m2/M) v (1PN clock rate), fitted to
    alpha (u - e sin u) + gamma sin u (u the eccentric anomaly): the periodic coefficient is gamma."""
    M = GM1 + GM2
    for pb, e in ((0.323 * DAY, 0.617), (2.0 * DAY, 0.2), (10.0 * DAY, 0.9)):
        a = PM.semi_major_axis(M, pb)
        n = 2 * math.pi / pb

        def rate_du(u):  # (d(t - tau)/dt) * dt/du
            r = a * (1 - e * math.cos(u))
            v2 = M * (2 / r - 1 / a)
            return ((GM2 / M) ** 2 * v2 / 2 + GM2 / r) / C**2 * r / (n * a)
        us = np.linspace(0, 2 * math.pi, 41)[1:]
        dt = np.array([integrate.quad(rate_du, 0, u, epsabs=0, epsrel=1e-13)[0] for u in us])
        B = np.column_stack([us - e * np.sin(us), np.sin(us)])
        coef, *_ = np.linalg.lstsq(B, dt, rcond=None)
        assert np.max(np.abs(B @ coef - dt)) < 1e-12 * np.max(np.abs(dt))
        assert coef[1] == pytest.approx(P.einstein_gamma(GM1, GM2, pb, e), rel=1e-12)  # quad epsrel 1e-13
    # review B5, N10: gamma lives in the core (the engine's only form of it); peters_mathews uses that function
    assert PM.einstein_gamma is P.einstein_gamma


# --- PSR B1913+16 ------------------------------------------------------------------------------------------------

T_SUN = D.PULSAR_T_SUN_S
GMS = T_SUN * C**3  # G Msun as used by the timing (T_sun c^3)
PB = D.PSR_B1913_PB_DAYS[0] * DAY
ECC = D.PSR_B1913_ECC[0]


def _omdot(year_days=D.PULSAR_YEAR_DAYS, deg=D.PSR_B1913_PERIASTRON_DEG_PER_YR[0]):
    return math.radians(deg) / (year_days * DAY)


def _masses(gamma=D.PSR_B1913_GAMMA_S[0], **kw):
    return PM.masses_from_pk(_omdot(**kw), gamma, PB, ECC)


def test_psr_b1913_t_sun_is_the_engines_solar_mass():
    """The paper's T_sun = G M_sun / c^3 = 4.925490947 us against the IAU 2015 nominal G M_sun of the engine."""
    assert GM_SUN / C**3 == pytest.approx(T_SUN, rel=1e-9)


def test_psr_b1913_masses_from_omega_dot_and_gamma():
    """Weisberg & Huang Sec. 4.3: m1 = 1.438 +- 0.001, m2 = 1.390 +- 0.001 Msun from <omega_dot> and gamma through
    their Eqs. (16), (17): reproduced to the printed digits."""
    g1, g2 = _masses()
    for g, (m, s) in ((g1, D.PSR_B1913_M_PULSAR_MSUN), (g2, D.PSR_B1913_M_COMPANION_MSUN)):
        assert abs(g / GMS - m) <= 0.0005  # the half-unit of the last printed digit
    # the two post-Keplerian formulas give back the inputs
    assert PM.omega_dot(g1, g2, PB, ECC) == pytest.approx(_omdot(), rel=1e-13)
    assert PM.einstein_gamma(g1, g2, PB, ECC) == pytest.approx(D.PSR_B1913_GAMMA_S[0], rel=1e-13)


def test_psr_b1913_orbital_decay_gr_prediction():
    """Pb_dot^GR from the masses and Eq. (22) (Peters-Mathews) against the paper's -2.40263(5)e-12. Our inputs are
    the printed values; the change of the result over their rounding intervals (half a unit of the last digit,
    every corner) is added to the published uncertainty as the tolerance."""
    def pbdot(om_deg, gam, pb_d, e):
        g1, g2 = PM.masses_from_pk(math.radians(om_deg) / (D.PULSAR_YEAR_DAYS * DAY), gam, pb_d * DAY, e)
        return PM.pb_dot(g1, g2, pb_d * DAY, e)
    base = (D.PSR_B1913_PERIASTRON_DEG_PER_YR[0], D.PSR_B1913_GAMMA_S[0], D.PSR_B1913_PB_DAYS[0], D.PSR_B1913_ECC[0])
    half = (0.5e-6, 0.5e-6, 0.5e-12, 0.5e-7)
    val = pbdot(*base)
    spread = 0.0
    for k in range(4):
        for s in (-1, 1):
            arg = list(base)
            arg[k] += s * half[k]
            spread = max(spread, abs(pbdot(*arg) - val))
    ref, sig = D.PSR_B1913_PBDOT_GR
    assert abs(val - ref) <= sig + 4 * spread + 0.5e-17
    # the tropical year in deg/yr would move the result by more than the published uncertainty
    g1, g2 = _masses(year_days=365.2422)
    assert abs(PM.pb_dot(g1, g2, PB, ECC) - ref) > 2 * sig


def test_psr_b1913_observed_over_gr_ratio():
    """Weisberg & Huang Eq. (23): Pb_dot^intr / Pb_dot^GR = 0.9983 +- 0.0016 with Pb_dot^intr = Pb_dot^obs -
    Pb_dot^gal (Eq. (15)). From the printed Pb_dot^obs and Pb_dot^gal (rounding intervals) and our GR value the ratio
    interval contains 0.9983, and general relativity passes: |ratio - 1| within 2 sigma."""
    g1, g2 = _masses()
    gr = PM.pb_dot(g1, g2, PB, ECC)
    obs, gal = D.PSR_B1913_PBDOT_OBS[0], D.PSR_B1913_PBDOT_GAL[0]
    intr = obs - gal
    assert intr == pytest.approx(D.PSR_B1913_PBDOT_INTR[0], abs=0.5e-15)
    lo = (intr - 1.0e-15) / gr  # obs and gal each rounded to 1e-15: the difference within +-1e-15
    hi = (intr + 1.0e-15) / gr
    ratio, sig = D.PSR_B1913_PBDOT_RATIO
    assert min(lo, hi) - 0.5e-4 <= ratio <= max(lo, hi) + 0.5e-4
    assert abs(intr / gr - 1.0) < 2 * sig


def test_psr_b1913_inclination_from_kepler():
    """sin i = 0.7327 +- 0.0004 (Weisberg & Huang Sec. 4.3) from x = a1 sin i / c, a1 = a m2 / M and Kepler's law with
    the masses from <omega_dot> and gamma (the uncertainty of sin i comes from that of gamma)."""
    g1, g2 = _masses()
    a = PM.semi_major_axis(g1 + g2, PB)
    sini = D.PSR_B1913_X_LIGHT_S[0] * C / (a * g2 / (g1 + g2))
    assert abs(sini - D.PSR_B1913_SIN_I[0]) <= D.PSR_B1913_SIN_I[1]


def _b1913_scaled():
    g1, g2 = _masses()
    M = g1 + g2
    nu = g1 * g2 / M**2
    U = P.mass_units(M)
    a = PM.semi_major_axis(M, PB) / U["length"]
    return g1, g2, nu, a, U


def test_psr_b1913_decay_through_the_equations_of_motion():
    """The engine's PN equations of motion integrated over five orbits of PSR B1913+16 by variation of constants
    (the reaction changes the orbit by 1.6e-12 per period).
    (a) 2.5PN reaction alone: the decay of the osculating semi-major axis gives Pb_dot = (3/2) Delta a / a equal to
        Peters-Mathews: measured 5.9e-12, bound 1e-10 (the first neglected order, eps_rr = 1.6e-12, plus the
        elements route's error at rtol 1e-12).
    (b) all terms (1PN, 2PN, 2.5PN, 3.5PN): the loss of E_2PN per radial period, integrated (the Newtonian part from
        the cancellation-free change of the osculating a, the PN part from ``energy(..., newtonian=False)``), against
        the first-order average of the reaction over the 2PN orbit (``averaged_dissipation``), two routes to the same
        quantity: measured 1.2e-6 at rtol 1e-13 (7.1e-6 at 1e-12, 3.0e-7 at 3e-14: the elements route's error,
        whose variables carry the 1PN oscillation of 1e-6 of the orbit); bound 5e-6. It replaces the earlier bound
        100 GM/(c^2 a) on |Pb_dot / Peters - 1| (review B5, N7), which was not derived.
    (c) the PN corrections to the Peters-Mathews decay (measured -2.8e-5 through the osculating a) are below 0.1 of
        the measurement's 1.6e-3: they do not affect the GR test."""
    g1, g2, nu, a, U = _b1913_scaled()
    ref = PM.pb_dot(g1, g2, PB, ECC)
    out = P.integrate(P.periapsis_state(a, ECC), 5.3 * 2 * math.pi * a**1.5, nu, orders=(2.5,), method="elements",
                      n_out=3)
    da = np.array([el["da"] for el in out["elements"]])
    assert len(da) >= 5
    slope = np.polyfit(np.arange(len(da)), da, 1)[0]
    assert abs(1.5 * slope / out["elements"][0]["a0"] / ref - 1.0) < 1e-10
    out = P.integrate(P.periapsis_state(a, ECC), 5.3 * 2 * math.pi * a**1.5, nu, method="elements", n_out=3,
                      rtol=1e-13)
    els, tp = out["elements"], out["t_peri"]
    dEN = np.array([el["da"] / (2 * el["a0"] * (el["a0"] + el["da"])) for el in els])  # E_N = -1/(2a)
    EPN = np.array([float(P.energy(*out["at"](t), nu, 2, newtonian=False)) for t in tp])
    per_orbit = np.polyfit(np.arange(len(tp)), dEN + EPN - EPN[0], 1)[0]
    s0 = P.state(tp[0], *out["at"](tp[0]))
    res = P.averaged_dissipation(s0, nu, conservative=(1, 2), dissipative=(2.5, 3.5), order=2, rtol=1e-13)
    assert abs(per_orbit / (res["dE"] * res["P_r"]) - 1.0) < 5e-6
    pbd = 1.5 * np.polyfit(np.arange(len(els)), [el["da"] for el in els], 1)[0] / els[0]["a0"]
    assert abs(pbd / ref - 1.0) < 0.1 * D.PSR_B1913_PBDOT_RATIO[1]


def test_psr_b1913_averaged_reaction_at_1pn():
    """For the orbit of PSR B1913+16 the engine's reaction (2.5PN + 3.5PN) averaged over the 2PN orbit against the
    1PN flux of Blanchet 2014 Eqs. (358)-(359) with x and e_t from eps, j at 1PN (Eqs. (350), (346e)): measured
    ratio - 1 - x I1/I0 = -2.40e-10 = -52 x^2 (review B5, N3: an O(x^2) remainder with a large coefficient; the
    docstring said ~1e-11 before), against the 1PN term x I1/I0 = 2.41e-6; bound 1e-3 x I1/I0 = 2.4e-9 (10 x the
    measurement): a wrong 3.5PN term changing the 1PN flux by more than 0.1 % fails."""
    g1, g2, nu, a, U = _b1913_scaled()
    st = P.periapsis_state(a, ECC)
    res = P.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=(2.5, 3.5), order=2, rtol=1e-13)
    gi = P.gauge_invariants(st["x"], st["v"], nu)
    x = P.x_parameter(gi["eps"], gi["j"], nu, order=1)
    et = P.time_eccentricity(gi["eps"], gi["j"], nu)
    I0 = (1 + 73 / 24 * et**2 + 37 / 96 * et**4) / (1 - et * et) ** 3.5
    e2 = et * et
    I1 = (-1247 / 336 - 35 / 12 * nu + e2 * (10475 / 672 - 1081 / 36 * nu) + e2**2 * (10043 / 384 - 311 / 12 * nu)
          + e2**3 * (2179 / 1792 - 851 / 576 * nu)) / (1 - e2) ** 4.5
    ratio = res["dE"] / (-6.4 * nu * x**5 * I0)
    assert abs(ratio - 1 - x * I1 / I0) < 1e-3 * abs(x * I1 / I0)


def test_evolve_stops_where_orbit_averaging_fails():
    """Review B5, N11: by default ``evolve`` stops when eps_rr = |da/dt| P_b / a reaches 0.05 (status
    "averaging_limit"), not at 1e-6 of the start. Circular orbit: eps_rr = (64/5) nu (GM/(c^2 a))^(5/2) 2 pi, so the
    stop is at G M / (c^2 a) = (0.05 / (128 pi nu / 5))^(2/5) (= 0.0908, a = 11.0 G M/c^2 here). An eccentric start
    (e0 = 0.9) circularizes first and stops at the same a; along the way c0 of a(e) is kept (7.7e-10) and t + T_rest
    equals Peters' T (2.4e-12). A start beyond the limit (a = 1e7 m, e = 0.999: eps_rr = 890) returns at once.
    eps_rr_max=None restores the old range (a down to 1e-6 a0, i.e. 2 km < G M/c^2 = 4.2 km)."""
    M = GM1 + GM2
    nu = GM1 * GM2 / M**2
    m = M / C**2
    for e0 in (0.0, 0.9):
        T = PM.coalescence_time(GM1, GM2, 2e9, e0)
        st, status = PM.evolve({"t": 0.0, "a": 2e9, "e": e0}, 1e30, GM1, GM2)
        assert status == "averaging_limit"
        assert float(PM.averaging_parameter(GM1, GM2, st["a"], st["e"])) == pytest.approx(0.05, rel=1e-6)
        assert m / st["a"] == pytest.approx((0.05 / (128 * math.pi * nu / 5)) ** 0.4, rel=1e-6)
        assert (st["t"] + PM.coalescence_time(GM1, GM2, st["a"], st["e"])) / T - 1 == pytest.approx(0, abs=1e-11)
    st, status = PM.evolve({"t": 0.0, "a": 2e9, "e": 0.0}, 1e30, GM1, GM2, eps_rr_max=None)
    assert status == "a_stop" and st["a"] == pytest.approx(2e3, rel=1e-12)
    st, status = PM.evolve({"t": 0.0, "a": 1e7, "e": 0.999}, 1.0, GM1, GM2)
    assert status == "averaging_limit" and st["t"] == 0.0
