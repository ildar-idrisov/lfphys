# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Worldlines of objects in lab coordinates (t, x, y).

In GR runs the lab coordinates are Schwarzschild (t, r, phi) drawn as x = r cos(phi), y = r sin(phi); proper time
then comes from the metric. In flat runs they are inertial lab coordinates.

* ``Piecewise`` - inertial segments; an action "boost" ends the current segment at the current time.
* ``Orbit``     - a circular orbit about the origin with angular velocity omega (set by the scenario from Kepler's
                  law, which for circular orbits holds exactly in Schwarzschild coordinates).

Proper time is integrated with the clock rate of the world's law set (``clock_rate``, ``lfphys.laws``); in accepted
physics (``lfphys.core.relativity``):
  flat SR:   dtau/dt = sqrt(1 - v^2/c^2);
  GR:        dtau/dt = sqrt(f - (v_r^2/f + v_t^2)/c^2),  f = 1 - rs/r  (v_r, v_t: coordinate velocities).
(The absolute time of Galilean kinematics, dtau/dt = 1, is an alternative outside the core:
``lfphys.theories.alternatives.kinematics``; review 2026-10-23, E8.)

``sphere_meeting``: the geometry of the first meeting of a worldline with an expanding sphere about a (possibly
moving) centre; which sphere is a light front is decided by the physics that calls it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import integrate, optimize

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "kinematics",
    "title": T("Worldlines and proper time"),
    "statement": T("Piecewise inertial worldlines and circular orbits; proper time is the integral of the clock "
                   "rate in the metric of the world's laws (SR: sqrt(1 - v²/c²); Schwarzschild: sqrt(f - (v_r²/f + "
                   "v_t²)/c²))."),
    "validity": T("the clock rate is set by the world's law set (lfphys.laws); the accepted one is "
                  "lfphys.core.relativity"),
    "basis": ["lfphys.core.relativity.metric_clock_rate"],
    "conflicts": [],
}


def clock_rate(laws, rs: float, pos, vel) -> float:
    """dtau/dt from the world's law set (``laws.clock_rate``)."""
    return laws.clock_rate(rs, pos, vel)


@dataclass
class Segment:
    t0: float
    x0: np.ndarray
    v: np.ndarray
    tau0: float  # proper time at t0


@dataclass
class Piecewise:
    laws: object  # a law set (lfphys.laws): c, relativistic, clock_rate, clock_rate_flat
    rs: float
    segments: list = field(default_factory=list)

    @classmethod
    def start(cls, laws, rs, t0, x0, v, tau0=0.0):
        w = cls(laws, rs)
        w.segments.append(Segment(float(t0), np.asarray(x0, float), np.asarray(v, float), float(tau0)))
        w._check(w.segments[0])
        return w

    def _check(self, s: Segment):
        clock_rate(self.laws, self.rs, s.x0, s.v)

    def _seg(self, t: float) -> Segment:
        seg = self.segments[0]
        for s in self.segments:
            if s.t0 <= t:
                seg = s
            else:
                break
        return seg

    def pos(self, t: float) -> np.ndarray:
        s = self._seg(t)
        return s.x0 + s.v * (t - s.t0)

    def vel(self, t: float) -> np.ndarray:
        return self._seg(t).v.copy()

    def tau(self, t: float) -> float:
        s = self._seg(t)
        return s.tau0 + self._dtau(s, s.t0, t)

    def _dtau(self, s: Segment, ta: float, tb: float) -> float:
        if tb == ta:
            return 0.0
        if not self.laws.relativistic:
            return tb - ta
        if self.rs == 0.0:
            return (tb - ta) * self.laws.clock_rate_flat(s.v)
        if not np.any(s.v):
            return (tb - ta) * clock_rate(self.laws, self.rs, s.x0, s.v)
        val, _ = integrate.quad(lambda t: clock_rate(self.laws, self.rs, s.x0 + s.v * (t - s.t0), s.v),
                                ta, tb, epsabs=0.0, epsrel=1e-13, limit=200)
        return val

    def boost(self, t: float, v_new) -> None:
        """Change velocity at lab time t (t must not precede the last segment start)."""
        last = self.segments[-1]
        if t < last.t0:
            raise ValueError("boost before the last change of motion")
        x = self.pos(t)
        tau = self.tau(t)
        seg = Segment(float(t), x, np.asarray(v_new, float), tau)
        self._check(seg)
        if t == last.t0:
            self.segments[-1] = seg
        else:
            self.segments.append(seg)

    def pieces(self, t_from: float = -math.inf):
        """(t_start, t_end, x0_at_t_start, v) for segments overlapping [t_from, inf)."""
        out = []
        for i, s in enumerate(self.segments):
            t_end = self.segments[i + 1].t0 if i + 1 < len(self.segments) else math.inf
            if t_end <= t_from:
                continue
            ta = max(s.t0, t_from)
            out.append((ta, t_end, s.x0 + s.v * (ta - s.t0), s.v))
        return out

    def to_json(self) -> dict:
        return {"kind": "piecewise",
                "segments": [{"t0": s.t0, "x0": s.x0.tolist(), "v": s.v.tolist(), "tau0": s.tau0}
                             for s in self.segments]}


