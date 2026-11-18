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


# --- real detectors and the inequalities without fair sampling (EX2 §4.7) ----------------------------------------
from lfphys.core.quantum import qubits as Q  # noqa: E402
from lfphys.theories.models import photodetector as PD  # noqa: E402

DEG = math.pi / 180
GIUSTINA = (94.4 * DEG, 62.4 * DEG, -6.5 * DEG, 25.5 * DEG)  # a1, a2, b1, b2 (Giustina et al. 2015)


def _ports(n_det, angle):
    """The analyser's ports (all of them) and the ones with a detector."""
    P = Q.polarizer_projectors(angle)
    return list(P), list(P[:n_det])


def _enumerated_slot(state, angle_a, angle_b, na, nb, eta_a, eta_b, pd_a, pd_b, mu, nmax=12):
    """The slot's outcome probabilities by enumeration (a second method): each pair's ports (Born), each photon's
    detection, an OR over a Poisson number of pairs (truncated at nmax) and over the dark clicks."""
    all_a, _ = _ports(na, angle_a)
    all_b, _ = _ports(nb, angle_b)
    P = Q.joint_probabilities(state, all_a, all_b)
    ea, eb = np.broadcast_to(eta_a, (na,)), np.broadcast_to(eta_b, (nb,))
    pair = {}  # (mask A, mask B) -> probability, for one pair
    for i in range(2):
        for j in range(2):
            for di in (0, 1):
                for dj in (0, 1):
                    wa = (ea[i] if di else 1 - ea[i]) if i < na else (1.0 if di == 0 else 0.0)
                    wb = (eb[j] if dj else 1 - eb[j]) if j < nb else (1.0 if dj == 0 else 0.0)
                    key = ((1 << i) if (di and i < na) else 0, (1 << j) if (dj and j < nb) else 0)
                    pair[key] = pair.get(key, 0.0) + P[i, j] * wa * wb

    def orconv(d1, d2):
        out = {}
        for (a1, b1), p1 in d1.items():
            for (a2, b2), p2 in d2.items():
                k = (a1 | a2, b1 | b2)
                out[k] = out.get(k, 0.0) + p1 * p2
        return out

    if mu is None:
        total = pair
    else:
        total, power = {}, {(0, 0): 1.0}
        for n in range(nmax + 1):
            w = math.exp(-mu) * mu ** n / math.factorial(n)
            for k, p in power.items():
                total[k] = total.get(k, 0.0) + w * p
            power = orconv(power, pair)
    dark = {(0, 0): 1.0}
    for k, p in enumerate(np.broadcast_to(pd_a, (na,))):
        dark = orconv(dark, {(1 << k, 0): p, (0, 0): 1 - p})
    for k, p in enumerate(np.broadcast_to(pd_b, (nb,))):
        dark = orconv(dark, {(0, 1 << k): p, (0, 0): 1 - p})
    total = orconv(total, dark)
    pat = {1: (0b1, 0b0), 2: (0b01, 0b10, 0b00, 0b11)}
    return np.array([[total.get((ma, mb), 0.0) for mb in pat[nb]] for ma in pat[na]])


@pytest.mark.parametrize("na,nb,mu", [(1, 1, None), (1, 1, 0.05), (2, 2, 0.3), (2, 1, 1.5), (2, 2, None)])
def test_slot_probabilities_against_an_enumeration(na, nb, mu):
    for _ in range(4):
        state = Q.werner(Q.eberhard_state(rng.uniform(-3, 3)), rng.uniform(0.7, 1.0))
        aa, ab = rng.uniform(0, math.pi, 2)
        ea, eb = rng.uniform(0.5, 1, na), rng.uniform(0.5, 1, nb)
        pa, pb = rng.uniform(0, 0.05, na), rng.uniform(0, 0.05, nb)
        got = BS.slot_probabilities(state, _ports(na, aa)[1], _ports(nb, ab)[1], ea, eb, pa, pb, mu)
        ref = _enumerated_slot(state, aa, ab, na, nb, ea, eb, pa, pb, mu, nmax=40 if mu and mu > 1 else 14)
        assert got.shape == ref.shape == (len(BS.outcome_labels(na)), len(BS.outcome_labels(nb)))
        assert got.sum() == pytest.approx(1.0, abs=1e-14)
        assert got == pytest.approx(ref, abs=1e-13)


