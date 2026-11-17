# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Engine M1, the projectile (design explore_2026-11-14 §4, §8): ``lfphys.core.mechanics`` and
``lfphys.theories.models.drag_quadratic`` against closed forms and independent second methods.

The stated error is 1e-9 relative; the measured deviations are printed (``pytest -s``) and recorded in the
docstrings."""

import math

import numpy as np
import pytest
from scipy import integrate

from lfphys.core.mechanics import (G_STANDARD, Body, Event, LinearDrag, air, fly, linear_drag_apex_time,
                                   linear_drag_landing_time, linear_drag_state, oseen_error, stokes_drag,
                                   vacuum_apex_height, vacuum_landing_time, vacuum_state)
from lfphys.theories.models import drag_quadratic as dq

G = G_STANDARD
TOL = 1e-9
BALL = Body(0.058, 0.067, "ball 67 mm")     # «like a tennis ball» (design §5.2)
STEEL = Body(0.0329, 0.020, "steel 20 mm")


def _v(speed, deg):
    return [speed * math.cos(math.radians(deg)), speed * math.sin(math.radians(deg))]


def _rel(a, b):
    return abs(a / b - 1.0)


# --- no drag ----------------------------------------------------------------------------------------------------------
VAC = [(0.0, 25.0, 45.0), (2.0, 10.0, 30.0), (5.0, 3.0, -20.0), (1.25, 2.0, 0.0), (10.0, 25.0, 85.0), (0.0, 5.0, 15.0)]


@pytest.mark.parametrize("h,v,th", VAC)
def test_vacuum_against_closed_forms(h, v, th):
    """Measured: T, L, H within 2e-15; the trajectory within 3e-15 of its scale; the energy balance 4e-15."""
    v0 = _v(v, th)
    f = fly(STEEL, [0.0, h], v0)
    T = vacuum_landing_time(h, v0[1])
    errs = {"T": _rel(f.flight_time, T), "L": _rel(f.range, v0[0] * T),
            "H": _rel(f.apex_height, vacuum_apex_height(h, v0[1]))}
    s = f.sample()
    r, vv = vacuum_state(s["t"], [0.0, h], v0)
    scale = max(h, v * v / G)
    errs["r"] = float(np.max(np.abs(s["r"] - r))) / scale
    errs["v"] = float(np.max(np.abs(s["v"] - vv))) / max(v, math.sqrt(2 * G * h))
    errs["E"] = f.energy_balance()
    print("vacuum", h, v, th, errs)
    assert max(errs.values()) < TOL
    if v0[1] > 0:
        assert f.apex["t"] == pytest.approx(v0[1] / G, rel=TOL)
    else:
        assert f.apex is None and f.apex_height == h


def test_vacuum_in_3d_equals_the_2d_flight():
    """The same launch turned about the vertical: x, z share the horizontal motion."""
    f2 = fly(STEEL, [0.0, 3.0], _v(12.0, 35.0))
    c, s = math.cos(0.7), math.sin(0.7)
    vh, vy = _v(12.0, 35.0)
    f3 = fly(STEEL, [1.0, -2.0, 3.0], [vh * c, vh * s, vy])
    assert f3.flight_time == pytest.approx(f2.flight_time, rel=1e-13)
    assert f3.range == pytest.approx(f2.range, rel=1e-12)
    assert f3.apex_height == pytest.approx(f2.apex_height, rel=1e-13)
    assert f3.results()["angle_land_deg"] == pytest.approx(f2.results()["angle_land_deg"], rel=1e-12)


# --- linear drag ------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("h,v,th,k", [(0.0, 10.0, 36.87, 0.3), (10.0, 10.0, 36.87, 0.3), (2.0, 10.0, 36.87, 0.3),
                                      (20.0, 4.0, -30.0, 1.5), (0.0, 30.0, 60.0, 0.05)])
def test_linear_drag_against_closed_forms(h, v, th, k):
    """x(t), y(t) and the Lambert-W landing time (design App. A: h 0, 10, 2 m). Measured: T 6e-15–1.5e-12, L up to
    4e-12, the positions up to 8e-12 of their scale, the velocities up to 6e-11, the apex time up to 8e-13; the energy
    balance 3e-12."""
    m = STEEL.mass
    drag = LinearDrag(k * m)
    v0 = _v(v, th)
    f = fly(STEEL, [0.0, h], v0, forces=[drag])
    T = linear_drag_landing_time(h, v0[1], k, G)
    s = f.sample(rate=240.0)
    r, vv = linear_drag_state(s["t"], [0.0, h], v0, k, G)
    errs = {"T": _rel(f.flight_time, T), "r": float(np.max(np.abs(s["r"] - r))) / max(h, v * v / G),
            "v": float(np.max(np.abs(s["v"] - vv))) / v, "E": f.energy_balance()}
    rT, _ = linear_drag_state(T, [0.0, h], v0, k, G)
    errs["L"] = _rel(f.range, rT[0])
    ta = linear_drag_apex_time(v0[1], k, G)
    if ta is not None:
        errs["t_apex"] = _rel(f.apex["t"], ta)
        errs["H"] = _rel(f.apex_height, linear_drag_state(ta, [0.0, h], v0, k, G)[0][1])
    print("linear", h, v, th, k, errs)
    assert max(errs.values()) < TOL
    assert abs(rT[1]) < 1e-12 * max(h, 1.0)  # the closed-form time lands the closed-form path


def test_lambert_landing_is_the_principal_root():
    """From the ground the other branch is the start (s = 0); W0 gives the flight."""
    T = linear_drag_landing_time(0.0, 6.0, 0.3, G)
    assert T > 0.1
    assert linear_drag_state(T, [0.0, 0.0], [8.0, 6.0], 0.3, G)[0][1] == pytest.approx(0.0, abs=1e-13)


def _landing_s_mp(h, vy0, k, g):
    """The landing condition h' + c (1 - e^{-s}) - s = 0 solved by bisection in 50-digit arithmetic (mpmath)."""
    import mpmath as mp
    mp.mp.dps = 50
    tau = 1 / mp.mpf(k)
    c = (mp.mpf(vy0) + g * tau) / (g * tau)
    hp = mp.mpf(h) / (g * tau * tau)

    def f(s):
        return hp + c * (1 - mp.exp(-s)) - s
    lo = mp.mpf(0) if h > 0 else mp.mpf(k) * mp.mpf(vy0) / g  # past the start (s = 0) when h = 0: beyond the apex
    hi = mp.mpf(1)
    while f(hi) > 0:
        hi *= 2
    for _ in range(400):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@pytest.mark.parametrize("k", [3.0, 1.0, 0.1, 1e-2, 1e-3, 1e-4, 1e-5])
