# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The experimental bounds stored in lfphys.core.data, applied to the theories that cite them (review 2026-10-23, E13:
they were stored but no code used them)."""

import math

import pytest

from lfphys.core import data
from lfphys.core.constants import GM_SUN
from lfphys.theories.alternatives import local_hidden, scalar_tensor
from lfphys.theories.approx import ppn

R_SUN = 6.957e8  # m, IAU 2015 nominal solar radius


def _within(value, bound, k=2.0):
    centre, sigma = bound
    return abs(value - centre) <= k * sigma


def test_cassini_bounds_brans_dicke():
    """gamma - 1 = (2.1 +- 2.3) 1e-5 (Bertotti, Iess, Tortora 2003): GR (gamma = 1) agrees; Brans-Dicke needs
    omega > ~4e4 at 2 sigma (gamma - 1 = -1/(2 + omega))."""
    assert _within(0.0, data.CASSINI_GAMMA_MINUS_1)
    assert _within(scalar_tensor.ppn_gamma(4.0e4) - 1.0, data.CASSINI_GAMMA_MINUS_1)
    assert not _within(scalar_tensor.ppn_gamma(1.0e3) - 1.0, data.CASSINI_GAMMA_MINUS_1)
    lo = data.CASSINI_GAMMA_MINUS_1[0] - 2 * data.CASSINI_GAMMA_MINUS_1[1]
    assert 1.0 / -lo - 2.0 == pytest.approx(39998.0, rel=1e-6)


def test_vlbi_excludes_light_as_newtonian_corpuscles():
    """VLBI: gamma - 1 = (-1.6 +- 1.5) 1e-4. Corpuscular light deflects as gamma = 0 (half of GR): excluded by
    thousands of sigma; GR agrees."""
    full = ppn.deflection(GM_SUN, R_SUN, gamma=1.0)
    half = ppn.deflection(GM_SUN, R_SUN, gamma=0.0)
    assert math.degrees(full) * 3600 == pytest.approx(1.75, abs=0.01)
    gamma_corpuscle = 2 * half / full - 1
    assert _within(0.0, data.VLBI_GAMMA_MINUS_1)
    assert abs(gamma_corpuscle - 1 - data.VLBI_GAMMA_MINUS_1[0]) / data.VLBI_GAMMA_MINUS_1[1] > 1000


def test_hensen_violates_the_local_bound():
    """Hensen et al. 2015: S = 2.42 +- 0.20 exceeds the local bound |S| <= 2 by 2.1 sigma; the engine's local models
    reach at most 2 (the sign model at the spin-optimal angles) and sqrt(2) (the polarization model)."""
    S, dS = data.HENSEN_2015_S
    assert (S - 2.0) / dS == pytest.approx(2.1, abs=1e-12)
    a, a2, b, b2 = 0.0, math.pi / 2, math.pi / 4, 3 * math.pi / 4  # the singlet's optimal CHSH angles
    E = local_hidden.sign_model_E
    S_sign = E(a - b) - E(a - b2) + E(a2 - b) + E(a2 - b2)
    assert abs(S_sign) == pytest.approx(2.0, abs=1e-12)
    P = local_hidden.polarization_model_E
    aa, aa2, bb, bb2 = 0.0, math.pi / 4, math.pi / 8, 3 * math.pi / 8
    S_pol = P(aa, bb) - P(aa, bb2) + P(aa2, bb) + P(aa2, bb2)
    assert abs(S_pol) == pytest.approx(math.sqrt(2.0), abs=1e-12)
    assert S - 2 * dS > 2.0 - 1e-12  # the measurement lies beyond the local bound by 2 sigma


def test_codata_edition():
    """CODATA 2022 (scipy >= 1.15): m_e = 9.1093837139(28)e-31 kg, alpha^-1 = 137.035999177(21) (review E14)."""
    from scipy import constants as sc
    assert sc.m_e == 9.1093837139e-31
    assert 1 / sc.fine_structure == pytest.approx(137.035999177, abs=2e-9)
