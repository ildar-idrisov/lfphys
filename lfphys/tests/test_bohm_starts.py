# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Bohmian slit trajectories start |Psi|^2-distributed (review 2026-10-23, E10): the uniform-in-slit starts had a
Kolmogorov-Smirnov distance 0.081 from |Psi|^2 for a 5 um slit at z0 = 2a."""

import math

import numpy as np
import pytest

from lfphys.theories.approx.paraxial import slit_amplitudes
from lfphys.theories.interpretations import bohm


@pytest.mark.parametrize("a", [5e-6, 20e-6])
def test_slit_starts_follow_the_born_density(a, ru):
    k = 2 * math.pi / 633e-9
    n = 400
    out = bohm.slit_trajectories(k, [0.0], a, math.inf, np.eye(1), [1.0], 1e-3, n=n, n_steps=4)
    x0 = np.sort(out["x"][0])
    # independent CDF of |Psi(x, 2a)|^2 on a different (coarser, wider) grid, trapezoid
    xs = np.linspace(-8 * a, 8 * a, 60001)
    rho = np.abs(slit_amplitudes(xs[None, :], 2 * a, k, [0.0], a)[0, 0]) ** 2
    cdf = np.concatenate([[0.0], np.cumsum(0.5 * (rho[1:] + rho[:-1]) * np.diff(xs))])
    cdf /= cdf[-1]
    F = np.interp(x0, xs, cdf)
    ks = np.max(np.abs(F - (np.arange(n) + 0.5) / n))
    assert ks < 0.5 / n + 2e-3
    assert np.mean(np.abs(x0) > 0.48 * a) > 0.03  # part of |Psi|^2 lies outside the slit window, and starts go there
    # the relativity conflict is declared
    assert any("relativity" in str(c) for c in bohm.ABOUT["conflicts"])
    assert any("относительн" in ru(c) for c in bohm.ABOUT["conflicts"])
