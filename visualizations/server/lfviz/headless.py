# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A world run headless, on a frame clock of its own, and its messages packed (design
``lfphys/sources/explore_2026-11-14_design.md`` §1.2, §1.3): the one runner of the site's recordings
(``site/record.py``), of the atlases' points (``site/atlas.py``) and of the server's live points
(``lfviz.atlas_live``).

``run_spec(viz_id, base, values, seed, clock, stop, script, emit)`` resolves the preset ``base`` and ``values`` through
the world's schema, asks ``check_params`` (a ``Refusal`` there is ``PointRefused``: not a failure) and
``estimate_bytes``, builds ``viz["simulation"]`` and drives ``lfviz.sim.Runner`` with no wall-time budget, so that the
result does not depend on the speed of the CPU. It drops what serves only the resumption of a live run (``DROP``) and
strips the frames' timing fields (``FRAME_TIMING``): the same spec and code give the same messages (integrator D6).

* ``clock``: ``{"fps": f, "speed": s | None}`` (the recordings: one frame every ``speed / fps`` of world time, the speed
  changed by a script's ``speed`` command, ``s`` None for the world's default) or ``{"frame_dt": dt}`` (the atlases: a
  frame at every multiple of ``dt`` of world time, the last one at the stop time);
* ``stop``: ``{"seconds": s}`` (exactly ``round(s × fps)`` frames), ``{"world_s": t}`` (until the world time ``t``) or
  ``{"event": kind, "after_s": a, "max_world_s": m}`` (until ``a`` world seconds after the first ``event`` message whose
  ``kind`` or ``name`` is ``kind``; a run that reaches ``m`` first fails);
* ``script``: ``[{"at", "cmd", "args"}]`` applied at their frame (``round(at × fps)``, or ``round(at / dt)``) before the
  frame is drawn; ``captions`` (recordings, design §2.2): an accumulative ``caption {t, text, n, at, hold?}`` at its
  frame, after the script's commands of that frame;
* ``emit(meta, blobs)``: every kept message, in order, as the world emitted it (the caller encodes or packs it).

