# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Run manager: one run = one worker process + one recording + any number of viewers.

* A run is started only by an explicit request (the owner's browser, ``POST /api/runs``).
* Everything the worker emits is written to ``runs/<id>/stream.lfrec`` from the first message and broadcast to
  the viewers. A viewer that joins late gets the record so far (all accumulative messages, frames thinned to at
  most ``HISTORY_FRAMES``), then the live tail, with no gap and no duplicate.
* Frames may be dropped for a slow viewer; accumulative messages never are.
* A run with no viewers pauses after ``idle_pause`` seconds; after ``idle_suspend`` seconds its worker is released
  (state "suspended"). A suspended run is resumed when it is asked to compute again: its world is rebuilt by
  replaying the recorded commands at their times (``Runner.restore``) and goes on from the end of its record (owner,
  2026-10-28: there is no "stop"; a run is recording or paused, and can always be continued). When every worker is
  busy, the run idle longest without viewers is suspended to make room. A worker that ends by itself (a crash, a
  failed rebuild) leaves its run suspended too: the record is whole, and ⏺ tries again.
* A resume continues the world from its last checkpoint (``lfviz.checkpoint``: the worker writes the world's whole
  state when the run is suspended, when it pauses and every two minutes of computation, and records each with a
  ``checkpoint`` message), repeating only what the record holds after it; without a usable one (another code hash, a
  missing or unreadable file) the world is rebuilt from its start by replaying the record (owner, 2026-10-29).
* The record is the truth, ``meta.json`` a cache of it: at start the latest world, its parameters and the world time
  are taken from the record, and a record cut by a crash is cut back to its last whole message (the cut bytes are
  kept apart in ``stream.cut-tail.bin``).
* While a resumed world is being rebuilt it is never suspended to make room or for idleness, and a world-changing
  command other than the one that resumed it is refused (it could not be applied before the rebuild ends).
* A playground's run (plan P15.0) keeps its record as a moving window, the buffer (owner, 2026-10-29: «можно делать
  автозапись всех последних N кадров, старые вышедшие из окна удалять, сохранять все только если нажата запись
  вручную»; the scheme agreed then: the button keeps the buffer and records on, checkpoints in the buffer, the window by
  time or size): the record is split into segments, each starting where the worker writes a checkpoint (its
  ``record_segment`` marker, then the scene, the section's ``rekey`` and the latest value of every set-like message,
  ``lfviz.playground``; then the ``checkpoint``), so that every segment can be shown from its first message; segments
  older than the window (``buffer.window_s`` seconds of the time the world was shown computing — frames flowing, a
  pause does not age the record — and ``buffer.window_mb`` with the checkpoint files) are deleted unless recording was
  switched on while they were kept (``set_recording``), never while a history or a download reads them. The worlds'
  headers are kept apart (``headers.lfrec``) and sent before the first kept message of their world. A resume
  continues from a checkpoint; a world whose start has left the buffer, or whose kept record has a hole, is not
  rebuilt by replay (``_latest_world``: ``complete``; the worker refuses too when the checkpoint does not load).
* Limits: concurrent workers, a quota for the runs folder, and removal of runs whose last action (a viewer, a
  command) is older than ``keep_days`` (3 by default, owner 2026-10-28), the oldest last action first beyond the
  quota; runs marked "keep" and runs open in a tab are never removed. The period is set on the catalogue page and
  kept in the runs folder's ``settings.json`` (owner, 2026-10-29); a change that would remove runs at once lists them
  and is applied only when those runs are confirmed.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import shutil
import struct
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import checkpoint as CK, limits, protocol, registry, devices
from .i18n import T, is_t, join, json_hook, text_of

SETTINGS_NAME = "settings.json"  # the runs folder's own settings: the removal period chosen on the catalogue page
KEEP_DAYS_MAX = 3650

HISTORY_FRAMES = 4000
MAX_PENDING_FRAMES = 8


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


@dataclass
class Entry:
    offset: int  # of the message body inside the file
    length: int
    is_frame: bool
    kind: str = ""  # the message type (only "header", "command" and "checkpoint" are looked up)
    t: float | None = None  # the world time of the message (a restore repeats every advance of the frame clock)
    seg: int = 0  # the segment file of the record (a playground's buffer: lfviz.runs, Run.seg_path)


RESUMING = ("play", "step", "next_event", "set", "action", "view", "scene", "new_world")  # commands that need the world
WORLD_COMMANDS = ("set", "action", "view", "scene", "new_world")  # recorded with their time (sim.Runner.WORLD_COMMANDS)


def _entry(off: int, msg: bytes, pm: dict, seg: int = 0) -> Entry:
    typ = pm.get("type")
    t = pm.get("t")
    return Entry(off, len(msg), typ == "frame", typ if typ in ("header", "command", "checkpoint") else "",
                 float(t) if isinstance(t, (int, float)) else None, seg)


BUFFER_DEFAULT = {"window_s": 600, "window_mb": 1024}  # a playground's buffer: the last 10 min, at most 1 GB
NOT_RECORDED = ("scene_export", "busy")  # forwarded to the viewers, never written (a file the player saves; what the
# worker is computing now: review UX-ui U9)


class Viewer:
    def __init__(self, ws, run: "Run", n_history: int):
        self.ws = ws
        self.run = run
        self.q: asyncio.Queue = asyncio.Queue()
        self.pending_frames = 0
        self.n_history = n_history
        self.alive = True

    def offer(self, msg: bytes, is_frame: bool):
        if not self.alive:
            return
        if is_frame:
            if self.pending_frames >= MAX_PENDING_FRAMES:
                return
            self.pending_frames += 1
        self.q.put_nowait((msg, is_frame))

    async def pump(self):
        try:
            await self.run.send_history(self.ws, self.n_history)
            while self.alive:
                msg, is_frame = await self.q.get()
                if msg is None:
                    break
                if is_frame:
                    self.pending_frames -= 1
                await self.ws.send_bytes(msg)
        except (ConnectionError, RuntimeError, asyncio.CancelledError):
            pass
        except OSError:  # a record file gone or unreadable: close, the player reconnects (review B6-F9)
            try:
                await self.ws.close()
            except Exception:  # noqa: BLE001
                pass
        finally:
            self.alive = False