@pytest.mark.parametrize("h,vy0", [(0.0, 10.0), (2.0, 6.0), (10.0, 0.0), (10.0, -3.0)])
def test_lambert_landing_time_is_exact_also_for_weak_drag(h, vy0, k):
    """Review R-E F2: Lambert's W alone erred by ~1e-16 / s^2 relative (1e-8 at s = 1.4e-4, 7e-7 at s = 2e-5); with the
    Newton polish the landing time is exact to round-off against a 50-digit bisection of the landing condition, from
    the Stokes regime of a real ball (k = 1e-4 1/s: a 20 mm steel ball in air) to strong drag. Measured: <= 8e-16
    (W alone: up to 7.3e-7 at k = 1e-5, as the review found)."""
    T = linear_drag_landing_time(h, vy0, k, G)
    ref = float(_landing_s_mp(h, vy0, k, G)) / k
    assert _rel(T, ref) < 2e-15


@pytest.mark.parametrize("ratio", [1.0, 1.5, 3.0])
def test_lambert_landing_time_downwards_beyond_the_terminal_speed(ratio):
    """Review R-E F10: launched downwards at or beyond the terminal speed (c <= 0) the same formula holds (the argument
    of W0 is >= 0); c = 0 is uniform motion at v_t, T = h / v_t. Against the 50-digit bisection and the flight
    integrated by DOP853."""
    k, h = 0.5, 20.0
    vt = G / k
    T = linear_drag_landing_time(h, -ratio * vt, k, G)
    assert _rel(T, float(_landing_s_mp(h, -ratio * vt, k, G)) / k) < 2e-15
    if ratio == 1.0:
        assert T == pytest.approx(h / vt, rel=1e-15)
    f = fly(STEEL, [0.0, h], [1.0, -ratio * vt], forces=[LinearDrag(k * STEEL.mass)])
    assert _rel(f.flight_time, T) < TOL


