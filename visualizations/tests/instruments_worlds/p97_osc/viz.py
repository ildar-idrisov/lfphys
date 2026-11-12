# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A fixture playground for the instruments' tests (plan P16.3; found only through ``LFVIZ_EXTRA``, never in the
catalogue): harmonic oscillators x'' = -(k/m) x advanced by the exact rotation of their phase plane, so that every
measured value has a closed form; a live law ``k`` (the spring constant, refused above 100 Н/м: a refusal inside the
world), a live law ``alloc_mb`` that holds that many MB (the memory budget's test), a random kick per object (the
sweeps' determinism: the generator's state travels in the checkpoint). Measurables: each oscillator's position and
energy (``of`` = its id), the total energy, and the first oscillator's position (undefined without one). With
``P97_MEASURE=1`` in the environment the world offers ``measure()`` (the sweeps then read it instead of ``frame()``);
with ``P97_MEASURE=tuple`` a ``measure()`` that breaks the contract (it returns ``(values, notes)``, as p02's did:
review LB1-p02-ux Q3).

Added for the processing of the LB1 reviews: a live law ``cost_ms`` (wall milliseconds of busy CPU per world second of
the advance, so that the cost estimate has a cost to measure: review LB1-framework F4; what the world computes does not
depend on it), and a type ``ball``: a two-dimensional isotropic oscillator x'' = -(k/m) x, y'' = -(k/m) y with the
handles position (x, y) and velocity (vx, vy), reported in every frame's ``at`` (an object-parameter sweep of a handle
goes through the scene's ``edit``: review F1); for the sweep form's labels (review LB1-p02-ux X9) the label of
``alloc_mb`` names its unit, and a live law ``damp`` (inert) is shown only in the world mode ``kmode = damped``."""

from __future__ import annotations

import math
import os
import time

import numpy as np

from lfviz.errors import Refusal
from lfviz.i18n import T
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, PlaygroundSimulation, scene_param

M, MS, KG = T("m"), T("m/s"), T("kg")
OSC = Schema([Param("x", "x", "float", 1.0, unit=M), Param("v", "v", "float", 0.0, unit=MS),
              Param("m", T("mass"), "float", 1.0, unit=KG, min=1e-6), Param("kick", T("kick"), "float", 0.0, min=0.0)])
BALL = Schema([Param("x", "x", "float", 1.0, unit=M), Param("y", "y", "float", 0.0, unit=M),
               Param("vx", "vx", "float", 0.0, unit=MS), Param("vy", "vy", "float", 0.0, unit=MS),
               Param("m", T("mass"), "float", 1.0, unit=KG, min=1e-6),
               Param("glow", T("glow"), "bool", False)])
SCHEMA = Schema([Param("k", T("Spring stiffness"), "float", 4.0, unit=T("N/m"), min=1e-6, max=1e4, live=True),
                 Param("alloc_mb", T("Hold memory, MB"), "int", 0, unit=T("MB"), min=0, max=100000, live=True),
                 Param("cost_ms", T("Cost of computing"), "float", 0.0, unit=T("ms per 1 s of the world"), min=0.0, max=1e6,
                       live=True),
                 Param("kmode", T("Mode"), "select", "plain", options=[("plain", T("undamped")), ("damped", T("damped"))]),
                 Param("damp", T("Damping"), "float", 0.0, unit=T("1/s"), min=0.0, live=True, show_if={"kmode": ["damped"]}),
                 scene_param()], presets={
    "one": {"label": T("One oscillator"), "params": {"scene": {"format": "lfscene", "version": 1, "objects": [
        {"type": "osc", "values": {"x": 1.0, "v": 0.0, "m": 1.0}}]}}},
    "two": {"label": T("Two oscillators, one with kicks"), "params": {"scene": {"format": "lfscene", "version": 1,
                                                                               "objects": [
        {"type": "osc", "values": {"x": 1.0, "v": 0.5, "m": 2.0, "kick": 0.3}},
        {"type": "osc", "values": {"x": -0.5, "v": 0.0, "m": 1.0}}]}}},
    "empty": {"label": T("An empty scene"), "params": {}},
    "ball": {"label": T("An oscillator and a ball on a plane"), "params": {"scene": {"format": "lfscene", "version": 1,
                                                                             "objects": [
        {"type": "osc", "values": {"x": 1.0, "v": 0.0, "m": 1.0}},
        {"type": "ball", "values": {"x": 1.0, "y": 0.5, "vx": 0.0, "vy": 0.3, "m": 1.0}}]}}},
})


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p97_osc"
    PALETTE = {"osc": ObjectType("osc", T("Oscillator"), "body", OSC, color="#1c7ed6"),
               "ball": ObjectType("ball", T("Ball"), "body", BALL, color="#e8590c",
                                  handles={"position": ["x", "y"], "velocity": ["vx", "vy"]})}
    default_speed = 1.0
    speed_range = (0.01, 100.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.k = float(params["k"])
        self.alloc_mb = int(params["alloc_mb"])
        self.cost_ms = float(params["cost_ms"])
        self.damp = float(params["damp"])  # inert: only the forms' show_if is tested with it
        self.held = None
        self.xv = {}  # id -> np.array([x, v])
        self.balls = {}  # id -> np.array([x, y, vx, vy])
        self.start_scene()

    # --- the scene ---
    def on_add(self, obj, state):
        v = obj["values"]
        if obj["type"] == "ball":
            self.balls[obj["id"]] = np.array(state["s"] if state else [v["x"], v["y"], v["vx"], v["vy"]], float)
            return
        self.xv[obj["id"]] = np.array(state["xv"] if state else [v["x"], v["v"]], float)

    def on_remove(self, obj):
        self.xv.pop(obj["id"], None)
        self.balls.pop(obj["id"], None)

    def on_set(self, obj, old):
        # a parameter whose ``old`` is None (an edit) or unequal (a change, or a sweep applying the stored value again)
        # is applied; never arithmetic on ``old`` (the LB1 edit semantics)
        v = obj["values"]
        if obj["type"] == "ball":
            s = self.balls[obj["id"]]
            for i, key in enumerate(("x", "y", "vx", "vy")):
                if v[key] != old.get(key):
                    s[i] = v[key]
            return
        s = self.xv[obj["id"]]
        if v["x"] != old.get("x"):
            s[0] = v["x"]
        if v["v"] != old.get("v"):
            s[1] = v["v"]

    def object_state(self, obj):
        if obj["type"] == "ball":
            s = self.balls.get(obj["id"])
            return None if s is None else {"s": s.tolist()}
        s = self.xv.get(obj["id"])
        return None if s is None else {"xv": s.tolist()}

    # --- live laws ---
    def live_values(self):
        return {"k": self.k, "alloc_mb": self.alloc_mb, "cost_ms": self.cost_ms, "damp": self.damp}

    def set_live(self, values):
        k = float(values.get("k", self.k))
        if k > 100.0:
            raise Refusal(T("a spring stiffer than 100 N/m ({k:g} N/m) is not computed in this world", k=k),
                          T("take k at most 100 N/m"))
        mb = int(values.get("alloc_mb", self.alloc_mb))
        if mb != self.alloc_mb:
            self.held = np.ones(mb * 2 ** 17) if mb else None  # 8 bytes each: mb MB, held by the world
        self.k, self.alloc_mb = k, mb
        self.cost_ms = float(values.get("cost_ms", self.cost_ms))
        self.damp = float(values.get("damp", self.damp))
        return T("k = {k:g} N/m", k=k)

    # --- physics ---
    def advance(self, t_target):
        dt = t_target - self.t
        if dt <= 0:
            return
        for oid, s in self.xv.items():
            vals = self.objects[oid]["values"]
            w = math.sqrt(self.k / vals["m"])
            c, sn = math.cos(w * dt), math.sin(w * dt)
            x, v = s
            s[0], s[1] = x * c + v / w * sn, -x * w * sn + v * c
            if vals["kick"]:
                s[1] += vals["kick"] * self.rng.normal() * math.sqrt(dt)
        for oid, s in self.balls.items():
            w = math.sqrt(self.k / self.objects[oid]["values"]["m"])
            c, sn = math.cos(w * dt), math.sin(w * dt)
            for i in (0, 1):
                x, v = s[i], s[2 + i]
                s[i], s[2 + i] = x * c + v / w * sn, -x * w * sn + v * c
        if self.cost_ms:  # busy CPU, proportional to the world time advanced (the estimate's test: F4)
            end = time.perf_counter() + self.cost_ms * dt / 1e3
            while time.perf_counter() < end:
                pass
        self.t = t_target

    def max_step(self):
        return 0.05

    # --- instruments ---
    def measurables(self):
        J, world = T("J"), T("World")
        out = [{"id": "E", "label": T("Total energy"), "unit": J, "of": None, "group": world},
               {"id": "x_first", "label": T("Position of the first oscillator"), "unit": M, "of": None, "group": world}]
        for oid in self.xv:
            out.append({"id": f"{oid}.x", "label": T("position"), "unit": M, "of": oid, "group": T("Oscillators")})
            out.append({"id": f"{oid}.E", "label": T("energy"), "unit": J, "of": oid, "group": T("Oscillators")})
        for oid in self.balls:
            out.append({"id": f"{oid}.x", "label": "x", "unit": M, "of": oid, "group": T("Balls")})
            out.append({"id": f"{oid}.y", "label": "y", "unit": M, "of": oid, "group": T("Balls")})
        return out

    def scene_meta(self):  # the framework sends measurables() in the scene message (API §2); kept here for older ones
        meta = super().scene_meta()
        meta.setdefault("measurables", self.measurables())
        return meta

    def _meas(self):
        meas, note = {}, {}
        tot = 0.0
        for oid, (x, v) in self.xv.items():
            m = self.objects[oid]["values"]["m"]
            e = 0.5 * m * v * v + 0.5 * self.k * x * x
            meas[f"{oid}.x"], meas[f"{oid}.E"] = float(x), float(e)
            tot += e
        for oid, (x, y, vx, vy) in self.balls.items():
            m = self.objects[oid]["values"]["m"]
            meas[f"{oid}.x"], meas[f"{oid}.y"] = float(x), float(y)
            tot += 0.5 * m * (vx * vx + vy * vy) + 0.5 * self.k * (x * x + y * y)
        meas["E"] = tot
        if self.xv:
            meas["x_first"] = float(next(iter(self.xv.values()))[0])
        else:
            meas["x_first"] = None
            note["x_first"] = T("there are no oscillators in the scene")
        return meas, note

    def frame(self):
        meas, note = self._meas()
        ids = list(self.xv)
        pos = np.array([self.xv[i] for i in ids], float).reshape(-1, 2)
        at = {oid: [float(s[0]), float(s[1]), 0.0] for oid, s in self.balls.items()}  # the handles' objects (API §1)
        return {"ids": ids, "meas": meas, **({"meas_note": note} if note else {}), **({"at": at} if at else {})}, \
            {"pos": pos.astype(np.float32)}

    def header(self):
        return {"title": T("Oscillators (tests of the instruments)"), "actions": [], "playground": self.playground_header(),
                "modifications": SCHEMA.modifications(self.params), "units": {"t": T("s")}}, {}


if os.environ.get("P97_MEASURE") == "1":
    Simulation.measure = lambda self: self._meas()[0]
elif os.environ.get("P97_MEASURE") == "tuple":  # breaks the contract (a dict): the sweep must say so (LB1-p02-ux Q3)
    Simulation.measure = lambda self: self._meas()


VIZ = {"id": "p97_osc", "title": T("Oscillators (tests of the instruments)"), "summary": "", "purpose": "", "version": "1.0",
       "schema": SCHEMA, "simulation": Simulation, "kind": "playground", "section": "toy"}
