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
``action``, ``view``, ``scene``, ``new_world``; not a scene's ``export``) is recorded as a ``command`` message with the world's time at which it was
applied. A world is rebuilt from its parameters and seed by repeating, in the order of its record, every advance of
the frame clock (each recorded frame's time) and every command (``Runner.restore``), with nothing emitted, and
continues from the end of its record. Repeating the same advances makes the rebuilt world the same even where its
random draws depend on how time was split into frames (the particle sources of v02, v05, v07); tested for every
visualization in ``tests/test_restore.py``.

Continuing from the last state (owner, 2026-10-29): the runner writes checkpoints of its world's whole state
(``lfviz.checkpoint``) when its run is suspended, when it pauses and every ``CHECKPOINT_EVERY`` seconds of computation,
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

from .errors import owner_text
from .i18n import T

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
        """Apply an action at the current time; return a human-readable log line (a text, ``lfviz.i18n.T``)."""
        raise ValueError(f"unknown action {name!r}")

    def engine_modules(self) -> list[str]:
        """The lfphys modules this world's physics comes from (ids like "core.relativity"), for the player's panel
        "Physics of this world" (core vs theories outside the core)."""
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
        raise ValueError(T("this world has no view requests"))

    def set_live(self, values: dict) -> str:
        """Change live parameters at the current time (the experimenter rebuilds part of the set-up); return a log
        line. Must leave the world unchanged when it raises."""
        raise ValueError(T("nothing can be changed while this world runs"))

    def next_event_time(self) -> float | None:
        return None

    def after_header(self) -> None:
        """Called right after the header is emitted (flush messages produced while constructing the world)."""

    def max_step(self) -> float | None:
        """Largest simulation-time step the world can take in one advance (None = unlimited)."""
        return None

    # --- optional hooks asked before a world is built (review 2026-11-04 UX-params P1, P8; RULES.md §3) ---------------
    @classmethod
    def check_params(cls, params: dict) -> None:
        """Refuse a combination of world parameters that cannot be built, cheaply and before anything is allocated:
        raise ``lfviz.errors.Refusal(text, hint)`` (texts: what is wrong, what to change). The server asks it before it starts a
        run (the catalogue then shows the reason on the form) and the worker before a new world."""

    @classmethod
    def estimate_bytes(cls, params: dict):
        """The memory a world with these parameters will allocate, in bytes (or ``(bytes, what, change)`` with the
        owner's words for what takes it and what to change); None when not known. Compared with the worker's budget
        before the world is built: above it the world is refused (``lfviz.limits``; review UX-params P8)."""
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
        return [{"id": "?", "layer": "?", "title": T("the engine's catalogue is not available: {error}", error=str(e))}]


MakeWorld = Callable[[str | None, dict | None, int | None], tuple[Simulation, dict]]


def _backend_info(notes=()) -> dict | None:
    """Devices and precisions of the engine's kernels in this run (plan P11): the settings in force and what each
    kernel called so far ran on (``lfphys.core.backend.used``)."""
    try:
        from lfphys.core import backend as B
    except Exception:  # the engine without the backend (an old record): nothing to report
        return None
    return {"settings": B.settings(), "used": B.used(), "notes": list(notes)}


CHECKPOINT_EVERY = 120.0  # seconds of wall time between checkpoints of a computing world
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
        self.ckpt_dirty = False  # the world changed since the last checkpoint (an advance, a frame, a command)
        self.ckpt_wall = time.monotonic()
        self.ckpt_failed = 0  # the world number whose state could not be pickled (not tried again for that world)
        self.ckpt_root: Path | None = None  # engine/: the code files of a checkpoint are recorded relative to it
        self.ckpt_writer = None  # lfviz.checkpoint.Writer: files written in the background
        self.last_error = None  # the last failure reported (a repeat is not reported again: review B6-F6)
        self.gpu_hot = False  # the backend's temperature guard as last reported (review B6-F19)
        # the worker's output (lfviz.worker.Output) when there is one: a computing command's messages are held and
        # written together when it is done, after a "busy" notice that is not recorded (review UX-ui U9): a command
        # cancelled meanwhile leaves nothing in the record, and a world that fails to show itself is dropped whole
        self.out = None
        self.action_labels: dict = {}  # an action's name -> its label in the header (review UX-params P20)
        self.ckpt_last: dict | None = None  # the last checkpoint message with a file (checkpoint_now repeats it)

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
            raise ValueError(T("the world's frame holds keys of the player {keys}: rename them in the world's frame()",
                               keys=str(sorted(clash))))
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

    def _thermal_note(self):
        """The backend's temperature guard switched GPU 0's kernels to the CPU or back (review B6-F19): said in the
        record and the player when it happens, not only in the next world's header (a playground world lasts hours)."""
        try:
            from lfphys.core import backend as B
            th = B.thermal()
        except Exception:  # noqa: BLE001 - the engine without the guard: nothing to say
            return
        hot = bool(th.get("hot"))
        if hot == self.gpu_hot:
            return
        self.gpu_hot = hot
        t = th.get("temp") if th.get("temp") is not None else th.get("last_temp")
        text = (T("GPU 0 is hot ({temp:.0f} °C): the engine's kernels run on the CPU until it cools to {resume:.0f} °C "
                  "(slower; the results of the CPU and the GPU agree within the tolerances)", temp=t,
                  resume=th["resume_c"])
                if hot else T("GPU 0 has cooled ({temp:.0f} °C): the engine's kernels may run on the GPU again", temp=t))
        self.emit({"type": "notice", "t": self.sim.t, "text": text, "backend": _backend_info()})

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

    WORLD_COMMANDS = ("set", "action", "view", "scene", "new_world")  # recorded with their time: a restore replays them
    COMPUTING = ("step", "next_event") + WORLD_COMMANDS  # may take long: held and announced (review UX-ui U9)

    def handle(self, msg: dict):
        cmd = msg.get("cmd")
        args = msg.get("args") or {}
        if self.out is None or cmd not in self.COMPUTING or (cmd == "scene" and args.get("op") == "export"):
            self._handle(cmd, args)
            return
        self.out.busy({"type": "busy", "on": True, "cmd": cmd, "what": _busy_what(cmd, args, self.action_labels),
                       "wall": time.time(), "t": self.sim.t})
        self.out.hold()
        try:
            self._handle(cmd, args)
        finally:
            # "busy off" first, then what the command emitted: once the server has read it the command is done and
            # cannot be cancelled; before it, a cancel drops everything after (lfviz.runs.Run.cancel)
            self.out.release({"type": "busy", "on": False, "cmd": cmd, "t": self.sim.t})

    def _handle(self, cmd, args: dict):
        # a scene's export changes nothing: neither recorded nor making the checkpoint stale (review B6-F24)
        export = cmd == "scene" and args.get("op") == "export"
        if cmd not in ("play", "pause", "speed", "stop", "checkpoint_now") and not export:  # may change the world (CK-9)
            self.ckpt_dirty = True
        if cmd in self.WORLD_COMMANDS and not export:
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
                self.emit({"type": "notice", "t": self.sim.t, "text": T("No scheduled events ahead")})
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
                self._refused(e, "action", label=self.action_labels.get(name) or name)
            else:
                if text:  # a change that says nothing makes no empty line in "Events" (review LB1-p02-ux X12)
                    self.emit({"type": "event", "kind": "action", "t": self.sim.t, "name": name,
                               "args": args.get("args") or {}, "text": text})
                self.dirty = True
        elif cmd == "set":  # live parameters: applied at once, at the current moment
            values = args.get("values") or {}
            try:
                text = self.sim.set_live(values)
            except Exception as e:  # any failure is a refused change, reported; the world goes on
                self._refused(e, "set")
            else:
                if text:  # a no-op change (the values in force already) logs nothing (review LB1-p02-ux X12)
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
                self._refused(e, "view")
            else:
                if text:
                    self.emit({"type": "event", "kind": "view", "t": self.sim.t, "name": "view", "args": args,
                               "text": text})
                self.dirty = True
        elif cmd == "scene":  # a playground's scene changed by hand (lfviz.playground): applied at the current moment
            try:
                text = self.sim.scene(args)
            except Exception as e:  # noqa: BLE001 - a refused change is reported; the scene is left as it was
                self._refused(e, "scene")
            else:
                if text:
                    self.emit({"type": "event", "kind": "scene", "t": self.sim.t, "name": args.get("op"),
                               "args": {k: v for k, v in args.items() if k != "state"}, "text": text})
                self.dirty = True
        elif cmd == "new_world":
            self._new_world(args)
        elif cmd == "checkpoint_now":
            # the server asks for the state as it is now (a sweep of the instruments starts from it; integrator,
            # 2026-11-11): always answered by a ``checkpoint`` message carrying the request's tag; not a change of the
            # world (not recorded as a command, never resumes a run)
            self.checkpoint("request", tag=args.get("tag"), force=True)
        elif cmd == "stop":
            if args.get("checkpoint"):  # the run is suspended: it continues later from this very state
                self.checkpoint("suspend")
            if self.ckpt_writer is not None:
                self.ckpt_writer.wait()  # the file is in place before the worker ends
            self.stopped = True
        else:
            self.emit({"type": "error", "t": self.sim.t, "text": T("unknown command {cmd}", cmd=repr(cmd))})

    def _refused(self, e: BaseException, context: str, **fmt):
        """Report a refused or failed command in the owner's terms (lfviz.errors): a refusal as it is; any other failure
        as a short sentence, its exception and traceback kept in ``detail`` and the worker's log (review
        UX-params P4)."""
        text, detail = owner_text(e, context, **fmt)
        self.emit({"type": "error", "t": self.sim.t, "text": text, **({"detail": detail} if detail else {})})

    def _start_world(self):
        """Show the world: its header, what it emitted while being built (``after_header``) and what happens at its
        initial moment. Raises when any of it fails: the caller reports the world as not built (review UX-params P3: an
        exception in ``after_header`` killed the worker and every ⏺ repeated it)."""
        meta, blobs = self.sim.header()
        meta = dict(meta)
        meta.update(type="header", t=self.sim.t, fps=self.fps, world=self.world, live=self.sim.live_values(),
                    params=self.sim.params, seed=self.sim.seed, preset=self.world_info.get("preset"),
                    engine=_engine_info(self.sim), backend=_backend_info(self.backend_notes))
        if self.adopted_view is not None:
            meta["adopted_view"] = self.adopted_view
        self.action_labels = {a.get("name"): a.get("label") for a in (meta.get("actions") or [])
                              if isinstance(a, dict) and a.get("name")}
        self.emit(meta, blobs)
        self.sim.after_header()
        self.sim.advance(self.sim.t)  # reveal what happens at the initial moment itself (t = 0 events)

    def start(self) -> bool:
        """Show the first world (``_start_world``); when it fails the owner reads why ("World not created: …") and the
        worker ends with the reason "world not built": the server keeps such a run as failed, never resumable (review
        UX-params P3: the worker died and every ⏺ repeated the failure). Its messages are not held: a world that takes
        long to show itself (v08's slices on the CPU) is drawn as it comes. False when it failed."""
        try:
            self._start_world()
        except Exception as e:  # noqa: BLE001 - reported to the owner, the worker ends
            text, detail = owner_text(e, "build")
            self.emit({"type": "error", "t": self.sim.t, "text": text, **({"detail": detail} if detail else {})})
            self.emit({"type": "end", "t": self.sim.t, "reason": "world not built"})
            return False
        return True

    def _new_world(self, args: dict):
        """A new world inside this run: new laws or initial conditions; the previous world stays in the record. A world
        that cannot be built, or fails to show itself, is refused as a whole: the previous world goes on."""
        if self.make_world is None:
            self.emit({"type": "error", "t": self.sim.t, "text": T("A new world cannot be created here")})
            return
        params = args.get("params")
        export = getattr(self.sim, "carry_export", None)
        carried = None
        if args.get("carry") and export is not None:
            # the scene carried over (plan P16.1, "carry the scene over"): the current world's export becomes the new world's
            # initial scene, a parameter of the new world (its header holds it: a restore rebuilds the same world); the
            # heavy state its section gives (``carry_state``: atoms, a flow) goes to a file of the run named there with
            # its hash (review LB1-F5), so that a restore by replay reads the very same state
            try:
                from . import playground as PG
                scene, heavy = export()
                if heavy is not None:
                    carried = PG.store_carry(heavy, self.world + 1, self.ckpt_dir)
            except Exception as e:  # noqa: BLE001 - a scene that cannot be exported: the new world is refused
                self._refused(e, "new_world")
                return
            params = {**(params or {}), "scene": {**scene, "carry": True, **({"carry_file": carried} if carried else {})}}

        def drop():
            if carried is not None:
                from . import playground as PG
                PG.drop_carry(carried, self.ckpt_dir)
        try:
            sim, info = self.make_world(args.get("preset"), params, args.get("seed"))
        except Exception as e:  # any failure is a refused change, reported; the world goes on
            drop()
            self._refused(e, "new_world")
            return
        adopted = None
        note = None
        try:  # what the experimenter placed in the view (slice planes) carries over to the new world
            adopted = self.sim.view_state()
            sim.adopt_view(adopted)
        except Exception as e:  # noqa: BLE001 - the new world starts with its default view
            adopted = None
            note = T("the previous world's view was not carried over: {why}", why=owner_text(e)[0])
        before = (self.sim, self.world, self.world_info, self.adopted_view, self.speed, self.rate_win,
                  self.action_labels)
        mark = self.out.mark() if self.out is not None else None
        self.sim = sim
        self.world += 1
        self.world_info = dict(info or {})
        self.adopted_view = adopted  # in the header: a restore of this world takes it over again (review C1-5)
        self.speed = float(sim.default_speed)
        self.rate_win = []
        try:
            if note:
                self.emit({"type": "notice", "t": sim.t, "text": note})
            self._start_world()
        except Exception as e:  # noqa: BLE001 - the new world never shows itself; the previous one goes on
            if mark is not None:
                self.out.drop(mark)
            (self.sim, self.world, self.world_info, self.adopted_view, self.speed, self.rate_win,
             self.action_labels) = before
            drop()
            self._refused(e, "new_world")
            return
        if self.ckpt_dir is not None and hasattr(sim, "carry_export"):  # earlier worlds are never restored again
            from . import playground as PG
            PG.prune_carry(self.world, self.ckpt_dir)
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
    def checkpoint_state(self) -> dict:
        """What a checkpoint holds: the world and the runner's state of it."""
        try:  # the devices each kernel ran on so far: a new world's header reports them (lfphys.core.backend.used)
            from lfphys.core import backend as B
            used = B.used()
        except Exception:  # noqa: BLE001 - the engine without the backend
            used = None
        return {"sim": self.sim, "world": self.world, "world_info": self.world_info, "speed": self.speed,
                "adopted_view": self.adopted_view, "backend_notes": self.backend_notes, "backend_used": used}

    def checkpoint(self, reason: str, tag=None, force: bool = False):
        """Write the world's whole state and record where it stands (a ``checkpoint`` message: the record after it
        is all a resume repeats). Nothing is written when nothing changed since the last one; a world whose state
        cannot be written is reported once (a resume then rebuilds it from its start).

        ``force`` (the command ``checkpoint_now``): always answered by a ``checkpoint`` message carrying ``tag`` —
        a new file, or, when nothing changed since the last one, that file's message again; ``error`` when no file can
        be given. The file is written in the background: whoever asked waits for it to appear."""
        extra = {"tag": tag} if force else {}
        if self.ckpt_dir is None or self.ckpt_failed == self.world:
            if force:
                why = (T("this worker writes no saved states") if self.ckpt_dir is None
                       else T("the state of this world cannot be saved (see the earlier message about saving)"))
                self.emit({"type": "checkpoint", "t": self.sim.t, "world": self.world, "reason": reason, **extra,
                           "error": why})
            return
        from . import checkpoint as C
        if self.ckpt_writer is None:
            self.ckpt_writer = C.Writer()
        if self.ckpt_writer.take_failure():  # the last file was not written (review CK-8): write the state again
            self.ckpt_dirty = True
        if not self.ckpt_dirty:
            last = self.ckpt_last
            if not force:
                return
            if last is not None and last.get("world") == self.world:  # this very state is in that file
                self.emit({**last, "reason": reason, **extra})
                return
        t0 = time.monotonic()
        start = getattr(self.sim, "segment_start", None)
        if start is not None:  # a playground: a new segment of the record starts here, drawable on its own
            # (lfviz.playground: the scene, the section's rekey, the latest value of every set-like message); emitted
            # before the state is pickled, so that the checkpoint follows them in the record
            self.emit({"type": "record_segment", "t": self.sim.t, "world": self.world})
            start()
        try:
            data = C.dumps(self.checkpoint_state(), self.emit)
        except Exception as e:  # noqa: BLE001 - the state cannot be pickled: a resume rebuilds the world by replay
            self.ckpt_failed = self.world
            traceback.print_exc(file=sys.stderr)
            self.emit({"type": "checkpoint", "t": self.sim.t, "world": self.world, "reason": reason, **extra,
                       "error": f"{type(e).__name__}: {e}"[:500]})
            return
        name = C.new_name(self.world)
        root = self.ckpt_root or Path(__file__).resolve().parents[3]
        files = C.code_files(root)
        self.ckpt_writer.submit(self.ckpt_dir, name, data)  # written in the background (review CK-12)
        self.ckpt_dirty = False
        self.ckpt_wall = time.monotonic()
        msg = {"type": "checkpoint", "t": self.sim.t, "world": self.world, "reason": reason, "file": name,
               "bytes": len(data), "code": C.files_hash(root, files), "files": files, "env": C.runtime_env(),
               "ms": round((self.ckpt_wall - t0) * 1e3, 1)}
        self.ckpt_last = msg
        self.emit({**msg, **extra})

    def restore_from(self, state: dict, script: list, t_end: float, mute):
        """Continue a world from a checkpoint (``state``, loaded with this worker's output function): take over the
        runner's state of that world, then repeat what the record holds after the checkpoint (``script``, as in
        ``restore``) with nothing emitted, and advance to ``t_end``."""
        self.sim = state["sim"]
        self.world = int(state["world"])
        self.world_info = dict(state.get("world_info") or {})
        self.speed = float(state.get("speed", self.sim.default_speed))
        self.adopted_view = state.get("adopted_view")
        # the backend notes stay this worker's (the devices of this start: review CK-11); the record of the kernels'
        # devices is the saved world's, as an uninterrupted run would report it
        if state.get("backend_used") is not None:
            from lfphys.core import backend as B
            B.set_used(state["backend_used"])
        changed = bool(script) or t_end > self.sim.t
        mute(True)
        try:
            self._replay(script)
            if t_end > self.sim.t:
                self._advance(t_end)
        finally:
            mute(False)
        self.ckpt_dirty = changed
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
        if start and not self.start():
            return
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
                    self.last_error = None
                    self._thermal_note()
                if self.playing and time.monotonic() - self.ckpt_wall > getattr(self.sim, "checkpoint_every",
                                                                                 CHECKPOINT_EVERY):
                    self.checkpoint("periodic")
            except Exception as e:  # the physics failed: report, pause, keep the process alive
                self.playing = False
                self.dirty = False  # a failing frame is not drawn again and again (review B6-F6)
                key = traceback.format_exc()
                if key != self.last_error:  # the same failure again (e.g. after a command): once
                    # in the owner's terms, the traceback in the detail and the log (review UX-params P4, UX-ui U6)
                    text, detail = owner_text(e, "advance", t=float(self.sim.t))
                    self.emit({"type": "error", "t": self.sim.t, "text": text, **({"detail": detail} if detail else {})})
                    self.last_error = key
                self._state("error")
            spent = time.monotonic() - t0
            if self.playing and spent < period:
                time.sleep(period - spent)
        if self.ckpt_writer is not None:
            self.ckpt_writer.wait()
        self.emit({"type": "end", "t": self.sim.t, "reason": "stop"})


_SCENE_OPS = {"remove": T("scene: an object is being removed"), "set": T("scene: an object is being changed"),
              "edit": T("scene: an object is being moved"), "duplicate": T("scene: an object is being copied"),
              "label": T("scene: an object is being renamed"), "clear": T("scene: being cleared")}


def _busy_what(cmd: str, args: dict, labels: dict):
    """What a computing command is doing, in the owner's words (the busy notice, review UX-ui U9)."""
    if cmd == "scene":
        op = args.get("op")
        if op == "add":
            return T("scene: an object “{type}” is being added", type=args["type"]) if args.get("type") \
                else T("scene: an object is being added")
        return _SCENE_OPS.get(op, T("scene: an object is being changed"))
    if cmd == "set":
        return T("the set-up is being rebuilt")
    if cmd == "action":
        return T("action “{label}”", label=labels.get(args.get("name")) or args.get("name"))
    if cmd == "view":
        return T("a slice is being built")
    if cmd == "new_world":
        return T("a new world is being created")
    if cmd == "step":
        return T("a step of the computation")
    if cmd == "next_event":
        return T("computing up to the next event")
    return cmd
