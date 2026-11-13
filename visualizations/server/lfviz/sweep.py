# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Parameter sweeps (plan P16.3; owner, 2026-11-04 and 2026-11-11; integrator's API of 2026-11-11, §4): the same scene
from the current moment for a list of values of a live law or of an object's parameter, a chosen measurable read over
a chosen stretch of world time, a table and a plot — computed in a separate memory-limited process, the live world
unaffected.

    POST   /api/runs/{id}/sweep              {"target": {"kind": "law", "id": <live law>} | {"kind": "object", "obj": <id>,
                                              "param": <param id>}, "values": [...] (<= 50), "duration": <world time>,
                                              "measure": <measurable id>, "stat": "final" | "mean_last" | "max" | "min",
                                              "window": <world time, for mean_last>, "n_samples"?: 200 (<= 2000),
                                              "estimate"?: true} -> {n, state, estimate, base} (with "estimate": only
                                              {estimate}); 400 with {error, hint, estimate} above the budget
    GET    /api/runs/{id}/sweeps             the run's sweeps (newest last): n, state, progress, what was swept and measured
    GET    /api/runs/{id}/sweeps/{n}         progress and results ({...}?format=csv: the table, its set-up in «#» lines)
    POST   /api/runs/{id}/sweeps/{n}/cancel  stop a running sweep (what it computed is kept, state "cancelled"); a sweep
                                             that is not running answers 200 {already: true} (a second click, another
                                             tab: review LB1-framework F10); works also for a run deleted meanwhile
    DELETE /api/runs/{id}/sweeps/{n}         remove a finished sweep with its results; 409 while it runs

How a sweep is computed.

* **The state it starts from.** The server asks the run's worker for a checkpoint of the world as it is now (command
  ``checkpoint_now {tag}``: the worker answers with a recorded ``checkpoint`` message carrying the tag; nothing of the
  world changes). Only the server sends that command: the client routes refuse it (``lfviz.app``, review F6). A
  suspended run (no worker) starts from its latest usable checkpoint in the record, and the result says so. The
  checkpoint's code files and runtime must be the ones on the disk now (``lfviz.checkpoint``: the sweep process loads
  the world with today's code), else the sweep is refused. The file is linked into ``sweeps/`` so that the worker's own
  rotation of its checkpoints cannot remove it under the sweep; it is deleted when the sweep ends.
* **The process.** ``python -m lfviz.sweep --file sweeps/<n>.json``: its own memory budget as its hard limit, smaller
  than a world's (``sweep_mem``: ``LFVIZ_SWEEP_MEM_GB``, by default half the worker budget, at least 512 MB; a sweep
  whose state copy and world do not fit it, or the memory the container has free now, is refused before it starts),
  the first process the kernel ends when the container's memory runs out (``oom_score_adj`` 1000: the live worlds keep
  theirs at 0), a lower CPU priority than the worlds, the CPU only unless ``LFVIZ_SWEEP_GPU=1`` (a GPU kernel of a
  sweep would share GPU 0 with the live worlds outside their accounting and their thermal guard; review F9), the run's
  device settings otherwise. For every value it unpickles the checkpoint into a fresh world, applies the change exactly
  as the live world would — the runner's ``set`` for a law; for an object's parameter the scene's ``edit`` when the
  parameter is one of the type's handles (a position or a velocity: its stored value is where the object was put, not
  where it is, so the value is applied even when it equals it), else the scene's ``set``, and a value equal to the
  stored one is applied again too (the section's ``on_set`` sees the parameter as changed, ``old`` holding the stored
  value: ``_again``), so that every row of the table is the same experiment (review F1) — a refusal is that value's
  result, in the world's words; then it advances the world and reads the measurable at equally spaced moments
  (``n_samples`` steps: over the window for ``mean_last``, over the whole duration for ``max`` / ``min``, the end only
  for ``final``) — through the world's ``measure()`` when it has one (a dict {id: number}: anything else is the
  world breaking the instruments' contract, said as such and the sweep stops; review LB1-p02-ux Q3), else through
  ``frame()``'s ``meas``. ``final``: the last reading; ``mean_last``: the trapezoid mean over the window; ``max`` /
  ``min``: over the readings from the change on (undefined readings left out, and counted). The result states the
  readings and their spacing (F7). The same sweep from the same state gives the same numbers (the world's random
  generator is in the checkpoint).
* **The cost.** Before a sweep starts its cost is estimated from the world's own measured cost in the record: only the
  frames computed while the world played (``speed_actual`` set) with no command since the previous frame, whose
  ``cpu_ms`` is the advance and the frame — a paused world's frame also counts the runner's wait for the next command
  (review F4); the cheapest frame as the cost of one reading; the latest checkpoint's size for a restore. A sweep above
  the budget (``LFVIZ_SWEEP_BUDGET_S``, 10 min) is refused. A world that has not played has no measured cost: its
  sweep starts and measures itself. The budget is held inside the advance too (review F2): the process advances in
  pieces of at most ``CHUNK_S`` of wall time along the world's own steps, and between them it stops when its wall time
  passes ``OVERRUN`` × the budget, or when, after ``PROBE_S`` of advancing, its measured cost projects the whole sweep
  beyond that; the server ends a process still running ``WATCH_GRACE_S`` after that (one step of the world longer than
  the budget), keeping the values computed.
* **Limits.** One sweep per run and ``MAX_SWEEPS`` on the server at a time. A run deleted or removed while its sweep
  runs ends that sweep within about a second: the server's watch sees the run gone and ends the process, and the
  process itself exits when its folder is gone (review F3).

The process writes its whole state to ``sweeps/<n>.json`` (atomically, at most once a second and after each value): the
request, where it started from, the estimate, the progress, and per value the measured number (or the reason there is
none), the readings it was taken from, how the change was applied, and what it cost.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import secrets
import shutil
import sys
import time
from pathlib import Path

from .i18n import T, error_body, has_unit, is_t, join, json_hook, names_unit, render_in, text_of  # noqa: F401

MAX_VALUES = 50
N_SAMPLES = 200
N_SAMPLES_MAX = 2000
MAX_SWEEPS = 2
OVERRUN = 1.5  # a sweep stops by itself beyond this times the budget
CHUNK_S = 0.25  # wall seconds of one piece of an advance: the process looks at its clock between them (F2)
PROBE_S = 3.0  # wall seconds of advancing after which the process projects its whole cost from what it measured (F2)
WATCH_GRACE_S = 30.0  # the server ends a process still running this long after OVERRUN × the budget (F2)
TRACE_POINTS = 200  # readings kept per value for the plot of its course
STATS = ("final", "mean_last", "max", "min")
SPEC = re.compile(r"^(\d+)\.json$")
MIB = 2 ** 20


def budget_s() -> float:
    try:
        v = float(os.environ.get("LFVIZ_SWEEP_BUDGET_S", "") or 600.0)
    except ValueError:
        v = 600.0
    return v if v > 0 else 600.0


