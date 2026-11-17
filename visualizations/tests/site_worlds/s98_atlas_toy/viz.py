# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A toy school demonstration for the tests of the atlases and the screens (``tests/test_atlas.py``,
``tests/test_atlas_live.py``, the player's screens; design ``lfphys/sources/explore_2026-11-14_design.md`` §8; found
only through ``LFVIZ_EXTRA``, never in the catalogue). It is the fixture of the player's step: its built atlases are
committed in ``tests/site_worlds/recordings/s98_atlas_toy/`` (``tests/site_worlds/make_fixture.py`` remakes them;
``tests/test_atlas.py`` checks that they are what the builder makes now).

A ball thrown from a height ``h_m`` at a speed ``v0`` and an angle ``angle_deg`` in a uniform field, without air. It is
a test world: its motion is the closed form of the uniform field (not an engine module), sampled every 1/120 s of
world time and sent in ``traj`` chunks (blob ``s``: t, x, y, vx, vy per row) as the run's time reaches the samples; the
apex and the landing are events when the time reaches them (the landing's data: T, L, v); every frame carries ``meas``
(x, y, v and, once reached, range, flight_time, apex_h) and a blob ``ghost`` (dropped by the Explore screen); a ``story``
message at the landing (dropped by the Explore screen). Its checks at the landing: the landing time found by bisection
of y(t) = 0 against the quadratic formula, and the energy at the landing against the start. With ``companion: drop`` a
second ball is dropped at the same moment (its height in the frames, ``drop_y``). The world refuses h = 0 with an angle
≤ 0 (no flight), so that an atlas has a refused point. Its three screens: Watch (the recording ``story`` with captions,
a ``speed`` change and a new world in its script), Explore (h × angle, 2 × 3 points, one refused) and Lab work (one
step, five heights off a chute, with two laws: the slope of L against √h, and the intercept of the line through the same
points, zero; their references from ``lab_reference``).
"""

from __future__ import annotations

import math

import numpy as np

from lfviz.errors import Refusal
from lfviz.i18n import T
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as Base

G = 9.80665  # the conventional standard gravity, m/s² (scipy.constants.g)
DT = 1.0 / 120.0  # the sampling of the path, world seconds

SCHEMA = Schema([
    Param("h_m", T("Height"), "float", 1.0, unit=T("m"), min=0.0, max=5.0),
    Param("v0", T("Speed"), "float", 2.0, unit=T("m/s"), min=0.0, max=10.0),
    Param("angle_deg", T("Angle"), "float", 0.0, unit="°", min=-30.0, max=90.0),
    Param("companion", T("Second ball"), "select", "none",
          options=[("none", T("none")), ("drop", T("a ball dropped at the same moment"))]),
], presets={
    "field": {"label": T("A throw from a table"), "params": {"h_m": 1.0, "v0": 2.0, "angle_deg": 0.0}},
    "chute": {"label": T("A ball off a chute"), "params": {"h_m": 0.6, "v0": 1.5, "angle_deg": 0.0}},
    "story": {"label": T("Two balls at the same moment"), "params": {"h_m": 1.25, "v0": 2.0, "companion": "drop"}},
})

MEASURABLES = [{"id": "range", "label": T("Range"), "unit": "m"},
               {"id": "flight_time", "label": T("Flight time"), "unit": "s"},
               {"id": "apex_h", "label": T("Apex height"), "unit": "m"}]


class Simulation(Base):
    default_speed = 1.0
    speed_range = (0.01, 10.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.h = float(params["h_m"])
        self.v0 = float(params["v0"])
        a = math.radians(float(params["angle_deg"]))
        self.vx, self.vy = self.v0 * math.cos(a), self.v0 * math.sin(a)
        self.drop = params.get("companion") == "drop"
        disc = self.vy * self.vy + 2.0 * G * self.h
        self.T = (self.vy + math.sqrt(disc)) / G  # the landing time (quadratic formula: the check's reference)
        self.T_apex = self.vy / G if self.vy > 0 else None
        self.next_sample = 0  # index of the next sample to send
        self.landed = False
        self.apexed = self.T_apex is None

    @classmethod
    def check_params(cls, params):
        if float(params["h_m"]) <= 0.0 and float(params["angle_deg"]) <= 0.0:
            raise Refusal(T("The ball starts on the ground moving along it or into it: no flight"),
                          T("raise the height or the angle"))

    @classmethod
    def lab_reference(cls, step_id, fixed, values, reference):
        """The laws of a lab step (design §2.3, integrator D4): ``heights``: L = k·√h with k = v₀·√(2/g) (a horizontal
        throw; ``k_horizontal``), so the line through the points has no intercept (``zero_intercept``)."""
        if step_id == "heights" and reference == "k_horizontal":
            v0 = float(fixed["v0"])
            return {"value": v0 * math.sqrt(2.0 / G), "unit": "m^½", "label": T("k = v₀·√(2/g)"),
                    "how": T("closed form of a horizontal throw without air"), "kind": "closed form"}
        if step_id == "heights" and reference == "zero_intercept":
            return {"value": 0.0, "unit": "m", "label": T("no intercept: L = k·√h"),
                    "how": T("closed form of a horizontal throw without air"), "kind": "closed form"}
        raise ValueError(T("no law for the step {step}", step=step_id))

    def pos(self, t):
        t = min(t, self.T)
        return self.vx * t, self.h + self.vy * t - 0.5 * G * t * t

    def vel(self, t):
        if t >= self.T:
            return 0.0, 0.0
        return self.vx, self.vy - G * t

    def header(self):
        L = self.vx * self.T
        H = self.h + (self.vy ** 2 / (2 * G) if self.vy > 0 else 0.0)
        return {"title": T("A thrown ball for the tests of the atlases"),
                "scene": {"box": [[-0.2, -0.05], [max(1.0, L * 1.1), max(1.0, H * 1.15)]]},
                "launcher": {"h": self.h, "angle": float(self.params["angle_deg"]), "v0": self.v0},
                "companion": self.params.get("companion"), "measurables": MEASURABLES,
                "units": {"t": T("s"), "x": T("m")}, "actions": []}, {"ticks": np.linspace(0.0, 5.0, 51)}

    def _samples(self, t_target):
        rows = []
        while self.next_sample < 10 ** 9:
            ts = min(self.next_sample * DT, self.T)
            if ts > t_target + 1e-12:
                break
            x, y = self.pos(ts)
            vx, vy = self.vel(ts) if ts < self.T else (self.vx, self.vy - G * self.T)
            rows.append((ts, x, y, vx, vy))
            self.next_sample += 1
            if ts >= self.T:
                self.next_sample = 10 ** 9  # the last sample is the landing itself
                break
        if rows:
            self.emit({"type": "traj", "t": t_target, "n": len(rows)}, {"s": np.array(rows, dtype=np.float64)})

    def advance(self, t_target):
        if not self.apexed and self.T_apex <= t_target:
            self.apexed = True
            self.emit({"type": "event", "kind": "apex", "t": self.T_apex, "text": T("apex"),
                       "data": {"H": self.pos(self.T_apex)[1]}})
        self._samples(t_target)
        if not self.landed and self.T <= t_target:
            self.landed = True
            L = self.vx * self.T
            vy = self.vy - G * self.T
            self.emit({"type": "event", "kind": "landing", "t": self.T, "text": T("landing"),
                       "data": {"T": self.T, "L": L, "v": math.hypot(self.vx, vy)}})
            self.emit({"type": "story", "t": self.T, "text": T("the ball has landed")})
            lo, hi = 0.0, self.T * 2 + 1.0  # the second method: bisection of y(t) = 0 on the path's own formula
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if self.h + self.vy * mid - 0.5 * G * mid * mid > 0:
                    lo = mid
                else:
                    hi = mid
            t_bis = 0.5 * (lo + hi)
            self.emit({"type": "check", "t": self.T, "id": "landing_time", "label": T("landing time"),
                       "value": t_bis, "ref": self.T, "unit": "s", "rel": (t_bis - self.T) / self.T, "tol": 1e-12,
                       "group": "", "note": T("bisection of y(t) = 0 against the quadratic formula")})
            e0 = 0.5 * self.v0 ** 2 + G * self.h
            e1 = 0.5 * (self.vx ** 2 + vy ** 2)
            self.emit({"type": "check", "t": self.T, "id": "energy", "label": T("energy at the landing"),
                       "value": e1, "ref": e0, "unit": "J/kg", "rel": (e1 - e0) / e0, "tol": 1e-12, "group": "",
                       "note": T("per unit mass, against the start")})
        self.t = t_target

    def frame(self):
        x, y = self.pos(self.t)
        vx, vy = self.vel(self.t)
        meas = {"x": x, "y": y, "v": math.hypot(vx, vy),
                "range": self.vx * self.T if self.landed else None,
                "flight_time": self.T if self.landed else None,
                "apex_h": (self.pos(self.T_apex)[1] if self.T_apex is not None else self.h) if self.apexed else None}
        meta = {"x": x, "y": y, "landed": self.landed, "meas": meas}
        if self.drop:
            meta["drop_y"] = max(0.0, self.h - 0.5 * G * self.t * self.t)
        return meta, {"ghost": np.full(16, x, dtype=np.float32)}

    def next_event_time(self):
        if not self.apexed:
            return self.T_apex
        return None if self.landed else self.T

    def max_step(self):
        return 0.05


_STEP_COLS = [{"id": "h", "label": T("h, m"), "from": "ruler"},
              {"id": "L", "label": T("L, m"), "from": "tape"},
              {"id": "sqrt_h", "label": T("√h, m^½"), "of": "h", "op": "sqrt"}]

VIZ = {
    "id": "s98_atlas_toy", "title": T("A thrown ball for the tests of the atlases"), "summary": "", "purpose": "",
    "version": "1.0", "schema": SCHEMA, "simulation": Simulation, "audience": "school", "section": "mechanics",
    "teaser": T("A ball is thrown; where does it land?"), "related": [],
    "curriculum": [{"system": "FRP-OOO-2025-base", "grade": 7}, {"system": "AP1", "unit": 1}],
    "recordings": [
        {"id": "story", "preset": "story", "seconds": 6, "fps": 10, "speed": 0.25, "seed": 1, "poster": 1.5,
         "script": [{"at": 3.0, "cmd": "new_world", "args": {"preset": "story", "params": {"v0": 4.0}}},
                    {"at": 4.5, "cmd": "speed", "args": {"value": 0.5}}],
         "captions": [{"at": 0.0, "text": T("Two balls start at the same moment: one is dropped, the other thrown.")},
                      {"at": 1.5, "text": T("At every moment both balls are at the same height."), "hold": 1.0},
                      {"at": 3.0, "text": T("Twice the speed: twice as far, at the same moment.")}],
         "quantize": {"traj.s": "u16"}},
        {"id": "field", "preset": "field", "seconds": 2, "fps": 10, "speed": None, "seed": 1, "poster": 1.0},
    ],
    "screens": [
        {"id": "watch", "kind": "watch", "recording": "story", "more": ["field"]},
        {"id": "explore", "kind": "explore", "preset": "field", "fixed": {},
         "controls": [{"param": "h_m", "values": [0.0, 1.0], "default": 1.0},
                      {"param": "angle_deg", "values": [0.0, 30.0, 60.0], "default": 0.0}],
         "acts": "next", "time": "flight", "frame_dt": 1 / 30,
         "stop": {"event": "landing", "after_s": 0.2, "max_world_s": 5.0},
         "drop": {"types": ["story"], "frame_blobs": ["ghost"]},
         "quantize": {"traj.s": "u16", "header.ticks": "u16"},
         "overlays": ["path", "strobe", "v"], "traces": 3, "readouts": ["range", "flight_time", "apex_h"]},
        {"id": "lab", "kind": "lab",
         "instruments": {
             "tape": {"kind": "ruler", "label": T("Measuring tape"), "unit": "m", "division": 0.001, "error": 0.0005,
                      "reads": "range"},
             "ruler": {"kind": "ruler", "label": T("Ruler"), "unit": "m", "division": 0.01, "error": 0.005,
                       "reads": "control:h_m"},
             "stopwatch": {"kind": "stopwatch", "label": T("Stopwatch"), "unit": "s", "division": 0.01, "error": 0.2,
                           "manual": True, "error_note": T("your reaction time, about 0.2 s")}},
         "steps": [{"id": "heights", "title": T("Height and range"),
                    "goal": T("Find how the range depends on the height of the throw"), "preset": "chute",
                    "controls": [{"param": "h_m", "values": [0.2, 0.4, 0.6, 0.8, 1.0], "default": 0.6}],
                    "fixed": {"v0": 1.5}, "instruments": ["ruler", "tape", "stopwatch"], "columns": _STEP_COLS,
                    "plot": {"x": "sqrt_h", "y": "L", "fit": "line0", "fits": ["line0", "line"]},
                    "laws": [{"x": "sqrt_h", "y": "L", "model": "line0", "quantity": "slope", "label": T("k = L / √h"),
                              "unit": "m^½", "reference": "k_horizontal"},
                             {"x": "sqrt_h", "y": "L", "model": "line", "quantity": "intercept",
                              "label": T("intercept of L against √h"), "unit": "m", "reference": "zero_intercept"}],
                    "hint": T("measure the range from the edge of the table"),
                    "frame_dt": 1 / 60, "stop": {"event": "landing", "after_s": 0.2, "max_world_s": 3.0},
                    "quantize": {"traj.s": "u16"}}],
         "worksheet": {"frp": [{"system": "FRP-OOO-2025-base", "grade": 7,
                                "programme": T("A programme for the tests of the site"),
                                "name": T("Testing the hypothesis: the higher the launch, the farther the ball flies")}],
                       "variants": [{"id": "grade7", "grade": 7, "label": T("Grade 7: the range against the height"),
                                     "steps": ["heights"], "plot": {"heights": {"x": "h", "y": "L", "fit": None}},
                                     "questions": [{"q": T("Does the range grow with the height?"),
                                                    "answer": T("Yes, but more slowly than the height.")}]}],
                       "equipment": [T("a chute"), T("a steel ball"), T("a ruler"), T("a measuring tape")],
                       "questions": [{"q": T("Why does the range grow more slowly than the height?"),
                                      "answer": T("The time of the fall grows as the square root of the height.")}],
                       "teacher": [T("The chute's speed is not told to the students: they find it from the slope.")]}},
    ],
}
