# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Slices of a 3-D field on planes of any orientation (owner, 2026-10-27) and the energy current of the scalar wave:
against the engine's other routes (transverse planes, axis-aligned slices), against the exact field without FFTs
(lfphys.core.optics.aperture_fields) and against closed forms (a plane wave; the power through every plane)."""

import math

import numpy as np
import pytest

from lfphys.core import geometry as G
from lfphys.core.optics import angular_spectrum as AS
from lfphys.core.optics import aperture_fields as AF

LAM = 1.0
K = 2 * math.pi / LAM


def _grid(n, dx):
    return (np.arange(n) - n // 2) * dx


def test_horizontal_planes_have_a_horizontal_u_and_v_into_the_depth():
    for n in ((0, -1, 0), (1, 0, 0), (0, 0, 1), (0.3, -0.8, 0.5), (-0.2, 0.1, -0.97)):
        p = G.Plane.horizontal(n, origin=(0.1, 0.2, 3.0))
        nn = np.asarray(n) / np.linalg.norm(n)
        assert abs(p.u[2]) < 1e-15 and np.allclose(p.normal, nn, atol=1e-12)
        assert p.v[2] >= -1e-12
    assert G.Plane.horizontal((0, -1, 0)).name == "xz" and G.Plane.horizontal((0, 0, 1)).name == "xy"


def test_plane_route_equals_the_slice_and_transverse_routes():
    n, dx = 96, LAM / 6
    x = _grid(n, dx)
    X, Y = np.meshgrid(x, x, indexing="ij")
    w = 1.0
    sampled = np.exp(-((X - 0.3) ** 2 + (Y + 0.2) ** 2) / w ** 2) * np.exp(1j * 0.8 * X)
    zs = np.linspace(0.0, 5.0, 11)
    c = x[n // 2 + 4]
    # y = c (normal -y: u = +x, v = +z), a sampled source
    s, U = AS.propagate_plane(sampled, dx, K, G.Plane.horizontal((0, -1, 0), (0.0, c, 0.0)), (-3.0, 3.0), zs,
                              check=True)
    ref = AS.propagate_slice(sampled, dx, K, zs, axis=1, at=c, check=True)
    idx = np.rint(s / dx).astype(int) + n // 2
    assert np.max(np.abs(U - ref[:, idx])) < 1e-12
    # transverse plane z = 2.5 (u = x, v = y): t on the y nodes
    s, U = AS.propagate_plane(sampled, dx, K, G.Plane.horizontal((0, 0, 1), (0.0, 0.0, 2.5)), (-2.0, 2.0), x[30:60],
                              check=True)
    ref = AS.propagate_field(sampled, dx, K, 2.5, check=True)
    idx = np.rint(s / dx).astype(int) + n // 2
    assert np.max(np.abs(U - ref[idx][:, 30:60].T)) < 1e-12
    # x = c (normal +x: u = +y, the source turned by 90 degrees): a spectral source (the Gaussian, shifted)
    spec = AS.Spectral((n, n), lambda qx, qy: AF.gaussian_spectrum(w)(qx, qy) * np.exp(-1j * (qx * 0.3 - qy * 0.2)))
    s, U = AS.propagate_plane(spec, dx, K, G.Plane.horizontal((1, 0, 0), (c, 0.0, 0.0)), (-3.0, 3.0), zs,
                              check=True)
    ref = AS.propagate_slice(spec, dx, K, zs, axis=0, at=c, check=True)
    idx = np.rint(s / dx).astype(int) + n // 2
    assert np.max(np.abs(U - ref[:, idx])) < 1e-11


def test_tilted_plane_equals_the_exact_field():
    """A plane tilted in every direction through the field of two rectangles (exact spectrum): at its grid points the
    field equals the Rayleigh-Sommerfeld integral (no FFTs) within the window's error, estimated by doubling the
    window on the same plane."""
    n, dx = 128, LAM / 4
    rects = [(-1.6, -0.6, -2.0, 2.0), (0.6, 1.6, -2.0, 2.0)]
    src = AS.Spectral((n, n), AF.rect_spectrum(rects))
    plane = G.Plane.horizontal((0.3, -0.8, 0.5), origin=(0.2, 0.1, 6.0))
    ts = np.linspace(-4.0, 4.0, 17)
    s, U = AS.propagate_plane(src, dx, K, plane, (-4.0, 4.0), ts, pad=8, check=True)
    s2, U2 = AS.propagate_plane(src, dx, K, plane, (-4.0, 4.0), ts, pad=16, check=True)
    est = 1.5 * np.nanmax(np.abs(U - U2))
    assert est < 1e-3
    for i in (0, 5, 8, 12, 16):
        for jj in (0, len(s) // 3, len(s) // 2, len(s) - 1):
            P = plane.to3d(s[jj], ts[i])
            ref = AF.rectangles_field(K, rects, float(P[2]), float(P[0]), float(P[1]))[0]
            assert abs(U[i, jj] - ref) <= est + 1e-9, (i, jj)


def test_planes_through_the_axis_of_a_round_source_agree_at_every_azimuth():
    n, dx, w = 96, LAM / 6, 1.2
    src = AS.Spectral((n, n), AF.gaussian_spectrum(w))
    zs = np.linspace(0.5, 6.0, 12)
    s0, U0 = AS.propagate_plane(src, dx, K, G.Plane.horizontal((0, -1, 0)), (-3.0, 3.0), zs, check=True)
    for phi in (17.0, 63.0, 140.0):
        a = math.radians(phi)
        p = G.Plane.horizontal((-math.sin(a), math.cos(a), 0.0))  # contains the axis, u at azimuth phi (+/-)
        s, U = AS.propagate_plane(src, dx, K, p, (-3.0, 3.0), zs, check=True)
        assert np.allclose(s, s0) and np.max(np.abs(U - U0)) < 1e-11
    # and the exact Hankel integral at a few points
    for i, jj in ((3, 10), (11, 20), (7, len(s0) // 2)):
        ref = AF.gaussian_field(K, w, zs[i], abs(s0[jj]))[0]
        assert abs(U0[i, jj] - ref) < 1e-7  # the window x2: grazing light of a waist ~lambda, measured 3e-8


def test_points_before_the_source_are_nan():
    n, dx = 64, LAM / 4
    src = AS.Spectral((n, n), AF.gaussian_spectrum(1.0))
    plane = G.Plane.horizontal((0, -0.6, -0.8), origin=(0.0, 0.0, 0.5))
    s, U = AS.propagate_plane(src, dx, K, plane, (-2.0, 2.0), np.linspace(-3, 3, 7), check=True)
    zt = 0.5 + np.linspace(-3, 3, 7) * plane.v[2]
    assert np.all(np.isnan(U[zt < 0])) and np.all(np.isfinite(U[zt >= 0]))


# --- the current -----------------------------------------------------------------------------------------------------
def test_current_of_a_plane_wave_is_its_direction():
    n, dx = 64, LAM / 4
    x = _grid(n, dx)
    qx = 2 * math.pi * 5 / (n * dx)
    U0 = np.outer(np.exp(1j * qx * x), np.ones(n))
    j, P = AS.propagate_current(U0, dx, K, [0.0, 3.0], pad=1, check=True)
    kz = math.sqrt(K * K - qx * qx)
    assert np.allclose(j[:, 0], qx / K, atol=1e-12) and np.allclose(j[:, 1], 0.0, atol=1e-12)
    assert np.allclose(j[:, 2], kz / K, atol=1e-12)
    assert np.allclose(P, kz / K * (n * dx) ** 2, rtol=1e-12)


def test_power_through_every_plane_is_conserved_and_equals_the_spectrum():
    n, dx = 96, LAM / 6
    rects = [(-1.0, 1.0, -0.6, 0.6)]
    src = AS.Spectral((n, n), AF.rect_spectrum(rects))
    j, P = AS.propagate_current(src, dx, K, [0.0, 0.5, 3.0, 9.0], pad=4, check=True)
    ref = AS.flux_of_spectrum(src, dx, K, pad=4)
    assert np.max(np.abs(P[1:] - ref)) < 1e-10 * ref  # z = 0 carries evanescent parts too: no flux, same P
    assert abs(P[0] - ref) < 1e-10 * ref


def test_current_of_a_gaussian_equals_the_derivatives_of_the_exact_field():
    """j = Im(U* grad U)/k against the exact Hankel integral and its exact derivatives in z and r (quadrature)."""
    n, dx, w = 128, LAM / 6, 1.0
    src = AS.Spectral((n, n), AF.gaussian_spectrum(w))
    z = 2.0
    j, _ = AS.propagate_current(src, dx, K, [z], pad=16, check=True)  # window x16: U within 1.6e-8 of the exact field
    x = _grid(n, dx)
    for i in (n // 2, n // 2 + 6, n // 2 - 13):
        r = abs(x[i])
        U = AF.gaussian_field(K, w, z, r)[0]
        dUz = AF.gaussian_field(K, w, z, r, deriv="z")[0]
        dUr = AF.gaussian_field(K, w, z, r, deriv="r")[0]
        assert j[0, 2, i, n // 2] == pytest.approx((np.conj(U) * dUz).imag / K, abs=5e-8)
        assert j[0, 0, i, n // 2] == pytest.approx((np.conj(U) * dUr).imag / K * np.sign(x[i]), abs=5e-8)
        assert abs(j[0, 1, i, n // 2]) < 1e-12


def test_derivatives_of_the_gaussian_reference_equal_its_differences():
    w, z, r, h = 0.9, 1.7, 0.6, 1e-3
    for d, f in (("z", lambda e: AF.gaussian_field(K, w, z + e, r)[0]),
                 ("r", lambda e: AF.gaussian_field(K, w, z, r + e)[0])):
        five = (-f(2 * h) + 8 * f(h) - 8 * f(-h) + f(-2 * h)) / (12 * h)  # error ~h^4 |U^(5)| / 30
        assert AF.gaussian_field(K, w, z, r, deriv=d)[0] == pytest.approx(five, abs=1e-7)