def test_slot_probabilities_limits_are_the_projective_ones():
    """eta = 1, no dark clicks, one pair: the two-detector table is the Born table of the projectors (no "0", no
    "+-"); the one-detector "++" cell is Tr(rho Pi (x) Pi); mu -> 0 leaves only the dark clicks."""
    PA, PB = Q.polarizer_projectors(0.3), Q.polarizer_projectors(1.1)
    t = BS.slot_probabilities(Q.PHI_PLUS, PA, PB, 1.0, 1.0)
    assert t[:2, :2] == pytest.approx(Q.joint_probabilities(Q.PHI_PLUS, PA, PB), abs=1e-15)
    assert np.abs(t[2:, :]).sum() + np.abs(t[:, 2:]).sum() == pytest.approx(0.0, abs=1e-15)
    t1 = BS.slot_probabilities(Q.PHI_PLUS, [PA[0]], [PB[0]], 1.0, 1.0)
    assert t1[0, 0] == pytest.approx(math.cos(0.8) ** 2 / 2, abs=1e-15)
    t0 = BS.slot_probabilities(Q.PHI_PLUS, [PA[0]], [PB[0]], 0.7, 0.7, 0.01, 0.02, mu=0.0)
    assert t0 == pytest.approx(np.outer([0.01, 0.99], [0.02, 0.98]), abs=1e-15)
    # a small mu: per slot = mu x per pair to first order
    j1 = BS.j_polarisers(Q.eberhard_state(-2.9), GIUSTINA, 0.786, 0.762)
    js = BS.j_polarisers(Q.eberhard_state(-2.9), GIUSTINA, 0.786, 0.762, mu=1e-6)
    assert js / 1e-6 == pytest.approx(j1, rel=1e-5)


def test_slot_probabilities_against_the_time_stream():
    """Settings chosen at random per locally defined slot at each station, Poisson pairs (mu = 0.2: multi-pair
    emission), real detectors (dark counts, dead time, jitter): the counted slot outcomes of each setting pair equal
    ``slot_probabilities`` within 5σ (plus the slots' coupling)."""
    n, slot, R = 400_000, 1e-6, 2e5
    state = Q.werner(Q.eberhard_state(-0.6), 0.95)
    angles_a, angles_b = (0.1, 0.9), (-0.3, 0.5)
    da = [PD.Detector(0.7, 3e4, 22e-9, 0.15e-9), PD.Detector(0.6, 1e4, 22e-9, 0.15e-9)]   # two detectors at A
    db = [PD.Detector(0.68, 5e4, 20e-9, 0.15e-9)]                                         # one at B
    pp = [[Q.joint_probabilities(state, Q.polarizer_projectors(a), Q.polarizer_projectors(b)) for b in angles_b]
          for a in angles_a]
    sa, sb = rng.integers(0, 2, n), rng.integers(0, 2, n)
    (ca, cb), _ = PD.pair_slots(n, slot, R, pp, sa, sb, da, db, rng)
    oa = np.select([ca[0] & ~ca[1], ~ca[0] & ca[1], ~ca[0] & ~ca[1]], [0, 1, 2], 3)  # "+", "-", "0", "+-"
    ob = np.where(cb[0], 0, 1)                                                          # "+", "0"
    eps = PD.slot_coupling(22e-9, 0.15e-9, slot)
    for x in (0, 1):
        for y in (0, 1):
            m = (sa == x) & (sb == y)
            counts = np.zeros((4, 2))
            np.add.at(counts, (oa[m], ob[m]), 1)
            ref = BS.slot_probabilities(state, Q.polarizer_projectors(angles_a[x]),
                                        [Q.polarizer_projectors(angles_b[y])[0]],
                                        [d.eta for d in da], db[0].eta,
                                        [PD.dark_click_probability(d.dark_rate, slot) for d in da],
                                        PD.dark_click_probability(db[0].dark_rate, slot), mu=R * slot)
            f = counts / m.sum()
            assert np.all(np.abs(f - ref) < 5 * np.sqrt(ref * (1 - ref) / m.sum()) + eps * ref + 1e-12)


