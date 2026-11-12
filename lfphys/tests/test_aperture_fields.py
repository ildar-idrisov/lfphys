# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The exact references of lfphys.core.optics.aperture_fields against independent quadratures of the
Rayleigh-Sommerfeld integral (scipy / mpmath, 2-D and 1-D) and against each other."""

import math

import numpy as np
import pytest

from lfphys.core.optics import aperture_fields as AF

LAM = 1.0
K = 2 * math.pi / LAM


def _rs_kernel(z):
    """RS-I: U(P) = (z/2pi) int U0 e^{ikR} (1 - ikR) / R^3 dS."""
    def f(x, y):
        R = math.sqrt(x * x + y * y + z * z)
        return z / (2 * math.pi) * np.exp(1j * K * R) * (1 - 1j * K * R) / R**3
    return f


def _dblquad(f, xa, xb, ya, yb):
    from scipy.integrate import dblquad
    re = dblquad(lambda y, x: f(x, y).real, xa, xb, ya, yb, epsabs=1e-12, epsrel=1e-12)[0]
    im = dblquad(lambda y, x: f(x, y).imag, xa, xb, ya, yb, epsabs=1e-12, epsrel=1e-12)[0]
    return re + 1j * im


def test_circle_closed_form_equals_the_radial_integral():
    mp = pytest.importorskip("mpmath")
    for a, z in ((0.8, 1.5), (3.0, 4.0)):
        f = lambda rho: rho * z * mp.expj(K * mp.sqrt(rho**2 + z**2)) * (1 - 1j * K * mp.sqrt(rho**2 + z**2)) \
            / (rho**2 + z**2) ** 1.5  # noqa: E731
        ref = complex(mp.quad(f, mp.linspace(0, a, 9)))
        assert AF.circle_on_axis(K, a, z) == pytest.approx(ref, abs=1e-12)


@pytest.mark.parametrize("x0,y0", [(0.0, 0.0), (0.3, -0.2), (2.0, 0.5)])
def test_rectangle_equals_the_2d_rayleigh_sommerfeld_integral(x0, y0):
    """A 2 x 1.4 rectangle (the point inside, inside off-centre, and outside it) against scipy's 2-D quadrature."""
    pytest.importorskip("scipy")
    z = 2.0
    rect = (-1.0, 1.0, -0.7, 0.7)
    val, err = AF.rectangles_field(K, [rect], z, x0, y0)
    ref = _dblquad(_rs_kernel(z), rect[0] - x0, rect[1] - x0, rect[2] - y0, rect[3] - y0)
    assert err < 1e-11
    assert val == pytest.approx(ref, abs=1e-9)


def test_rectangles_add_and_shift_and_a_wide_one_is_a_plane_wave():
    z = 5.0
    r1, r2 = (-2.0, -1.0, -3.0, 3.0), (1.0, 2.0, -3.0, 3.0)
    both = AF.rectangles_field(K, [r1, r2], z)[0]
    assert both == pytest.approx(AF.rectangles_field(K, [r1], z)[0] + AF.rectangles_field(K, [r2], z)[0], abs=1e-12)
    # moving the point equals moving the aperture
    a = AF.rectangles_field(K, [r1], z, x0=0.4, y0=0.1)[0]
    b = AF.rectangles_field(K, [(r1[0] - 0.4, r1[1] - 0.4, r1[2] - 0.1, r1[3] - 0.1)], z)[0]
    assert a == pytest.approx(b, abs=1e-12)
    # an aperture much wider than z: the field tends to the plane wave e^{ikz}; the remainder is the edge wave
    # of order z/R_edge
    big = AF.rectangles_field(K, [(-400.0, 400.0, -400.0, 400.0)], 1.0)
    assert abs(big[0] - np.exp(1j * K)) < 3.0 / 400 and big[1] < 1e-10


def test_a_staircase_of_strips_converges_to_the_disc():
    """Consistency of the two routes: a disc approximated by thin rectangles converges to the disc's closed form as
    the strips get thinner."""
    a, z = 1.0, 3.0
    ref = AF.circle_on_axis(K, a, z)

    def stair(nstrip):
        edges = np.linspace(-a, a, nstrip + 1)
        rects = []
        for x1, x2 in zip(edges[:-1], edges[1:]):
            xm = 0.5 * (x1 + x2)
            h = math.sqrt(max(a * a - xm * xm, 0.0))
            rects.append((x1, x2, -h, h))
        return abs(AF.rectangles_field(K, rects, z)[0] - ref)
    e1, e2 = stair(40), stair(80)
    assert e2 < 0.5 * e1 and e2 < 2e-3


