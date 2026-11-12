# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Objective collapse (GRW): spontaneous localisations of every particle at a rate lambda per atomic mass unit
(mass-proportional), each a Gaussian of width r_C. For the density matrix a hit is a random momentum kick
q ~ N(0, 1/(2 r_C^2)); a hit at distance z' before the plane z shifts a paraxial pattern by q (z - z') / k.
Averaged over hits uniform in z' (Poisson number Lam_z = rate z / v), the characteristic function of the shift is

    phi(w) = exp(-Lam_z [1 - sqrt(pi) erf(a) / (2a)]),   a = |w| z / (2 k r_C).

GRW is a different theory (it changes the dynamics and predicts, e.g., anomalous heating), not an interpretation;
its parameters are bounded by experiments (matter-wave interferometry, cantilever and X-ray emission tests).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": "Спонтанный коллапс GRW",
    "statement": "Каждая частица спонтанно локализуется с частотой λ на а.е.м. гауссианом ширины r_C; для матрицы "
                 "плотности — случайный толчок q ~ N(0, 1/(2r_C²)).",
    "validity": "модификация квантовой динамики; параметры ограничены опытами (интерферометрия молекул, "
                "аномальный нагрев, спонтанное рентгеновское излучение)",
    "basis": ["Ghirardi, Rimini, Weber, Phys. Rev. D 34, 470 (1986)", "Bassi et al., Rev. Mod. Phys. 85, 471 (2013)"],
    "conflicts": ["lfphys.core.quantum: линейная квантовая механика без коллапса"],
}


def grw_shift_cf(w, k, z, lam_z, rc):
    """Characteristic function E[exp(-i w Delta)] of the total pattern shift from GRW hits during a flight of
    length z (Poisson mean lam_z hits, uniform in z')."""
    a = np.abs(w) * z / (2 * k * rc)
    sm = a < 1e-6
    ab = np.where(sm, 1.0, a)
    g = np.where(sm, 1 - a * a / 3, math.sqrt(math.pi) * special.erf(ab) / (2 * ab))
    return np.exp(-lam_z * (1 - g)).astype(complex)


def grw_kicks(rng, n_hits, rc):
    """Momentum kicks of n GRW hits (one draw per hit)."""
    return rng.normal(0.0, 1.0 / (math.sqrt(2.0) * rc), size=n_hits)


def which_slit_gram(G):
    """Forced which-slit collapse at the slits (a declared modification, no physical mechanism): the cross terms
    of the marks' Gram matrix are removed, whatever the marks are. G (..., n, n)."""
    n = G.shape[-1]
    return G * np.eye(n)