def test_stokes_law_and_reynolds():
    """b = 3 pi mu d with the air of core.data; a 50 um droplet of water reaches v_t = m g / b, and its Reynolds number
    along the path is rho |v| d / mu (here up to 0.25: the law's error 3 Re/16 = 4.7 %). This checks the engine's law,
    not the droplet's real fall: the history force, not modelled, changes its speed by ~4 % while it accelerates
    (``test_the_stated_size_of_the_history_force``)."""
    a = air()
    d = 50e-6
    drag = stokes_drag(d)
    assert drag.b == pytest.approx(3 * math.pi * a["mu"] * d, rel=1e-15)
    drop = Body(1000.0 * math.pi * d ** 3 / 6.0, d, "water droplet")
    f = fly(drop, [0.0, 0.05], [0.0, 0.0], forces=[drag])
    vt = drag.terminal_speed(drop.mass, G)
    assert abs(f.landing["vy"]) == pytest.approx(vt, rel=1e-9)  # 0.05 m is ~600 relaxation lengths
    re = f.reynolds()[0]
    assert re.max() == pytest.approx(a["rho"] * vt * d / a["mu"], rel=1e-6)
    assert re.max() < 0.26 and float(oseen_error(re.max())) < 0.048
    assert f.energy_balance() < TOL


def _maxey_riley(R, history=True, unsteady=True, dt=1e-3, T=1.0):
    """A sphere in the Stokes regime released from rest (units tau_p, g tau_p): (1 + R/2) a = (1 - R) - v - 1.5
    sqrt(2/pi) sqrt(R) int_0^t a(s) / sqrt(t - s) ds, by product integration (a constant on each step, implicit in the
    newest step). history/unsteady False: without the history term / without the added mass and the buoyancy."""
    C = 1.5 * math.sqrt(2.0 / math.pi) * math.sqrt(R) if history else 0.0
    m, src = (1.0 + R / 2.0, 1.0 - R) if unsteady else (1.0, 1.0)
    n = int(round(T / dt))
    a, v, tj = np.zeros(n), np.zeros(n + 1), np.arange(n + 1) * dt
    for k in range(n):
        tm = (k + 0.5) * dt
        hist = float(2.0 * (np.sqrt(tm - tj[:k]) - np.sqrt(tm - tj[1:k + 1])) @ a[:k]) if k else 0.0
        a[k] = (src - v[k] - C * hist) / (m + dt / 2.0 + 2.0 * C * math.sqrt(dt / 2.0))
        v[k + 1] = v[k] + a[k] * dt
    return v[-1]


@pytest.mark.parametrize("rho_body,stated", [(7850.0, 0.014), (998.2, 0.039)])
def test_the_stated_size_of_the_history_force(rho_body, stated):
    """Review R-E F3: core.mechanics.drag states the unsteady forces Stokes's law leaves out. At t = tau_p the full
    Maxey–Riley speed is below the steady law's by 1.44 % for steel in air and 4.03 % for a water droplet (the history
    term alone 1.42 % and 3.89 %: of order sqrt(rho_air / rho_body), not rho_air / rho_body = 1.5e-4 and 1.2e-3 as
    stated before). The integration converges in the step (2e-3 and 5e-4 give the same three digits)."""
    R = air()["rho"] / rho_body
    v_steady = 1.0 - math.exp(-1.0)
    alone = 1.0 - _maxey_riley(R, unsteady=False) / v_steady
    full = 1.0 - _maxey_riley(R) / v_steady
    print("history force", rho_body, alone, full)
    assert alone == pytest.approx(stated, rel=0.05) and 0.5 * math.sqrt(R) < alone < 1.5 * math.sqrt(R)
    assert full > alone > 10 * R