def sweep_mem(worker_mem: int) -> int:
    """A sweep process's memory budget (review F9): ``LFVIZ_SWEEP_MEM_GB`` when set, else half a worker's budget (at
    least 512 MB, never more than a worker's)."""
    try:
        gb = float(os.environ.get("LFVIZ_SWEEP_MEM_GB", "") or 0.0)
    except ValueError:
        gb = 0.0
    if gb > 0:
        return int(gb * 2 ** 30)
    return int(min(worker_mem, max(512 * MIB, worker_mem // 2)))


def fmt_wall(s: float | None):
    """Seconds of computation in the owner's words (a text): "0.4 s", "12 s", "2 min 10 s", "1 h 5 min"."""
    if s is None or not math.isfinite(s):
        return "—"
    if s < 10:
        return T("{s:.1f} s", s=s)
    if s < 60:
        return T("{s:.0f} s", s=s)
    if s < 3600:
        m, r = divmod(int(round(s)), 60)
        return T("{m:d} min {s:d} s", m=m, s=r) if r else T("{m:d} min", m=m)
    h, r = divmod(int(round(s)), 3600)
    return T("{h:d} h {m:d} min", h=h, m=r // 60) if r // 60 else T("{h:d} h", h=h)


def fmt_num(x) -> str:
    """A number for the logs (English)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return str(x)
    return f"{x:.6g}"


#: seconds with the SI prefix of their scale (msgids "{x:.6g} ms", …)
T_PREFIX = ((1.0, "s"), (1e-3, "ms"), (1e-6, "µs"), (1e-9, "ns"), (1e-12, "ps"), (1e-15, "fs"), (1e-18, "as"))


def _is_seconds(unit) -> bool:
    return (is_t(unit) and unit.get("$t") == "s" and not unit.get("a")) or unit in ("s", "с")  # i18n-ok (old records)


def fmt_t(x, unit="s"):
    """A world time for the owner (a text): seconds with the SI prefix of their scale ("50 fs", "1.5 s"); another
    world unit ("M", or a world that counts in fs) as it is."""
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
        return "—"
    if not _is_seconds(unit) or x == 0:
        if _is_seconds(unit):
            return T("{x:.6g} s", x=x)
        return T("{x:.6g} {unit}", x=x, unit=unit)
    for k, u in T_PREFIX:
        if abs(x) >= 0.99999 * k:
            return T("{x:.6g} " + u, x=x / k)  # i18n-msgids: "{x:.6g} s" "{x:.6g} ms" "{x:.6g} µs" "{x:.6g} ns" "{x:.6g} ps" "{x:.6g} fs" "{x:.6g} as"
    return T("{x:.6g} as", x=x / 1e-18)


def with_unit(label, unit):
    """"label, unit" — unless the label already names the unit ("Window size, nm", "Number of slits"; review
    LB1-p02-ux X9). Texts (``T``, live or read back from JSON) are compared by msgid and arguments (``names_unit``),
    never by a rendering or a repr (review i18n-code F2)."""
    if not unit:
        return label or ""
    if names_unit(label or "", unit):
        return label
    return T("{label}, {unit}", label=label or "", unit=unit)


class Refused(ValueError):
    """A sweep that is not started, with the owner's text and what to change."""

    def __init__(self, text, hint="", status: int = 400, **extra):
        super().__init__(text)
        self.text, self.hint, self.status, self.extra = text, hint, status, extra


# --- the request ----------------------------------------------------------------------------------------------------
def _number(body, key, what, positive=True):
    v = body.get(key)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) \
            or (positive and not float(v) > 0):
        raise Refused(T("“{what}” is a positive finite number (the world's time)", what=what))
    return float(v)


def _ident(v, what: str) -> str:
    """An id from the request: a short string (a list or a number would break the lookups: review F12)."""
    if not isinstance(v, str) or not v or len(v) > 200:
        raise Refused(T("“{what}” is an identifier (a string)", what=what))
    return v


def _param_of(d: dict):
    """A parameter rebuilt from its JSON form (``Param.to_json``; the palette in a world's header)."""
    import dataclasses  # noqa: PLC0415
    from .params import Param  # noqa: PLC0415
    names = {f.name for f in dataclasses.fields(Param)}
    kw = {k: d[k] for k in names if k in d}
    opts = []
    for o in d.get("options") or []:
        if isinstance(o, dict):
            opts.append((o.get("value"), o.get("label", ""), o["show_if"]) if o.get("show_if")
                        else (o.get("value"), o.get("label", "")))
        elif isinstance(o, (list, tuple)):
            opts.append(tuple(o))
    kw["options"] = opts
    return Param(**kw)


def object_param(viz: dict, w, obj: dict, pid: str):
    """(the parameter, whether it is one of the type's handles, the type's parameters for a refusal) of an object of
    the latest scene — from the palette the world's header gave (the sections build it per world: review LB1-p02-ux X1),
    else from the class (a section with a class-level palette and an older record)."""
    from .playground import handle_ids  # noqa: PLC0415
    typ = obj.get("type")
    tj = (getattr(w, "palette", None) or {}).get(typ)
    if tj is not None:
        params = [d for d in (tj.get("params") or []) if isinstance(d, dict) and isinstance(d.get("id"), str)]
        have = [T("“{label}” ({id})", label=d.get("label") or d["id"], id=d["id"]) for d in params]
        d = next((d for d in params if d["id"] == pid), None)
        try:
            p = _param_of(d) if d is not None else None
        except (TypeError, ValueError):
            p = None
        return p, pid in handle_ids(tj.get("handles")), have
    ot = (getattr(viz["simulation"], "PALETTE", None) or {}).get(typ)
    if ot is None:
        return None, False, []
    return ot.schema.by_id.get(pid), pid in ot.handle_ids(), [T("“{label}” ({id})", label=q.label, id=q.id)
                                                              for q in ot.schema.params]


def sampling(req: dict) -> dict:
    """How the measure is read: the number of readings and the world time between them."""
    n = req["n_samples"]
    if req["stat"] == "final":
        return {"readings": 1, "dt": None}
    span = req["window"] if req["stat"] == "mean_last" else req["duration"]
    return {"readings": n + 1, "dt": span / n}


def stat_text(req: dict, t_unit):
    """What the number is, with its sampling (review F7): "the maximum over 201 readings 1.5 ms apart"."""
    s = sampling(req)
    if req["stat"] == "final":
        return T("at the end (1 reading)")
    k, dt = s["readings"], fmt_t(s["dt"], t_unit)
    if req["stat"] == "mean_last":
        return T("the mean over the last {window} ({n:d} readings {dt} apart)", window=fmt_t(req["window"], t_unit),
                 n=k, dt=dt)
    if req["stat"] == "max":
        return T("the maximum over {n:d} readings {dt} apart", n=k, dt=dt)
    return T("the minimum over {n:d} readings {dt} apart", n=k, dt=dt)


def validate(viz: dict, idx, body) -> tuple[dict, dict]:
    """The request checked against the run's world (its schema, the latest scene with the palette of the world's header,
    the measurables it declares now): (the request as it will be computed, what it means for the owner: labels and
    units). ``Refused`` otherwise."""
    from .params import _coerce  # noqa: PLC0415 - the parameters' own checks, as the forms use them
    if not isinstance(body, dict):
        raise Refused(T("the request body is a JSON object"))
    if not idx.worlds:
        raise Refused(T("the record holds no world"))
    world = max(idx.worlds)
    w = idx.worlds[world]
    tg = body.get("target")
    if not isinstance(tg, dict) or tg.get("kind") not in ("law", "object"):
        raise Refused(T("“target” is {kind: law, id} or {kind: object, obj, param}"))
    if tg["kind"] == "law":
        lid = _ident(tg.get("id"), "target.id")
        p = viz["schema"].by_id.get(lid)
        if p is None or not p.live:
            live = join([T("“{label}” ({id})", label=q.label, id=q.id) for q in viz["schema"].params if q.live],
                        ", ") or T("none")
            raise Refused(T("“{id}” is not a law that can be changed while the world runs; such laws of this world: "
                            "{laws}", id=lid, laws=live),
                          T("a sweep does not vary the laws that only a new world changes"))
        target = {"kind": "law", "id": p.id}
        info = {"target_label": p.label, "target_unit": p.unit, "target_text": T("the law “{label}”", label=p.label),
                "target_handle": False}
    else:
        oid, pid = _ident(tg.get("obj"), "target.obj"), _ident(tg.get("param"), "target.param")
        obj = w.objects.get(oid)
        if obj is None:
            raise Refused(T("the scene has no object “{id}”", id=oid), T("choose an object of the current scene"))
        p, handle, have = object_param(viz, w, obj, pid)
        if p is None:
            raise Refused(T("“{label}” has no parameter “{id}”; there are: {params}", label=obj.get("label") or oid,
                            id=pid, params=join(have, ", ") or T("none")))
        target = {"kind": "object", "obj": oid, "param": p.id}
        info = {"target_label": T("{object}: {label}", object=obj.get("label") or oid, label=p.label),
                "target_unit": p.unit,
                "target_text": T("“{label}” of the object “{object}”", label=p.label, object=obj.get("label") or oid),
                "target_handle": handle}
    if p.type == "json":
        raise Refused(T("“{label}” is neither a number nor an option: a sweep does not vary such parameters",
                        label=p.label))
    vals = body.get("values")
    if not isinstance(vals, list) or not vals:
        raise Refused(T("“values” is a list of values"))
    if len(vals) > MAX_VALUES:
        raise Refused(T("{n:d} values — at most {max:d}", n=len(vals), max=MAX_VALUES), T("shorten the list"))
    values, errs = [], []
    for v in vals:
        x, e = _coerce(p, v)
        if e and e not in errs:
            errs.append(e)
        values.append(x)
    if errs:
        raise Refused(join(errs, "; "))
    duration = _number(body, "duration", T("duration"))
    mid = body.get("measure")
    now = w.current if w.current is not None else set(w.decl)
    if not isinstance(mid, str) or mid not in w.decl:
        have = ", ".join(sorted(now)) or T("none: the world reports no measurable quantities")
        raise Refused(T("there is no measurable quantity “{id}” (there are: {have})", id=str(mid)[:200], have=have))
    if mid not in now:  # declared once, its object removed since (review F12)
        from .instruments import display_label  # noqa: PLC0415
        raise Refused(T("the world does not measure “{label}” now: its object is no longer in the scene",
                        label=display_label(w, w.decl[mid])),
                      T("choose a quantity among those the world measures now"))
    stat = body.get("stat", "final")
    if not isinstance(stat, str) or stat not in STATS:
        raise Refused(T("“stat” is final, mean_last, max or min"))
    window = None
    if stat == "mean_last":
        window = _number(body, "window", T("the averaging window"))
        if window > duration:
            raise Refused(T("the averaging window is longer than the sweep"),
                          T("make the window no longer than the duration"))
    ns = body.get("n_samples", N_SAMPLES)
    if isinstance(ns, bool) or not isinstance(ns, (int, float)) or int(ns) != ns or not 1 <= ns <= N_SAMPLES_MAX:
        raise Refused(T("“n_samples” is a whole number from 1 to {max:d}", max=N_SAMPLES_MAX))
    d = w.decl[mid]
    from .instruments import display_label  # noqa: PLC0415
    req = {"target": target, "values": values, "duration": duration, "measure": mid, "stat": stat, "window": window,
           "n_samples": int(ns)}
    info.update(world=world, t_unit=w.t_unit, measure_label=display_label(w, d), measure_unit=d.get("unit") or "",
                stat_text=stat_text(req, w.t_unit), sampling=sampling(req))
    return req, info


def n_readings(req: dict) -> int:
    return sampling(req)["readings"]


# --- the cost estimate ----------------------------------------------------------------------------------------------
def measured_cost(run, idx, entries: list, n_frames: int = 400) -> dict:
    """The latest world's cost as the record measured it (in a thread). Only frames computed while the world played
    (``speed_actual`` set: playing for more than half a second at one speed) with no command or checkpoint since the
    previous frame are counted: their ``cpu_ms`` is the advance over the world time since that frame plus the frame
    itself, so their sum over the world time they advanced bounds the cost per unit of world time from above (a frame's
    own cost counted as advance; every frame of a playing world advances, so the two cannot be told apart). A paused
    world's frame also counts the runner's wait for the command that made it (up to a frame period: review F4,
    estimates 57 to 2600 times too high), so a world that was only stepped has no measured cost. The cheapest of those
    frames bounds the cost of one reading; the latest checkpoint's size and pickling time give the restore."""
    from .instruments import read_json  # noqa: PLC0415
    world = max(idx.worlds) if idx.worlds else None
    picked, ck, nfr = [], None, 0  # newest first: frames, and the commands / checkpoints between them
    for w, a, b in reversed(idx.spans):
        if w != world:
            continue
        for i in range(b - 1, a - 1, -1):
            e = entries[i]
            if e.is_frame:
                if nfr < n_frames:
                    picked.append(e)
                    nfr += 1
            elif e.kind in ("command", "checkpoint"):
                if nfr < n_frames:
                    picked.append(e)
                if e.kind == "checkpoint" and ck is None:
                    ck = e
            if nfr >= n_frames and ck is not None:
                break
        if nfr >= n_frames and ck is not None:
            break
    picked.reverse()
    files: dict = {}
    run.readers += 1
    try:
        fm = [(e, read_json(files, run, e) if e.is_frame else None) for e in picked]
        ckm = read_json(files, run, ck) if ck is not None else None
    finally:
        run.readers -= 1
        for f in files.values():
            f.close()
    frames = [m for e, m in fm if m is not None]
    num = den = 0.0
    played = []
    prev, dirty = None, True
    for e, m in fm:
        if m is None:  # a command or a checkpoint: the next frame's time holds it
            dirty = True
            continue
        if prev is not None and not dirty and m.get("speed_actual") is not None:
            dt = float(m.get("t") or 0.0) - float(prev.get("t") or 0.0)
            if dt > 0:
                played.append(float(m.get("cpu_ms") or 0.0))
                num += played[-1]
                den += dt
        prev, dirty = m, False
    cpu = played or [float(m.get("cpu_ms") or 0.0) for m in frames]
    out = {"frames": len(frames), "frames_played": len(played), "sample_ms": min(cpu) if cpu else None,
           "ms_per_t": num / den if den > 0 else None}
    if ckm and not ckm.get("error"):
        out["ckpt_bytes"] = ckm.get("bytes")
        out["ckpt_ms"] = ckm.get("ms")
    return out


def estimate(req: dict, info: dict, cost: dict, budget: float) -> dict:
    """The sweep's cost in seconds of computation, from the world's measured cost (``measured_cost``)."""
    n = len(req["values"])
    nr = n_readings(req)
    b = float(cost.get("ckpt_bytes") or 0.0)
    restore_s = 0.05 + b / 150e6 + 1.5e-3 * float(cost.get("ckpt_ms") or 0.0)  # unpickling ~ pickling, ~150 MB/s
    start_s = 3.0  # the process: the interpreter, the engine, the world's modules
    out = {"n_values": n, "n_readings": nr, "duration": req["duration"], "budget_s": budget,
           "restore_s": restore_s, "sample_ms": cost.get("sample_ms"), "ms_per_t": cost.get("ms_per_t"),
           "frames_measured": cost.get("frames_played", 0)}
    if cost.get("ms_per_t") is None:
        out.update(known=False, total_s=None, text=T(
            "{values:d} values × {n:d} readings: the record has not measured the cost of computing this world (the "
            "world has not yet been run with ⏺ — steps and pauses do not show it). The sweep measures it itself in the first "
            "{probe} of computing and stops if the whole of it would take more than {limit} (the budget {budget} × "
            "{k:g})", values=n, n=nr, probe=fmt_wall(PROBE_S), limit=fmt_wall(OVERRUN * budget),
            budget=fmt_wall(budget), k=OVERRUN))
        return out
    adv_s = req["duration"] * cost["ms_per_t"] / 1e3
    smp_s = nr * (cost.get("sample_ms") or 0.0) / 1e3
    per = restore_s + adv_s + smp_s
    total = start_s + n * per
    unit = info.get("t_unit") or "s"
    out.update(known=True, per_value_s=per, total_s=total, text=T(
        "≈ {total} of computing: {values:d} values × (restoring {restore} + {duration} of the world × {ms:.3g} ms per "
        "1 {unit} + {n:d} readings × {sample:.3g} ms); the budget is {budget}. The estimate comes from the cost of "
        "computing this world while it was running ({frames:d} frames of the record); the sweep checks it itself and stops "
        "if it exceeds {limit}", total=fmt_wall(total), values=n, restore=fmt_wall(restore_s),
        duration=fmt_t(req["duration"], unit), ms=cost["ms_per_t"], unit=unit, n=nr,
        sample=cost.get("sample_ms") or 0.0, budget=fmt_wall(budget), frames=int(cost.get("frames_played", 0)),
        limit=fmt_wall(OVERRUN * budget)))
    return out


# --- the server's side ----------------------------------------------------------------------------------------------
def _write_json(path: Path, data: dict):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False, default=str))
    tmp.replace(path)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


_NOW_SUPPORTED: bool | None = None


def checkpoint_now_supported() -> bool:
    """Whether the workers answer ``checkpoint_now`` (the framework's command; an unknown command would put an error
    into the record): its name in the runner's code."""
    global _NOW_SUPPORTED
    if _NOW_SUPPORTED is None:
        import inspect  # noqa: PLC0415
        from . import sim  # noqa: PLC0415
        try:
            _NOW_SUPPORTED = "checkpoint_now" in inspect.getsource(sim.Runner)
        except (OSError, TypeError):
            _NOW_SUPPORTED = False
    return _NOW_SUPPORTED


def container_free() -> int | None:
    """The memory the server's container can still give (its cgroup's limit minus what it uses, the reclaimable page
    cache not counted), or None without a limit."""
    for lim_p, cur_p, stat_p, key in (
            ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.stat",
             "inactive_file"),
            ("/sys/fs/cgroup/memory/memory.limit_in_bytes", "/sys/fs/cgroup/memory/memory.usage_in_bytes",
             "/sys/fs/cgroup/memory/memory.stat", "total_inactive_file")):
        try:
            lim, cur = open(lim_p).read().strip(), open(cur_p).read().strip()
        except OSError:
            continue
        if not (lim.isdigit() and cur.isdigit()) or int(lim) >= 2 ** 60:
            continue
        cache = 0
        try:
            for line in open(stat_p):
                k, _, v = line.partition(" ")
                if k == key and v.strip().isdigit():
                    cache = int(v)
        except OSError:
            pass
        return int(lim) - max(0, int(cur) - cache)
    return None


