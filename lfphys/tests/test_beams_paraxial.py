# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Paraxial Laguerre-Gauss and Hermite-Gauss beams (theories.approx.beams_paraxial), each against a closed form or an
independent route: the paraxial equation by finite differences, orthonormality and power by quadrature, the HG <-> LG
coefficients by overlap integrals, the Fresnel propagation of the waist's spectrum, the exact propagation (angular
spectrum and the order-l Hankel route, agreeing to the FFT window's error) with the paraxial error scaling as (lambda/w0)^2, the Gouy phase measured on
the axis and on a ring of the exactly propagated field, the OAM per photon of the sampled field, traced energy flow
lines and extracted equiphase surfaces. Negative controls where a test checks a tolerance."""

import math

import numpy as np
import pytest

from lfphys.core.optics import angular_spectrum as AS
from lfphys.core.optics import beams as B
from lfphys.theories.approx import beams_paraxial as PX

LAM = 1.0
K = 2 * math.pi / LAM


def _grid(n, half):
    x = np.linspace(-half, half, n)
    return x, *np.meshgrid(x, x, indexing="ij")


def _lap_dz(f, X, Y, z, h):
    """Fourth-order central differences: the transverse Laplacian and d/dz of f(x, y, z)."""
    d2 = lambda g: (-g(2) + 16 * g(1) - 30 * g(0) + 16 * g(-1) - g(-2)) / (12 * h * h)  # noqa: E731
    lap = d2(lambda s: f(X + s * h, Y, z)) + d2(lambda s: f(X, Y + s * h, z))
    dz = (-f(X, Y, z + 2 * h) + 8 * f(X, Y, z + h) - 8 * f(X, Y, z - h) + f(X, Y, z - 2 * h)) / (12 * h)
    return lap, dz


@pytest.mark.parametrize("p,l", [(0, 0), (0, 1), (1, 2), (2, -3), (3, 4)])
def test_lg_satisfies_the_paraxial_equation(p, l):
    w0 = 2.0
    x, X, Y = _grid(9, 3.0)
    z = 0.37 * PX.rayleigh(K, w0)
    lap, dz = _lap_dz(lambda a, b, c: PX.lg(p, l, a, b, c, K, w0), X, Y, z, 2e-3)
    res = np.max(np.abs(lap + 2j * K * dz)) / np.max(np.abs(2 * K * dz))
    assert res < 2e-8, res
    # negative control: the Gouy phase with the wrong sign
    g = lambda a, b, c: PX.lg(p, l, a, b, c, K, w0) * np.exp(2j * PX.gouy(2 * p + abs(l), c, K, w0))  # noqa: E731
    lap, dz = _lap_dz(g, X, Y, z, 2e-3)
    assert np.max(np.abs(lap + 2j * K * dz)) / np.max(np.abs(2 * K * dz)) > 1e-2


@pytest.mark.parametrize("n,m", [(0, 0), (2, 1), (3, 3)])
def test_hg_satisfies_the_paraxial_equation(n, m):
    w0 = 2.0
    x, X, Y = _grid(9, 3.0)
    lap, dz = _lap_dz(lambda a, b, c: PX.hg(n, m, a, b, c, K, w0), X, Y, -0.8 * PX.rayleigh(K, w0), 2e-3)
    assert np.max(np.abs(lap + 2j * K * dz)) / np.max(np.abs(2 * K * dz)) < 2e-8


def test_modes_are_orthonormal_and_carry_unit_power_at_every_z():
    w0 = 1.5
    zr = PX.rayleigh(K, w0)
    for z in (0.0, 0.7 * zr, 3.0 * zr):
        w = float(PX.params(z, K, w0)[0])
        x, X, Y = _grid(321, 9.0 * w)
        dA = (x[1] - x[0]) ** 2
        lgs = [PX.lg(p, l, X, Y, z, K, w0) for p in range(3) for l in range(-2, 3)]
        G = np.array([[np.vdot(a, b) * dA for b in lgs] for a in lgs])
        assert np.max(np.abs(G - np.eye(len(lgs)))) < 1e-10, (z, np.max(np.abs(G - np.eye(len(lgs)))))
        hgs = [PX.hg(n, m, X, Y, z, K, w0) for n in range(4) for m in range(4)]
        G = np.array([[np.vdot(a, b) * dA for b in hgs] for a in hgs])
        assert np.max(np.abs(G - np.eye(len(hgs)))) < 1e-10


@pytest.mark.parametrize("p,l", [(0, 1), (0, -2), (1, 1), (1, -3), (2, 2)])
def test_lg_from_hg_coefficients_reproduces_the_mode(p, l):
    w0 = 1.0
    x, X, Y = _grid(201, 6.0)
    dA = (x[1] - x[0]) ** 2
    c = PX.lg_hg_coefficients(p, l)
    N = 2 * p + abs(l)
    for z in (0.0, 0.8 * PX.rayleigh(K, w0)):
        ref = PX.lg(p, l, X, Y, z, K, w0)
        assert np.max(np.abs(PX.hg_sum(c, X, Y, z, K, w0) - ref)) < 1e-12
        # an independent route: the overlap integrals <HG_{N-k,k} | LG>
        ov = np.array([np.vdot(PX.hg(N - kk, kk, X, Y, z, K, w0), ref) * dA for kk in range(N + 1)])
        assert np.max(np.abs(ov - c)) < 1e-10
    # negative control: without the factors i^k the sum is the diagonal HG mode, not the LG mode
    bare = PX.hg_sum(np.real(c / 1j ** np.arange(N + 1)), X, Y, 0.0, K, w0)
    assert np.max(np.abs(bare - PX.lg(p, l, X, Y, 0.0, K, w0))) > 0.1


def test_diagonal_hg_and_the_astigmatic_converter():
    w0 = 1.0
    x, X, Y = _grid(161, 5.0)
    s2 = math.sqrt(2.0)
    for n, m in [(1, 0), (2, 1), (1, 3), (2, 2)]:
        d = PX.diagonal_hg_coefficients(n, m)
        turned = PX.hg(n, m, (X - Y) / s2, (X + Y) / s2, 0.0, K, w0)
        assert np.max(np.abs(PX.hg_sum(d, X, Y, 0.0, K, w0) - turned)) < 1e-12
        # the pi/2 converter turns the diagonal HG_{n,m} into (-1)^min(n,m) LG_{min(n,m), m-n}
        out = PX.hg_sum(PX.mode_converter(d, math.pi / 2), X, Y, 0.0, K, w0)
        p, l = min(n, m), m - n
        assert np.max(np.abs(out - (-1) ** p * PX.lg(p, l, X, Y, 0.0, K, w0))) < 1e-12
    # the pi converter turns LG_{p,l} into LG_{p,-l} (image inversion), at any z
    z = 0.6 * PX.rayleigh(K, w0)
    for p, l in [(0, 2), (1, -1), (2, 3)]:
        out = PX.hg_sum(PX.mode_converter(PX.lg_hg_coefficients(p, l), math.pi), X, Y, z, K, w0)
        assert np.max(np.abs(out - PX.lg(p, -l, X, Y, z, K, w0))) < 1e-12
        assert np.max(np.abs(out - PX.lg(p, l, X, Y, z, K, w0))) > 0.1  # it did change the mode


@pytest.mark.parametrize("p,l", [(0, 1), (1, 2), (2, -3)])
def test_fresnel_propagation_of_the_waist_spectrum_is_the_closed_form(p, l):
    w0 = 2.0
    fn, qmax = B.lg_waist_spectrum(p, l, w0)
    r = np.linspace(0.0, 4.0 * w0, 17)
    for z in (0.0, 0.4 * PX.rayleigh(K, w0), 2.5 * PX.rayleigh(K, w0)):
        v, err = PX.fresnel_vortex(fn, l, K, r, z, qmax)
        assert np.max(np.abs(v - PX.lg(p, l, r, 0 * r, z, K, w0))) < 1e-13 and err < 1e-13


def test_fresnel_table_equals_the_closed_form():
    p, l, w0 = 1, -2, 1.5
    fn, qmax = B.lg_waist_spectrum(p, l, w0)
    zr = PX.rayleigh(K, w0)
    r = np.linspace(0, 6 * w0, 50)
    z = np.linspace(-2 * zr, 2 * zr, 9)
    T = PX.fresnel_table(fn, l, K, r, z, qmax)
    Z, R = np.meshgrid(z, r, indexing="ij")
    assert np.max(np.abs(T - PX.lg(p, l, R, 0 * R, Z, K, w0))) < 1e-13


@pytest.mark.parametrize("p,l", [(0, 1), (0, -1), (1, 2), (0, 3), (2, -4)])
def test_oam_per_photon_of_the_sampled_field_is_l(p, l):
    w0 = 1.0
    for z in (0.0, 1.3 * PX.rayleigh(K, w0)):
        w = float(PX.params(z, K, w0)[0])
        x, X, Y = _grid(256, 7.0 * w)
        U = PX.lg(p, l, X, Y, z, K, w0)
        assert abs(B.scalar_oam_per_photon(U, x, x) - l) < 1e-10


def test_oam_per_photon_negative_controls():
    w0 = 1.0
    x, X, Y = _grid(256, 7.0)
    a, b = PX.lg(0, 1, X, Y, 0, K, w0), PX.lg(0, -1, X, Y, 0, K, w0)
    assert abs(B.scalar_oam_per_photon(a + b, x, x)) < 1e-10  # a standing azimuthal wave: no OAM
    assert abs(B.scalar_oam_per_photon(np.abs(a), x, x)) < 1e-10  # the phase removed: no OAM
    two = PX.lg(0, 2, X, Y, 0, K, w0) + PX.lg(0, 0, X, Y, 0, K, w0)
    assert abs(B.scalar_oam_per_photon(two, x, x) - 1.0) < 1e-10  # half the photons with 2, half with 0


@pytest.mark.parametrize("p,l", [(0, 0), (2, 0), (1, 2), (0, -3)])
def test_gouy_phase_measured_on_the_exactly_propagated_field(p, l):
    """The exact field (order-l Hankel route of the LG waist) measured on the axis (l = 0) or on the ring
    r = w(z)/sqrt2 (its azimuthal Fourier coefficient of order l): arg[U e^{-ikz}] = rho^2 z/z_R - (2p+|l|+1) psi,
    rho = r / w(z), up to the paraxial error O((lambda/w0)^2) (w0 = 20 lambda here)."""
    w0 = 20.0
    zr = PX.rayleigh(K, w0)
    fn, qmax = B.lg_waist_spectrum(p, l, w0)
    beam = B.VortexBeam(l, K, fn, qmax)
    for z in (0.5 * zr, zr, 3.0 * zr):
        w = float(PX.params(z, K, w0)[0])
        rho = 0.0 if l == 0 else 1 / math.sqrt(2)
        U = complex(beam.scalar(rho * w, z)[0]) * np.exp(-1j * K * z)
        meas = np.angle(U)  # the radial factor is positive at rho = 0 and at rho = 1/sqrt2 for these (p, l)
        ref = rho * rho * z / zr - (2 * p + abs(l) + 1) * math.atan(z / zr)
        assert abs(np.angle(np.exp(1j * (meas - ref)))) < 1e-3, (z, meas, ref)
        wrong = rho * rho * z / zr - (2 * p + abs(l)) * math.atan(z / zr)  # negative control: Gouy off by one
        assert abs(np.angle(np.exp(1j * (meas - wrong)))) > 0.4


def test_angular_spectrum_matches_the_closed_form_with_paraxial_error_lambda_over_w0_squared():
    """The exact angular-spectrum propagation (FFT) of the sampled LG waist against the paraxial closed form at
    z = z_R: the difference falls as (lambda/w0)^2; the same FFT against the order-l Hankel route (two exact
    methods) agrees to the FFT window's error (3e-9 of the peak with the window padded 4 times; 2e-8 with 2)."""
    p, l = 1, 2
    errs = []
    for w0 in (1.5, 3.0):
        n, dx = 256, w0 / 10
        x = (np.arange(n) - n // 2) * dx
        X, Y = np.meshgrid(x, x, indexing="ij")
        zr = PX.rayleigh(K, w0)
        U = AS.propagate_field(PX.lg(p, l, X, Y, 0.0, K, w0), dx, K, zr, pad=4, check=True)
        ref = PX.lg(p, l, X, Y, zr, K, w0) * np.exp(1j * K * zr)
        peak = np.max(np.abs(ref))
        errs.append(np.max(np.abs(U - ref)) / peak)
        # two exact routes: FFT against the Hankel route at points of the row y = 0
        fn, qmax = B.lg_waist_spectrum(p, l, w0)
        sel = slice(n // 2 - 30, n // 2 + 31, 6)
        hk = B.VortexBeam(l, K, fn, qmax).scalar(np.abs(x[sel]), zr) * np.exp(1j * l * np.angle(x[sel] + 0j))
        assert np.max(np.abs(U[sel, n // 2] - hk)) / peak < 1e-8  # the FFT window's error (3e-9 measured)
        # negative control: against the closed form with the Gouy phase reversed
        bad = ref * np.exp(2j * PX.gouy(2 * p + abs(l), zr, K, w0))
        assert np.max(np.abs(U - bad)) / peak > 0.5
    ratio = errs[0] / errs[1]
    assert 3.4 < ratio < 4.6, (errs, ratio)
    assert errs[1] < 0.03  # measured 2026-11-04: 0.100 at w0 = 1.5 lambda, 0.0251 at 3 lambda (LG_{1,2}, z = z_R)


@pytest.mark.parametrize("p,l", [(0, 2), (1, 1), (0, -3)])
def test_traced_flow_lines_follow_the_closed_form_spiral(p, l):
    w0 = 1.5
    zr = PX.rayleigh(K, w0)
    a = np.linspace(0, 2 * math.pi, 6, endpoint=False) + 0.3
    r0 = 0.8 * w0 if p == 0 else 0.45 * w0  # inside the first ring for p = 1 (L_1^1 has a node at 2r^2/w^2 = 2)
    starts = np.stack([r0 * np.cos(a), r0 * np.sin(a), np.full(6, -zr)], axis=1)
    lines = B.trace_lines(lambda xx, yy, zz: PX.current(p, l, xx, yy, zz, K, w0), starts, 2 * zr, 300)
    zs = lines[0, :, 2]
    worst = 0.0
    for i in range(6):
        xr, yr = PX.flow_line(l, r0, float(a[i]), -zr, zs, K, w0)
        worst = max(worst, float(np.max(np.hypot(lines[i, :, 0] - xr, lines[i, :, 1] - yr))))
    assert worst < 2e-6 * w0, worst
    xr, yr = PX.flow_line(-l, r0, float(a[0]), -zr, zs, K, w0)  # negative control: the opposite twist
    assert np.max(np.hypot(lines[0, :, 0] - xr, lines[0, :, 1] - yr)) > 0.2 * w0


@pytest.mark.parametrize("p,l", [(0, 3), (1, -2)])
def test_extracted_equiphase_surfaces_are_the_closed_form_helicoids(p, l):
    w0 = 1.2
    zr = PX.rayleigh(K, w0)
    z = np.linspace(-zr, zr, 41)
    r = np.linspace(0.3, 1.4, 10) * w0
    phi = np.linspace(0, 2 * math.pi, 256, endpoint=False)
    Z, R, P = np.meshgrid(z, r, phi, indexing="ij")
    U = PX.lg(p, l, R * np.cos(P), R * np.sin(P), Z, K, w0) * np.exp(1j * K * Z)
    for phase0 in (0.0, 1.1):
        pos, tri = B.isophase_sheets(U * np.exp(-1j * phase0), B.cylinder_coords(r, phi, z))
        rr, ph, zz = np.hypot(pos[:, 0], pos[:, 1]), np.arctan2(pos[:, 1], pos[:, 0]), pos[:, 2]
        ref = PX.helix_phi(p, l, rr, zz, K, w0, phase0)  # (|l|, n)
        d = np.min(np.abs(np.angle(np.exp(1j * (ph[None] - ref)))), axis=0)
        assert np.max(d) < 1e-9, np.max(d)
        sheets_ok = len(tri) >= 0.9 * 2 * abs(l) * (len(z) - 1) * (len(r) - 1)
        assert sheets_ok, (len(tri), 2 * abs(l) * (len(z) - 1) * (len(r) - 1))
    ref = PX.helix_phi(p, l, rr, zz, K, w0, phase0 + math.pi / 2)  # negative control: another phase
    assert np.max(np.min(np.abs(np.angle(np.exp(1j * (ph[None] - ref)))), axis=0)) > 0.3


def test_field_current_of_any_field_and_the_shared_gaussian_parameters():
    """Review B8-beams, O12: the paraxial current of any field by differences (``field_current``, used by v16 for the
    Fresnel field behind a plate) against the LG mode's current from its own gradient (``current``), with and without
    the carrier e^{ikz} (it drops out); a wrong k is off (negative control). The Gaussian parameters are those of
    ``theories.approx.gaussian_beam`` (one definition), and ``fresnel_table_nodes`` is the node count the table uses."""
    from lfphys.theories.approx import gaussian_beam as GB
    p, l, w0 = 1, 2, 1.7
    x, X, Y = _grid(7, 2.5)
    z = 0.6 * PX.rayleigh(K, w0)
    ref = PX.current(p, l, X, Y, z, K, w0)
    for carrier in (False, True):
        fn = (lambda a, b, c: PX.lg(p, l, a, b, c, K, w0) * (np.exp(1j * K * c) if carrier else 1.0))  # noqa: E731
        j = PX.field_current(fn, X, Y, np.full_like(X, z), K, w0 / 400)
        assert np.max(np.abs(j - ref)) < 1e-9 * np.max(np.abs(ref)), carrier
    j2 = PX.field_current(lambda a, b, c: PX.lg(p, l, a, b, c, K, w0), X, Y, np.full_like(X, z), 1.1 * K, w0 / 400)
    assert np.max(np.abs(j2[:2] - ref[:2])) > 1e-2 * np.max(np.abs(ref[:2]))
    assert PX.rayleigh is GB.rayleigh
    zz = np.linspace(-3, 3, 7)
    assert np.allclose(PX.params(zz, K, w0)[0], GB.width(zz, K, w0), rtol=0, atol=0)
    fn, qmax = B.lg_waist_spectrum(0, l, w0)
    r, zt = np.linspace(0, 6, 40), np.linspace(-2, 2, 5)
    nq = PX.fresnel_table_nodes(l, K, 6.0, 2.0, qmax)
    assert nq % 16 == 0 and nq >= 16 * 16
    T = PX.fresnel_table(fn, l, K, r, zt, qmax)  # the table itself still agrees with the closed form
    Z, R = np.meshgrid(zt, r, indexing="ij")
    assert np.max(np.abs(T - PX.lg(0, l, R, 0 * R, Z, K, w0))) < 1e-10