@dataclass
class Run:
    mgr: "RunManager"
    id: str
    viz_id: str
    meta: dict
    dir: Path
    entries: list = field(default_factory=list)
    viewers: set = field(default_factory=set)
    proc: asyncio.subprocess.Process | None = None
    file: object = None
    size: int = len(protocol.MAGIC)
    last_viewer_time: float = field(default_factory=time.monotonic)
    _reader: asyncio.Task | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)  # resume / stop / delete one at a time (review C1-1)
    rebuilding: bool = False  # a resumed worker is rebuilding its world (until its first "state")
    unapplied: list = field(default_factory=list)  # world-changing commands sent to it meanwhile
    n_errors_at_resume: int = 0  # the passport's errors before this rebuild (only later ones explain its failure)
    stopping: bool = False  # the worker is being stopped (it writes its checkpoint): a command waits for it (CK-4)
    seg: int = 0  # the segment being written (0: stream.lfrec; a playground's buffer adds stream.NNNNNN.lfrec)
    headers: dict = field(default_factory=dict)  # world number -> its header message (a buffer keeps them apart)
    readers: int = 0  # histories and downloads being sent: the window is not trimmed meanwhile (review B6-F9)
    last_frame_wall: float = 0.0  # when the last frame arrived (the window counts the time frames flow: B6-F10)
    busy: dict | None = None  # what the worker is computing now (its "busy" notice), None when idle (review UX-ui U9)
    busy_sent: list = field(default_factory=list)  # world-changing commands sent while it computed (not yet applied)
    cancelling: bool = False  # a cancel was decided: nothing the worker writes from now on is recorded or shown

    @property
    def stream_path(self) -> Path:
        return self.dir / "stream.lfrec"

    def seg_path(self, k: int) -> Path:
        return self.stream_path if k == 0 else self.dir / f"stream.{k:06d}.lfrec"

    @property
    def buffered(self) -> bool:
        return isinstance(self.meta.get("buffer"), dict)

    def _read(self, e: Entry, cache: dict) -> bytes:
        f = cache.get(e.seg)
        if f is None:
            f = cache[e.seg] = open(self.seg_path(e.seg), "rb")
        f.seek(e.offset)
        return f.read(e.length)

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    @property
    def ckpt_dir(self) -> Path:
        return self.dir / "checkpoints"

    def disk_size(self) -> int:
        """The record and the checkpoint files (also a temporary one being written): what the run takes on the disk
        (the quota counts it)."""
        try:
            rec = sum(p.stat().st_size for p in self.dir.glob("stream*.lfrec"))
            # the checkpoints and the states carried into new worlds (lfviz.playground.store_carry; review LB1-F5)
            return rec + sum(p.stat().st_size for p in self.ckpt_dir.glob("w*-*.*")) \
                + sum(p.stat().st_size for p in self.ckpt_dir.glob("carry-w*-*.npz*"))
        except OSError:
            return self.size

    def touch(self):
        """The run's last action (a viewer came or left, a command): removal after ``keep_days`` counts from it. Saved
        at once when no worker saves the meta (review C1-9: a visit to a suspended run was lost at a restart)."""
        self.meta["last_action"] = time.time()
        self.meta["last_action_iso"] = _now_iso()
        if not self.running:
            self.save_meta()

    def save_meta(self):
        self.meta["size"] = self.size
        self.meta["n_messages"] = len(self.entries)
        tmp = self.dir / "meta.json.tmp"
        tmp.write_text(json.dumps(self.meta, ensure_ascii=False, indent=1))
        tmp.replace(self.dir / "meta.json")

    def summary(self) -> dict:
        m = self.meta
        return {
            "id": self.id, "viz": self.viz_id, "title": m.get("title"), "state": m.get("state"),
            "created": m.get("created"), "ended": m.get("ended"), "sim_t": m.get("sim_t", 0.0),
            "playing": m.get("playing", False), "speed": m.get("speed"), "viewers": len(self.viewers),
            "size": self.disk_size(), "keep": m.get("keep", False), "preset": m.get("preset"), "seed": m.get("seed"),
            "restorable": bool(m.get("restorable")), "last_action": m.get("last_action_iso"),
            "resume_error": m.get("resume_error"),
            "modifications": m.get("modifications", []), "approximations": m.get("approximations", []),
            "label": m.get("label", ""), "devices_override": bool((m.get("backend_settings") or {}).get("override")),
            "n_worlds": max(1, len(m.get("worlds", []))), "scene": m.get("scene", ""),
            "kind": m.get("kind", "demo"), "recording": bool((m.get("buffer") or {}).get("recording")),
            # why a run has no world (its first world was refused): shown in the run list (review UX-params P1)
            "error": (m.get("errors") or [None])[-1] if m.get("state") == "failed" else None,
            "busy": self.busy,
        }

    # --- recording and broadcast ------------------------------------------------------------------------
    def _note_header(self, meta: dict, wall: str):
        """A world starts (the first, or a new world inside this run): the passport's list of worlds and the latest
        world's parameters."""
        self.meta["modifications"] = meta.get("modifications", [])
        self.meta["approximations"] = meta.get("approximations", [])  # approximations flagged by the world
        self.meta["scene"] = meta.get("title", "")
        worlds = self.meta.setdefault("worlds", [])
        n = int(meta.get("world", len(worlds) + 1))
        if not any(w.get("n") == n for w in worlds):
            worlds.append({"n": n, "wall": wall, "scene": meta.get("title", ""),
                           "preset": meta.get("preset"), "seed": meta.get("seed"),
                           "params": meta.get("params"), "modifications": meta.get("modifications", []),
                           "approximations": meta.get("approximations", [])})
        if meta.get("params") is not None:
            self.meta["params"] = meta["params"]
            self.meta["seed"] = meta.get("seed", self.meta.get("seed"))
            self.meta["preset"] = meta.get("preset")

    def _ingest(self, msg: bytes):
        if self.cancelling:  # a cancel was decided: the command's output (and anything after) never happened
            return
        meta = protocol.peek_meta(msg)
        typ = meta.get("type")
        is_frame = typ == "frame"
        if typ == "busy":
            self.busy = {k: meta.get(k) for k in ("cmd", "what", "wall", "t")} if meta.get("on") else None
            if not meta.get("on"):
                self.busy_sent = []
        if typ in NOT_RECORDED:
            for v in list(self.viewers):
                v.offer(msg, False)
            return
        if typ == "record_segment" and self.buffered:
            self._new_segment(meta)
        if is_frame and self.buffered:  # the window counts the time the world was shown computing (review B6-F10)
            now = time.time()
            if 0.0 < now - self.last_frame_wall < 1.0 and self.meta["buffer"].get("segs"):
                sg = self.meta["buffer"]["segs"][-1]
                sg["play_s"] = sg.get("play_s", 0.0) + (now - self.last_frame_wall)
            self.last_frame_wall = now
        self.file.write(struct.pack("<I", len(msg)))
        self.file.write(msg)
        self.file.flush()
        self.entries.append(_entry(self.size + 4, msg, meta, self.seg))
        self.size += 4 + len(msg)
        if typ == "header" and self.buffered:
            self._keep_header(int(meta.get("world", 1)), msg)
        if "t" in meta and meta["t"] is not None:
            self.meta["sim_t"] = meta["t"]
        if typ == "state":
            self.meta["playing"] = meta.get("playing", False)
            self.meta["speed"] = meta.get("speed")
            if self.rebuilding and meta.get("reason") == "start":  # the resumed world is rebuilt and goes on
                self.rebuilding = False
                self.unapplied = []
                self.meta.pop("resume_error", None)
        elif typ == "header":
            self._note_header(meta, _now_iso())
            self.save_meta()  # a crash right after a new world must not resume the previous one (review C1-16)
        elif typ == "error":
            errs = self.meta.setdefault("errors", [])
            text = meta.get("text", "")
            errs.append(text if is_t(text) else str(text)[:2000])  # a text (T) stays one: the player renders it
            del errs[:-200]  # the passport keeps the latest 200 (review B6-F6)
            self.meta["n_errors"] = int(self.meta.get("n_errors", len(errs) - 1)) + 1  # all, for the slice below
        elif typ == "end" and meta.get("reason") == "world not built":  # its first world failed to show itself (P3)
            self.meta["not_built"] = True
        elif typ == "resumed" and self.meta.get("resumes"):  # how the worker actually continued (review CK-11)
            self.meta["resumes"][-1]["from"] = meta.get("how")
        elif isinstance(meta.get("approximations"), list):  # the world's approximations in force changed (review C11)
            self.meta["approximations"] = meta["approximations"]
        for v in list(self.viewers):
            v.offer(msg, is_frame)

    async def read_worker(self):
        assert self.proc is not None
        try:
            while True:
                head = await self.proc.stdout.readexactly(4)
                (n,) = struct.unpack("<I", head)
                self._ingest(await self.proc.stdout.readexactly(n))
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        rc = await self.proc.wait()
        st = self.meta.get("state")
        by_server = st in ("stopped", "suspended")
        if self.rebuilding:  # the worker ended before its world was rebuilt
            if self.unapplied:  # review C1-2: say which changes were accepted but never applied
                self._ingest(protocol.encode({"type": "error", "t": self.meta.get("sim_t", 0.0), "text": T(
                    "Not applied (the run was suspended while the world was recomputed along the record): {cmds}. "
                    "Repeat after ⏺.", cmds=", ".join(map(str, self.unapplied)))}))
            if not by_server:  # the rebuild failed: why, for the player (⏺ tries again)
                k = int(self.meta.get("n_errors", 0)) - self.n_errors_at_resume
                new = self.meta.get("errors", [])[-k:] if k > 0 else []
                last = new[-1] if new else T("the worker exited with code {code}", code=rc)
                self.meta["resume_error"] = last if is_t(last) else str(last)[:500]
        self.rebuilding = False
        self.unapplied = []
        self.busy = None
        self.file.close()
        if not by_server:
            # a worker that ended by itself: a restorable record of a world is whole and can be continued (review
            # C1-14); one whose first world was never built has nothing to continue
            if self.meta.get("restorable") and any(e.kind == "header" for e in self.entries) \
                    and not self.meta.get("not_built"):
                self.meta["state"] = "suspended"
                self.meta["stop_reason"] = "worker ended" if rc == 0 else f"worker failed (code {rc})"
            else:
                self.meta["state"] = "finished" if rc == 0 else "failed"
        self.meta["ended"] = _now_iso()
        self.meta["returncode"] = rc
        self.meta["playing"] = False
        self.save_meta()
        for v in list(self.viewers):
            v.offer(protocol.encode({"type": "closed", "state": self.meta["state"],
                                     "resume_error": self.meta.get("resume_error")}), False)

    async def send_history(self, ws, n: int):
        """Send record entries [0, n): all accumulative messages, frames thinned to HISTORY_FRAMES."""
        entries = self.entries[:n]
        n_frames = sum(1 for e in entries if e.is_frame)
        stride = max(1, -(-n_frames // HISTORY_FRAMES))
        last_frame = max((i for i, e in enumerate(entries) if e.is_frame), default=-1)
        # the stride first: the player counts each frame replayed as `stride` frames, so the history it keeps stays
        # uniform when the live frames are added (review C1-12)
        await ws.send_bytes(protocol.encode({"type": "history_start", "frame_stride": stride,
                                             **({"buffer": self.buffer_state()} if self.buffered else {})}))
        cache: dict = {}
        self.readers += 1
        try:
            k = 0
            world_sent, seg_prev = None, None  # a buffer: a world's header goes before its first kept message
            for i, e in enumerate(entries):
                if self.buffered and e.seg != seg_prev:
                    seg_prev = e.seg
                    w = self._world_of_seg(e.seg)
                    if e.kind != "header" and w != world_sent and w in self.headers:
                        await ws.send_bytes(self.headers[w])
                        world_sent = w
                if e.kind == "header":
                    world_sent = protocol.peek_meta(self._read(e, cache)).get("world", 1)
                if e.is_frame:
                    keep = (k % stride == 0) or i == last_frame
                    k += 1
                    if not keep:
                        continue
                await ws.send_bytes(self._read(e, cache))
        finally:
            self.readers -= 1
            for f in cache.values():
                f.close()
        has_world = (bool(self.headers) or any(e.kind == "header" for e in self.entries)) and not self.meta.get("not_built")
        await ws.send_bytes(protocol.encode({"type": "history_end", "n": n, "live": self.running,
                                             "state": self.meta.get("state"), "rebuilding": self.rebuilding,
                                             "resume_error": self.meta.get("resume_error"),
                                             # a run whose first world was refused has nothing to continue, and the
                                             # player says why (review UX-params P1)
                                             "start_error": None if has_world else (self.meta.get("errors") or [None])[-1],
                                             "resumable": bool(self.meta.get("restorable")) and has_world
                                             and self.meta.get("state") in ("suspended", "running")}))
        if self.busy:  # computing now: the viewer shows it, with how long it has been at it (review UX-ui U9)
            b = self.busy
            await ws.send_bytes(protocol.encode({"type": "busy", "on": True, **b,
                                                 "elapsed": max(0.0, time.time() - float(b.get("wall") or time.time()))}))

    def add_viewer(self, ws) -> Viewer:
        v = Viewer(ws, self, len(self.entries))
        self.viewers.add(v)
        self.meta["last_viewed"] = _now_iso()
        self.touch()
        return v

    def remove_viewer(self, v: Viewer):
        v.alive = False
        v.q.put_nowait((None, False))
        self.viewers.discard(v)
        self.last_viewer_time = time.monotonic()
        self.touch()

    def command(self, cmd: dict, source: str = "", first: bool = False):
        """Forward a command to the worker. While a resumed world is being rebuilt, a world-changing command is refused
        unless it is the one that resumed the run (``first``): it could be applied only after the rebuild and would
        be lost if the run were suspended meanwhile (review C1-2)."""
        if not self.running:
            raise RuntimeError(T("the run is not running"))
        name = cmd.get("cmd")
        if self.rebuilding and name in WORLD_COMMANDS and not first:
            raise RuntimeError(T("the world is still being restored: the change was not accepted — repeat it when "
                                 "the record resumes"))
        line = json.dumps({"cmd": name, "args": cmd.get("args") or {}}, ensure_ascii=False)
        self.proc.stdin.write(line.encode() + b"\n")
        if self.busy and name in WORLD_COMMANDS:
            self.busy_sent.append(name)
        if self.rebuilding and name in WORLD_COMMANDS:
            self.unapplied.append(name)
        log = self.meta.setdefault("commands", [])
        if len(log) < 20000:
            log.append({"wall": _now_iso(), "from": source, "cmd": name, "args": cmd.get("args") or {}})
        self.touch()

    async def command_resuming(self, cmd: dict, source: str = ""):
        """A command from a viewer: a suspended run is resumed first when the command asks it to compute or to change
        the world (the command then follows the rebuild); a pause or a speed for a suspended run is kept as the next
        start's setting. A command that arrives while the run is being suspended waits for the suspension to end and
        then resumes it (review CK-4: it was acknowledged and lost)."""
        if cmd.get("cmd") == "cancel":  # the server's own command: stop what the worker is computing (U9)
            await self.cancel(source)
            return
        if self.stopping:
            async with self.lock:
                pass
        if not self.running:
            if cmd.get("cmd") in RESUMING:
                if await self.mgr.resume(self, first=cmd, source=source):
                    return
            else:
                if cmd.get("cmd") == "speed":
                    self.meta["speed"] = (cmd.get("args") or {}).get("value", self.meta.get("speed"))
                    self.touch()
                return
        self.command(cmd, source)

    CANCEL_TEXT = {"scene": T("a change of the scene"), "set": T("a change of the set-up"), "action": T("an action"),
                   "view": T("a slice"), "new_world": T("a new world"), "step": T("a step"),
                   "next_event": T("the computation up to an event")}

    async def cancel(self, source: str = "") -> dict:
        """Cancel the computing command the worker is busy with (review UX-ui U9: a scene change could block a world
        for minutes with no way out). The worker holds a command's messages until it is done and announces the end
        first ("busy off", ``lfviz.worker.Output``), so a command not finished when the cancel is decided has left
        nothing in the record: the worker is ended, everything it writes from then on is dropped, and the run is
        resumed from its record — the world as it was just before the command (its last checkpoint and the record
        after it). Refused (RuntimeError) when the worker computes nothing (the command was already done)."""
        async with self.lock:
            b = self.busy
            if not self.running or not b or b.get("cmd") == "build":
                raise RuntimeError(T("nothing to cancel: the world is computing nothing now (the change is already "
                                     "applied)"))
            if self.rebuilding:
                raise RuntimeError(T("the world is still being restored: a change can be cancelled, not the "
                                     "restoration"))
            sent = list(self.busy_sent)
            self.cancelling = True
            self.meta["state"] = "suspended"
            self.meta["stop_reason"] = "cancel"
            try:
                self.proc.kill()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(self.proc.wait(), 10.0)
            except asyncio.TimeoutError:
                pass
            if self._reader is not None:
                try:
                    await asyncio.wait_for(asyncio.shield(self._reader), 10.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            self.cancelling = False
            self.busy = None
            self.busy_sent = []
            for v in list(self.viewers):
                v.offer(protocol.encode({"type": "busy", "on": False, "cancelled": True}), False)
        what = b.get("what") or self.CANCEL_TEXT.get(b.get("cmd"), b.get("cmd") or T("the computation"))
        if sent:
            text = T("Cancelled: {what}. The world is back at the moment before this command (it was not applied) "
                     "and continues from it, paused; the commands sent during the computation were not applied either: "
                     "{cmds}", what=what, cmds=", ".join(map(str, sent)))
        else:
            text = T("Cancelled: {what}. The world is back at the moment before this command (it was not applied) "
                     "and continues from it, paused", what=what)
        log = self.meta.setdefault("commands", [])
        log.append({"wall": _now_iso(), "from": source, "cmd": "cancel", "args": {"cancelled": b}})
        try:
            await self.mgr.resume(self)
        except (RuntimeError, OverflowError) as e:
            text = T("{text}. It could not be resumed at once ({why}); ⏺ will try again", text=text, why=text_of(e))
        self._ingest(protocol.encode({"type": "notice", "t": self.meta.get("sim_t", 0.0), "text": text}))
        return {"ok": True, "cancelled": b}

    def _latest_world(self) -> dict:
        """The latest world as the record has it: its header (parameters, seed, preset, number, the view it took
        over), the run's first seed, what it went through since its header in order — every frame's time (an advance
        of the frame clock) and every world-changing command with its time, what a restore repeats — and the world
        time it reached (the latest time of its messages). The record, not ``meta.json``, which a crash can leave
        stale (review C1-16)."""
        heads = [i for i, e in enumerate(self.entries) if e.kind == "header"]
        if not heads and not self.headers:
            raise RuntimeError(T("the record holds no world: there is nothing to resume"))
        script = []
        ckpt, ckpt_at = None, 0  # the last usable checkpoint of this world and its place in the script
        env = CK.runtime_env()
        root = registry.ROOT.parent
        cache: dict = {}
        try:
            def meta_of(e):
                return protocol.peek_meta(self._read(e, cache))
            segs = (self.meta.get("buffer") or {}).get("segs") or []
            if heads and (not self.headers or meta_of(self.entries[heads[-1]]).get("world", 1) >= max(self.headers)):
                head = heads[-1]
                header = meta_of(self.entries[head])
                # complete: every segment from the header's on is still kept (a protected stretch, then a trimmed
                # one, leaves a hole: the commands in it are gone — review B6-F1)
                ks = sorted(sg["k"] for sg in segs if sg["k"] >= self.entries[head].seg)
                complete = not segs or ks == list(range(self.entries[head].seg, self.entries[head].seg + len(ks)))
            else:  # a buffer whose latest world began before the kept window: its header from the store
                header = protocol.peek_meta(self.headers[max(self.headers)])
                head = -1
                complete = False
            # only this world's entries (an earlier world's protected segments may be kept before them: review B6-F3)
            latest = int(header.get("world", 1))
            seg_world = {sg["k"]: int(sg.get("world", 1)) for sg in segs}
            first_h = self.headers.get(min(self.headers)) if self.headers else None
            first = (protocol.peek_meta(first_h) if first_h is not None
                     else header if not heads or heads[0] == head else meta_of(self.entries[heads[0]]))
            t_end = float(header.get("t") or 0.0)
            for e in self.entries[head + 1:]:
                if head < 0 and seg_world.get(e.seg, latest) != latest:
                    continue
                if e.t is not None:
                    t_end = max(t_end, e.t)
                if e.is_frame:
                    if e.t is not None:
                        script.append({"frame": e.t})
                elif e.kind == "command":
                    m = meta_of(e)
                    script.append({"t": m.get("t", 0.0), "cmd": m.get("cmd"), "args": m.get("args") or {}})
                elif e.kind == "checkpoint":
                    # usable: a proper name in this run's folder, the same world, the code files the world ran
                    # unchanged and the same runtime (review CK-5, CK-10)
                    m = meta_of(e)
                    name = str(m.get("file") or "")
                    path = self.ckpt_dir / name
                    if (CK.NAME.match(name) and not m.get("error") and m.get("world") == header.get("world", 1)
                            and isinstance(m.get("files"), list) and m.get("env") == env and path.is_file()
                            and CK.files_hash(root, m["files"]) == m.get("code")):
                        ckpt, ckpt_at = {"file": str(path), "t": m.get("t")}, len(script)
        finally:
            for f in cache.values():
                f.close()
        if ckpt is not None:
            ckpt["commands"] = script[ckpt_at:]
        return {"header": header, "seed0": first.get("seed"), "script": script, "t_end": t_end, "checkpoint": ckpt,
                "complete": complete}

    def _cut_to_index(self):
        """Make the file end where the index ends before anything is appended (a tail cut by a crash would otherwise
        swallow the new messages: review C1-10)."""
        sp = self.seg_path(self.seg)
        if sp.stat().st_size != self.size:
            with open(sp, "r+b") as f:
                f.seek(self.size)
                tail = f.read()
                f.truncate(self.size)
            with open(self.dir / "stream.cut-tail.bin", "ab") as f:
                f.write(tail)

    # --- a playground's buffer: the record as a moving window --------------------------------------------------
    def buffer_state(self) -> dict:
        b = self.meta.get("buffer") or {}
        segs = b.get("segs") or []
        return {"window_s": b.get("window_s"), "window_mb": b.get("window_mb"), "recording": bool(b.get("recording")),
                "kept_from_t": segs[0]["t0"] if segs else None, "trimmed": bool(b.get("trimmed")),
                "protected": b.get("protected") or [], "size": self.disk_size()}

    def _world_of_seg(self, k: int) -> int:
        for sg in (self.meta.get("buffer") or {}).get("segs") or []:
            if sg["k"] == k:
                return int(sg.get("world", 1))
        return max(self.headers) if self.headers else 1

    def _keep_header(self, world: int, msg: bytes):
        """A world's header kept apart (it must survive the segment it was written in)."""
        self.headers[world] = msg
        with open(self.dir / "headers.lfrec", "ab") as f:
            f.write(struct.pack("<I", len(msg)) + msg)

    def _new_segment(self, meta: dict):
        """Close the segment being written and open the next one at a ``record_segment`` marker (it is followed by
        the scene and the checkpoint: the new segment is drawable on its own), then drop what left the window."""
        b = self.meta["buffer"]
        segs = b.setdefault("segs", [])
        if not segs or self.size > len(protocol.MAGIC):  # an empty segment is reused
            self.file.close()
            self.seg += 1
            self.file = open(self.seg_path(self.seg), "wb")
            self.file.write(protocol.MAGIC)
            self.file.flush()
            self.size = len(protocol.MAGIC)
            segs.append({"k": self.seg, "wall0": time.time(), "t0": meta.get("t"), "world": int(meta.get("world", 1))})
        if b.get("recording"):
            self._protect(self.seg, None)
        self._trim()
        self.save_meta()

    def _protect(self, k_from: int, k_to):
        """Keep segments k_from..k_to (None: open) for good."""
        prot = self.meta["buffer"].setdefault("protected", [])
        if prot and prot[-1][1] is None:
            return
        prot.append([k_from, k_to])

    def _protected(self, k: int) -> bool:
        return any(a <= k and (b is None or k <= b) for a, b in (self.meta["buffer"].get("protected") or []))

    def _trim(self):
        """Delete the oldest segments that left the window, never a protected one nor the newest two (the latest
        complete segment and the one being written). The window's time is the time the world was shown computing
        (frames flowing), not the wall clock: a pause or a suspension does not age the record (review B6-F10); its
        size counts the unprotected segments and the checkpoint files (B6-F21). Not while a history or a download
        reads the segments (B6-F9): the next segment's start trims."""
        b = self.meta["buffer"]
        segs = b.get("segs") or []
        if len(segs) <= 2 or self.readers:
            return
        sizes = {sg["k"]: (self.seg_path(sg["k"]).stat().st_size if self.seg_path(sg["k"]).is_file() else 0)
                 for sg in segs}
        ck = sum(f.stat().st_size for f in self.ckpt_dir.glob("*") if f.is_file()) if self.ckpt_dir.is_dir() else 0
        total = ck + sum(sizes[sg["k"]] for sg in segs if not self._protected(sg["k"]))
        window_s = float(b.get("window_s") or BUFFER_DEFAULT["window_s"])
        drop = set()
        for i, sg in enumerate(segs[:-2]):
            if self._protected(sg["k"]):
                continue
            later = sum(float(q.get("play_s", 0.0)) for q in segs[i + 1:])  # the segments after it cover the window
            if later >= window_s or total > float(b.get("window_mb") or BUFFER_DEFAULT["window_mb"]) * 2 ** 20:
                drop.add(sg["k"])
                total -= sizes[sg["k"]]
        if not drop:
            return
        for k in drop:
            if k == 0:  # the first segment is the record's main file: emptied, not removed
                self.seg_path(0).write_bytes(protocol.MAGIC)
            else:
                self.seg_path(k).unlink(missing_ok=True)
        self.entries = [e for e in self.entries if e.seg not in drop]
        b["segs"] = [sg for sg in segs if sg["k"] not in drop]
        b["trimmed"] = True
        self._offer_state()

    def set_recording(self, on: bool | None, window_s=None, window_mb=None) -> dict:
        """Recording switched on (owner, 2026-10-29): what the buffer holds now and everything from now on is kept for
        good; off: the record goes on as a moving window again (what was kept stays). The window's length can be
        changed at the same time."""
        if not self.buffered:
            raise RuntimeError(T("this run is recorded whole: only a laboratory has a record window"))
        b = self.meta["buffer"]
        if window_s is not None:
            w = float(window_s)
            if not 30 <= w <= 86400:
                raise ValueError(T("the record window: from 30 s to a day"))
            b["window_s"] = w
        if window_mb is not None:
            w = float(window_mb)
            if not 16 <= w <= 65536:
                raise ValueError(T("the record window: from 16 MB to 64 GB"))
            b["window_mb"] = w
        if on is None:
            on = bool(b.get("recording"))
        if on and not b.get("recording"):
            first = min((sg["k"] for sg in b.get("segs") or []), default=self.seg)
            prot = b.setdefault("protected", [])
            if prot and prot[-1][1] is not None and prot[-1][1] >= first - 1:
                prot[-1][1] = None  # the range kept last time goes on (no overlapping ranges: review B6-F24)
            else:
                prot.append([first, None])
            b["recording"] = True
        elif not on and b.get("recording"):
            prot = b.get("protected") or []
            if prot and prot[-1][1] is None:
                prot[-1][1] = self.seg
            b["recording"] = False
        st = self._offer_state()
        self.save_meta()
        return st

    def _offer_state(self) -> dict:
        """The record's state now, to every viewer (not recorded: it is the run's, not the world's; review B6-F11)."""
        st = self.buffer_state()
        msg = protocol.encode({"type": "record_state", "t": self.meta.get("sim_t", 0.0), **st})
        for v in list(self.viewers):
            v.offer(msg, False)
        return st

    async def suspend(self, reason: str = "user"):
        """Release the worker; the record stays and the run can be resumed (``RunManager.resume``): the worker writes
        a checkpoint of its world first, so that the run continues from this very state."""
        await self.stop(reason, state="suspended" if self.meta.get("restorable") else "stopped")

    async def stop(self, reason: str = "user", state: str = "stopped"):
        async with self.lock:
            await self._stop(reason, state)

    async def _stop(self, reason: str, state: str):
        if not self.running:
            return
        self.stopping = True
        try:
            await self._stop_worker(reason, state)
        finally:
            self.stopping = False

    async def _stop_worker(self, reason: str, state: str):
        self.meta["state"] = state
        self.meta["stop_reason"] = reason
        keep_state = state == "suspended"  # a suspended world is checkpointed on its way out (it continues from it)
        try:
            self.command({"cmd": "stop", "args": {"checkpoint": True} if keep_state else {}}, "server")
            await self.proc.stdin.drain()
            self.proc.stdin.close()
        except (RuntimeError, ConnectionError):
            pass
        try:
            await asyncio.wait_for(self.proc.wait(), 60.0 if keep_state else 5.0)
        except asyncio.TimeoutError:
            self.proc.terminate()
            try:
                await asyncio.wait_for(self.proc.wait(), 3.0)
            except asyncio.TimeoutError:
                self.proc.kill()
        if self._reader is not None:  # the record, its file and the meta are final before the lock is released
            try:
                await asyncio.wait_for(asyncio.shield(self._reader), 10.0)  # never cancels the reader
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass


class RunManager:
    def __init__(self, runs_dir: Path, max_workers: int = 3, keep_days: float = 3.0, quota_gb: float = 5.0,
                 idle_pause: float = 60.0, idle_suspend: float = 1800.0, worker_mem_gb: float | None = None):
        self.dir = Path(runs_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        # every worker's memory budget, its hard limit (review UX-params P8: one world took 31 GB of the shared host)
        self.worker_mem = (int(worker_mem_gb * limits.GIB) if worker_mem_gb and worker_mem_gb > 0
                           else limits.default_budget(max_workers))
        self.keep_days = self._saved_keep_days(keep_days)  # the period set on the page wins over the default
        self.quota_gb = quota_gb
        self.idle_pause = idle_pause
        self.idle_suspend = idle_suspend
        self.runs: dict[str, Run] = {}
        self.viz_cache: dict[str, dict] = {}
        self._slots = asyncio.Lock()
        self._load_existing()

    # --- visualizations -------------------------------------------------------------------------------
    def viz(self, viz_id: str) -> dict:
        if viz_id not in self.viz_cache:
            self.viz_cache[viz_id] = registry.load(viz_id)
        return self.viz_cache[viz_id]

    # --- existing records -----------------------------------------------------------------------------
    def _load_existing(self):
        for d in sorted(self.dir.iterdir()):
            try:
                run = self._load_one(d)
            except Exception as e:  # noqa: BLE001 - one unreadable record must not keep the server down (review C1-10)
                print(f"lfviz: record {d.name} skipped: {type(e).__name__}: {e}", file=sys.stderr)
                continue
            if run is not None:
                self.runs[run.id] = run

    def _load_one(self, d: Path) -> Run | None:
        mp = d / "meta.json"
        sp = d / "stream.lfrec"
        if not (d.is_dir() and mp.is_file() and sp.is_file()):
            return None
        try:
            meta = json.loads(mp.read_text(), object_hook=json_hook)  # texts back as T (review i18n-code F2)
        except (OSError, json.JSONDecodeError):
            return None
        if meta.get("state") in ("running", "starting"):
            # the server stopped under it: a restorable run is resumed when asked, an older one stays a record
            meta["state"] = "suspended" if meta.get("restorable") else "interrupted"
            meta["playing"] = False
        if meta.get("last_action") is None:  # a record from before the last action was kept: its record's time
            meta["last_action"] = sp.stat().st_mtime
            meta["last_action_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(meta["last_action"]))
        run = Run(self, d.name, meta.get("viz", ""), meta, d)
        for tmp in [*run.ckpt_dir.glob("w*-*.tmp"), *run.ckpt_dir.glob("carry-w*-*.npz.tmp")]:  # a write cut (CK-8)
            tmp.unlink(missing_ok=True)
        segs = [0]
        if run.buffered:  # a playground's buffer: the kept segments in order, the worlds' headers kept apart
            segs = sorted({0} | {int(sg["k"]) for sg in meta["buffer"].get("segs") or []})
            hp = d / "headers.lfrec"
            if hp.is_file():
                for _, msg in protocol.iter_stream(hp.read_bytes(), 0):
                    try:
                        run.headers[int(protocol.peek_meta(msg).get("world", 1))] = msg
                    except Exception:  # noqa: BLE001 - a header cut by a crash: the record's own copy serves
                        break
        sim_t = None
        for k in segs:
            path = run.seg_path(k)
            if not path.is_file():
                continue
            data = path.read_bytes()
            if not data.startswith(protocol.MAGIC):
                raise ValueError("not a record (no magic)")
            end = len(protocol.MAGIC)
            for off, msg in protocol.iter_stream(data, end):
                try:
                    pm = protocol.peek_meta(msg)
                except Exception:  # noqa: BLE001 - garbage (zeros after a power cut): the record ends before it
                    break
                run.entries.append(_entry(off + 4, msg, pm, k))
                end = off + 4 + len(msg)
                if pm.get("type") == "header":  # the record is the truth: meta.json may have missed a new world
                    run._note_header(pm, meta.get("ended") or meta.get("created") or "")
                    if run.buffered:
                        run.headers.setdefault(int(pm.get("world", 1)), msg)
                elif pm.get("type") != "error" and isinstance(pm.get("approximations"), list):
                    meta["approximations"] = pm["approximations"]
                if isinstance(pm.get("t"), (int, float)):
                    sim_t = pm["t"]
            run.seg, run.size = k, end
            if end < len(data):  # a message cut by a crash: kept apart, the record cut back to its last whole message
                run._cut_to_index()
                meta["cut_tail_bytes"] = meta.get("cut_tail_bytes", 0) + len(data) - end
        if sim_t is not None:
            meta["sim_t"] = sim_t
        run.save_meta()
        return run

    # --- lifecycle ------------------------------------------------------------------------------------
    def n_running(self) -> int:
        return sum(1 for r in self.runs.values() if r.running)

    async def start(self, viz_id: str, preset: str | None, values: dict | None, seed: int | None,
                    label: str = "", source: str = "", backend: dict | None = None,
                    backend_notes: list | None = None) -> Run:
        async with self._slots:  # a free worker is taken by one start or resume at a time (review C1-1)
            return await self._start(viz_id, preset, values, seed, label, source, backend, backend_notes)

    async def _start(self, viz_id, preset, values, seed, label, source, backend, backend_notes) -> Run:
        await self._make_room()
        viz = self.viz(viz_id)
        params, errors = viz["schema"].resolve(preset, values)
        if errors:
            e = ValueError(join(errors, "; "))
            e.fields = {er.pid: er for er in errors if getattr(er, "pid", None)}  # the form marks these fields
            raise e
        if viz.get("kind") == "playground" and params.get("scene"):  # before a worker is spawned (review B6-F17)
            from .playground import check_scene
            check_scene(params["scene"], viz_id)
        # what the world says about these parameters before it is built: a refused combination, the memory it needs
        # (review UX-params P1, P8): the catalogue shows the reason on the form, nothing is started
        sim_cls = viz["simulation"]
        if hasattr(sim_cls, "check_params"):
            sim_cls.check_params(params)
        limits.check_estimate(sim_cls, params, budget=self.worker_mem)
        if seed is None:
            seed = secrets.randbelow(2**31)
        rid = time.strftime("%Y%m%d-%H%M%S") + "-" + viz_id.split("_")[0] + "-" + secrets.token_hex(2)
        d = self.dir / rid
        d.mkdir(parents=True)
        meta = {
            "id": rid, "viz": viz_id, "title": viz["title"], "version": viz.get("version", ""),
            "code": registry.code_hash(viz_id), "preset": preset, "params": params, "seed": seed,
            "label": label, "created": _now_iso(), "state": "starting", "keep": False,
            "modifications": viz["schema"].modifications(params), "started_from": source,
            "python": sys.version.split()[0],
            "backend_settings": devices.load() if backend is None else backend,
            "backend_notes": list(backend_notes or []), "restorable": True,
        }
        if viz.get("kind") == "playground":  # the record as a moving window (owner, 2026-10-29)
            meta["kind"] = "playground"
            meta["buffer"] = {**BUFFER_DEFAULT, "recording": False, "protected": [],
                              "segs": [{"k": 0, "wall0": time.time(), "t0": 0.0, "world": 1}]}
        run = Run(self, rid, viz_id, meta, d)
        run.touch()
        run.file = open(run.stream_path, "wb")
        run.file.write(protocol.MAGIC)
        run.file.flush()
        await self._spawn(run, {"params": params, "seed": seed, "preset": preset, "backend": meta["backend_settings"]})
        self.runs[rid] = run
        return run

    async def _make_room(self):
        """Free a worker when all are busy: suspend the run idle longest without viewers (never one whose world is
        being rebuilt)."""
        if self.n_running() < self.max_workers:
            return
        idle = [r for r in self.runs.values() if r.running and not r.viewers and not r.rebuilding]
        if not idle:
            raise OverflowError(T("all {n:d} workers are busy with open runs: close the tab of one of them (it will be "
                                  "suspended and resume when you open it again)", n=self.max_workers))
        await min(idle, key=lambda r: r.last_viewer_time).suspend("room for another run")

    async def resume(self, run: Run, first: dict | None = None, source: str = "") -> bool:
        """Rebuild a suspended run's world from its record and let it compute again; ``first`` (the command that
        asked for it) follows the rebuild. False when the run was running already (another viewer resumed it): one
        worker per run, whoever asks at the same moment (review C1-1)."""
        async with run.lock:
            if run.running:
                return False
            if not run.meta.get("restorable"):
                raise RuntimeError(T("this record was made before the version that can continue runs: start a new run "
                                     "with the same parameters (the “▶ Start a new world” button or the catalogue)"))
            w = run._latest_world()
            header, script, t_end, ckpt = w["header"], w["script"], w["t_end"], w["checkpoint"]
            if ckpt is None and not w["complete"]:
                raise RuntimeError(T("it cannot be resumed: the saved state does not fit (the code or the libraries' versions "
                                     "changed), and the world's start has already left the record's window — there "
                                     "is nothing to recompute it from. Start the world again from a scene file or a "
                                     "scenario"))
            async with self._slots:
                await self._make_room()
                run._cut_to_index()
                run.file = open(run.seg_path(run.seg), "ab")
                code = registry.code_hash(run.viz_id)
                prev = (run.meta.get("resumes") or [{}])[-1].get("code") or run.meta.get("code")
                n_cmd = sum(1 for c in script if "cmd" in c)
                if ckpt is not None:
                    text = T("Resuming from the world's saved state at t = {t:.6g} s…", t=ckpt["t"])
                elif code != prev:
                    text = T("Resuming: the world is recomputed from its start along the record up to t = {t:.6g} s "
                             "({n:d} changes of the set-up)… The visualization's code changed since last time: the "
                             "continuation is computed by the new version, the earlier part of the record by the old "
                             "one", t=t_end, n=n_cmd)
                else:
                    text = T("Resuming: the world is recomputed from its start along the record up to t = {t:.6g} s "
                             "({n:d} changes of the set-up)…", t=t_end, n=n_cmd)
                run._ingest(protocol.encode({"type": "notice", "t": t_end, "text": text}))
                init = {"params": header.get("params") or run.meta.get("params"), "seed": header.get("seed", 0),
                        "seed0": w["seed0"], "preset": header.get("preset"),
                        "backend": run.meta.get("backend_settings"),
                        "restore": {"world": header.get("world", 1), "commands": script, "t_end": t_end,
                                    "adopted_view": header.get("adopted_view"), "checkpoint": ckpt,
                                    "complete": bool(w["complete"])}}
                run.rebuilding = True
                run.unapplied = []
                run.n_errors_at_resume = int(run.meta.get("n_errors", len(run.meta.get("errors", []))))
                run.last_viewer_time = time.monotonic()  # idleness counts from now (review C1-2)
                try:
                    await self._spawn(run, init)
                except BaseException:
                    run.rebuilding = False
                    run.file.close()
                    raise
            run.meta["resumed"] = run.meta.get("resumed", 0) + 1
            run.meta.setdefault("resumes", []).append({"wall": _now_iso(), "t": t_end, "code": code,
                                                       "from": "checkpoint" if ckpt is not None else "replay"})
            if run.meta.get("speed"):  # the speed the run had (or was given while suspended)
                run.command({"cmd": "speed", "args": {"value": run.meta["speed"]}}, "server")
            if first is not None:
                run.command(first, source, first=True)
            return True

    async def _spawn(self, run: Run, init: dict):
        meta, d, viz_id = run.meta, run.dir, run.viz_id
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(registry.SERVER), str(registry.ROOT), str(registry.ENGINE)])
        env.setdefault("OMP_NUM_THREADS", "2")
        env.setdefault("OPENBLAS_NUM_THREADS", "2")
        env[limits.ENV] = str(self.worker_mem)  # the worker's hard memory limit (lfviz.limits; review UX-params P8)
        init = {**init, "checkpoints": {"dir": str(run.ckpt_dir), "code": registry.code_hash(viz_id)}}
        log = open(d / "worker.log", "ab")  # appended: a resumed run keeps the earlier workers' diagnostics
        run.proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "lfviz.worker", "--viz", viz_id,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=log, env=env,
            cwd=str(registry.ROOT))
        log.close()
        run.proc.stdin.write((json.dumps(init) + "\n").encode())
        await run.proc.stdin.drain()
        meta["state"] = "running"
        meta["pid"] = run.proc.pid
        run.save_meta()
        run._reader = asyncio.create_task(run.read_worker())

    def get(self, rid: str) -> Run:
        if rid not in self.runs:
            raise KeyError(rid)
        return self.runs[rid]

    async def delete(self, rid: str):
        """Delete a run with its record; a run still computing without viewers is suspended first (review C1-15)."""
        run = self.get(rid)
        async with run.lock:
            if run.viewers:
                raise RuntimeError(T("the run is open in a tab: close it, then delete the run"))
            await run._stop("delete", "stopped")
            self._remove(run)

    def _remove(self, run: Run):
        shutil.rmtree(run.dir, ignore_errors=True)
        self.runs.pop(run.id, None)

    def list(self) -> list[dict]:
        return [r.summary() for r in sorted(self.runs.values(), key=lambda r: r.meta.get("created", ""),
                                             reverse=True)]

    async def shutdown(self):
        # all at once: one after another, several slow workers would outlast the container's stop grace (review C1-10)
        await asyncio.gather(*(r.suspend("server shutdown") for r in list(self.runs.values()) if r.running))

    # --- housekeeping ---------------------------------------------------------------------------------
    async def housekeeping(self):
        t_save = 0.0
        t_clean = 0.0
        while True:
            await asyncio.sleep(5.0)
            now = time.monotonic()
            for r in list(self.runs.values()):
                if not r.running or r.viewers or r.rebuilding:
                    continue
                idle = now - r.last_viewer_time
                if idle > self.idle_suspend:
                    await r.suspend("no viewers")
                elif idle > self.idle_pause and r.meta.get("playing"):
                    try:
                        r.command({"cmd": "pause", "args": {"reason": "no_viewers"}}, "server")
                    except RuntimeError:
                        pass
            if now - t_save > 10.0:
                t_save = now
                for r in self.runs.values():
                    if r.running:
                        r.save_meta()
            if now - t_clean > 3600.0:
                t_clean = now
                self.cleanup()

    def cleanup(self) -> list[str]:
        """Remove the runs the limits remove (``_removable``)."""
        removed = self._removable(self.keep_days)
        for r in removed:
            self._remove(r)
        return [r.id for r in removed]

    def _removable(self, keep_days: float) -> list[Run]:
        """Runs whose last action is older than ``keep_days``, then, beyond the quota, those with the oldest last
        action, except runs marked "keep", computing, open in a tab or being resumed (review C1-9)."""
        removed = []
        done = [r for r in self.runs.values()
                if not r.running and not r.viewers and not r.lock.locked() and not r.meta.get("keep")]
        cutoff = time.time() - keep_days * 86400
        last = lambda r: float(r.meta.get("last_action") or 0.0)  # noqa: E731 (set for every run at load)
        for r in done:
            if last(r) < cutoff:
                removed.append(r)
        total = sum(r.disk_size() for r in self.runs.values()) - sum(r.disk_size() for r in removed)
        quota = self.quota_gb * 1e9
        for r in sorted(done, key=last):
            if total <= quota:
                break
            if r not in removed:
                removed.append(r)
                total -= r.disk_size()
        return removed

    # --- the removal period (owner, 2026-10-29: set on the catalogue page, kept on the server) --------------------
    @staticmethod
    def keep_days_error(v) -> str | None:
        """Why ``v`` is not a removal period (None if it is): whole days from 1 to ``KEEP_DAYS_MAX``."""
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 1 <= v <= KEEP_DAYS_MAX or v != int(v):
            return T("a whole number of days from 1 to {max:d} is needed", max=KEEP_DAYS_MAX)
        return None

    def _saved_keep_days(self, default: float) -> float:
        try:
            v = json.loads((self.dir / SETTINGS_NAME).read_text())["keep_days"]
        except (OSError, ValueError, KeyError, TypeError):
            return default
        if self.keep_days_error(v) is not None:
            print(f"lfviz: {SETTINGS_NAME}: keep_days {v!r} ignored, {default} used", file=sys.stderr)
            return default
        return int(v)

    def set_keep_days(self, days, confirm=()) -> dict:
        """Save a new removal period and apply it at once. When it would remove runs that are not all in ``confirm``
        (ids the owner agreed to lose), nothing changes and they are returned as ``would_remove``; otherwise
        ``removed`` lists what went. ValueError: not a period."""
        err = self.keep_days_error(days)
        if err:
            raise ValueError(err)
        if not isinstance(confirm, (list, tuple)):
            raise ValueError(T("confirm is a list of the runs that may be removed"))
        days = int(days)
        would = [r.id for r in self._removable(days)]
        if set(would) - {str(c) for c in confirm}:
            return {"keep_days": self.keep_days, "would_remove": would}
        tmp = self.dir / (SETTINGS_NAME + ".tmp")
        tmp.write_text(json.dumps({"keep_days": days}))
        tmp.replace(self.dir / SETTINGS_NAME)
        self.keep_days = days
        return {"keep_days": days, "removed": self.cleanup()}
