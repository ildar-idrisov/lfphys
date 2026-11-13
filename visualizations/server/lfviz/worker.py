# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The process that runs one simulation (spawned by the server, one per run).

    python -m lfviz.worker --viz u31_light_travel

stdin : first line - JSON {"params": {...}, "seed": int, "preset": str|null[, "seed0": int, "checkpoints": {"dir":
        path, "code": hash}, "restore": {"world": n, "commands": [{frame: t} | {t, cmd, args}], "t_end": t,
        "adopted_view": ..., "checkpoint": {"file": path, "commands": [...]}, "complete": bool}]} (with "restore":
        continue the world from its checkpoint, repeating only the record after it, or, without a usable checkpoint,
        rebuild it by repeating its recorded frames and commands in order — emitting nothing until it reaches t_end —
        then go on; never when "complete" is false: a playground's window lost part of the world; "checkpoints":
        where this worker writes the world's state, lfviz.checkpoint; "seed0" is the run's first seed, used by a later
        new world given none); then one JSON command per line
        ({"cmd": "play" | "pause" | "speed" | "step" | "next_event" | "action" | "set" | "view" | "scene" |
          "new_world" | "checkpoint_now" | "stop",
          "args": {...}}); ``checkpoint_now {tag}`` (the server's, for the instruments' sweeps) is answered by a
        ``checkpoint`` message carrying the tag, and changes nothing.
stdout: length-prefixed binary messages (``protocol``). Nothing else may be printed to stdout;
        diagnostics go to stderr (the server stores them in the run folder as ``worker.log``).

The worker holds its memory budget (``lfviz.limits``: ``LFVIZ_WORKER_MEM`` from the server, set as its hard limit of
private memory before a world is built; review UX-params P8), asks a world's ``check_params`` and ``estimate_bytes``
before building it, and writes a computing command's messages (and a world's start) as one piece after a ``busy``
notice (``Output``; review UX-ui U9, UX-params P3).
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import traceback
from pathlib import Path

from . import checkpoint, limits, protocol, registry
from .errors import owner_text
from .i18n import T, join, text_of
from .sim import Runner