def _gauss_mp(k, w, z, r=0.0):
    """The same Hankel integral by mpmath (an independent code): panels of a quarter oscillation in c, J0 by mpmath."""
    mp = pytest.importorskip("mpmath")
    mp.mp.dps = 25
    K, W, Z, Rr = mp.mpf(k), mp.mpf(w), mp.mpf(z), mp.mpf(r)

    def prop(c):
        q = K * mp.sqrt(1 - c * c)
        return c * mp.exp(-q * q * W * W / 4) * mp.expj(K * Z * c) * mp.besselj(0, q * Rr)

    def evan(s):
        q = mp.sqrt(K * K + s * s)
        return s * mp.exp(-q * q * W * W / 4 - Z * s) * mp.besselj(0, q * Rr)
    npan = int(math.ceil(4 * k * (z + r) / (2 * math.pi))) + 4
    tot = sum(mp.quad(prop, [mp.mpf(i) / npan, mp.mpf(i + 1) / npan]) for i in range(npan))
    return complex(W * W / 2 * (K * K * tot + mp.quad(evan, [0, 1 / W, mp.inf])))


def test_gaussian_reference_converged_at_large_kz():
    """Review B1-13: lambda = 0.3, w = 0.5, z = 80 (k z = 1676): against composite Gauss-Legendre in c with
    4000 and 8000 panels (numpy, 12 nodes) and against mpmath."""
    k, w, z = 2 * math.pi / 0.3, 0.5, 80.0
    val, err = AF.gaussian_on_axis(k, w, z)
    gx, gw = np.polynomial.legendre.leggauss(12)

    def gl(npan):
        e = np.linspace(0.0, 1.0, npan + 1)
        lo, hi = e[:-1, None], e[1:, None]
        c = 0.5 * (hi - lo) * gx + 0.5 * (hi + lo)
        f = c * np.exp(-k * k * (1 - c * c) * w * w / 4) * np.exp(1j * k * z * c)
        prop = np.sum(0.5 * (hi - lo) * gw * f)
        s = np.linspace(0.0, 60.0 / w, 200001)  # evanescent part: smooth and fast-decaying
        ev = np.trapezoid(s * np.exp(-(k * k + s * s) * w * w / 4 - z * s), s)
        return w * w / 2 * (k * k * prop + ev)
    a, b = gl(4000), gl(8000)
    assert abs(a - b) < 1e-13 and err < 1e-12
    assert abs(val - b) < 1e-12
    assert abs(val - _gauss_mp(k, w, z)) < 1e-12


@pytest.mark.parametrize("w,z,r", [(1.5, 3.0, 0.0), (1.2, 2.0, 0.6), (0.6, 10.0, 2.5)])
def test_gaussian_reference_equals_mpmath_off_axis(w, z, r):
    val, err = AF.gaussian_field(K, w, z, r)
    assert err < 1e-12 and abs(val - _gauss_mp(K, w, z, r)) < 1e-12


def test_gaussian_off_axis_by_symmetry_and_small_distance():
    pytest.importorskip("mpmath")
    w = 1.0
    # at z = 0 the integral returns the given field
    for r in (0.0, 0.5, 1.3):
        assert AF.gaussian_field(K, w, 0.0, r)[0] == pytest.approx(math.exp(-r * r / w / w), abs=1e-12)
    # at z > 0 it equals the 2-D RS integral (scipy)
    pytest.importorskip("scipy")
    z, x0 = 1.0, 0.6
    f = _rs_kernel(z)
    ref = _dblquad(lambda x, y: f(x - x0, y) * math.exp(-(x * x + y * y) / w / w), -6.0, 6.0, -6.0, 6.0)
    assert AF.gaussian_field(K, w, z, x0)[0] == pytest.approx(ref, abs=1e-8)


# --- spectra of the sources, and the exact source in the angular spectrum ------------------------------------------
def test_spectra_equal_their_defining_integrals():
    from scipy.integrate import quad
    for q in (0.0, 0.7, -3.1, 25.0):
        a, b = -0.4, 1.3
        ref = quad(lambda x: math.cos(q * x), a, b, limit=200)[0] - 1j * quad(lambda x: math.sin(q * x), a, b,
                                                                               limit=200)[0]
        assert AF.interval_spectrum([(a, b)])(np.array(q)) == pytest.approx(ref, abs=1e-12)
    a = 1.2
    for qx, qy in ((0.0, 0.0), (1.5, -0.4), (4.0, 3.0)):
        # disc: int_0^a int_0^2pi e^{-i q rho cos(phi - beta)} rho dphi drho = 2 pi int_0^a J0(q rho) rho drho
        from scipy.special import j0
        q = math.hypot(qx, qy)
        ref = 2 * math.pi * quad(lambda r: j0(q * r) * r, 0, a)[0]
        assert complex(AF.disc_spectrum(a)(np.array(qx), np.array(qy))) == pytest.approx(ref, abs=1e-12)
    w = 0.8
    assert complex(AF.gaussian_spectrum(w)(np.array(1.1), np.array(0.3))) == pytest.approx(
        math.pi * w * w * math.exp(-(1.1**2 + 0.3**2) * w * w / 4), abs=1e-14)


def test_rotated_source():
    rect = (0.2, 1.0, -0.5, 0.3)
    qx, qy = np.meshgrid(np.linspace(-5, 5, 7), np.linspace(-4, 4, 5), indexing="ij")
    turned = AF.rotated(AF.rect_spectrum([rect]), math.pi / 2)(qx, qy)  # (x, y) -> (-y, x)
    assert np.allclose(turned, AF.rect_spectrum([(-rect[3], -rect[2], rect[0], rect[1])])(qx, qy), atol=1e-12)


