# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.elliptic against mpmath at 30 digits (an independent implementation in arbitrary precision) and
SciPy's Carlson functions.

Tolerances (u = 2^-53):
* R_F: at most ~12 duplications of three square roots, three products and sums of positive numbers (each a
  well-conditioned average) and a positive-weight polynomial: 32 u relative (measured 2026-10-29: <= 4u).
* F(phi|m) = sin(phi) R_F(...) + 2 j K: the R_F bound plus the reduction phi - j pi (absolute u |phi|, amplified by
  the integrand 1/sqrt(1 - m sin^2) <= max(1, 1/sqrt(1 - m))): 64 u relative + that term.
* sn, cn, dn by the AGM (0 <= m < 1): the argument reduced modulo 4K (absolute error <= 4 u |u| (1 + 1/K)), then
  phi_N = 2^N a_N u rounded (relative u) and halved N <= 12 times through arcsin steps whose derivative is <= 1 in
  the mean: absolute error <= 128 u (1 + |u|) (measured <= 8e-15 for |u| <= 20). For m < 0 the transformation with
  v = u sqrt(1 - m) divides by dn(v|mu) >= sqrt(1 - mu) = 1/sqrt(1 - m): the bound is multiplied by (1 - m) and
  taken at |v| (measured 3e-11 for m = -1000, |u| <= 20).
