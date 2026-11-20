# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.core.mechanics.earth_frame`` (design explore_EX2_2026-11-18 §7 «E03», §11 item 42): the WGS 84 normal
gravity against the standard's printed values (NIMA TR8350.2, Tables 3.1, 3.3, 3.4; checked on its text 2026-11-18)
and the Coriolis force against the first-order closed forms (the eastward drift of a dropped body, the sideways offset
of a throw in vacuum by its quadrature), the 3-D flight with the whole force against the planar flight with the
sideways offset, and the force's geometry."""

import math

import numpy as np
import pytest
from scipy import integrate

from lfphys.core.mechanics import (G_STANDARD, WGS84, Body, Coriolis, Medium, drop_east_drift, fly,
                                   latitude_for_gravity, normal_gravity, omega_vector, sideways)
from lfphys.theories.models import drag_quadratic as dq

G = G_STANDARD
STEEL = Body(0.0329, 0.020, "steel 20 mm")
BALL = Body(0.058, 0.067, "ball 67 mm")


# --- the normal gravity -----------------------------------------------------------------------------------------------
def test_normal_gravity_at_the_equator_and_the_poles_is_the_standard_s_printed_values():
    """Table 3.4: gamma_e = 9.7803253359, gamma_p = 9.8321849378 m/s^2; Somigliana's formula with the printed k and
    e^2 gives the pole's value to 6e-11 m/s^2 (the printed digits)."""
    assert normal_gravity(0.0) == pytest.approx(9.7803253359, abs=1e-12)
    assert normal_gravity(90.0) == pytest.approx(9.8321849378, abs=1e-10)
    assert normal_gravity(-90.0) == normal_gravity(90.0)


def test_the_derived_constants_follow_from_the_defining_ones():
    """Table 3.3/3.4 against a, 1/f, GM, omega (Table 3.1): e^2 = f (2 - f), b = a (1 - f), m = omega^2 a^2 b / GM, k =
    b gamma_p / (a gamma_e) - 1, each to its printed digits (and those of b: 1e-4 m, i.e. 3e-14 in m)."""
    W = WGS84
    f = 1.0 / W["inv_f"]
    assert f * (2.0 - f) == pytest.approx(W["e2"], abs=5e-15)
    assert W["a"] * (1.0 - f) == pytest.approx(W["b"], abs=1e-4)
    assert W["omega"] ** 2 * W["a"] ** 2 * W["b"] / W["GM"] == pytest.approx(W["m"], abs=5e-14)  # b to 1e-4 m
    assert W["b"] * W["gamma_p"] / (W["a"] * W["gamma_e"]) - 1.0 == pytest.approx(W["k"], abs=2e-11)


def test_the_standard_gravity_is_the_normal_gravity_at_45_5_degrees():
    """Design §11 item 42 (computed there with the constants as recalled; here with the checked ones): g_n = 9.80665
    m/s^2 at 45.4996°, and 9.80620 m/s^2 at 45°."""
    lat = latitude_for_gravity(G)
    assert lat == pytest.approx(45.4996, abs=5e-5)
    assert normal_gravity(lat) == pytest.approx(G, abs=1e-12)
    assert round(normal_gravity(45.0), 5) == 9.80620


def test_normal_gravity_above_the_ellipsoid():
    """Eq. (4-3) against its own two terms written out, and the free-air gradient near -3.09e-6 s^-2 at 45°."""
    W = WGS84
    f = 1.0 / W["inv_f"]
    for lat, h in ((0.0, 1000.0), (45.0, 10.0), (60.0, 8848.0)):
        s2 = math.sin(math.radians(lat)) ** 2
        g0 = normal_gravity(lat)
        ref = g0 * (1 - 2 / W["a"] * (1 + f + W["m"] - 2 * f * s2) * h + 3 * h * h / W["a"] ** 2)
        assert normal_gravity(lat, h) == pytest.approx(ref, rel=1e-15)
    grad = (normal_gravity(45.0, 1.0) - normal_gravity(45.0, -1.0)) / 2.0
    assert grad == pytest.approx(-3.086e-6, rel=2e-3)


@pytest.mark.parametrize("call", [lambda: normal_gravity(91.0), lambda: normal_gravity(10.0, 3e4),
                                  lambda: normal_gravity(float("nan")), lambda: latitude_for_gravity(9.9),
                                  lambda: omega_vector(100.0, 0.0)])
def test_refusals(call):
    with pytest.raises(ValueError):
        call()