def _grid(n, dx):
    return (np.arange(n) - n // 2) * dx


def test_exact_source_equals_samples_for_a_smooth_field_and_the_exact_field_for_sharp_ones():
    """A Gaussian given by samples or by its spectrum gives the same field (the samples are band-limited); an
    off-centre rectangle and a disc given by their spectra give the exact Rayleigh-Sommerfeld field (no staircase:
    the only errors left are the window's and the omitted evanescent components, at 1e-5 here), where area-sampled
    edges are off by ~1e-2."""
    from lfphys.core.optics import angular_spectrum as AS
    n, dx = 128, LAM / 4
    x = _grid(n, dx)
    X, Y = np.meshgrid(x, x, indexing="ij")
    w = 1.5
    sampled = AS.propagate_field(np.exp(-(X**2 + Y**2) / w**2), dx, K, [0.0, 3.0], check=True)
    spec = AS.propagate_field(AS.Spectral((n, n), AF.gaussian_spectrum(w)), dx, K, [0.0, 3.0], check=True)
    assert np.max(np.abs(sampled - spec)) < 1e-12
    rect = (0.3, 1.7, -0.6, 0.9)
    z = 4.0
    src = AS.Spectral((n, n), AF.rect_spectrum([rect]))
    U = AS.propagate_field(src, dx, K, z, pad=8, check=True)
    d = np.max(np.abs(U - AS.propagate_field(src, dx, K, z, pad=16, check=True)))  # the window's error estimate
    cov = np.zeros((n, n))  # area-weighted samples (8 x 8 sub-pixels), for comparison
    for sx in (np.arange(8) + 0.5) / 8 - 0.5:
        for sy in (np.arange(8) + 0.5) / 8 - 0.5:
            Xs, Ys = X + sx * dx, Y + sy * dx
            cov += (Xs >= rect[0]) & (Xs <= rect[1]) & (Ys >= rect[2]) & (Ys <= rect[3])
    Us = AS.propagate_field(cov / 64, dx, K, z, pad=8, check=True)
    errs, errs_s = [], []
    for i, j in ((n // 2, n // 2), (n // 2 + 4, n // 2 + 1), (n // 2 + 20, n // 2 - 9), (n // 2 - 30, n // 2 + 25)):
        ref = AF.rectangles_field(K, [rect], z, x[i], x[j])[0]
        errs.append(abs(U[i, j] - ref))
        errs_s.append(abs(Us[i, j] - ref))
    assert max(errs) <= 1.5 * d < 1e-3 and max(errs_s) > 10 * max(errs)
    D = AS.propagate_field(AS.Spectral((n, n), AF.disc_spectrum(2.0)), dx, K, [z], pad=8, check=True)[0]
    D2 = AS.propagate_field(AS.Spectral((n, n), AF.disc_spectrum(2.0)), dx, K, [z], pad=16, check=True)[0]
    assert abs(D[n // 2, n // 2] - AF.circle_on_axis(K, 2.0, z)) <= 1.5 * np.max(np.abs(D - D2)) < 1e-3


def test_band_limit_keeps_everything_at_z0_and_converges_faster_in_the_window():
    """The band-limited angular spectrum (Matsushima & Shimobaba 2009): identical at z = 0; for a narrow slit pair
    seen deep (wide angles) it is closer to the exact field than the plain sum at small windows."""
    from lfphys.core.optics import angular_spectrum as AS
    n, dx = 128, LAM / 4
    rects = [(-2.25, -1.75, -4.0, 4.0), (1.75, 2.25, -4.0, 4.0)]
    src = AS.Spectral((n, n), AF.rect_spectrum(rects))
    assert np.max(np.abs(AS.propagate_field(src, dx, K, 0.0, check=True, band_limit=True)
                         - AS.propagate_field(src, dx, K, 0.0, check=True))) < 1e-15
    z = 40.0
    x = _grid(n, dx)
    pts = [(n // 2, n // 2), (n // 2 + 16, n // 2), (n // 2 + 40, n // 2 + 30), (n - 1, n // 2)]
    ref = np.array([AF.rectangles_field(K, rects, z, x[i], x[j])[0] for i, j in pts])

    def err(pad, bl):
        U = AS.propagate_field(src, dx, K, z, pad=pad, check=True, band_limit=bl)
        return max(abs(U[i, j] - r) for (i, j), r in zip(pts, ref)) / np.max(np.abs(U))
    plain, banded = [err(p, False) for p in (2, 4, 16)], [err(p, True) for p in (2, 4, 16)]
    assert banded[0] < 0.5 * plain[0] and banded[1] < plain[1]
    # both shrink as the window grows; the band-limited one much more slowly here (it leaves out real grazing light):
    # measured 2026-10-27: plain 0.29 -> 8.7e-3, band-limited 7.3e-3 -> 5.3e-3 from pad 2 to 16. Neither is better
    # everywhere, so a run measures both (v08: the window estimate).
    assert plain[2] < plain[0] / 10 and banded[2] < banded[0]
