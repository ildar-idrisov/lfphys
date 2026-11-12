# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Born probabilities from float traces at exactly-zero cells (review 2026-10-23, V7-1).

At perfectly (anti)correlated settings one joint probability Tr(rho Pi_a (x) Pi_b) is exactly 0; the float trace gives
+-1e-17. numpy's Generator.choice rejects a negative entry, so before the fix sample_pairs raised at about half of
such settings (photons a = b = 30 deg, spins a = b = 30 deg, spins a = 50, b = 230 deg)."""

import math

import numpy as np
import pytest

from lfphys.core.quantum import qubits as Q


def _spin(deg):
    r = math.radians(deg)
    return Q.projectors([math.sin(r), 0.0, math.cos(r)])


def _pol(deg):
    return Q.polarizer_projectors(math.radians(deg))


CASES = [(Q.PHI_PLUS, _pol, 30.0, 30.0, +1), (Q.PHI_PLUS, _pol, 30.0, 120.0, -1), (Q.SINGLET, _spin, 30.0, 30.0, -1),
         (Q.SINGLET, _spin, 50.0, 230.0, +1)]


@pytest.mark.parametrize("state,proj,a,b,sign", CASES)
def test_zero_cells_are_non_negative_and_sampling_works(state, proj, a, b, sign):
    P = Q.joint_probabilities(state, proj(a), proj(b))
    assert P.min() >= 0.0 and P.sum() == pytest.approx(1.0, abs=1e-15)
    rng = np.random.default_rng(30)
    iA, iB = Q.sample_pairs(state, proj(a), proj(b), 20000, rng)
    A, B = 1 - 2 * iA, 1 - 2 * iB
    assert np.all(A * B == sign)  # perfect (anti)correlation: the zero cells are never drawn
    assert abs(np.mean(A)) < 5 / math.sqrt(20000)


def test_all_half_degree_settings_with_a_zero_cell():
    """The reviewer's map: a = b over [0, 360) in half degrees, photons and spins; and the anti-correlated ones."""
    for state, proj, off in ((Q.PHI_PLUS, _pol, 0.0), (Q.PHI_PLUS, _pol, 90.0), (Q.SINGLET, _spin, 0.0),
                             (Q.SINGLET, _spin, 180.0)):
        for deg in np.arange(0.0, 360.0, 0.5):
            P = Q.joint_probabilities(state, proj(float(deg)), proj(float(deg) + off))
            assert P.min() >= 0.0


def test_measure_of_an_eigenstate_and_genuinely_negative_input():
    up = Q.ket(math.cos(0.3), math.sin(0.3))  # the + eigenstate of a polarizer at 0.3 rad
    rho = Q.dm(up)
    p = Q.measure(rho, Q.polarizer_projectors(0.3))
    assert p.min() >= 0.0 and p[0] == pytest.approx(1.0, abs=1e-15)
    p, k, post = Q.measure(rho, Q.polarizer_projectors(0.3), np.random.default_rng(1))
    assert k == 0
    # round-off is clipped; a negative "probability" beyond round-off is an invalid state and is refused
    assert Q.born_probabilities([0.5, 0.5 + 1e-17, -1e-17]).min() == 0.0
    with pytest.raises(ValueError):
        Q.born_probabilities([1.2, -0.2])
