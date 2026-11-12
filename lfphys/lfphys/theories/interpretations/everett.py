# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Everett (many-worlds) reading: the measurement interaction entangles the system with the apparatus and the
observer; every outcome is realised in its own branch, with weight |amplitude|^2; nothing collapses. The branch
weights are the Born probabilities of the core; an observer inside a branch sees one outcome. No new prediction for
outcome statistics; what the weights mean (probability or "caring measure") is debated.
"""

from __future__ import annotations

import numpy as np

ABOUT = {
    "layer": "theories", "kind": "interpretation",
    "title": "Многомировая интерпретация Эверетта: ветвление без коллапса",
    "statement": "Измерение запутывает систему с прибором; все исходы реализуются в ветвях с весами |амплитуда|²; "
                 "коллапса нет. Предсказания исходов совпадают с ядром.",
    "validity": "те же предсказания для статистики исходов",
    "basis": ["Everett, Rev. Mod. Phys. 29, 454 (1957)", "DeWitt, Physics Today 23, 30 (1970)"],
    "conflicts": ["копенгагенская интерпретация: один исход и коллапс; Бом: одна траектория"],
}


def branch(psi, projectors, labels=None) -> list[dict]:
    """The branches of a measurement: each outcome's (unnormalised) component and its weight."""
    psi = np.asarray(psi, complex)
    out = []
    for i, P in enumerate(projectors):
        comp = P @ psi
        w = float(np.vdot(comp, comp).real)
        out.append({"outcome": labels[i] if labels else i, "weight": w, "state": comp})
    return out


def branch_tree(weights_per_step) -> list[tuple[tuple, float]]:
    """All branches of a sequence of independent measurements: (history, weight) with weight = product."""
    tree = [((), 1.0)]
    for ws in weights_per_step:
        tree = [(h + (k,), w * wk) for h, w in tree for k, wk in enumerate(ws) if wk > 0]
    return tree
