# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The fields of lfphys.core.optics.interfaces for p light and for any polarisation (EX2 design §3.5, §11 item 2):
the components E and Z0 H of ``field_components`` against a second method (the plane-wave amplitudes of every layer
found by solving the boundary conditions directly), the continuity of the tangential fields and of the normal D and B,
the Joule balance for p (Poynting's theorem against 1 - R - T of the transfer matrices), isotropy at normal incidence,
Brewster's angle without a standing wave, an opaque gap without overflow, the field of a Jones state and the power
factors. The s results of ``field_profile`` and ``stack`` are those of test_optics.py and test_thin_films.py,
unchanged."""

import cmath
import math

import numpy as np
import pytest

from lfphys.core.optics import interfaces as I
from lfphys.core.optics import thin_films as tf

POLS = ("s", "p")
LAM = 633.0
STRUCTURES = [  # (ns, ds) in nm: one boundary (both sides), lossless stacks, a prism gap (TIR), absorbing films
    ([1.0, 1.515], []), ([1.515, 1.0], []), ([1.0, 0.2 + 3.3j], []),
    ([1.0, 1.38, 1.52], [114.7]), ([1.0, 2.3, 1.45, 2.3, 1.52], [60.0, 90.0, 60.0]),
    ([1.5, 1.0, 1.5], [200.0]), ([1.0, 0.2 + 3.3j, 1.5], [30.0]), ([1.5, 0.2 + 3.3j, 1.0], [50.0]),
    ([1.0, 2.3, 0.5 + 2.0j, 1.45, 1.52], [60.0, 20.0, 95.0]), ([1.0, 1.0 + 0.05j, 1.0], [500.0]),
]


def _cos(n0, n, th):
    """cos theta in medium n, the decaying / forward branch (Im(n cos) >= 0, then Re >= 0)."""
    c = cmath.sqrt(1 - (n0 * math.sin(th) / n) ** 2)
    if (n * c).imag < 0 or ((n * c).imag == 0 and (n * c).real < 0):
        c = -c
    return c


def _direct(ns, ds, lam, th, pol, z):
    """Second method: the forward and backward plane-wave amplitudes (a_j, b_j) of every medium from the boundary
    conditions (tangential E and H continuous at every interface), solved as one linear system with a_0 = 1 and no
    backward wave in the exit medium; then E and Z0 H of the plane waves themselves: p forward along (c, 0, -sigma),
    backward along (-c, 0, -sigma), Z0 H = n (a + b) y; s: E = (a + b) y, Z0 H = n (a (-c, 0, sigma) + b (c, 0,
    sigma)), sigma = n0 sin theta / n."""
    ns = [complex(n) for n in ns]
    N = len(ns) - 2
    edges = np.concatenate([[0.0], np.cumsum(ds)]) if ds else np.array([0.0])
    cs = [_cos(ns[0], n, th) for n in ns]
    ks = [2 * math.pi * n * c / lam for n, c in zip(ns, cs)]
    d = [0.0] + list(ds) + [0.0]

    def rows(j, zeta):  # coefficients of (a_j, b_j) in (E_t, H_t) at local depth zeta of medium j
        f, b = cmath.exp(1j * ks[j] * zeta), cmath.exp(-1j * ks[j] * zeta)
        n, c = ns[j], cs[j]
        if pol == "s":
            return (f, b), (n * c * f, -n * c * b)
        return (c * f, -c * b), (n * f, n * b)

    m = 2 * N + 2  # unknowns: r, (a_j, b_j) for j = 1..N, t
    A = np.zeros((m, m), complex)
    rhs = np.zeros(m, complex)

    def col(j, which):  # column of a_j (which 0) or b_j (which 1); medium 0: only b (= r); exit: only a (= t)
        if j == 0:
            return None if which == 0 else 0
        if j == N + 1:
            return m - 1 if which == 0 else None
        return 1 + 2 * (j - 1) + which

    for i in range(N + 1):  # interface between medium i and i + 1
        left, right = rows(i, d[i] if i > 0 else 0.0), rows(i + 1, 0.0)
        for eq in range(2):
            r = 2 * i + eq
            for which in range(2):
                cl, cr = col(i, which), col(i + 1, which)
                if cl is None:  # a_0 = 1 on the right-hand side
                    rhs[r] -= left[eq][which]
                else:
                    A[r, cl] += left[eq][which]
                if cr is not None:
                    A[r, cr] -= right[eq][which]
    x = np.linalg.solve(A, rhs)
    amp = [(1.0, x[0])] + [(x[1 + 2 * (j - 1)], x[2 + 2 * (j - 1)]) for j in range(1, N + 1)] + [(x[-1], 0.0)]
    s0 = (ns[0] * math.sin(th)).real
    out_E = np.zeros((len(z), 3), complex)
    out_H = np.zeros((len(z), 3), complex)
    for i, zz in enumerate(z):
        if zz < 0:
            j, zeta = 0, zz
        elif zz >= edges[-1]:
            j, zeta = N + 1, zz - edges[-1]
        else:
            j = int(np.searchsorted(edges, zz, side="right"))
            zeta = zz - edges[j - 1]
        a, b = amp[j]
        n, c = ns[j], cs[j]
        sig = s0 / n
        f, g = a * cmath.exp(1j * ks[j] * zeta), b * cmath.exp(-1j * ks[j] * zeta)
        if pol == "p":
            out_E[i] = [c * (f - g), 0.0, -sig * (f + g)]
            out_H[i] = [0.0, n * (f + g), 0.0]
        else:
            out_E[i] = [0.0, f + g, 0.0]
            out_H[i] = [n * c * (-f + g), 0.0, n * sig * (f + g)]
    return out_E, out_H, x[0], x[-1]


@pytest.mark.parametrize("pol", POLS)
@pytest.mark.parametrize("ns,ds", STRUCTURES)
def test_field_components_against_the_boundary_conditions_solved_directly(ns, ds, pol):
    """E and Z0 H of ``field_components`` (characteristic matrices carried back from the exit) against the plane-wave
    amplitudes of every medium solved from the boundary conditions as one linear system; r and t against ``stack``."""
    rng = np.random.default_rng(3501)
    tot = float(sum(ds))
    z = np.concatenate([rng.uniform(-400.0, 0.0, 30), rng.uniform(0.0, tot, 60) if tot else [],
                        rng.uniform(tot, tot + 400.0, 30)])
    for th in np.radians([0.0, 25.0, 45.0, 60.0, 80.0]):
        E, H = I.field_components(ns, ds, LAM, th, z, pol)
        E2, H2, r, t = _direct(ns, ds, LAM, th, pol, z)
        st = I.stack(ns, ds, LAM, th, pol)
        assert abs(r - st["r"]) < 1e-12 and abs(t - st["t"]) < 1e-12
        scale = max(1.0, float(np.max(np.abs(E2))), float(np.max(np.abs(H2))))
        assert np.max(np.abs(E - E2)) < 1e-11 * scale, (pol, math.degrees(th))
        assert np.max(np.abs(H - H2)) < 1e-11 * scale, (pol, math.degrees(th))


@pytest.mark.parametrize("ns,ds", STRUCTURES)
def test_tangential_fields_and_normal_d_and_b_are_continuous(ns, ds):
    """At every interface E_x, E_y, H_x, H_y and the normal D_z = n^2 E_z and B_z = H_z of p and s light are
    continuous (the field one ulp before the interface against the field at it); E_z of p jumps by
    n_left^2/n_right^2."""
    ns_c = [complex(n) for n in ns]
    edges = np.concatenate([[0.0], np.cumsum(ds)]) if ds else np.array([0.0])
    for th in np.radians([0.0, 30.0, 50.0, 75.0]):
        for pol in POLS:
            for k, e in enumerate(edges):
                zl, zr = np.nextafter(e, -np.inf), e
                E, H = I.field_components(ns, ds, LAM, th, [zl, zr], pol)
                scale = max(1.0, float(np.max(np.abs(E))), float(np.max(np.abs(H))))
                for c in (0, 1):
                    assert abs(E[0, c] - E[1, c]) < 1e-12 * scale and abs(H[0, c] - H[1, c]) < 1e-12 * scale
                nl, nr = ns_c[k], ns_c[k + 1]
                assert abs(nl ** 2 * E[0, 2] - nr ** 2 * E[1, 2]) < 1e-12 * scale * max(abs(nl), abs(nr)) ** 2
                assert abs(H[0, 2] - H[1, 2]) < 1e-12 * scale


@pytest.mark.parametrize("ns,ds", [s for s in STRUCTURES if any(complex(n).imag for n in s[0][1:-1])])
def test_joule_heating_for_p_equals_one_minus_R_minus_T(ns, ds):
    """Poynting's theorem for p light: k0/(n0 cos theta0) sum Im(n^2) integral |E_x|^2 + |E_z|^2 = 1 - R_p - T_p of the
    transfer matrices (as test_thin_films.py checks for s)."""
    for th in np.radians([0.0, 30.0, 44.0, 70.0, 85.0]):
        st = I.stack(ns, ds, LAM, th, "p")
        A = tf.joule_absorption_p(ns, ds, LAM, th)["A"]
        assert A == pytest.approx(st["A"], rel=1e-8, abs=1e-12)


@pytest.mark.parametrize("n0,kap,d,lam,deg", [
    (1.0, 20.0, 500.0, 300.0, 0.0), (4.0, 20.0, 500.0, 300.0, 70.24), (1.0, 3.3, 30.0, 633.0, 0.0),
    (1.0, 10.0, 100.0, 300.0, 60.0), (1.0, 0.0001, 500.0, 300.0, 30.0),
])
def test_joule_heating_for_p_resolves_the_skin_depth(n0, kap, d, lam, deg):
    """The skin-depth cases of review V5-3, for p light."""
    ns, ds = [n0, complex(0.2, kap), 1.07], [d]
    th = math.radians(deg)
    st = I.stack(ns, ds, lam, th, "p")
    res = tf.joule_absorption_p(ns, ds, lam, th)
    assert abs(res["A"] + st["R"] + st["T"] - 1.0) < 1e-12 * max(1.0, 1e3 * res["A"]) + 2e-13


def test_joule_heating_for_p_is_zero_for_lossless_layers():
    assert tf.joule_absorption_p([1.0, 2.3, 1.45, 1.52], [60.0, 95.0], 550.0, 0.3)["A"] == 0.0


@pytest.mark.parametrize("ns,ds", STRUCTURES)
def test_p_and_s_profiles_coincide_at_normal_incidence(ns, ds):
    """At normal incidence p and s are the same physical wave turned by 90 degrees: equal |E|^2 everywhere."""
    z = np.linspace(-500.0, float(sum(ds)) + 300.0, 97)
    a, b = I.field_profile(ns, ds, LAM, 0.0, z, "p"), I.field_profile(ns, ds, LAM, 0.0, z, "s")
    assert np.max(np.abs(a - b)) < 1e-13 * max(1.0, float(np.max(b)))


@pytest.mark.parametrize("n1,n2", [(1.0, 1.515), (1.0, 1.75), (1.515, 1.0)])
def test_brewster_angle_has_no_reflected_p_wave(n1, n2):
    """At Brewster's angle the p field in the incidence medium is the incident wave alone (|E|^2 = 1, no standing
    wave) and in the second medium |t_p|^2; an s wave keeps its standing wave."""
    th = I.brewster(n1, n2)
    z_in = np.linspace(-2000.0, -1.0, 41)
    assert np.max(np.abs(I.field_profile([n1, n2], [], LAM, th, z_in, "p") - 1.0)) < 1e-13
    t = I.stack([n1, n2], [], LAM, th, "p")["t"]
    z_out = np.linspace(0.0, 2000.0, 41)
    assert np.allclose(I.field_profile([n1, n2], [], LAM, th, z_out, "p"), abs(t) ** 2, rtol=1e-13)
    assert np.ptp(I.field_profile([n1, n2], [], LAM, th, z_in, "s")) > 1e-3


def test_s_profile_equals_the_components():
    """``field_profile(..., "s")`` (the code of 2026-10-23, unchanged) and |E_y|^2 of ``field_components`` agree."""
    for ns, ds in STRUCTURES:
        z = np.linspace(-400.0, float(sum(ds)) + 300.0, 61)
        for th in np.radians([0.0, 40.0, 70.0]):
            a = I.field_profile(ns, ds, LAM, th, z, "s")
            E, _ = I.field_components(ns, ds, LAM, th, z, "s")
            assert np.allclose(np.abs(E[:, 1]) ** 2, a, rtol=1e-12, atol=1e-300)
            assert np.all(E[:, 0] == 0) and np.all(E[:, 2] == 0)


@pytest.mark.parametrize("pol", POLS)
def test_opaque_gap_p_field_does_not_overflow(pol):
    """As test_optics.py's opaque gap for s: a 100 um air gap beyond the critical angle, the field finite and
    decaying."""
    I2 = I.field_profile([1.5, 1.0, 1.5], [100e3], LAM, math.radians(60.0), [-100.0, 0.0, 50.0, 1e3, 5e4, 1.001e5],
                         pol)
    assert np.all(np.isfinite(I2)) and I2[2] < I2[1] and I2[3] < 1e-3 and I2[4] < 1e-100


def test_evanescent_p_wave_decays_with_the_s_length():
    """Beyond the critical angle the p field in the rarer medium decays with the same length as s
    (``thin_films.evanescent_length``); its |E|^2 at the surface is |t_p|^2 (2 sin^2 theta_t - 1)... with
    sin theta_t = n1 sin theta / n2 > 1 (|cos|^2 + |sin|^2 of a complex angle)."""
    n1, n2 = 1.5, 1.0
    for th in np.radians([45.0, 60.0, 85.0]):
        L = tf.evanescent_length(n1, n2, LAM, th)
        z1, z2 = 50.0, 250.0
        a, b = I.field_profile([n1, n2], [], LAM, th, [z1, z2], "p")
        assert 2 * (z2 - z1) / math.log(a / b) == pytest.approx(L, rel=1e-10)
        t = I.stack([n1, n2], [], LAM, th, "p")["t"]
        st2 = (n1 * math.sin(th) / n2) ** 2
        assert I.field_profile([n1, n2], [], LAM, th, [0.0], "p")[0] == pytest.approx(abs(t) ** 2 * (2 * st2 - 1),
                                                                                       rel=1e-13)


@pytest.mark.parametrize("ns,ds", STRUCTURES[3:])
def test_field_of_a_jones_state(ns, ds):
    """``field_jones``: (1, 0) is the p field, (0, 1) the s field; |E|^2 of a Jones vector J is ``field_intensity`` of
    J J^dagger (no interference term between p and s), so that +-45 degrees give the same profile and unpolarised light
    the mean of the two profiles."""
    z = np.linspace(-300.0, float(sum(ds)) + 200.0, 41)
    th = math.radians(35.0)
    Ep, _ = I.field_components(ns, ds, LAM, th, z, "p")
    Es, _ = I.field_components(ns, ds, LAM, th, z, "s")
    assert np.array_equal(I.field_jones(ns, ds, LAM, th, z, (1.0, 0.0))[0], Ep)
    assert np.array_equal(I.field_jones(ns, ds, LAM, th, z, (0.0, 1.0))[0], Es)
    rng = np.random.default_rng(3502)
    for _ in range(5):
        J = rng.normal(size=2) + 1j * rng.normal(size=2)
        E, _ = I.field_jones(ns, ds, LAM, th, z, J)
        ref = I.field_intensity(ns, ds, LAM, th, z, np.outer(J, J.conj()))
        assert np.allclose(np.sum(np.abs(E) ** 2, axis=-1), ref, rtol=1e-12)
    plus = I.field_intensity(ns, ds, LAM, th, z, np.array([1, 1]) / math.sqrt(2))
    minus = I.field_intensity(ns, ds, LAM, th, z, np.array([1, -1]) / math.sqrt(2))
    unpol = I.field_intensity(ns, ds, LAM, th, z, np.eye(2) / 2)
    mean = 0.5 * (I.field_profile(ns, ds, LAM, th, z, "p") + I.field_profile(ns, ds, LAM, th, z, "s"))
    assert np.allclose(plus, minus, rtol=1e-13) and np.allclose(unpol, mean, rtol=1e-15)


@pytest.mark.parametrize("ns,ds", STRUCTURES + [([1.0, 1.4, 0.3 + 2.0j], [80.0])])
def test_power_factor_is_T_over_t_squared(ns, ds):
    """``power_factor`` = T/|t|^2 of ``stack`` for s and p (also into an absorbing exit medium, where the two
    differ)."""
    for th in np.radians([0.0, 30.0, 60.0, 85.0]):
        for pol in POLS:
            st = I.stack(ns, ds, LAM, th, pol)
            f = I.power_factor(ns, th, pol)
            assert f * abs(st["t"]) ** 2 == pytest.approx(st["T"], rel=1e-13, abs=1e-300)
