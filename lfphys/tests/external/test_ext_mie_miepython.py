# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.core.optics.mie`` against miepython 3.3.0 (plan items P1 and P13, batch B8).

Compared, for transparent, absorbing, m < 1 and strongly absorbing spheres from x = 0.1 to 10^4: the efficiencies
Q_ext, Q_sca, Q_back and g (``mie.efficiencies`` against ``miepython.efficiencies_mx``), the amplitudes S1, S2 at six
angles (``mie.amplitudes`` against ``miepython.S1_S2(..., norm="wiscombe")``, which is unnormalised) and the
coefficients a_n, b_n at three orders (``mie.coefficients`` against ``miepython.coefficients``).

Conventions (miepython's documentation, its API pages for ``efficiencies_mx``: "m = n - ik", and ``coefficients``:
"If the imaginary part of the refractive index is positive, it is automatically corrected to its conjugate value"):
miepython is given conj(m). Measured here (``test_conventions``): its a_n, b_n equal the engine's (Bohren & Huffman's,
exp(-i omega t)), while its S1, S2 are the complex conjugates (Wiscombe's exp(+i omega t)); the rows compare
conj(S_miepython). miepython sums the series to Wiscombe's number of terms N_W = x + 4.05 x^(1/3) + 2 without margin;
the engine to N_W + 16 (the tail trimmed below 1e-20).

Exact reference: the same series in 40-digit mpmath for the same binary64 inputs (D_n(mx) downward from
N + |mx| + 20 |mx|^(1/3) + 60, psi_n(x) by Miller's algorithm, chi_n(x) upward, then the sums), summed to the engine's
N: eng err and lib err; and the exact coefficients' sensitivities x |da_n/dx| by a 50-digit forward difference
(relative step 1e-22). [error in earlier] the start was N + |mx| + 60, not enough when |mx| >> N (review B8-mie, M9;
no case here has |mx| >> N).

Tolerance "coefficient budgets + truncation" (derived per row; the two sides' bounds added):
* the engine: its tested coefficient bound (``mie.coefficient_bound``: u (4 N + 8 s) of the largest coefficient, s the
  largest sensitivity x |da_n/dx| / max|a| of the case, a mixed forward-backward bound; tests/test_mie.py checks it
  against Arb and 50-digit references, also on resonance peaks) propagated through the row's formula with the moduli
  of its partial derivatives (Q_ext: (2/x^2)(2n+1); Q_sca: (4/x^2)(2n+1)|a_n|; Q_back: (2/x^2)(2n+1)|sum|; g: through
  g Q_sca and Q_sca; S: c_n |pi_n|, c_n |tau_n|), plus gamma_{8N} times the moduli of the summed terms (the sum's
  rounding). [error in earlier] the engine's budget was a blanket 2e-11 (1e-12 for x <= 1000 in this docstring),
  which does not hold on narrow resonances (review B8-mie, M1, M8);
* miepython: the measured distance of its own coefficients to the exact ones (the largest over n <= its N, on the
  same case), propagated the same way, plus the omitted tail (the exact terms n > N_W of the row's formula, summed in
  mpmath), plus gamma_{8N} times the moduli. The library has no stated error bound; its coefficient error is
  measured, so its Q and S rows test its sums and angular functions given those coefficients.
Tolerance "stated bound + 16N u" (the coefficient rows): the engine's tested bound (with the sensitivity of that
order) plus 16 N u of the largest coefficient for the library's recurrences (a rounding allowance of 16 operations per
order). Known disagreements are kept as strict xfails with their numbers: miepython's coefficients carry an error of
about the same size at every order, ~3e-13 of the largest coefficient at x = 100, ~1e-12 at x = 1000, ~1.1e-9 at
x = 10^4 (up to 3e-8 near n ~ x) (``test_miepython_coefficient_error_by_order``); the two rows at x = 100 became xfails
when the engine's budget became its honest bound instead of the blanket 2e-11, which had covered them. [error in
earlier] the xfail text said "its top orders lose accuracy", while the rows that fail are n = 1 and n = N/2 (review
B8-mie, M8).
"""

from __future__ import annotations

import functools
import math

import mpmath as mp
import numpy as np
import pytest

import miepython

from lfphys.core.optics import mie

from _common import U, Row, check, gamma, params

GROUP = "miepython"
DPS = 40
ANGLES = (0.0, 30.0, 90.0, 137.9, 170.0, 180.0)
CASES = [  # (m in the engine's convention, x)
    (1.333, 0.1), (1.333, 1.0), (1.333, 10.0), (1.333, 100.0), (1.333, 1000.0), (1.333, 1e4),
    (1.333 + 1e-8j, 500.0), (1.5 + 0.1j, 1.0), (1.5 + 0.1j, 100.0), (1.5 + 0.1j, 3000.0), (0.75, 30.0),
    (0.75, 300.0), (2.0 + 1.0j, 0.1), (2.0 + 1.0j, 10.0), (10.0 + 10.0j, 50.0),
]


def _exact(m, x, N, dps=DPS, h=0):
    """a_n, b_n (n = 1..N) and the mpmath context's values, by the textbook recurrences at dps digits, at the binary64
    x times (1 + h) (h = 0: x itself)."""
    with mp.workdps(dps):
        m = mp.mpc(m)
        x = mp.mpf(x) * (1 + mp.mpf(h))
        mx = m * x
        top = N + int(abs(complex(mx))) + int(20 * abs(complex(mx)) ** (1.0 / 3.0)) + 60
        D = mp.mpc(0)
        Dm = [None] * (N + 1)
        Dx = mp.mpf(0)
        Dxs = [None] * (N + 2)
        for n in range(top, 0, -1):
            if n <= N:
                Dm[n] = D
            if n <= N + 1:
                Dxs[n] = Dx
            D = n / mx - 1 / (D + n / mx)
            Dx = n / x - 1 / (Dx + n / x)
        P = [mp.mpf(0)] * (N + 1)
        P[N] = mp.mpf(1)
        for n in range(N, 0, -1):
            P[n - 1] = P[n] * (Dxs[n] + n / x)
        s = mp.sin(x)
        p1 = s / x - mp.cos(x)
        sc = s / P[0] if abs(s) >= abs(p1) else p1 / P[1]
        P = [p * sc for p in P]
        X = [mp.cos(x)]
        prev = -mp.sin(x)
        for n in range(1, N + 1):
            X.append((2 * n - 1) / x * X[-1] - prev)
            prev = X[-2]
        a, b = [], []
        for n in range(1, N + 1):
            xi, xi1 = P[n] - 1j * X[n], P[n - 1] - 1j * X[n - 1]
            ta, tb = Dm[n] / m + n / x, Dm[n] * m + n / x
            a.append((ta * P[n] - P[n - 1]) / (ta * xi - xi1))
            b.append((tb * P[n] - P[n - 1]) / (tb * xi - xi1))
        return a, b


def _sums(a, b, x, mus, upto):
    """Exact Q_ext, Q_sca, Q_back, g, S1(mu), S2(mu) from the first ``upto`` coefficients (mpmath)."""
    with mp.workdps(DPS):
        x = mp.mpf(x)
        qe = qs = gq = mp.mpf(0)
        sb = mp.mpc(0)
        for n in range(1, upto + 1):
            an, bn = a[n - 1], b[n - 1]
            qe += (2 * n + 1) * (an.real + bn.real)
            qs += (2 * n + 1) * (abs(an) ** 2 + abs(bn) ** 2)
            sb += (2 * n + 1) * (-1) ** n * (an - bn)
            if n < upto:
                gq += mp.mpf(n * (n + 2)) / (n + 1) * (an * mp.conj(a[n]) + bn * mp.conj(b[n])).real
            gq += mp.mpf(2 * n + 1) / (n * (n + 1)) * (an * mp.conj(bn)).real
        out = {"Qext": 2 * qe / x ** 2, "Qsca": 2 * qs / x ** 2, "Qback": abs(sb) ** 2 / x ** 2}
        out["g"] = 4 * gq / x ** 2 / out["Qsca"]
        S = []
        for mu in mus:
            mu = mp.mpf(mu)
            p0, p1 = mp.mpf(0), mp.mpf(1)
            s1 = s2 = mp.mpc(0)
            for n in range(1, upto + 1):
                if n > 1:
                    p0, p1 = p1, ((2 * n - 1) * mu * p1 - n * p0) / (n - 1)
                tau = n * mu * p1 - (n + 1) * p0
                c = mp.mpf(2 * n + 1) / (n * (n + 1))
                s1 += c * (a[n - 1] * p1 + b[n - 1] * tau)
                s2 += c * (a[n - 1] * tau + b[n - 1] * p1)
            S.append((s1, s2))
        out["S"] = S
        return out


def _weights(a, b, x, mus):
    """The moduli of the partial derivatives of each row's quantity with respect to |a_n|, |b_n| (summed over n),
    and the moduli of the summed terms (for the rounding of the sums), from float coefficients."""
    N = len(a)
    n = np.arange(1, N + 1, dtype=float)
    f = 2.0 / x ** 2
    sb = abs(np.sum((2 * n + 1) * (-1.0) ** n * (a - b)))
    q = mie.efficiencies_from(a, b, x)
    w = {"Qext": f * np.sum(2 * (2 * n + 1)), "Qsca": f * np.sum((2 * n + 1) * 2 * (np.abs(a) + np.abs(b))),
         "Qback": 2 * sb * np.sum(2 * (2 * n + 1)) / x ** 2}
    mods = {"Qext": f * np.sum((2 * n + 1) * (np.abs(a) + np.abs(b))), "Qsca": q["Qsca"],
            "Qback": (np.sum((2 * n + 1) * (np.abs(a) + np.abs(b)))) ** 2 / x ** 2}
    ap, bp = np.abs(np.append(a, 0.0)), np.abs(np.append(b, 0.0))
    am = np.abs(np.insert(a, 0, 0.0))[:-1]
    bm = np.abs(np.insert(b, 0, 0.0))[:-1]
    c1 = n * (n + 2) / (n + 1)
    c0 = (n - 1) * (n + 1) / np.maximum(n, 1)
    wgq = 4 / x ** 2 * np.sum(c1 * (ap[1:] + bp[1:]) + c0 * (am + bm) + (2 * n + 1) / (n * (n + 1)) * 2)
    mgq = 4 / x ** 2 * np.sum(c1 * (ap[:-1] * ap[1:] + bp[:-1] * bp[1:]) + (2 * n + 1) / (n * (n + 1)) * ap[:-1] * bp[:-1])
    w["g"] = (wgq + abs(q["g"]) * w["Qsca"]) / q["Qsca"]
    mods["g"] = (mgq + abs(q["g"]) * q["Qsca"]) / q["Qsca"]
    PI, TAU = mie.angular(np.asarray(mus), N)
    c = (2 * n + 1) / (n * (n + 1))
    w["S"] = c @ (np.abs(PI) + np.abs(TAU))
    mods["S1"] = (c * np.abs(a)) @ np.abs(PI) + (c * np.abs(b)) @ np.abs(TAU)
    mods["S2"] = (c * np.abs(a)) @ np.abs(TAU) + (c * np.abs(b)) @ np.abs(PI)
    return w, mods


def _c(v):
    return complex(v)


def _case_rows(m, x):
    mus = [math.cos(math.radians(t)) for t in ANGLES]
    ae, be = mie.coefficients(m, x)
    N = len(ae)
    al, bl = (np.asarray(v) for v in miepython.coefficients(np.conj(m), x))
    NL = len(al)
    ea, eb = _exact(m, x, max(N, NL))
    full = _sums(ea, eb, x, mus, N)
    trunc = _sums(ea, eb, x, mus, NL)
    ex_a = np.array([_c(v) for v in ea])
    ex_b = np.array([_c(v) for v in eb])
    amax = max(np.abs(ex_a).max(), np.abs(ex_b).max())
    sens = _sensitivity(m, x, max(N, NL)) / amax
    de_n = mie.coefficient_bound(x, sens) * amax  # per order
    de = float(de_n[:N].max())
    dl = max(np.abs(al - ex_a[:NL]).max(), np.abs(bl - ex_b[:NL]).max())
    w, mods = _weights(ae, be, x, mus)
    g8 = gamma(8 * N)
    inp = f"m={m}, x={x:g}"
    out = []
    qe, qs, qb, g = (float(v) for v in miepython.efficiencies_mx(np.conj(m), x))
    qeng = mie.efficiencies_from(ae, be, x)
    for key, lib in (("Qext", qe), ("Qsca", qs), ("Qback", qb), ("g", g)):
        ref = float(full[key])
        tail = abs(float(full[key] - trunc[key]))
        tol = (de * w[key] + g8 * mods[key]) + (dl * w[key] + tail + g8 * mods[key])
        out.append(Row(GROUP, f"efficiencies {key}", inp, qeng[key], lib, tol, "coefficient budgets + truncation",
                       eng_err=abs(qeng[key] - ref), lib_err=abs(lib - ref)))
    S1l, S2l = miepython.S1_S2(np.conj(m), x, np.array(mus), norm="wiscombe")
    S1e, S2e = mie.amplitudes(ae, be, np.arccos(mus))
    for k, th in enumerate(ANGLES):
        for name, eng, lib, ref, rtr, mod in (("S1", S1e[k], np.conj(S1l[k]), full["S"][k][0], trunc["S"][k][0],
                                               mods["S1"][k]),
                                              ("S2", S2e[k], np.conj(S2l[k]), full["S"][k][1], trunc["S"][k][1],
                                               mods["S2"][k])):
            tail = abs(_c(ref - rtr))
            tol = (de * w["S"][k] + g8 * mod) + (dl * w["S"][k] + tail + g8 * mod)
            out.append(Row(GROUP, f"amplitude {name} (conj of miepython's)", f"{inp}, theta={th:g} deg", complex(eng),
                           complex(lib), tol, "coefficient budgets + truncation", eng_err=abs(complex(eng) - _c(ref)),
                           lib_err=abs(complex(lib) - _c(ref))))
    for n in sorted({1, max(1, NL // 2), NL}):
        for name, eng, lib, ref in (("a", ae[n - 1], al[n - 1], ex_a[n - 1]), ("b", be[n - 1], bl[n - 1], ex_b[n - 1])):
            tol = float(de_n[n - 1]) + 16 * NL * U * amax
            row = Row(GROUP, f"coefficient {name}_n", f"{inp}, n={n}", complex(eng), complex(lib), tol,
                      "stated bound + 16N u", eng_err=abs(complex(eng) - ref), lib_err=abs(complex(lib) - ref))
            if not row.ok and row.lib_err > row.tol and row.eng_err <= de_n[n - 1]:
                row.xfail = (f"miepython's {name}_{n} is {row.lib_err / amax:.2e} of the largest coefficient from the "
                             f"exact value (the engine's {row.eng_err / amax:.2e}), beyond the 16 N u allowance: its "
                             f"coefficients carry an error of that size at every order, ~3e-13 at x = 100, ~1e-12 at "
                             f"1000, ~1.1e-9 at 1e4 (up to 3e-8 near n ~ x) (measured, "
                             f"test_miepython_coefficient_error_by_order)")
            out.append(row)
    return out


def _sensitivity(m, x, N, h=1e-22):
    """x |d a_n/dx| and x |d b_n/dx| of the exact coefficients (the larger of the two, per order): a forward difference
    with relative step h in 50 digits (truncation ~h x/Gamma relative for a resonance of width Gamma; rounding
    1e-50/h)."""
    with mp.workdps(50):
        a0, b0 = _exact(m, x, N, dps=50)
        a1, b1 = _exact(m, x, N, dps=50, h=h)
        return np.array([max(float(abs(p - q)), float(abs(r - t))) / h for p, q, r, t in zip(a1, a0, b1, b0)])


@functools.lru_cache(maxsize=None)
def rows() -> list[Row]:
    out = []
    for m, x in CASES:
        out += _case_rows(m, x)
    return out


@pytest.mark.parametrize("row", params(rows()))
def test_mie(row):
    check(row)


def test_conventions():
    """miepython takes m = n - ik (and conjugates a positive imaginary part itself); its a_n, b_n are the engine's,
    its S1, S2 (norm "wiscombe") the complex conjugates of the engine's; Q_ext = 4/x^2 Re S(0) holds for its
    conjugated S(0) as for the engine's."""
    m, x = 1.5 + 0.1j, 3.0
    a, b = (np.asarray(v) for v in miepython.coefficients(np.conj(m), x))
    a2, _ = (np.asarray(v) for v in miepython.coefficients(m, x))
    ae, be = mie.coefficients(m, x)
    n = len(a)
    assert np.allclose(a, ae[:n], rtol=1e-12, atol=1e-15) and np.allclose(a2, a)
    S1, _ = miepython.S1_S2(np.conj(m), x, np.array([1.0]), norm="wiscombe")
    s1, _ = mie.amplitudes(ae, be, np.array([0.0]))
    assert abs(np.conj(S1[0]) - s1[0]) <= 1e-9 * abs(s1[0]) and abs(S1[0] - s1[0]) > 1e-3 * abs(s1[0])
    qe = float(miepython.efficiencies_mx(np.conj(m), x)[0])
    assert abs(4 / x ** 2 * np.conj(S1[0]).real - qe) <= 1e-9 * qe


