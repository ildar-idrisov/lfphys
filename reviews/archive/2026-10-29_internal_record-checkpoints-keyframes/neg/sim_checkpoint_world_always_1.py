# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Base class of a simulation and the real-time runner.

A visualization subclasses ``Simulation``. The runner owns the transport (play, pause, speed, step, jump to the
next event) and the frame clock; the simulation owns the physics and the world state.

Message types a simulation emits (``self.emit(meta, blobs)``); every one carries the simulation time ``t``:

* ``header``  - first in every world: scene description, the actions it accepts, units, checks it will report;
  the runner adds ``world`` (1, 2, ...), ``params``, ``preset``, ``seed`` and ``live`` (current live values);
* ``live``    - the current values of the live parameters after a change (command ``set``) or a refused change;
* ``frame``   - the current state, ~``fps`` times per second while playing (droppable: a viewer that is slow
  may miss frames, never anything else);
* any other type (``event``, ``pulse``, ``detections``, ``segment``, ``check``, ...) - accumulative data, never
  dropped, recorded and replayed in order.

Causality rule for the implementation (RULES.md, section 2): a simulation may compute ahead internally, but it
reveals an event to the viewer only when the run's time has reached it, and it recomputes pending (future)
events when an action changes the world.

Restoring a world (owner, 2026-10-28: a run can always be continued): every command that changes the world (``set``,
``action``, ``view``, ``new_world``) is recorded as a ``command`` message with the world's time at which it was
applied. A world is rebuilt from its parameters and seed by repeating, in the order of its record, every advance of
the frame clock (each recorded frame's time) and every command (``Runner.restore``), with nothing emitted, and
continues from the end of its record. Repeating the same advances makes the rebuilt world the same even where its
random draws depend on how time was split into frames (the particle sources of v02, v05, v07); tested for every
visualization in ``tests/test_restore.py``.

Continuing from the last state (owner, 2026-10-29): the runner writes checkpoints of its world's whole state
(``lfviz.checkpoint``) when its run is suspended, when it pauses and every ``checkpoint.EVERY`` seconds of computation,
each recorded by a ``checkpoint`` message; a resume loads the last one and repeats only the record after it
(``Runner.restore_from``), so a long run is not recomputed. Tested for every visualization in
``tests/test_checkpoint.py``: the world continued from a checkpoint emits exactly what the original emits.
"""

from __future__ import annotations

import queue
import sys
import time
import traceback
from pathlib import Path
from typing import Callable

import numpy as np

Emit = Callable[..., None]


class Simulation:
    #: simulation seconds per wall second at start
    default_speed: float = 1.0
    #: speed limits for the slider (simulation seconds per wall second)
    speed_range: tuple[float, float] = (1e-12, 1e18)

    def __init__(self, params: dict, seed: int, emit: Emit):
        self.params = params
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.emit = emit
        self.t = 0.0

    # --- contract -------------------------------------------------------------------------------------
    def header(self) -> tuple[dict, dict]:
        raise NotImplementedError

    def advance(self, t_target: float) -> None:
        """Move the world to ``t_target`` and emit what happened on the way."""
        raise NotImplementedError

    def frame(self) -> tuple[dict, dict]:
        raise NotImplementedError

    def action(self, name: str, args: dict) -> str:
        """Apply an action at the current time; return a human-readable log line (Russian)."""
        raise ValueError(f"unknown action {name!r}")

    def engine_modules(self) -> list[str]:
        """The lfphys modules this world's physics comes from (ids like "core.relativity"), for the player's panel
        «Физика этого мира» (core vs theories outside the core)."""
        return []

    def live_values(self) -> dict:
        """Current values of the live parameters (``Param.live``) of this world."""
        return {}

    def view_state(self):
        """The view's state worth keeping in a new world of this run (e.g. the slice planes the experimenter placed);
        None by default."""
        return None

    def adopt_view(self, state) -> None:
        """Take over the view's state of the previous world (called before the new world's header)."""

    def view(self, args: dict) -> str:
        """A view request of the player that needs the engine (a slice plane in a 3-D scene, RULES.md §2.9): computes
        and emits what the view shows; never changes the world's physics. Returns a short text (or "")."""
        raise ValueError("у этого мира нет запросов просмотра")

    def set_live(self, values: dict) -> str:
        """Change live parameters at the current time (the experimenter rebuilds part of the set-up); return a log
        line. Must leave the world unchanged when it raises."""
        raise ValueError("в этом мире нечего менять на ходу")

    def next_event_time(self) -> float | None:
        return None

    def after_header(self) -> None:
        """Called right after the header is emitted (flush messages produced while constructing the world)."""

    def max_step(self) -> float | None:
        """Largest simulation-time step the world can take in one advance (None = unlimited)."""
        return None


