# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Law set for light and clocks: which kinematics and which gravity a world uses.

A law set composes the layers of the engine: the accepted laws (core: special relativity, Schwarzschild) and the
theories outside the core (Newtonian corpuscles: an approximation; ether and emission kinematics: alternatives).
The choice is made explicitly and validated; a world whose law set differs from the accepted one is "modified
physics".

* ``kinematics="SR"``       - Lorentz transformations, light speed c in every inertial frame (core);
* ``kinematics="ether"``    - Galilean transformations, light at c relative to the ether at rest in the lab;
* ``kinematics="emission"`` - Galilean transformations, light at c relative to its source;
* ``gravity="GR"``          - Schwarzschild exterior, null geodesics (core);
* ``gravity="newton"``      - light as Newtonian corpuscles (Soldner); only with the emission kinematics;
* ``gravity="none"``        - bodies have no gravitational field (they still absorb light);
* ``c_factor``              - the speed of light is c_factor * c.

Valid combinations: GR requires SR (Schwarzschild is a solution of GR, whose local kinematics is SR); newton
requires emission.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..core import relativity
from ..core.constants import C
from ..core.gravity import arrivals
from ..theories.alternatives import kinematics as alt

ABOUT = {
    "layer": "laws", "kind": "law set",
    "title": "Законы света и часов: кинематика × гравитация",
    "statement": "Выбор кинематики (СТО / эфир / баллистика) и гравитации (ОТО / ньютоновы корпускулы / нет) для "
                 "мира; общепринятое сочетание — СТО + ОТО.",
    "validity": "сочетания проверяются (validate)",
    "basis": [],
    "conflicts": [],
}

KINEMATICS = [("SR", "СТО (преобразования Лоренца)"),
              ("ether", "Галилей + эфир (скорость c относительно эфира)"),
              ("emission", "Баллистическая (Ритц: c относительно источника)")]
GRAVITY = [("GR", "ОТО (Шварцшильд, нулевые геодезические)"),
           ("newton", "Ньютон: свет как корпускулы (Зольднер)"),
           ("none", "Без гравитации")]
STANDARD = {"kinematics": "SR", "gravity": "GR", "c_factor": 1.0}


@dataclass(frozen=True)
class Laws:
    kinematics: str = "SR"
    gravity: str = "GR"
    c_factor: float = 1.0

    @property
    def c(self) -> float:
        return C * self.c_factor

    @property
    def relativistic(self) -> bool:
        return self.kinematics == "SR"

    @property
    def standard(self) -> bool:
        return (self.kinematics, self.gravity, self.c_factor) == ("SR", "GR", 1.0)

    def validate(self) -> list[str]:
        err = []
        if self.kinematics not in dict(KINEMATICS):
            err.append(f"неизвестная кинематика {self.kinematics}")
        if self.gravity not in dict(GRAVITY):
            err.append(f"неизвестная гравитация {self.gravity}")
        if self.gravity == "GR" and self.kinematics != "SR":
            err.append("ОТО требует СТО: метрика Шварцшильда локально лоренцева. "
                       "Для эфира или баллистики выберите «Без гравитации» или «Ньютон» (только баллистика).")
        if self.gravity == "newton" and self.kinematics != "emission":
            err.append("Ньютоново притяжение света имеет смысл только для корпускул, то есть для "
                       "баллистической кинематики.")
        if not (self.c_factor > 0):
            err.append("скорость света должна быть положительной")
        return err

    def rs(self, gm: float) -> float:
        """Schwarzschild radius 2GM/c^2 (zero unless gravity is GR)."""
        return 2.0 * gm / self.c**2 if self.gravity == "GR" else 0.0

    # --- frames and clocks ----------------------------------------------------------------------------
    def frame_matrix(self, v) -> np.ndarray:
        """Lab (ct, x, y) -> (ct', x', y') of the inertial frame moving with lab velocity v."""
        if self.relativistic:
            return relativity.boost_matrix(v, self.c)
        return alt.galilean_frame_matrix(v, self.c)

    def clock_rate_flat(self, v) -> float:
        """dtau/dt of a clock moving with lab velocity v in flat spacetime (Galilean: absolute time)."""
        return relativity.clock_rate_flat(v, self.c) if self.relativistic else 1.0

    def clock_rate(self, rs: float, pos, vel) -> float:
        """dtau/dt from the metric of the law set (flat or Schwarzschild); Galilean worlds have absolute time."""
        if not self.relativistic:
            return 1.0
        return relativity.metric_clock_rate(self.c, rs, pos, vel)

    def emit_velocities(self, directions_rest: np.ndarray, v_source) -> np.ndarray:
        """Lab velocities of light emitted along unit directions given in the source's rest frame (flat)."""
        if self.kinematics == "ether":
            return alt.ether_emit_velocities(directions_rest, v_source, self.c)
        if self.kinematics == "emission":
            return alt.emission_emit_velocities(directions_rest, v_source, self.c)
        return relativity.emit_velocities(directions_rest, v_source, self.c)

    def front_velocity(self, v_source) -> np.ndarray:
        """Velocity of the centre of a flash's front in flat space: the emission point (SR, ether) or the source
        (emission theory)."""
        return np.asarray(v_source, float) if self.kinematics == "emission" else np.zeros(2)


def flat_arrival(laws: Laws, t0, origin, w, wl, t_from=-math.inf):
    """Arrival of a flash's front (emitted at t0 from ``origin`` by a source with lab velocity ``w``) at a worldline,
    flat spacetime, under the law set's kinematics: the core's front of special relativity (also the ether's, in
    the ether frame = the lab), or the emission theory's front about the moving source (outside the core)."""
    if laws.kinematics == "emission":
        return alt.emission_front_arrival(laws.c, t0, origin, w, wl, t_from)
    return arrivals.front_arrival(laws.c, t0, origin, wl, t_from)
