# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Statistics of coincidence counts in a Bell test (simulated data).

Counts of one setting pair are ``(N++, N+-, N-+, N--)`` (first sign: side A, second: side B).

* ``correlation``: E = (N++ + N-- - N+- - N-+) / N; each pair contributes x = A B in {-1, +1}, Var x = 1 - E^2, so the
  standard error is sqrt((1 - E^2) / N) (plug-in estimate from the data);
* ``se_under``: the same error under a hypothesised E_ref (the variance of the null hypothesis; defined also when the
  data happen to give |E| = 1);
* ``chsh``: S = s1 E1 + s2 E2 + s3 E3 + s4 E4 (default signs +, -, +, + for E(a,b) - E(a,b') + E(a',b) + E(a',b'));
  four distinct cells are independent samples, so Var S = sum Var E_k. With coinciding settings (a' = a or b' = b)
  two cells are the same counts; given the cells' ``keys`` the error groups them: S = sum over distinct cells c of
  w_c E_c with w_c the sum of the signs of the cells equal to c, Var S = sum_c w_c^2 Var E_c (review 2026-10-23,
  V7-2; e.g. a' = a: S = 2 E(a,b), Var S = 4 Var E(a,b));
* ``marginal``: P(+) of one side and its binomial error;
* ``difference``: p1 - p2 of two independent binomial proportions with the pooled standard error (the error under
  the hypothesis p1 = p2, used for the no-signalling test);
* ``chi2_points``: sum of squared z-scores of independent estimates against references, with its p-value.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps

ABOUT = {
    "layer": "tools", "kind": "statistics",
    "title": "Статистика опыта Белла",
    "statement": "Оценка корреляции E и её стандартной ошибки по счётам совпадений, CHSH-параметр S и его ошибка, "
                 "разность маргинальных вероятностей (проверка отсутствия сигнала), χ² точек против эталона.",
    "validity": "инструмент, не физика; ошибки — нормальное приближение (N ≳ 30 на ячейку)",
    "basis": ["биномиальная и мультиномиальная статистика; CHSH: Clauser, Horne, Shimony, Holt, PRL 23, 880 (1969)"],
    "conflicts": [],
}

CHSH_SIGNS = (1, -1, 1, 1)


def correlation(counts):
    """(E, se, N) from (N++, N+-, N-+, N--); (None, None, 0) for no counts."""
    npp, npm, nmp, nmm = (int(x) for x in counts)
    n = npp + npm + nmp + nmm
    if n == 0:
        return None, None, 0
    E = (npp + nmm - npm - nmp) / n
    return E, math.sqrt(max(1.0 - E * E, 0.0) / n), n


def se_under(E_ref: float, n: int):
    """Standard error of the estimate of E from n pairs if the true correlation is E_ref."""
    if n <= 0:
        return None
    return math.sqrt(max(1.0 - E_ref * E_ref, 0.0) / n)


def _groups(signs, keys):
    """[(first index, summed sign)] of the distinct cells; without keys every cell is distinct."""
    if keys is None:
        return [(k, s) for k, s in enumerate(signs)]
    out: dict = {}
    for k, (key, s) in enumerate(zip(keys, signs)):
        i, w = out.get(key, (k, 0))
        out[key] = (i, w + s)
    return list(out.values())


def chsh(cells, signs=CHSH_SIGNS, keys=None):
    """(S, se) from four count tuples; (None, None) if a cell is empty. ``keys`` (one per cell, e.g. its pair of
    analyzer angles): cells with equal keys are the same counts and are counted once in the error."""
    S = 0.0
    var = 0.0
    for i, w in _groups(signs, keys):
        E, se, n = correlation(cells[i])
        if n == 0:
            return None, None
        S += w * E
        var += w * w * se * se
    return S, math.sqrt(var)


def chsh_se_under(E_refs, ns, keys=None, signs=CHSH_SIGNS):
    """Standard error of S under the hypothesised correlations E_refs with ns pairs per cell (``keys`` as in
    ``chsh``)."""
    var = 0.0
    for i, w in _groups(signs, keys):
        if ns[i] <= 0:
            return None
        var += w * w * (1.0 - E_refs[i] * E_refs[i]) / ns[i]
    return math.sqrt(max(var, 0.0))


def marginal(counts, side: str):
    """(P(+), se, N) of side "A" or "B" from (N++, N+-, N-+, N--)."""
    npp, npm, nmp, nmm = (int(x) for x in counts)
    n = npp + npm + nmp + nmm
    if n == 0:
        return None, None, 0
    k = npp + npm if side == "A" else npp + nmp
    p = k / n
    return p, math.sqrt(p * (1 - p) / n), n


def difference(k1: int, n1: int, k2: int, n2: int):
    """(p1 - p2, pooled se) of two binomial proportions k1/n1 and k2/n2; (None, None) if a sample is empty."""
    if n1 <= 0 or n2 <= 0:
        return None, None
    p1, p2 = k1 / n1, k2 / n2
    pb = (k1 + k2) / (n1 + n2)
    return p1 - p2, math.sqrt(max(pb * (1 - pb), 0.0) * (1.0 / n1 + 1.0 / n2))


def zscore(value, ref, se):
    """(value - ref) / se; 0 when they agree exactly and se = 0; +-inf when they differ and se = 0."""
    if value is None or ref is None or se is None:
        return None
    d = value - ref
    if se > 0:
        return d / se
    return 0.0 if d == 0 else math.copysign(math.inf, d)


def chi2_points(values, refs, ses):
    """(chi2, dof, p) of independent estimates against references (points with se = 0 are skipped)."""
    v = np.asarray(values, float)
    r = np.asarray(refs, float)
    s = np.asarray(ses, float)
    m = s > 0
    if not np.any(m):
        return None, 0, None
    x2 = float(np.sum(((v[m] - r[m]) / s[m]) ** 2))
    dof = int(np.sum(m))
    return x2, dof, float(sps.chi2.sf(x2, dof))
