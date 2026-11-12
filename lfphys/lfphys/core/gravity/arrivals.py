# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Exact arrival events of a light flash at a receiver worldline.

A flash is an emission event (t0, origin) by a source with lab velocity w. Its front reaches the receiver at the
first t >= t0 (and t >= t_from) where the receiver's worldline meets it:

* flat (special relativity): |x_R(t) - origin| = c (t - t0), the front centred on the emission event; solved
  exactly per inertial piece (quadratic), by bracketing + brentq on orbits (``worldlines.sphere_meeting``);
  the front of the refuted emission theory (centred on the moving source) is computed outside the core,
  ``lfphys.theories.alternatives.kinematics.emission_front_arrival`` (review 2026-10-23, E8);
* GR: geodesics connecting the emission point with the receiver's position (``schwarzschild.connect``); for a
  moving receiver the arrival time is the fixed point t = t0 + dt(x_R(t)), iterated to 1e-13 relative; each
  image (ccw / cw) is a separate arrival;
* Newtonian corpuscles: ``lfphys.theories.alternatives.newton_light.newton_arrivals`` (a refuted alternative, outside the core).

Returned arrival: dict(t, image, dir) with ``dir`` the unit lab propagation direction of the light at the
receiver (local static frame in GR).
"""

from __future__ import annotations

import math

import numpy as np

from ..numerics import moving_root
from ..worldlines import sphere_meeting
from . import schwarzschild

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Приход вспышки к мировой линии",
    "statement": "Момент встречи фронта вспышки с приёмником: в плоском пространстве — квадратное уравнение на "
                 "каждом инерциальном куске (СТО: фронт с центром в точке вспышки при любом движении источника); "
                 "в ОТО — точное соединение геодезическими и поиск корня для движущегося приёмника.",
    "validity": "плоское пространство или внешность Шварцшильда",
    "basis": ["lfphys.core.gravity.schwarzschild"],
    "conflicts": [],
}


def front_arrival(c, t0, origin, wl, t_from=-math.inf):
    """Arrival of the light front of a flash (emission event t0, ``origin``) at a worldline in flat spacetime: in
    special relativity the front is the sphere |x - origin| = c (t - t0), centred on the emission event whatever the
    motion of the source. Returns dict(t, image, dir, speed_lab, method) or None."""
    return sphere_meeting(c, t0, origin, np.zeros(2), wl, t_from)


def gr_arrivals(c, rs, r_abs, t0, origin, wl, t_from=-math.inf):
    """Arrivals of the primary and the secondary image (the two lowest-order paths, one on each side of the body)
    of a flash at a worldline, Schwarzschild exterior."""
    origin = np.asarray(origin, float)
    out = []
    first = schwarzschild.connect(origin, wl.pos(max(t0, t_from)), rs, c, r_abs)
    for img0 in first:
        side = img0["side"]
        last = {}

        def dt_of(pos, side=side, last=last):
            imgs = [m for m in schwarzschild.connect(origin, pos, rs, c, r_abs) if m["side"] == side]
            if not imgs:
                return None
            last["img"] = imgs[0]
            return imgs[0]["dt"]

        t = moving_root(dt_of, t0, t_from, wl)
        if t is None:
            continue
        dt_of(wl.pos(t))
        img = last["img"]
        out.append({"t": float(t), "image": 0, "side": side, "key": f"s{side:+d}", "dir": img["arrive_dir"].tolist(),
                    "b": img["b"], "branch": img["branch"], "emit_dir": img["emit_dir"].tolist(),
                    "method": "exact (quadrature + root finding)"})
    out.sort(key=lambda a: a["t"])
    for i, a in enumerate(out):
        a["image"] = i
    return out