def memory_need(state_bytes: float) -> int:
    """What a sweep process holds at most: the state's bytes, the world unpickled from them (about as large), and the
    interpreter with the engine."""
    return int(2.2 * float(state_bytes or 0.0) + 300 * MIB)


class SweepManager:
    def __init__(self, mgr):
        self.mgr = mgr
        self.active: dict = {}  # (run id, n) -> {"proc", "task", "cancel": bool, "killed": None | "gone" | "over"}
        self.lock = asyncio.Lock()

    @property
    def mem(self) -> int:
        return sweep_mem(int(self.mgr.worker_mem))

    @staticmethod
    def folder(run) -> Path:
        return run.dir / "sweeps"

    def spec_path(self, run, n: int) -> Path:
        return self.folder(run) / f"{int(n)}.json"

    def _running_of(self, run) -> list:
        return [n for (rid, n) in self.active if rid == run.id]

    # --- start --------------------------------------------------------------------------------------------------
    async def start(self, run, body: dict) -> dict:
        from . import instruments  # noqa: PLC0415
        from .limits import fmt_bytes  # noqa: PLC0415
        viz = self.mgr.viz(run.viz_id)
        idx, entries, _ = await instruments.indexed(run)
        req, info = validate(viz, idx, body)
        cost = await asyncio.to_thread(measured_cost, run, idx, entries)
        bud = budget_s()
        est = estimate(req, info, cost, bud)
        if est["known"] and est["total_s"] > bud:
            raise Refused(T("The sweep would take about {total} of computing — more than the budget of {budget}",
                            total=fmt_wall(est["total_s"]), budget=fmt_wall(bud)),
                          T("reduce the number of values, the duration or the number of readings"), estimate=est)
        if body.get("estimate"):
            return {"estimate": est, **info}
        async with self.lock:
            mine = self._running_of(run)
            if mine:
                raise Refused(T("this run already has sweep no. {n:d} running: wait for it or cancel it", n=mine[0]),
                              status=409)
            if len(self.active) >= MAX_SWEEPS:
                raise Refused(T("{n:d} sweeps already run on the server (no more than {max:d} at once): wait for one of "
                                "them", n=len(self.active), max=MAX_SWEEPS), status=409)
            folder = self.folder(run)
            folder.mkdir(parents=True, exist_ok=True)
            used = [int(m.group(1)) for p in folder.iterdir() if (m := SPEC.match(p.name))]
            n = max(used, default=0) + 1
            self.active[(run.id, n)] = {"proc": None, "task": None, "cancel": False, "killed": None,
                                        "budget": bud}  # reserved while the base comes
        dst = folder / f"{n}.base.pkl"
        try:
            base = await self._base(run, info["world"], info["t_unit"])
            try:
                os.link(base["path"], dst)
            except OSError:
                await asyncio.to_thread(shutil.copyfile, base["path"], dst)
            # the memory the sweep will hold (review F9): within its own budget, and free in the container now
            need = memory_need(base.get("bytes") or dst.stat().st_size)
            mem = self.mem
            if need > mem:
                raise Refused(T("a sweep of this world needs about {need} of memory (a copy of the world's state and "
                                "a world made from it), while a sweep is given {mem}", need=fmt_bytes(need),
                                mem=fmt_bytes(mem)),
                              T("make the world smaller (the grid, the number of particles) — or use a server with a "
                                "larger LFVIZ_SWEEP_MEM_GB"), status=409)
            free = container_free()
            if free is not None and need > free:
                raise Refused(T("the server has {free} of memory free now, while the sweep needs about {need}: the "
                                "running worlds come first", free=fmt_bytes(free), need=fmt_bytes(need)),
                              T("repeat when other runs stop"), status=409)
            spec = {"n": n, "run": run.id, "viz": run.viz_id, "state": "starting", "created": _now_iso(),
                    "request": req, **info, "estimate": est, "budget_s": bud, "mem_bytes": mem,
                    "base": {**{k: v for k, v in base.items() if k != "path"}, "path": str(dst)},
                    "backend": run.meta.get("backend_settings") or {},
                    "progress": {"done": 0, "total": len(req["values"]), "frac": 0.0}, "results": []}
            path = self.spec_path(run, n)
            _write_json(path, spec)
            proc = await self._spawn(run, path, folder / f"{n}.log", mem)
        except BaseException:
            self.active.pop((run.id, n), None)
            dst.unlink(missing_ok=True)
            raise
        a = self.active[(run.id, n)]
        a["proc"] = proc
        a["task"] = asyncio.create_task(self._watch(run, n, proc))
        return {"n": n, "state": "starting", "estimate": est,
                "base": {k: v for k, v in spec["base"].items() if k != "path"}, **info}

    async def _base(self, run, world: int, t_unit="s") -> dict:
        """The checkpoint the sweep starts from: a fresh one of the running world (``checkpoint_now``), else the
        latest usable one in the record (and the result says so)."""
        if run.running and run.rebuilding:
            raise Refused(T("the world is still being restored along the record: start the sweep when the record resumes"),
                          status=409)
        if run.running and checkpoint_now_supported():
            return await self._checkpoint_now(run, world)
        try:
            lw = run._latest_world()
        except RuntimeError as e:
            raise Refused(text_of(e)) from None
        ck = lw["checkpoint"]
        if ck is None:
            raise Refused(T("the world has no usable saved state (it is written at a pause and every 2 minutes of "
                            "computing)"),
                          T("press ⏺, let the world compute for a few seconds and pause it — then repeat the sweep"))
        tail = ck.get("commands") or []
        n_fr = sum(1 for c in tail if "frame" in c)
        n_cmd = len(tail) - n_fr
        now_t = run.meta.get("sim_t")
        if run.running:
            note = T("The sweep starts from the world's latest saved state, t = {t} (the world is now at t = {now}): "
                     "a worker of this version cannot save a fresh state", t=fmt_t(ck["t"], t_unit),
                     now=fmt_t(now_t, t_unit))
        else:
            note = T("The run is suspended: the sweep starts from its latest saved state, t = {t}",
                     t=fmt_t(ck["t"], t_unit))
        if n_fr or n_cmd:
            note = T("{note}; after it the record holds {frames:d} more frames and {changes:d} changes — they are not "
                     "in the sweep", note=note, frames=n_fr, changes=n_cmd)
        return {"path": ck["file"], "t": ck["t"], "world": int(lw["header"].get("world", 1)), "source": "latest",
                "file": Path(ck["file"]).name, "bytes": ck.get("bytes"), "note": note}

    async def _checkpoint_now(self, run, world: int) -> dict:
        from . import checkpoint as CK, protocol, registry  # noqa: PLC0415
        tag = "sweep-" + secrets.token_hex(6)  # made here: the client routes cannot send this command (review F6)
        run.command({"cmd": "checkpoint_now", "args": {"tag": tag}}, "sweep")
        try:
            await run.proc.stdin.drain()
        except (ConnectionError, AttributeError):
            pass
        deadline = time.monotonic() + 120.0
        seen: set = set()
        meta = None
        while meta is None:
            cache: dict = {}
            try:
                ents = run.entries
                for e in reversed(ents[-5000:]):
                    if e.kind != "checkpoint" or (e.seg, e.offset) in seen:
                        continue
                    seen.add((e.seg, e.offset))
                    m = protocol.peek_meta(run._read(e, cache))
                    if m.get("tag") == tag:
                        meta = m
                        break
            finally:
                for f in cache.values():
                    f.close()
            if meta is not None:
                break
            if not run.running:
                raise Refused(T("the run's worker ended without saving the world's state: repeat the sweep"), status=409)
            if time.monotonic() > deadline:
                busy = (run.busy or {}).get("what")
                raise Refused(T("the world did not save its state within 2 min (it is busy: {busy})", busy=busy) if busy
                              else T("the world did not save its state within 2 min"),
                              T("repeat the sweep when the world is free"), status=409)
            await asyncio.sleep(0.1)
        if meta.get("error"):
            raise Refused(T("the world's state was not saved: {error}", error=meta["error"]),
                          T("a sweep of this world is not possible"), status=409)
        name = str(meta.get("file") or "")
        root = registry.ROOT.parent
        if not CK.NAME.match(name) or int(meta.get("world", 0)) != int(world):
            raise Refused(T("the worker answered with another state of the world: repeat the sweep"), status=409)
        if meta.get("env") != CK.runtime_env() or not isinstance(meta.get("files"), list) \
                or CK.files_hash(root, meta["files"]) != meta.get("code"):
            raise Refused(T("the engine's code or the libraries changed after this world was started: the sweep would "
                            "compute it with other code"),
                          T("suspend the run and continue it (⏺) — or start a new world"), status=409)
        path = run.ckpt_dir / name
        while not path.is_file():  # the worker writes it in the background (lfviz.checkpoint.Writer)
            if time.monotonic() > deadline + 60.0:
                raise Refused(T("the file of the saved state never appeared: repeat the sweep"), status=409)
            await asyncio.sleep(0.1)
        return {"path": str(path), "t": meta.get("t"), "world": int(meta.get("world", 1)), "source": "now",
                "file": name, "bytes": meta.get("bytes"), "note": ""}

    async def _spawn(self, run, spec: Path, log_path: Path, mem: int):
        from . import limits, registry  # noqa: PLC0415
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(registry.SERVER), str(registry.ROOT), str(registry.ENGINE)])
        env.setdefault("OMP_NUM_THREADS", "2")
        env.setdefault("OPENBLAS_NUM_THREADS", "2")
        env[limits.ENV] = str(int(mem))  # its own hard limit, below a world's (review F9)
        if os.environ.get("LFVIZ_SWEEP_GPU") != "1":
            env["LFPHYS_NO_GPU"] = "1"  # the CPU: GPU 0 belongs to the live worlds and their thermal guard (F9)
        log = open(log_path, "ab")
        try:
            return await asyncio.create_subprocess_exec(
                sys.executable, "-m", "lfviz.sweep", "--file", str(spec),
                stdin=asyncio.subprocess.DEVNULL, stdout=log, stderr=log, env=env, cwd=str(registry.ROOT))
        finally:
            log.close()

    async def _watch(self, run, n: int, proc):
        """Wait for the process; meanwhile, once a second, end it when its run was deleted or removed (F3) or when it
        is still running ``WATCH_GRACE_S`` after ``OVERRUN`` × the budget (F2: the process checks its clock between
        the world's steps, and a single step may be longer than the budget)."""
        a = self.active.get((run.id, n)) or {}
        limit = OVERRUN * float(a.get("budget") or budget_s()) + WATCH_GRACE_S
        t0 = time.monotonic()
        waiter = asyncio.ensure_future(proc.wait())
        while True:
            done, _ = await asyncio.wait({waiter}, timeout=1.0)
            if done:
                break
            why = None
            if self.mgr.runs.get(run.id) is not run or not run.dir.is_dir():
                why = "gone"
            elif time.monotonic() - t0 > limit:
                why = "over"
            if why and not a.get("killed"):
                a["killed"] = why
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
        rc = waiter.result()
        self.active.pop((run.id, n), None)
        if a.get("killed") == "gone":
            return  # the run's folder went with it: nothing to write
        path = self.spec_path(run, n)
        try:
            spec = json.loads(path.read_text(), object_hook=json_hook)
        except (OSError, ValueError):
            spec = None
        if spec is not None and spec.get("state") in ("starting", "running"):
            k = len(spec.get("results") or [])
            if a.get("cancel"):
                spec.update(state="cancelled", message=T(
                    "Cancelled: {k:d} of {n:d} values computed; they are kept", k=k, n=len(spec["request"]["values"])))
            elif a.get("killed") == "over":
                spec.update(state="over_budget", message=T(
                    "Stopped by the server: the sweep computed longer than {limit} (the budget {budget} × {k:g} and "
                    "{grace} of margin) — one step of the world was longer than the limit. {n:d} values computed, they "
                    "are kept; reduce the duration or the world's step", limit=fmt_wall(limit),
                    budget=fmt_wall(a.get("budget")), k=OVERRUN, grace=fmt_wall(WATCH_GRACE_S), n=k))
            elif rc and rc < 0:
                spec.update(state="failed", message=T(
                    "The sweep's process was stopped by the system (signal {sig:d}): probably the container ran out of "
                    "memory. The computed values are kept", sig=-rc))
            else:
                spec.update(state="failed", message=T(
                    "The sweep's process exited with code {code} (details in sweeps/{n:d}.log). The computed values "
                    "are kept", code=rc, n=n))
            spec["ended"] = _now_iso()
            try:
                _write_json(path, spec)
            except OSError:
                pass
        try:
            (self.folder(run) / f"{n}.base.pkl").unlink(missing_ok=True)
        except OSError:
            pass

    # --- read, list, cancel, remove -----------------------------------------------------------------------------
    def read(self, run, n: int) -> dict:
        path = self.spec_path(run, n)
        spec = json.loads(path.read_text(), object_hook=json_hook)  # OSError / ValueError: the caller answers 404
        active = (run.id, n) in self.active
        if not active and spec.get("state") in ("starting", "running"):  # the server restarted under it
            spec.update(state="interrupted", message=T("The sweep was interrupted: the server restarted. The computed "
                                                       "values are kept"), ended=_now_iso())
            _write_json(path, spec)
            (self.folder(run) / f"{n}.base.pkl").unlink(missing_ok=True)
        spec["active"] = active
        spec.pop("backend", None)
        if isinstance(spec.get("base"), dict):
            spec["base"].pop("path", None)
        return spec

    def list(self, run) -> list:
        folder = self.folder(run)
        out = []
        if not folder.is_dir():
            return out
        for p in sorted(folder.iterdir(), key=lambda q: int(SPEC.match(q.name).group(1)) if SPEC.match(q.name) else 0):
            m = SPEC.match(p.name)
            if not m:
                continue
            try:
                s = self.read(run, int(m.group(1)))
            except (OSError, ValueError):
                continue
            out.append({k: s.get(k) for k in ("n", "state", "created", "ended", "request", "progress", "message",
                                               "target_label", "target_unit", "measure_label", "measure_unit",
                                               "stat_text", "t_unit", "active")})
        return out

    async def cancel(self, rid: str, n: int, run=None) -> dict:
        """Stop a running sweep, keeping what it computed. Idempotent (review F10): a sweep not running answers that it
        is stopped already. ``run`` may be None: its run was deleted meanwhile (review F3)."""
        a = self.active.get((rid, n))
        if a is None:
            if run is None or not self.spec_path(run, n).is_file():
                raise Refused(T("there is no such sweep"), status=404)
            state = json.loads(self.spec_path(run, n).read_text(), object_hook=json_hook).get("state")
            return {"ok": True, "already": True, "state": state, "text": T("the sweep has stopped already")}
        a["cancel"] = True
        proc, task = a.get("proc"), a.get("task")
        if proc is None:
            raise Refused(T("the sweep is still starting: try cancelling again in a second"), status=409)
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        if task is not None:
            await asyncio.wait_for(asyncio.shield(task), 30.0)
        return {"ok": True, "cancelled": n}

    def remove(self, run, n: int) -> dict:
        """Remove a finished sweep with its results; refused while it runs (review F10: a second "cancel" removed what
        the first one kept)."""
        if (run.id, n) in self.active:
            raise Refused(T("the sweep is still running: first “✕ cancel”, then remove"), status=409)
        path = self.spec_path(run, n)
        if not path.is_file():
            raise Refused(T("there is no such sweep"), status=404)
        for p in (path, self.folder(run) / f"{n}.log", self.folder(run) / f"{n}.base.pkl"):
            p.unlink(missing_ok=True)
        return {"ok": True, "removed": n}

    async def shutdown(self):
        for a in list(self.active.values()):
            a["cancel"] = True
            if a.get("proc") is not None:
                try:
                    a["proc"].kill()
                except ProcessLookupError:
                    pass
        tasks = [a["task"] for a in self.active.values() if a.get("task") is not None]
        if tasks:
            await asyncio.wait(tasks, timeout=10.0)


