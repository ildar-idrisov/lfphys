# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The vectorised transfer matrices (review UX-ui U3) against the sequential route they replaced and closed forms.

``transfer.chain`` multiplies the slices' 2x2 matrices pairwise in log2(n) vectorised levels; before, each of the n
slices was one Python step, and the quantum playground (p02) spent 18-60 s per scene change re-tuning its absorbers
through 440 000 such steps. The second method here is that sequential loop, copied verbatim from the version before
the change (``_sequential_profile``): the two must agree to rounding (the products are the same, only associated
differently; each partial product is normalised in both). The scene's vectorised reflections over many absorber
strengths must equal one call per strength, and the edge layers' ramp must equal ``schrodinger_nd.layer_reflection``.
"""

from __future__ import annotations

import math
import time

import numpy as np
import pytest

from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S
from lfphys.core.quantum import transfer


def _sequential_profile(E, V, x0, x1, n_slices, m=1.0, hbar=1.0):
    """The route of ``transmission_profile`` before review UX-ui U3: one matrix product per slice (the reference)."""
    E = np.atleast_1d(np.asarray(E, float)).astype(complex)
    edges = np.linspace(x0, x1, n_slices + 1)
    h = (x1 - x0) / n_slices
    Vs = np.concatenate([[V(x0 - 1.0)], V(0.5 * (edges[1:] + edges[:-1])), [V(x1 + 1.0)]])
    k = np.sqrt(2 * m * (E[:, None] - Vs[None, :])) / hbar
    k = np.where(np.abs(k) == 0, 1e-30, k)
    M00 = np.ones(len(E), complex); M01 = np.zeros(len(E), complex)  # noqa: E702
    M10 = np.zeros(len(E), complex); M11 = np.ones(len(E), complex)  # noqa: E702
    S_ = np.zeros(len(E))
    for j in range(len(edges)):
        (a00, a01, a10, a11), sj = transfer._step(k[:, j], k[:, j + 1], 0.0 if j == 0 else h)
        M00, M01, M10, M11 = (M00 * a00 + M01 * a10, M00 * a01 + M01 * a11,
                              M10 * a00 + M11 * a10, M10 * a01 + M11 * a11)
        mx = np.maximum.reduce([np.abs(M00), np.abs(M01), np.abs(M10), np.abs(M11)])
        M00, M01, M10, M11 = M00 / mx, M01 / mx, M10 / mx, M11 / mx
        S_ = S_ + sj + np.log(mx)
    kin, kout = k[:, 0], k[:, -1]
    with np.errstate(under="ignore", invalid="ignore", divide="ignore"):
        T = np.where(np.abs(kout.imag) < 1e-12 * np.abs(kout), (kout.real / kin.real) * np.exp(-2 * S_) / np.abs(M00) ** 2,
                     0.0)
    return T.real, np.abs(M10 / M00) ** 2


def test_chain_is_the_ordered_product():
    """Random complex matrices, odd and even counts: the pairwise product equals the left-to-right one to rounding,
    the factors e^{s_j} go into the exponent, and a product that overflows a double (entries ~1e600) is carried."""
    rng = np.random.default_rng(3)
    for n in (1, 2, 3, 7, 16, 33):
        A = rng.normal(size=(5, n, 2, 2)) + 1j * rng.normal(size=(5, n, 2, 2))
        s = rng.normal(size=(5, n))
        P = np.tile(np.eye(2, dtype=complex), (5, 1, 1))
        logs = np.zeros(5)
        for j in range(n):
            P = P @ A[:, j]
            mx = np.max(np.abs(P), axis=(1, 2))
            P, logs = P / mx[:, None, None], logs + np.log(mx) + s[:, j]
        p00, p01, p10, p11, S_ = transfer.chain(A[..., 0, 0], A[..., 0, 1], A[..., 1, 0], A[..., 1, 1], s)
        got = np.stack([np.stack([p00, p01], -1), np.stack([p10, p11], -1)], -2) * np.exp(S_ - logs)[:, None, None]
        assert np.max(np.abs(got - P)) < 1e-13 * n
    big = np.full(2000, 1e300 + 0j)  # 2000 factors of 1e300: e^S = 1e600000, far beyond a double
    p00, _, _, _, S_ = transfer.chain(big, np.zeros(2000), np.zeros(2000), big)
    assert abs(p00) == 1.0 and S_ == pytest.approx(2000 * 300 * math.log(10), rel=1e-12)


CASES = [
    ("rectangular barrier", np.linspace(0.2, 2.5, 40), lambda x: np.where((x >= 0) & (x < 2.0), 1.0, 0.0), 0.0, 2.0,
     1),
    ("Poschl-Teller", np.linspace(0.2, 2.5, 40), lambda x: 1.0 / np.cosh(np.asarray(x, float)) ** 2, -15.0, 15.0, 2000),
    ("absorbing ramp", np.linspace(0.05, 5.0, 9),
     lambda x: -1j * 0.5 * np.clip(np.asarray(x) / 6.0, 0, 1) ** 2 * ((np.asarray(x) > 0) & (np.asarray(x) <= 6.0)),
     0.0, 6.0, 2000),
    ("thick barrier", np.array([0.5]), lambda x: np.where((x > 0) & (x < 2000.0), 1.0, 0.0), 0.0, 2000.0, 400),
    ("wide sharp barrier (v03)", np.linspace(0.5, 1.4, 13),
     lambda x: 0.5 * (np.tanh(np.asarray(x) / 0.02) - np.tanh((np.asarray(x) - 10.0) / 0.02)), -0.2, 10.2, 3000),
]


@pytest.mark.parametrize("name,E,V,x0,x1,n", CASES, ids=[c[0] for c in CASES])
def test_profile_equals_the_sequential_route(name, E, V, x0, x1, n):
    T0, R0 = _sequential_profile(E, V, x0, x1, n)
    T1, R1 = transfer.transmission_profile(E, V, x0, x1, n, return_r=True)
    # rounding of n products of normalised matrices, associated differently: a few eps per level and per slice
    tol = 64 * n * np.finfo(float).eps
    assert np.all(np.abs(T1 - T0) <= tol * np.maximum(T0, 1e-300) + 1e-300), name
    assert np.all(np.abs(R1 - R0) <= tol * np.maximum(R0, 1e-300) + 1e-300), name


def test_closed_form_through_the_vectorised_route():
    E = np.linspace(0.2, 2.5, 40)
    T = transfer.transmission_profile(E, lambda x: np.where((x >= 0) & (x < 2.0), 1.0, 0.0), 0.0, 2.0, 1)
    assert np.allclose(T, [transfer.rectangular_barrier(e, 1.0, 2.0) for e in E], rtol=1e-10)


def test_negative_control_the_comparison_sees_a_wrong_product():
    """A product taken in the wrong order (the slices reversed: the wave enters from the other side of an asymmetric
    absorber) differs from the reference far beyond the tolerance of the comparison above."""
    E = np.linspace(0.05, 5.0, 9)
    ramp = lambda x: -1j * 0.5 * np.clip(np.asarray(x) / 6.0, 0, 1) ** 2 * ((np.asarray(x) > 0) & (np.asarray(x) <= 6.0))  # noqa: E731
    _, R0 = _sequential_profile(E, ramp, 0.0, 6.0, 2000)
    _, Rrev = transfer.transmission_profile(E, lambda x: ramp(6.0 - np.asarray(x)), 0.0, 6.0, 2000, return_r=True)
    assert np.max(np.abs(Rrev - R0) / R0) > 1.0  # the abrupt face reflects orders of magnitude more


def test_vectorised_route_is_faster():
    """The point of the change (U3): the sequential loop costs one Python step per slice."""
    E = np.linspace(0.05, 5.0, 4)
    ramp = lambda x: -1j * 0.5 * np.clip(np.asarray(x) / 6.0, 0, 1) ** 2 * ((np.asarray(x) > 0) & (np.asarray(x) <= 6.0))  # noqa: E731
    t0 = time.perf_counter()
    _sequential_profile(E, ramp, 0.0, 6.0, 4000)
    t_old = time.perf_counter() - t0
    t0 = time.perf_counter()
    transfer.transmission_profile(E, ramp, 0.0, 6.0, 4000)
    t_new = time.perf_counter() - t0
    assert t_new < 0.5 * t_old, (t_new, t_old)


def test_strengths_at_once_equal_one_call_each():
    """Detector and edge-layer reflections over a set of absorber strengths in one call (p02's choice of W0) equal one
    call per strength; the edge layers' ramp equals ``schrodinger_nd.layer_reflection``."""
    W0s = np.logspace(-1, 2, 7)
    ks, m = np.array([1.5, 2.0, 2.7]), 1.3
    det = Q.Detector([5.0, None], [9.0, None], 1.0, 0.8)
    R, T = det.reflection(ks, m, axis=0, strengths=W0s)
    for i, W in enumerate(W0s):
        r1, t1 = Q.Detector([5.0, None], [9.0, None], float(W), 0.8).reflection(ks, m, axis=0)
        assert np.allclose(R[i], r1, rtol=1e-12, atol=0) and np.allclose(T[i], t1, rtol=1e-12, atol=1e-300)
        Te, Re = transfer.transmission_profile(ks ** 2 / (2 * m), lambda x, W=W: -1j * W * Q.smooth_interval(
            np.asarray(x, float), 5.0, 9.0, 0.8), 5.0 - 6 * Q.edge_eps(0.8), 9.0 + 6 * Q.edge_eps(0.8), 4000, m,
            return_r=True)
        assert np.allclose(R[i], Re, rtol=1e-12) and np.allclose(T[i], Te, rtol=1e-12, atol=1e-300)
    lay = Q.EdgeLayers(width=8.0, strength=1.0)
    R, T = lay.reflection(ks, m, strengths=W0s)
    for i, W in enumerate(W0s):
        Rs, Ts = S.layer_reflection(ks, 8.0, float(W), m)
        assert np.allclose(R[i], Rs, rtol=1e-12) and np.allclose(T[i], Ts, rtol=1e-12, atol=1e-300)
    Rs, Ts = Q.EdgeLayers(width=8.0, strength=3.0).reflection(ks, m)
    assert Rs.shape == (3,) and np.allclose(Rs, S.layer_reflection(ks, 8.0, 3.0, m)[0], rtol=1e-12)
