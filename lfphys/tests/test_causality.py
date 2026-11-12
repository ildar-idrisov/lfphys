# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.causality against an independent method: the Lorentz matrices of lfphys.core.relativity."""

import math

import numpy as np
import pytest
from scipy import constants as sc

from lfphys.core import causality as K
from lfphys.core import relativity as R

C = sc.c
rng = np.random.default_rng(20261023)


def _boost(e, v):
    """Event (t, x, y) seen from the frame moving with lab velocity v (2-vector): via the 3x3 boost matrix."""
    M = R.boost_matrix(np.asarray(v, float), C)
    ct, x, y = M @ np.array([C * e[0], e[1], e[2]])
    return np.array([ct / C, x, y])


def test_interval_closed_form_and_classes():
    e1 = (0.0, 0.0)
    assert K.interval(e1, (1e-6, 100.0), C) == pytest.approx((C * 1e-6) ** 2 - 100.0**2, rel=1e-15)
    assert K.relation(e1, (1e-6, 100.0), C) == K.TIMELIKE  # c dt = 299.8 m > 100 m
    assert K.relation(e1, (1e-6, 500.0), C) == K.SPACELIKE
    assert K.relation(e1, (1e-6, C * 1e-6), C) == K.LIGHTLIKE  # exactly on the cone
    assert K.relation(e1, (-1e-6, -C * 1e-6), C) == K.LIGHTLIKE  # past cone
    assert K.in_future_cone(e1, (1e-6, 100.0), C) and not K.in_future_cone((1e-6, 100.0), e1, C)
    assert not K.in_future_cone(e1, (1e-6, 500.0), C)
    assert K.in_future_cone(e1, (1e-6, C * 1e-6), C)  # a light signal reaches it


def test_interval_is_invariant_under_lorentz_boosts():
    for _ in range(200):
        e1 = np.array([rng.normal() * 1e-6, *rng.normal(size=2) * 300.0])
        e2 = np.array([rng.normal() * 1e-6, *rng.normal(size=2) * 300.0])
        v = rng.normal(size=2)
        v *= rng.uniform(0, 0.99) * C / np.linalg.norm(v)
        s_lab = K.interval(e1, e2, C)
        s_mov = K.interval(_boost(e1, v), _boost(e2, v), C)
        scale = (C * (e2[0] - e1[0])) ** 2 + np.sum((e2[1:] - e1[1:]) ** 2)
        assert abs(s_mov - s_lab) <= 1e-12 * scale
        assert K.relation(_boost(e1, v), _boost(e2, v), C) == K.relation(e1, e2, C)


def test_time_difference_in_frame_matches_the_boost_matrix():
    for _ in range(200):
        e1 = np.array([rng.normal() * 1e-6, *rng.normal(size=2) * 300.0])
        e2 = np.array([rng.normal() * 1e-6, *rng.normal(size=2) * 300.0])
        v = rng.normal(size=2)
        v *= rng.uniform(0, 0.999) * C / np.linalg.norm(v)
        ref = _boost(e2, v)[0] - _boost(e1, v)[0]
        assert K.time_difference_in_frame(e1, e2, v, C) == pytest.approx(ref, abs=1e-12 * (1e-6 + abs(ref)))
    with pytest.raises(ValueError):
        K.time_difference_in_frame((0, 0), (1, 1), [C], C)


def test_space_like_order_reverses_just_above_v_star_and_time_like_never():
    for _ in range(100):
        dt = rng.uniform(1e-9, 1e-6)
        dist = C * dt * rng.uniform(1.05, 20.0)  # space-like
        ang = rng.uniform(0, 2 * math.pi)
        n = np.array([math.cos(ang), math.sin(ang)])
        e1 = np.array([0.0, 0.0, 0.0])
        e2 = np.array([dt, *(dist * n)])
        b = K.order_reversal_speed(e1, e2, C)
        assert b == pytest.approx(C * dt / dist, rel=1e-14) and b < 1
        below = _boost(e2, (1 - 1e-6) * b * C * n)[0] - _boost(e1, (1 - 1e-6) * b * C * n)[0]
        above = _boost(e2, min(1 + 1e-6, (1 + b) / (2 * b)) * b * C * n)[0] - _boost(e1, min(1 + 1e-6, (1 + b) / (2 * b)) * b * C * n)[0]
        assert below > 0 > above
    for _ in range(100):  # time-like: no inertial frame reverses the order
        dt = rng.uniform(1e-9, 1e-6)
        dist = C * dt * rng.uniform(0.0, 0.95)
        e2 = np.array([dt, dist, 0.0])
        assert K.order_reversal_speed(np.zeros(3), e2, C) >= 1
        for _ in range(20):
            v = rng.normal(size=2)
            v *= rng.uniform(0, 0.999999) * C / np.linalg.norm(v)
            assert _boost(e2, v)[0] - _boost(np.zeros(3), v)[0] > 0


def test_vectorised_events():
    e1 = np.zeros((5, 2))
    e2 = np.stack([np.full(5, 1e-6), np.array([0.0, 100.0, C * 1e-6, 400.0, -1000.0])], axis=1)
    rel = K.relation(e1, e2, C)
    assert list(rel) == [K.TIMELIKE, K.TIMELIKE, K.LIGHTLIKE, K.SPACELIKE, K.SPACELIKE]
    s2 = K.interval(e1, e2, C)
    assert s2.shape == (5,) and s2[3] == pytest.approx((C * 1e-6) ** 2 - 400.0**2, rel=1e-14)
    b = K.order_reversal_speed(e1, e2, C)
    assert math.isinf(b[0]) and b[4] == pytest.approx(C * 1e-6 / 1000.0, rel=1e-14)
