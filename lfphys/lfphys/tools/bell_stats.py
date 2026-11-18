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

Real detectors and the inequalities without fair sampling (EX2 design §4.7):
* ``slot_probabilities``: the outcome probabilities of one trial (a locally defined slot) for two stations, each an
  analyser with one or two threshold detectors (``lfphys.core.quantum.qubits`` POVMs), with dark clicks and a Poisson
  number of pairs per slot (mean mu = R Ts; multi-pair emission) or exactly one pair. With U a set of detectors and
  q(U) = Tr[rho (I - sum_{k in U_A} eta_k Pi_k) (x) (I - sum_{l in U_B} eta_l Pi_l)] the probability that one pair is
  seen by none of them, P(no detector of U clicks) = G(q(U)) prod_{k in U} (1 - p_k) with G(q) = q (one pair) or
  exp(-mu (1 - q)) (Poisson, independent pairs); the probability of an exact click pattern C follows by
  inclusion-exclusion, sum_{W subset C} (-1)^|W| P(no click in W or in D minus C);
* ``j_estimate``: the CH-Eberhard J = p++(a1 b1) - p+0(a1 b2) - p0+(a2 b1) - p++(a2 b2) <= 0 (Giustina et al. 2015,
  eq. (1); Eberhard 1993, ineq. (8)), "+" a detection and "0" none, from the outcome counts of each setting pair;