# --- quadratic drag (the model) ---------------------------------------------------------------------------------------
def test_quadratic_vertical_up_and_down_against_closed_forms():
    """Thrown straight up from 2 m at 20 m/s: the top at (v_t/g) atan(v0/v_t), its height, v(t) up (tan) and down
    (tanh), the landing at t_top + (v_t/g) arccosh(exp(g H / v_t^2)). Measured: 3e-13–4e-11."""
    drag = dq.QuadraticDrag.sphere(BALL.diameter)
    k = drag.k(BALL.mass)
    h, v0 = 2.0, 20.0
    f = fly(BALL, [0.0, h], [0.0, v0], forces=[drag])
    up = dq.vertical_up(0.0, v0, k)
    H = h + up["h_up"]
    errs = {"t_top": _rel(f.apex["t"], up["t_top"]), "H": _rel(f.apex_height, H),
            "T": _rel(f.flight_time, up["t_top"] + dq.fall_time(H, k))}
    t = np.linspace(0.0, up["t_top"], 50)
    s = f.sample_at(t)
    ref = dq.vertical_up(t, v0, k)
    errs["v_up"] = float(np.max(np.abs(s["v"][:, 1] - ref["v"]))) / v0
    errs["y_up"] = float(np.max(np.abs(s["r"][:, 1] - h - ref["y"]))) / H
    t2 = np.linspace(up["t_top"], f.flight_time, 50)
    s2 = f.sample_at(t2)
    ref2 = dq.vertical_down(t2 - up["t_top"], k)
    errs["v_down"] = float(np.max(np.abs(-s2["v"][:, 1] - ref2["v"]))) / v0
    errs["y_down"] = float(np.max(np.abs(H - s2["r"][:, 1] - ref2["fallen"]))) / H
    errs["E"] = f.energy_balance()
    print("vertical", errs)
    assert max(errs.values()) < TOL
    assert np.all(s["r"][:, 0] == 0.0)


def _radau(body, drag, h, v0):
    """The second integrator: Radau IIA (implicit, order 5; another family than DOP853), with the landing event."""
    k = drag.k(body.mass)

    def rhs(t, Y):
        vx, vy = Y[2], Y[3]
        sp = math.hypot(vx, vy)
        return [vx, vy, -k * sp * vx, -G - k * sp * vy]

    def land(t, Y):
        return Y[1]
    land.terminal, land.direction = True, -1
    sol = integrate.solve_ivp(rhs, (0.0, 100.0), [0.0, h, v0[0], v0[1]], method="Radau", rtol=1e-13,
                              atol=[1e-13 * 10] * 2 + [1e-13 * 10] * 2, events=land)
    T = float(sol.t_events[0][0])
    return T, float(sol.y_events[0][0][0])


QUAD = [(0.0, 25.0, 45.0), (0.0, 25.0, 40.0), (10.0, 25.0, 20.0), (5.0, 15.0, 0.0), (3.0, 10.0, -25.0),
        (0.0, 20.0, 70.0), (1.0, 2.0, 0.0)]


@pytest.mark.parametrize("h,v,th", QUAD)
def test_quadratic_2d_against_the_hodograph_and_radau(h, v, th):
    """Measured: against the hodograph up to 3.6e-11 in T, L, H, the landing speed and angle; Radau IIA (rtol 1e-13)
    gives the same deviations (the hodograph and Radau agree with each other better than with DOP853 at rtol 1e-11)."""
    drag = dq.QuadraticDrag.sphere(BALL.diameter)
    v0 = _v(v, th)
    f = fly(BALL, [0.0, h], v0, forces=[drag])
    hd = dq.hodograph(v, math.radians(th), h, drag.k(BALL.mass))
    res = f.results()
    errs = {"T": _rel(res["T"], hd["T"]), "L": _rel(res["L"], hd["L"]), "H": _rel(res["H"], hd["H"]),
            "v_land": _rel(res["v_land"], hd["v_land"]),
            "angle": _rel(res["angle_land_deg"], hd["angle_land_deg"])}
    if hd["t_apex"] is not None:
        errs["t_apex"] = _rel(f.apex["t"], hd["t_apex"])
    T_r, L_r = _radau(BALL, drag, h, v0)
    errs["T_radau"], errs["L_radau"] = _rel(res["T"], T_r), _rel(res["L"], L_r)
    errs["E"] = f.energy_balance()
    print("quadratic", h, v, th, errs)
    assert max(errs.values()) < TOL


