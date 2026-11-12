# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The exact series for a plane wave scattered by an infinite circular cylinder (``core.optics.cylinder``), checked
without trusting its formulas: the fields it builds satisfy the boundary conditions at the surface (continuity of the
axial field and of the tangential field of the other kind; zero tangential E on a PEC), the optical theorem
(Q_ext = Q_sca without absorption), the integral of the angular pattern equals Q_sca, the Rayleigh limit of a thin
cylinder follows from the radiation of a line dipole p = (m^2 - 1) pi a^2 E (TM), and the truncation is converged.
A second method is the FDTD solver itself (tests/test_fdtd_scattering.py)."""

import math

import numpy as np
import pytest

from lfphys.core.optics import cylinder as cy

CASES = [(1.5, 3.0), (2.0 + 0.3j, 3.0), (1.33, 0.7), (3.0 + 1.0j, 8.0), (0.7, 2.0)]


@pytest.mark.parametrize("m,x", CASES)
@pytest.mark.parametrize("pol", ["tm", "te"])
def test_boundary_conditions(m, x, pol):
    phi = np.linspace(0, 2 * np.pi, 13)
    eps = 1e-10
    out = cy.fields(m, x, pol, x * (1 + eps), phi)
    inn = cy.fields(m, x, pol, x * (1 - eps), phi)
    scale = np.abs(out["axial"]).max() + np.abs(out["azimuthal"]).max()
    assert np.max(np.abs(out["axial"] - inn["axial"])) < 1e-7 * scale
    assert np.max(np.abs(out["azimuthal"] - inn["azimuthal"])) < 1e-7 * scale * abs(complex(m)) ** 2


@pytest.mark.parametrize("pol", ["tm", "te"])
def test_pec_boundary(pol):
    for x in (0.5, 3.0, 10.0):
        f = cy.fields("pec", x, pol, x, np.linspace(0, 2 * np.pi, 9))
        tang = f["axial"] if pol == "tm" else f["azimuthal"]  # E_z (TM) or E_phi (TE) on the surface
        assert np.max(np.abs(tang)) < 1e-11, (x, np.max(np.abs(tang)))


@pytest.mark.parametrize("m,x", CASES + [("pec", 3.0)])
@pytest.mark.parametrize("pol", ["tm", "te"])
def test_optical_theorem_and_pattern_integral(m, x, pol):
    q = cy.efficiencies(m, x, pol)
    phi = np.linspace(0, 2 * np.pi, 4097)[:-1]
    integ = np.mean(cy.dsigma_dphi(m, x, pol, phi)) * 2 * np.pi / (2 * x)  # k = 1, a = x
    assert integ == pytest.approx(q["Qsca"], rel=1e-12)
    if isinstance(m, str) or complex(m).imag == 0:
        assert q["Qabs"] == pytest.approx(0.0, abs=1e-13 * q["Qext"])
    else:
        assert q["Qabs"] > 0


def test_rayleigh_limit_tm():
    """Q_sca -> (pi^2 x^3 / 8)(m^2 - 1)^2 for x -> 0 (a line dipole p = (m^2 - 1) pi a^2 E radiating omega^3 p^2 / 8
    per unit length), with a correction O(x^2 ln x) (the 2-D Green's function's logarithm: measured 1.9e-3, 5.7e-4,
    1.6e-4 at x = 0.02, 0.01, 0.005)."""
    m = 1.5
    r = [cy.efficiencies(m, x, "tm")["Qsca"] / (math.pi ** 2 * x ** 3 / 8 * (m * m - 1) ** 2) - 1
         for x in (0.02, 0.01, 0.005)]
    assert abs(r[2]) < 3e-4 and 3.0 < r[0] / r[1] < 4.0 and 3.0 < r[1] / r[2] < 4.0, r


@pytest.mark.parametrize("pol", ["tm", "te"])
def test_truncation_converged(pol):
    for m, x in CASES:
        c = cy.coefficients(m, x, pol)
        c2 = cy.coefficients(m, x, pol, nmax=len(c) + 20)
        assert np.max(np.abs(c2[len(c):])) < 1e-15 * np.max(np.abs(c))
        assert np.allclose(c2[:len(c)], c, rtol=0, atol=1e-15)
