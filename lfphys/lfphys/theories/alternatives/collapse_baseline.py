# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""GRW spontaneous collapse against the which-path decoherence of accepted physics (plan item P5): one call that a
double-slit world can use to put the two loss-of-visibility rates side by side.

GRW's master equation (Bassi et al., RMP 85, 471 (2013), eqs. 21, 22): <x|T[rho]|y> = lambda [1 - exp(-(x - y)^2 /
(4 r_C^2))] <x|rho|y>, lambda proportional to the mass (here lambda_amu per atomic mass unit, as in ``collapse`` and
the v02 world; lambda_GRW ~ 1e-16 1/s, r_C ~ 1e-7 m, their eq. 19). This is the same density-matrix form as a Poisson
stream of Gaussian momentum kicks of an environment (``core.quantum.decoherence``): for one two-path superposition
GRW is indistinguishable from such an environment with rate lambda m and width r_C. The baseline is what the
environment of the experiment does anyway: pure dephasing gamma_phi and a which-path probe stream (rate, overlap).
A measured visibility bounds lambda only after the baseline is accounted for; GRW scales with the mass alone, the
baseline with the environment.
"""

from __future__ import annotations

import math

from lfphys.core.quantum import decoherence as dec

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": "GRW против декогеренции среды: сравнение скоростей",
    "statement": "Член GRW λ[1 − e^{−d²/4r_C²}] имеет ту же форму, что поток гауссовых толчков от среды; функция "
                 "compare даёт видность от GRW, от дефазировки и от зондов-регистраторов пути и их отношение.",
    "validity": "модификация квантовой динамики (GRW) сравнивается с базой — декогеренцией по уравнению Линдблада; "
                "параметры GRW ограничены опытами при подавленной декогеренции среды",
    "basis": ["Bassi et al., Rev. Mod. Phys. 85, 471 (2013), eqs. (19), (21), (22)",
              "Ghirardi, Rimini, Weber, Phys. Rev. D 34, 470 (1986)",
              "Hornberger, arXiv:quant-ph/0612118, eqs. (5.170)–(5.171)",
              "lfphys/sources/verification_2026-10-29_p5.md — проверка цитат и выводов"],
    "conflicts": ["lfphys.core.quantum: линейная квантовая механика без коллапса; та же потеря видности возникает "
                  "от среды (core.quantum.decoherence)"],
}


def grw_rate(d: float, mass_amu: float, lam_amu: float = 1e-16, rc: float = 1e-7) -> float:
    """GRW decay rate of the coherence between two positions a distance d apart: lambda m [1 - exp(-d^2/(4 r_C^2))]."""
    return float(dec.localisation_rate(d, lam_amu * mass_amu, rc))


def compare(d: float, T: float, mass_amu: float, lam_amu: float = 1e-16, rc: float = 1e-7, *,
            gamma_phi: float = 0.0, probe_rate: float = 0.0, probe_overlap=1.0, converging: bool = True) -> dict:
    """Visibility factors over a flight of duration T with path separation d (constant, or falling linearly to 0 at
    the screen if ``converging``): GRW (lambda m per amu, r_C), pure dephasing gamma_phi, and a which-path probe
    stream (rate and overlap: a number, or a function of the separation chi(s)). Returns the factors, the exponents
    (-ln V) and their ratio GRW / baseline (inf if the baseline is zero)."""
    lam = lam_amu * mass_amu
    if converging:
        e_grw = lam * T * dec.mean_kick_loss_converging(d, rc)
    else:
        e_grw = float(dec.localisation_rate(d, lam, rc)) * T
    e_deph = gamma_phi * T
    if callable(probe_overlap):
        sep = (lambda t: d * (1 - t / T)) if converging else (lambda t: d + 0 * t)
        e_probe = -math.log(dec.separation_visibility(sep, T, probe_rate, overlap=probe_overlap))
    else:
        e_probe = probe_rate * T * (1.0 - complex(probe_overlap).real)
    base = e_deph + e_probe
    return {"V_grw": math.exp(-e_grw), "V_dephasing": math.exp(-e_deph), "V_probe": math.exp(-e_probe),
            "V_baseline": math.exp(-base), "V_total": math.exp(-(e_grw + base)),
            "exponent_grw": e_grw, "exponent_baseline": base,
            "grw_over_baseline": (e_grw / base) if base > 0 else math.inf}
