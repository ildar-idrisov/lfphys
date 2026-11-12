# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Geometrical (ray) optics in the paraxial matrix form: a ray is (height y, angle theta); elements act by 2x2 ray
transfer (ABCD) matrices. Snell's law n1 sin t1 = n2 sin t2 exactly; the matrices use small angles.
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": "Лучевая (геометрическая) оптика: закон Снелла и матрицы ABCD",
    "statement": "Луч — высота и угол; свободный промежуток, тонкая линза, преломление на границе — матрицы 2×2; "
                 "формула линзы 1/s + 1/s' = 1/f.",
    "validity": "размеры ≫ λ (нет дифракции); матрицы — малые углы (параксиальность)",
    "basis": ["Born & Wolf, Principles of Optics, гл. 3–4"],
    "conflicts": ["lfphys.core.optics: волновая оптика — дифракция и интерференция, которых лучи не дают"],
}


def snell(n1: float, n2: float, theta1: float) -> float | None:
    s = n1 * math.sin(theta1) / n2
    return math.asin(s) if abs(s) <= 1 else None  # None: total internal reflection


def free(d: float) -> np.ndarray:
    return np.array([[1.0, d], [0.0, 1.0]])


def thin_lens(f: float) -> np.ndarray:
    return np.array([[1.0, 0.0], [-1.0 / f, 1.0]])


def interface(n1: float, n2: float, R: float = math.inf) -> np.ndarray:
    """Refraction at a spherical surface of radius R (inf: plane); angles in the media."""
    return np.array([[1.0, 0.0], [(n1 - n2) / (n2 * R) if math.isfinite(R) else 0.0, n1 / n2]])


def system(*mats) -> np.ndarray:
    """Matrices in the order the light meets them."""
    M = np.eye(2)
    for m in mats:
        M = m @ M
    return M


def image_distance(f: float, s: float) -> float:
    return 1.0 / (1.0 / f - 1.0 / s)
