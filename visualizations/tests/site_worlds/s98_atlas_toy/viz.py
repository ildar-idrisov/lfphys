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
≤ 0 (no flight), so that an atlas has a refused point. Its screens: Watch (the recording ``story`` with captions, a
``speed`` change and a new world in its script), Explore (h × angle, 2 × 3 points, one refused), a second Explore
``throws`` and Lab work (step 1: five heights off a chute, with two laws: the slope of L against √h, and the intercept
of the line through the same points, zero; their references from ``lab_reference``; step 2: the timer's ticks).

EX2 (design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §5, §7): a timer ticks every 0.1 s of the flight (an
event of kind ``tick`` and the counted measurable ``n_ticks``); ``range`` declares its reference ``range_ref`` (the
closed form) and ``v_mean`` (the mean speed of the path's samples so far) its run's own standard error ``v_mean_se``;
the screen ``throws`` has a compound control (``throw``: the speed and the angle together), frames per played second
at half speed (``fps``, ``speed``), a stop by counted events (six ticks or the landing) and ``drop.blobs``; the lab's
step ``ticks`` has a counter (√N), a readout with the run's σ, formula columns (one of them undefined at the first
height, with its reason) and a stop by counted events. ``g`` is an attribute (``u96_lab_toy`` changes it, a law
parameter)."""

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

TICK = 0.1  # the timer's period, world seconds

MEASURABLES = [{"id": "range", "label": T("Range"), "unit": "m", "ref": "range_ref", "ref_label": T("formula")},
               {"id": "flight_time", "label": T("Flight time"), "unit": "s"},
               {"id": "apex_h", "label": T("Apex height"), "unit": "m"},
               {"id": "range_ref", "label": T("Range by the formula"), "unit": "m"},
               {"id": "v_mean", "label": T("Mean speed"), "unit": "m/s", "sigma": "v_mean_se"},
               {"id": "v_mean_se", "label": T("Standard error of the mean speed"), "unit": "m/s"},
               {"id": "n_ticks", "label": T("Timer ticks"), "unit": ""}]


class Simulation(Base):
    default_speed = 1.0
    speed_range = (0.01, 10.0)

    g = G  # the field's strength (a subclass may change it: u96_lab_toy's law parameter)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.g = self.field(params)
        G = self.g  # noqa: N806 - the formulas below read the field as the module's constant does
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
        self.ticks = 0  # the timer's ticks during the flight (EX2: a counted measurable and a stop by counted events)
        self.speeds = []  # the speeds of the path's samples sent so far (v_mean and its standard error)

    @classmethod
    def field(cls, params) -> float:
        """The field's strength for these parameters (m/s²)."""
        return G

    @classmethod
    def check_params(cls, params):
        if float(params["h_m"]) <= 0.0 and float(params["angle_deg"]) <= 0.0:
            raise Refusal(T("The ball starts on the ground moving along it or into it: no flight"),
                          T("raise the height or the angle"))

    @classmethod
    def lab_reference(cls, step_id, fixed, values, reference):
        """The laws of a lab step (design §2.3, integrator D4): ``heights``: L = k·√h with k = v₀·√(2/g) (a horizontal
        throw; ``k_horizontal``), so the line through the points has no intercept (``zero_intercept``)."""
        g = cls.field(fixed)
        if step_id == "heights" and reference == "k_horizontal":
            v0 = float(fixed["v0"])
            return {"value": v0 * math.sqrt(2.0 / g), "unit": "m^½", "label": T("k = v₀·√(2/g)"),
                    "how": T("closed form of a horizontal throw without air"), "kind": "closed form"}
        if step_id == "ticks" and reference == "fall_coefficient":
            return {"value": math.sqrt(2.0 / g), "unit": T("s/m^½"), "label": T("T = √(2/g)·√h"),
                    "how": T("closed form of a fall from rest without air"), "kind": "closed form"}
        if step_id == "heights" and reference == "zero_intercept":
            return {"value": 0.0, "unit": "m", "label": T("no intercept: L = k·√h"),
                    "how": T("closed form of a horizontal throw without air"), "kind": "closed form"}
        raise ValueError(T("no law for the step {step}", step=step_id))

    def pos(self, t):
        t = min(t, self.T)
        return self.vx * t, self.h + self.vy * t - 0.5 * self.g * t * t

    def vel(self, t):
        if t >= self.T:
            return 0.0, 0.0
        return self.vx, self.vy - self.g * t

    def header(self):
        L = self.vx * self.T
        H = self.h + (self.vy ** 2 / (2 * self.g) if self.vy > 0 else 0.0)
        return {"title": T("A thrown ball for the tests of the atlases"),
                "scene": {"box": [[-0.2, -0.05], [max(1.0, L * 1.1), max(1.0, H * 1.15)]]},
                "launcher": {"h": self.h, "angle": float(self.params["angle_deg"]), "v0": self.v0},
                "companion": self.params.get("companion"), "measurables": MEASURABLES,
                "units": {"t": T("s"), "x": T("m")}, "actions": []}, \
            {"ticks": np.linspace(0.0, 5.0, 51), "aim": self.aim()}

    def aim(self):
        """The launcher's aim line (64 points along the launch direction): the same for every point of an atlas with the
        same angle, so an atlas's pool stores it once (EX2 §5 F10)."""
        a = math.radians(float(self.params["angle_deg"]))
        r = np.linspace(0.0, 0.3, 64)
        return np.column_stack([r * math.cos(a), r * math.sin(a)]).ravel()

    def _samples(self, t_target):
        rows = []
        while self.next_sample < 10 ** 9:
            ts = min(self.next_sample * DT, self.T)
            if ts > t_target + 1e-12:
                break
            x, y = self.pos(ts)
            vx, vy = self.vel(ts) if ts < self.T else (self.vx, self.vy - self.g * self.T)
            rows.append((ts, x, y, vx, vy))
            self.speeds.append(math.hypot(vx, vy))
            self.next_sample += 1
            if ts >= self.T:
                self.next_sample = 10 ** 9  # the last sample is the landing itself
                break
        if rows:
            self.emit({"type": "traj", "t": t_target, "n": len(rows)}, {"s": np.array(rows, dtype=np.float64)})

    def advance(self, t_target):
        while (self.ticks + 1) * TICK < self.T and (self.ticks + 1) * TICK <= t_target + 1e-12:  # the timer, in flight
            self.ticks += 1
            self.emit({"type": "event", "kind": "tick", "t": self.ticks * TICK, "text": T("a tick of the timer"),
                       "data": {"n": self.ticks}})
        if not self.apexed and self.T_apex <= t_target:
            self.apexed = True
            self.emit({"type": "event", "kind": "apex", "t": self.T_apex, "text": T("apex"),
                       "data": {"H": self.pos(self.T_apex)[1]}})
        self._samples(t_target)
        if not self.landed and self.T <= t_target:
            self.landed = True
            L = self.vx * self.T
            vy = self.vy - self.g * self.T
            self.emit({"type": "event", "kind": "landing", "t": self.T, "text": T("landing"),
                       "data": {"T": self.T, "L": L, "v": math.hypot(self.vx, vy)}})
            self.emit({"type": "story", "t": self.T, "text": T("the ball has landed")})
            lo, hi = 0.0, self.T * 2 + 1.0  # the second method: bisection of y(t) = 0 on the path's own formula
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if self.h + self.vy * mid - 0.5 * self.g * mid * mid > 0:
                    lo = mid
                else:
                    hi = mid
            t_bis = 0.5 * (lo + hi)
            self.emit({"type": "check", "t": self.T, "id": "landing_time", "label": T("landing time"),
                       "value": t_bis, "ref": self.T, "unit": "s", "rel": (t_bis - self.T) / self.T, "tol": 1e-12,
                       "group": "", "note": T("bisection of y(t) = 0 against the quadratic formula")})
            e0 = 0.5 * self.v0 ** 2 + self.g * self.h
            e1 = 0.5 * (self.vx ** 2 + vy ** 2)
            self.emit({"type": "check", "t": self.T, "id": "energy", "label": T("energy at the landing"),
                       "value": e1, "ref": e0, "unit": "J/kg", "rel": (e1 - e0) / e0, "tol": 1e-12, "group": "",
                       "note": T("per unit mass, against the start")})
        self.t = t_target

    def frame(self):
        x, y = self.pos(self.t)
        vx, vy = self.vel(self.t)
        n = len(self.speeds)
        mean = sum(self.speeds) / n if n else None
        se = (math.sqrt(sum((v - mean) ** 2 for v in self.speeds) / (n - 1)) / math.sqrt(n)) if n >= 2 else None
        meas = {"x": x, "y": y, "v": math.hypot(vx, vy),
                "range": self.vx * self.T if self.landed else None,
                "flight_time": self.T if self.landed else None,
                "apex_h": (self.pos(self.T_apex)[1] if self.T_apex is not None else self.h) if self.apexed else None,
                "range_ref": self.vx * self.T, "v_mean": mean, "v_mean_se": se if se else None,
                "n_ticks": self.ticks}
        meta = {"x": x, "y": y, "landed": self.landed, "meas": meas}
        if self.drop:
            meta["drop_y"] = max(0.0, self.h - 0.5 * self.g * self.t * self.t)
        return meta, {"ghost": np.full(16, x, dtype=np.float32)}

    def next_event_time(self):
        tick = (self.ticks + 1) * TICK if (self.ticks + 1) * TICK < self.T else None
        nxt = self.T_apex if not self.apexed else (None if self.landed else self.T)
        return min(x for x in (tick, nxt) if x is not None) if (tick, nxt) != (None, None) else None

    def max_step(self):
        return 0.05


_STEP_COLS = [{"id": "h", "label": T("h, m"), "from": "ruler"},
              {"id": "L", "label": T("L, m"), "from": "tape"},
              {"id": "sqrt_h", "label": T("√h, m^½"), "of": "h", "op": "sqrt"}]
# the step "ticks" (EX2 §5 F4, F5): a counter, a readout with the run's own σ, formula columns (one undefined at the
# first height: √ of a negative number)
_TICK_COLS = [{"id": "h", "label": T("h, m"), "from": "ruler"},
              {"id": "n", "label": T("n, ticks"), "from": "ticks"},
              {"id": "v", "label": T("v, m/s"), "from": "speedo"},
              {"id": "sqrt_h", "label": T("√h, m^½"), "expr": "sqrt(h)"},
              {"id": "T", "label": T("T = 0.1·n, s"), "expr": "0.1 * n"},
              {"id": "d", "label": T("√(n − 2.5)"), "expr": "sqrt(n - 2.5)"}]

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
         "overlays": ["path", "strobe", "v"], "traces": 3, "readouts": ["range", "flight_time", "apex_h", "v_mean"]},
        # EX2 §5 F1–F3, F8: a compound control, frames per played second at half speed, counted events, drop.blobs
        {"id": "throws", "kind": "explore", "label": T("Throws"), "preset": "field", "fixed": {},
         "controls": [{"id": "throw", "label": T("Throw"), "values": ["flat", "lob", "steep"],
                       "labels": [T("flat, 2 m/s"), T("a lob, 3 m/s at 30°"), T("steep, 2.5 m/s at 60°")],
                       "sets": {"v0": [2.0, 3.0, 2.5], "angle_deg": [0.0, 30.0, 60.0]}, "default": "lob"},
                      {"param": "h_m", "values": [0.5, 1.0], "default": 1.0}],
         "acts": "next", "time": "flight", "fps": 20, "speed": 0.5,
         "stop": {"events": {"tick": 6, "landing": 1}, "after_s": 0.1, "max_world_s": 5.0},
         "drop": {"types": ["story"], "blobs": ["frame.ghost", "header.tick*"]},
         "quantize": {"traj.s": "u16"}, "overlays": ["path", "v"], "traces": 2,
         "readouts": ["range", "v_mean", "n_ticks"]},
        {"id": "lab", "kind": "lab",
         "instruments": {
             "tape": {"kind": "ruler", "label": T("Measuring tape"), "unit": "m", "division": 0.001, "error": 0.0005,
                      "reads": "range"},
             "ruler": {"kind": "ruler", "label": T("Ruler"), "unit": "m", "division": 0.01, "error": 0.005,
                       "reads": "control:h_m"},
             "stopwatch": {"kind": "stopwatch", "label": T("Stopwatch"), "unit": "s", "division": 0.01, "error": 0.2,
                           "manual": True, "error_note": T("your reaction time, about 0.2 s")},
             "ticks": {"kind": "counter", "label": T("Tick counter"), "unit": "", "error": "poisson",
                       "reads": "n_ticks"},
             "speedo": {"kind": "readout", "label": T("Speedometer"), "unit": "m/s", "division": 0.001,
                        "sigma": "v_mean_se", "reads": "v_mean"}},
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
                    "quantize": {"traj.s": "u16"}},
                   {"id": "ticks", "title": T("The timer's ticks"),
                    "goal": T("Count the timer's ticks during the fall and find how the fall time depends on the height"),
                    "preset": "chute", "controls": [{"param": "h_m", "values": [0.2, 0.45, 0.8, 1.25], "default": 0.45}],
                    "fixed": {"v0": 0.0}, "instruments": ["ruler", "ticks", "speedo"], "columns": _TICK_COLS,
                    "plot": {"x": "sqrt_h", "y": "T", "fit": "line0", "fits": ["line0", "line"]},
                    "laws": [{"x": "sqrt_h", "y": "T", "model": "line0", "quantity": "slope", "label": T("T / √h"),
                              "unit": T("s/m^½"), "reference": "fall_coefficient"}],
                    "frame_dt": 1 / 60, "stop": {"events": {"landing": 1}, "after_s": 0.05, "max_world_s": 3.0},
                    "drop": {"blobs": ["frame.ghost"]}, "quantize": {"traj.s": "u16"}}],
         # the task sheet (EX2 §5 F8): no questions, answers or teacher's pages; the teacher's variant preselects
         "worksheet": {"frp": [{"system": "FRP-OOO-2025-base", "grade": 7,
                                "programme": T("A programme for the tests of the site"),
                                "name": T("Testing the hypothesis: the higher the launch, the farther the ball flies")}],
                       "goal": T("Find how the range and the fall time of a ball depend on the height of its launch"),
                       "bench": [T("A ball leaves a chute horizontally at 1.5 m/s from a stand 0.2–1.0 m high; a ruler "
                                   "on the stand, a measuring tape on the floor, a hand stopwatch."),
                                 T("In part 2 the ball falls from rest; a timer ticks every 0.1 s of the fall, with a "
                                   "tick counter and a speedometer.")],
                       "procedure": [T("Part 1: for each height launch the ball, read the range on the tape and plot "
                                       "the range against the square root of the height."),
                                     T("Part 2: count the ticks during the fall at each height and plot T = 0.1·n "
                                       "against the square root of the height.")],
                       "record": [T("the table of your readings with their errors"),
                                  T("each fit: the model, the points used, the parameters with their errors")],
                       "record_rows": 8,
                       "variants": [{"id": "grade7", "grade": 7, "label": T("Grade 7: the range against the height"),
                                     "steps": ["heights"], "values": {"heights": {"h_m": 1.0}},
                                     "text": {"goal": T("Does the range grow with the height?"),
                                              "procedure": [T("Plot the range against the height, without a line.")]}}]}},
    ],
}
