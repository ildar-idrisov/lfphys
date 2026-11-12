# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Closed forms of thin-film optics (lfphys.core.optics.thin_films) against the transfer-matrix method
(lfphys.core.optics.interfaces.stack, an independent route) and against limiting cases."""

import math

import numpy as np
import pytest

from lfphys.core.optics import interfaces, thin_films as tf

POLS = ("s", "p")


# --- one film: Airy summation with complex Fresnel coefficients == transfer matrices ---------------------
@pytest.mark.parametrize("pol", POLS)
@pytest.mark.parametrize("n0,n1,n2,d", [
    (1.0, 1.38, 1.5, 99.6),            # antireflection layer
    (1.0, 2.3, 1.0, 2000.0),           # free-standing high-index film
    (1.0, 0.2 + 3.3j, 1.5, 30.0),      # metal-like film
    (1.5, 0.2 + 3.3j, 1.0, 50.0),      # Kretschmann geometry
    (1.5, 1.0, 1.5, 300.0),            # gap between prisms (evanescent beyond 41.8 deg)
    (1.0, 1.0 + 0.05j, 1.0, 500.0),    # weakly absorbing index-matched film
])
def test_single_film_equals_stack(n0, n1, n2, d, pol):
    for th in np.radians([0.0, 10.0, 35.0, 45.0, 60.0, 80.0, 89.0]):
        st = interfaces.stack([n0, n1, n2], [d], 633.0, th, pol)
        sf = tf.single_film(n0, n1, n2, d, 633.0, th, pol)
        assert abs(sf["r"] - st["r"]) < 1e-12
        assert abs(sf["t"] - st["t"]) < 1e-12
        assert sf["R"] == pytest.approx(st["R"], abs=1e-13)
        assert sf["T"] == pytest.approx(st["T"], abs=1e-13)


def test_fresnel_helper_matches_interfaces_for_real_angles():
    for pol in POLS:
        for th in np.radians([0.0, 20.0, 56.0, 70.0]):
            c0 = complex(math.cos(th))
            c1 = interfaces.snell_cos(1.0, 1.7, c0)
            r, t = tf._rt(1.0, c0, 1.7, c1, pol)
            r2, t2, _, _ = interfaces.fresnel(1.0, 1.7, th, pol)
            assert abs(r - r2) < 1e-15 and abs(t - t2) < 1e-15


# --- Airy intensity formula (Fabry-Perot) ---------------------------------------------------------------
@pytest.mark.parametrize("pol", POLS)
@pytest.mark.parametrize("n0,n1,n2", [(1.0, 2.3, 1.0), (1.0, 2.3, 1.52), (1.33, 1.6, 1.0), (1.0, 1.45, 3.5)])
def test_airy_intensity_formula_equals_stack(n0, n1, n2, pol):
    d = 1700.0
    for lam in np.linspace(400.0, 1600.0, 97):
        for th in np.radians([0.0, 25.0, 40.0]):
            if n0 * math.sin(th) >= min(n1, n2):
                continue
            a = tf.airy(n0, n1, n2, d, lam, th, pol)
            st = interfaces.stack([n0, n1, n2], [d], lam, th, pol)
            assert a["T"] == pytest.approx(st["T"], rel=1e-11, abs=1e-14)


def test_airy_symmetric_film_is_the_textbook_form():
    n, d = 2.3, 1234.0
    R1 = ((n - 1) / (n + 1)) ** 2
    F = 4 * R1 / (1 - R1) ** 2
    for lam in (450.0, 633.0, 1064.0):
        a = tf.airy(1.0, n, 1.0, d, lam, 0.0, "s")
        delta = 4 * math.pi * n * d / lam
        assert a["F"] == pytest.approx(F, rel=1e-14)
        assert a["T_max"] == pytest.approx(1.0, rel=1e-14)
        assert a["T"] == pytest.approx(1 / (1 + F * math.sin(delta / 2) ** 2), rel=1e-12)


def test_airy_refuses_absorbing_or_totally_reflecting_films():
    with pytest.raises(ValueError):
        tf.airy(1.0, 0.2 + 3j, 1.5, 30.0, 633.0, 0.0, "s")
    with pytest.raises(ValueError):
        tf.airy(1.5, 1.0, 1.5, 300.0, 633.0, math.radians(60.0), "s")


# --- quarter-wave layer and stack -----------------------------------------------------------------------
@pytest.mark.parametrize("n1", [1.38, math.sqrt(1.5), 1.6, 2.0])
def test_quarter_wave_layer(n1):
    lam0 = 550.0
    st = interfaces.stack([1.0, n1, 1.5], [lam0 / (4 * n1)], lam0, 0.0, "s")
    assert st["R"] == pytest.approx(tf.quarter_wave_R(1.0, n1, 1.5), rel=1e-12, abs=1e-15)
    if n1 == math.sqrt(1.5):
        assert st["R"] < 1e-30


@pytest.mark.parametrize("N", [1, 2, 5, 8, 15])
def test_quarter_wave_stack_both_orders(N):
    """(HL)^N with H next to the incidence medium and (LH)^N with L next to it: each against the transfer matrices.
    The form ((n0 nH^2N - ns nL^2N)/(n0 nH^2N + ns nL^2N))^2 belongs to the L-first order."""
    n0, nH, nL, ns, lam0 = 1.0, 2.3, 1.45, 1.52, 550.0
    dH, dL = lam0 / (4 * nH), lam0 / (4 * nL)
    hl = interfaces.stack([n0] + [nH, nL] * N + [ns], [dH, dL] * N, lam0, 0.0, "s")["R"]
    lh = interfaces.stack([n0] + [nL, nH] * N + [ns], [dL, dH] * N, lam0, 0.0, "s")["R"]
    assert hl == pytest.approx(tf.quarter_wave_stack_R(n0, nH, nL, ns, N), rel=1e-11)
    assert lh == pytest.approx(tf.quarter_wave_stack_R(n0, nL, nH, ns, N), rel=1e-11)
    spec_form = ((n0 * nH ** (2 * N) - ns * nL ** (2 * N)) / (n0 * nH ** (2 * N) + ns * nL ** (2 * N))) ** 2
    assert lh == pytest.approx(spec_form, rel=1e-11)
    assert hl > lh  # H next to the incidence medium reflects more (n0 = 1 < ns)


# --- frustrated total internal reflection and the evanescent wave ---------------------------------------
@pytest.mark.parametrize("pol", POLS)
def test_ftir_tunnelling_formula_equals_stack(pol):
    n1, ng = 1.5, 1.0
    for th in np.radians([42.0, 45.0, 60.0, 80.0]):
        for d in (10.0, 100.0, 300.0, 1000.0):
            st = interfaces.stack([n1, ng, n1], [d], 633.0, th, pol)
            assert tf.ftir_T(n1, ng, d, 633.0, th, pol) == pytest.approx(st["T"], rel=1e-10)
    # the critical angle itself (kappa = 0) and below it (the continuation is the symmetric film's Airy formula)
    th_c = math.asin(ng / n1)
    for th in (th_c, th_c * (1 - 1e-12), np.radians(20.0), np.radians(35.0)):
        for d in (10.0, 300.0):
            st = interfaces.stack([n1, ng, n1], [d], 633.0, th, pol)
            assert tf.ftir_T(n1, ng, d, 633.0, th, pol) == pytest.approx(st["T"], rel=1e-10)


def test_evanescent_length_against_the_field_profile():
    n1, n2, lam = 1.5, 1.0, 633.0
    for th in np.radians([45.0, 60.0, 85.0]):
        L = tf.evanescent_length(n1, n2, lam, th)
        z1, z2 = 50.0, 250.0
        I1, I2 = interfaces.field_profile([n1, n2], [], lam, th, [z1, z2])
        assert 2 * (z2 - z1) / math.log(I1 / I2) == pytest.approx(L, rel=1e-10)


# --- absorption as Joule heating ------------------------------------------------------------------------
@pytest.mark.parametrize("ns,ds", [
    ([1.0, 0.2 + 3.3j, 1.5], [30.0]),
    ([1.5, 0.2 + 3.3j, 1.0], [50.0]),
    ([1.0, 1.0 + 0.05j, 1.0], [500.0]),
    ([1.0, 2.3, 0.5 + 2.0j, 1.45, 1.52], [60.0, 20.0, 95.0]),
])
def test_joule_heating_equals_one_minus_R_minus_T(ns, ds):
    for th in np.radians([0.0, 30.0, 44.0, 70.0]):
        st = interfaces.stack(ns, ds, 633.0, th, "s")
        A = tf.joule_absorption_s(ns, ds, 633.0, th)["A"]
        assert A == pytest.approx(st["A"], rel=1e-8, abs=1e-12)


def test_joule_heating_is_zero_for_lossless_layers():
    assert tf.joule_absorption_s([1.0, 2.3, 1.45, 1.52], [60.0, 95.0], 550.0, 0.3)["A"] == 0.0


# --- review 2026-10-23 (v05: V5-2, V5-3) --------------------------------------------------------------------
U = 2.0 ** -53


def _arb_evanescent_length(n1, n2, lam, th):
    """Independent high-precision route (Arb ball arithmetic, python-flint): 1/kappa for the binary64 inputs."""
    import flint
    flint.ctx.prec = 256
    a = flint.arb
    q = (a(n1) * a(th).sin()) ** 2 - a(n2) ** 2
    return float(a(lam) / (2 * a.pi() * q.sqrt()))


def test_evanescent_length_is_accurate_near_the_critical_angle():
    """V5-2: n1^2 sin^2 - n2^2 by float subtraction lost digits as eps/q (rel 2.8e-8 at theta_c + 1e-7 deg); the
    closed form now evaluates q in 160-bit arithmetic: one rounding, whatever the distance to theta_c."""
    pytest.importorskip("flint")
    n1, n2, lam = 1.5, 1.0, 633.0
    thc = math.degrees(math.asin(n2 / n1))
    angles = [thc + x for x in (1e-7, 1e-9, 1e-12, 1e-5, 18.0)] + [41.8103149] + [thc + k * 1e-14 for k in range(2, 41)]
    for deg in angles:
        th = math.radians(deg)
        ref = _arb_evanescent_length(n1, n2, lam, th)
        assert tf.evanescent_length(n1, n2, lam, th) == pytest.approx(ref, rel=4 * U), deg
        assert tf.evanescent_q(n1, n2, th) > 0
    for n1, n2 in ((1.33, 1.0), (4.0, 3.7), (2.3, 1.45)):
        for deg in (math.degrees(math.asin(n2 / n1)) + 1e-10, 70.0):
            th = math.radians(deg)
            if tf.evanescent_q(n1, n2, th) > 0:
                assert tf.evanescent_length(n1, n2, 500.0, th) == pytest.approx(
                    _arb_evanescent_length(n1, n2, 500.0, th), rel=4 * U)
    with pytest.raises(ValueError):
        tf.evanescent_length(1.5, 1.0, 633.0, math.radians(thc - 1e-9))


@pytest.mark.parametrize("n0,n1,n2,d,lam,dth", [
    (1.5, 1.0, 1.5, 200.0, 633.0, 7.3e-11),     # prism gap near grazing (reviewer: 41.8103149 deg, 4.1e-12)
    (1.5, 1.0, 1.5, 200.0, 633.0, -1.75e-11),
    (1.5, 1.0, 1.5, 200.0, 633.0, 1.7e-14),
    (4.0, 2.3, 1.0, 20000.0, 300.0, -1e-4),      # thick film near grazing: the phase k n d cos(theta1) is ill-conditioned
    (4.0, 2.3, 1.0, 20000.0, 300.0, 1e-6),
    (3.87, 3.73, 2.15, 40.9, 1278.7, 1e-7),
    (3.49, 1.19 + 19.7j, 3.4777, 0.639, 941.4, 0.0),  # metal film near the exit critical angle
])
def test_single_film_near_grazing_within_its_error_bound(n0, n1, n2, d, lam, dth):
    """V5-2: the Airy sum is a ratio N/D with D = 1 + r01 r12 e^{2i beta} -> 0 when the wave grazes inside the layer;
    single_film returns a first-order bound of its own rounding (err_r, err_t, growing as 1/|D|), and it evaluates
    the Snell cosines exactly as the transfer matrices do, so the comparison tests the algebra, not the rounding of
    sin^2(theta) (which shifts the phase by ~ k u / cos(theta1) near grazing)."""
    nr = n1.real if isinstance(n1, complex) else n1
    th = (math.asin(nr / n0) if not isinstance(n1, complex) else math.asin(n2 / n0)) + dth
    for pol in POLS:
        st = interfaces.stack([n0, n1, n2], [d], lam, th, pol)
        sf = tf.single_film(n0, n1, n2, d, lam, th, pol)
        dr, dt = abs(sf["r"] - st["r"]), abs(sf["t"] - st["t"])
        assert dr <= sf["err_r"] + 8 * U * (1 + abs(st["r"])), (pol, dr, sf["err_r"])
        assert dt <= sf["err_t"] + 8 * U * (1 + abs(st["t"])), (pol, dt, sf["err_t"])
        if abs(sf["D"]) > 0.1:  # far from grazing the two routes agree to a few ulp
            assert max(dr, dt) < 1e-14


def test_single_film_refuses_exact_grazing():
    """At an angle where the float cosine in the layer is exactly 0 the Airy sum is 0/0: a ValueError, not a
    ZeroDivisionError (the caller compares on both sides instead)."""
    th = math.asin(1.0 / 1.5)
    assert interfaces._cosines([1.5, 1.0, 1.5], th)[1] == 0.0
    for pol in POLS:
        with pytest.raises(ValueError):
            tf.single_film(1.5, 1.0, 1.5, 200.0, 633.0, th, pol)


@pytest.mark.parametrize("n0,kap,d,lam,deg", [
    (1.0, 20.0, 500.0, 300.0, 0.0), (4.0, 20.0, 500.0, 300.0, 70.24), (1.0, 3.3, 30.0, 633.0, 0.0),
    (1.0, 10.0, 100.0, 300.0, 0.0), (1.0, 5.0, 200.0, 400.0, 0.0), (1.0, 0.0001, 500.0, 300.0, 30.0),
])
def test_joule_heating_resolves_the_skin_depth(n0, kap, d, lam, deg):
    """V5-3: Simpson with 2001 points per layer left +2.1e-8 (normal incidence) and +2.9e-8 (n0 = 4, 70.24 deg) for a
    1.2 nm skin depth in a 500 nm film; the nodes now follow the decay length and the standing-wave period."""
    ns, ds = [n0, complex(0.2, kap), 1.07], [d]
    th = math.radians(deg)
    st = interfaces.stack(ns, ds, lam, th, "s")
    res = tf.joule_absorption_s(ns, ds, lam, th)
    assert abs(res["A"] + st["R"] + st["T"] - 1.0) < 1e-12 * max(1.0, 1e3 * res["A"]) + 2e-13


def test_single_film_and_stack_agree_within_both_rounding_bounds_near_grazing():
    """V5-2: over random single layers in the v05 ranges, angles concentrated within 1e-16 ... 1e-2 rad of a grazing
    angle in the layer or of the exit critical angle, |Airy - matrices| <= err(Airy) + err(matrices) (both first-order
    rounding bounds; a fuzz of 120 000 comparisons gave at most 0.25 of the sum)."""
    rng = np.random.default_rng(1023)
    worst = 0.0
    for _ in range(3000):
        n0, ns, lam = rng.uniform(1, 4), rng.uniform(1, 4), rng.uniform(300, 1600)
        if rng.random() < 0.5:
            n1, d = rng.uniform(1, 4), math.exp(rng.uniform(0, math.log(20000)))
        else:
            n1, d = complex(rng.uniform(0.01, 5), rng.uniform(0, 20)), math.exp(rng.uniform(math.log(0.1), math.log(500)))
        th = math.radians(rng.uniform(0, 89.9))
        if not isinstance(n1, complex) and n1 < n0 and rng.random() < 0.6:
            th = math.asin(n1 / n0) + rng.choice([1, -1]) * 10 ** rng.uniform(-16, -2)
        elif ns < n0 and rng.random() < 0.5:
            th = math.asin(ns / n0) + rng.choice([1, -1]) * 10 ** rng.uniform(-16, -2)
        for pol in POLS:
            try:
                sf = tf.single_film(n0, n1, ns, d, lam, th, pol)
            except ValueError:  # exact grazing: 0/0
                continue
            st = interfaces.stack([n0, n1, ns], [d], lam, th, pol)
            mb = tf.stack_error_single_layer(n0, n1, ns, d, lam, th, pol)
            for x, y, b in ((sf["r"], st["r"], sf["err_r"] + mb["err_r"]), (sf["t"], st["t"], sf["err_t"] + mb["err_t"])):
                assert abs(x - y) <= b, (pol, abs(x - y), b, n0, n1, ns, d, lam, th)
                if b > 0:
                    worst = max(worst, abs(x - y) / b)
    assert worst > 1e-3  # the bound is not vacuous


def test_airy_formula_and_stack_agree_within_both_rounding_bounds_near_grazing():
    """Found while fuzzing the V5-2 fix: just below grazing inside the film (F -> infinity) the Airy intensity formula
    with its own asin/cos disagreed with the matrices by up to 0.1. With the engine's cosines and phase the difference
    stays within the sum of the two first-order rounding bounds."""
    rng = np.random.default_rng(1024)
    for _ in range(3000):
        n0 = rng.uniform(1.05, 4)
        n1 = rng.uniform(1, n0 * 0.999)
        thg = math.asin(n1 / n0)
        th = thg - 10 ** rng.uniform(-16, -1) if rng.random() < 0.8 else rng.uniform(0, thg)
        ns = rng.uniform(n0 * math.sin(th) * 1.0001, 4.0) if n0 * math.sin(th) * 1.0001 < 4.0 else 4.0
        d, lam = math.exp(rng.uniform(0, math.log(20000))), rng.uniform(300, 1600)
        for pol in POLS:
            try:
                a = tf.airy(n0, n1, ns, d, lam, th, pol)
            except ValueError:
                continue
            T = interfaces.stack([n0, n1, ns], [d], lam, th, pol)["T"]
            b = a["err_T"] + tf.stack_error_single_layer(n0, n1, ns, d, lam, th, pol)["err_T"]
            assert abs(a["T"] - T) <= b, (pol, a["T"], T, b, n0, n1, ns, d, lam, th)