# --- the Coriolis force -----------------------------------------------------------------------------------------------
def test_omega_in_the_flight_s_frame():
    """(x, z, y) = (along the azimuth, to its left, up): Omega = omega (cos phi cos A, cos phi sin A, sin phi); facing
    east the left is north."""
    w = WGS84["omega"]
    Om = omega_vector(45.0, 90.0)
    assert Om == pytest.approx([0.0, w * math.cos(math.radians(45)), w * math.sin(math.radians(45))], abs=1e-20)
    assert np.linalg.norm(omega_vector(12.3, 217.0)) == pytest.approx(w, rel=1e-15)
    assert omega_vector(0.0, 0.0) == pytest.approx([w, 0.0, 0.0], abs=1e-20)  # at the equator facing north


def test_the_force_does_no_work_and_its_planar_part_is_normal_to_the_velocity():
    c = Coriolis(2.0, 40.0, 70.0)
    rng = np.random.default_rng(1)
    for _ in range(20):
        v3 = rng.normal(size=3)
        assert c.force(0.0, None, v3) @ v3 == pytest.approx(0.0, abs=1e-18)
        v2 = rng.normal(size=2)
        F2 = c.force(0.0, None, v2)
        assert F2 @ v2 == pytest.approx(0.0, abs=1e-18)
        # the planar part and the out-of-plane part are the 3-D force at (v_x, 0, v_y)
        F3 = c.force(0.0, None, np.array([v2[0], 0.0, v2[1]]))
        assert F3[[0, 2]] == pytest.approx(F2, rel=1e-14, abs=1e-20)
        assert F3[1] == pytest.approx(float(c.out_of_plane(v2)), rel=1e-14, abs=1e-20)


def test_directions_in_the_northern_hemisphere():
    """A throw to the east is pushed up (Eötvös) and to the right; to the west down and to the right."""
    m = 1.0
    east = Coriolis(m, 45.0, 90.0)
    west = Coriolis(m, 45.0, 270.0)
    assert east.force(0.0, None, [10.0, 0.0])[1] > 0 and west.force(0.0, None, [10.0, 0.0])[1] < 0
    assert east.out_of_plane([10.0, 0.0]) < 0 and west.out_of_plane([10.0, 0.0]) < 0  # z is to the left


@pytest.mark.parametrize("h,lat", [(100.0, 45.0), (50.0, 0.0), (20.0, 60.0)])
def test_a_dropped_body_drifts_east_by_the_first_order_closed_form(h, lat):
    """x_E = (1/3) omega g t^3 cos phi (vacuum, from rest): the 3-D flight with the whole force against it; the
    difference is second order, (omega t)^2 relative (measured 1e-9–1e-8). The x axis faces east (azimuth 90°), so
    the drift is along x; the north–south drift is second order."""
    f = fly(STEEL, [0.0, 0.0, h], [0.0, 0.0, 0.0], forces=[Coriolis(STEEL.mass, lat, 90.0)])
    ref = drop_east_drift(h, lat, G)
    T = math.sqrt(2 * h / G)
    assert f.landing["r"][0] == pytest.approx(ref, rel=5 * (WGS84["omega"] * T) ** 2 + 1e-9)
    assert abs(f.landing["r"][1]) < 10 * WGS84["omega"] ** 2 * T ** 2 * h
    assert f.flight_time == pytest.approx(T, rel=1e-8)


@pytest.mark.parametrize("lat,az,v,th", [(45.5, 90.0, 20.0, 42.3), (45.5, 0.0, 20.0, 30.0), (-30.0, 200.0, 25.0, 60.0)])
def test_the_sideways_offset_in_vacuum_by_its_quadrature(lat, az, v, th):
    """In vacuum the sideways equation has no damping: z(T) = -2 int_0^T (T - t) (Omega_y v_x(t) - Omega_x v_y(t)) dt.
    Along the flight's own velocities (the planar flight with the force's planar part) by scipy.integrate.quad
    against ``sideways`` (1e-8); along the vacuum path v_x = const, v_y = v_y0 - g t (the first-order closed form)
    against ``sideways`` and the 3-D flight with the whole force, which differ from it at order Omega T."""
    v0 = [v * math.cos(math.radians(th)), v * math.sin(math.radians(th))]
    cor = Coriolis(BALL.mass, lat, az)
    f2 = fly(BALL, [0.0, 0.0], v0, forces=[cor])
    T = f2.flight_time
    Om = cor.omega

    def vel(t):
        return f2.state(t)[1]
    path = integrate.quad(lambda t: -2.0 * (T - t) * (Om[2] * vel(t)[0] - Om[0] * vel(t)[1]), 0.0, T,
                          epsabs=0.0, epsrel=1e-12, limit=200)[0]
    vac = integrate.quad(lambda t: -2.0 * (T - t) * (Om[2] * v0[0] - Om[0] * (v0[1] - G * t)), 0.0, T,
                         epsabs=0.0, epsrel=1e-10)[0]
    sw = sideways(f2, cor)
    assert sw["z_land"] == pytest.approx(path, rel=1e-8)
    eps = WGS84["omega"] * T
    assert sw["z_land"] == pytest.approx(vac, rel=20 * eps)
    f3 = fly(BALL, [0.0, 0.0, 0.0], [v0[0], 0.0, v0[1]], forces=[cor])
    assert f3.landing["r"][1] == pytest.approx(sw["z_land"], rel=20 * eps * eps + 1e-9)