def _quantum_tables(state, angles, eta_a, eta_b, pd_a=0.0, pd_b=0.0, mu=None):
    a1, a2, b1, b2 = angles
    return [[BS.slot_probabilities(state, [Q.polarizer_projectors(a)[0]], [Q.polarizer_projectors(b)[0]], eta_a, eta_b,
                                   pd_a, pd_b, mu) for b in (b1, b2)] for a in (a1, a2)]


def test_j_for_giustinas_state_angles_and_efficiencies():
    """J per pair = 0.01134 at Giustina et al.'s r = -2.9, angles and efficiencies 78.6 % and 76.2 % (design A.7), and
    per slot about 4e-5 at their 3 500 pairs per second in 1 µs trials («quantum mechanics predicts an optimal J-value
    of about 4 × 10−5»); a direct formula with the state's amplitudes as the second method."""
    psi = Q.eberhard_state(-2.9)
    J = BS.j_polarisers(psi, GIUSTINA, 0.786, 0.762)
    assert J == pytest.approx(0.01134, abs=5e-6)

    def amp2(a, b):  # |<a b|psi>|^2 with <theta| = (cos, sin)
        return abs(np.kron([math.cos(a), math.sin(a)], [math.cos(b), math.sin(b)]) @ psi) ** 2

    def mA(a):
        u = [math.cos(a), math.sin(a)]
        return abs(np.kron(u, [1, 0]) @ psi) ** 2 + abs(np.kron(u, [0, 1]) @ psi) ** 2

    def mB(b):
        v = [math.cos(b), math.sin(b)]
        return abs(np.kron([1, 0], v) @ psi) ** 2 + abs(np.kron([0, 1], v) @ psi) ** 2

    a1, a2, b1, b2 = GIUSTINA
    ea, eb = 0.786, 0.762
    ref = (ea * eb * amp2(a1, b1) - (ea * mA(a1) - ea * eb * amp2(a1, b2)) - (eb * mB(b1) - ea * eb * amp2(a2, b1))
           - ea * eb * amp2(a2, b2))
    assert J == pytest.approx(ref, abs=1e-15)
    for eta, j in ((0.60, -0.0239), (0.70, -0.0060), (0.75, 0.0053), (0.80, 0.0182), (1.00, 0.0852)):
        assert BS.j_polarisers(psi, GIUSTINA, eta, eta) == pytest.approx(j, abs=5e-5)
    js = BS.j_polarisers(psi, GIUSTINA, 0.786, 0.762, mu=3500 * 1e-6)
    assert js == pytest.approx(4e-5, rel=0.05) and js == pytest.approx(0.0035 * J, rel=0.01)
    assert BS.ch_value(_quantum_tables(psi, GIUSTINA, 0.786, 0.762)) == pytest.approx(J, abs=1e-15)  # no signalling


@pytest.mark.parametrize("which", ["J", "CH"])
def test_ch_and_j_estimators_are_unbiased_with_covering_errors(which):
    """Monte Carlo of whole runs: settings at random per trial, outcomes from the exact multinomial; the estimate's
    mean equals the closed form, its spread the mean standard error, and ±1.96 se covers 95 %."""
    state = Q.werner(Q.eberhard_state(-2.9), 0.99)
    tab = _quantum_tables(state, GIUSTINA, 0.786, 0.762, 2e-4, 2e-4, mu=0.05)
    ref = BS.j_value(tab) if which == "J" else BS.ch_value(tab)
    est = BS.j_estimate if which == "J" else BS.ch_estimate
    vals, ses = [], []
    for _ in range(3000):
        ns = rng.multinomial(80_000, [0.25] * 4).reshape(2, 2)
        counts = [[BS.sample_counts(tab[i][j], ns[i, j], rng) for j in (0, 1)] for i in (0, 1)]
        v, s = est(counts)
        vals.append(v)
        ses.append(s)
    vals, ses = np.array(vals), np.array(ses)
    assert vals.mean() == pytest.approx(ref, abs=4 * vals.std() / math.sqrt(len(vals)))
    assert vals.std() == pytest.approx(ses.mean(), rel=0.04)
    cover = np.mean(np.abs(vals - ref) < 1.96 * ses)
    assert abs(cover - 0.95) < 4 * math.sqrt(0.95 * 0.05 / len(vals))


