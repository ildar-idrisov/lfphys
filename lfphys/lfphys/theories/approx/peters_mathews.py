# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Secular (orbit-averaged) evolution of a binary by gravitational radiation at leading order (Peters & Mathews
1963, Peters 1964), and the leading post-Keplerian parameters with which binary pulsars are weighed.

Quoted forms (Blanchet, Living Rev. Relativ. 17, 2 (2014), Eqs. (4), (9)-(13); Weisberg & Huang, ApJ 829, 55
(2016), Eqs. (16), (17), (22)); masses enter as G m (m^3 s^-2), M = m1 + m2; every function takes c (default the SI
value), so c = 1 with G m in units of a chosen mass gives the scaled units of ``lfphys.core.gravity.pn_binary``:

    <dP/dt> = -(192 pi / (5 c^5)) (2 pi G / P)^(5/3) m1 m2 M^(-1/3) f(e),
    f(e) = (1 + 73 e^2 / 24 + 37 e^4 / 96) / (1 - e^2)^(7/2)                            (Blanchet Eq. (11)),
    <de/dt> = -(608 pi e / (15 c^5 P)) (2 pi G / P)^(5/3) m1 m2 M^(-1/3) (1 + 121 e^2 / 304) / (1 - e^2)^(5/2)
                                                                                         (Blanchet Eq. (12)),
    e^2 (1 + 121 e^2 / 304)^(145/121) / (1 - e^2)^(19/6) = c0 P^(19/9)                     (Blanchet Eq. (13)).

With Kepler's law G M = Omega^2 a^3 and E = -G m1 m2 / (2a), J = m1 m2 sqrt(G a (1 - e^2) / M) (Blanchet Eq. (10))
these are equivalent to Peters' forms used here:

    <da/dt> = -(64/5) G^3 m1 m2 M / (c^5 a^3) f(e),
    <de/dt> = -(304/15) e G^3 m1 m2 M / (c^5 a^4) (1 + 121 e^2 / 304) / (1 - e^2)^(5/2),
    <dE/dt> = -(32/5) G^4 m1^2 m2^2 M / (c^5 a^5) f(e),
    <dJ/dt> = -(32/5) G^(7/2) m1^2 m2^2 M^(1/2) / (c^5 a^(7/2)) (1 + 7 e^2 / 8) / (1 - e^2)^2,
    a(e) = c0 e^(12/19) (1 + 121 e^2 / 304)^(870/2299) / (1 - e^2),

and the time to coalescence (a -> 0) from (a0, e0), with beta = (64/5) G^3 m1 m2 M / c^5 and c0 from a(e0) = a0:

    T = (12/19) (c0^4 / beta) int_0^e0 e^(29/19) (1 + 121 e^2 / 304)^(1181/2299) (1 - e^2)^(-3/2) de,
    T(e0 = 0) = a0^4 / (4 beta).

These are the orbit averages of the quadrupole fluxes over a Newtonian ellipse; the tests derive them again by
quadrature of ``lfphys.core.gravity.gw_quadrupole`` over Kepler orbits and compare with the averaged radiation
reaction of ``lfphys.core.gravity.pn_binary``.

Post-Keplerian parameters (general relativity, Damour & Deruelle 1986, as quoted by Weisberg & Huang 2016):
<omega_dot> = 3 (G M)^(2/3) c^-2 (P_b / 2 pi)^(-5/3) / (1 - e^2) (the 1PN periastron advance, Eq. (16); a simplified
form of the 2PN K(eps, j) the core has, hence here) and the Einstein delay gamma = e (P_b / 2 pi)^(1/3) G^(2/3) m2
(m1 + 2 m2) M^(-4/3) / c^2 (Eq. (17); the engine's only form of it, so it lives in the core,
``lfphys.core.gravity.pn_binary.einstein_gamma``, and is imported here); with the two measured the masses follow
(``masses_from_pk``).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate

from lfphys.i18n import T