@pytest.mark.parametrize("th", [88.0, 89.9, 89.99])
def test_a_near_vertical_range_is_accurate_to_the_flight_s_length_scale(th):
    """Review R-E F7: the stated 1e-9 applies to lengths relative to the flight's length scale max(h, v0^2/g); the
    range of a near-vertical throw is a small part of it (L = 0.0126 m at 89.99° and 25 m/s), so its own relative error
    is larger. Measured against the hodograph: 4e-11, 3e-11, 3e-11 of v0^2/g; 1.0e-9, 1.7e-8, 1.4e-7 of L."""
    drag = dq.QuadraticDrag.sphere(BALL.diameter)
    f = fly(BALL, [0.0, 0.0], _v(25.0, th), forces=[drag])
    hd = dq.hodograph(25.0, math.radians(th), 0.0, drag.k(BALL.mass))
    assert abs(f.range - hd["L"]) < TOL * 25.0 ** 2 / G
    assert _rel(f.flight_time, hd["T"]) < TOL and _rel(f.apex_height, hd["H"]) < TOL


def test_air_shortens_the_range_and_moves_the_optimum_below_45():
    """Design §5.3 (stand-in, App. A): with air the 67 mm ball at 25 m/s from the ground flies furthest below 45°.
    The engine's own numbers (the stand-in's 36.47 m at 40° and 36.16 m at 45° used k = 0.01729 1/m; with the air of
    core.data, rho 1.2041, k = 0.017200 1/m)."""
    drag = dq.QuadraticDrag.sphere(BALL.diameter)
    assert drag.k(BALL.mass) == pytest.approx(0.0172006, rel=1e-5)
    L = {th: fly(BALL, [0.0, 0.0], _v(25.0, th), forces=[drag]).range for th in (35, 40, 45)}
    Lvac = fly(BALL, [0.0, 0.0], _v(25.0, 45.0)).range
    print("ranges", L, Lvac)
    assert L[40] > L[45] and L[40] > L[35] and Lvac > 1.7 * L[45]
    assert Lvac == pytest.approx(25.0 ** 2 / G, rel=1e-13)


def test_quadratic_validity_along_the_path():
    """The share of the drag's work done outside 10^3 < Re < 2·10^5 (S03's check): zero for the 25 m/s throw (Re from
    5·10^4 to 1.1·10^5); a 67 mm ball pushed off a 0.5 m table at 0.05 m/s starts at Re = 222, and the drag's work
    done until Re reaches 10^3 (at 0.225 m/s) is the share outside, checked against fine samples."""
    drag = dq.QuadraticDrag.sphere(BALL.diameter)
    f = fly(BALL, [0.0, 0.0], _v(25.0, 45.0), forces=[drag])
    val = dq.validity(f, drag)
    a = air()
    assert val["share_outside"] == 0.0
    assert val["re_max"] == pytest.approx(a["rho"] * 25.0 * BALL.diameter / a["mu"], rel=1e-12)
    assert dq.CD_CURVE_ON_RANGE[0] <= val["cd_curve_min"] <= val["cd_curve_max"] <= dq.CD_CURVE_ON_RANGE[1]
    g2 = fly(BALL, [0.0, 0.5], [0.05, 0.0], forces=[drag])
    v2 = dq.validity(g2, drag)
    # Re crosses 10^3 at v = 10^3 mu / (rho d): the work before that is the whole drag work up to that time
    v_lo = 1e3 * a["mu"] / (a["rho"] * BALL.diameter)
    s = g2.sample(rate=20000.0)
    speed = np.linalg.norm(s["v"], axis=1)
    j = int(np.argmax(speed > v_lo))
    W_lo = abs(s["W"][j])
    assert 0.0 < v2["share_outside"] < 1e-3
    assert v2["share_outside"] == pytest.approx(W_lo / v2["work"], rel=0.05)
    assert v2["re_min"] < 1e3 < v2["re_max"] < 2e5


