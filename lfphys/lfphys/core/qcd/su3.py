# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Colour algebra of QCD: the Gell-Mann matrices lambda_a (a = 1..8), the generators T_a = lambda_a / 2 of SU(3),
the structure constants [T_a, T_b] = i f_abc T_c, the symmetric constants {lambda_a, lambda_b} = (4/3) delta_ab I +
2 d_abc lambda_c, and the Casimirs C_F = 4/3 (quarks), C_A = 3 (gluons), T_F = 1/2.
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Цветовая алгебра SU(3)",
    "statement": "Матрицы Гелл-Манна, структурные константы f_abc и d_abc, казимиры C_F = 4/3, C_A = 3, T_F = 1/2.",
    "validity": "математика калибровочной группы КХД",
    "basis": ["Gell-Mann, Phys. Rev. 125, 1067 (1962)", "Fritzsch, Gell-Mann, Leutwyler, Phys. Lett. B 47, 365 (1973)"],
    "conflicts": [],
}

_s3 = 1.0 / math.sqrt(3.0)
LAMBDA = np.zeros((8, 3, 3), complex)
LAMBDA[0][0, 1] = LAMBDA[0][1, 0] = 1
LAMBDA[1][0, 1], LAMBDA[1][1, 0] = -1j, 1j
LAMBDA[2][0, 0], LAMBDA[2][1, 1] = 1, -1
LAMBDA[3][0, 2] = LAMBDA[3][2, 0] = 1
LAMBDA[4][0, 2], LAMBDA[4][2, 0] = -1j, 1j
LAMBDA[5][1, 2] = LAMBDA[5][2, 1] = 1
LAMBDA[6][1, 2], LAMBDA[6][2, 1] = -1j, 1j
LAMBDA[7] = _s3 * np.diag([1, 1, -2])
T = LAMBDA / 2

C_F = 4.0 / 3.0
C_A = 3.0
T_F = 0.5


def structure_constants() -> tuple[np.ndarray, np.ndarray]:
    """f_abc = -(i/4) Tr(lambda_a [lambda_b, lambda_c]),  d_abc = (1/4) Tr(lambda_a {lambda_b, lambda_c})."""
    f = np.zeros((8, 8, 8))
    d = np.zeros((8, 8, 8))
    for a in range(8):
        for b in range(8):
            for c in range(8):
                comm = LAMBDA[b] @ LAMBDA[c] - LAMBDA[c] @ LAMBDA[b]
                anti = LAMBDA[b] @ LAMBDA[c] + LAMBDA[c] @ LAMBDA[b]
                f[a, b, c] = np.real(-0.25j * np.trace(LAMBDA[a] @ comm))
                d[a, b, c] = np.real(0.25 * np.trace(LAMBDA[a] @ anti))
    return f, d
