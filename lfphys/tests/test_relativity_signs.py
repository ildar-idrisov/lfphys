# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Sign conventions and precision near c of lfphys.core.relativity (review 2026-10-23, E6 and E14)."""

import math

import numpy as np
import pytest

from lfphys.core import relativity as R
from lfphys.core.constants import C


def test_wigner_rotation_sign():
    """u along x, v along y: theta > 0 and the axes of F2 (rows of R) are turned clockwise by theta."""
    u, v = np.array([0.5, 0.0]) * C, np.array([0.0, 0.5]) * C
    th = R.wigner_rotation_angle(u, v, C)
    assert th > 0
    lam = R.boost_matrix(v, C) @ R.boost_matrix(u, C)
    inv = np.linalg.inv(lam)
    w = inv[1:, 0] / inv[0, 0] * C
    Rm = (lam @ np.linalg.inv(R.boost_matrix(w, C)))[1:, 1:]
    x_axis = Rm[0]  # F2's x axis expressed in the frame reached by B(w): the first row of the coordinate matrix
    assert math.atan2(x_axis[1], x_axis[0]) == pytest.approx(-th, abs=1e-12)
    # small speeds: theta = |u x v| / (2 c^2) to leading order; swapping the order flips the sign
    a, b = np.array([1e-3, 0.0]) * C, np.array([0.0, 2e-3]) * C
    assert R.wigner_rotation_angle(a, b, C) == pytest.approx(1e-6, rel=1e-5)
    assert R.wigner_rotation_angle(b, a, C) == pytest.approx(-1e-6, rel=1e-5)


def test_gamma_near_c():
    mpmath = pytest.importorskip("mpmath")
    mpmath.mp.dps = 40
    for eps in (1e-6, 1e-8, 1e-10, 1e-12, 1e-14):
        b = 1.0 - eps
        ref = 1 / mpmath.sqrt(1 - mpmath.mpf(b) ** 2)
        assert R.gamma(b) == pytest.approx(float(ref), rel=3e-16)
        assert R.gamma(-b) == R.gamma(b)
