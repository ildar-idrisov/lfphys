# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P10: planes, slices, modelling modes, and the 2-D / 3-D angular spectrum (exact transverse planes, the volume,
exact longitudinal slices) against an independent route (mpmath quadrature of the defining integral)."""

import math

import numpy as np
import pytest

from lfphys.core import geometry as G
from lfphys.core.optics import angular_spectrum as AS
from lfphys.core.optics import aperture_fields as AF

LAM = 1.0
K = 2 * math.pi / LAM


# --- planes --------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["xy", "xz", "yz"])
def test_presets_are_orthonormal_and_round_trip(name):
    p = G.Plane.preset(name, offset=0.7)
    R = p.rotation
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-15) and np.linalg.det(R) == pytest.approx(1.0, abs=1e-15)
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=50), rng.normal(size=50)
    P = p.to3d(a, b)
    a2, b2, d = p.to2d(P)
    assert np.allclose(a2, a, atol=1e-14) and np.allclose(b2, b, atol=1e-14) and np.allclose(d, 0, atol=1e-14)
    assert p.to2d(p.to3d(0, 0) + 2.0 * p.normal)[2] == pytest.approx(2.0)
    missing = {"xy": 2, "xz": 1, "yz": 0}[name]
    assert p.origin[missing] == pytest.approx(0.7)  # the offset is along the positive missing axis


def test_custom_plane_and_rotation_between_planes():
    p = G.Plane.from_normal((1.0, 2.0, 2.0), origin=(0.1, 0.2, 0.3))
    assert np.allclose(p.normal, np.array([1, 2, 2]) / 3, atol=1e-15)
    q = G.Plane.preset("xz")
    R = G.rotation_between(p, q)
    assert np.allclose(R @ np.asarray(p.u), q.u) and np.allclose(R @ p.normal, q.normal)
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-14)
    assert G.angle_between(G.Plane.preset("xy"), G.Plane.preset("xz")) == pytest.approx(math.pi / 2)
    # a 2-D model is unchanged by the plane it is placed in: in-plane vectors keep lengths and angles
    v1, v2 = p.vec_to3d(1.0, 0.5), p.vec_to3d(-0.3, 2.0)
    assert v1 @ v2 == pytest.approx(1.0 * -0.3 + 0.5 * 2.0, abs=1e-14)
    assert p.same_as(G.Plane.from_dict(p.as_dict())) and not p.same_as(q)


def test_slice_is_exact_on_grid_nodes_and_bounded_otherwise():
    g = G.Grid.uniform((16, 12, 10), (8.0, 6.0, 5.0))
    X, Y, Z = g.mesh()
    f = 1.5 * X - 0.25 * Y + 0.5 * Z + 0.1 * X * Y  # trilinear functions are interpolated exactly
    plane = G.Plane.preset("xz", offset=g.axes[1][3])
    vals, exact = G.slice_field(f, g, plane, g.axes[0], g.axes[2])
    assert exact and np.allclose(vals, f[:, 3, :])
    tilted = G.Plane.from_normal((0.3, 1.0, 0.2), origin=(0.1, -0.2, 0.05))
    a = np.linspace(-1.5, 1.5, 7)
    vals, exact = G.slice_field(f, g, tilted, a, a)
    P = tilted.to3d(*np.meshgrid(a, a, indexing="ij"))
    ref = 1.5 * P[..., 0] - 0.25 * P[..., 1] + 0.5 * P[..., 2] + 0.1 * P[..., 0] * P[..., 1]
    assert not exact and np.allclose(vals, ref, atol=1e-12)
    # a smooth non-linear field: the error stays within sum h^2 |f''| / 8
    q = np.sin(X) * np.cos(0.7 * Y) * np.exp(0.2 * Z)
    vals, _ = G.slice_field(q, g, tilted, a, a)
    refq = np.sin(P[..., 0]) * np.cos(0.7 * P[..., 1]) * np.exp(0.2 * P[..., 2])
    bound = G.interpolation_bound(g, (1.0 * math.exp(0.5), 0.49 * math.exp(0.5), 0.04 * math.exp(0.5)))
    assert np.nanmax(np.abs(vals - refq)) <= bound


def test_modelling_modes():
    full = G.Modelling("full3d")
    assert full.explorable(G.Plane.preset("yz", 3.0)) and not full.approximation and not full.approximations()
    xz = G.Plane.preset("xz")
    sl = G.Modelling("slices", [xz], exact=True, reason="угловой спектр точен на любой координатной плоскости")
    assert sl.explorable(G.Plane.preset("xz")) and not sl.explorable(G.Plane.preset("xy"))
    assert sl.describe()["note"].startswith("только заданные срезы, каждый точен")
    red = G.Modelling("slices", [xz], exact=False, reason="щель конечной длины считается как бесконечная")
    assert red.approximation and "ПРИБЛИЖЕНИЕ" in red.describe()["note"]
    with pytest.raises(ValueError):
        G.Modelling("slices", [])


def test_each_slice_carries_its_own_exactness():
    """Review B1-12: one approximate plane among exact ones is flagged alone, with its reason and label."""
    m = G.Modelling("slices", [G.Slice(G.Plane.preset("xz", 0.0), False, "щель принята бесконечной"),
                               G.Slice(G.Plane.preset("yz", 0.0)), G.Slice(G.Plane.preset("xy", 30.0))])
    assert m.approximation and not m.is_exact(G.Plane.preset("xz")) and m.is_exact(G.Plane.preset("xy", 30.0))
    assert m.approximations() == ["срез y = 0: щель принята бесконечной"]
    d = m.describe()
    assert [p["exact"] for p in d["planes"]] == [False, True, True]
    assert [p["label"] for p in d["planes"]] == ["y = 0", "x = 0", "z = 30"]
    assert "Остальные срезы точны" in d["note"]
    only = G.Modelling("slices", [G.Slice(G.Plane.preset("xz"), False, "приближение")])
    assert "Остальные" not in only.describe()["note"]


def test_geometry_edge_cases():
    """Review B1-16 and B1-3: a plane's name follows its axes; a one-node axis is refused with a message; Grid.uniform
    puts node i at (i - n//2) d for odd and even n, as the angular spectrum does."""
    assert G.Plane((0, 0, 0), (1, 0, 0), (0, 0, 1)).name == "xz"
    assert G.Plane.from_normal((1.0, 1.0, 0.0)).name == "custom"
    g = G.Grid.uniform((4, 1, 4), (4.0, 1.0, 4.0))
    with pytest.raises(ValueError, match="two nodes"):
        G.slice_field(np.zeros(g.shape), g, G.Plane.preset("xz"), [0.0], [0.0])
    for n in (5, 6):
        assert np.allclose(G.Grid.uniform(n, float(n)).axes[0], np.arange(n) - n // 2)
    ax = G.axial_plane(30.0)
    assert G._label(ax) == "через ось z, φ = 30°" and G._label(G.Plane.from_normal((0.3, 0.2, 1.0))) == \
        "произвольная плоскость"
    assert G.axial_plane(0.0).same_as(G.Plane.preset("xz")) and G.axial_plane(90.0).same_as(G.Plane.preset("yz"))


# --- the angular spectrum in 3-D -----------------------------------------------------------------------------------
def _gauss_on_axis(w, z):
    """U(0, 0, z) of U(r, 0) = exp(-r^2/w^2) from the defining integral (no FFT; lfphys.core.optics.aperture_fields)."""
    pytest.importorskip("mpmath")
    val, err = AF.gaussian_on_axis(K, w, z)
    assert err < 1e-12
    return val


@pytest.mark.parametrize("z", [3.0, 10.0])
def test_3d_on_axis_field_equals_the_defining_integral(z):
    """A Gaussian of waist 1.5 lambda (far from paraxial) on z = 0: the FFT route against the 1-D quadrature."""
    w, dx, n = 1.5, LAM / 8, 160
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-(X**2 + Y**2) / w**2)
    U = AS.propagate_field(U0, dx, K, z, pad=2, check=True)
    assert U[n // 2, n // 2] == pytest.approx(_gauss_on_axis(w, z), abs=2e-9)


def test_field_invariant_along_an_axis_reduces_exactly_to_2d():
    """A field independent of y: the 3-D propagation equals the 2-D one in every y (exact reduction by symmetry), and
    likewise for a field independent of x."""
    dx, n = LAM / 8, 128
    x = (np.arange(n) - n // 2) * dx
    u1 = np.exp(-(x / 1.2) ** 2) * (1 + 0.3 * np.cos(3 * x))
    ref = AS.propagate(u1, dx, K, 4.0, pad=2)
    # no padding along the invariant axis: the window is periodic there, so the field is truly invariant
    U3 = AS.propagate_field(np.outer(u1, np.ones(n)), dx, K, 4.0, pad=(2, 1), check=True)
    assert np.max(np.abs(U3 - ref[:, None])) < 1e-12
    U3t = AS.propagate_field(np.outer(np.ones(n), u1), dx, K, 4.0, pad=(1, 2), check=True)
    assert np.max(np.abs(U3t - ref[None, :])) < 1e-12


def test_slices_without_the_volume_equal_the_volume_and_interpolate_exactly():
    dx, n = LAM / 6, 96
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-((X - 0.3) ** 2 + (Y + 0.2) ** 2) / 1.0) * np.exp(1j * 0.8 * X)
    zs = np.linspace(0.0, 6.0, 7)
    vol = AS.propagate_volume(U0, dx, K, zs, check=True)
    j = n // 2 + 3
    s_y = AS.propagate_slice(U0, dx, K, zs, axis=1, at=x[j], check=True)  # the plane y = x[j]: field across x
    s_x = AS.propagate_slice(U0, dx, K, zs, axis=0, at=x[j], check=True)  # the plane x = x[j]: field across y
    assert np.max(np.abs(s_y - vol[:, :, j])) < 1e-12 and np.max(np.abs(s_x - vol[:, j, :])) < 1e-12
    # between nodes: the exact value of the band-limited field (direct sum over the spectrum as reference)
    at = x[j] + 0.37 * dx
    s_mid = AS.propagate_slice(U0, dx, K, [5.0], axis=1, at=at, check=True)[0]
    m = 256
    buf = np.zeros((m, m), complex)
    o = m // 2 - n // 2  # sample i at x = (i - n//2) dx (the convention; the odd-n test checks it independently)
    buf[o:o + n, o:o + n] = U0
    kx = 2 * math.pi * np.fft.fftfreq(m, dx)
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    kz = np.sqrt((K * K - KX**2 - KY**2).astype(complex))
    kz = np.where(kz.imag < 0, -kz, kz)
    B = np.fft.fft2(np.fft.ifftshift(buf)) * np.exp(1j * kz * 5.0)
    xs = x[n // 2 - 10:n // 2 + 10]
    direct = np.array([np.sum(B * np.exp(1j * (KX * xx + KY * at))) / m**2 for xx in xs])
    assert np.max(np.abs(s_mid[n // 2 - 10:n // 2 + 10] - direct)) < 1e-12


@pytest.mark.parametrize("n,pad", [(65, 2), (64, 2), (65, 1), (63, (2, 3))])
def test_slices_for_odd_and_even_n_against_an_independent_reference(n, pad):
    """Review B1-3: with an odd n and a padded window the slice route sat one sample off. Here the slice x = c (c off
    the nodes), the slice y = c and the transverse plane are compared with the Hankel integral of the Gaussian
    (mpmath, no FFT), at points off the axis."""
    pytest.importorskip("mpmath")
    w, dx, z = 1.2, LAM / 6, 2.0
    x = (np.arange(n) - n // 2) * dx  # the convention of the engine (Grid.uniform)
    assert np.allclose(G.Grid.uniform(n, n * dx).axes[0], x)
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-(X**2 + Y**2) / w**2)
    c = 0.37
    s_x = AS.propagate_slice(U0, dx, K, [z], axis=0, at=c, pad=pad, check=True)[0]  # x = c, across y
    s_y = AS.propagate_slice(U0, dx, K, [z], axis=1, at=-c, pad=pad, check=True)[0]  # y = -c, across x
    plane = AS.propagate_field(U0, dx, K, z, pad=pad, check=True)
    for j in (n // 2 - 3, n // 2, n // 2 + 2):
        ref = AF.gaussian_field(K, w, z, r=math.hypot(c, x[j]))[0]
        assert abs(s_x[j] - ref) < 1e-6 and abs(s_y[j] - ref) < 1e-6
        ref_node = AF.gaussian_field(K, w, z, r=math.hypot(x[n // 2 + 1], x[j]))[0]
        assert abs(plane[n // 2 + 1, j] - ref_node) < 1e-6


def test_negative_distance_is_refused():
    with pytest.raises(ValueError, match="z >= 0"):
        AS.propagate_field(np.ones((8, 8)), 0.1, K, -0.5)


def test_propagation_is_a_group():
    dx, n = LAM / 6, 192  # window +-16 lambda: the Gaussian (w = 3 lambda) is < 1e-12 at its edge after 2.5 lambda
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-(X**2 + Y**2) / 9.0)
    a = AS.propagate_field(AS.propagate_field(U0, dx, K, 1.0, pad=2, check=True), dx, K, 1.5, pad=2, check=True)
    b = AS.propagate_field(U0, dx, K, 2.5, pad=2, check=True)
    assert np.max(np.abs(a - b)) < 1e-11


def test_finite_slit_reduced_to_2d_is_an_approximation_that_shrinks_with_length():
    """Mode "chosen slices" with a reduced model: a slit of finite length L computed as an infinite one (2-D) on its
    central plane. The run must flag it; its error, measured against the exact 3-D slice, falls as L grows."""
    dx, n = LAM / 4, 128
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    zs = np.linspace(1.0, 8.0, 8)
    slit = np.where(np.abs(x) <= 1.0, 1.0, 0.0)
    ref2d = AS.propagate(slit, dx, K, zs, pad=2)
    errs = []
    for L in (4.0, 8.0, 14.0):
        U0 = np.where((np.abs(X) <= 1.0) & (np.abs(Y) <= L / 2), 1.0, 0.0)
        exact = AS.propagate_slice(U0, dx, K, zs, axis=1, at=0.0, check=True)
        errs.append(np.max(np.abs(exact - ref2d)) / np.max(np.abs(exact)))
    assert errs[0] > errs[1] > errs[2] > 0
    flag = G.Modelling("slices", [G.Plane.preset("xz")], exact=False,
                       reason=f"щель длиной L считается бесконечной: ошибка {errs[-1]:.1e} при L = 14λ")
    assert flag.approximation


def test_plane_cut_by_a_box():
    """The cut of a plane by a box (the slice planes of every 3-D world): every vertex of the polygon lies on the plane
    and on a face of the box; the polygon is convex and ordered; a plane outside the box is refused."""
    import numpy as np
    from lfphys.core import geometry as G
    box = ((-1.0, -2.0, 0.0), (1.0, 2.0, 5.0))
    rng = np.random.default_rng(7)
    for _ in range(50):
        n = rng.normal(size=3)
        n /= np.linalg.norm(n)
        o = np.array([0.0, 0.0, 2.5]) + rng.uniform(-0.5, 0.5, 3)
        pl, poly, s_rng, t_rng = G.plane_cut(o, n, box)
        P = G.plane_points(pl, poly[:, 0], poly[:, 1])
        pts = np.array([P[i, i] for i in range(len(poly))])  # the vertices themselves
        assert np.max(np.abs((pts - np.asarray(pl.origin)) @ pl.normal)) < 1e-12
        lo, hi = np.asarray(box[0]), np.asarray(box[1])
        on_face = np.min(np.minimum(np.abs(pts - lo), np.abs(pts - hi)), axis=1)
        assert np.max(on_face) < 1e-12 and np.all(G.inside_box(pts, box))
        ang = np.arctan2(poly[:, 1] - poly[:, 1].mean(), poly[:, 0] - poly[:, 0].mean())
        assert np.all(np.diff(ang) > 0)
        assert s_rng == (poly[:, 0].min(), poly[:, 0].max()) and t_rng == (poly[:, 1].min(), poly[:, 1].max())
    import pytest
    with pytest.raises(ValueError):
        G.plane_cut((0.0, 0.0, 9.0), (0.0, 0.0, 1.0), box)


def test_plane_cut_through_corners():
    """Planes through corners of the box (review B2-7): a face is cut as its 4 corners, a diagonal plane as a rectangle
    with 4 corners, the plane x + y + z = 0 as a hexagon, each corner once; a plane touching the box at one corner only
    does not cut it (refused)."""
    import numpy as np
    from lfphys.core import geometry as G
    box = ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))
    for o, n, k in (((1.0, 0.0, 0.0), (1.0, 0.0, 0.0), 4), ((-1.0, 0.0, 0.0), (1.0, 0.0, 0.0), 4),
                    ((0.0, 0.0, 1.0), (0.0, 0.0, -1.0), 4), ((0.0, 0.0, 0.0), (1.0, -1.0, 0.0), 4),
                    ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 6), ((1.0, 1.0, 1.0), (1.0, 1.0, 1.0), 1)):
        try:
            pl, poly, _, _ = G.plane_cut(o, n, box)
        except ValueError:
            assert k < 3
            continue
        assert len(poly) == k, (o, n, poly)
        assert len({(round(a, 9), round(b, 9)) for a, b in poly}) == k