def test_ch_and_j_exact_cases():
    """Hand-made tables: J and CH of counts against their definitions; a setting pair without trials gives None."""
    t = [[np.array([[40, 10], [10, 940]]), np.array([[20, 30], [5, 945]])],
         [np.array([[25, 5], [35, 935]]), np.array([[30, 20], [20, 930]])]]
    J, se = BS.j_estimate(t)
    assert J == pytest.approx(40 / 1000 - 30 / 1000 - 35 / 1000 - 30 / 1000, abs=1e-15)
    var = (0.04 * 0.96 + 0.03 * 0.97 + 0.035 * 0.965 + 0.03 * 0.97) / 1000
    assert se == pytest.approx(math.sqrt(var), rel=1e-12)
    CH, _ = BS.ch_estimate(t)
    pa = (50 + 50) / 2000
    pb = (50 + 60) / 2000
    assert CH == pytest.approx(0.040 + 0.020 + 0.025 - 0.030 - pa - pb, abs=1e-15)
    t[1][1] = np.zeros((2, 2))
    assert BS.j_estimate(t) == (None, None) and BS.ch_estimate(t) == (None, None)
    four = np.arange(16.0).reshape(4, 4)
    assert BS.plus_table(four) == pytest.approx(np.array([[0 + 3 + 12 + 15, 1 + 2 + 13 + 14],
                                                          [4 + 7 + 8 + 11, 5 + 6 + 9 + 10]]))


def test_thresholds_against_a_direct_search():
    """The maximally entangled state violates CH/J only above 2/(1 + sqrt 2) (Gisin and Gisin, eq. (18); Eberhard's
    (7): 2(sqrt 2 - 1)): the search finds J < 0 just below and J > 0 just above, and (sqrt 2 - 1)/2 at eta = 1. Below
    2/3 no state and no angles give J > 0 (Eberhard 1993); weakly entangled states approach 2/3 from above."""
    singlet = Q.eberhard_state(-1.0)
    chsh = (0.0, 45 * DEG, 22.5 * DEG, -22.5 * DEG)
    thr = BS.CH_THRESHOLD_MAXIMAL
    assert thr == pytest.approx(2 * (math.sqrt(2) - 1), abs=1e-15) and thr == pytest.approx(0.8284, abs=5e-5)
    assert BS.best_j(singlet, thr - 0.002, thr - 0.002, starts=6, x0=chsh)[0] < 0
    assert BS.best_j(singlet, thr + 0.002, thr + 0.002, starts=6, x0=chsh)[0] > 0
    assert BS.best_j(singlet, 1.0, 1.0, starts=4, x0=chsh)[0] == pytest.approx((math.sqrt(2) - 1) / 2, abs=1e-9)
    for r in (-0.01, -0.05, -0.3, -1.0, -5.0):
        assert BS.best_j(Q.eberhard_state(r), 0.66, 0.66, starts=6)[0] <= 1e-12
    assert BS.best_j(Q.eberhard_state(-0.05), 0.68, 0.68, starts=8)[0] > 0
    assert BS.EBERHARD_LIMIT == pytest.approx(2 / 3, abs=1e-15)


@pytest.mark.parametrize("eta,r,zeta,dalpha", [(0.70, 0.136, 0.02, 21.4), (0.75, 0.311, 0.31, 32.0),
                                               (0.80, 0.465, 1.10, 37.9), (0.85, 0.608, 2.48, 41.5),
                                               (0.90, 0.741, 4.50, 43.6), (1.00, 1.000, 10.36, 45.0)])
def test_largest_j_against_eberhards_table(eta, r, zeta, dalpha):
    """Eberhard's Table 2 (preprint LBL-32696): the largest background zeta (per pair, added to both single-detection
    terms) that still allows a violation at efficiency eta, with the state's r and the angle a2 - a1 (= +-(b2 - b1)).
    The largest J per pair over the angles at that r is 2 zeta to the table's rounding, at the same angles. (The
    95 % row is not used: its r and zeta are unreadable in the scan.)"""
    J, x = BS.best_j(Q.eberhard_state(r), eta, eta, starts=10)
    assert 100 * J / 2 == pytest.approx(zeta, abs=0.0051)
    da = math.degrees(abs(x[1] - x[0])) % 180
    db = math.degrees(abs(x[3] - x[2])) % 180
    assert min(da, 180 - da) == pytest.approx(dalpha, abs=0.06)
    assert min(db, 180 - db) == pytest.approx(dalpha, abs=0.06)


