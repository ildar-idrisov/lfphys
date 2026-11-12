# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Optics of the core and the approximations outside it, each against an independent route."""

import math

import numpy as np
import pytest
from scipy import constants as sc
from scipy import integrate, optimize

from lfphys.core.optics import angular_spectrum, interfaces, radiation, scalar
from lfphys.theories.approx import gaussian_beam, ray_optics


# --- interfaces and stacks ---------------------------------------------------------------------------------
@pytest.mark.parametrize("pol", ["s", "p"])
def test_fresnel_energy_balance_and_tir(pol):
    for th in np.linspace(0, 89.9, 50):
        r, t, R, T = interfaces.fresnel(1.0, 1.5, math.radians(th), pol)
        assert R + T == pytest.approx(1.0, abs=1e-14)
    crit = interfaces.critical(1.5, 1.0)
    for th in np.linspace(math.degrees(crit) + 0.1, 89.9, 20):
        r, t, R, T = interfaces.fresnel(1.5, 1.0, math.radians(th), pol)
        assert R == pytest.approx(1.0, abs=1e-14) and abs(T) < 1e-14


def test_normal_incidence_and_brewster():
    n1, n2 = 1.0, 1.52
    R0 = ((n1 - n2) / (n1 + n2)) ** 2
    for pol in "sp":
        assert interfaces.fresnel(n1, n2, 0.0, pol)[2] == pytest.approx(R0, rel=1e-14)
    assert interfaces.fresnel(n1, n2, interfaces.brewster(n1, n2), "p")[2] < 1e-30


@pytest.mark.parametrize("pol", ["s", "p"])
@pytest.mark.parametrize("th", [0.0, 0.4, 1.2])
def test_stack_without_layers_is_one_interface(pol, th):
    r, t, R, T = interfaces.fresnel(1.0, 1.7, th, pol)
    st = interfaces.stack([1.0, 1.7], [], 0.5, th, pol)
    assert st["r"] == pytest.approx(r, abs=1e-15) and st["T"] == pytest.approx(T, abs=1e-14)


def test_quarter_wave_antireflection():
    n0, n2 = 1.0, 1.5
    n1 = math.sqrt(n0 * n2)
    lam = 0.55
    st = interfaces.stack([n0, n1, n2], [lam / (4 * n1)], lam, 0.0, "s")
    assert st["R"] < 1e-28 and st["T"] == pytest.approx(1.0, abs=1e-14)


@pytest.mark.parametrize("pol", ["s", "p"])
def test_fabry_perot_slab_is_airy(pol):
    n, d, th = 1.5, 10.0, 0.3
    ct = math.sqrt(1 - (math.sin(th) / n) ** 2)
    R1 = interfaces.fresnel(1.0, n, th, pol)[2]
    F = 4 * R1 / (1 - R1) ** 2
    for lam in np.linspace(0.5, 0.6, 41):
        delta = 4 * math.pi * n * d * ct / lam
        airy = 1 / (1 + F * math.sin(delta / 2) ** 2)
        assert interfaces.stack([1.0, n, 1.0], [d], lam, th, pol)["T"] == pytest.approx(airy, rel=1e-12)


def test_absorbing_film_balance_and_beer_lambert():
    lam, kappa, d = 0.5, 1e-3, 50.0
    st = interfaces.stack([1.0, 1.0 + 1j * kappa, 1.0], [d], lam, 0.0, "s")
    assert st["R"] + st["T"] + st["A"] == pytest.approx(1.0, abs=1e-14) and st["A"] > 0
    assert st["T"] == pytest.approx(math.exp(-4 * math.pi * kappa * d / lam), rel=1e-5)


# --- free-space propagation: two exact routes and the paraxial beam ----------------------------------------
def test_angular_spectrum_equals_rayleigh_sommerfeld():
    lam = 1.0
    k = 2 * math.pi / lam
    w0, z = 5.0, 20.0
    x = np.linspace(-40, 40, 4096)
    U0 = np.exp(-x**2 / w0**2)
    Uas = angular_spectrum.propagate(U0, x[1] - x[0], k, z, pad=4)
    xp, wp = np.polynomial.legendre.leggauss(400)
    xp, wp = 6 * w0 * xp, 6 * w0 * wp
    sel = np.abs(x) < 25
    R = np.hypot(x[sel][:, None] - xp[None, :], z)
    Urs = (scalar.rs_kernel(k, z, R) * (np.exp(-xp**2 / w0**2) * wp)[None, :]).sum(axis=1)
    assert np.max(np.abs(Uas[sel] - Urs)) < 1e-6 * np.max(np.abs(Urs))


def test_paraxial_gaussian_beam_against_exact_propagation():
    lam = 1.0
    k = 2 * math.pi / lam
    w0 = 50.0
    zr = gaussian_beam.rayleigh(k, w0)
    x = np.linspace(-1000, 1000, 8192)
    U = angular_spectrum.propagate(np.exp(-x**2 / w0**2), x[1] - x[0], k, zr, pad=2) * np.exp(-1j * k * zr)
    u = gaussian_beam.field_1d(x, zr, k, w0)
    assert np.max(np.abs(U - u)) < 2e-3  # corrections of order (lambda / w0)^2
    I = np.abs(U) ** 2
    w_meas = math.sqrt(4 * np.sum(I * x**2) / np.sum(I))
    assert w_meas == pytest.approx(gaussian_beam.width(zr, k, w0), rel=2e-3)


