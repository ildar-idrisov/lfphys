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


# --- group delays (EX2 design §3.9, §11 item 27) ---------------------------------------------------------------------
from lfphys.core.constants import C as C_LIGHT  # noqa: E402
from lfphys.core.optics import materials as MAT  # noqa: E402


def _toy(lam, a=1.6, b=1.2e4, k=0.03, e=2e-3):
    """A smooth dispersive index n(lam) = a + b/lam^2 + i (k + e (lam/500)) and its derivative (lam in nm)."""
    return complex(a + b / lam ** 2, k + e * lam / 500.0), complex(-2 * b / lam ** 3, e / 500.0)


LAYERS = {"dispersive": {}, "air": {"a": 1.0, "b": 0.0, "k": 0.0, "e": 0.0}}


@pytest.mark.parametrize("layer", list(LAYERS))
def test_layer_derivative_is_the_layers_matrix_differentiated(layer):
    """``_layer_d`` returns ``_layer``'s matrix itself and its derivative in lam (central differences of ``_layer``
    with the index's own dispersion and the incidence medium's, 4th order), s and p; for an air layer below, at and
    beyond its critical angle (u = 0 near 41.4 degrees: the matrix depends on u analytically)."""
    th_c = math.asin(1.0 / _toy(600.0, a=1.5, b=4e3, k=0.0, e=0.0)[0].real)
    for pol in POLS:
        for th in [0.0, 0.5, 0.7, th_c, th_c * (1 + 1e-9), 1.0]:
            for d in (40.0, 300.0):
                lam = 600.0
                kw = LAYERS[layer]

                def mat(l):
                    n0, _ = _toy(l, a=1.5, b=4e3, k=0.0, e=0.0)
                    n0 = n0.real
                    n, _ = _toy(l, **kw)
                    c = I._cosines([n0, n, 1.0], th)[1]
                    Mt, s = I._layer(n, c, d, l, pol)
                    return Mt * math.exp(s)

                n0, dn0 = _toy(lam, a=1.5, b=4e3, k=0.0, e=0.0)
                n, dn = _toy(lam, **kw)
                c = I._cosines([n0.real, n, 1.0], th)[1]
                Mt, dMt, s = I._layer_d(n, dn, c, d, lam, pol, n0.real * math.sin(th), dn0.real * math.sin(th))
                Mref, sref = I._layer(n, c, d, lam, pol)
                assert np.array_equal(Mt, Mref) and s == sref
                h = 1e-2
                fd = (8 * (mat(lam + h) - mat(lam - h)) - (mat(lam + 2 * h) - mat(lam - 2 * h))) / (12 * h)
                assert np.allclose(dMt * math.exp(s), fd, rtol=1e-7, atol=1e-9 * np.max(np.abs(fd))), (pol, th, d)


@pytest.mark.parametrize("pol", POLS)
def test_group_delay_of_a_lossless_slab_is_the_closed_form(pol):
    """A non-dispersive slab n between equal media: t = t01 t12 e^{i beta}/(1 + rho e^{2i beta}), rho = r01 r12, so
    tau_t = (n d cos theta1 / c)(1 - rho^2)/(1 + 2 rho cos 2beta + rho^2) and, with phi_r = arg(r01 + r12 e^{2i beta})
    - arg(1 + rho e^{2i beta}), tau_r = (n d cos theta1 / c) [2 r12 (r12 + r01 cos 2beta)/(r01^2 + 2 rho cos 2beta +
    r12^2) - 2 rho (rho + cos 2beta)/(1 + 2 rho cos 2beta + rho^2)] (1e-12)."""
    for n, d in ((1.5, 2000.0), (2.3, 137.0), (1.38, 99.6)):
        for th in np.radians([0.0, 20.0, 45.0, 70.0]):
            for lam in np.linspace(450.0, 700.0, 11):
                c1 = math.sqrt(1 - (math.sin(th) / n) ** 2)
                r01 = I.fresnel(1.0, n, th, pol)[0].real
                r12 = I.fresnel(n, 1.0, math.asin(math.sin(th) / n), pol)[0].real
                rho = r01 * r12
                beta = 2 * math.pi * n * d * c1 / lam
                tau1 = n * d * 1e-9 * c1 / C_LIGHT
                c2 = math.cos(2 * beta)
                tau_t = tau1 * (1 - rho ** 2) / (1 + 2 * rho * c2 + rho ** 2)
                g = I.group_delay([1.0, n, 1.0], [d], lam, th, pol)
                assert g["tau_t"] == pytest.approx(tau_t, rel=1e-12)
                num_r = r01 ** 2 + 2 * rho * c2 + r12 ** 2  # |r01 + r12 e^{2i beta}|^2: 0 for a reflectionless slab
                if num_r > 1e-6:
                    den_t = 1 + 2 * rho * c2 + rho ** 2
                    tau_r = tau1 * (2 * r12 * (r12 + r01 * c2) / num_r - 2 * rho * (rho + c2) / den_t)
                    assert g["tau_r"] == pytest.approx(tau_r, rel=1e-9, abs=1e-12 * tau1)
                st = I.stack([1.0, n, 1.0], [d], lam, th, pol)
                assert g["r"] == pytest.approx(st["r"], abs=1e-14) and g["t"] == pytest.approx(st["t"], abs=1e-14)