def table_csv(spec: dict, lang: str = "en") -> str:
    """The table of a sweep: its set-up in «#» lines (the base moment, the duration, the sampling, how the measure was
    read — review F7), then one header line and a row per value. Its texts in ``lang`` (the player's language; English
    by default), the third «#» line in ``key=value`` form for programs."""
    import csv  # noqa: PLC0415
    import io  # noqa: PLC0415
    R = lambda x: render_in(x, lang)  # noqa: E731
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    tu, mu, unit = spec.get("target_unit") or "", spec.get("measure_unit") or "", spec.get("t_unit") or "s"
    req, base = spec.get("request") or {}, spec.get("base") or {}
    smp = spec.get("sampling") or (sampling(req) if req else {})
    sampler = spec.get("sampler")
    src = {"now": T("the world at the moment the sweep started"),
           "latest": T("the world's latest saved state")}.get(base.get("source"), "")
    buf.write("# " + R(T("sweep no. {n} of run {run}: {target} → {measure} ({stat})", n=spec.get("n"), run=spec.get("run"),
                         target=spec.get("target_text") or "", measure=spec.get("measure_label") or "",
                         stat=spec.get("stat_text") or "")) + "\r\n")
    line = T("from t = {t} ({source}, world {world}); each value — {duration} of the world; {n:d} readings", t=fmt_t(
        base.get("t"), unit), source=src, world=base.get("world"), duration=fmt_t(req.get("duration"), unit),
        n=smp.get("readings"))
    if smp.get("dt"):
        line = T("{text}, {dt} apart", text=line, dt=fmt_t(smp.get("dt"), unit))
    if sampler:
        line = T("{text}; the quantity was read through {sampler}()", text=line, sampler=sampler)
    buf.write("# " + R(line) + "\r\n")
    buf.write(f"# base_t={base.get('t')!r}; t_unit={render_in(unit, 'en')}; duration={req.get('duration')!r}; "
              f"window={req.get('window')!r}; stat={req.get('stat')}; n_samples={req.get('n_samples')}; "
              f"readings={smp.get('readings')}; dt_readings={smp.get('dt')!r}; sampler={sampler}; "
              f"source={base.get('source')}; state={spec.get('state')}\r\n")
    w.writerow([R(with_unit(spec.get("target_label"), tu)),
                R(with_unit(T("{label} ({stat})", label=spec.get("measure_label") or "", stat=spec.get("stat_text") or ""),
                            mu)), R(T("note"))])
    for r in spec.get("results") or []:
        v, m = r.get("value"), r.get("measured")
        w.writerow([repr(v) if isinstance(v, float) else v, "" if m is None else repr(float(m)),
                    R(r.get("error") or r.get("note") or "")])
    return buf.getvalue()


