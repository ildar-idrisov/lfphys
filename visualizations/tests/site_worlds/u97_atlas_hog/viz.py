# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A world that misbehaves on purpose, for the tests of the server's live points (``tests/test_atlas_live.py``; found
only through ``LFVIZ_EXTRA``): its point runs as the toy ball of ``s98_atlas_toy`` (``mode: none``), or allocates far
more memory than a live point is given (``mem``), or computes forever (``cpu``). Its atlas is never built: the live
point's process must end on its memory and time limits, never the server."""

from __future__ import annotations

import numpy as np

from lfviz.i18n import T
from lfviz.params import Param, Schema
from s98_atlas_toy.viz import SCHEMA as TOY, Simulation as Toy

SCHEMA = Schema(list(TOY.params) + [Param("mode", T("Mode"), "select", "none",
                                          options=[("none", T("none")), ("mem", "mem"), ("cpu", "cpu")])],
                presets={"field": TOY.presets["field"]})


class Simulation(Toy):
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


VIZ = {"id": "u97_atlas_hog", "title": T("A thrown ball for the tests of the atlases"), "summary": "", "purpose": "",
       "version": "1.0", "schema": SCHEMA, "simulation": Simulation, "audience": "university", "section": "mechanics",
       "teaser": T("A ball is thrown; where does it land?"), "related": [],
       "courses": [{"text": T("A book for the tests of the site"), "chapters": "1"}],
       "recordings": [{"id": "only", "preset": "field", "seconds": 1, "fps": 10, "speed": None, "seed": 1,
                       "poster": 0, "script": []}],
       "screens": [{"id": "explore", "kind": "explore", "preset": "field", "fixed": {},
                    "controls": [{"param": "h_m", "values": [0.5, 1.0], "default": 1.0},
                                 {"param": "mode", "values": ["none", "mem", "cpu"], "default": "none"}],
                    "acts": "now", "time": "none", "frame_dt": 0.05,
                    "stop": {"event": "landing", "after_s": 0.0, "max_world_s": 5.0}}]}
