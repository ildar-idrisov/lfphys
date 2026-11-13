# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Quarkonium in the Cornell potential: a heavy quark-antiquark pair bound by V(r) = -kappa/r + r/a^2 (one-gluon
exchange at short distance, a confining string at long distance), solved non-relativistically for the
spin-averaged levels:  M(n, L) = 2 m_q + E(n, L),  reduced mass m_q / 2, natural units (hbar = c = 1, GeV).

Parameters: kappa = 0.52, a = 2.34 GeV^-1, m_c = 1.84 GeV, m_b = 5.18 GeV, as quoted by Eichten & Quigg, PRD 52,
1726 (1995), for the model of Eichten et al., PRD 21, 203 (1980) (the 1980 text itself was not readable; see
lfphys/sources/verification_2026-10-23.md, item 10). The parameters are FITTED; spin-dependent splittings,
relativistic corrections and coupling to open-flavour channels are not in the model.

The absolute mass scale is not fixed by these numbers: with them 2 m_c + E(1S) = 3.94 GeV, while the spin-averaged
1S charmonium mass is 3.07 GeV (an additive constant is not published with the parameters). The model's predictions
used here are therefore the level SPLITTINGS (``splittings``: M(n, L) - M(1S)); computed with these parameters they
come out 2-10 % from the measured spin-averaged splittings (2S-1S: 591 vs 605 MeV for charmonium).
"""

from __future__ import annotations

from ...core.quantum import radial
from lfphys.i18n import T
from lfphys.codes import coded

ABOUT = {
    "layer": "theories", "kind": "model",
    "title": T("Quarkonium in the Cornell potential"),
    "statement": T("A pair of heavy quarks in the potential V(r) = −κ/r + r/a² (gluon exchange + the confining "
                   "string); non-relativistic spin-averaged levels M = 2m_q + E(n, L)."),
    "validity": T("fitted parameters (κ, a, m_q); predicts the level splittings (the absolute scale is not set); no "
                  "spin forces, relativistic corrections or coupling to open channels; not applicable above the D D̄ "
                  "/ B B̄ threshold; the splittings agree with experiment to 2–10 %"),
    "basis": ["Eichten et al., PRD 17, 3090 (1978); PRD 21, 203 (1980)", "Eichten & Quigg, PRD 52, 1726 (1995)"],
    "conflicts": [T("QCD (lfphys.core.qcd): the potential is not derived from the Lagrangian in this form; lattice "
                    "QCD gives it only approximately; the constants κ, a, m_q are a fit, not parameters of QCD")],
}

PARAMS = {"kappa": 0.52, "a": 2.34, "m_c": 1.84, "m_b": 5.18}


def potential(kappa: float, a: float):
    return lambda r: -kappa / r + r / (a * a)


def _box_needed(kappa, a, mu, L, E_top):
    """Radius beyond which the highest state is negligible: its classical turning point r_t (V + L(L+1)/(2 mu r^2)
    = E_top) plus 8 decay lengths of the linear potential, l = (2 mu sigma)^(-1/3), sigma = 1/a^2 (Airy tail
    ~ exp(-(2/3)(x/l)^(3/2)): e^-15 at x = 8 l)."""
    import math
    sigma = 1.0 / (a * a)
    f = lambda r: -kappa / r + sigma * r + L * (L + 1) / (2 * mu * r * r) - E_top  # noqa: E731
    lo, hi = 1e-3, 1.0
    while f(hi) < 0:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return hi + 8.0 * (2 * mu * sigma) ** (-1.0 / 3.0)


def spectrum(m_q: float, kappa: float = PARAMS["kappa"], a: float = PARAMS["a"], L_max: int = 2, n_max: int = 3,
             R: float = 25.0, N: int = 700, info: dict | None = None) -> dict:
    """{(n, L): mass in GeV} for n = 1..n_max radial excitations and L = 0..L_max. The box (0, R) is enlarged when the
    highest state needs more room (its turning point plus 8 decay lengths, ``_box_needed``), with N in proportion up
    to 1400 points: a light quark or a weak string has large states, and in a fixed box they became box levels
    (review 2026-10-23, V6-5). ``info`` (a dict), if given, receives the largest box used: R, N."""
    out = {}
    V = potential(kappa, a)
    mu = 0.5 * m_q
    for L in range(L_max + 1):
        R_L, N_L = R, N
        for _ in range(4):
            E, r, u = radial.levels(V, L, mu, R_L, N=N_L, n_states=n_max)
            need = _box_needed(kappa, a, mu, L, float(E[n_max - 1]))
            if need <= R_L:
                break
            R_L, N_L = 1.1 * need, min(1400, int(N * 1.1 * need / R))
        else:
            raise coded(ValueError(T("Cornell spectrum: the states need a box beyond {R:.3g} GeV⁻¹ (m_q = {m_q}, "
                                     "κ = {kappa}, a = {a})", R=float(R_L), m_q=float(m_q), kappa=float(kappa),
                                     a=float(a))), "cornell.box")
        for n in range(n_max):
            out[(n + 1, L)] = 2 * m_q + E[n]
        if info is not None:
            info["R"], info["N"] = max(info.get("R", 0.0), R_L), max(info.get("N", 0), N_L)
    return out


def splittings(m_q: float, **kw) -> dict:
    """{(n, L): M(n, L) - M(1, 0) in GeV}: what the model predicts without an additive constant."""
    sp = spectrum(m_q, **kw)
    base = sp[(1, 0)]
    return {k: v - base for k, v in sp.items()}
