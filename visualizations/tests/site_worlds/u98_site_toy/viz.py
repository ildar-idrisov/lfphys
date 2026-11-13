# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A tiny demonstration for the tests of the site's recorder and build (``tests/test_recorder.py``,
``tests/test_site_build.py``; found only through ``LFVIZ_EXTRA``, never in the catalogue): a point moving at a speed
``v`` along x. Every frame carries its position (``x``) and an array (``pos``); every 0.5 s of world time the world emits
an accumulative ``tick`` event; the action ``kick`` doubles the speed and says so in an event; ``v`` is live. The
frames' array has a size ``n`` (a parameter: a random array when it is above 4)."""

from __future__ import annotations

import numpy as np

from lfviz.i18n import T
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as Base

SCHEMA = Schema([Param("v", T("Speed"), "float", 1.0, unit=T("m/s"), min=0.0, max=100.0, live=True),
                 Param("n", T("Size of the frame's array"), "int", 4, min=1, max=10_000_000)],
                presets={"slow": {"label": T("A slow point"), "params": {"v": 1.0}},
                         "fast": {"label": T("A fast point"), "params": {"v": 5.0}}})


class Simulation(Base):
    default_speed = 1.0
    speed_range = (0.01, 100.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.v = float(params["v"])
        self.n = int(params["n"])
        self.x = 0.0
        self.next_tick = 0.5

    def header(self):
        return {"title": T("A point for the tests of the site"), "actions": [{"name": "kick", "label": T("Kick")}],
                "units": {"t": T("s")}, "checks": []}, {}

    def advance(self, t_target):
        while self.next_tick <= t_target:
            self.x += self.v * (self.next_tick - self.t)
            self.t = self.next_tick
            self.emit({"type": "event", "kind": "tick", "t": self.t, "text": T("tick")})
            self.next_tick += 0.5
        self.x += self.v * (t_target - self.t)
        self.t = t_target

    def frame(self):
        arr = self.rng.random(self.n).astype(np.float32) if self.n > 4 else np.full(self.n, self.x, np.float32)
        return {"x": self.x, "v": self.v}, {"pos": arr}

    def action(self, name, args):
        if name != "kick":
            raise ValueError(T("unknown action {name}", name=name))
        self.v *= 2.0
        return T("kicked: v = {v:g} m/s", v=self.v)

    def live_values(self):
        return {"v": self.v}

    def set_live(self, values):
        self.v = float(values.get("v", self.v))
        return T("v = {v:g} m/s", v=self.v)

    def max_step(self):
        return 0.1


VIZ = {"id": "u98_site_toy", "title": T("A point for the tests of the site"), "summary": "", "purpose": "",
       "version": "1.0", "schema": SCHEMA, "simulation": Simulation, "audience": "university", "section": "mechanics",
       "teaser": T("A point moves; ticks every half second."), "related": ["r98_site_probe"],
       "courses": [{"text": T("A book for the tests of the site"), "chapters": "1"}],
       "recordings": [
           {"id": "slow", "preset": "slow", "seconds": 3, "fps": 10, "speed": None, "seed": 1, "poster": 2,
            "script": [{"at": 1.0, "cmd": "action", "args": {"name": "kick", "args": {}}},
                       {"at": 2.0, "cmd": "set", "args": {"values": {"v": 0.5}}}]},
           {"id": "fast", "preset": "fast", "seconds": 2, "fps": 5, "speed": 2.0, "seed": 1, "poster": 0, "script": []},
       ]}