A run **fails** (``RunFailed``) on an error message or an exception of the world, a world not built, a stop event not
reached, and a check whose last state is ✗ (``check_state``: a check marked ``expected`` is a ✗ on purpose and does
not fail). It returns an ``Outcome`` (frames, worlds, the checks' last states, the CPU time, the stop time).

``Packer`` packs messages for a point file or a quantised recording: it drops the message types and frame blobs a
screen does not draw, quantises the blobs of a ``quantize`` map (``protocol.quantize``; the largest error per blob is
measured) and writes a header as a delta against the screen's base header:

    {"type": "header", "t", "$delta": true, <the top-level keys whose JSON differs from the base header>,
     "$drop": [keys of the base header this header lacks]?, "$drop_blobs": [base blobs it lacks]?}

with only the header blobs whose stored bytes (or ``q``) differ from the base's. A reader rebuilds the header as
``{...base, ...delta}`` without the ``$``-keys and the dropped keys (a top-level key is replaced whole, not merged), and
its blobs as the base's blobs overridden by the delta's (``merge_header``).
"""

from __future__ import annotations

import gzip
import json
import queue
import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from . import limits, protocol, registry
from .errors import Refusal
from .i18n import join, render_in

#: messages that serve only the resumption of a live run, and what a worker never records (design §4.1 of the start page)
DROP = {"checkpoint", "command", "resumed", "record_segment", "busy", "scene_export"}
#: what the runner adds to a frame from the wall clock or the CPU: never in a recording or a point (integrator D6)
FRAME_TIMING = ("cpu_ms", "speed_actual")


class RunFailed(Exception):
    """A headless run that must not be shipped: what failed, in English for the build's log."""


class PointRefused(Exception):
    """The world refuses these parameters (``check_params`` raised): not a failure. ``text`` and ``hint`` are the
    refusal's texts (``T``)."""

    def __init__(self, text, hint=None):
        self.text, self.hint = text, hint
        super().__init__(render_in(text) if text is not None else "refused")


def check_state(c: dict) -> str:
    """A check's state as the player draws it (``player.js checkState``): info, ok, failed, expected (a ✗ on purpose) or
    na (no reference)."""
    if c.get("info"):
        return "info"
    ok = None
    if c.get("ok") is True or c.get("ok") is False:
        ok = c["ok"]
    elif c.get("ref") is not None and c.get("rel") is not None:
        try:
            ok = abs(float(c["rel"])) <= max(float(c.get("tol") or 1e-9), 1e-12)
        except (TypeError, ValueError):
            ok = None
    if ok is None:
        return "na"
    return "ok" if ok else ("expected" if c.get("expected") else "failed")


@dataclass
class Outcome:
    frames: int = 0
    worlds: int = 0
    checks: dict = field(default_factory=dict)  # (world, check id) -> its last state (check_state)
    flips: list = field(default_factory=list)  # (world, id, t) where a check was ✗ before its last state
    errors: list = field(default_factory=list)  # the texts of the world's error messages
    cpu_s: float = 0.0
    t_end: float = 0.0
    stop_event_t: float | None = None  # the world time of the stop event (an event stop rule)

    def check_counts(self) -> dict:
        out = {"ok": 0, "failed": 0, "expected": 0, "info": 0, "na": 0}
        for st in self.checks.values():
            out[st] = out.get(st, 0) + 1
        return out


def resolve(viz: dict, base: str | None, values: dict | None) -> dict:
    """The world's parameters for a preset and values (ValueError naming every problem the schema finds)."""
    params, errs = viz["schema"].resolve(base, dict(values or {}))
    if errs:
        raise ValueError(join(errs, "; "))
    return params


def refusal(viz: dict, params: dict) -> PointRefused | None:
    """The world's refusal of these parameters (``Simulation.check_params``), or None."""
    try:
        viz["simulation"].check_params(params)
    except Refusal as e:
        return PointRefused(e.text, e.hint)
    except ValueError as e:  # ``ValueError(T(...))``: a plain refusal
        return PointRefused(e.args[0] if e.args else str(e))
    return None


def run_spec(viz_id: str, base: str | None, values: dict | None, seed: int, clock: dict, stop: dict,
             script: list | None = None, emit: Callable | None = None, *, captions: list | None = None,
             end_reason: str = "recording", label: str = "", log: Callable | None = None) -> Outcome:
    """Run a world headless (the module's docstring). Raises ``PointRefused`` (the world refuses the parameters),
    ``ValueError`` (the schema refuses them) or ``RunFailed``."""
    from .sim import Runner  # noqa: PLC0415 - the runner imports the engine's registry lazily
    viz = registry.load(viz_id)
    label = label or viz_id
    out = Outcome()
    seed = int(seed if seed is not None else 1)

    def keep(meta, blobs=None):
        typ = meta.get("type")
        if typ in DROP:
            return
        if typ == "frame":  # no wall-clock or CPU time (D6)
            meta = {k: v for k, v in meta.items() if k not in FRAME_TIMING}
            out.frames += 1
        elif typ == "header":
            out.worlds += 1
        elif typ == "error":
            out.errors.append(meta.get("text"))
        elif typ == "check" and meta.get("id") is not None:
            key = (out.worlds, str(meta["id"]))
            if out.checks.get(key) == "failed":
                out.flips.append((*key, meta.get("t")))
            out.checks[key] = check_state(meta)
        elif typ == "event" and stop_event is not None and out.stop_event_t is None \
                and stop_event in (meta.get("kind"), meta.get("name")):
            out.stop_event_t = float(meta.get("t", 0.0))
        if emit is not None:
            emit(meta, blobs)

    stop_event = stop.get("event") if isinstance(stop, dict) else None
    try:  # the devices of the engine's kernels, as a worker configures them (LFPHYS_NO_GPU=1: the CPU); the kernels
        # this process ran for an earlier run are forgotten, so the header names this run's own (review F1)
        from lfphys.core import backend as _backend
        _backend.reset_used()
        notes = _backend.configure({})
    except Exception:  # noqa: BLE001 - the engine without the backend
        notes = []

    def make_world(pr, vals, sd):
        p = resolve(viz, pr, vals)
        limits.check_estimate(viz["simulation"], p)
        return viz["simulation"](p, seed if sd in (None, "") else int(sd), keep), {"preset": pr}

    params = resolve(viz, base, values)
    refused = refusal(viz, params)
    if refused is not None:
        raise refused
    limits.check_estimate(viz["simulation"], params)

    if "fps" in clock:
        fps = float(clock["fps"])
        step_of = None  # the runner's speed decides
    else:
        fps = 1.0 / float(clock["frame_dt"])
        dt = float(clock["frame_dt"])
        step_of = dt
    t0 = time.process_time()
    sim = viz["simulation"](params, seed, keep)
    runner = Runner(sim, keep, queue.Queue(), fps=fps, make_world=make_world,
                    world_info={"preset": base, "backend_notes": notes})

    def fail(why):
        raise RunFailed(f"{label}: {why}")

    if not runner.start():
        fail(f"the world was not built: {[render_in(e) for e in out.errors]}")
    runner._state("start")
    if clock.get("speed") is not None:
        runner.handle({"cmd": "speed", "args": {"value": float(clock["speed"])}})
    runner.handle({"cmd": "play"})

    def frame_of(at):
        return int(round(float(at) * fps)) if step_of is None else int(round(float(at) / step_of))

    if "seconds" in stop:
        n = int(round(float(stop["seconds"]) * fps))
    else:
        n = None
    at_frame: dict = {}
    for c in script or []:
        k = frame_of(c["at"])
        at_frame.setdefault(min(n - 1, k) if n else k, []).append(("cmd", c))
    for i, c in enumerate(captions or []):
        k = frame_of(c["at"])
        at_frame.setdefault(min(n - 1, k) if n else k, []).append(("caption", i, c))
    last = time.monotonic()
    k = 0
    t_stop = float(stop["world_s"]) if "world_s" in stop else None
    max_t = float(stop["max_world_s"]) if "max_world_s" in stop else None
    while True:
        try:
            if k:
                if step_of is None:
                    runner._advance(runner.sim.t + runner.speed / fps)
                else:
                    target = k * step_of
                    if t_stop is not None:
                        target = min(target, t_stop)
                    elif max_t is not None:
                        target = min(target, max_t)
                    runner._advance(target)
            for item in at_frame.get(k, []):
                if item[0] == "cmd":
                    runner.handle({"cmd": item[1]["cmd"], "args": dict(item[1].get("args") or {})})
                else:
                    _i, c = item[1], item[2]
                    cap = {"type": "caption", "t": runner.sim.t, "text": c["text"], "n": _i, "at": c["at"]}
                    if c.get("hold") is not None:
                        cap["hold"] = c["hold"]
                    keep(cap)
            runner._frame(0.0)  # keep() drops the runner's timing fields
        except Exception as e:  # noqa: BLE001 - the physics failed: nothing is shipped
            fail(f"frame {k}" + (f" of {n}" if n else "") + f": {type(e).__name__}: {e}")
        if out.errors:
            fail(f"the world reported an error at frame {k}: {render_in(out.errors[0])}")
        if log is not None and time.monotonic() - last > 60:
            last = time.monotonic()
            log(f"  {label}: frame {k + 1}" + (f" of {n}" if n else "") + f", t = {runner.sim.t:.6g}")
        k += 1
        if n is not None:
            if k >= n:
                break
            continue
        if stop_event is not None and out.stop_event_t is not None and t_stop is None:
            t_stop = out.stop_event_t + float(stop.get("after_s", 0.0))
        if t_stop is not None and runner.sim.t >= t_stop * (1 - 1e-12) - 1e-12:
            break
        if t_stop is None and max_t is not None and runner.sim.t >= max_t * (1 - 1e-12):
            fail(f"the stop event {stop_event!r} did not happen by the world time {max_t:g} s (max_world_s)")
    keep({"type": "end", "t": runner.sim.t, "reason": end_reason})
    if n is not None and out.frames != n:
        fail(f"{out.frames} frames instead of {n}")
    out.cpu_s = time.process_time() - t0
    out.t_end = runner.sim.t
    bad = sorted(f"{cid} (world {w})" for (w, cid), st in out.checks.items() if st == "failed")
    if bad:
        fail(f"{len(bad)} check(s) end failed: {', '.join(bad)}")
    if out.flips and log is not None:
        log(f"  note: {label}: a check was ✗ before its last state: "
            f"{sorted({f'{cid} (world {w})' for w, cid, _t in out.flips})}")
    return out


# --- packing (design §1.3) ------------------------------------------------------------------------------------------
def _jsonable(x):
    return json.dumps(protocol.clean(x), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _blob_sig(b) -> tuple:
    """What decides a stored blob's bytes: its codes (or array) and ``q``."""
    if isinstance(b, protocol.Quantized):
        return (b.codes.dtype.str, b.codes.shape, b.codes.tobytes(), _jsonable(b.q))
    a = np.ascontiguousarray(np.asarray(b))
    return (a.dtype.str, a.shape, a.tobytes(), None)


class Packer:
    """Packs a run's messages for a point file or a quantised recording (the module's docstring). ``quantize``: a
    screen's map ``{"<type>.<blob>[|<blob>…]": encoding}``; ``drop``: ``{"types": [...], "frame_blobs": [...]}``;
    ``base``: the screen's base header ``(meta, blobs)`` as packed (``pack_base``), or None (a full header). ``quant``
    collects, per ``<type>.<blob>``, the encoding and the largest error and relative error (to the range) seen."""

    def __init__(self, quantize: dict | None = None, drop: dict | None = None, base: tuple | None = None):
        self.qmap: dict = {}
        for typ, blob, enc in registry.quantize_items(quantize or {}):
            self.qmap[(typ, blob)] = enc
        drop = drop or {}
        self.drop_types = set(drop.get("types") or [])
        self.drop_frame_blobs = set(drop.get("frame_blobs") or [])
        self.base = base
        self.quant: dict = {}

    def _note(self, key: str, enc: str, qb):
        if not isinstance(qb, protocol.Quantized):
            return
        e = self.quant.setdefault(key, {"enc": enc, "max_err": None, "max_rel": None})
        err = qb.max_err
        span = qb.span
        rel = ([a / s if s > 0 else 0.0 for a, s in zip(err, span)] if isinstance(err, list)
               else (err / span if span > 0 else 0.0))
        for k, v in (("max_err", err), ("max_rel", rel)):
            old = e[k]
            if old is None:
                e[k] = v
            elif isinstance(v, list) and isinstance(old, list) and len(v) == len(old):
                e[k] = [max(a, b) for a, b in zip(old, v)]
            else:  # the columns changed between messages: one number
                e[k] = max(max(old) if isinstance(old, list) else old, max(v) if isinstance(v, list) else v)

    def blobs(self, typ: str, blobs: dict | None) -> dict:
        """A message's blobs with the frame's dropped blobs left out and the map's blobs quantised."""
        out = {}
        for name, arr in (blobs or {}).items():
            if typ == "frame" and name in self.drop_frame_blobs:
                continue
            enc = self.qmap.get((typ, name))
            if enc is not None and not isinstance(arr, protocol.Quantized):
                a = np.asarray(arr)
                if a.dtype.kind in "fiu" and a.size:
                    arr = protocol.quantize(a, enc)
                    self._note(f"{typ}.{name}", enc, arr)
            out[name] = arr
        return out

    def pack_base(self, meta: dict, blobs: dict | None) -> tuple:
        """The base header as stored (its blobs quantised): what ``base`` takes and the base file holds."""
        return dict(meta), self.blobs("header", blobs)

    def message(self, meta: dict, blobs: dict | None = None) -> bytes | None:
        """One message encoded as packed, or None when its type is dropped."""
        typ = meta.get("type")
        if typ in self.drop_types:
            return None
        b = self.blobs(typ, blobs)
        if typ == "header" and self.base is not None:
            meta, b = self.delta(meta, b)
        return protocol.encode(meta, b)

    def delta(self, meta: dict, blobs: dict) -> tuple[dict, dict]:
        bmeta, bblobs = self.base
        out = {"type": "header", "t": meta.get("t"), "$delta": True}
        for k, v in meta.items():
            if k in ("type", "t", "blobs"):
                continue
            if k not in bmeta or _jsonable(v) != _jsonable(bmeta[k]):
                out[k] = v
        gone = sorted(k for k in bmeta if k not in meta and k not in ("type", "t", "blobs"))
        if gone:
            out["$drop"] = gone
        ob = {n: a for n, a in blobs.items() if n not in bblobs or _blob_sig(a) != _blob_sig(bblobs[n])}
        gone_b = sorted(n for n in bblobs if n not in blobs)
        if gone_b:
            out["$drop_blobs"] = gone_b
        return out, ob


def merge_header(base: tuple, delta: tuple) -> tuple[dict, dict]:
    """A point's full header from the base header and its delta, both decoded ``(meta, blobs)`` (what the player does):
    ``{...base, ...delta}`` without the ``$``-keys and the dropped keys; blobs: the base's overridden by the delta's."""
    bmeta, bblobs = base
    dmeta, dblobs = delta
    if not dmeta.get("$delta"):
        return dmeta, dblobs
    meta = {k: v for k, v in bmeta.items() if k != "blobs"}
    meta.update({k: v for k, v in dmeta.items() if k != "blobs"})
    for k in list(dmeta.get("$drop") or []) + ["$delta", "$drop", "$drop_blobs"]:
        meta.pop(k, None)
    blobs = {n: a for n, a in bblobs.items() if n not in (dmeta.get("$drop_blobs") or [])}
    blobs.update(dblobs)
    return meta, blobs


def stream(messages: list[bytes]) -> bytes:
    """An ``LFVREC1`` stream of encoded messages."""
    return protocol.MAGIC + b"".join(protocol.frame_stream_item(m) for m in messages)


def gz(data: bytes) -> bytes:
    """gzip -9 with mtime 0: the same bytes for the same data."""
    return gzip.compress(data, compresslevel=9, mtime=0)


def read_stream(data: bytes, raw: bool = False) -> list[tuple[dict, dict]]:
    """The decoded messages of an ``LFVREC1`` stream (gzip or not)."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    if not data.startswith(protocol.MAGIC):
        raise ValueError("not an LFVREC1 stream")
    return [protocol.decode(m, raw=raw) for _o, m in protocol.iter_stream(data, len(protocol.MAGIC))]