@pytest.mark.parametrize("pol", POLS)
def test_group_delay_of_total_reflection_with_dispersion_against_the_complex_step(pol):
    """N-BK7 into air beyond the critical angle: arg r_s = -2 atan(Q/(n1 cos theta)), arg r_p = -2 atan(n1 Q/(n2^2 cos
    theta)), Q = sqrt(n1^2 sin^2 theta - n2^2), with SCHOTT's Sellmeier n1(lambda); this real-analytic phase
    differentiated by the complex step (Im phi(lambda + ih)/h) against ``group_delay`` with ``materials.dindex``."""
    spec = MAT.data.OPTICAL_MATERIALS["schott_n_bk7"]
    for lam in (450.0, 550.0, 632.8, 800.0, 1500.0):
        for th in np.radians([43.0, 50.0, 60.0, 75.0]):
            def phase(z):
                w = z / 1000.0
                n1 = np.sqrt(1 + sum(b * w * w / (w * w - c) for b, c in zip(spec["B"], spec["C"])))
                Q = np.sqrt(n1 * n1 * math.sin(th) ** 2 - 1.0)
                return -2 * np.arctan(Q / (n1 * math.cos(th))) if pol == "s" else -2 * np.arctan(n1 * Q / math.cos(th))
            ref = phase(complex(lam, 1e-20)).imag / 1e-20
            n1 = MAT.index("schott_n_bk7", lam).real
            dn1 = MAT.dindex("schott_n_bk7", lam).real
            g = I.group_delay([n1, 1.0], [], lam, th, pol, [dn1, 0.0])
            assert g["dphi_r"] == pytest.approx(ref, rel=1e-11)
            assert g["tau_r"] == pytest.approx(-1e-9 * lam ** 2 / (2 * math.pi * C_LIGHT) * ref, rel=1e-11)


def _phase_fd(build, lam, th, pol, h=1e-3):
    """d(arg r)/dlam and d(arg t)/dlam by 4th-order central differences of ``stack`` (``build(lam)`` gives ns, ds)."""
    def ph(l):
        ns, ds = build(l)
        st = I.stack(ns, ds, l, th, pol)
        return np.array([cmath.phase(st["r"]), cmath.phase(st["t"])])
    p = [ph(lam + k * h) for k in (-2, -1, 1, 2)]
    return (8 * (p[2] - p[1]) - (p[3] - p[0])) / (12 * h)


def _build(layers, ds, sub="schott_n_bk7", inc=None):
    def f(lam):
        n0 = 1.0 if inc is None else MAT.index(inc, lam).real
        return [n0] + [MAT.index(k, lam) for k in layers] + [MAT.index(sub, lam)], ds
    return f


def _dns(layers, sub="schott_n_bk7", inc=None):
    def f(lam):
        d0 = 0.0 if inc is None else MAT.dindex(inc, lam).real
        return [d0] + [MAT.dindex(k, lam) for k in layers] + [MAT.dindex(sub, lam)]
    return f