def test_miepython_number_of_terms_is_wiscombes():
    """The truncation the tolerances account for: miepython stops at Wiscombe's N (Eq. 50 of NCAR/TN-140)."""
    for x in (10.0, 100.0, 1000.0, 5000.0):
        a, _ = miepython.coefficients(1.333, x)
        assert abs(len(a) - mie.n_wiscombe(x)) <= 1, (x, len(a), mie.n_wiscombe(x))


def test_miepython_coefficient_error_by_order():
    """The cause of the coefficient xfails (review B8-mie, M8): at x = 10^4 miepython's coefficients are ~1.1e-9 of
    the largest coefficient from the exact ones at every order (measured: 1.0-1.3e-9 for n <= 5044, the xfailed rows
    n = 1 and N/2 among them), up to 3e-8 near n ~ x; at x = 1000 ~1e-12 at every order (1.5e-10 near n ~ x); at
    x = 100 ~3e-13 (the xfailed n = 1 and 60); at x = 10, ~1e-15. The engine stays within its bound u (4N + 8 s)
    everywhere."""
    out = {}
    for x in (10.0, 100.0, 1000.0, 1e4):
        al, bl = (np.asarray(v) for v in miepython.coefficients(1.333, x))
        N = len(al)
        ea, eb = _exact(1.333, x, N)
        ea = np.array([_c(v) for v in ea])
        eb = np.array([_c(v) for v in eb])
        amax = max(np.abs(ea).max(), np.abs(eb).max())
        err = np.maximum(np.abs(al - ea), np.abs(bl - eb)) / amax
        out[x] = err
        ae, be = mie.coefficients(1.333, x, n_max=N)
        erre = np.maximum(np.abs(ae - ea), np.abs(be - eb)) / amax
        assert np.all(erre <= mie.coefficient_bound(x, _sensitivity(1.333, x, N) / amax))
    low = out[1e4][:N // 2]  # n = 1 .. N/2 at x = 1e4: the same size at every order
    assert 5e-10 < np.median(low) < 2e-9 and low.max() < 3e-9 and low[0] > 5e-10
    assert out[1e4].max() > 1e-8  # near n ~ x
    assert np.median(out[1000.0]) < 3e-12 and out[10.0].max() < 1e-13
    assert 1e-13 < np.median(out[100.0][:60]) < 1e-12
