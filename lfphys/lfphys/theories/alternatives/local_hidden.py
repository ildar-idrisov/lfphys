# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Local hidden-variable models of the correlations of a pair (alternatives refuted by loophole-free Bell tests).
Each pair carries a hidden variable lambda fixed at the source; each side's outcome depends only on its own setting
and lambda. Any such model obeys the CHSH inequality |S| <= 2.

* ``sign_model``: lambda = a random unit vector in the plane; A = sign(a.lambda), B = -sign(b.lambda)
  (Bell 1964): E(a, b) = -1 + 2 theta/pi, theta = angle between a and b (a straight line instead of -cos theta);
* ``polarization_model``: each photon has a definite polarization angle lambda (both the same), and passes a
  polarizer at alpha with probability cos^2(alpha - lambda) (Malus law, independently): E = (1/2) cos 2(alpha - beta),
  half the quantum value.
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": "Локальные скрытые параметры",
    "statement": "Исход каждой стороны задан её настройкой и общим скрытым параметром из источника; любая такая "
                 "модель даёт |S| ≤ 2 (неравенство CHSH).",
    "validity": "опровергнуты опытами Белла без лазеек (2015): нарушение CHSH",
    "basis": ["Bell, Physics 1, 195 (1964)", "Hensen et al., Nature 526, 682 (2015)"],
    "conflicts": ["lfphys.core.quantum.qubits: квантовые корреляции дают S до 2√2"],
}


def sign_model(a: float, b: float, n: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Outcomes (+-1) for n pairs, measurement directions at angles a, b (rad) in the plane."""
    lam = rng.uniform(0, 2 * math.pi, n)
    A = np.sign(np.cos(lam - a))
    B = -np.sign(np.cos(lam - b))
    return A, B


def sign_model_E(theta: float) -> float:
    th = abs((theta + math.pi) % (2 * math.pi) - math.pi)
    return -1.0 + 2.0 * th / math.pi


def polarization_model(alpha: float, beta: float, n: int, rng) -> tuple[np.ndarray, np.ndarray]:
    lam = rng.uniform(0, math.pi, n)
    A = np.where(rng.random(n) < np.cos(alpha - lam) ** 2, 1, -1)
    B = np.where(rng.random(n) < np.cos(beta - lam) ** 2, 1, -1)
    return A, B


def polarization_model_E(alpha: float, beta: float) -> float:
    return 0.5 * math.cos(2 * (alpha - beta))