from ...core.constants import C
from ...core.gravity import pn_binary as _pn

ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": T("Secular evolution of a binary by radiation (Peters–Mathews) and the post-Keplerian parameters"),
    "statement": T("The orbit-averaged losses of energy and angular momentum to quadrupole radiation, da/dt, de/dt, "
                   "the period derivative Ṗb with the factor f(e), the relation a(e), the time to merger (step by "
                   "step, stopping where averaging loses its meaning); the periastron advance ω̇ (1PN) and the masses "
                   "of the pulsar and its companion from ω̇ and the Einstein delay γ (γ from the core, "
                   "lfphys.core.gravity.pn_binary)."),
    "validity": T("leading order: relative corrections O(GM/(c²a)) to the flux (~10⁻⁵ for PSR B1913+16); averaging "
                  "over the orbit holds while the orbit changes little within a period (far from merger); ω̇ and γ at "
                  "leading order (the 2PN corrections to ω̇ ~ GM/(c²a(1−e²)))"),
    "basis": ["Peters & Mathews, Phys. Rev. 131, 435 (1963)", "Peters, Phys. Rev. 136, B1224 (1964)",
              "Blanchet, Living Rev. Relativ. 17, 2 (2014), Eqs. (4), (9)-(13)",
              "Weisberg & Huang, ApJ 829, 55 (2016), Eqs. (16), (17), (22), (23)"],
    "conflicts": [T("lfphys.core.gravity.pn_binary: the full equations of motion with the 2.5PN+3.5PN radiation "
                    "reaction give both the oscillations of the elements within an orbit and the 1PN correction to "
                    "the flux, which are absent here; near merger (the orbit changes within a period) averaging does "
                    "not apply"),
                  T("lfphys.core.gravity.gw_quadrupole: the instantaneous flux along the computed trajectory; here "
                    "its average over the Kepler ellipse")],
}

TWO_PI = 2.0 * math.pi


def enhancement(e):
    """Peters-Mathews f(e) = (1 + 73 e^2/24 + 37 e^4/96) / (1 - e^2)^(7/2) (f(0) = 1)."""
    e2 = np.asarray(e, float) ** 2
    return (1.0 + 73.0 / 24.0 * e2 + 37.0 / 96.0 * e2 * e2) / (1.0 - e2) ** 3.5


def semi_major_axis(gm_total: float, pb: float) -> float:
    """Kepler's third law: a = (G M (P_b / 2 pi)^2)^(1/3) (m)."""
    return (gm_total * (pb / TWO_PI) ** 2) ** (1.0 / 3.0)


def orbital_period(gm_total: float, a: float) -> float:
    return TWO_PI * math.sqrt(a**3 / gm_total)


def _beta(gm1: float, gm2: float, c: float = C) -> float:
    return 12.8 * gm1 * gm2 * (gm1 + gm2) / c**5


def energy_loss_rate(gm1: float, gm2: float, a, e, G: float | None = None, c: float = C):
    """<dE/dt> (W, negative): -(32/5) G^4 m1^2 m2^2 M / (c^5 a^5) f(e). Needs G to turn G m into energy: by default
    the CODATA value of ``lfphys.core.constants``."""
    if G is None:
        from ...core.constants import G as G_
        G = G_
    return -6.4 * (gm1 * gm2) ** 2 * (gm1 + gm2) / (G * c**5 * np.asarray(a, float) ** 5) * enhancement(e)


def angular_momentum_loss_rate(gm1: float, gm2: float, a, e, G: float | None = None, c: float = C):
    """<dJ/dt> (N m, negative): -(32/5) G^(7/2) m1^2 m2^2 M^(1/2) / (c^5 a^(7/2)) (1 + 7 e^2/8) / (1 - e^2)^2."""
    if G is None:
        from ...core.constants import G as G_
        G = G_
    e2 = np.asarray(e, float) ** 2
    return (-6.4 * (gm1 * gm2) ** 2 * math.sqrt(gm1 + gm2) / (G * c**5 * np.asarray(a, float) ** 3.5)
            * (1.0 + 0.875 * e2) / (1.0 - e2) ** 2)


def da_dt(gm1: float, gm2: float, a, e, c: float = C):
    """<da/dt> (m/s): -(64/5) G^3 m1 m2 M / (c^5 a^3) f(e)."""
    return -_beta(gm1, gm2, c) / np.asarray(a, float) ** 3 * enhancement(e)


def de_dt(gm1: float, gm2: float, a, e, c: float = C):
    """<de/dt> (1/s): -(304/15) e G^3 m1 m2 M / (c^5 a^4) (1 + 121 e^2/304) / (1 - e^2)^(5/2)."""
    e = np.asarray(e, float)
    e2 = e * e
    return (-19.0 / 12.0 * _beta(gm1, gm2, c) * e / np.asarray(a, float) ** 4
            * (1.0 + 121.0 / 304.0 * e2) / (1.0 - e2) ** 2.5)


