# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.core.qcd.running`` against CRunDec 3.1 (plan item P13), through its Python bindings ``rundec`` 0.7: the
MS-bar coupling alpha_s(mu) at 1 to 4 loops with a fixed number of flavours, the same across the heavy-quark
thresholds (MS-bar decoupling at mu = m_h(m_h), as in the engine), and the decoupling relations alone.

What CRunDec is asked for. Running: ``AlphasExact(alpha0, mu0, mu, nf, loops)``. Thresholds: the engine's convention
reproduced with CRunDec's pieces, segment by segment: run with n_f flavours to mu = m_h, then
``DecAsDownMS(alpha, m_h, m_h, n_l, loops)`` going down or ``DecAsUpMS(alpha, m_h, m_h, n_l, loops)`` going up (both
with ``loops``-loop running taking (loops-1)-loop matching, the convention of RunDec and of the engine). CRunDec's own
``AlH2AlL``/``AlL2AlH`` decouple at pole masses and are therefore not the same physics input; they are not used.
Inputs: alpha_s(M_Z) = 0.1180, M_Z = 91.1880 GeV, m_c(m_c) = 1.2730, m_b(m_b) = 4.183, m_t(m_t) = 162.5 GeV
(``lfphys.core.data``, PDG 2024).

Exact reference. For the binary64 inputs, the solution of da/dL = f(a) = -sum_i beta_i a^(i+2) (a = alpha_s/(4 pi),
L = ln mu^2) is found in 30-digit mpmath from L - L0 = integral_{a0}^{a} da'/f(a') (mpmath quad and findroot), with
the decoupling relations in mpmath at the thresholds: it gives each side's own error (eng_err, lib_err).

