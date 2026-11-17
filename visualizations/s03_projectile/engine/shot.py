# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""One thrown ball: its flight computed by the engine, sampled for drawing, with the references of its checks.

Orchestration only (``RULES.md`` §1, ``lfphys/LAYERS.md``): the flight is ``lfphys.core.mechanics.fly`` (Newton's
second law in a uniform field, DOP853 with the landing and the apex located by the integrator, the drag's work carried
in the state); the air is the quadratic drag of a sphere with a constant drag coefficient,
``lfphys.theories.models.drag_quadratic`` (a model: its validity is computed along the path); the references are the
closed forms of the flight in vacuum (``lfphys.core.mechanics``), the hodograph quadrature of the quadratic drag (the
second method: no time integration) and, for a vertical throw in air, the closed forms of vertical motion with
quadratic drag. Here: the choice of the ball, the launch vector, the samples every 1/60 s of world time (every 6th is a
multiple of 0.1 s: the strobe), and the comparisons. The second drag model, the measured drag curve of a smooth sphere
(``drag_quadratic.CurveDrag``: C_d(Re) of Morrison 2016 at every instant), flies the same launch for comparison only:
the world's ball always flies with the constant C_d.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import data
from lfphys.core.mechanics import (G_STANDARD, Body, fly, vacuum_apex_height, vacuum_landing_time)
from lfphys.theories.models import drag_quadratic as dq

#: the balls of the world: diameter (m) and mass (kg). A steel ball of 20 mm has 32.9 g at the density of steel
#: (7.85 g/cm³, a nominal value); the light ball has the size and mass of a tennis ball (ITF Rules of Tennis, Appendix
#: I: 6.54–6.86 cm, 56.0–59.4 g; checked 2026-11-14) but is treated as a smooth sphere (C_d 0.47): a real tennis ball's
#: felt has its own drag.
OBJECTS = {"steel20": {"d": 0.020, "m": 0.0329}, "ball67": {"d": 0.067, "m": 0.058}}
#: samples per world second: t_k = k/60 s exactly, so every 6th is a multiple of 0.1 s (the strobe); a polyline through
#: them departs from the computed path by at most g·Δt²/8 = 0.34 mm (Δt = 1/60 s), far below a pixel
RATE = 60.0
STROBE_EVERY = 6
AIR_T_C, AIR_P = 20.0, data.P_ATM  # the air: 20 °C, 101 325 Pa (U.S. Standard Atmosphere 1976 through core.data)
VALID_SHARE = 0.01  # the constant C_d's check: under 1 % of the drag's work done outside its Reynolds range


def medium() -> dict:
    """The air's density and viscosity (``core.data.fluid_properties``)."""
    return data.fluid_properties("air", AIR_T_C, AIR_P)


def body_of(obj: str) -> Body:
    o = OBJECTS[obj]
    return Body(o["m"], o["d"], obj)


def drag_of(obj: str) -> dq.QuadraticDrag:
    return dq.QuadraticDrag.sphere(OBJECTS[obj]["d"], medium())


def curve_flight(obj: str, h: float, v0: float, angle_deg: float):
    """The same launch in air with the second drag model, the measured drag curve (``drag_quadratic.CurveDrag``): the
    engine's flight (its ``range``, ``flight_time``). For comparison only (R-E F1): it shows how much the constant C_d
    itself moves the result."""
    vx, vy = launch_vector(v0, angle_deg)
    return fly(body_of(obj), (0.0, float(h)), (vx, vy), forces=[dq.CurveDrag.sphere(OBJECTS[obj]["d"], medium())])


def launch_vector(v0: float, angle_deg: float) -> tuple[float, float]:
    """(v_x, v_y) of a launch: exact zeros at 0° and 90° (cos 90° is not exactly zero in floating point)."""
    if angle_deg == 90.0:
        return 0.0, float(v0)
    if angle_deg == 0.0:
        return float(v0), 0.0
    a = math.radians(angle_deg)
    return v0 * math.cos(a), v0 * math.sin(a)


