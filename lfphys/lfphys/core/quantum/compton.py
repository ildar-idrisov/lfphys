# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Compton scattering of a photon by a free electron at rest: kinematics and the Klein-Nishina cross-section
(lowest order of quantum electrodynamics, unpolarized).

    lambda' - lambda = lambda_C (1 - cos theta),   E'/E = 1 / (1 + (E/mc^2)(1 - cos theta)),
    dsigma/dOmega = (r_e^2 / 2) (E'/E)^2 (E'/E + E/E' - sin^2 theta)

Thomson limit (E << mc^2): dsigma/dOmega = (r_e^2/2)(1 + cos^2 theta), sigma_T = 8 pi r_e^2 / 3.
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
from scipy import constants as sc

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Комптоновское рассеяние (формула Клейна–Нишины)",
    "statement": "Сдвиг длины волны λ' − λ = λ_C(1 − cos θ) и сечение Клейна–Нишины (низший порядок КЭД); "
                 "томсоновский предел.",
    "validity": "свободный покоящийся электрон, неполяризованные фотоны; поправки КЭД высших порядков ~α/π",
    "basis": ["Compton, Phys. Rev. 21, 483 (1923)", "Klein & Nishina, Z. Phys. 52, 853 (1929)"],
    "conflicts": [],
}

ME_C2 = sc.m_e * sc.c**2
LAMBDA_C = sc.h / (sc.m_e * sc.c)
R_E = sc.physical_constants["classical electron radius"][0]


def energy_ratio(E: float, theta) -> np.ndarray:
    return 1.0 / (1.0 + E / ME_C2 * (1.0 - np.cos(theta)))


def klein_nishina(E: float, theta) -> np.ndarray:
    P = energy_ratio(E, theta)
    return 0.5 * R_E**2 * P**2 * (P + 1.0 / P - np.sin(theta) ** 2)


# sigma / sigma_T = sum_k c_k x^k, exact coefficients of the Taylor series of the closed form (derived with rational
# power-series arithmetic): 1 - 2x + 26/5 x^2 - 133/10 x^3 + ...; |c_k| ~ 2^k, so 20 terms reach 1e-20 at x = 0.05
_KN_SERIES = tuple(float(Fraction(c)) for c in (
    "1/1", "-2/1", "26/5", "-133/10", "1144/35", "-544/7", "3784/21", "-6148/15", "151552/165", "-111872/55", "637952/143", "-883328/91", "9545728/455", "-1577984/35", "8195072/85", "-10469888/51", "421986304/969", "-262406144/285", "1290665984/665", "-1570930688/385"))


def total_cross_section(E: float) -> float:
    """Closed-form integral of Klein-Nishina over angles. Below x = E/mc^2 = 0.05 its Taylor series (the closed form
    cancels like 1/x^3 there: 6e-5 relative at x = 1e-4 with log(1 + 2x), review 2026-10-23 E2); above, the closed
    form with log1p (error below 1e-12 relative)."""
    x = E / ME_C2
    sigma_t = 8 * math.pi * R_E**2 / 3
    if x < 0.05:
        acc = 0.0
        for c in reversed(_KN_SERIES):
            acc = acc * x + c
        return sigma_t * acc
    lg = math.log1p(2 * x)
    return 2 * math.pi * R_E**2 * ((1 + x) / x**3 * (2 * x * (1 + x) / (1 + 2 * x) - lg)
                                   + lg / (2 * x) - (1 + 3 * x) / (1 + 2 * x) ** 2)