@pytest.mark.parametrize("v,th,h", [(20.0, 42.3, 0.0), (20.0, 70.0, 0.0), (25.0, 45.0, 10.0)])
def test_3d_flight_with_the_whole_force_against_the_planar_flight_and_the_sideways_offset(v, th, h):
    """In air (the measured drag curve, buoyancy, added mass) at 45.5° N toward the east: the 3-D flight's landing
    against the planar flight (the force's planar part) and the sideways offset's own equation; they differ at order
    (Omega T)^2 (measured: 3e-9 of the offset, 1e-12 of the range). Explore's longest throw (25 m/s, 45°, from 10 m)
    lands 2.4 mm further east and 7.3 mm to the right (design A.8); along the throw the two differ by 1e-8 of the
    range, also second order."""
    air = Medium.air()
    v0 = [v * math.cos(math.radians(th)), v * math.sin(math.radians(th))]
    drag = dq.CurveDrag.sphere(BALL.diameter)
    cor = Coriolis(BALL.mass, 45.5, 90.0)
    f0 = fly(BALL, [0.0, h], v0, forces=[drag], medium=air)
    f2 = fly(BALL, [0.0, h], v0, forces=[drag, cor], medium=air)
    f3 = fly(BALL, [0.0, 0.0, h], [v0[0], 0.0, v0[1]], forces=[drag, cor], medium=air)
    sw = sideways(f2, cor)
    T = f2.flight_time
    eps = (WGS84["omega"] * T) ** 2
    assert f3.landing["r"][1] == pytest.approx(sw["z_land"], rel=20 * eps + 1e-9)
    assert f3.landing["r"][0] == pytest.approx(f2.range, rel=20 * eps + 1e-9)
    assert f3.flight_time == pytest.approx(T, rel=20 * eps + 1e-9)
    assert f2.energy_balance() < 1e-9  # the Coriolis force does no work
    if h == 10.0:
        assert (f2.range - f0.range) * 1e3 == pytest.approx(2.42, abs=0.01)
        assert sw["right"] * 1e3 == pytest.approx(7.30, abs=0.01)


def test_sideways_refusals():
    cor = Coriolis(BALL.mass, 45.0, 90.0)
    f3 = fly(BALL, [0.0, 0.0, 1.0], [1.0, 0.0, 1.0], forces=[cor])
    with pytest.raises(ValueError):
        sideways(f3, cor)
    f2 = fly(BALL, [0.0, 1.0], [1.0, 1.0])
    with pytest.raises(ValueError):
        sideways(f2, cor)


def test_the_entrained_fluid_s_coriolis_term_cancels_against_the_lift_on_the_air_s_vorticity():
    """Review EX2, R2-E F5 (not adopted, module docstring): in the inviscid theory of Auton, Hunt & Prud'homme (1988)
    the fluid's force on a sphere besides the pressure gradient is C_A m_f (Du/Dt - dV/dt) + (1/2) m_f (u - V) x omega
    (C_A = 1/2). For a fluid at rest in the rotating frame (u = Omega x r, omega = 2 Omega, inertial quantities), the
    sum is -C_A m_f a_rel exactly: no Coriolis term on the entrained mass, so ``Coriolis`` acts on m (and the added
    mass on the relative acceleration only, as ``fly`` has it)."""
    rng = np.random.default_rng(42)
    for _ in range(20):
        Om, r, v, a = (rng.normal(size=3) for _ in range(4))
        mf, CA = rng.uniform(0.1, 2.0), 0.5
        u = np.cross(Om, r)
        Du = np.cross(Om, np.cross(Om, r))
        V = v + u
        dV = a + 2 * np.cross(Om, v) + np.cross(Om, np.cross(Om, r))
        F = CA * mf * (Du - dV) + 0.5 * mf * np.cross(u - V, 2 * Om)
        assert np.allclose(F, -CA * mf * a, rtol=0, atol=1e-12 * mf * (1 + np.abs(a).max()))
