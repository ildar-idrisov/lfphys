# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Brans-Dicke scalar-tensor gravity: a scalar field couples to matter with the parameter omega. In the weak field
it differs from general relativity through the PPN parameter gamma = (1 + omega) / (2 + omega) (beta = 1); GR is the
limit omega -> infinity. The Cassini time-delay measurement gamma - 1 = (2.1 +- 2.3) 1e-5 (Bertotti, Iess & Tortora
2003) bounds omega > ~40 000.
"""

from __future__ import annotations

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": "Скалярно-тензорная гравитация Бранса–Дикке",
    "statement": "Скалярное поле с параметром связи ω; в слабом поле γ = (1+ω)/(2+ω), β = 1; ОТО — предел ω → ∞.",
    "validity": "ограничена опытом Cassini: ω > ~4·10⁴",
    "basis": ["Brans & Dicke, Phys. Rev. 124, 925 (1961)", "Bertotti, Iess, Tortora, Nature 425, 374 (2003)"],
    "conflicts": ["lfphys.core.gravity: ОТО (γ = 1); при малых ω противоречит измерениям Cassini"],
}


def ppn_gamma(omega: float) -> float:
    return (1.0 + omega) / (2.0 + omega)


def ppn_beta(omega: float) -> float:
    return 1.0