Tolerance "integrators" (derived from each side's stated error control):
* CRunDec integrates with an embedded Runge-Kutta pair (Cash-Karp coefficients) and accepts a step when its error
  estimate is below eps = 1e-10 in a = alpha_s/pi (CRunDec.3.1.cpp, fRungeKuttaImpl: "double eps=1e-10"). Its stated
  error control thus allows pi eps in alpha_s per accepted step (the estimate is that of the embedded fourth-order
  solution; CRunDec keeps the fifth-order one), times the step's propagation factor G to the end of the run.
* The engine integrates with scipy's DOP853, rtol = 1e-12 and atol = 1e-16 on a = alpha_s/(4 pi) (running.py): local
  error estimates below atol + rtol |a| per accepted step, i.e. 4 pi (atol + rtol max|a|) per step in alpha_s.
* The number of accepted steps: for CRunDec from a re-implementation of its step-size control (described below; it
  must reproduce CRunDec's result to 1e-14 relative, which test_crundec_step_count_reproduces_crundec checks); for the
  engine by recording scipy's solve_ivp result while the engine calls it (``running.integrate`` is wrapped, the
  engine's code is unchanged).
* Propagation: for an autonomous equation da/dL = f(a), an error at a_k reaches the end multiplied by exactly
  f(a_end)/f(a_k); within a segment this is at most max(1, f(a_end)/f(a_start)) (|f| grows with a), and later segments
  and decoupling steps multiply it by their own f(a_out)/f(a_in) and d(alpha_out)/d(alpha_in).
Known disagreement (strict xfail): a CRunDec run over |ln(mu/mu0)| < 1e-4 ends at mu0 e^(+-1e-4) instead of mu
(test_crundec_short_range_lands_at_its_first_step); it affects the rows that end within 1e-4 beyond a threshold.
Tolerance "decoupling": both sides evaluate alpha (1 + c2 a^2 + c3 a^3) in at most 16 roundings per term (the
coefficients with zeta_3, a = alpha/pi, the powers and products, the sum): 2 gamma_16 alpha (1 + |c2| a^2 + |c3| a^3).
"""

from __future__ import annotations

import functools
import math
from types import SimpleNamespace

import mpmath as mp
import pytest
import rundec
from scipy import integrate as sp_integrate

from lfphys.core import data
from lfphys.core.qcd import running

from _common import Row, check, gamma, params

GROUP = "alpha_s (CRunDec)"
A_MZ, M_Z = data.ALPHA_S_MZ[0], data.M_Z[0]
TH = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
CRD_EPS = 1e-10  # CRunDec 3.1, fRungeKuttaImpl
ENG_RTOL, ENG_ATOL = 1e-12, 1e-16  # lfphys.core.qcd.running._evolve
CRD = rundec.CRunDec()

# --- exact reference (mpmath) ---------------------------------------------------------------------------------------

DPS = 30  # digits of the exact reference (mpmath precision is set per function, not globally)
with mp.workdps(DPS + 10):
    Z3 = mp.zeta(3)


def mp_betas(nf: int, loops: int):
    nf = mp.mpf(nf)
    b = [11 - mp.mpf(2) / 3 * nf,
         102 - mp.mpf(38) / 3 * nf,
         mp.mpf(2857) / 2 - mp.mpf(5033) / 18 * nf + mp.mpf(325) / 54 * nf ** 2,
         (mp.mpf(149753) / 6 + 3564 * Z3) - (mp.mpf(1078361) / 162 + mp.mpf(6508) / 27 * Z3) * nf
         + (mp.mpf(50065) / 162 + mp.mpf(6472) / 81 * Z3) * nf ** 2 + mp.mpf(1093) / 729 * nf ** 3]
    return b[:loops]


def mp_run(alpha0, mu0, mu1, nf, loops, guess):
    """alpha_s(mu1) from alpha_s(mu0) with nf flavours, exactly (30 digits) for these inputs."""
    if mu0 == mu1:
        return mp.mpf(alpha0)
    b = mp_betas(nf, loops)
    f = lambda a: -sum(bi * a ** (i + 2) for i, bi in enumerate(b))  # noqa: E731
    a0 = mp.mpf(alpha0) / (4 * mp.pi)
    dL = 2 * (mp.log(mp.mpf(mu1)) - mp.log(mp.mpf(mu0)))
    a = mp.findroot(lambda a: mp.quad(lambda x: 1 / f(x), [a0, a]) - dL, mp.mpf(guess) / (4 * mp.pi))
    return 4 * mp.pi * a


def mp_dec(alpha, n_l, loops, down):
    a = alpha / mp.pi
    c2 = mp.mpf(11) / 72 if loops >= 3 else 0
    c3 = (mp.mpf(564731) / 124416 - mp.mpf(82043) / 27648 * Z3 - mp.mpf(2633) / 31104 * n_l) if loops >= 4 else 0
    return alpha * (1 + c2 * a * a + c3 * a ** 3) if down else alpha * (1 - c2 * a * a - c3 * a ** 3)


def f_beta(alpha, nf, loops):
    """d alpha / d ln mu^2 in float (the propagation factors only need a few digits)."""
    a = alpha / (4 * math.pi)
    return -4 * math.pi * sum(b * a ** (i + 2) for i, b in enumerate(running.beta_coefficients(nf, loops)))


# --- CRunDec's integrator: number of accepted steps -----------------------------------------------------------------

# Cash & Karp, ACM Trans. Math. Softw. 16, 201 (1990): the embedded 5(4) pair that CRunDec uses
CK_B = ((), (0.2,), (3 / 40, 9 / 40), (0.3, -0.9, 6 / 5), (-11 / 54, 2.5, -70 / 27, 35 / 27),
        (1631 / 55296, 175 / 512, 575 / 13824, 44275 / 110592, 253 / 4096))
CK_C = (37 / 378, 0.0, 250 / 621, 125 / 594, 0.0, 512 / 1771)
CK_DC = (37 / 378 - 2825 / 27648, 0.0, 250 / 621 - 18575 / 48384, 125 / 594 - 13525 / 55296, 0.0 - 277 / 14336,
         512 / 1771 - 0.25)
ZETA3_F = 1.2020569031595942  # CRunDec's Zeta3 macro rounded to binary64


def crd_betas(nf: int):
    """CRunDec's SetConstants: beta_i / 4^(i+1) (the coefficients in a = alpha_s/pi), loops 1-4."""
    nf = float(nf)
    return [0.25 * (11.0 - 2. * nf / 3.0),
            (102.0 - 38. * nf / 3.0) / 16.0,
            (0.5 * 2857. - 5033. * nf / 18.0 + 325. * nf * nf / 54.0) / 64.0,
            (149753. / 6.0 + 3564. * ZETA3_F + (-1078361. / 162.0 - 6508. * ZETA3_F / 27.0) * nf
             + (50065. / 162.0 + 6472. * ZETA3_F / 81.0) * nf * nf + 1093. * nf * nf * nf / 729.0) / 256.0]


def crd_replica(alpha0, mu0, mu1, nf, loops):
    """(alpha_s(mu1), accepted steps): CRunDec 3.1's AlphasExact re-implemented from its description: x = ln mu,
    y = alpha_s/pi, dy/dx = 2 sum_i (-Beta_i y^(i+2)); first step h = +-1e-4; a step is rejected while
    err = |yerr|/1e-10 > 1, the step then shrinking to max(0.9 h err^-0.25, 0.1 h); an accepted step takes the
    fifth-order value and the next step is 0.9 h err^-0.2 if err > 1.89e-4, else 5 h; the last step is cut to end at
    ln mu1."""
    beta = crd_betas(nf)

    def f(A):
        B = A * A
        s = (-beta[0] * B, -beta[1] * B * A, -beta[2] * B * B, -beta[3] * B * B * A)
        out = 0.0
        for i in range(loops):
            out += s[i]
        return out * 2

    x, y, end = math.log(mu0), alpha0 / math.pi, math.log(mu1)
    h = 1e-4 if mu0 < mu1 else -1e-4
    steps = 0
    while (x < end) if mu0 < mu1 else (x > end):
        while True:
            k = []
            for i in range(6):
                yi = y
                for j, bij in enumerate(CK_B[i]):
                    yi = yi + bij * k[j]
                k.append(h * f(yi))
            ytemp = y
            for i in range(6):
                ytemp = ytemp + CK_C[i] * k[i]
            yerr = 0.0
            for i in range(6):
                yerr = yerr + CK_DC[i] * k[i]
            err = max(0.0, abs(yerr / CRD_EPS))
            if err > 1.0:
                htemp = 0.9 * h * err ** -0.25
                h = max(htemp, 0.1 * h) if h >= 0 else min(htemp, 0.1 * h)
                if x + h == x:
                    raise RuntimeError("step size too small")
                continue
            hnext = 0.9 * h * err ** -0.2 if err > 1.89e-4 else 5.0 * h
            x += h
            y = ytemp
            h = hnext
            steps += 1
            break
        if (x + h >= end) if mu0 < mu1 else (x + h <= end):
            h = end - x
    return y * math.pi, steps


# --- the two sides along a path -------------------------------------------------------------------------------------

def _path(mu0, mu1, th):
    """Segments [(mu_a, mu_b, nf)] and threshold crossings, in the engine's convention (n_f counts m_q < mu)."""
    edges = sorted(th.values())
    up = mu1 > mu0
    nf = 3 + sum(1 for m in edges if m < mu0)
    cross = [m for m in edges if mu0 <= m < mu1] if up else sorted((m for m in edges if mu1 <= m < mu0), reverse=True)
    segs, cur = [], mu0
    for m in cross:
        if m != cur:
            segs.append((cur, m, nf))
        segs.append(("dec", m, nf))
        nf = nf + 1 if up else nf - 1
        cur = m
    if mu1 != cur:
        segs.append((cur, mu1, nf))
    return segs, up


class _StepCounter:
    """Wraps scipy.integrate for the engine module: records the number of accepted steps of each solve_ivp call."""

    def __init__(self):
        self.calls = []

    def solve_ivp(self, *args, **kw):
        sol = sp_integrate.solve_ivp(*args, **kw)
        self.calls.append(len(sol.t) - 1)
        return sol


def engine_alpha(mu, alpha0, mu0, th, loops):
    """The engine's alpha_s(mu) and its accepted DOP853 steps per segment (the engine's code is unchanged)."""
    counter = _StepCounter()
    saved = running.integrate
    running.integrate = SimpleNamespace(solve_ivp=counter.solve_ivp)
    try:
        val = running.alpha_s(mu, alpha0, mu0, th, loops)
    finally:
        running.integrate = saved
    return val, counter.calls


def library_alpha(mu, alpha0, mu0, th, loops):
    """CRunDec along the same path; also the exact value and the per-segment data for the tolerance."""
    segs, up = _path(mu0, mu, th)
    a_lib, a_ex = alpha0, mp.mpf(alpha0)
    trace = []  # (kind, alpha_in, alpha_out, nf, crd_steps, |ln(mu_out/mu_in)|)
    for s in segs:
        if s[0] == "dec":
            _, m, nf = s
            n_l = nf - 1 if not up else nf
            fn = CRD.DecAsDownMS if not up else CRD.DecAsUpMS
            new = fn(a_lib, m, m, n_l, loops)
            a_ex = mp_dec(a_ex, n_l, loops, down=not up)
            trace.append(("dec", a_lib, new, n_l, 0, 0.0))
            a_lib = new
        else:
            m0, m1, nf = s
            new = CRD.AlphasExact(a_lib, m0, m1, nf, loops)
            steps = crd_replica(a_lib, m0, m1, nf, loops)[1]
            a_ex = mp_run(a_ex, m0, m1, nf, loops, new)
            trace.append(("run", a_lib, new, nf, steps, abs(math.log(m1 / m0))))
            a_lib = new
    return a_lib, a_ex, trace


def tolerance(trace, eng_steps, loops):
    """Sum of both integrators' bounds along the path (module docstring)."""
    tol, G_after = 0.0, 1.0
    run_idx = [i for i, t in enumerate(trace) if t[0] == "run"]
    eng = list(eng_steps)
    if len(eng) != len(run_idx):
        raise AssertionError(f"engine segments {len(eng)} != path segments {len(run_idx)}")
    for t in reversed(trace):
        kind, a_in, a_out, nf, steps, _ = t
        if kind == "dec":
            h = 1e-7 * a_in
            down = a_out > a_in
            d = (running.decoupling(a_in + h, nf, loops, down) - running.decoupling(a_in - h, nf, loops, down)) / (2 * h)
            tol += G_after * 2 * gamma(16) * a_out * 1.1  # the relation's rounding (|c2| a^2 + |c3| a^3 < 0.1 here)
            G_after *= abs(d)
            continue
        ratio = abs(f_beta(a_out, nf, loops) / f_beta(a_in, nf, loops))
        G_within = max(1.0, ratio)
        n_eng = eng.pop()
        a_max = max(a_in, a_out) / (4 * math.pi)
        tol += G_after * G_within * (steps * math.pi * CRD_EPS + n_eng * 4 * math.pi * (ENG_ATOL + ENG_RTOL * a_max))
        G_after *= ratio
    return tol


CRD_H0 = 1e-4  # CRunDec's first step in ln mu (AlphasExact: h = 1e-4 or -1e-4)


def _row(quantity, label, mu, mu0, alpha0, th, loops):
    eng, eng_steps = engine_alpha(mu, alpha0, mu0, th, loops)
    lib, ex, trace = library_alpha(mu, alpha0, mu0, th, loops)
    row = Row(GROUP, quantity, label, eng, lib, tolerance(trace, eng_steps, loops), "integrators",
              float(abs(eng - ex)), float(abs(lib - ex)))
    short = [t[5] for t in trace if t[0] == "run" and t[5] < CRD_H0]
    if short:  # known CRunDec behaviour, test_crundec_short_range_lands_at_its_first_step
        row.xfail = (f"CRunDec AlphasExact over a range |ln(mu/mu0)| = {short[0]:.3g} < 1e-4 takes its fixed first "
                     f"step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured |engine - CRunDec| = "
                     f"{row.diff:.3g}, |engine - exact| = {row.eng_err:.3g}, |CRunDec - exact| = {row.lib_err:.3g} "
                     f"(tolerance {row.tol:.3g})")
    return row


# --- rows -----------------------------------------------------------------------------------------------------------

LOW = {3: {}, 4: {"c": 0.1}, 5: {"c": 0.1, "b": 0.2}, 6: {"c": 0.1, "b": 0.2, "t": 0.3}}  # n_f fixed above 0.3 GeV


@functools.lru_cache(maxsize=None)
@mp.workdps(DPS)
def rows() -> list[Row]:
    out = []
    for nf, th in LOW.items():
        for loops in (1, 2, 3, 4):
            for mu in (1.5, 5.0, 30.0, 300.0, 3000.0):
                out.append(_row(f"alpha_s, n_f = {nf} fixed, {loops} loop", f"mu={mu:g} GeV", mu, M_Z, A_MZ, th,
                                loops))
    for loops in (1, 2, 3, 4):
        for mu in (1.3, 1.77686, 2.0, 3.0, TH["b"] * (1 - 1e-6), TH["b"] * (1 + 1e-6), 10.0, TH["t"] * (1 + 1e-6),
                   500.0, 5000.0):
            out.append(_row(f"alpha_s with thresholds, {loops} loop", f"mu={mu:.9g} GeV", mu, M_Z, A_MZ, TH, loops))
    for loops in (1, 2, 3, 4):
        for n_l in (3, 4, 5):
            for alpha in (0.1, 0.2, 0.3, 0.4):
                for down in (True, False):
                    eng = running.decoupling(alpha, n_l, loops, down)
                    fn = CRD.DecAsDownMS if down else CRD.DecAsUpMS
                    lib = fn(alpha, 4.0, 4.0, n_l, loops)  # at mu = m_h: the logarithms vanish
                    ex = mp_dec(mp.mpf(alpha), n_l, loops, down)
                    a = alpha / math.pi
                    c3 = 564731 / 124416 - 82043 / 27648 * ZETA3_F - 2633 / 31104 * n_l
                    tol = 2 * gamma(16) * alpha * (1 + 11 / 72 * a * a + abs(c3) * a ** 3)
                    out.append(Row(GROUP, f"decoupling {'down' if down else 'up'}, {loops} loop", f"n_l={n_l}, "
                                   f"alpha={alpha}", eng, lib, tol, "decoupling", float(abs(eng - ex)),
                                   float(abs(lib - ex))))
    return out


@pytest.mark.parametrize("row", params(rows()))
def test_alpha_s(row):
    check(row)


@pytest.mark.parametrize("nf,loops,mu", [(3, 4, 1.5), (5, 4, 4.183), (5, 2, 1000.0), (6, 4, 5000.0), (4, 1, 2.0),
                                         (5, 3, 91.188 * 1.0001)])
def test_crundec_step_count_reproduces_crundec(nf, loops, mu):
    """The re-implementation of CRunDec's step-size control (used only to count its accepted steps for the
    tolerance) reproduces CRunDec's alpha_s to 1e-14 relative, so the count is CRunDec's."""
    rep, steps = crd_replica(A_MZ, M_Z, mu, nf, loops)
    lib = CRD.AlphasExact(A_MZ, M_Z, mu, nf, loops)
    assert abs(rep / lib - 1) < 1e-14, (rep, lib, steps)
    assert steps >= 1


@pytest.mark.parametrize("dl", [-9.9e-5, -1e-5, -1e-6, 1e-6, 5e-5])
@mp.workdps(DPS)
def test_crundec_short_range_lands_at_its_first_step(dl):
    """CRunDec 3.1 AlphasExact (also in CRunDec 3.1.3, whose AlphasExact is the same) starts with h = +-1e-4 in ln mu
    and cuts a step to the end point only after a step: over a range shorter than 1e-4 the single step overshoots, and
    the result is alpha_s at mu0 e^(+-1e-4), not at mu. Shown here against the exact solution (30-digit mpmath): the
    library value equals the exact value at the overshot point to 1e-15 and misses the requested one by ~1e-6 to 1e-8
    (the size of d alpha_s / d ln mu times the overshoot). The engine is not affected (its rows above)."""
    mu0, alpha0 = 4.183, 0.2
    mu1 = mu0 * math.exp(dl)
    lib = CRD.AlphasExact(alpha0, mu0, mu1, 4, 4)
    at_step = mp_run(alpha0, mu0, mu0 * math.exp(math.copysign(CRD_H0, dl)), 4, 4, lib)
    at_mu = mp_run(alpha0, mu0, mu1, 4, 4, lib)
    eng = running.alpha_s(mu1, alpha0, mu0, LOW[4], 4)
    assert abs(lib - at_step) < 1e-15
    assert abs(lib - at_mu) > 1e-3 * abs(f_beta(alpha0, 4, 4)) * 2 * (CRD_H0 - abs(dl))
    assert abs(eng - at_mu) < 1e-14


def test_one_loop_attribution():
    """At one loop the solution is closed: the engine is within 1e-11 relative of it (its verified accuracy,
    tests/test_qcd.py), CRunDec within its stated per-step tolerance; so the differences of order 1e-9 seen in the
    rows above come from CRunDec's integrator."""
    for mu in (1.5, 5.0, 3000.0):
        exact = A_MZ / (1 + A_MZ * running.beta_coefficients(3, 1)[0] / (4 * math.pi) * math.log(mu ** 2 / M_Z ** 2))
        eng = running.alpha_s(mu, A_MZ, M_Z, {}, loops=1)
        lib = CRD.AlphasExact(A_MZ, M_Z, mu, 3, 1)
        steps = crd_replica(A_MZ, M_Z, mu, 3, 1)[1]
        ratio = max(1.0, abs(f_beta(lib, 3, 1) / f_beta(A_MZ, 3, 1)))
        assert abs(eng / exact - 1) < 1e-11
        assert abs(lib - exact) <= steps * math.pi * CRD_EPS * ratio
