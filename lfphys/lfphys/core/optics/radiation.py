# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Thermal radiation of a black body (Planck's law) and its consequences.

    B_lambda(T) = 2 h c^2 / lambda^5 / (exp(h c / (lambda k T)) - 1)       (W m^-3 sr^-1)
    B_nu(T)     = 2 h nu^3 / c^2 / (exp(h nu / (k T)) - 1)                  (W m^-2 Hz^-1 sr^-1)

Wien's displacement lambda_max T = h c / (k x), x = 5 + W0(-5 e^-5) (Lambert W); the radiant exitance
pi int B_lambda d lambda = sigma T^4 with sigma = 2 pi^5 k^4 / (15 h^3 c^2).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import constants as sc
from scipy import special

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Излучение абсолютно чёрного тела (закон Планка)",
    "statement": "Спектральная яркость B_λ(T), B_ν(T); закон смещения Вина (через функцию Ламберта); "
                 "закон Стефана–Больцмана σT⁴.",
    "validity": "равновесное излучение; спектр реликтового фона — планковский: среднеквадратичные отклонения "
                "меньше 5·10⁻⁵ от максимума (COBE/FIRAS, Fixsen et al. 1996)",
    "basis": ["Planck 1900", "Fixsen et al., ApJ 473, 576 (1996), arXiv:astro-ph/9605054 (COBE/FIRAS, полный набор)",
              "Mather et al., ApJ 420, 439 (1994) (COBE/FIRAS: отклонения < 0,3 % максимума, rms 0,01 %)"],
    "conflicts": [],
}

H, C, K = sc.h, sc.c, sc.k


def planck_lambda(lam, T: float):
    lam = np.asarray(lam, float)
    x = H * C / (lam * K * T)
    return 2 * H * C * C / lam**5 / np.expm1(x)


def planck_nu(nu, T: float):
    nu = np.asarray(nu, float)
    return 2 * H * nu**3 / C**2 / np.expm1(H * nu / (K * T))


def wien_lambda_constant() -> float:
    """b = lambda_max T (m K)."""
    x = 5.0 + special.lambertw(-5.0 * math.exp(-5.0)).real
    return H * C / (K * x)


def stefan_boltzmann() -> float:
    return 2 * math.pi**5 * K**4 / (15 * H**3 * C**2)