def test_standard_drag_curve_values():
    """Morrison's correlation at the values computed when it was checked (2026-11-14)."""
    assert dq.cd_standard([1e3, 1e4, 1e5, 2e5]) == pytest.approx([0.48376, 0.39260, 0.42571, 0.41594], abs=1e-5)
    assert dq.cd_standard(0.5) == pytest.approx(24 / 0.5, rel=0.03)  # creeping flow
    # the third term rewritten without overflow (a^0.06 / (1 + a^8) for a^-7.94 / (1 + a^-8)): the published form
    re = np.array([1e-3, 0.5, 1e3, 1e5, 2.63e5, 1e6])
    a = re / 2.63e5
    pub = 24 / re + 2.6 * (re / 5) / (1 + (re / 5) ** 1.52) + 0.411 * a ** -7.94 / (1 + a ** -8) \
        + 0.25 * (re / 1e6) / (1 + re / 1e6)
    assert dq.cd_standard(re) == pytest.approx(pub, rel=1e-14)
    assert np.isfinite(dq.cd_standard(1e-200)) and dq.cd_standard(1e-200) == pytest.approx(2.4e201, rel=1e-12)


# --- the second model: the measured curve C_d(Re) (review R-E F1, decision D1) ----------------------------------------
def _morrison(re):
    """Morrison (2016), eq. (1), written out here as published (not through dq.cd_standard)."""
    a = re / 2.63e5
    return 24 / re + 2.6 * (re / 5.0) / (1 + (re / 5.0) ** 1.52) + 0.411 * a ** -7.94 / (1 + a ** -8.0) \
        + 0.25 * (re / 1e6) / (1 + re / 1e6)


def _radau_curve(body, h, v0):
    """Radau IIA (rtol 1e-13) with the curve's force written out: the second method for ``CurveDrag``."""
    a = air()
    rho, mu, d = a["rho"], a["mu"], body.diameter
    A = math.pi * d * d / 4

    def rhs(t, Y):
        vx, vy = Y[2], Y[3]
        sp = math.hypot(vx, vy)
        c = 0.5 * rho * _morrison(rho * sp * d / mu) * A * sp / body.mass
        return [vx, vy, -c * vx, -G - c * vy]

    def land(t, Y):
        return Y[1]
    land.terminal, land.direction = True, -1

    def apex(t, Y):
        return Y[3]
    apex.direction = -1
    sol = integrate.solve_ivp(rhs, (0.0, 100.0), [0.0, h, v0[0], v0[1]], method="Radau", rtol=1e-13,
                              atol=[1e-12] * 4, events=[land, apex])
    T = float(sol.t_events[0][0])
    H = float(sol.y_events[1][0][1]) if len(sol.t_events[1]) else h
    return T, float(sol.y_events[0][0][0]), H


@pytest.mark.parametrize("body,h,v,th", [(BALL, 0.0, 25.0, 45.0), (BALL, 0.0, 20.0, 40.0), (BALL, 0.0, 25.0, 42.0),
                                         (BALL, 10.0, 25.0, 20.0), (STEEL, 1.0, 1.5, 0.0), (BALL, 0.5, 0.05, 0.0)])
def test_curve_drag_against_radau(body, h, v, th):
    """The flight with the measured C_d(Re) (``CurveDrag``) against Radau IIA with Morrison's eq. (1) written out
    independently: T, L, H within 1e-9 (measured: up to 2e-11; 3e-10 in the 1.6 cm range of the last case), and its
    energy balance. The last case starts at Re = 222, below the plateau, and passes through the creeping-flow part of
    the curve."""
    drag = dq.CurveDrag.sphere(body.diameter)
    v0 = _v(v, th)
    f = fly(body, [0.0, h], v0, forces=[drag])
    T_r, L_r, H_r = _radau_curve(body, h, v0)
    res = f.results()
    errs = {"T": _rel(res["T"], T_r), "L": _rel(res["L"], L_r), "H": _rel(res["H"], H_r) if th > 0 else 0.0,
            "E": f.energy_balance()}
    print("curve drag", body.name, h, v, th, errs)
    assert max(errs.values()) < TOL