try:  # the sweeps' registry of an app (the tests reach the processes through it)
    from aiohttp import web as _web
    SWEEPS = _web.AppKey("sweeps", SweepManager)
except ImportError:  # the sweep process does not need aiohttp
    SWEEPS = "lfviz.sweeps"


def add_routes(app, mgr):
    from aiohttp import web  # noqa: PLC0415
    SW = SweepManager(mgr)
    app[SWEEPS] = SW

    def js(data, status=200):
        return web.json_response(data, status=status, dumps=lambda d: json.dumps(d, ensure_ascii=False, default=str))

    def refused(e: Refused):
        return js(error_body(e.text, **({"hint": e.hint} if e.hint else {}), **e.extra), e.status)

    def run_of(request):
        return mgr.get(request.match_info["id"])

    def n_of(request) -> int:
        s = request.match_info["n"]
        if not (s.isascii() and s.isdigit()) or len(s) > 9:  # «²» is a digit to isdigit (review F12)
            raise Refused(T("there is no such sweep"), status=404)
        return int(s)

    async def post(request):
        try:
            run = run_of(request)
        except KeyError:
            return js(error_body(T("there is no such run")), 404)
        try:
            body = await request.json()
        except ValueError:  # not JSON, or not UTF-8
            return js(error_body(T("the request body is not JSON")), 400)
        try:
            return js(await SW.start(run, body))
        except Refused as e:
            return refused(e)

    async def get_list(request):
        try:
            return js(SW.list(run_of(request)))
        except KeyError:
            return js(error_body(T("there is no such run")), 404)

    async def get_one(request):
        try:
            run = run_of(request)
            spec = SW.read(run, n_of(request))
        except KeyError:
            return js(error_body(T("there is no such run")), 404)
        except Refused as e:
            return refused(e)
        except (OSError, ValueError):
            return js(error_body(T("there is no such sweep")), 404)
        if (request.query.get("format") or "").lower() == "csv":
            return web.Response(text=table_csv(spec, request.query.get("lang") or "en"), content_type="text/csv",
                                charset="utf-8", headers={
                "Content-Disposition": f'attachment; filename="{run.id}-sweep{spec["n"]}.csv"'})
        return js(spec)

    async def cancel(request):
        rid = request.match_info["id"]
        try:
            n = n_of(request)
            return js(await SW.cancel(rid, n, mgr.runs.get(rid)))
        except Refused as e:
            return refused(e)
        except (OSError, ValueError):
            return js(error_body(T("there is no such sweep")), 404)

    async def remove(request):
        try:
            return js(SW.remove(run_of(request), n_of(request)))
        except KeyError:
            return js(error_body(T("there is no such run")), 404)
        except Refused as e:
            return refused(e)

    async def on_cleanup(app):
        await SW.shutdown()

    app.on_cleanup.append(on_cleanup)
    app.router.add_post("/api/runs/{id}/sweep", post)
    app.router.add_get("/api/runs/{id}/sweeps", get_list)
    app.router.add_get("/api/runs/{id}/sweeps/{n}", get_one)
    app.router.add_post("/api/runs/{id}/sweeps/{n}/cancel", cancel)
    app.router.add_delete("/api/runs/{id}/sweeps/{n}", remove)
    return SW