"""

import math

import mpmath as mp
import numpy as np
import pytest
from scipy import special as sp

from lfphys.core import elliptic as EL

U = 2.0 ** -53


@pytest.fixture(autouse=True)
def _dps():
    with mp.workdps(30):
        yield


def test_rf_against_mpmath_and_scipy():
    rng = np.random.default_rng(7)
    x = rng.uniform(0, 5, 300)
    y = rng.uniform(0, 5, 300)
    z = 10.0 ** rng.uniform(-8, 3, 300)
    x[:10] = 0.0
    got = EL.rf(x, y, z)
    ref = np.array([float(mp.elliprf(a, b, c)) for a, b, c in zip(x, y, z)])
    assert np.max(np.abs(got / ref - 1)) <= 32 * U
    assert np.max(np.abs(got / sp.elliprf(x, y, z) - 1)) <= 64 * U  # SciPy's own error adds its share


def test_complete_and_incomplete_first_kind():
    m = np.array([-1e4, -100.0, -1.0, -1e-3, 0.0, 0.3, 0.9, 1 - 1e-6, 1 - 1e-12])
    K = EL.ellipk(m)
    Kr = np.array([float(mp.ellipk(v)) for v in m])
    assert np.max(np.abs(K / Kr - 1)) <= 32 * U
    rng = np.random.default_rng(3)
    phi = rng.uniform(-9, 9, 400)
    mm = np.concatenate((rng.uniform(-50, 0, 200), rng.uniform(0, 0.999999, 200)))
    F = EL.ellipf(phi, mm)
    Fr = np.array([float(mp.ellipf(p, q)) for p, q in zip(phi, mm)])
    amp = np.maximum(1.0, 1.0 / np.sqrt(1.0 - np.minimum(mm, 0.999999)))
    tol = 64 * U * np.abs(Fr) + U * np.abs(phi) * amp * 4
    assert np.all(np.abs(F - Fr) <= tol)
    # K(m) = F(pi/2|m) up to fl(pi/2) = pi/2 - 6.1e-17 times the integrand 1/sqrt(1 - m) (4e-12 at m = 1 - 1e-12)
    # and F(phi + pi) = F(phi) + 2K
    dphi = float(mp.pi / 2 - mp.mpf(math.pi / 2))
    tol = 64 * U * np.abs(K) + abs(dphi) * np.maximum(1.0, 1.0 / np.sqrt(1.0 - np.minimum(m, 1 - 1e-12))) * 1.01
    assert np.all(np.abs(EL.ellipf(np.full(9, math.pi / 2), m) - K) <= tol)
    assert np.allclose(EL.ellipf(0.7 + math.pi, 0.5), EL.ellipf(0.7, 0.5) + 2 * EL.ellipk(0.5), rtol=64 * U)


@pytest.mark.parametrize("m", [0.0, 0.3, 0.9, 0.999999, 1 - 1e-9, 1 - 1e-11, 1 - 1e-14, 1.0])
def test_jacobi_functions_for_parameters_in_unit_interval(m):
    u = np.linspace(-20.0, 20.0, 81)
    sn, cn, dn = EL.ellipj(u, np.full_like(u, m))
    for name, got in (("sn", sn), ("cn", cn), ("dn", dn)):
        ref = np.array([float(mp.re(mp.ellipfun(name, v, m=m))) for v in u])
        assert np.all(np.abs(got - ref) <= 128 * U * (1 + np.abs(u))), name
    # identities hold to round-off
    assert np.allclose(sn ** 2 + cn ** 2, 1.0, atol=8 * U)
    assert np.allclose(dn ** 2 + m * sn ** 2, 1.0, atol=16 * U)


def test_cephes_ellipj_is_inaccurate_near_one_and_ours_is_not():
    """The reason for the own AGM (STATUS-worthy fact, measured): SciPy's Cephes ellipj switches to a first-order
    expansion in 1 - m above m = 1 - 1e-10, whose error grows with u."""
    m, u = 1 - 1e-11, 20.0
    ref = float(mp.re(mp.ellipfun("sn", u, m=m)))
    assert abs(sp.ellipj(u, m)[0] - ref) > 1e-8
    assert abs(EL.ellipj(u, m)[0] - ref) <= 128 * U * (1 + u)


@pytest.mark.parametrize("m", [-1000.0, -5.0, -0.3])
def test_jacobi_functions_for_negative_parameters(m):
    u = np.linspace(-20.0, 20.0, 41)
    sn, cn, dn = EL.ellipj(u, np.full_like(u, m))
    v = np.abs(u) * math.sqrt(1 - m)
    tol = 128 * U * (1 + v) * (1 - m)
    for name, got in (("sn", sn), ("cn", cn), ("dn", dn)):
        ref = np.array([float(mp.re(mp.ellipfun(name, x, m=m))) for x in u])
        assert np.all(np.abs(got - ref) <= tol), name


def test_complete_third_and_second_kind():
    for n, m in ((0.3, 0.5), (-2.0, -3.0), (0.9, 0.99), (-0.5, 0.0)):
        assert abs(EL.ellippi(n, m) / float(mp.ellippi(n, m)) - 1) <= 64 * U
    for m in (-4.0, 0.0, 0.7, 1 - 1e-9):
        assert abs(EL.ellipe(m) / float(mp.ellipe(m)) - 1) <= 64 * U


@pytest.mark.parametrize("m,dphi", [(1 - 1e-6, 1e-4), (1 - 1e-9, 1e-6), (1 - 1e-12, 1e-6), (1 - 1e-13, 1e-7),
                                    (1 - 1e-13, 3e-9), (1 - 1e-14, 1e-8), (1 - 1e-14, 0.0)])
def test_incomplete_first_kind_near_the_logarithmic_corner(m, dphi):
    """Review B5-K11: F(phi|m) for m -> 1 and phi -> pi/2 (the phases of rays grazing the critical curve). The second
    argument of R_F, 1 - m sin^2 phi, is formed as cos^2 phi + (1 - m) sin^2 phi; the formula 1 - m sin^2 phi lost
    2.7e-6 relative at m = 1 - 1e-13, phi = pi/2 - 3e-9. With phi = pi/2 - dphi exactly representable in the reduced
    range (no reduction by pi), the bound is the R_F bound plus sin, cos (one ulp each): 64 u relative."""
    phi = math.pi / 2 - dphi
    F = float(EL.ellipf(phi, m))
    ref = mp.ellipf(mp.mpf(phi), mp.mpf(m))
    assert abs(F - float(ref)) <= 64 * U * abs(float(ref)), (F, ref)