def test_abcd_free_space_and_thin_lens():
    k, w0 = 2 * math.pi, 3.0
    q0 = -1j * gaussian_beam.rayleigh(k, w0)
    q = gaussian_beam.transform_q(q0, ray_optics.free(7.0))
    assert q == pytest.approx(q0 + 7.0)
    f, s = 10.0, 30.0
    M = ray_optics.system(ray_optics.free(s), ray_optics.thin_lens(f), ray_optics.free(ray_optics.image_distance(f, s)))
    assert abs(M[0, 1]) < 1e-12  # imaging: the height does not depend on the angle
    assert ray_optics.snell(1.5, 1.0, math.radians(60)) is None


# --- black body ---------------------------------------------------------------------------------------------
def test_planck_integrates_to_stefan_boltzmann():
    T = 5772.0
    hc_kt = sc.h * sc.c / (sc.k * T)
    val, _ = integrate.quad(lambda x: radiation.planck_lambda(hc_kt / x, T) * hc_kt / x**2, 1e-6, 200, limit=400,
                            epsabs=0, epsrel=1e-12)
    assert math.pi * val == pytest.approx(radiation.stefan_boltzmann() * T**4, rel=1e-10)
    assert radiation.stefan_boltzmann() == pytest.approx(sc.Stefan_Boltzmann, rel=1e-12)


def test_wien_displacement():
    b = radiation.wien_lambda_constant()
    assert b == pytest.approx(sc.physical_constants["Wien wavelength displacement law constant"][0], rel=1e-12)
    T = 3000.0
    res = optimize.minimize_scalar(lambda lam: -radiation.planck_lambda(lam, T), bounds=(5e-7, 2e-6),
                                   method="bounded", options={"xatol": 1e-15})
    assert res.x == pytest.approx(b / T, rel=1e-7)


def test_field_profile_is_continuous_and_matches_the_interfaces():
    ns, ds, lam, th = [1.0, 2.3, 1.45, 2.3, 1.52], [0.06, 0.09, 0.06], 0.55, 0.3
    tot = sum(ds)
    edges = np.concatenate([[0.0], np.cumsum(ds)])
    for e in edges:  # continuity of the tangential field at every interface
        a, b = interfaces.field_profile(ns, ds, lam, th, [e - 1e-9, e + 1e-9])
        assert a == pytest.approx(b, rel=1e-6)
    st = interfaces.stack(ns, ds, lam, th, "s")
    k = 2 * math.pi / lam * math.cos(th)
    z = np.linspace(-1.0, -0.1, 7)
    ref = np.abs(np.exp(1j * k * z) + st["r"] * np.exp(-1j * k * z)) ** 2
    assert np.allclose(interfaces.field_profile(ns, ds, lam, th, z), ref, rtol=1e-12)
    assert interfaces.field_profile(ns, ds, lam, th, [tot + 0.3])[0] == pytest.approx(abs(st["t"]) ** 2, rel=1e-12)
    # antireflection: no standing wave in front of the coating
    n1 = math.sqrt(1.5)
    flat = interfaces.field_profile([1.0, n1, 1.5], [lam / (4 * n1)], lam, 0.0, np.linspace(-1, 0, 11))
    assert np.allclose(flat, 1.0, atol=1e-13)


@pytest.mark.parametrize("pol", ["s", "p"])
def test_stack_transmission_amplitudes_and_grazing_limits(pol):
    """t of one interface against Fresnel; a wave grazing inside a layer (its critical angle) and grazing incidence
    are regular limits of the characteristic matrices (no division by vanishing coefficients)."""
    for th in (0.0, 0.5, 1.2):
        r, t, R, T = interfaces.fresnel(1.0, 1.7, th, pol)
        st = interfaces.stack([1.0, 1.7], [], 0.5, th, pol)
        assert st["t"] == pytest.approx(t, abs=1e-15) and st["r"] == pytest.approx(r, abs=1e-15)
    # glass prism - air gap - glass: at the gap's critical angle the wave grazes inside the gap
    th_c = math.asin(1.0 / 1.5)
    for th in (th_c, th_c * (1 - 1e-9), th_c * (1 + 1e-9)):
        st = interfaces.stack([1.5, 1.0, 1.5], [0.2], 0.5, th, pol)
        assert math.isfinite(st["R"]) and st["R"] + st["T"] == pytest.approx(1.0, abs=1e-12)
    st = interfaces.stack([1.0, 1.4, 1.5], [0.1], 0.5, math.pi / 2, pol)
    assert st["R"] == pytest.approx(1.0, abs=1e-12) and abs(st["T"]) < 1e-12


@pytest.mark.parametrize("pol", ["s", "p"])
def test_opaque_gap_does_not_overflow(pol):
    """A 100-300 um air gap beyond the critical angle (kappa d ~ 800-2500): T underflows smoothly to 0 instead of
    raising OverflowError (review 2026-10-23, E3); the stack and the FTIR closed form agree on log T while T is
    representable, and the field decays inside the gap without overflow."""
    from lfphys.core.optics import thin_films
    th = math.radians(60.0)
    for d in (30e3, 80e3, 100e3, 300e3):  # nm
        st = interfaces.stack([1.5, 1.0, 1.5], [d], 633.0, th, pol)
        assert st["R"] == pytest.approx(1.0, abs=1e-12) and 0.0 <= st["T"] < 1e-100
        Tf = thin_films.ftir_T(1.5, 1.0, d, 633.0, th, pol)
        assert 0.0 <= Tf < 1e-100
        if st["T"] > 1e-300:
            assert math.log(st["T"]) == pytest.approx(math.log(Tf), rel=1e-10)
    I = interfaces.field_profile([1.5, 1.0, 1.5], [100e3], 633.0, th, [-100.0, 0.0, 50.0, 1e3, 5e4, 1.001e5])
    assert np.all(np.isfinite(I)) and I[2] < I[1] and I[3] < 1e-3 and I[4] < 1e-100