def test_threshold_efficiency_by_bisection():
    assert BS.threshold_efficiency(Q.eberhard_state(-1.0), starts=3, tol=1e-4) == pytest.approx(BS.CH_THRESHOLD_MAXIMAL,
                                                                                                abs=2e-4)
    t = BS.threshold_efficiency(Q.eberhard_state(-0.1), starts=3, tol=1e-3)
    assert BS.EBERHARD_LIMIT < t < 0.69
    assert math.isnan(BS.threshold_efficiency(Q.eberhard_state(-1.0), lo=0.5, hi=0.7, starts=3))


def test_accidentals_subtracted_and_not():
    """Coincidences = true ones (E = cos 2(a - b) of |Phi+>) + accidentals (Poisson, equal in the four detector pairs):
    subtracting N_acc = w N_A N_B / T makes E and S unbiased with covering errors; leaving them shrinks E by
    true/(true + accidental), as Dehlinger and Mitchell say («This background ... acts to decrease |S|»)."""
    assert BS.accidentals([1e5, 2e5], [3e5], 25e-9, 15.0) == pytest.approx(
        np.array([[1e5 * 3e5], [2e5 * 3e5]]) * 25e-9 / 15.0, rel=1e-15)
    assert float(PD.accidental_rate(25e-9, 1e5 / 15.0, 3e5 / 15.0)) * 15.0 == pytest.approx(25e-9 * 1e5 * 3e5 / 15.0,
                                                                                             rel=1e-14)
    angles = [(0.0, 22.5), (0.0, 67.5), (45.0, 22.5), (45.0, 67.5)]
    true_n, acc = 2000.0, 120.0
    Es = [math.cos(2 * (a - b) * DEG) for a, b in angles]
    S_ref = Es[0] - Es[1] + Es[2] + Es[3]
    S_sub, S_raw, se_sub = [], [], []
    for _ in range(3000):
        cells, accs = [], []
        for E in Es:
            lam = true_n * np.array([(1 + E) / 4, (1 - E) / 4, (1 - E) / 4, (1 + E) / 4]) + acc / 4
            cells.append(rng.poisson(lam))
            accs.append([acc / 4] * 4)
        s, e = BS.chsh_subtracted(cells, accs)
        S_sub.append(s)
        se_sub.append(e)
        S_raw.append(BS.chsh_subtracted(cells)[0])
    S_sub, S_raw, se_sub = map(np.array, (S_sub, S_raw, se_sub))
    assert S_sub.mean() == pytest.approx(S_ref, abs=4 * S_sub.std() / math.sqrt(len(S_sub)) + 2e-4)
    assert S_sub.std() == pytest.approx(se_sub.mean(), rel=0.05)
    tol = 4 * S_raw.std() / math.sqrt(len(S_raw)) + 2e-4
    assert S_raw.mean() == pytest.approx(S_ref * true_n / (true_n + acc), abs=tol)
    # no accidentals: the same as ``correlation``
    c = (300, 40, 50, 310)
    E0, se0, n0 = BS.correlation(c)
    E1, se1, n1 = BS.correlation_subtracted(c)
    assert (E1, n1) == pytest.approx((E0, n0), abs=1e-15)
    assert se1 == pytest.approx(se0 * math.sqrt(1.0), rel=1e-12)


def test_background_raises_the_threshold_as_shalm_reports():
    """Shalm et al. 2015: «These background counts in our system raise the efficiency needed to violate a Bell
    inequality from 2/3 to 72.5 %», with background probabilities 8.9e-7 (Alice) and 3.2e-7 (Bob) per window and a
    pair in a pump pulse with probability about 5e-4. With one pulse per trial (their trials aggregate several: not
    modelled) the slot probabilities give a threshold between 72 % and 73.5 %: no state near the optimum violates J
    at 72 %, one does at 73.5 %."""
    pa, pb, mu = 8.9e-7, 3.2e-7, 5e-4
    for r in (0.15, 0.2, 0.25, 0.3):
        assert BS.best_j(Q.eberhard_state(r), 0.72, 0.72, pa, pb, mu, starts=4)[0] < 0
    assert BS.best_j(Q.eberhard_state(0.25), 0.735, 0.735, pa, pb, mu, starts=4)[0] > 0