# --- the sweep process ----------------------------------------------------------------------------------------------
class _Sink:
    """The output of a swept world: only its refusals and failures are kept (they are a value's result)."""

    def __init__(self):
        self.errors: list = []

    def emit(self, meta, blobs=None):
        if isinstance(meta, dict) and meta.get("type") == "error":
            text = meta.get("text") or ""
            self.errors.append(text if is_t(text) else str(text)[:1000])


class _OverBudget(Exception):
    def __init__(self, elapsed: float, projected: float | None = None):
        super().__init__("over budget")
        self.elapsed, self.projected = elapsed, projected


class _Gone(Exception):
    """The sweep's folder is gone (its run was deleted): the process ends without a word."""


class _Contract(Exception):
    """The world does not keep the instruments' contract (API P16.3 §2): the sweep cannot read it at all."""


class Clock:
    """The sweep process's wall clock and what it measured of the world's cost (review F2)."""

    def __init__(self, budget: float = 1e9, tick=None, folder: Path | None = None, w0: float | None = None):
        self.w0 = time.monotonic() if w0 is None else w0
        self.budget = float(budget)
        self.tick = tick or (lambda frac: None)
        self.folder = folder
        self.adv_wall = 0.0  # wall seconds spent advancing, the whole sweep
        self.adv_t = 0.0  # world time advanced, the whole sweep
        self.val_wall = self.val_t = 0.0  # the same for the value being computed
        self.projected: float | None = None
        self._dir_seen = time.monotonic()

    def new_value(self):
        self.val_wall = self.val_t = 0.0

    def advanced(self, wall: float, dt: float):
        self.adv_wall += wall
        self.adv_t += dt
        self.val_wall += wall
        self.val_t += dt

    def check(self, remaining_t: float | None = None):
        """Between pieces of an advance and between readings: stop beyond ``OVERRUN`` × the budget, or when the cost
        measured so far projects the sweep beyond it; end quietly when the sweep's folder is gone."""
        now = time.monotonic()
        if self.folder is not None and now - self._dir_seen >= 1.0:
            self._dir_seen = now
            if not self.folder.is_dir():
                raise _Gone()
        el = now - self.w0
        lim = OVERRUN * self.budget
        if el > lim:
            raise _OverBudget(el)
        if remaining_t is not None and self.adv_wall >= PROBE_S and self.adv_t > 0:
            rate = self.adv_wall / self.adv_t
            if self.val_wall >= 1.0 and self.val_t > 0:  # a value dearer than the ones before (a finer step, say)
                rate = max(rate, self.val_wall / self.val_t)
            self.projected = el + rate * max(0.0, remaining_t)
            if self.projected > lim:
                raise _OverBudget(el, self.projected)