class Output:
    """The worker's output (stdout): a message is written at once, or held while a computing command or a world's start
    is under way (``hold``) and written with the rest when it is done (``release``); ``busy`` notices are written at
    once (the server forwards them and does not record them). Muted while a world is rebuilt from its record."""

    def __init__(self, stream):
        self.stream = stream
        self.lock = threading.Lock()
        self.muted = False
        self.held: list | None = None

    def _write(self, data: bytes):
        with self.lock:
            self.stream.write(data)
            self.stream.flush()

    def emit(self, meta, blobs=None):
        if self.muted:
            return
        item = protocol.frame_stream_item(protocol.encode(meta, blobs))
        if self.held is not None:
            self.held.append(item)
            return
        self._write(item)

    def busy(self, meta: dict):
        if not self.muted:
            self._write(protocol.frame_stream_item(protocol.encode(meta)))

    def hold(self):
        if self.held is None:
            self.held = []

    def mark(self) -> int:
        return len(self.held) if self.held is not None else 0

    def drop(self, mark: int):
        if self.held is not None:
            del self.held[mark:]

    def release(self, first: dict | None = None):
        """Write what was held (``first`` before it: the busy notice's end) and write at once from now on."""
        items, self.held = self.held or [], None
        if first is not None and not self.muted:
            items = [protocol.frame_stream_item(protocol.encode(first))] + items
        if items:
            self._write(b"".join(items))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run one visualization simulation over stdin/stdout.")
    ap.add_argument("--viz", required=True, help="visualization id, e.g. u31_light_travel")
    ap.add_argument("--fps", type=float, default=20.0, help="frames per second while playing")
    a = ap.parse_args(argv)

    limits.apply_hard_limit()  # before anything large is allocated (review UX-params P8)
    registry.ensure_path()
    out = Output(sys.stdout.buffer)
    sys.stdout = sys.stderr  # any stray print() goes to the log, not into the binary stream
    emit = out.emit

    def mute(on: bool):
        out.muted = bool(on)

    init = json.loads(sys.stdin.readline())
    try:  # devices and precisions of the engine's kernels for this run (plan P11): the settings in force at its start
        from lfphys.core import backend as _backend
        backend_notes = _backend.configure(init.get("backend") or {})
    except Exception as e:  # noqa: BLE001 - the run goes on with the defaults
        backend_notes = [T("the device settings were not applied: {error}", error=text_of(e))]
    viz = registry.load(a.viz)
    rs = init.get("restore")
    t0 = float(rs.get("t_end", 0.0)) if rs else 0.0  # a failed restore is reported at the record's end (review C1-14)
    params, errors = viz["schema"].resolve(None, init.get("params") or {})
    if errors:
        emit({"type": "error", "t": t0, "text": T("{head}: {body}", head=T("World not restored") if rs else
                                                    T("World not created"), body=join(errors, "; "))})
        emit({"type": "end", "t": t0, "reason": "bad parameters"})
        return 2
    seed = int(init.get("seed", 0))
    seed0 = int(init.get("seed0", seed))  # the run's first seed: a new world without one takes it (review C1-20)

    def precheck(p):
        """What a world says about its parameters before it is built: a refused combination, and the memory it needs
        against this worker's budget (review UX-params P1, P8)."""
        viz["simulation"].check_params(p) if hasattr(viz["simulation"], "check_params") else None
        limits.check_estimate(viz["simulation"], p)

    def make_world(preset, values, seed):
        """A new world of the same visualization (command new_world): defaults, then the preset, then values."""
        p, errs = viz["schema"].resolve(preset, values or {})
        if errs:
            raise ValueError(join(errs, "; "))
        precheck(p)
        s = seed0 if seed in (None, "") else int(seed)
        return viz["simulation"](p, s, emit), {"preset": preset}

    q: "queue.Queue[dict]" = queue.Queue()

    def reader():
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                q.put(json.loads(line))
            except json.JSONDecodeError:
                pass
        q.put({"cmd": "stop"})  # the server closed the pipe

    threading.Thread(target=reader, daemon=True).start()
    ck = init.get("checkpoints") or {}
    # a carried scene's state (lfviz.playground.store_carry; review LB1-F5) lives in the same folder as the checkpoints:
    # a world restored by replay reads it from there
    from . import playground as _playground
    _playground.set_carry_dir(ck.get("dir"))

    def new_runner(sim):
        r = Runner(sim, emit, q, fps=a.fps, make_world=make_world,
                   world_info={"preset": init.get("preset"), "backend_notes": backend_notes})
        r.out = out
        r.ckpt_dir = Path(ck["dir"]) if ck.get("dir") else None
        r.ckpt_root = registry.ROOT.parent
        return r

    import time as _time
    out.busy({"type": "busy", "on": True, "cmd": "build",
              "what": T("the world is being restored") if rs else T("the world is being built"),
              "t": t0, "wall": _time.time()})
    cp = (rs or {}).get("checkpoint")
    if cp:  # continue from the last state (owner, 2026-10-29): no recomputation of the record before it
        try:
            state = checkpoint.loads(Path(cp["file"]).read_bytes(), emit)
            runner = new_runner(state["sim"])
            t_ck = runner.sim.t
            n_tail = sum(1 for c in cp.get("commands") or [] if "frame" in c)
            runner.restore_from(state, cp.get("commands") or [], t0, mute)
        except Exception as e:  # noqa: BLE001 - fall back to the rebuild from the start, and say why
            traceback.print_exc()  # to worker.log
            if rs.get("complete") is False:  # a moving window lost the world's start: no rebuild (review B6-F2)
                out.busy({"type": "busy", "on": False, "cmd": "build", "t": t0})
                emit({"type": "error", "t": t0, "detail": f"{type(e).__name__}: {e}"[:500],
                      "text": T("The saved state did not load, and the world's start has already left the record's "
                                "window — it cannot be continued. Start the world again from a scene file or a "
                                "scenario")})
                emit({"type": "end", "t": t0, "reason": "restore failed"})
                return 4
            emit({"type": "notice", "t": t0, "detail": f"{type(e).__name__}: {e}"[:500],
                  "text": T("The saved state did not load; the world is recomputed from its start along the record")})
        else:
            out.busy({"type": "busy", "on": False, "cmd": "build", "t": runner.sim.t})
            emit({"type": "resumed", "t": runner.sim.t, "how": "checkpoint", "tail_frames": n_tail})
            emit({"type": "notice", "t": runner.sim.t, "text": (
                T("The world continued from its saved state at t = {t0:.6g} s (then {n:d} frames of the record were "
                  "repeated); the record continues from t = {t1:.6g} s", t0=t_ck, n=n_tail, t1=runner.sim.t) if n_tail
                else T("The world continued from its saved state at t = {t0:.6g} s; the record continues from "
                       "t = {t1:.6g} s", t0=t_ck, t1=runner.sim.t))})
            runner.run(start=False)
            return 0
    try:
        if not rs:
            precheck(params)
        sim = viz["simulation"](params, seed, emit)
    except Exception as e:  # the first world could not be built: say why in the player, do not die with a traceback
        text, detail = owner_text(e, "restore" if rs else "build")
        out.busy({"type": "busy", "on": False, "cmd": "build", "t": t0})
        emit({"type": "error", "t": t0, "text": text, **({"detail": detail} if detail else {})})
        emit({"type": "end", "t": t0, "reason": "world not built"})
        return 3
    runner = new_runner(sim)
    if rs:
        try:
            runner.restore(rs.get("world", 1), rs.get("commands") or [], t0, mute, rs.get("adopted_view"))
        except Exception as e:  # noqa: BLE001 - say why in the player
            text, detail = owner_text(e, "restore")
            out.busy({"type": "busy", "on": False, "cmd": "build", "t": t0})
            emit({"type": "error", "t": t0, "text": text, **({"detail": detail} if detail else {})})
            emit({"type": "end", "t": t0, "reason": "restore failed"})
            return 4
        out.busy({"type": "busy", "on": False, "cmd": "build", "t": runner.sim.t})
        n_cmd = sum(1 for c in rs.get("commands") or [] if "cmd" in c)
        emit({"type": "resumed", "t": runner.sim.t, "how": "replay"})
        emit({"type": "notice", "t": runner.sim.t,
              "text": T("World restored: recomputed from its start along the record ({n:d} changes of the set-up) "
                        "and continuing from t = {t:.6g} s", n=n_cmd, t=runner.sim.t)})
        runner.run(start=False)
    else:
        ok = runner.start()
        out.busy({"type": "busy", "on": False, "cmd": "build", "t": runner.sim.t})
        if not ok:
            return 3
        runner.run(start=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
