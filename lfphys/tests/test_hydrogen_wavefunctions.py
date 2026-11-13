# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Hydrogen-like wave functions (plan P14.5): R_nl by the log-scaled Laguerre recurrence against the explicit power
series (an independent route with its own round-off bound), normalisation, the closed-form moments <r^k>, node counts,
the value at the origin, the scaling with Z and a, large n, the reduced-mass energies and the edges of the input."""

import math

import numpy as np
import pytest
from scipy import constants as sc

from lfphys.core.quantum import central3d as C, hydrogen as H

EPS = np.finfo(float).eps


def _rmax(n):
    return 2.0 * n * n + 40.0 * n  # e^{-r/n} r^{2n}: beyond this the tail is below 1e-20 for every n here


def test_recurrence_matches_the_series_within_both_round_off_bounds():
    """The series' bound (64 eps sum |terms|, it cancels for large rho and k) plus the log route's own: exp of a sum
    of logs of size S loses ~ S eps relatively, and the recurrence ~ k eps."""
    r = np.linspace(0.0, 200.0, 4001)
    for n, l in [(1, 0), (2, 0), (2, 1), (3, 2), (5, 1), (10, 3), (20, 0), (30, 10), (40, 3)]:
        R = H.radial(n, l, r)
        Rs, b = H.radial_series(n, l, r)
        rho = 2.0 * r / n
        S = np.abs(np.log(np.where(np.abs(R) > 0, np.abs(R), 1.0))) + rho + l * np.abs(np.log(np.where(rho > 0, rho, 1.0)))
        tol = b + 8 * EPS * (S + 4 * n) * np.abs(R) + 1e-300
        assert np.all(np.abs(R - Rs) <= tol), (n, l, np.max(np.abs(R - Rs) / tol))


@pytest.mark.parametrize("n,l", [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2), (6, 2), (12, 7), (30, 10), (60, 0),
                                 (100, 5), (150, 149)])
def test_normalised_and_mean_radius_closed_form(n, l):
    """int R^2 r^2 dr = 1 and <r> = (3n^2 - l(l+1))/2 by Gauss-Legendre panels (no overflow at n = 150: the product is
    formed in logarithms)."""
    R = lambda r: H.radial(n, l, r)  # noqa: E731
    panels = 400 if n <= 30 else 2000
    assert C.moment(R, 0, _rmax(n), panels) == pytest.approx(1.0, abs=1e-11)
    assert C.moment(R, 1, _rmax(n), panels) == pytest.approx(H.expectation(n, l, 1), rel=1e-11)


@pytest.mark.parametrize("n,l", [(1, 0), (2, 1), (3, 0), (4, 2), (5, 4), (7, 3)])
def test_moments_closed_forms(n, l):
    R = lambda r: H.radial(n, l, r)  # noqa: E731
    for k in (-2, -1, 2):
        assert C.moment(R, k, _rmax(n)) == pytest.approx(H.expectation(n, l, k), rel=1e-11), k


def test_orthogonality_in_n():
    for l in (0, 1, 3):
        for n1 in range(l + 1, l + 5):
            for n2 in range(n1 + 1, l + 6):
                r, w = C.radial_quadrature(_rmax(n2), 400)
                ov = float(np.sum(w * H.radial(n1, l, r) * H.radial(n2, l, r) * r * r))
                assert abs(ov) < 1e-13, (n1, n2, l, ov)


def test_node_counts_and_origin():
    """n - l - 1 radial nodes; R_n0(0) = 2 (Z/(n a))^(3/2); R_nl(0) = 0 for l > 0."""
    for n, l in [(1, 0), (2, 0), (3, 1), (5, 0), (8, 3), (20, 0), (20, 19)]:
        r = np.linspace(1e-6, _rmax(n), 200001)
        R = H.radial(n, l, r)
        big = np.abs(R) > 1e-12 * np.max(np.abs(R))  # the far tail underflows to signless zeros
        s = np.sign(R[big])
        assert int(np.sum(s[1:] != s[:-1])) == n - l - 1, (n, l)
    for n in (1, 2, 7, 40):
        assert float(H.radial(n, 0, 0.0, Z=3.0, a=0.5)) == pytest.approx(2 * (3.0 / (n * 0.5)) ** 1.5, rel=1e-13)
        assert float(H.radial(n, n - 1, 0.0)) == pytest.approx(0.0 if n > 1 else 2.0, abs=4 * EPS)


def test_scaling_with_charge_and_radius():
    r = np.linspace(0.0, 30.0, 301)
    for n, l in [(1, 0), (3, 2), (6, 1)]:
        a, Z = 0.37, 3.0
        assert np.allclose(H.radial(n, l, r, Z, a), (Z / a) ** 1.5 * H.radial(n, l, Z * r / a), rtol=1e-13, atol=0)
        assert H.expectation(n, l, 1, Z, a) == pytest.approx(a / Z * H.expectation(n, l, 1), rel=1e-15)


def test_energies_of_any_reduced_mass():
    """level(n, Z, mu) = -mu c^2 (Z alpha)^2 / (2 n^2): the electron with the proton's reduced mass is
    schrodinger_level; positronium (mu = m_e/2) has half the binding and twice the Bohr radius."""
    mu = H.reduced_mass(sc.m_e, sc.m_p)
    for n in (1, 2, 5):
        assert H.level(n, 1, mu) == pytest.approx(H.schrodinger_level(n, 1, sc.m_p), rel=1e-15)
    assert H.level(1, 1, H.reduced_mass(sc.m_e, sc.m_e)) == pytest.approx(0.5 * H.level(1), rel=1e-15)
    assert H.bohr_radius(sc.m_e) == pytest.approx(sc.physical_constants["Bohr radius"][0], rel=1e-9)
    assert H.hartree(sc.m_e) == pytest.approx(sc.physical_constants["Hartree energy"][0], rel=1e-9)
    assert H.reduced_mass(sc.m_e, math.inf) == sc.m_e


def test_orbital_labels_and_refused_inputs(ru):
    assert H.orbital(3, 2, 0, real=True).label == "3d_z²" and H.orbital(1, 0, 0).energy == -0.5
    assert H.orbital(2, 1, 0, Z=2.0).energy == -0.5
    for bad in ((0, 0, 0), (2, 2, 0), (2, -1, 0), (3, 1, 2)):
        with pytest.raises(ValueError):
            H.orbital(*bad)
    with pytest.raises(ValueError, match=r"need \|m\| ≤ l \(m = 2, l = 1\)") as e:
        H.orbital(3, 1, 2)
    assert ru(e.value.args[0]) == "нужно |m| ≤ l (m = 2, l = 1)"
    with pytest.raises(ValueError, match="closed forms exist only") as e:
        H.expectation(2, 1, 3)
    assert "в замкнутом виде" in ru(e.value.args[0])
    with pytest.raises(ValueError):
        H.radial_series(1, 1, 1.0)