class Shot:
    """A ball of kind ``obj`` launched from (0, h) at v0 and angle_deg, in vacuum or in air (``air``)."""

    def __init__(self, obj: str, h: float, v0: float, angle_deg: float, air: bool):
        self.obj, self.h, self.v0, self.angle, self.air = obj, float(h), float(v0), float(angle_deg), bool(air)
        self.body = body_of(obj)
        self.drag = drag_of(obj) if air else None
        self.vx0, self.vy0 = launch_vector(self.v0, self.angle)
        self.k = self.drag.k(self.body.mass) if air else 0.0
        self.flight = fly(self.body, (0.0, self.h), (self.vx0, self.vy0), forces=[self.drag] if air else [])
        fl = self.flight
        self.T = fl.flight_time
        self.L = fl.range
        self.H = fl.apex_height
        self.t_apex = fl.apex["t"] if fl.apex else None
        s = fl.sample(RATE)
        self.ts = s["t"]
        self.xs, self.ys = s["r"][:, 0], s["r"][:, 1]
        self.vxs, self.vys = s["v"][:, 0], s["v"][:, 1]
    # --- the state ----------------------------------------------------------------------------------------------------
    def at(self, t: float) -> dict:
        """The state at t (clamped to the flight; after the landing the ball lies where it landed)."""
        return self.flight.record(min(max(float(t), 0.0), self.T))

    def rows(self, i0: int, i1: int) -> np.ndarray:
        """Samples i0..i1-1 as rows t, x, y (the drawn table: blob ``s`` of ``traj``)."""
        return np.column_stack([self.ts[i0:i1], self.xs[i0:i1], self.ys[i0:i1]])

    def n_until(self, t: float) -> int:
        """How many samples have times <= t."""
        return int(np.searchsorted(self.ts, t * (1 + 1e-15) + 1e-15, side="right"))

    def box(self) -> tuple[float, float, float]:
        """x_min, x_max, y_max of the computed path (samples and landing)."""
        xs = np.append(self.xs, self.L)
        return float(xs.min()), float(xs.max()), float(max(self.ys.max(), self.H))

    # --- the references -----------------------------------------------------------------------------------------------
    def references(self) -> dict:
        """T, L, H of the second method: in vacuum the closed forms; in air the hodograph quadrature (any launch with a
        horizontal speed) or the closed forms of vertical motion with quadratic drag (a vertical throw or a drop)."""
        g = self.flight.g
        if not self.air:
            T = vacuum_landing_time(self.h, self.vy0, g)
            return {"T": T, "L": self.vx0 * T, "H": vacuum_apex_height(self.h, self.vy0, g), "how": "vacuum"}
        if self.vx0 > 0.0:
            r = dq.hodograph(self.v0, math.radians(self.angle), self.h, self.k, g)
            return {"T": r["T"], "L": r["L"], "H": r["H"], "how": "hodograph"}
        if self.vy0 > 0.0:  # straight up, then down from the top
            up = dq.vertical_up(0.0, self.vy0, self.k, g)
            top = self.h + up["h_up"]
            return {"T": up["t_top"] + dq.fall_time(top, self.k, g), "L": 0.0, "H": top, "how": "vertical"}
        return {"T": dq.fall_time(self.h, self.k, g), "L": 0.0, "H": self.h, "how": "vertical"}

    def energy_balance(self) -> float:
        return self.flight.energy_balance()

    def validity(self) -> dict | None:
        return dq.validity(self.flight, self.drag) if self.air else None


def optimum_angle(obj: str, h: float, v0: float, air: bool, step: float = 0.1,
                  curve: bool = False) -> tuple[float, float, int]:
    """The launch angle of the largest range (degrees), that range and the number of flights computed: a scan at 1°
    steps, then at ``step`` around the best one. No closed form exists with quadratic drag; it is the engine's
    computation. ``curve``: in air with the measured drag curve instead of the constant C_d (the second model)."""
    def rng(a):
        return curve_flight(obj, h, v0, a).range if (air and curve) else Shot(obj, h, v0, a, air).L
    coarse = np.arange(1.0, 89.5, 1.0)
    best = float(coarse[int(np.argmax([rng(a) for a in coarse]))])
    fine = np.round(np.arange(best - 1.0, best + 1.0 + step / 2, step), 6)
    ls = [rng(a) for a in fine]
    i = int(np.argmax(ls))
    return float(fine[i]), float(ls[i]), len(coarse) + len(fine)


G = G_STANDARD