def pb_dot(gm1: float, gm2: float, pb: float, e: float, c: float = C) -> float:
    """<dP_b/dt> (dimensionless): -(192 pi / (5 c^5)) (2 pi / P_b)^(5/3) G m1 G m2 (G M)^(-1/3) f(e)
    (Blanchet 2014 Eq. (11); Weisberg & Huang 2016 Eq. (22))."""
    return (-192.0 * math.pi / (5.0 * c**5) * (TWO_PI / pb) ** (5.0 / 3.0) * gm1 * gm2 * (gm1 + gm2) ** (-1.0 / 3.0)
            * float(enhancement(e)))


def _g(e):
    return 1.0 + 121.0 / 304.0 * e * e


def c0_of(a0: float, e0: float) -> float:
    """The constant of a(e) = c0 e^(12/19) (1 + 121 e^2/304)^(870/2299) / (1 - e^2) through (a0, e0), e0 > 0."""
    return a0 * (1.0 - e0 * e0) / (e0 ** (12.0 / 19.0) * _g(e0) ** (870.0 / 2299.0))


def a_of_e(a0: float, e0: float, e):
    """Semi-major axis on the secular track through (a0, e0) at eccentricity e (Peters 1964; Blanchet Eq. (13))."""
    e = np.asarray(e, float)
    return c0_of(a0, e0) * e ** (12.0 / 19.0) * _g(e) ** (870.0 / 2299.0) / (1.0 - e * e)


def coalescence_time(gm1: float, gm2: float, a0: float, e0: float, c: float = C) -> float:
    """Time (s) for the secular track from (a0, e0) to reach a = 0. e0 = 0: a0^4 / (4 beta); otherwise Peters'
    integral over e, evaluated with e = e0 s^(19/48) (which makes the integrand smooth at e = 0) by adaptive
    Gauss-Kronrod quadrature to 1e-13."""
    beta = _beta(gm1, gm2, c)
    if e0 == 0.0:
        return a0**4 / (4.0 * beta)
    if not 0.0 < e0 < 1.0:
        raise ValueError("coalescence_time: 0 <= e0 < 1")
    c0 = c0_of(a0, e0)
    # int_0^e0 e^(29/19) g^(1181/2299) (1 - e^2)^(-3/2) de with e = e0 s^k, k = 19/48: de = e0 k s^(k-1) ds and
    # e^(29/19) e0 k s^(k-1) = e0^(48/19) k s^((29/19) k + k - 1) = e0^(48/19) k s^0
    k = 19.0 / 48.0

    def f(s):
        e = e0 * s**k
        return _g(e) ** (1181.0 / 2299.0) * (1.0 - e * e) ** -1.5

    I = integrate.quad(f, 0.0, 1.0, epsabs=0.0, epsrel=1e-13, limit=200)[0] * e0 ** (48.0 / 19.0) * k
    return 12.0 / 19.0 * c0**4 / beta * I


def averaging_parameter(gm1: float, gm2: float, a, e, c: float = C):
    """eps_rr = |<da/dt>| P_b / a, the relative change of the orbit per period: the orbit average (and so everything
    in this module) needs eps_rr << 1 (the error of the per-orbit secular change is of second order in it; tests of
    the core's equations of motion measure 0.6 eps_rr^2)."""
    a = np.asarray(a, float)
    return np.abs(da_dt(gm1, gm2, a, e, c)) * TWO_PI * np.sqrt(a**3 / (gm1 + gm2)) / a


