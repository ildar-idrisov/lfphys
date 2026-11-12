# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Special relativity in 3+1 (lfphys.core.lorentz, plan P9) against closed forms and second routes: group properties,
the 2+1 module as the special case z = 0, the Wigner rotation by matrices against a closed form and against SL(2, C),
aberration and Doppler, the searchlight effect, the transformation of fields against the field tensor, light-time
images and Penrose's circle.

Tolerances: every quantity here is a product of a few exact matrices with entries up to gamma, so the round-off is a
few ulps times gamma^2 (gamma <= 20 in these draws: 1e-12 is a bound with margin; measured: <= 4e-15 at gamma <= 3)."""

import math

import numpy as np
import pytest

from lfphys.core import lorentz as L
from lfphys.core import relativity as R

RNG = np.random.default_rng(20261027)


def _velocities(n, bmax=0.95):
    d = RNG.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1)[:, None]
    return d * RNG.uniform(0.0, bmax, size=n)[:, None]


def test_boost_is_lorentz_and_inverts():
    v = _velocities(500, 0.998)
    B = L.boost(v)
    assert L.lorentz_defect(B) < 1e-12
    assert np.max(np.abs(L.boost(v) @ L.boost(-v) - np.eye(4))) < 1e-12
    assert np.max(np.abs(L.inverse(B) - np.linalg.inv(B))) < 1e-10
    # the frame's origin: x' = 0 along x = v t
    U = L.four_velocity(v)
    assert np.max(np.abs(np.einsum("nij,nj->ni", B, U)[:, 1:])) < 1e-12
    # gamma from |v|, near c too
    assert L.gamma_of([0.0, 0.0, 1 - 1e-12]) == pytest.approx(R.gamma(1 - 1e-12), rel=1e-15)
    with pytest.raises(ValueError):
        L.boost([0.6, 0.8, 0.0])


def test_2plus1_is_the_special_case():
    """Every 2+1 function of core.relativity equals the 3+1 one in the plane z = 0."""
    for _ in range(50):
        u2, v2 = _velocities(2, 0.9)[:, :2] * 0.99
        u3, v3 = np.r_[u2, 0.0], np.r_[v2, 0.0]
        assert np.max(np.abs(R.boost_matrix(u2, 1.0) - L.boost(u3)[:3, :3])) < 1e-15
        assert np.allclose(L.add_velocities(u3, v3)[:2], R.compose_velocities(v2, u2, 1.0), atol=1e-15)
        _, _, n, th = L.wigner_rotation(u3, v3)
        assert th * n[2] == pytest.approx(R.wigner_rotation_angle(u2, v2, 1.0), abs=1e-14)
        ns = np.array([[math.cos(0.7), math.sin(0.7)]])
        nl, D = L.aberrate(np.c_[ns, [0.0]], u3)
        assert np.allclose(nl[0, :2], R.aberrate(ns, u2, 1.0)[0], atol=1e-14)
        b = float(np.linalg.norm(u2))
        cos_lab = float(nl[0] @ u3) / b
        assert D[0] == pytest.approx(R.doppler_factor(b, cos_lab), rel=1e-13)


def test_decompose_rebuilds_any_transformation():
    v, ax = _velocities(300, 0.99), RNG.normal(size=(300, 3))
    an = RNG.uniform(0, math.pi, 300)
    Lm = L.rotation(ax, an) @ L.boost(v)
    w, Rm = L.decompose(Lm)
    assert np.max(np.abs(w - v)) < 1e-12
    assert np.max(np.abs(Rm - L.rot3(ax, an))) < 1e-12
    n, th = L.axis_angle(Rm)
    assert np.max(np.abs(th - an)) < 1e-12
    axn = ax / np.linalg.norm(ax, axis=1)[:, None]
    assert np.max(np.abs(n - axn)[an > 1e-6]) < 1e-9
    # near pi the axis keeps its sign
    n, th = L.axis_angle(L.rot3(ax, math.pi - 1e-10))
    assert np.max(np.abs(n - axn)) < 1e-9


def test_velocity_addition_by_matrices_and_inverse():
    u, v = _velocities(500), _velocities(500)
    w = L.add_velocities(u, v)
    wm, _ = L.decompose(L.boost(v) @ L.boost(u))
    assert np.max(np.abs(w - wm)) < 1e-13
    assert np.max(np.abs(L.add_velocities(u, L.relative_velocity(u, w)) - w)) < 1e-13
    assert np.all(np.linalg.norm(w, axis=1) < 1.0)


def test_wigner_rotation_three_routes():
    """The angle by matrices (decompose), by the closed form in the Lorentz factors, and by SL(2, C); the axis along
    u x v; the small-speed limit |u x v| / (2 c^2)."""
    u, v = _velocities(2000), _velocities(2000)
    w, Rm, n, th = L.wigner_rotation(u, v)
    assert np.max(np.abs(th - L.wigner_angle_closed_form(u, v))) < 1e-12
    cr = np.cross(u, v)
    assert np.min(np.einsum("ij,ij->i", n, cr / np.linalg.norm(cr, axis=1)[:, None])) > 1 - 1e-12
    A = L.sl2_boost(v) @ L.sl2_boost(u)
    Ar = A @ np.linalg.inv(L.sl2_boost(w))  # the SU(2) part
    assert np.max(np.abs(Ar @ Ar.conj().transpose(0, 2, 1) - np.eye(2))) < 1e-12
    assert np.max(np.abs(L.lorentz_of_sl2(Ar)[:, 1:, 1:] - Rm)) < 1e-12
    # small speeds
    a, b = np.array([1e-4, 0, 0]), np.array([0, 2e-4, 3e-5])
    _, _, n, th = L.wigner_rotation(a, b)
    assert th == pytest.approx(np.linalg.norm(np.cross(a, b)) / 2, rel=1e-7)
    # parallel boosts: no rotation
    _, _, _, th = L.wigner_rotation([0.3, 0.2, 0.1], [0.6, 0.4, 0.2])
    assert th < 1e-12


def test_double_cover():
    """A rotation by theta + 2 pi is the same SO(3) element but the opposite SU(2) element; SL(2, C) is a
    homomorphism onto the Lorentz group."""
    ax = RNG.normal(size=(40, 3))
    an = RNG.uniform(0, 2 * math.pi, 40)
    A1, A2 = L.sl2_rotation(ax, an), L.sl2_rotation(ax, an + 2 * math.pi)
    assert np.max(np.abs(A1 + A2)) < 1e-14
    assert np.max(np.abs(L.lorentz_of_sl2(A1) - L.lorentz_of_sl2(A2))) < 1e-14
    n, th = L.su2_axis_angle(A1)
    assert np.max(np.abs(th - an)) < 1e-12
    u, v = _velocities(40), _velocities(40)
    P, Q = L.sl2_boost(u) @ A1, L.sl2_boost(v)
    assert np.max(np.abs(L.lorentz_of_sl2(Q @ P) - L.lorentz_of_sl2(Q) @ L.lorentz_of_sl2(P))) < 1e-12


def test_aberration_and_doppler_closed_forms():
    b = 0.85
    th = np.linspace(0.0, math.pi, 181)
    ns = np.stack([np.cos(th), np.sin(th), np.zeros_like(th)], 1)
    nl, D = L.aberrate(ns, [b, 0.0, 0.0])
    assert np.max(np.abs(nl[:, 0] - (np.cos(th) + b) / (1 + b * np.cos(th)))) < 1e-14
    assert np.max(np.abs(np.linalg.norm(nl, axis=1) - 1)) < 1e-14
    assert np.max(np.abs(D - R.gamma(b) * (1 + b * np.cos(th)))) < 1e-13
    assert np.max(np.abs(D - L.doppler(nl, [b, 0.0, 0.0]))) < 1e-12
    # a source moving in any direction: aberration is a rotation-covariant map
    Rm = L.rot3([1.0, 2.0, -0.5], 0.9)
    nl2, D2 = L.aberrate(ns @ Rm.T, Rm @ np.array([b, 0.0, 0.0]))
    assert np.max(np.abs(nl2 - nl @ Rm.T)) < 1e-13 and np.max(np.abs(D2 - D)) < 1e-13


def test_searchlight_conserves_the_emitted_power():
    """For a source isotropic in its rest frame the power per lab time of emission integrates to the rest-frame power
    (D^3/gamma averages to 1 over the sphere); per time of reception D^4 averages to gamma^2 (1 + beta^2/3) (the
    integral of gamma^-4 (1 - beta mu)^-4 over mu). Gauss-Legendre with 400 nodes: exact for these rational integrands
    to round-off at beta <= 0.95."""
    for b in (0.1, 0.6, 0.95):
        mu, w = np.polynomial.legendre.leggauss(400)
        n = np.stack([mu, np.sqrt(1 - mu * mu), 0 * mu], 1)
        I4, I3 = L.searchlight(n, [b, 0.0, 0.0])
        g = R.gamma(b)
        assert 0.5 * np.sum(w * I3) == pytest.approx(1.0, rel=1e-12)
        # int D^4 dmu/2 = gamma^-4/(2) int (1 - b mu)^-4 dmu = gamma^-4 (1 + b^2/3) / (1 - b^2)^3 = gamma^2 (1 + b^2/3)
        assert 0.5 * np.sum(w * I4) == pytest.approx(g * g * (1 + b * b / 3), rel=1e-10)


def test_field_transformation_against_the_tensor():
    E, B = RNG.normal(size=(200, 3)), RNG.normal(size=(200, 3))
    for c in (1.0, 2.5):
        v = _velocities(200, 0.97) * c
        Ep, Bp = L.transform_fields(E, B, v, c)
        Lb = L.boost(v, c)
        Ft = Lb @ L.field_tensor(E, B, c) @ np.swapaxes(Lb, -1, -2)
        E2, B2 = L.fields_of_tensor(Ft, c)
        assert np.max(np.abs(E2 - Ep)) < 1e-11 * c and np.max(np.abs(B2 - Bp)) < 1e-11
        # the invariants E^2 - c^2 B^2 and E.B
        inv1 = np.sum(E * E, 1) - c * c * np.sum(B * B, 1)
        assert np.max(np.abs(np.sum(Ep * Ep, 1) - c * c * np.sum(Bp * Bp, 1) - inv1)) < 1e-9 * c * c
        assert np.max(np.abs(np.sum(Ep * Bp, 1) - np.sum(E * B, 1))) < 1e-10 * c
    # a pure magnetic field seen from a moving frame: E' = gamma v x B
    Ep, _ = L.transform_fields([0, 0, 0], [0, 0, 1.0], [0.6, 0, 0])
    assert np.allclose(Ep, [0, -1.25 * 0.6, 0], atol=1e-15)


def test_light_time_image():
    """The emission event lies on the past light cone of the observation and on the point's worldline; the image of a
    point at rest in a moving frame is the aberration of its direction in that frame (Terrell)."""
    x0, v = RNG.normal(size=(300, 3)) * 3, _velocities(300, 0.9)
    te, xe, d, D = L.apparent(x0, v, 0.7)
    assert np.max(np.abs(np.linalg.norm(xe, axis=1) - (0.7 - te))) < 1e-12
    assert np.max(np.abs(xe - (x0 + v * te[:, None]))) < 1e-12
    assert np.all(te <= 0.7)
    # observer moving with u: d is the aberrated lab direction; the Doppler factor from the two frequencies
    u = np.array([0.0, 0.5, 0.3])
    te2, xe2, d2, D2 = L.apparent(x0, v, 0.7, observer_v=u)
    k_lab = -xe2 / np.linalg.norm(xe2, axis=1)[:, None]
    # the photon travels along k_lab in the lab; in the observer's frame along aberrate(k_lab) with the observer as
    # "source" of the frame change: transform the null vector with boost(u)
    k4 = np.c_[np.ones(len(k_lab)), k_lab] @ L.boost(u).T
    assert np.max(np.abs(d2 + k4[:, 1:] / k4[:, :1])) < 1e-12
    g, gv = L.gamma_of(u), L.gamma_of(v)
    assert np.max(np.abs(D2 - g * (1 - k_lab @ u) / (gv * (1 - np.sum(k_lab * v, 1))))) < 1e-12


def test_penrose_circle():
    """The outline of a sphere (round in its rest frame) seen with light-time from the lab is a circle (Penrose 1959).
    Three checks (review B2-5): the outline directions are coplanar; each outline ray grazes the body: its emission
    point lies on the body (the contracted ellipsoid |x_perp|^2 + gamma^2 x_par^2 = r^2 about the centre at the emission
    time); and by brute force the light-time images of 40 000 points of the body's surface all fall inside that circle
    and reach its rim (the outline's size and position, not only its shape)."""
    rng = np.random.default_rng(5)
    for P, rad, v in (([3.0, 1.0, -0.5], 0.7, [0.6, 0.3, 0.1]), ([0.0, 5.0, 0.0], 1.5, [0.95, 0.0, 0.0]),
                      ([-2.0, 0.3, 4.0], 0.4, [0.0, -0.4, 0.85])):
        P, b = np.asarray(P), np.asarray(v)
        d = L.sphere_outline(P, rad, b, n=400)
        assert np.max(np.abs(np.linalg.norm(d, axis=1) - 1)) < 1e-13
        U, sv, Vt = np.linalg.svd(d - d.mean(0))
        assert sv[2] < 1e-12 * sv[0]
        cdir = Vt[2] * np.sign(Vt[2] @ d.mean(0))  # the circle's centre on the celestial sphere
        cos_k = float(np.mean(d @ cdir))
        assert np.max(np.abs(d @ cdir - cos_k)) < 1e-12
        # the grazing point: the foot of the perpendicular from T P on the line s T (d + v); emission at time -s
        gm = float(L.gamma_of(b))
        nv = b / np.linalg.norm(b)
        T = np.eye(3) + (gm - 1) * np.outer(nv, nv)
        m = (d + b) @ T.T
        s = (m @ (T @ P)) / np.sum(m * m, 1)
        r = s[:, None] * (d + b) - P  # emission point minus the centre at the emission time
        par = r @ nv
        on_body = np.sum(r * r, 1) - par**2 + gm**2 * par**2
        assert np.max(np.abs(on_body - rad**2)) < 1e-10 * rad**2
        # brute force: points of the body's surface at t = 0 (the rest-frame sphere contracted along v), imaged
        q = rng.normal(size=(40000, 3))
        q /= np.linalg.norm(q, axis=1)[:, None]
        Ti = np.eye(3) + (1 / gm - 1) * np.outer(nv, nv)
        X0 = P + (rad * q) @ Ti.T
        _, _, dimg, _ = L.apparent(X0, np.broadcast_to(b, X0.shape), 0.0)
        ang = np.arccos(np.clip(dimg @ cdir, -1, 1))
        kappa = math.acos(cos_k)
        assert ang.max() <= kappa + 1e-9 and ang.max() >= kappa - 2e-3 * kappa


def test_edges_are_refused_not_silent():
    """Review B2-8: a velocity sum that rounds to |w| >= c and an image of a point at the observer are refused with a
    reason, not returned as an impossible velocity or NaN."""
    with pytest.raises(ValueError):
        L.add_velocities([1 - 1e-9, 0, 0], [1 - 1e-9, 0, 0])
    with pytest.raises(ValueError):
        L.apparent([[0.5, 0.0, 0.0]], [[-0.5, 0.0, 0.0]], 1.0)  # at the origin at t = 1
    w = L.add_velocities([0.999999, 0, 0], [0.999999, 0, 0])  # still representable
    assert np.linalg.norm(w) < 1
