# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Paraxial Gaussian beams (time dependence exp(-i omega t), field exp(i k z) u(x, z)).

The paraxial equation 2ik du/dz + d^2u/dx^2 = 0 (one transverse dimension) has the solution
    u(x, z) = (q0/q)^(1/2) exp(i k x^2 / (2 q)),   q = z - i z_R,   z_R = k w0^2 / 2,
with width w(z) = w0 sqrt(1 + (z/z_R)^2), wavefront radius R(z) = z + z_R^2/z and Gouy phase lag (1/2) arctan(z/z_R)
(arctan(z/z_R) for two transverse dimensions). Through an optical system with ray matrix [[A, B], [C, D]]:
q' = (A q + B)/(C q + D).
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": "Гауссов пучок (параксиальное приближение)",
    "statement": "Решение параксиального волнового уравнения: ширина w(z), радиус фронта R(z), фаза Гюи, "
                 "комплексный параметр q и его преобразование матрицами ABCD.",
    "validity": "малая расходимость, w0 ≫ λ (поправки порядка (λ/w0)²)",
    "basis": ["Kogelnik & Li, Appl. Opt. 5, 1550 (1966)", "Siegman, Lasers, гл. 17"],
    "conflicts": ["lfphys.core.optics.angular_spectrum: точное распространение отличается при сильной фокусировке "
                  "(w0 ~ λ)"],
}


def rayleigh(k: float, w0: float) -> float:
    return 0.5 * k * w0 * w0


def width(z, k: float, w0: float):
    return w0 * np.sqrt(1 + (np.asarray(z) / rayleigh(k, w0)) ** 2)


def field_1d(x, z: float, k: float, w0: float):
    """u(x, z) for one transverse dimension (multiply by exp(i k z) for the full field); u(x, 0) = exp(-x^2/w0^2)."""
    zr = rayleigh(k, w0)
    q0 = -1j * zr
    q = z + q0
    return np.sqrt(q0 / q) * np.exp(1j * k * np.asarray(x) ** 2 / (2 * q))


def gouy(z: float, k: float, w0: float, dims: int = 1) -> float:
    return (0.5 if dims == 1 else 1.0) * math.atan(z / rayleigh(k, w0))


def transform_q(q: complex, abcd) -> complex:
    (A, B), (Cc, D) = abcd
    return (A * q + B) / (Cc * q + D)
