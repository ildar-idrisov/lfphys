# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The running strong coupling alpha_s(mu) in the MS-bar scheme.

Renormalisation-group equation, a = alpha_s / (4 pi):

    d a / d ln mu^2 = - beta_0 a^2 - beta_1 a^3 - beta_2 a^4 - beta_3 a^5,

with (SU(3), n_f light flavours; van Ritbergen, Vermaseren & Larin 1997)
    beta_0 = 11 - 2/3 n_f,
    beta_1 = 102 - 38/3 n_f,
    beta_2 = 2857/2 - 5033/18 n_f + 325/54 n_f^2,
    beta_3 = (149753/6 + 3564 zeta_3) - (1078361/162 + 6508/27 zeta_3) n_f + (50065/162 + 6472/81 zeta_3) n_f^2
             + 1093/729 n_f^3.
(verified against the paper, lfphys/sources/verification_2026-10-23.md, item 7; the five-loop beta_4 of Baikov,
Chetyrkin & Kühn 2017 is not included). Integrated numerically (DOP853, relative tolerance 1e-12).

Quark thresholds: n_f changes at mu = m_h, the MS-bar mass at its own scale, with the decoupling relation of
Chetyrkin, Kniehl & Steinhauser 1997 at that scale (RunDec, Chetyrkin, Kühn & Steinhauser, Comput. Phys. Commun.
133, 43 (2000), arXiv:hep-ph/0004189, Eqs. (20) and (23) at mu = m_h(m_h); checked against the paper's source):
    alpha^(n_l) = alpha^(n_f) [1 + 11/72 a^2 + (564731/124416 - 82043/27648 zeta_3 - 2633/31104 n_l) a^3],
    a = alpha^(n_f)/pi (downwards), and upwards
    alpha^(n_f) = alpha^(n_l) [1 - 11/72 a'^2 + (-564731/124416 + 82043/27648 zeta_3 + 2633/31104 n_l) a'^3],
    a' = alpha^(n_l)/pi.
Running at L loops uses matching at L - 1 loops (RunDec: "consistency requires the matching conditions to be
implemented in terms of N-loop formulae" for N + 1-loop running): continuous at 1 and 2 loops, the a^2 term at 3,
a^2 and a^3 at 4. (Until 2026-10-23 the matching was continuous at every order; at 4 loops that shifted alpha_s by
-1.0e-3 relative at m_b and -5.6e-3 at m_c: review 2026-10-23, E7.)

Asymptotic freedom: beta_0 > 0 for n_f <= 16, so alpha_s falls at short distances (Gross & Wilczek; Politzer 1973).
Theoretical uncertainty: the truncation of the beta function and of the matching (estimate it by comparing loop
orders, and the matching scale dependence, e.g. matching at mu = 2 m_h, which this module does not offer).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate, special

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Бег константы сильного взаимодействия α_s (КХД, схема MS-bar)",
    "statement": "Уравнение ренормгруппы с β-функцией до четырёх петель; пороги тяжёлых кварков; асимптотическая "
                 "свобода (β₀ > 0 при n_f ≤ 16).",
    "validity": "пертурбативная область μ ≳ 1.5 ГэВ; неопределённость — усечение ряда (сравнение порядков); "
                "сшивка на порогах на одну петлю ниже бега (до трёх петель при беге в четыре)",
    "basis": ["Gross & Wilczek, PRL 30, 1343 (1973); Politzer, PRL 30, 1346 (1973)",
              "van Ritbergen, Vermaseren, Larin, Phys. Lett. B 400, 379 (1997)",
              "Chetyrkin, Kniehl, Steinhauser, PRL 79, 2184 (1997); RunDec: Comput. Phys. Commun. 133, 43 (2000)",
              "PDG, обзор «Quantum Chromodynamics» (α_s(M_Z) — в lfphys.core.data)"],
    "conflicts": [],
}

ZETA3 = float(special.zeta(3.0))


def beta_coefficients(nf: int, loops: int = 4) -> list[float]:
    b = [11.0 - 2.0 / 3.0 * nf,
         102.0 - 38.0 / 3.0 * nf,
         2857.0 / 2.0 - 5033.0 / 18.0 * nf + 325.0 / 54.0 * nf**2,
         (149753.0 / 6.0 + 3564.0 * ZETA3) - (1078361.0 / 162.0 + 6508.0 / 27.0 * ZETA3) * nf
         + (50065.0 / 162.0 + 6472.0 / 81.0 * ZETA3) * nf**2 + 1093.0 / 729.0 * nf**3]
    return b[:loops]


class LandauPole(ValueError):
    """The perturbative coupling diverges on the way (alpha_s > ALPHA_MAX): the RG solution does not exist there."""

    def __init__(self, mu):
        self.mu = mu
        super().__init__(f"полюс Ландау: α_s расходится около μ ≈ {mu:.3g} ГэВ (теория возмущений неприменима)")


ALPHA_MAX = 3.0


def _evolve(a0: float, L0: float, L1: float, nf: int, loops: int) -> float:
    b = beta_coefficients(nf, loops)

    def rhs(L, y):
        a = y[0]
        return [-sum(bi * a ** (i + 2) for i, bi in enumerate(b))]

    def pole(L, y):
        return y[0] - ALPHA_MAX / (4 * math.pi)
    pole.terminal = True
    if L1 == L0:
        return a0
    if 4 * math.pi * a0 >= ALPHA_MAX:
        # the coupling is already past the bound at the start (a heavy-quark decoupling can push it over just below a
        # pole: alpha_s(M_Z) = 0.19 at 4 loops gives 4.9 just below m_b); the event cannot fire on a start that is
        # already past it, and the integration then failed on the overflow (review UX-params P5)
        raise LandauPole(math.exp(0.5 * L0))
    sol = integrate.solve_ivp(rhs, (L0, L1), [a0], method="DOP853", rtol=1e-12, atol=1e-16, events=pole)
    if sol.t_events[0].size:
        raise LandauPole(math.exp(0.5 * float(sol.t_events[0][0])))
    if not sol.success:
        if sol.t.size and 4 * math.pi * float(sol.y[0, -1]) >= ALPHA_MAX:  # stopped past the bound: the same pole
            raise LandauPole(math.exp(0.5 * float(sol.t[-1])))
        raise ValueError(f"RG integration failed at mu = {math.exp(0.5 * float(sol.t[-1])):.4g} GeV: {sol.message}")
    return float(sol.y[0, -1])


ZETA3 = 1.2020569031595942


def decoupling(alpha: float, n_l: int, loops: int, down: bool) -> float:
    """alpha_s across a heavy-quark threshold at mu = m_h(m_h) (MS-bar), with ``loops - 1``-loop matching (see the
    module docstring). down: alpha^(n_f) -> alpha^(n_l); otherwise alpha^(n_l) -> alpha^(n_f)."""
    a = alpha / math.pi
    c2 = 11.0 / 72.0 if loops >= 3 else 0.0
    c3 = (564731.0 / 124416.0 - 82043.0 / 27648.0 * ZETA3 - 2633.0 / 31104.0 * n_l) if loops >= 4 else 0.0
    if down:
        return alpha * (1.0 + c2 * a * a + c3 * a**3)
    return alpha * (1.0 - c2 * a * a - c3 * a**3)


def alpha_s(mu: float, alpha_ref: float, mu_ref: float, thresholds: dict, loops: int = 4) -> float:
    """alpha_s(mu) from alpha_s(mu_ref), mu in GeV. ``thresholds``: {"c": m_c, "b": m_b, "t": m_t} (MS-bar masses
    m_q(m_q), GeV); n_f counts the quarks lighter than the scale (u, d, s always light). At each threshold crossed the
    decoupling relation of ``loops - 1`` loops is applied (``decoupling``)."""
    edges = sorted(math.log(q * q) for q in thresholds.values())
    a = alpha_ref / (4 * math.pi)
    L = math.log(mu_ref**2)
    target = math.log(mu**2)
    up = target > L
    # the coupling at mu = m_h belongs to the theory without h (n_f counts quarks with m_q < mu), so a threshold at the
    # start is crossed going up, one at the target is crossed going down
    if up:
        cross = sorted(e for e in edges if L <= e < target)
    else:
        cross = sorted((e for e in edges if target <= e < L), reverse=True)

    def nf_between(l1, l2):
        mid = 0.5 * (l1 + l2)
        return 3 + sum(1 for e in edges if mid > e)
    for e in cross:
        if e != L:
            a = _evolve(a, L, e, nf_between(L, e), loops)
        L = e
        nf_above = 3 + sum(1 for x in edges if x <= e)  # flavours just above the threshold, h included
        a = decoupling(4 * math.pi * a, nf_above - 1, loops, down=not up) / (4 * math.pi)
        if not (4 * math.pi * a < ALPHA_MAX):  # the matching itself took the coupling past the bound (P5)
            raise LandauPole(math.exp(0.5 * L))
    if target != L:
        a = _evolve(a, L, target, nf_between(L, target), loops)
    return 4 * math.pi * a


def one_loop(mu: float, alpha_ref: float, mu_ref: float, nf: int) -> float:
    """Closed form at one loop (fixed n_f): alpha(mu) = alpha_ref / (1 + alpha_ref beta_0/(4 pi) ln(mu^2/mu_ref^2))."""
    return alpha_ref / (1 + alpha_ref * beta_coefficients(nf, 1)[0] / (4 * math.pi) * math.log(mu**2 / mu_ref**2))


def scan(mus, alpha_ref: float, mu_ref: float, thresholds: dict, loops: int = 4) -> np.ndarray:
    return np.array([alpha_s(m, alpha_ref, mu_ref, thresholds, loops) for m in mus])