def test_curve_drag_with_a_constant_curve_is_the_constant_model():
    """With C_d(Re) = 0.47 the force is QuadraticDrag's (to round-off) and the flight is the hodograph's."""
    cst = dq.CurveDrag.sphere(BALL.diameter, curve=lambda re: 0.47 + 0.0 * np.asarray(re, float))
    q = dq.QuadraticDrag.sphere(BALL.diameter)
    for vv in ([3.0, 4.0], [-20.0, 0.1], [0.0, -7.0]):
        assert cst.force(0.0, None, vv) == pytest.approx(q.force(0.0, None, vv), rel=1e-15)
    f = fly(BALL, [0.0, 0.0], _v(25.0, 45.0), forces=[cst])
    hd = dq.hodograph(25.0, math.radians(45.0), 0.0, q.k(BALL.mass))
    assert _rel(f.range, hd["L"]) < TOL and _rel(f.flight_time, hd["T"]) < TOL


def test_curve_drag_is_stokes_in_creeping_flow_and_the_review_numbers():
    """At Re = 1e-6 the curve's force is Stokes's 3 pi mu d v (the curve's other terms: 4e-9 relative). The ranges with
    the measured curve against the constant 0.47, as the review R-E F1 computed them independently
    (d_energy_validity.out: 27.2222 / 28.2371 m and 36.2338 / 37.8905 m, i.e. +3.73 % and +4.57 %)."""
    drag = dq.CurveDrag.sphere(BALL.diameter)
    a = air()
    v_small = 1e-6 * a["mu"] / (a["rho"] * BALL.diameter)
    F = drag.force(0.0, None, [v_small, 0.0])
    assert -F[0] == pytest.approx(3 * math.pi * a["mu"] * BALL.diameter * v_small, rel=1e-7)
    assert np.all(drag.force(0.0, None, [0.0, 0.0]) == 0.0)
    q = dq.QuadraticDrag.sphere(BALL.diameter)
    for v, th, Lc, Lm in ((20.0, 40.0, 27.2222, 28.2371), (25.0, 45.0, 36.2338, 37.8905)):
        assert fly(BALL, [0.0, 0.0], _v(v, th), forces=[q]).range == pytest.approx(Lc, abs=6e-5)
        assert fly(BALL, [0.0, 0.0], _v(v, th), forces=[drag]).range == pytest.approx(Lm, abs=6e-5)
    assert float(drag.cd_at(25.0)) == pytest.approx(float(dq.cd_standard(drag.reynolds(25.0))), rel=1e-15)


def test_curve_drag_refusals():
    with pytest.raises(ValueError):
        dq.CurveDrag.sphere(0.0)
    with pytest.raises(ValueError):
        dq.CurveDrag(1.0, 1.2, -1.0, 0.1)
    with pytest.raises(ValueError):  # a 1 m sphere at 30 m/s: Re 2e6, beyond the curve
        fly(Body(500.0, 1.0), [0.0, 1.0], [30.0, 0.0], forces=[dq.CurveDrag.sphere(1.0)])


# --- energy, events, sampling, refusals -------------------------------------------------------------------------------
@pytest.mark.parametrize("h,v,th", [(0.0, 25.0, 45.0), (10.0, 25.0, 85.0), (1.0, 2.0, 0.0), (20.0, 40.0, -30.0)])
def test_energy_balance(h, v, th):
    """E_k + E_p − W = E_0 along the whole flight with both drags (measured 2e-12–3e-11)."""
    drags = [dq.QuadraticDrag.sphere(BALL.diameter), LinearDrag(0.002)]
    f = fly(BALL, [0.0, h], _v(v, th), forces=drags)
    e = f.energy_balance()
    s = f.sample()
    print("energy", h, v, th, e)
    assert e < TOL
    assert np.all(np.diff(s["W"]) <= 0) and np.all(s["W_i"] <= 0)  # drag only takes energy


