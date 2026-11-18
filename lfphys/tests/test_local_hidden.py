# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.theories.alternatives.local_hidden, Gisin and Gisin's detection-loophole model (Phys. Lett. A 260, 323
(1999); EX2 §4.7): its Monte Carlo against its closed forms (the detected pairs' correlation -a.b, 75 % per side),
CH and J <= 0 at every setting sampled, CHSH = 2 sqrt 2 under fair sampling at the optimal angles. The sign and
polarisation models are tested in test_quantum.py and test_experimental_bounds.py."""

import math

import numpy as np
import pytest

from lfphys.core.quantum import qubits as Q
from lfphys.theories.alternatives import local_hidden as LH
from lfphys.tools import bell_stats as BS

rng = np.random.default_rng(1999)


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


@pytest.mark.parametrize("trial", range(4))
def test_detected_pairs_have_the_singlets_correlation(trial):
    a, b = _unit(rng.normal(size=3)), _unit(rng.normal(size=3))
    n = 400_000
    A, B = LH.gisin_gisin(a, b, n, rng)
    both = (A != 0) & (B != 0)
    E = np.mean(A[both] * B[both])
    ref = LH.gisin_gisin_E(a, b)
    assert ref == pytest.approx(-a @ b, abs=1e-15)
    assert abs(E - ref) < 5 * math.sqrt((1 - ref * ref) / both.sum())
    # every side fires in 75 % of the pairs, both in 50 %; outcomes of a single side are unbiased
    for X in (A, B):
        assert abs(np.mean(X != 0) - 0.75) < 5 * math.sqrt(0.75 * 0.25 / n)
        assert abs(np.mean(X == 1) - 0.375) < 5 * math.sqrt(0.375 * 0.625 / n)
    assert abs(both.mean() - 0.5) < 5 * math.sqrt(0.25 / n)
    assert LH.gisin_gisin_efficiency() == (0.75, 0.75)


def test_monte_carlo_against_the_closed_table():
    a, b = LH.poincare(0.2), LH.poincare(1.0)
    for state, nu in (("singlet", 0.0), ("phi_plus", 1 / 9)):
        n = 300_000
        A, B = LH.gisin_gisin(a, b, n, rng, state=state, no_outcome=nu)
        idx = {1: 0, -1: 1, 0: 2}
        counts = np.zeros((3, 3))
        np.add.at(counts, (np.vectorize(idx.get)(A), np.vectorize(idx.get)(B)), 1)
        t = LH.gisin_gisin_table(a, b, state, nu)
        assert t.sum() == pytest.approx(1.0, abs=1e-15)
        assert np.all(np.abs(counts / n - t) < 5 * np.sqrt(t * (1 - t) / n) + 1e-12)


def test_asymmetric_model_and_the_no_outcome_extension():
    """The asymmetric model: Alice fires in half the pairs, Bob always (their eq. (3)); with "no outcome at all" of
    probability 1/9 the two sides look independent, each with 8/9 x 3/4 = 2/3 (P(both) = (2/3)^2)."""
    n = 300_000
    a, b = _unit([0.3, 0.1, 1.0]), _unit([1.0, -0.2, 0.4])
    A, B = LH.gisin_gisin(a, b, n, rng, symmetric=False)
    assert abs(np.mean(A != 0) - 0.5) < 5 * math.sqrt(0.25 / n) and np.all(B != 0)
    both = A != 0
    assert abs(np.mean(A[both] * B[both]) + a @ b) < 5 * math.sqrt(1 / both.sum())
    A, B = LH.gisin_gisin(a, b, n, rng, no_outcome=1 / 9)
    ea, eb = LH.gisin_gisin_efficiency(1 / 9)
    assert ea == pytest.approx(2 / 3, abs=1e-15) and eb == pytest.approx(2 / 3, abs=1e-15)
    assert abs(np.mean(A != 0) - 2 / 3) < 5 * math.sqrt(2 / 9 / n)
    assert abs(np.mean((A != 0) & (B != 0)) - 4 / 9) < 5 * math.sqrt(4 / 9 * 5 / 9 / n)


def _gg_tables(angles, state="phi_plus", nu=0.0):
    """Two-detector tables ("+", "-", "0", "+-") of the model at the four setting pairs (no "+-": one outcome per
    side)."""
    out = []
    for a in angles[:2]:
        row = []
        for b in angles[2:]:
            t3 = LH.gisin_gisin_table(LH.poincare(a), LH.poincare(b), state, nu)
            t4 = np.zeros((4, 4))
            t4[:3, :3] = t3
            row.append(t4)
        out.append(row)
    return out


def test_ch_and_j_never_violated_while_chsh_under_fair_sampling_is():
    """At every setting sampled CH (Gisin and Gisin's (15)) and J are <= 0: CH = (1 - nu)(X - 4)/8 with |X| <= 2 sqrt
    2; at the CHSH angles the coincidences alone (fair sampling) give S = 2 sqrt 2: the local model «violates» CHSH
    through the detection loophole."""
    for _ in range(500):
        ang = rng.uniform(0, math.pi, 4)
        nu = rng.choice([0.0, 1 / 9])
        tabs = _gg_tables(ang, nu=nu)
        ch, j = BS.ch_value(tabs), BS.j_value(tabs)
        E = lambda x, y: LH.gisin_gisin_E(LH.poincare(x), LH.poincare(y), "phi_plus")  # noqa: E731
        X = E(ang[0], ang[2]) + E(ang[0], ang[3]) + E(ang[1], ang[2]) - E(ang[1], ang[3])
        assert ch == pytest.approx((1 - nu) * (X - 4) / 8, abs=1e-15)
        assert ch <= -(1 - nu) * (4 - 2 * math.sqrt(2)) / 8 + 1e-15 and j == pytest.approx(ch, abs=1e-15)
    # CHSH under fair sampling at the photons' CHSH angles (a, a', b, b') = (0, 45, 22.5, 67.5) degrees
    deg = math.pi / 180
    pairs = [(0, 22.5), (0, 67.5), (45, 22.5), (45, 67.5)]
    Es = [LH.gisin_gisin_E(LH.poincare(a * deg), LH.poincare(b * deg), "phi_plus") for a, b in pairs]
    assert Es[0] - Es[1] + Es[2] + Es[3] == pytest.approx(2 * math.sqrt(2), abs=1e-14)
    # the same from sampled pairs, counting coincidences only
    n = 200_000
    S, var = 0.0, 0.0
    for (a, b), s in zip(pairs, BS.CHSH_SIGNS):
        A, B = LH.gisin_gisin(LH.poincare(a * deg), LH.poincare(b * deg), n, rng, state="phi_plus")
        m = (A != 0) & (B != 0)
        cells = (np.sum((A == 1) & (B == 1)), np.sum((A == 1) & (B == -1)), np.sum((A == -1) & (B == 1)),
                 np.sum((A == -1) & (B == -1)))
        E, se, _ = BS.correlation(cells)
        S += s * E
        var += se * se
        assert m.sum() == sum(cells)
    assert abs(S - 2 * math.sqrt(2)) < 5 * math.sqrt(var)
    assert (S - 2) / math.sqrt(var) > 20  # a «violation» by a local model


def test_quantum_violates_where_the_model_cannot():
    """With the model's own 75 % the maximally entangled state does not violate J either (it needs 82.8 %); at 90 %
    it does, which no local model can."""
    phi = Q.PHI_PLUS
    chsh = (0.0, 45 * math.pi / 180, 22.5 * math.pi / 180, -22.5 * math.pi / 180)
    assert BS.best_j(phi, 0.75, 0.75, starts=4, x0=chsh)[0] < 0
    assert BS.best_j(phi, 0.90, 0.90, starts=4, x0=chsh)[0] > 0
    with pytest.raises(ValueError):
        LH.gisin_gisin([0, 0, 1], [1, 0, 0], 10, rng, state="ghz")