def _engine_info(sim) -> list[dict]:
    """Catalogue entries (lfphys.registry) of the engine modules a world uses."""
    names = sim.engine_modules()
    if not names:
        return []
    try:
        from lfphys import registry
        return registry.describe(names)
    except Exception as e:  # the panel must never break a run
        return [{"id": "?", "layer": "?", "title": f"каталог движка недоступен: {e}"}]


MakeWorld = Callable[[str | None, dict | None, int | None], tuple[Simulation, dict]]


def _backend_info(notes=()) -> dict | None:
    """Devices and precisions of the engine's kernels in this run (plan P11): the settings in force and what each
    kernel called so far ran on (``lfphys.core.backend.used``)."""
    try:
        from lfphys.core import backend as B
    except Exception:  # the engine without the backend (an old record): nothing to report
        return None
    return {"settings": B.settings(), "used": B.used(), "notes": list(notes)}


CHECKPOINT_EVERY = 120.0  # seconds of wall time between checkpoints of a computing world (lfviz.checkpoint.EVERY)
RUNNER_FRAME_KEYS = {"type", "cpu_ms", "lag", "speed_actual"}  # set by the runner in every frame; a world must not use them


class Runner:
    """Transport and frame clock of one run. A run holds one or more worlds: ``new_world`` replaces the simulation
    by a new one (other laws or initial conditions) inside the same run and record; the previous worlds stay in the
    record. ``make_world(preset, values, seed) -> (sim, info)`` builds a world (raises ValueError on bad input)."""

    def __init__(self, sim: Simulation, emit: Emit, commands: "queue.Queue[dict]", fps: float = 20.0,
                 make_world: MakeWorld | None = None, world_info: dict | None = None):
        self.sim = sim
        self.emit = emit
        self.q = commands
        self.fps = fps
        self.make_world = make_world
        self.world = 1
        self.world_info = dict(world_info or {})
        self.backend_notes = list(self.world_info.pop("backend_notes", []))
        self.playing = False
        self.speed = float(sim.default_speed)
        self.stopped = False
        self.dirty = True
        self.lag = False
        self.rate_win = []  # (wall time, world time) while playing at one speed: the measured speed of the world
        self.adopted_view = None  # the view state this world took over from the previous one (slice planes)
        self.ckpt_dir: Path | None = None  # where checkpoints go (set by the worker; None: none are written)
        self.code = ""  # the code hash recorded with each checkpoint (a resume uses only those of the same code)
        self.ckpt_dirty = False  # the world changed since the last checkpoint (an advance, a frame, a command)
        self.ckpt_wall = time.monotonic()
        self.ckpt_failed = 0  # the world number whose checkpoint failed (not retried for that world)

    def _state(self, reason: str | None = None):
        meta = {"type": "state", "t": self.sim.t, "playing": self.playing, "speed": self.speed,
                "speed_range": list(self.sim.speed_range)}
        if reason:
            meta["reason"] = reason
        self.emit(meta)

    def _frame(self, cpu_ms: float):
        meta, blobs = self.sim.frame()
        meta = dict(meta)
        clash = RUNNER_FRAME_KEYS & set(meta)
        if clash:  # review B4-1: a key of the runner silently overwrote a world's own field
            raise ValueError(f"кадр мира содержит ключи плеера {sorted(clash)}: переименуйте их в frame() мира")
        self.ckpt_dirty = True  # a world's frame() may change its state (v10 counts frames between its images)
        meta["type"] = "frame"
        meta["t"] = self.sim.t
        meta["cpu_ms"] = round(cpu_ms, 2)
        meta["speed_actual"] = self.rate()  # not "rate": worlds use that key (v04: the body's dτ/dt)
        # the computation could not keep up: the advance stopped short in this frame, or (a single step longer than a
        # frame) the measured speed is below the chosen one (review B4-11)
        meta["lag"] = bool(self.lag or (self.playing and meta["speed_actual"] is not None
                                        and meta["speed_actual"] < 0.97 * self.speed))
        self.emit(meta, blobs)

    RATE_WINDOW = 1.5  # seconds of wall time over which the world's actual speed is measured

    def _rate_sample(self):
        now = time.monotonic()
        self.rate_win.append((now, self.sim.t))
        while len(self.rate_win) > 2 and now - self.rate_win[1][0] > self.RATE_WINDOW:
            self.rate_win.pop(0)

    def rate(self) -> float | None:
        """World seconds per wall second actually reached over the last RATE_WINDOW while playing (None until half
        of it has passed): below the chosen speed when the computation cannot keep up (``lag``)."""
        w = self.rate_win
        if len(w) < 2 or w[-1][0] - w[0][0] < 0.5 * self.RATE_WINDOW:
            return None
        return (w[-1][1] - w[0][1]) / (w[-1][0] - w[0][0])

    def _advance(self, target: float, budget: float | None = None):
        """Advance the world to ``target`` in steps of at most ``max_step``. With a wall-time ``budget`` the world
        stops early when the computation cannot keep up (the effective speed drops; reported as ``lag``)."""
        lim = self.sim.max_step()
        t0 = time.monotonic()
        self.lag = False
        self.ckpt_dirty = True
        while self.sim.t < target:
            nxt = target if lim is None else min(target, self.sim.t + lim)
            self.sim.advance(nxt)
            if budget is not None and self.sim.t < target and time.monotonic() - t0 > budget:
                self.lag = True
                break

    WORLD_COMMANDS = ("set", "action", "view", "new_world")  # recorded with their time: a restore replays them

    def handle(self, msg: dict):
        cmd = msg.get("cmd")
        args = msg.get("args") or {}
        if cmd in self.WORLD_COMMANDS:
            self.ckpt_dirty = True
            self.emit({"type": "command", "t": self.sim.t, "cmd": cmd, "args": args})
        if cmd == "play":
            self.playing = True
            self.rate_win = []
            self._state(args.get("reason"))
        elif cmd == "pause":
            self.playing = False
            self.rate_win = []
            self._state(args.get("reason"))
            if time.monotonic() - self.ckpt_wall > 10.0:  # cheap insurance against a crash while paused
                self.checkpoint("pause")
        elif cmd == "speed":
            lo, hi = self.sim.speed_range
            self.speed = float(min(max(float(args["value"]), lo), hi))
            self.rate_win = []
            self._state()
        elif cmd == "step":
            dt = float(args.get("dt", self.speed / self.fps))
            self._advance(self.sim.t + dt)
            self.dirty = True
            self._state("step")
        elif cmd == "next_event":
            te = self.sim.next_event_time()
            if te is None:
                self.emit({"type": "notice", "t": self.sim.t, "text": "Впереди нет запланированных событий"})
            else:
                if te <= self.sim.t:  # an event at the current instant (review v01 R21): reveal it in place
                    self.sim.advance(self.sim.t)
                else:
                    self._advance(te)
                self.dirty = True
                self._state("next_event")
        elif cmd == "action":
            name = args.get("name")
            try:
                text = self.sim.action(name, args.get("args") or {})
            except Exception as e:  # any failure is a refused change, reported; the world goes on
                self.emit({"type": "error", "t": self.sim.t, "text": f"Действие {name}: {e}"})
            else:
                self.emit({"type": "event", "kind": "action", "t": self.sim.t, "name": name,
                           "args": args.get("args") or {}, "text": text})
                self.dirty = True
        elif cmd == "set":  # live parameters: applied at once, at the current moment
            values = args.get("values") or {}
            try:
                text = self.sim.set_live(values)
            except Exception as e:  # any failure is a refused change, reported; the world goes on
                self.emit({"type": "error", "t": self.sim.t, "text": f"Изменение не применено: {e}"})
            else:
                self.emit({"type": "event", "kind": "action", "t": self.sim.t, "name": "set", "args": values,
                           "text": text})
                self.dirty = True
            # always report the values in force, so that a refused change is rolled back in the player
            # and the engine modules in force: a live change may bring a module in or out (a ghost orbit, a reading)
            self.emit({"type": "live", "t": self.sim.t, "values": self.sim.live_values(),
                       "engine": _engine_info(self.sim)})
        elif cmd == "view":  # a view request (e.g. a slice plane of a 3-D world): computed, recorded, no physics change
            try:
                text = self.sim.view(args)
            except Exception as e:  # noqa: BLE001 - a refused request is reported; the world goes on
                self.emit({"type": "error", "t": self.sim.t, "text": f"Просмотр: {e}"})
            else:
                if text:
                    self.emit({"type": "event", "kind": "view", "t": self.sim.t, "name": "view", "args": args,
                               "text": text})
                self.dirty = True
        elif cmd == "new_world":
            self._new_world(args)
        elif cmd == "stop":
            if args.get("checkpoint"):  # the run is suspended: it continues later from this very state
                self.checkpoint("suspend")
            self.stopped = True
        else:
            self.emit({"type": "error", "t": self.sim.t, "text": f"неизвестная команда {cmd!r}"})

    def _start_world(self):
        meta, blobs = self.sim.header()
        meta = dict(meta)
        meta.update(type="header", t=self.sim.t, fps=self.fps, world=self.world, live=self.sim.live_values(),
                    params=self.sim.params, seed=self.sim.seed, preset=self.world_info.get("preset"),
                    engine=_engine_info(self.sim), backend=_backend_info(self.backend_notes))
        if self.adopted_view is not None:
            meta["adopted_view"] = self.adopted_view
        self.emit(meta, blobs)
        self.sim.after_header()
        try:  # reveal what happens at the initial moment itself (t = 0 events)
            self.sim.advance(self.sim.t)
        except Exception:
            self.emit({"type": "error", "t": self.sim.t, "text": traceback.format_exc()})

    def _new_world(self, args: dict):
        """A new world inside this run: new laws or initial conditions; the previous world stays in the record."""
        if self.make_world is None:
            self.emit({"type": "error", "t": self.sim.t, "text": "новый мир здесь создать нельзя"})
            return
        try:
            sim, info = self.make_world(args.get("preset"), args.get("params"), args.get("seed"))
        except Exception as e:  # any failure is a refused change, reported; the world goes on
            self.emit({"type": "error", "t": self.sim.t, "text": f"Новый мир не создан: {e}"})
            return
        adopted = None
        try:  # what the experimenter placed in the view (slice planes) carries over to the new world
            adopted = self.sim.view_state()
            sim.adopt_view(adopted)
        except Exception as e:  # noqa: BLE001 - the new world starts with its default view
            adopted = None
            self.emit({"type": "notice", "t": sim.t, "text": f"вид прежнего мира не перенесён: {e}"})
        self.sim = sim
        self.world += 1
        self.world_info = dict(info or {})
        self.adopted_view = adopted  # in the header: a restore of this world takes it over again (review C1-5)
        self.speed = float(sim.default_speed)
        self.rate_win = []
        self._start_world()
        self.dirty = True
        self._state("new_world")

    @staticmethod
    def coalesce(msgs: list[dict]) -> list[dict]:
        """Merge consecutive ``set`` commands (a dragged slider sends many) into one."""
        out: list[dict] = []
        for m in msgs:
            if m.get("cmd") == "set" and out and out[-1].get("cmd") == "set":
                merged = dict((out[-1].get("args") or {}).get("values") or {})
                merged.update((m.get("args") or {}).get("values") or {})
                out[-1] = {"cmd": "set", "args": {"values": merged}}
            else:
                out.append(m)
        return out

    def restore(self, world: int, script: list, t_end: float, mute, adopted_view=None):
        """Rebuild the current world (already constructed from its parameters and seed) up to the end of its record:
        take over the view state it took over from the previous world (``adopted_view``, from its header), start it
        and repeat ``script`` — the record's frames ({"frame": t}: advance to t, draw the frame) and commands ({"cmd",
        "t", "args"}: advance to t, apply) in their recorded order — then advance to ``t_end``, with ``mute(True)``
        silencing every message meanwhile (the record has them already). ``world`` is the world's number in the run,
        kept for the next new world."""
        mute(True)
        try:
            self.world = int(world)
            if adopted_view is not None:
                self.sim.adopt_view(adopted_view)
                self.adopted_view = adopted_view
            self._start_world()
            self._replay(script)
            if t_end > self.sim.t:
                self._advance(t_end)
        finally:
            mute(False)
        self.dirty = True

    # --- checkpoints (lfviz.checkpoint) ------------------------------------------------------------------
    # NEGATIVE CONTROL (review 2026-10-29): the world number is not kept (always 1)
    def checkpoint_state(self) -> dict:
        """What a checkpoint holds: the world and the runner's state of it."""
        return {"sim": self.sim, "world": 1, "world_info": self.world_info, "speed": self.speed,
                "adopted_view": self.adopted_view, "backend_notes": self.backend_notes}

    def checkpoint(self, reason: str):
        """Write the world's whole state and record where it stands (a ``checkpoint`` message: the record after it
        is all a resume repeats). Nothing is written when nothing changed since the last one; a world whose state
        cannot be written is reported once (a resume then rebuilds it from its start)."""
        if self.ckpt_dir is None or not self.ckpt_dirty or self.ckpt_failed == self.world:
            return
        from . import checkpoint as C
        t0 = time.monotonic()
        try:
            data = C.dumps(self.checkpoint_state(), self.emit)
            path = C.write(self.ckpt_dir, self.world, data)
        except Exception as e:  # noqa: BLE001 - the run goes on; a resume falls back to the rebuild by replay
            self.ckpt_failed = self.world
            traceback.print_exc(file=sys.stderr)
            self.emit({"type": "checkpoint", "t": self.sim.t, "world": self.world, "reason": reason,
                       "error": f"{type(e).__name__}: {e}"[:500]})
            return
        self.ckpt_dirty = False
        self.ckpt_wall = time.monotonic()
        self.emit({"type": "checkpoint", "t": self.sim.t, "world": self.world, "reason": reason, "file": path.name,
                   "bytes": len(data), "code": self.code, "ms": round((self.ckpt_wall - t0) * 1e3, 1)})

    def restore_from(self, state: dict, script: list, t_end: float, mute):
        """Continue a world from a checkpoint (``state``, loaded with this worker's output function): take over the
        runner's state of that world, then repeat what the record holds after the checkpoint (``script``, as in
        ``restore``) with nothing emitted, and advance to ``t_end``."""
        self.sim = state["sim"]
        self.world = int(state["world"])
        self.world_info = dict(state.get("world_info") or {})
        self.speed = float(state.get("speed", self.sim.default_speed))
        self.adopted_view = state.get("adopted_view")
        self.backend_notes = list(state.get("backend_notes") or [])
        mute(True)
        try:
            self._replay(script)
            if t_end > self.sim.t:
                self._advance(t_end)
        finally:
            mute(False)
        self.ckpt_dirty = bool(script) or t_end > self.sim.t
        self.dirty = True

    def _replay(self, script: list):
        for c in script:
            if "frame" in c:
                t = float(c["frame"])
                if t > self.sim.t:
                    self._advance(t)
                self._frame(0.0)
            else:
                # a command handled after a step / next_event of the same batch has the time after that advance,
                # with no frame between them (review C1-4)
                t = float(c.get("t", self.sim.t))
                if t > self.sim.t:
                    self._advance(t)
                self.handle({"cmd": c["cmd"], "args": c.get("args") or {}})

    def run(self, start: bool = True):
        if start:
            self._start_world()
        self._state("start")
        period = 1.0 / self.fps
        last = time.monotonic()
        while not self.stopped:
            t0 = time.monotonic()
            try:
                # commands (wait up to one period when paused and nothing to draw)
                timeout = 0.0 if (self.playing or self.dirty) else period
                msgs = []
                try:
                    msgs.append(self.q.get(timeout=timeout) if timeout else self.q.get_nowait())
                    while True:
                        msgs.append(self.q.get_nowait())
                except queue.Empty:
                    pass
                for msg in self.coalesce(msgs):
                    self.handle(msg)
                    if self.stopped:
                        break
                if self.stopped:
                    break
                now = time.monotonic()
                dt = min(now - last, 0.25)  # a stall must not turn into a jump of the world
                last = now
                if self.playing:
                    if not self.rate_win:
                        self._rate_sample()
                    self._advance(self.sim.t + self.speed * dt, budget=0.6 * period)
                    self._rate_sample()
                if self.playing or self.dirty:
                    self._frame((time.monotonic() - t0) * 1e3)
                    self.dirty = False
                if self.playing and time.monotonic() - self.ckpt_wall > CHECKPOINT_EVERY:
                    self.checkpoint("periodic")
            except Exception:  # the physics failed: report, pause, keep the process alive
                self.playing = False
                self.emit({"type": "error", "t": self.sim.t, "text": traceback.format_exc()})
                self._state("error")
            spent = time.monotonic() - t0
            if self.playing and spent < period:
                time.sleep(period - spent)
        self.emit({"type": "end", "t": self.sim.t, "reason": "stop"})