@pytest.mark.parametrize("case", ["ar_film", "mirror_x4", "kretschmann"])
@pytest.mark.parametrize("pol", POLS)
def test_group_delay_with_real_materials_against_finite_differences(case, pol):
    """Dispersive structures of real materials (a MgF2 film on N-BK7, a Ta2O5/SiO2 quarter-wave mirror, 50 nm of gold on
    an N-BK7 prism): the exact derivative against 4th-order central differences of the phases of ``stack``."""
    if case == "ar_film":
        layers, ds, inc, angles = ["mgf2_film_rodriguez"], [96.64], None, (0.0, 30.0, 60.0)
    elif case == "mirror_x4":
        layers, ds, inc, angles = ["ta2o5_film_gao", "sio2_film_gao"] * 4, [63.74, 92.96] * 4, None, (0.0, 45.0)
    else:
        layers, ds, inc, angles = ["au_johnson_christy"], [50.0], "schott_n_bk7", (40.0, 43.773, 50.0)
    build, dns = _build(layers, ds, inc=inc), _dns(layers, inc=inc)
    if case == "kretschmann":  # the exit medium is air
        def build(lam, _b=build):  # noqa: E306
            ns, d = _b(lam)
            return ns[:-1] + [1.0], d

        def dns(lam, _d=dns):  # noqa: E306
            return _d(lam)[:-1] + [0.0]
    for lam in (451.3, 551.7, 632.8):  # off the tables' nodes (the interpolant's second derivative jumps there)
        for th in np.radians(angles):
            ns, d = build(lam)
            g = I.group_delay(ns, d, lam, th, pol, dns(lam))
            fd = _phase_fd(build, lam, th, pol)
            assert g["dphi_t"] == pytest.approx(fd[1], rel=2e-6, abs=1e-9)
            assert g["dphi_r"] == pytest.approx(fd[0], rel=2e-6, abs=1e-9)


@pytest.mark.parametrize("pol", POLS)
def test_frustrated_total_reflection_delay(pol):
    """A gap of air between two N-BK7 prisms beyond the critical angle (the optical tunnel barrier): the delays of r
    and t are equal (a symmetric lossless structure: r/t is imaginary), agree with finite differences, and saturate as
    the gap widens (the Hartman effect: at a fixed angle in non-dispersive media they tend to 0, the gap's phase no
    longer changing with lambda once e^{-kappa d} is negligible); a 100 um gap does not overflow."""
    th = math.radians(60.0)
    taus = []
    for d in (50.0, 100.0, 200.0, 400.0, 800.0, 1600.0, 3200.0):
        g = I.group_delay([1.515, 1.0, 1.515], [d], 632.8, th, pol)
        assert g["tau_r"] == pytest.approx(g["tau_t"], rel=1e-10, abs=1e-30)
        fd = _phase_fd(lambda lam, d=d: ([1.515, 1.0, 1.515], [d]), 632.8, th, pol)
        assert g["dphi_t"] == pytest.approx(fd[1], rel=1e-6, abs=1e-12)
        taus.append(abs(g["tau_t"]))
    assert all(b < a for a, b in zip(taus[1:], taus[2:])) and taus[-1] < 1e-25
    # with the glass's dispersion the delay keeps a finite, tiny value; still equal for r and t
    lam = 632.8
    nb, dnb = MAT.index("schott_n_bk7", lam).real, MAT.dindex("schott_n_bk7", lam).real
    g = I.group_delay([nb, 1.0, nb], [200.0], lam, th, pol, [dnb, 0.0, dnb])
    fd = _phase_fd(lambda l: ([MAT.index("schott_n_bk7", l).real, 1.0, MAT.index("schott_n_bk7", l).real], [200.0]),
                   lam, th, pol)
    assert g["dphi_t"] == pytest.approx(fd[1], rel=1e-6) and g["tau_r"] == pytest.approx(g["tau_t"], rel=1e-9)
    g = I.group_delay([1.5, 1.0, 1.5], [100e3], 633.0, th, pol)
    assert math.isfinite(g["tau_r"]) and math.isfinite(g["tau_t"])


def test_one_boundary_between_constant_indices_has_no_delay():
    """One boundary between non-dispersive media: r and t do not depend on lambda at a fixed angle (below and beyond
    the critical angle), so both delays are exactly 0."""
    for ns in ([1.0, 1.5], [1.5, 1.0]):
        for th in (0.0, 0.3, 0.9):
            for pol in POLS:
                g = I.group_delay(ns, [], 632.8, th, pol)
                assert g["tau_t"] == 0.0 and g["tau_r"] == 0.0
