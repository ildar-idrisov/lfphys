# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.tools.bell_stats: closed forms of the estimators against Monte-Carlo repetitions (an independent method)."""

import math

import numpy as np
import pytest
from scipy import stats as sps

from lfphys.tools import bell_stats as BS

rng = np.random.default_rng(1964)


def _cells(E, n, size):
    """Multinomial coincidence counts (N++, N+-, N-+, N--) with correlation E and unbiased marginals."""
    p = [(1 + E) / 4, (1 - E) / 4, (1 - E) / 4, (1 + E) / 4]
    return rng.multinomial(n, p, size=size)


def test_correlation_exact_values():
    assert BS.correlation((10, 0, 0, 10)) == (1.0, 0.0, 20)
    E, se, n = BS.correlation((30, 10, 20, 40))
    assert E == pytest.approx(0.4) and n == 100 and se == pytest.approx(math.sqrt(0.84 / 100))
    assert BS.correlation((0, 0, 0, 0)) == (None, None, 0)
    assert BS.marginal((30, 10, 20, 40), "A")[0] == pytest.approx(0.4)
    assert BS.marginal((30, 10, 20, 40), "B")[0] == pytest.approx(0.5)
    assert BS.zscore(1.0, 1.0, 0.0) == 0.0 and math.isinf(BS.zscore(0.9, 1.0, 0.0))


def test_standard_error_of_E_matches_the_spread_of_repetitions():
    E0, n = 0.6, 400
    cs = _cells(E0, n, 20000)
    Es = np.array([BS.correlation(c)[0] for c in cs])
    ses = np.array([BS.correlation(c)[1] for c in cs])
    ref = BS.se_under(E0, n)
    assert Es.mean() == pytest.approx(E0, abs=4 * ref / math.sqrt(len(Es)))  # unbiased
    assert Es.std() == pytest.approx(ref, rel=0.03)
    assert ses.mean() == pytest.approx(ref, rel=0.01)


def test_chsh_error_matches_the_spread_of_repetitions():
    Es = (0.7071, -0.7071, 0.7071, 0.7071)
    n = 250
    S = []
    for _ in range(8000):
        cells = [_cells(E, n, 1)[0] for E in Es]
        S.append(BS.chsh(cells)[0])
    S = np.array(S)
    ref = BS.chsh_se_under(Es, [n] * 4)
    assert S.mean() == pytest.approx(sum(s * E for s, E in zip(BS.CHSH_SIGNS, Es)), abs=4 * ref / math.sqrt(len(S)))
    assert S.std() == pytest.approx(ref, rel=0.03)
    assert BS.chsh([(1, 0, 0, 1)] * 3 + [(0, 0, 0, 0)]) == (None, None)


def test_pooled_difference_is_a_standard_normal_under_equal_proportions():
    n1, n2 = 300, 500
    k1 = rng.binomial(n1, 0.5, 20000)
    k2 = rng.binomial(n2, 0.5, 20000)
    z = np.array([d / s for d, s in (BS.difference(a, n1, b, n2) for a, b in zip(k1, k2))])
    assert abs(z.mean()) < 4 / math.sqrt(len(z))
    assert z.std() == pytest.approx(1.0, rel=0.03)


def test_chi2_points_p_values_are_uniform_under_the_reference():
    ps = []
    for _ in range(2000):
        refs = rng.uniform(-1, 1, 7)
        ses = rng.uniform(0.01, 0.1, 7)
        vals = refs + ses * rng.normal(size=7)
        x2, dof, p = BS.chi2_points(vals, refs, ses)
        assert dof == 7
        ps.append(p)
    assert sps.kstest(ps, "uniform").pvalue > 1e-3
    x2, dof, p = BS.chi2_points([1.0, 2.0], [0.0, 2.0], [0.5, 1.0])
    assert x2 == pytest.approx(4.0) and dof == 2 and p == pytest.approx(math.exp(-2.0))


@pytest.mark.parametrize("keys,signs_w", [
    (("ab", "ab2", "ab", "ab2"), {"ab": 2, "ab2": 0}),   # a' = a: (a,b) = (a',b), (a,b') = (a',b')
    (("ab", "ab", "a2b", "a2b"), {"ab": 0, "a2b": 2}),   # b' = b: (a,b) = (a,b'), (a',b) = (a',b')
    (("ab", "ab2", "ab", "a2b2"), {"ab": 2, "ab2": -1, "a2b2": 1}),  # a' = a only for b (a third distinct cell)
])
def test_chsh_error_with_coinciding_cells_matches_the_spread(keys, signs_w):
    """Review 2026-10-23, V7-2: cells that share one angle pair are the same counts; the error of S must group them,
    Var S = sum over distinct cells of (sum of their signs)^2 Var E. Without the keys the error assumes four
    independent cells (wrong by x1.55 or x0 in the reviewer's runs)."""
    Etrue = {"ab": 0.3, "ab2": -0.6, "a2b": 0.8, "a2b2": 0.1}
    n = 300
    S, se = [], []
    for _ in range(6000):
        counts = {k: _cells(Etrue[k], n, 1)[0] for k in signs_w}
        s, e = BS.chsh([counts[k] for k in keys], keys=keys)
        S.append(s)
        se.append(e)
    S = np.array(S)
    ref = math.sqrt(sum(w * w * (1 - Etrue[k] ** 2) / n for k, w in signs_w.items()))
    assert BS.chsh_se_under([Etrue[k] for k in keys], [n] * 4, keys=keys) == pytest.approx(ref, rel=1e-12)
    assert S.mean() == pytest.approx(sum(w * Etrue[k] for k, w in signs_w.items()), abs=4 * ref / math.sqrt(len(S)))
    assert S.std() == pytest.approx(ref, rel=0.04)
    assert np.mean(se) == pytest.approx(ref, rel=0.02)