def evolve(st: dict, dt: float, gm1: float, gm2: float, a_stop: float = 0.0, rtol: float = 1e-12, c: float = C,
           eps_rr_max: float | None = 0.05):
    """Step API: advance the secular state {"t": s, "a": m, "e": -} by dt (s) along Peters' equations. Returns
    (new state, status): "running" (the time t + dt was reached); "averaging_limit" (the default stop: the averaging
    parameter eps_rr = |da/dt| P_b / a reached ``eps_rr_max`` = 0.05, beyond which an orbit average does not
    describe the motion; for e = 0 at G M/(c^2 a) = (0.05 / (128 pi nu / 5))^(2/5), a = 11.0 G M/c^2 for nu = 1/4;
    an eccentric start circularizes first (2.8 Msun, a0 = 2e9 m, e0 = 0.9: stop at a = 11.0 G M/c^2, e = 7e-7); a
    start already beyond it (a = 1e7 m, e = 0.999: eps_rr = 890) returns at once (review B5, N11); eps_rr_max=None
    goes on); "a_stop" (a
    reached ``a_stop`` > 0; with neither stop the floor is 1e-6 of the start). The equations are integrated with
    s = ln(a0/a) as the independent variable and t, e as dependent ones (DOP853): a is exact along the run, nothing
    becomes stiff near coalescence, and the stops are reached exactly in a; t is then as precise as its own rounding
    allows (near coalescence the remaining time T - t can be below ulp(t), ~8 s at t = 6e16 s)."""
    t0, a0, e0 = float(st["t"]), float(st["a"]), float(st["e"])
    if not dt > 0.0:
        return {"t": t0, "a": a0, "e": e0}, "running"
    if eps_rr_max is not None and float(averaging_parameter(gm1, gm2, a0, e0, c)) >= eps_rr_max:
        return {"t": t0, "a": a0, "e": e0}, "averaging_limit"
    floor = a_stop if a_stop > 0 else 1e-6 * a0
    if not floor < a0:
        return {"t": t0, "a": a0, "e": e0}, "a_stop"
    s_max = math.log(a0 / floor)
    t_end = t0 + dt

    def rhs(s_, y):  # y = (t, e); ds/dt = -(da/dt)/a
        a, e = a0 * math.exp(-s_), max(y[1], 0.0)
        dtds = -a / float(da_dt(gm1, gm2, a, e, c))
        return [dtds, float(de_dt(gm1, gm2, a, e, c)) * dtds]

    def reached(s_, y):
        return y[0] - t_end
    reached.terminal = True
    reached.direction = 1
    events = [reached]
    if eps_rr_max is not None:
        def averaging(s_, y):
            return math.log(float(averaging_parameter(gm1, gm2, a0 * math.exp(-s_), max(y[1], 0.0), c))
                            / eps_rr_max)
        averaging.terminal = True
        averaging.direction = 1
        events.append(averaging)
    t_scale = a0 / abs(float(da_dt(gm1, gm2, a0, e0, c)))  # the decay time of the start
    sol = integrate.solve_ivp(rhs, (0.0, s_max), [t0, e0], method="DOP853", rtol=rtol,
                              atol=[1e-3 * rtol * max(abs(t0), t_scale), 1e-15], events=events)
    if sol.status < 0:  # pragma: no cover - integrator failure
        raise RuntimeError(f"peters_mathews.evolve: {sol.message}")
    s_end, (t_e, e_e) = float(sol.t[-1]), sol.y[:, -1]
    if sol.t_events[0].size:
        status = "running"
        t_e = t_end  # the event is at t = t_end by construction
    elif eps_rr_max is not None and sol.t_events[1].size:
        status = "averaging_limit"
    else:
        status = "a_stop"
    a_e = floor if status == "a_stop" else a0 * math.exp(-s_end)
    return {"t": float(t_e), "a": a_e, "e": max(float(e_e), 0.0)}, status


# --- post-Keplerian parameters (Weisberg & Huang 2016, Eqs. (16), (17)) -------------------------------------------

def omega_dot(gm1: float, gm2: float, pb: float, e: float, c: float = C) -> float:
    """<omega_dot> (rad/s), the 1PN periastron advance: 3 (G M)^(2/3) c^-2 (P_b / 2 pi)^(-5/3) / (1 - e^2)."""
    return 3.0 * (gm1 + gm2) ** (2.0 / 3.0) / c**2 * (pb / TWO_PI) ** (-5.0 / 3.0) / (1.0 - e * e)


# the Einstein delay gamma lives in the core (the engine's only form of it, LAYERS.md §1): imported for the weighing
einstein_gamma = _pn.einstein_gamma


def masses_from_pk(omdot: float, gamma: float, pb: float, e: float, c: float = C) -> tuple[float, float]:
    """(G m1, G m2) (pulsar, companion) from <omega_dot> (rad/s) and gamma (s): G M from Eq. (16), then
    G m2 (G M + G m2) = gamma c^2 (G M)^(4/3) / (e (P_b / 2 pi)^(1/3)) from Eq. (17)."""
    gM = (omdot * c**2 * (pb / TWO_PI) ** (5.0 / 3.0) * (1.0 - e * e) / 3.0) ** 1.5
    k = gamma * c**2 * gM ** (4.0 / 3.0) / (e * (pb / TWO_PI) ** (1.0 / 3.0))
    gm2 = 2.0 * k / (gM + math.sqrt(gM * gM + 4.0 * k))  # the positive root of x^2 + gM x - k, cancellation-free
    return gM - gm2, gm2
