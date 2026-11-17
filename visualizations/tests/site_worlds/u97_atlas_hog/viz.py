# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A world that misbehaves on purpose, for the tests of the server's live points and the atlases
(``tests/test_atlas_live.py``, ``tests/test_atlas.py``; found only through ``LFVIZ_EXTRA``): its point runs as the toy
ball of ``s98_atlas_toy`` (``mode: none``), or allocates far more memory than a live point is given (``mem``), or
computes forever (``cpu``), or refuses in its constructor as u32 refuses d ≤ a (``refuse``: a refused point, not a
failure; integrator D14), or ends with a check ✗ (``fail``). Its Explore atlas is never built: the live point's process
must end on its memory and time limits, never the server. Its ``faults`` atlas (``none`` and ``refuse``) is built by the
tests: the constructor's refusals are refused points."""

from __future__ import annotations

import numpy as np

from lfviz.errors import Refusal
from lfviz.i18n import T
from lfviz.params import Param, Schema
from s98_atlas_toy.viz import SCHEMA as TOY, Simulation as Toy

SCHEMA = Schema(list(TOY.params) + [Param("mode", T("Mode"), "select", "none",
                                          options=[("none", T("none")), ("mem", "mem"), ("cpu", "cpu"),
                                                   ("refuse", "refuse"), ("fail", "fail")])],
                presets={"field": TOY.presets["field"]})


class Simulation(Toy):
    def __init__(self, params, seed, emit):
        if params.get("mode") == "refuse":  # a refusal of the world's constructor (u32: d ≤ a)
            raise Refusal(T("This test world refuses the mode “refuse” while it is built"), T("choose another mode"))
        super().__init__(params, seed, emit)
        self.failed_check = False

    def advance(self, t_target):
        mode = self.params.get("mode")
        if mode == "mem" and t_target > 0:
            hog = []
            while True:  # beyond any budget: the process's RLIMIT_DATA ends it with a MemoryError
                hog.append(np.ones(2 ** 27))
        if mode == "cpu" and t_target > 0:
            x = 0
            while True:  # forever: the process's RLIMIT_CPU ends it
                x += 1
        super().advance(t_target)
        if mode == "fail" and self.landed and not self.failed_check:
            self.failed_check = True
            self.emit({"type": "check", "t": self.t, "id": "always_wrong", "label": T("a check that fails on purpose"),
                       "value": 1.0, "ref": 2.0, "unit": "", "rel": -0.5, "tol": 1e-12, "group": "",
                       "note": T("the test world's mode “fail”")})


VIZ = {"id": "u97_atlas_hog", "title": T("A thrown ball for the tests of the atlases"), "summary": "", "purpose": "",
       "version": "1.0", "schema": SCHEMA, "simulation": Simulation, "audience": "university", "section": "mechanics",
       "teaser": T("A ball is thrown; where does it land?"), "related": [],
       "courses": [{"text": T("A book for the tests of the site"), "chapters": "1"}],
       "recordings": [{"id": "only", "preset": "field", "seconds": 1, "fps": 10, "speed": None, "seed": 1,
                       "poster": 0, "script": []}],
       "screens": [{"id": "explore", "kind": "explore", "preset": "field", "fixed": {},
                    "controls": [{"param": "h_m", "values": [0.5, 1.0], "default": 1.0},
                                 {"param": "mode", "values": ["none", "mem", "cpu", "refuse", "fail"],
                                  "default": "none"}],
                    "acts": "now", "time": "none", "frame_dt": 0.05,
                    "stop": {"event": "landing", "after_s": 0.0, "max_world_s": 5.0}},
                   {"id": "faults", "kind": "explore", "preset": "field", "fixed": {},
                    "controls": [{"param": "h_m", "values": [0.5, 1.0], "default": 1.0},
                                 {"param": "mode", "values": ["none", "refuse"], "default": "none"}],
                    "acts": "now", "time": "none", "frame_dt": 0.05,
                    "stop": {"event": "landing", "after_s": 0.0, "max_world_s": 5.0}}]}
