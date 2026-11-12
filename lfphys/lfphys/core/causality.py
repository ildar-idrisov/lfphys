# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Causal structure of Minkowski space-time: the invariant interval between two events, their causal relation, the
light cone, and the frame dependence of the time order of space-like separated events.

Events are arrays ``(t, x)``, ``(t, x, y)`` or ``(t, x, y, z)`` (time in seconds, positions in metres) in one inertial
lab frame; leading axes broadcast, so many pairs of events are handled at once.

* interval: s^2 = c^2 (t2 - t1)^2 - |r2 - r1|^2 (signature +---); invariant under Lorentz transformations;
* relation: time-like (s^2 > 0), light-like (s^2 = 0), space-like (s^2 < 0); only time- or light-like events can be
  connected by a signal (no influence travels faster than c);
* in a frame moving with lab velocity v the time difference is dt' = gamma (dt - v.dr / c^2) (Lorentz
  transformation); for space-like events it changes sign in frames moving along dr faster than
  v* = c^2 |dt| / |dr| < c, so their time order is not absolute; for time-like events no inertial frame reverses it.

Exact closed forms evaluated in float64; tests compare them with the Lorentz matrices of ``lfphys.core.relativity``.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "kinematics",
    "title": T("The causal structure of spacetime: the interval and the light cone"),
    "statement": T("The interval s² = c²Δt² − |Δr|² is invariant; events are timelike (s² > 0), lightlike (s² = 0) "
                   "or spacelike (s² < 0). A signal connects only events inside or on the light cone; the time order "
                   "of spacelike events depends on the frame: it reverses in frames moving along Δr faster than v* = "
                   "c²|Δt|/|Δr| < c."),
    "validity": T("flat spacetime (SR); in a gravitational field, locally"),
    "basis": ["Einstein, Ann. Phys. 17, 891 (1905)", "Minkowski, Phys. Z. 10, 104 (1909)",
              T("the locality condition in Bell experiments: Bell 1964; Aspect, Dalibard, Roger, PRL 49, 1804 "
                "(1982); Weihs et al., PRL 81, 5039 (1998)")],
    "conflicts": [],
}

TIMELIKE, LIGHTLIKE, SPACELIKE = 1, 0, -1


def _split(e1, e2):
    e1 = np.asarray(e1, dtype=float)
    e2 = np.asarray(e2, dtype=float)
    if e1.shape[-1] != e2.shape[-1] or e1.shape[-1] < 2:
        raise ValueError("events must be (t, x[, y[, z]]) of the same dimension")
    dt = e2[..., 0] - e1[..., 0]
    dr = e2[..., 1:] - e1[..., 1:]
    return dt, dr


def interval(e1, e2, c: float):
    """s^2 = c^2 dt^2 - |dr|^2 (m^2); positive time-like, negative space-like."""
    dt, dr = _split(e1, e2)
    s2 = (c * dt) ** 2 - np.sum(dr * dr, axis=-1)
    return float(s2) if np.ndim(s2) == 0 else s2


def relation(e1, e2, c: float, rtol: float = 1e-12):
    """+1 time-like, 0 light-like (|s^2| <= rtol (c^2 dt^2 + |dr|^2)), -1 space-like."""
    dt, dr = _split(e1, e2)
    a = (c * dt) ** 2
    b = np.sum(dr * dr, axis=-1)
    s2 = a - b
    out = np.where(np.abs(s2) <= rtol * (a + b), LIGHTLIKE, np.where(s2 > 0, TIMELIKE, SPACELIKE))
    return int(out) if np.ndim(out) == 0 else out


def in_future_cone(e_from, e_to, c: float, rtol: float = 1e-12):
    """True when e_to lies inside or on the future light cone of e_from: a signal from e_from can reach it."""
    dt, _ = _split(e_from, e_to)
    rel = relation(e_from, e_to, c, rtol)
    out = (np.asarray(rel) >= LIGHTLIKE) & (dt >= 0)
    return bool(out) if np.ndim(out) == 0 else out


def time_difference_in_frame(e1, e2, v, c: float):
    """t2' - t1' in the inertial frame moving with lab velocity v (a vector of the events' spatial dimension):
    dt' = gamma (dt - v.dr / c^2)."""
    dt, dr = _split(e1, e2)
    v = np.asarray(v, dtype=float)
    if v.shape[-1] != dr.shape[-1]:
        raise ValueError("velocity must have the events' spatial dimension")
    b2 = float(v @ v) / c**2 if v.ndim == 1 else None
    if b2 is None:
        raise ValueError("one velocity vector per call")
    if b2 >= 1.0:
        raise ValueError("|v| >= c: no inertial frame moves at or faster than light")
    g = 1.0 / math.sqrt(1.0 - b2)
    out = g * (dt - (dr @ v) / c**2)
    return float(out) if np.ndim(out) == 0 else out


def order_reversal_speed(e1, e2, c: float):
    """Smallest speed, as a fraction of c, of an inertial frame (moving along dr) in which the time order of the two
    events is reversed: beta* = c |dt| / |dr|. It is below 1 exactly for space-like events; for time-like or
    light-like events it is >= 1 (no inertial frame reverses their order). Infinite when dr = 0."""
    dt, dr = _split(e1, e2)
    r = np.sqrt(np.sum(dr * dr, axis=-1))
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(r > 0, c * np.abs(dt) / np.where(r > 0, r, 1.0), np.inf)
    return float(out) if np.ndim(out) == 0 else out
