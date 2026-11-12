# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Quadrupole waveforms and fluxes (lfphys.core.gravity.gw_quadrupole) against closed forms and second routes:
the circular-orbit polarizations of Blanchet 2014 Eqs. (320), (322a), (323a); the derivatives of the quadrupole
against finite differences of exact Kepler positions; the flux of the waveforms over the sphere against the Einstein
luminosity (the energy balance of the waves); orbit averages against Peters & Mathews, one of them certified in Arb;
and the energy lost by an integrated orbit with radiation reaction against the energy the waves carry off."""

import math

import numpy as np
import pytest

from lfphys.core.gravity import gw_quadrupole as W
from lfphys.core.gravity import pn_binary as P
from lfphys.theories.approx import peters_mathews as PM


def _kepler(a, e, u):
    """Exact Kepler orbit (m = 1) at eccentric anomalies u: x, v (counter-clockwise, periapsis on +x)."""
    u = np.asarray(u, float)
    r = a * (1 - e * np.cos(u))
    x = np.stack([a * (np.cos(u) - e), a * math.sqrt(1 - e * e) * np.sin(u), 0 * u], axis=-1)
    v = np.stack([-a * np.sin(u), a * math.sqrt(1 - e * e) * np.cos(u), 0 * u], axis=-1) * (a**-0.5 / r)[..., None]
    return x, v


def _ecc_anomaly(Mmean, e):
    E = np.array(Mmean, float) + e * np.sin(Mmean)
    for _ in range(50):
        E = E - (E - e * np.sin(E) - Mmean) / (1 - e * np.cos(E))
    return E


@pytest.mark.parametrize("iota", [0.0, 0.4, math.pi / 2, 2.5])
@pytest.mark.parametrize("Phi", [0.0, 1.1, -2.0])
def test_circular_orbit_matches_blanchet(iota, Phi):
    """R h+ = -(2 mu x)(1 + cos^2 i) cos 2 psi, R hx = -(2 mu x) 2 cos i sin 2 psi (m = 1, x = 1/a), psi the orbital
    phase from the ascending node (Blanchet 2014 Eqs. (320), (322a), (323a) at Newtonian order, without the memory
    term). Exact to rounding."""
    nu, a = 0.2, 30.0
    t = np.linspace(0, 400.0, 37)
    w = a**-1.5
    x = a * np.stack([np.cos(w * t), np.sin(w * t), 0 * t], axis=1)
    v = a * w * np.stack([-np.sin(w * t), np.cos(w * t), 0 * t], axis=1)
    hp, hx = W.binary_waveform(x, v, nu, iota, Phi)
    N, Pv, Qv = W.observer_triad(iota, Phi)
    zP = np.cross([0, 0, 1.0], Pv)
    psi = np.arctan2(x @ zP, x @ Pv)
    amp = 2 * nu / a
    assert np.allclose(hp, -amp * (1 + math.cos(iota) ** 2) * np.cos(2 * psi), rtol=0, atol=1e-14 * amp)
    assert np.allclose(hx, -amp * 2 * math.cos(iota) * np.sin(2 * psi), rtol=0, atol=1e-14 * amp)


def test_tt_tensor_and_polarizations():
    rng = np.random.default_rng(3)
    for _ in range(10):
        Q2 = rng.normal(size=(3, 3))
        Q2 = Q2 + Q2.T
        iota, Phi = rng.uniform(0, math.pi), rng.uniform(-math.pi, math.pi)
        N, Pv, Qv = W.observer_triad(iota, Phi)
        assert np.allclose([N @ Pv, N @ Qv, Pv @ Qv], 0, atol=1e-15)
        assert np.allclose(np.cross(N, Pv), Qv)
        h = W.h_tt(Q2, N)
        assert np.allclose(h @ N, 0, atol=1e-13) and abs(np.trace(h)) < 1e-13 and np.allclose(h, h.T)
        hp, hx = W.polarizations(Q2, Pv, Qv)
        assert hp == pytest.approx(0.5 * (Pv @ h @ Pv - Qv @ h @ Qv), abs=1e-13)
        assert hx == pytest.approx(0.5 * (Pv @ h @ Qv + Qv @ h @ Pv), abs=1e-13)
        # rotating the polarization basis by alpha mixes h+ and hx by 2 alpha (spin-2)
        al = 0.37
        P2, Q2v = math.cos(al) * Pv + math.sin(al) * Qv, -math.sin(al) * Pv + math.cos(al) * Qv
        hp2, hx2 = W.polarizations(Q2, P2, Q2v)
        assert hp2 == pytest.approx(hp * math.cos(2 * al) + hx * math.sin(2 * al), abs=1e-13)
        assert hx2 == pytest.approx(-hp * math.sin(2 * al) + hx * math.cos(2 * al), abs=1e-13)


def test_flux_of_the_waves_over_the_sphere_is_the_quadrupole_luminosity():
    """(1/16 pi) int (dh+/dt^2 + dhx/dt^2) R^2 dOmega = (1/5) dddQ:dddQ for any trace-free source (the flux density
    is a quartic polynomial in N, which the product rule integrates exactly from 3 x 5 nodes on)."""
    rng = np.random.default_rng(5)
    for _ in range(20):
        Q3 = rng.normal(size=(3, 3))
        Q3 = Q3 + Q3.T
        Q3 -= np.trace(Q3) / 3 * np.eye(3)
        L = W.luminosity(Q3)
        for nm, nphi in ((3, 5), (6, 12), (10, 21)):
            assert W.flux_over_sphere(Q3, nm, nphi) == pytest.approx(L, rel=1e-13)
        assert abs(W.flux_over_sphere(Q3, 2, 3) / L - 1) > 1e-6  # a rule below the degree is not exact
    # along an eccentric orbit, batched
    x, v = _kepler(20.0, 0.6, np.linspace(0, 2 * math.pi, 50))
    a, j = W.newtonian_kinematics(x, v)
    _, _, Q3 = W.quadrupole(x, v, a, j, 0.25)
    assert np.allclose(W.flux_over_sphere(Q3), W.luminosity(Q3), rtol=1e-13, atol=0)


def test_instantaneous_luminosity_of_a_newtonian_binary():
    """For Newtonian motion (1/5) dddQ:dddQ = (8/15)(mu^2 m^2 / r^4)(12 v^2 - 11 rdot^2) (Peters & Mathews 1963;
    derived in the notes of this item from d^3(x x)/dt^3 = -(2m/r^3)[2(x v + v x) - 3 (rdot/r) x x])."""
    rng = np.random.default_rng(11)
    for _ in range(30):
        x = rng.normal(size=3) * 10
        v = rng.normal(size=3) * 0.2
        mu = rng.uniform(0.01, 0.25)
        a, j = W.newtonian_kinematics(x, v)
        _, Q2, Q3 = W.quadrupole(x, v, a, j, mu)
        r = np.linalg.norm(x)
        rd = x @ v / r
        assert W.luminosity(Q3) == pytest.approx(8 / 15 * mu**2 / r**4 * (12 * v @ v - 11 * rd * rd), rel=1e-13)


def test_derivatives_against_finite_differences_of_exact_positions():
    """d^2Q/dt^2 and d^3Q/dt^3 from (x, v, a, j) against central differences of mu x x at exact Kepler positions
    (Kepler's equation solved to rounding), 8th-order stencils; the tolerance is the difference between steps h and
    h/2 (the truncation error estimate) plus rounding."""
    a, e, mu = 10.0, 0.7, 0.2
    n = a**-1.5

    def Qt(t):
        x, _ = _kepler(a, e, _ecc_anomaly(np.atleast_1d(n * t), e))
        return mu * (x[0][:, None] * x[0][None, :] - np.eye(3) * (x[0] @ x[0]) / 3)

    c2 = {1: 8 / 5, 2: -1 / 5, 3: 8 / 315, 4: -1 / 560}  # 2nd derivative, 8th order (centre -205/72)
    c3 = {1: -488 / 240, 2: 338 / 240, 3: -72 / 240, 4: 7 / 240}  # 3rd derivative, 6th order (odd)

    def fd(t, h):
        d2 = -205 / 72 * Qt(t) + sum(c * (Qt(t + k * h) + Qt(t - k * h)) for k, c in c2.items())
        d3 = sum(c * (Qt(t + k * h) - Qt(t - k * h)) for k, c in c3.items())
        return d2 / h**2, d3 / h**3

    for t in (0.0, 3.0, 40.0, 90.0):
        x, v = _kepler(a, e, _ecc_anomaly(np.atleast_1d(n * t), e))
        acc, jk = W.newtonian_kinematics(x[0], v[0])
        _, Q2, Q3 = W.quadrupole(x[0], v[0], acc, jk, mu)
        r = np.linalg.norm(x[0])
        h = 0.02 * r / np.linalg.norm(v[0])
        A2, A3 = fd(t, h)
        B2, B3 = fd(t, h / 2)
        for an, f1, f2 in ((Q2, A2, B2), (Q3, A3, B3)):
            tol = 2 * np.max(np.abs(f1 - f2)) + 1e-9 * np.max(np.abs(an))
            assert np.max(np.abs(an - (f2 - np.trace(f2) / 3 * np.eye(3)))) <= tol


def test_jerk_of_the_pn_trajectory_against_differences_of_its_acceleration():
    """pn_binary.jerk (complex step) against a central difference of the acceleration along the integrated PN
    trajectory (dense output), all orders, strong field."""
    nu = 0.2
    out = P.integrate(P.periapsis_state(20.0, 0.4), 300.0, nu, n_out=7, rtol=1e-13)
    for t in out["t"][1:-1]:
        x, v = out["at"](t)
        j = P.jerk(x, v, nu)
        h = 0.05
        ap = P.acceleration(*out["at"](t + h), nu)
        am = P.acceleration(*out["at"](t - h), nu)
        ap2 = P.acceleration(*out["at"](t + 2 * h), nu)
        am2 = P.acceleration(*out["at"](t - 2 * h), nu)
        fd = (8 * (ap - am) - (ap2 - am2)) / (12 * h)
        assert np.max(np.abs(j - fd)) < 1e-7 * np.max(np.abs(j))


def _orbit_average(fun, a, e, n=512):
    u = 2 * math.pi * np.arange(n) / n
    x, v = _kepler(a, e, u)
    w = 1 - e * np.cos(u)
    vals = fun(x, v)
    return np.sum(vals * (w if vals.ndim == 1 else w[:, None]), axis=0) / n


@pytest.mark.parametrize("e", [0.0, 0.2, 0.6171340, 0.85])
def test_orbit_averaged_fluxes_are_peters_mathews(e):
    """<dE/dt> and <dJ/dt> of the waves over a Kepler ellipse (trapezoidal rule in the eccentric anomaly, converging
    geometrically) against Peters' closed forms in scaled units (G = c = m = 1, G m1 G m2 = nu)."""
    nu, a = 0.21, 40.0
    X1 = 0.5 * (1 + math.sqrt(1 - 4 * nu))
    X2 = 1 - X1

    def flux(x, v):
        acc, j = W.newtonian_kinematics(x, v)
        _, Q2, Q3 = W.quadrupole(x, v, acc, j, nu)
        return np.column_stack([W.luminosity(Q3), W.angular_momentum_flux(Q2, Q3)[:, 2]])

    L, Jz = _orbit_average(flux, a, e, 512 if e < 0.7 else 4096)
    assert -L == pytest.approx(float(PM.energy_loss_rate(X1, X2, a, e, G=1.0, c=1.0)), rel=1e-12)
    assert -Jz == pytest.approx(float(PM.angular_momentum_loss_rate(X1, X2, a, e, G=1.0, c=1.0)), rel=1e-12)


def test_peters_mathews_enhancement_certified_for_psr_b1913():
    """f(e) of PSR B1913+16 by rigorous Arb integration of the instantaneous flux (8/15)(12 v^2 - 11 rdot^2)/r^4 over
    the Kepler ellipse (a = m = mu = 1, eccentric anomaly): the ball must contain (32/5) f(e) computed in float64."""
    flint = pytest.importorskip("flint")
    from lfphys.core import data as D
    e = D.PSR_B1913_ECC[0]
    flint.ctx.prec = 128
    arb, acb = flint.arb, flint.acb
    E = arb(e)

    def integrand(u, d):
        r = 1 - acb(E) * u.cos()
        v2 = 2 / r - 1
        rd = acb(E) * u.sin() / r
        return acb(8) / 15 * (12 * v2 - 11 * rd * rd) / r**4 * r
    I = acb.integral(integrand, 0, 2 * arb.pi()).real / (2 * arb.pi())
    ref = 6.4 * float(PM.enhancement(e))
    assert I.rad() < 1e-25 * float(I.mid())
    assert abs(float(I.mid()) - ref) <= 4e-16 * ref + float(I.rad())


def test_energy_lost_by_the_orbit_is_carried_by_the_waves():
    """Newton + 2.5PN, integrated: the Newtonian energy lost between two periapses against the time integral of the
    waves' flux over the sphere (computed from h+ and hx along the computed trajectory). The instantaneous balance
    differs by a total derivative (Blanchet 2014 Eq. (8a)), equal at the two periapses up to the change of the orbit
    in between: relative residual bounded by eps_rr = |Delta a / a| per orbit."""
    nu = 0.25
    a0, e0 = 60.0, 0.5
    out = P.integrate(P.periapsis_state(a0, e0), 4.5 * 2 * math.pi * a0**1.5, nu, orders=(2.5,), rtol=1e-13, n_out=5)
    tp = out["t_peri"]
    assert len(tp) >= 4
    t0, t1 = tp[0], tp[3]
    def radiated(panels):
        nodes, wts = np.polynomial.legendre.leggauss(16)
        edges = np.linspace(t0, t1, panels + 1)
        tt = np.concatenate([0.5 * (b - a) * nodes + 0.5 * (b + a) for a, b in zip(edges[:-1], edges[1:])])
        ww = np.concatenate([0.5 * (b - a) * wts for a, b in zip(edges[:-1], edges[1:])])
        XV = [out["at"](t) for t in tt]
        X = np.array([z[0] for z in XV])
        V = np.array([z[1] for z in XV])
        acc, j = W.newtonian_kinematics(X, V)
        _, _, Q3 = W.quadrupole(X, V, acc, j, nu)
        return float(np.sum(ww * W.flux_over_sphere(Q3)))

    R1, R2 = radiated(150), radiated(300)
    E = [nu * float(P.energy(*out["at"](t), nu, order=0)) for t in (t0, t1)]  # total energy = mu (E/mu), m = 1
    eps_rr = abs(float(PM.da_dt(0.5, 0.5, a0, e0, c=1.0)) * 2 * math.pi * a0**1.5 / a0)
    assert abs(R1 / R2 - 1) < 1e-3 * eps_rr  # the time quadrature is converged far below the bound
    assert abs((E[0] - E[1]) / R2 - 1) < eps_rr


def test_strain_units():
    """h = (G m / c^2) / R times R h/m: a 2.8 Msun binary at 100 Mpc, x = 0.01 has h ~ 4 nu x G m/(c^2 R)."""
    from lfphys.core.constants import GM_SUN
    gm = 2.8 * GM_SUN
    R = 100 * 3.0857e22
    s = W.strain_scale(gm, R)
    assert s == pytest.approx(gm / 299792458.0**2 / R, rel=1e-15)
    hp, hx = W.binary_waveform(np.array([100.0, 0, 0]), np.array([0, 0.1, 0]), 0.25, 0.0, 0.0)
    assert abs(hp) * s == pytest.approx(4 * 0.25 * 0.01 * s, rel=1e-12)


def test_binary_waveform_with_pn_kinematics_differs_at_order_x():
    """Review B5, N4: on 2PN circular orbits (nu = 1/4) the face-on amplitude relative to 4 nu x differs from 1 at
    O(x) both with the default (Newtonian) kinematics and with the PN acceleration and jerk (slope 1 in x), and the
    two differ from the 1PN waveform's factor 1 + x (-13/6 + nu/6) (Blanchet 2014 Eqs. (322c), (323c) at i = 0) at
    the same order: measured at r = 10: -2.6 %, -11.6 %, -20.0 % (stated in the docstring)."""
    nu = 0.25
    rows = []
    for r in (100.0, 200.0, 400.0, 10.0):
        v = P.circular_speed(r, nu, (1, 2))
        x, vv = np.array([r, 0, 0.0]), np.array([0, v, 0.0])
        X = (v / r) ** (2.0 / 3.0)
        hp, hx = W.binary_waveform(x, vv, nu, 0.0, 0.0)
        a, j = P.acceleration(x, vv, nu, (1, 2)), P.jerk(x, vv, nu, (1, 2))
        hp2, hx2 = W.binary_waveform(x, vv, nu, 0.0, 0.0, a=a, j=j)
        rows.append((X, math.hypot(hp, hx) / (4 * nu * X) - 1, math.hypot(hp2, hx2) / (4 * nu * X) - 1))
    for col in (1, 2):
        for k in range(2):
            s = math.log(rows[k][col] / rows[k + 1][col]) / math.log(rows[k][0] / rows[k + 1][0])
            assert abs(s - 1.0) < 0.05
    X, d0, d1 = rows[3]
    assert d0 == pytest.approx(-0.026, abs=5e-4) and d1 == pytest.approx(-0.116, abs=5e-4)
    assert abs(d1 - X * (-13 / 6 + nu / 6)) > 0.05  # PN kinematics are not the 1PN waveform