def test_declared_event_and_apex_in_vacuum():
    """A declared event (passing x = 5 m) and the apex against the closed forms."""
    v0 = _v(12.0, 50.0)
    ev = Event("x5", lambda t, r, v: r[0] - 5.0, direction=1)
    f = fly(STEEL, [0.0, 1.0], v0, events=[ev])
    t5 = 5.0 / v0[0]
    assert f.events["x5"][0]["t"] == pytest.approx(t5, rel=1e-13)
    assert f.events["x5"][0]["y"] == pytest.approx(1.0 + v0[1] * t5 - 0.5 * G * t5 * t5, rel=1e-13)
    assert f.apex["y"] == pytest.approx(1.0 + v0[1] ** 2 / (2 * G), rel=1e-14)
    stop = Event("stop", lambda t, r, v: r[0] - 5.0, direction=1, terminal=True)
    with pytest.raises(ValueError):  # a terminal declared event before the landing: no landing
        fly(STEEL, [0.0, 1.0], v0, events=[stop], t_max=10.0)


def test_sampling_on_exact_multiples():
    f = fly(STEEL, [0.0, 1.25], [2.0, 0.0])
    s = f.sample()  # 1/120 s
    k = np.arange(len(s["t"]))
    assert np.array_equal(s["t"], k / 120.0)
    assert s["t"][12] == 0.1 and s["t"][36] == 0.3
    assert s["t"][-1] <= f.t_end < s["t"][-1] + 1 / 120
    e = f.sample(include_end=True)
    assert e["t"][-1] == f.t_end and len(e["t"]) == len(s["t"]) + 1
    assert f.flight_time == pytest.approx(math.sqrt(2 * 1.25 / G), rel=1e-14)
    assert f.landing["y"] == pytest.approx(0.0, abs=1e-14)


@pytest.mark.parametrize("call", [
    lambda: fly(STEEL, [0.0, -0.1], [1.0, 1.0]),                  # below the ground
    lambda: fly(STEEL, [0.0, 0.0], [5.0, 0.0]),                   # on the ground, not upwards
    lambda: fly(STEEL, [0.0, 0.0], [5.0, -1.0]),
    lambda: fly(STEEL, [0.0, float("nan")], [1.0, 1.0]),
    lambda: fly(STEEL, [0.0, 1.0], [1.0, float("inf")]),
    lambda: fly(STEEL, [0.0, 1.0], [1.0, 1.0], g=0.0),
    lambda: fly(STEEL, [0.0, 1.0, 2.0, 3.0], [1.0, 1.0, 1.0, 1.0]),
    lambda: Body(0.0),
    lambda: Body(-1.0),
    lambda: Body(1.0, -0.01),
    lambda: Body(float("nan")),
    lambda: stokes_drag(0.0),
    lambda: dq.QuadraticDrag.sphere(-1.0),
    lambda: dq.hodograph(10.0, math.radians(90.0), 1.0, 0.01),
    lambda: dq.hodograph(10.0, 0.0, 0.0, 0.01),
    lambda: linear_drag_landing_time(0.0, 0.0, 0.3, G),
])
def test_refusals(call):
    with pytest.raises(ValueError):
        call()


def test_a_body_held_up_is_refused():
    class Lift:
        def force(self, t, r, v):
            return np.array([0.0, 2.0 * G * STEEL.mass])
    with pytest.raises(ValueError):
        fly(STEEL, [0.0, 1.0], [1.0, 0.0], forces=[Lift()], t_max=5.0)


def test_speed_of_a_grid_point():
    """The S03 atlas computes 1130 flights; one with quadratic drag and its 1/120-s samples took 5 ms of CPU here (the
    design's stand-in: 1.5 ms without the sampling)."""
    import time
    drag = dq.QuadraticDrag.sphere(BALL.diameter)
    t0 = time.process_time()
    for th in range(0, 91, 10):
        fly(BALL, [0.0, 2.0], _v(25.0, th), forces=[drag]).sample()
    per = (time.process_time() - t0) / 10
    print("CPU per flight", per)
    assert per < 0.1
