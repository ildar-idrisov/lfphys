# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Run a simulation without the server: collect every message it emits (decoded), drive it by commands."""
from __future__ import annotations

import queue

from lfviz import protocol, registry
from lfviz.i18n import join
from lfviz.sim import Runner


class Harness:
    def __init__(self, viz_id: str, preset: str | None = None, params: dict | None = None, seed: int = 1):
        viz = registry.load(viz_id)
        self.params, errors = viz["schema"].resolve(preset, params)
        assert not errors, errors
        self.msgs = []
        sim = viz["simulation"](self.params, seed, self.emit)
        self.q: queue.Queue = queue.Queue()

        def make_world(pr, values, sd):
            p, errs = viz["schema"].resolve(pr, values or {})
            if errs:
                raise ValueError(join(errs, "; "))
            return viz["simulation"](p, seed if sd is None else int(sd), self.emit), {"preset": pr}

        self.runner = Runner(sim, self.emit, self.q, make_world=make_world, world_info={"preset": preset})
        self.runner._start_world()

    @property
    def sim(self):
        """The simulation of the current world (a new_world command replaces it)."""
        return self.runner.sim

    def emit(self, meta, blobs=None):
        # round trip through the wire format, as the browser would see it
        m, b = protocol.decode(protocol.encode(meta, blobs))
        self.msgs.append((m, b))

    def cmd(self, cmd, **args):
        self.runner.handle({"cmd": cmd, "args": args})

    def action(self, name, **args):
        self.runner.handle({"cmd": "action", "args": {"name": name, "args": args}})

    def run_to(self, t):
        self.runner._advance(t)

    def set(self, **values):
        """Change live parameters, as the player does (command ``set``)."""
        self.runner.handle({"cmd": "set", "args": {"values": values}})

    def of(self, typ):
        return [m for m, _ in self.msgs if m.get("type") == typ]

    def checks(self):
        out = {}
        for m in self.of("check"):
            out[m["id"]] = m
        return out

    def errors(self):
        """The errors' texts (a T as the player gets it: {"$t", "a"}, or a plain string)."""
        return [m["text"] for m in self.of("error")]