@dataclass
class Orbit:
    laws: object  # a law set (lfphys.laws): c, relativistic, clock_rate, clock_rate_flat
    rs: float
    radius: float
    omega: float
    phase0: float = 0.0
    tau0: float = 0.0

    def pos(self, t: float) -> np.ndarray:
        a = self.phase0 + self.omega * t
        return self.radius * np.array([math.cos(a), math.sin(a)])

    def vel(self, t: float) -> np.ndarray:
        a = self.phase0 + self.omega * t
        return self.radius * self.omega * np.array([-math.sin(a), math.cos(a)])

    def rate(self) -> float:
        return clock_rate(self.laws, self.rs, self.pos(0.0), self.vel(0.0))

    def tau(self, t: float) -> float:
        return self.tau0 + self.rate() * t

    def pieces(self, t_from: float = -math.inf):
        return None

    def to_json(self) -> dict:
        return {"kind": "orbit", "radius": self.radius, "omega": self.omega, "phase0": self.phase0}


def sphere_meeting(c, t0, origin, w, wl, t_from=-math.inf):
    """Geometry of flat space: the first time t >= max(t0, t_from) at which a worldline (Piecewise or Orbit) meets a
    sphere of radius c (t - t0) about a centre moving as ``origin + w (t - t0)``. Exact per inertial piece (a
    quadratic), bracketing + brentq on orbits. Returns dict(t, dt, image, dir, speed_lab, method) with ``dt`` the
    flight time t - t0 (on inertial pieces summed from the solved interval, exact to round-off of dt itself) and
    ``dir`` the unit direction from the emission point to the meeting point, or None. Which sphere is a light front is physics: the
    centre at rest at the emission event in special relativity (``lfphys.core.gravity.arrivals.front_arrival``); a
    centre moving with the source in the refuted emission theory (``lfphys.theories.alternatives.kinematics``)."""
    origin = np.asarray(origin, float)
    w = np.asarray(w, float)
    t_start = max(t0, t_from)
    if isinstance(wl, Piecewise):
        for ta, tb, xa, v in wl.pieces(t_start):
            # xa is the position at ta (pieces() already shifted it)
            hit = _flat_piece_shifted(c, t0, origin, w, ta, tb, xa, v)
            if hit is not None:
                t, dt = hit
                if t_from > t0 and t <= t_from:
                    continue  # an arrival exactly at the start of the search is in the past (review R2)
                return _flat_result(t0, origin, w, wl, t, dt)
        return None
    if isinstance(wl, Orbit):
        def g(t):
            return np.linalg.norm(wl.pos(t) - origin - w * (t - t0)) - c * (t - t0)
        lo = t_start
        if g(lo) <= 0:
            return _flat_result(t0, origin, w, wl, lo) if lo == t0 else None
        step = max(np.linalg.norm(wl.pos(lo) - origin) / c, 1e-12)
        hi = lo + step
        for _ in range(200):
            if g(hi) <= 0:
                break
            lo, hi = hi, hi + step
            step *= 2
        else:
            return None
        t = optimize.brentq(g, lo, hi, xtol=1e-15 * max(1.0, abs(hi)), rtol=1e-15, maxiter=300)
        return _flat_result(t0, origin, w, wl, t)
    raise TypeError(type(wl))


def _flat_piece_shifted(c, t0, origin, w, ta, tb, xa, v):
    """First t in [ta, tb), t >= t0, where the receiver (at xa at time ta, velocity v) meets the front: (t, t - t0),
    the flight time t - t0 summed from the solved interval itself (not a difference of absolute times, which at
    t ~ 4e11 s loses 3e-8 of an 1868 s flight: review UX-params P14), or None."""
    if tb <= t0:
        return None
    if ta < t0:
        xa = xa + v * (t0 - ta)
        ta = t0
    d = xa - origin - w * (ta - t0)
    u = v - w
    tau0 = ta - t0
    A = float(u @ u) - c * c
    B = 2.0 * float(d @ u) - 2.0 * c * c * tau0
    C = float(d @ d) - c * c * tau0 * tau0
    if C <= 0 and tau0 == 0:
        return (ta, 0.0) if float(d @ d) == 0 else None
    roots = []
    if A == 0:
        if B != 0:
            roots = [-C / B]
    else:
        disc = B * B - 4 * A * C
        if disc < 0:
            return None
        sq = math.sqrt(disc)
        q = -0.5 * (B + math.copysign(sq, B))
        roots = [q / A] + ([C / q] if q != 0 else [])
    cand = sorted(s for s in roots if s >= 0.0 and ta + s < tb)
    return (ta + cand[0], tau0 + cand[0]) if cand else None


def _flat_result(t0, origin, w, wl, t, dt=None):
    """The meeting at absolute time t; ``dt`` = t - t0 when the caller knows it more precisely than the difference."""
    dt = (t - t0) if dt is None else dt
    xr = wl.pos(t)
    u = (xr - origin) / dt if dt > 0 else np.zeros(2)  # lab light velocity along the connecting line
    n = np.linalg.norm(u)
    return {"t": float(t), "dt": float(dt), "image": 0, "dir": (u / n).tolist() if n > 0 else [0.0, 0.0],
            "speed_lab": float(n), "method": "exact (quadratic)"}