def _value_of(raw):
    if raw is None or isinstance(raw, bool):
        return None
    try:
        x = float(raw)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _stat(req: dict, ts: list, vs: list) -> tuple[float | None, str]:
    """The measured number from the readings, and a note when some were undefined."""
    stat = req["stat"]
    bad = sum(1 for v in vs if v is None)
    if stat == "final":
        return vs[-1], (T("the quantity is undefined at the end") if vs[-1] is None else "")
    if stat == "mean_last":
        if bad:
            return None, T("the quantity is undefined in {bad:d} of the window's {n:d} readings", bad=bad, n=len(vs))
        span = ts[-1] - ts[0]
        if not span > 0:
            return vs[-1], ""
        acc = sum(0.5 * (vs[i] + vs[i + 1]) * (ts[i + 1] - ts[i]) for i in range(len(vs) - 1))
        return acc / span, ""
    ok = [v for v in vs if v is not None]
    if not ok:
        return None, T("the quantity is undefined in every reading")
    return (max(ok) if stat == "max" else min(ok)), (T("undefined in {bad:d} of {n:d} readings", bad=bad, n=len(vs))
                                                      if bad else "")


def _thin_trace(ts, vs, t0):
    k = max(1, -(-len(ts) // TRACE_POINTS))
    idx = list(range(0, len(ts), k))
    if idx[-1] != len(ts) - 1:
        idx.append(len(ts) - 1)
    return {"t": [ts[i] - t0 for i in idx], "v": [vs[i] for i in idx]}


# the stored value of a swept parameter as the section's on_set sees it in ``old`` when the swept value equals it (review
# F1): the same number or text for whatever the section computes with it, but equal to nothing, so that the parameter
# counts as changed and the value is applied again, as every other value of the sweep is
class _AgainFloat(float):
    __slots__ = ()

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    __hash__ = float.__hash__


class _AgainInt(int):
    __slots__ = ()

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    __hash__ = int.__hash__


class _AgainStr(str):
    __slots__ = ()

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    __hash__ = str.__hash__


AGAIN = (_AgainFloat, _AgainInt, _AgainStr)


def _again(v):
    """The always-unequal copy of a stored value, or None for a type that cannot have one (a flag: ``bool`` cannot be
    subclassed, and ``True != copy`` would ask ``bool`` first) — such a value equal to the stored one is not applied
    again, and its row says so."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return _AgainInt(v)
    if isinstance(v, float):
        return _AgainFloat(v)
    if isinstance(v, str):
        return _AgainStr(v)
    return None


def apply_change(runner, sim, req: dict, value) -> dict:
    """Apply one value to a fresh world as the live world would, at its current moment (review F1): a law by the
    runner's ``set``; an object's handle parameter (a position, a velocity) by the scene's ``edit``, which applies a
    value equal to the stored one too; any other parameter by the scene's ``set``, its stored value put into ``old`` as
    an always-unequal copy (``_again``) when the value equals it. Returns {how, applied?}: how it was applied and, when
    the world applied another value (a throw clamped to the largest speed), that value."""
    tg = req["target"]
    if tg["kind"] == "law":
        runner.handle({"cmd": "set", "args": {"values": {tg["id"]: value}}})
        return {"how": "set"}
    oid, pid = tg["obj"], tg["param"]
    objs = getattr(sim, "objects", None)
    obj = objs.get(oid) if isinstance(objs, dict) else None
    if obj is None:
        raise ValueError(T("the world's saved state has no object “{id}”", id=oid))
    ot = (getattr(sim, "PALETTE", None) or {}).get(obj.get("type"))
    handles = ot.handle_ids() if ot is not None else []
    if pid in handles:
        how = "edit"
        runner.handle({"cmd": "scene", "args": {"op": "edit", "id": oid, "values": {pid: value}}})
    else:
        how = "set"
        stored = obj["values"].get(pid)
        same = stored == value and type(stored) is type(value) or (
            isinstance(stored, (int, float)) and isinstance(value, (int, float)) and not isinstance(stored, bool)
            and not isinstance(value, bool) and stored == value)
        if same and _again(stored) is not None:
            obj["values"][pid] = _again(stored)
            how = "set_again"
        elif same:
            how = "set_same"  # a flag equal to its stored value: the world as it is (said in the row)
        try:
            runner.handle({"cmd": "scene", "args": {"op": "set", "id": oid, "values": {pid: value}}})
        finally:
            cur = sim.objects.get(oid)
            if cur is not None and isinstance(cur["values"].get(pid), AGAIN):  # refused and rolled back: the stored value
                cur["values"][pid] = stored
    out = {"how": how}
    cur = sim.objects.get(oid)
    if cur is not None and cur["values"].get(pid) != value:
        out["applied"] = cur["values"].get(pid)
    return out


def _read(sim, sampler: str, measure) -> tuple[dict, dict]:
    """One reading: ({id: value}, {id: note}). A world that answers in another form breaks the contract (Q3)."""
    if sampler == "measure":
        m = measure()
        if not isinstance(m, dict):
            raise _Contract(T("its measure() returned {type}, not a dict {quantity id: number}", type=type(m).__name__))
        return m, {}
    meta, _ = sim.frame()
    meas = meta.get("meas") if isinstance(meta, dict) else None
    if meas is None:
        meas = {}
    if not isinstance(meas, dict):
        raise _Contract(T("its frame carries “meas” as {type}, not as a dict {quantity id: number}",
                          type=type(meas).__name__))
    mn = meta.get("meas_note")
    return meas, (mn if isinstance(mn, dict) else {})


def run_value(data: bytes, req: dict, value, clock: Clock, later_t: float = 0.0) -> dict:
    """One value: a fresh world from the checkpoint, the change, the advance and the readings. ``later_t``: the world
    time the values after this one will advance (for the clock's projection)."""
    import queue  # noqa: PLC0415
    from . import checkpoint as CK  # noqa: PLC0415
    from .errors import owner_text  # noqa: PLC0415
    from .sim import Runner  # noqa: PLC0415
    w0 = time.monotonic()
    clock.new_value()
    sink = _Sink()
    state = CK.loads(data, sink.emit)
    sim = state["sim"]
    runner = Runner(sim, sink.emit, queue.Queue())
    runner.world = int(state.get("world", 1))
    restore_s = time.monotonic() - w0
    t0 = float(sim.t)
    applied = apply_change(runner, sim, req, value)
    if sink.errors:  # the world refused the change: that is this value's result
        return {"value": value, "measured": None, "error": sink.errors[0], "t0": t0, "restore_s": restore_s,
                "how": applied["how"], "wall_s": time.monotonic() - w0}
    dur, n = req["duration"], req["n_samples"]
    t_end = t0 + dur
    if req["stat"] == "final":
        grid = [t_end]
    elif req["stat"] == "mean_last":
        w = req["window"]
        grid = [t_end - w + w * i / n for i in range(n)] + [t_end]
    else:
        grid = [t0 + dur * i / n for i in range(n)] + [t_end]
    mid = req["measure"]
    measure = getattr(sim, "measure", None)
    sampler = "measure" if callable(measure) else "frame"
    ts, vs, notes = [], [], []
    sample_s = 0.0
    adv_s = 0.0
    try:
        for j, tgt in enumerate(grid):
            while sim.t < tgt:  # the world's own steps, in pieces of at most CHUNK_S of wall time (F2)
                a0, tb = time.monotonic(), float(sim.t)
                runner._advance(tgt, budget=CHUNK_S)
                dw = time.monotonic() - a0
                adv_s += dw
                clock.advanced(dw, float(sim.t) - tb)
                if not float(sim.t) > tb:
                    raise RuntimeError(T("the world did not advance in time from t = {t:.6g}", t=tb))
                clock.check(later_t + max(0.0, t_end - float(sim.t)))
            s0 = time.monotonic()
            meas, mn = _read(sim, sampler, measure)
            sample_s += time.monotonic() - s0
            ts.append(float(sim.t))
            vs.append(_value_of(meas.get(mid)))
            if vs[-1] is None:
                nt = mn.get(mid) or (T("the quantity is not measured in this frame") if mid not in meas else "")
                notes.append(nt if is_t(nt) else str(nt))
            clock.check(later_t + max(0.0, t_end - float(sim.t)))
            clock.tick((j + 1) / len(grid))
    except (_OverBudget, _Gone, _Contract):
        raise
    except Exception as e:  # noqa: BLE001 - the world failed while computing this value: that is its result
        import traceback  # noqa: PLC0415
        traceback.print_exc()
        text, detail = owner_text(e)
        return {"value": value, "measured": None,
                "error": T("The computation stopped at t = {t:.6g}: {text}", t=float(sim.t), text=text),
                "detail": detail, "t0": t0, "restore_s": restore_s, "how": applied["how"],
                "wall_s": time.monotonic() - w0}
    measured, note = _stat(req, ts, vs)
    if notes and not note:
        note = notes[-1]
    elif notes and notes[-1]:
        note = T("{text} ({why})", text=note, why=notes[-1])
    if "applied" in applied:
        ap = applied["applied"]
        num = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)  # noqa: E731
        note = join([note, T("the world applied {got:.6g} instead of {asked:.6g}", got=ap, asked=value)
                     if num(ap) and num(value) else T("the world applied {got} instead of {asked}", got=str(ap),
                                                      asked=str(value))], "; ")
    if applied["how"] == "set_same":
        note = join([note, T("equal to the flag's stored value: the world unchanged")], "; ")
    return {"value": value, "measured": measured, **({"note": note} if note else {}), "t0": t0, "t1": float(sim.t),
            "readings": len(vs), "sampler": sampler, "how": applied["how"],
            **({"applied": applied["applied"]} if "applied" in applied else {}),
            "trace": _thin_trace(ts, vs, t0), "restore_s": restore_s, "advance_s": adv_s,
            "sample_ms": 1e3 * sample_s / max(1, len(vs)), "wall_s": time.monotonic() - w0}


def _lower_priority():
    """The live worlds first: a lower CPU priority, and the first process the kernel ends when the container's memory
    runs out (``oom_score_adj`` 1000; raising one's own needs no privilege; review F9)."""
    try:
        os.nice(10)
    except OSError:
        pass
    try:
        with open("/proc/self/oom_score_adj", "w") as f:
            f.write("1000")
    except OSError:
        pass


def main(argv=None):
    import argparse  # noqa: PLC0415
    import gc  # noqa: PLC0415
    import traceback  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="Compute one parameter sweep of a run (spawned by the server; plan P16.3).")
    ap.add_argument("--file", required=True, help="the sweep's state file runs/<id>/sweeps/<n>.json")
    a = ap.parse_args(argv)

    from . import limits, registry  # noqa: PLC0415
    limits.apply_hard_limit()  # before anything large is allocated (RULES.md §3, «Memory budget»)
    _lower_priority()
    registry.ensure_path()
    sys.stdout = sys.stderr
    path = Path(a.file)
    spec = json.loads(path.read_text(), object_hook=json_hook)
    req = spec["request"]
    values = req["values"]
    bud = float(spec.get("budget_s") or budget_s())
    last_write = [0.0]
    w0 = time.monotonic()

    def write(force=False):
        now = time.monotonic()
        if force or now - last_write[0] >= 1.0:
            last_write[0] = now
            el = now - w0
            done = spec["progress"]["done"]
            eta = clock.projected - el if clock.projected is not None else (
                el / done * (len(values) - done) if done else None)
            spec["progress"].update(elapsed_s=el, eta_s=eta)
            if not path.parent.is_dir():
                raise _Gone()
            _write_json(path, spec)

    def tick(frac_in_value: float):
        spec["progress"]["frac"] = (spec["progress"]["done"] + frac_in_value) / len(values)
        write()

    clock = Clock(bud, tick, path.parent, w0)
    try:
        from .errors import owner_text  # noqa: PLC0415
        try:  # the run's devices and precisions (plan P11), as its worker has them
            from lfphys.core import backend as _backend  # noqa: PLC0415
            notes = _backend.configure(spec.get("backend") or {})
            if notes:
                spec["backend_notes"] = list(notes)
        except Exception as e:  # noqa: BLE001
            spec["backend_notes"] = [T("the device settings were not applied: {error}", error=text_of(e))]
        registry.load(spec["viz"])  # the world's modules (the checkpoint names them)
        base = Path(spec["base"]["path"])
        data = base.read_bytes()
        if base.parent == path.parent and base.name.endswith(".base.pkl"):  # held in memory from now on
            base.unlink(missing_ok=True)
        spec.update(state="running", started=_now_iso())
        write(force=True)
        for i, v in enumerate(values):
            try:
                r = run_value(data, req, v, clock, later_t=req["duration"] * (len(values) - i - 1))
            except (_OverBudget, _Gone, _Contract):
                raise
            except Exception as e:  # noqa: BLE001 - the state did not load or the change failed outside the world
                traceback.print_exc()
                text, detail = owner_text(e, "restore")
                r = {"value": v, "measured": None, "error": text, "detail": detail}
            spec["results"].append(r)
            spec["progress"]["done"] = i + 1
            spec["progress"]["frac"] = (i + 1) / len(values)
            if "sampler" in r:
                spec["sampler"] = r["sampler"]
                spec.setdefault("measured_cost", {"restore_s": r["restore_s"], "advance_s": r["advance_s"],
                                                  "sample_ms": r["sample_ms"], "duration": req["duration"]})
            gc.collect()
            el = time.monotonic() - w0
            if i + 1 < len(values) and el / (i + 1) * len(values) > OVERRUN * bud:
                raise _OverBudget(el, el / (i + 1) * len(values))
            write(force=True)
        ok = sum(1 for r in spec["results"] if r.get("measured") is not None)
        if ok:
            spec.update(state="done", ended=_now_iso(), message=T("Done: {k:d} of {n:d} values measured", k=ok,
                                                                    n=len(values)))
        else:  # nothing measured is not "done" (review LB1-p02-ux X7)
            first = next((r.get("error") or r.get("note") for r in spec["results"] if r.get("error") or r.get("note")),
                         "")
            spec.update(state="failed", ended=_now_iso(), message=(
                T("None of the {n:d} values was measured: {first} — the reasons per value are in the table",
                  n=len(values), first=first) if first
                else T("None of the {n:d} values was measured — the reasons per value are in the table",
                       n=len(values))))
    except _Gone:
        return 0  # the run was deleted: its folder went with the sweep
    except _OverBudget as e:
        k = len(spec["results"])
        lim = OVERRUN * bud
        how = (T("at the measured cost of computing, the whole sweep would take about {t}", t=fmt_wall(e.projected))
               if e.projected is not None else T("it has computed for {t} already", t=fmt_wall(e.elapsed)))
        spec.update(state="over_budget", ended=_now_iso(), message=T(
            "Stopped after {elapsed}: {how} — more than {limit} (the budget {budget} × {k:g}). Values computed: {n:d}, "
            "they are kept; reduce the number of values, the duration or the number of readings",
            elapsed=fmt_wall(e.elapsed), how=how, limit=fmt_wall(lim), budget=fmt_wall(bud), k=OVERRUN, n=k))
    except _Contract as e:
        traceback.print_exc()
        spec.update(state="failed", ended=_now_iso(), message=T(
            "The sweep was not computed: the world “{viz}” breaks the instruments' contract (API P16.3 §2) — {error}. "
            "It is the world's error, not the chosen values': a sweep in it is not possible until it is fixed",
            viz=spec.get("viz"), error=text_of(e)))
    except Exception as e:  # noqa: BLE001 - the sweep as a whole failed: why, for the owner
        traceback.print_exc()
        from .errors import owner_text  # noqa: PLC0415
        text, detail = owner_text(e, "restore")
        spec.update(state="failed", ended=_now_iso(), message=T("The sweep was not computed: {why}", why=text),
                    detail=detail)
    spec["progress"]["frac"] = 1.0
    try:
        write(force=True)
    except _Gone:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