* ``ch_estimate``: CH in Gisin and Gisin's form, their inequality (15) per trial:
  p++(a, b) + p++(a, b') + p++(a', b) - p++(a', b') - p+.(a) - p.+(b) <= 0 (Clauser and Horne 1974, ineq. (4), with a
  and a' exchanged; its lower bound -1 is not used), the singles pooled over the trials of their setting;
* both are linear in each setting pair's outcome frequencies: the standard error is that of the multinomial of each
  setting pair (independent given the numbers of trials), its significance the normal approximation (i.i.d. trials);
* ``correlation_subtracted`` / ``chsh_subtracted``: E and S from coincidences under fair sampling, with the
  accidentals (``accidentals``: w N_A N_B / T per detector pair, Dehlinger and Mitchell 2002) subtracted;
* thresholds: ``CH_THRESHOLD_MAXIMAL`` = 2/(1 + sqrt 2) (the maximally entangled state at the CHSH angles, Gisin and
  Gisin's eq. (18)), ``EBERHARD_LIMIT`` = 2/3 (approached by weakly entangled states without background, Eberhard
  1993); ``best_j`` searches the polariser angles, ``threshold_efficiency`` the smallest equal efficiency with J > 0.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import optimize
from scipy import stats as sps

from lfphys.core.quantum import qubits as Q
from lfphys.i18n import T

ABOUT = {
    "layer": "tools", "kind": "statistics",
    "title": T("Statistics of a Bell experiment"),
    "statement": T("The estimate of the correlation E and its standard error from coincidence counts, the CHSH "
                   "parameter S and its error, the difference of marginal probabilities (a check of no signalling), "
                   "χ² of the points against a reference; with real detectors: the outcome probabilities of a time "
                   "slot (dark clicks, a Poisson number of pairs), CHSH with the accidental coincidences subtracted, "
                   "CH and the CH–Eberhard J from all slots with their errors, the efficiency thresholds "
                   "2/(1 + √2) and 2/3."),
    "validity": T("a tool, not physics; the errors use the normal approximation (N ≳ 30 per cell); CHSH from "
                  "coincidences assumes fair sampling, CH and J do not; their significance assumes independent, "
                  "identically distributed trials (the experiments' martingale p-values are not computed); the slot "
                  "probabilities hold for independent pairs and independent slots"),
    "basis": [T("binomial and multinomial statistics; CHSH: Clauser, Horne, Shimony, Holt, PRL 23, 880 (1969)"),
              "Clauser, Horne, Phys. Rev. D 10, 526 (1974), ineq. (4)",
              T("Eberhard, Phys. Rev. A 47, R747 (1993) (preprint LBL-32696 read: ineq. (8), Table 2)"),
              "Gisin, Gisin, Phys. Lett. A 260, 323 (1999), ineqs. (15), (18)",
              "Giustina et al., PRL 115, 250401 (2015), eq. (1)", "Shalm et al., PRL 115, 250402 (2015)",
              "Dehlinger, Mitchell, Am. J. Phys. 70, 903 (2002)"],
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


# --- real detectors: slot probabilities (EX2 §4.7) ---------------------------------------------------------------
CH_THRESHOLD_MAXIMAL = 2.0 / (1.0 + math.sqrt(2.0))  # = 2 (sqrt 2 - 1) = 0.8284
EBERHARD_LIMIT = 2.0 / 3.0


def outcome_labels(n_detectors: int) -> tuple:
    """The outcomes of a station with one detector ("+", "0") or two ("+", "-", "0", "+-")."""
    return {1: Q.ONE_DETECTOR_OUTCOMES, 2: Q.TWO_DETECTOR_OUTCOMES}[n_detectors]


_PATTERNS = {1: (0b1, 0b0), 2: (0b01, 0b10, 0b00, 0b11)}  # the click set of each outcome, in outcome_labels' order


def _per_detector(x, n: int, name: str) -> list[float]:
    v = [float(y) for y in np.broadcast_to(np.asarray(x, float), (n,))]
    if any(not 0.0 <= y <= 1.0 for y in v):
        raise ValueError(T("{name} must lie in [0, 1]", name=name))
    return v


def slot_probabilities(state, ports_a, ports_b, eta_a, eta_b, p_dark_a=0.0, p_dark_b=0.0, mu=None) -> np.ndarray:
    """P[o_A, o_B]: the probabilities of the stations' outcomes (``outcome_labels``) in one trial. ``ports_a``: the
    projectors of the analyser's ports that have a detector (one: [Pi]; two: [Pi_+, Pi_-]); ``eta_a``, ``p_dark_a``:
    each detector's efficiency and dark-click probability in the trial (one value or one per detector; a dark rate d
    over a slot Ts gives 1 - exp(-d Ts)). ``mu`` None: exactly one pair in the trial; a number: a Poisson number of
    pairs of mean mu, each independently in ``state`` (a source whose slot holds many temporal modes). Rows and
    columns sum to the marginals; the whole sums to 1."""
    rho = Q.dm(state) if np.ndim(state) == 1 else np.asarray(state, complex)
    PA = [np.asarray(P, complex) for P in ports_a]
    PB = [np.asarray(P, complex) for P in ports_b]
    na, nb = len(PA), len(PB)
    if na not in (1, 2) or nb not in (1, 2):
        raise ValueError(T("a station has one or two detectors"))
    ea, eb = _per_detector(eta_a, na, "eta"), _per_detector(eta_b, nb, "eta")
    da, db = _per_detector(p_dark_a, na, "p_dark"), _per_detector(p_dark_b, nb, "p_dark")
    if mu is not None and not (math.isfinite(mu) and mu >= 0.0):
        raise ValueError(T("the mean number of pairs per slot must be finite and non-negative"))
    R4 = rho.reshape(2, 2, 2, 2)  # rho[(i j), (k l)] -> R4[i, j, k, l]

    def blind(eta, P, n, u):
        """I - sum over the detectors k in the set u of eta_k Pi_k: one photon seen by none of them."""
        F = np.eye(2, dtype=complex)
        for k in range(n):
            if u >> k & 1:
                F = F - eta[k] * P[k]
        return F

    def dark_ok(p, n, u):
        g = 1.0
        for k in range(n):
            if u >> k & 1:
                g *= 1.0 - p[k]
        return g

    # P(no detector of the sets ua (A), ub (B) clicks) for every pair of sets (bit masks)
    none = np.empty((1 << na, 1 << nb))
    FA = [blind(ea, PA, na, u) for u in range(1 << na)]
    FB = [blind(eb, PB, nb, u) for u in range(1 << nb)]
    for ua in range(1 << na):
        for ub in range(1 << nb):
            q = float(np.real(np.einsum("ijkl,ki,lj->", R4, FA[ua], FB[ub])))
            g = q if mu is None else math.exp(-mu * (1.0 - q))
            none[ua, ub] = g * dark_ok(da, na, ua) * dark_ok(db, nb, ub)

    def subsets(mask: int):
        sub = mask
        while True:
            yield sub
            if sub == 0:
                return
            sub = (sub - 1) & mask

    full_a, full_b = (1 << na) - 1, (1 << nb) - 1
    out = np.empty((len(_PATTERNS[na]), len(_PATTERNS[nb])))
    for i, ca in enumerate(_PATTERNS[na]):
        for j, cb in enumerate(_PATTERNS[nb]):
            tot = 0.0
            for wa in subsets(ca):
                for wb in subsets(cb):
                    sign = -1.0 if (bin(wa).count("1") + bin(wb).count("1")) % 2 else 1.0
                    tot += sign * none[(full_a & ~ca) | wa, (full_b & ~cb) | wb]
            out[i, j] = tot
    return Q.born_probabilities(out, dim=16)


def sample_counts(probs, n: int, rng) -> np.ndarray:
    """The outcome counts of n independent trials (multinomial) with the probabilities ``probs`` (any shape)."""
    p = np.asarray(probs, float)
    return rng.multinomial(int(n), p.ravel() / p.sum()).reshape(p.shape)


def plus_table(table) -> np.ndarray:
    """A 2 x 2 table ("+", "0") from a two-detector table: "+" when the station's "+" detector clicked (alone or with
    the "-" one), "0" otherwise; a 2 x 2 table is returned as it is."""
    t = np.asarray(table)
    def g(x, axis):
        if x.shape[axis] == 2:
            return x
        plus = np.take(x, [0, 3], axis=axis).sum(axis=axis)
        zero = np.take(x, [1, 2], axis=axis).sum(axis=axis)
        return np.stack([plus, zero], axis=axis)
    return g(g(t, 0), 1)


# --- CH, J and their errors --------------------------------------------------------------------------------------
def _linear(tables, coeffs, counts: bool):
    """sum over setting pairs s of sum_k c_sk f_sk (f the outcome frequencies of s; for probabilities, f = p) and, for
    counts, its multinomial standard error sqrt(sum_s (sum_k c^2 f - (sum_k c f)^2) / N_s)."""
    val, var = 0.0, 0.0
    for s, c in coeffs.items():
        t = np.asarray(tables[s[0]][s[1]], float)
        c = np.asarray(c, float)
        if counts:
            n = t.sum()
            if n <= 0:
                return None, None
            f = t / n
        else:
            f = t
        m = float(np.sum(c * f))
        val += m
        if counts:
            var += max(float(np.sum(c * c * f)) - m * m, 0.0) / n
    return val, (math.sqrt(var) if counts else None)


def _j_coeffs():
    c11 = np.array([[1.0, 0.0], [0.0, 0.0]])   # + p++(a1 b1)
    c12 = np.array([[0.0, -1.0], [0.0, 0.0]])  # - p+0(a1 b2)
    c21 = np.array([[0.0, 0.0], [-1.0, 0.0]])  # - p0+(a2 b1)
    c22 = np.array([[-1.0, 0.0], [0.0, 0.0]])  # - p++(a2 b2)
    return {(0, 0): c11, (0, 1): c12, (1, 0): c21, (1, 1): c22}


def j_value(probs) -> float:
    """J = p++(a1 b1) - p+0(a1 b2) - p0+(a2 b1) - p++(a2 b2) from the outcome probabilities ``probs[i][j]`` (2 x 2
    tables ("+", "0") of the setting pair (a_{i+1}, b_{j+1}); two-detector tables are reduced by ``plus_table``).
    Local realism: J <= 0."""
    return _linear([[plus_table(probs[i][j]) for j in (0, 1)] for i in (0, 1)], _j_coeffs(), False)[0]


def j_estimate(counts):
    """(J, se) from the outcome counts of the four setting pairs (``counts[i][j]``, as ``j_value``); each term from
    its own setting pair, so the error is the multinomial one of each; (None, None) when a setting pair has no
    trials. The significance J/se assumes i.i.d. trials."""
    return _linear([[plus_table(counts[i][j]) for j in (0, 1)] for i in (0, 1)], _j_coeffs(), True)


def _ch_coeffs(n):
    """Gisin and Gisin's (15) per trial with a = index 0, a' = 1, b = 0, b' = 1: p++(a,b) + p++(a,b') + p++(a',b) -
    p++(a',b') - p+.(a) - p.+(b); the singles pooled over the trials of their setting (weights N_s / N_setting)."""
    na = n[0][0] + n[0][1]
    nb = n[0][0] + n[1][0]
    plus_a = np.array([[1.0, 1.0], [0.0, 0.0]])
    plus_b = np.array([[1.0, 0.0], [1.0, 0.0]])
    pp = np.array([[1.0, 0.0], [0.0, 0.0]])
    return {(0, 0): pp - plus_a * n[0][0] / na - plus_b * n[0][0] / nb,
            (0, 1): pp - plus_a * n[0][1] / na,
            (1, 0): pp - plus_b * n[1][0] / nb,
            (1, 1): -pp}


def ch_value(probs) -> float:
    """CH in Gisin and Gisin's form (15) per trial from the outcome probabilities (as ``j_value``); local realism:
    CH <= 0. Equal to J when the marginals do not depend on the distant setting (no signalling)."""
    t = [[plus_table(probs[i][j]) for j in (0, 1)] for i in (0, 1)]
    return _linear(t, _ch_coeffs([[1.0, 1.0], [1.0, 1.0]]), False)[0]


def ch_estimate(counts):
    """(CH, se) from the outcome counts of the four setting pairs (as ``j_estimate``; the singles p+.(a), p.+(b) from
    all the trials with that setting)."""
    t = [[plus_table(counts[i][j]) for j in (0, 1)] for i in (0, 1)]
    n = [[float(np.sum(t[i][j])) for j in (0, 1)] for i in (0, 1)]
    if min(min(r) for r in n) <= 0:
        return None, None
    return _linear(t, _ch_coeffs(n), True)


# --- CHSH from coincidences, with the accidentals --------------------------------------------------------------
def accidentals(singles_a, singles_b, w: float, duration: float) -> np.ndarray:
    """N_acc = w N_A N_B / T for every pair of detectors (Dehlinger and Mitchell 2002, Table I: tau N_A N_B / T): the
    expected accidental coincidences within |t_B - t_A| <= w/2 of singles N_A, N_B counted over a time T."""
    return w * np.outer(np.asarray(singles_a, float), np.asarray(singles_b, float)) / duration


def correlation_subtracted(counts, acc=(0.0, 0.0, 0.0, 0.0), acc_se=(0.0, 0.0, 0.0, 0.0)):
    """(E, se, N) from coincidences (N++, N+-, N-+, N--) with the accidentals' estimates ``acc`` (same order)
    subtracted: E = (P - M)/(P + M), P = N++ + N-- - A++ - A--, M = N+- + N-+ - A+- - A-+; the error propagates
    Poisson counts (var N) and the accidentals' own errors ``acc_se``. With acc = 0 it equals ``correlation``.
    (None, None, N) when P + M <= 0."""
    n = np.asarray(counts, float)
    a = np.asarray(acc, float)
    sa = np.asarray(acc_se, float)
    net = n - a
    P, M = net[0] + net[3], net[1] + net[2]
    tot = P + M
    if tot <= 0:
        return None, None, float(tot)
    E = (P - M) / tot
    dP, dM = 2.0 * M / tot ** 2, -2.0 * P / tot ** 2  # dE/dP, dE/dM
    var = dP ** 2 * (n[0] + n[3] + sa[0] ** 2 + sa[3] ** 2) + dM ** 2 * (n[1] + n[2] + sa[1] ** 2 + sa[2] ** 2)
    return float(E), math.sqrt(max(var, 0.0)), float(tot)


def chsh_subtracted(cells, accs=None, acc_ses=None, signs=CHSH_SIGNS, keys=None):
    """(S, se) as ``chsh`` from four coincidence tuples with their accidentals subtracted (``accs``, ``acc_ses``: one
    4-tuple per cell, default none); under fair sampling, so named."""
    accs = accs if accs is not None else [(0.0,) * 4] * 4
    acc_ses = acc_ses if acc_ses is not None else [(0.0,) * 4] * 4
    S = 0.0
    var = 0.0
    for i, w in _groups(signs, keys):
        E, se, n = correlation_subtracted(cells[i], accs[i], acc_ses[i])
        if E is None:
            return None, None
        S += w * E
        var += w * w * se * se
    return S, math.sqrt(var)


# --- the efficiency thresholds ------------------------------------------------------------------------------------
def j_polarisers(state, angles, eta_a, eta_b, p_dark_a=0.0, p_dark_b=0.0, mu=None) -> float:
    """J (``j_value``) of one-detector stations with polarisers at ``angles`` = (a1, a2, b1, b2) (rad, from H), each
    followed by one detector behind the transmitted port: per pair (mu None) or per slot."""
    a1, a2, b1, b2 = angles
    tab = [[slot_probabilities(state, [Q.polarizer_projectors(a)[0]], [Q.polarizer_projectors(b)[0]], eta_a, eta_b,
                               p_dark_a, p_dark_b, mu) for b in (b1, b2)] for a in (a1, a2)]
    return j_value(tab)


def best_j(state, eta_a, eta_b, p_dark_a=0.0, p_dark_b=0.0, mu=None, starts: int = 24, seed: int = 0, x0=None):
    """(J_max, angles): the largest J over the four polariser angles, by Nelder-Mead from ``starts`` random starts
    (seeded) and ``x0`` if given. A direct search, not a proof of the maximum."""
    rng = np.random.default_rng(seed)
    f = lambda x: -j_polarisers(state, x, eta_a, eta_b, p_dark_a, p_dark_b, mu)  # noqa: E731
    xs = [np.asarray(x0, float)] if x0 is not None else []
    xs += [rng.uniform(-math.pi / 2, math.pi / 2, 4) for _ in range(starts)]
    best = (-math.inf, None)
    for x in xs:
        r = optimize.minimize(f, x, method="Nelder-Mead",
                              options={"xatol": 1e-9, "fatol": 1e-15, "maxiter": 4000, "maxfev": 8000})
        if -r.fun > best[0]:
            best = (float(-r.fun), np.mod(r.x + math.pi / 2, math.pi) - math.pi / 2)
    return best


def threshold_efficiency(state, p_dark=0.0, mu=None, lo: float = 0.5, hi: float = 1.0, tol: float = 1e-5,
                         starts: int = 12, seed: int = 0) -> float:
    """The smallest equal efficiency eta_A = eta_B at which ``best_j`` finds J > 0 (bisection on [lo, hi]; the best
    angles of the previous step start the next search). math.nan when J <= 0 even at ``hi``."""
    j_hi, x = best_j(state, hi, hi, p_dark, p_dark, mu, starts, seed)
    if j_hi <= 0.0:
        return math.nan
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        j, xm = best_j(state, mid, mid, p_dark, p_dark, mu, starts, seed, x0=x)
        if j > 0.0:
            hi, x = mid, xm
        else:
            lo = mid
    return 0.5 * (lo + hi)
