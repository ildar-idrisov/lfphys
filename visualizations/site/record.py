# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The offline recorder of the public site (design of the start page §4.1, §4.3; CONTRACT of steps S and P).

    python3 site/record.py --world u32_double_slit [--world ...] [--out DIR]
    python3 site/record.py --all | --stale [--out DIR]

For every recording spec of a world (``VIZ["recordings"]``, ``registry.recordings_of``) it runs the world headless with
``lfviz.sim.Runner`` (as ``tests/harness.py`` does) on a frame clock of its own: the world's first frame at its start,
then one frame every ``speed / fps`` of world time, exactly ``seconds × fps`` frames, with no wall-time budget, so the
result does not depend on the speed of the CPU. The spec's ``script`` is applied at its frame (``round(at × fps)``:
the world is advanced to that frame's time, the command applied, then the frame drawn). The stream it writes is an
ordinary ``LFVREC1`` record: the header and the world's messages as a worker emits them, ``state`` (start, then
playing), the frames, ``end {reason: "recording"}``; the ``checkpoint``, ``command``, ``resumed`` and ``record_segment``
messages are dropped (they serve the resumption of a live run only). The file is the same bytes for the same spec and
code (integrator D6): the frames carry no ``cpu_ms`` and no ``speed_actual`` (the recorder's CPU time goes into the
index as ``cpu_s``), and the header's kernels (``backend.used``) are this recording's own, not the process's so far.

A recording fails on an error message or an exception of the world, and when a check of the world ends failed (its
last state ✗, as the player draws it; a check marked ``expected`` is a ✗ on purpose and does not fail; integrator D5).
The index entry counts the checks' last states (``checks``: ok, failed, expected, info, na).

Budgets (``sitelib.BUDGET``): over the target (3 MB per file, 12 MB per world, gzip) the frames are thinned by a stride
(every k-th frame kept, the first, the last and the poster frame always; every other message is kept); never below
``MIN_KEPT_FPS`` frames per played second. Over the hard limit (10 MB, 25 MB) after thinning the recording fails: shorten
``seconds`` or lower ``fps`` in the world's spec.

Output, per world: ``<out>/<world>/<rec>.<hash8>.lfrec.gz`` (gzip -9 of the stream; ``hash8``: of the file's bytes, so a
new recording has a new name) and ``<out>/<world>/index.json`` (CONTRACT). ``poster_t`` is the world time of the
poster frame (the player seeks to it), ``poster_frame`` its index among the frames in the file.

``--stale`` records every world whose recordings are not all present with their current key (``plan.py``); a world is
always recorded whole. Exit code: 0 when everything was recorded within the hard limits, 1 otherwise.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
import os
import queue
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitelib as L  # noqa: E402

from lfviz import limits, protocol, registry  # noqa: E402
from lfviz.i18n import join, render_in  # noqa: E402
from lfviz.sim import Runner  # noqa: E402

#: messages that serve only the resumption of a live run (design §4.1), and what a worker never records
DROP = {"checkpoint", "command", "resumed", "record_segment", "busy", "scene_export"}
#: what the runner adds to a frame from the wall clock or the CPU: never in a recording (integrator D6)
FRAME_TIMING = ("cpu_ms", "speed_actual")
STRIDES = (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 24, 30, 32, 40, 48, 60)


class RecordingFailed(Exception):
    pass


@dataclass
class Raw:
    """A recorded stream before thinning: every message encoded, the frames marked."""
    spec: dict
    msgs: list = field(default_factory=list)  # (type, t, bytes)
    frames: list = field(default_factory=list)  # indexes into msgs of the frames, in order
    worlds: int = 0
    poster_k: int = 0  # the poster's frame (0-based among all frames)
    seconds_cpu: float = 0.0
    checks: dict = field(default_factory=dict)  # (world, check id) -> its last state (check_state)
    flips: list = field(default_factory=list)  # (world, id, t) where a check was ✗ before its last state


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
class Packed:
    """A stream thinned with a stride, compressed."""
    stride: int
    data: bytes
    gz: bytes
    kept: list  # the kept frames' numbers (0-based among all frames)
    poster_frame: int  # the poster's index among the kept frames


def _log(*a):
    print(*a, file=sys.stderr, flush=True)


def record(viz_id: str, spec: dict) -> Raw:
    """Run one recording spec of a world headless and return its messages (RecordingFailed on any error message or
    exception of the world: a recording of a failing world is not shipped)."""
    viz = registry.load(viz_id)
    fps = int(spec["fps"])
    n = int(round(float(spec["seconds"]) * fps))
    seed = int(spec.get("seed") if spec.get("seed") is not None else 1)
    raw = Raw(spec=dict(spec))
    errors = []

    def emit(meta, blobs=None):
        typ = meta.get("type")
        if typ in DROP:
            return
        if typ == "frame":  # no wall-clock or CPU time in a recording (D6)
            meta = {k: v for k, v in meta.items() if k not in FRAME_TIMING}
        data = protocol.encode(meta, blobs)
        if typ == "frame":
            raw.frames.append(len(raw.msgs))
        elif typ == "header":
            raw.worlds += 1
        elif typ == "error":
            errors.append(meta.get("text"))
        elif typ == "check" and meta.get("id") is not None:
            key = (raw.worlds, str(meta["id"]))
            if raw.checks.get(key) == "failed":
                raw.flips.append((*key, meta.get("t")))
            raw.checks[key] = check_state(meta)
        t = meta.get("t")
        raw.msgs.append((typ, float(t) if isinstance(t, (int, float)) else None, data))

    try:  # the devices of the engine's kernels, as a worker configures them (LFPHYS_NO_GPU=1: the CPU); the kernels
        # this process ran for an earlier recording are forgotten, so the header names this recording's own (review F1)
        from lfphys.core import backend as _backend
        _backend.reset_used()
        notes = _backend.configure({})
    except Exception:  # noqa: BLE001 - the engine without the backend
        notes = []

    def make_world(pr, values, sd):
        p, errs = viz["schema"].resolve(pr, values or {})
        if errs:
            raise ValueError(join(errs, "; "))
        limits.check_estimate(viz["simulation"], p)
        return viz["simulation"](p, seed if sd in (None, "") else int(sd), emit), {"preset": pr}

    params, errs = viz["schema"].resolve(spec["preset"], {})
    if errs:
        raise RecordingFailed(f"{viz_id}/{spec['id']}: preset {spec['preset']!r}: {[render_in(e) for e in errs]}")
    limits.check_estimate(viz["simulation"], params)
    t0 = time.process_time()
    sim = viz["simulation"](params, seed, emit)
    runner = Runner(sim, emit, queue.Queue(), fps=float(fps), make_world=make_world,
                    world_info={"preset": spec["preset"], "backend_notes": notes})

    def fail(why):
        raise RecordingFailed(f"{viz_id}/{spec['id']}: {why}")

    if not runner.start():
        fail(f"the world was not built: {[render_in(e) for e in errors]}")
    runner._state("start")
    if spec.get("speed") is not None:
        runner.handle({"cmd": "speed", "args": {"value": float(spec["speed"])}})
    runner.handle({"cmd": "play"})
    script = {}
    for c in spec.get("script") or []:
        script.setdefault(min(n - 1, int(round(float(c["at"]) * fps))), []).append(c)
    last = time.monotonic()
    for k in range(n):
        try:
            if k:
                runner._advance(runner.sim.t + runner.speed / fps)
            for c in script.get(k, []):
                runner.handle({"cmd": c["cmd"], "args": dict(c.get("args") or {})})
            runner._frame(0.0)  # emit() drops the runner's timing fields
        except Exception as e:  # noqa: BLE001 - the physics failed: no recording
            fail(f"frame {k} of {n}: {type(e).__name__}: {e}")
        if errors:
            fail(f"the world reported an error at frame {k}: {render_in(errors[0])}")
        if time.monotonic() - last > 60:
            last = time.monotonic()
            _log(f"  {viz_id}/{spec['id']}: frame {k + 1} of {n}, t = {runner.sim.t:.6g}")
    emit({"type": "end", "t": runner.sim.t, "reason": "recording"})
    if len(raw.frames) != n:
        fail(f"{len(raw.frames)} frames instead of {n}")
    raw.poster_k = min(n - 1, max(0, int(round(float(spec.get("poster") or 0) * fps))))
    raw.seconds_cpu = time.process_time() - t0
    bad = sorted(f"{cid} (world {w})" for (w, cid), st in raw.checks.items() if st == "failed")
    if bad:
        fail(f"{len(bad)} check(s) end failed: {', '.join(bad)}")
    if raw.flips:
        _log(f"  note: {viz_id}/{spec['id']}: a check was ✗ before its last state: "
             f"{sorted({f'{cid} (world {w})' for w, cid, _t in raw.flips})}")
    return raw


def check_counts(raw: Raw) -> dict:
    """The checks' last states of a recording, counted (the index entry's ``checks``)."""
    out = {"ok": 0, "failed": 0, "expected": 0, "info": 0, "na": 0}
    for st in raw.checks.values():
        out[st] = out.get(st, 0) + 1
    return out


def pack(raw: Raw, stride: int) -> Packed:
    """The stream with every ``stride``-th frame kept (the first, the last and the poster's always; every other message
    always), and its gzip -9."""
    n = len(raw.frames)
    keep_k = {k for k in range(n) if k % stride == 0} | {n - 1, raw.poster_k}
    drop_i = {raw.frames[k] for k in range(n) if k not in keep_k}
    parts = [protocol.MAGIC]
    for i, (_typ, _t, data) in enumerate(raw.msgs):
        if i not in drop_i:
            parts.append(protocol.frame_stream_item(data))
    data = b"".join(parts)
    kept = sorted(keep_k)
    return Packed(stride, data, gzip.compress(data, compresslevel=9, mtime=0), kept, kept.index(raw.poster_k))


def max_stride(raw: Raw) -> int:
    fps = float(raw.spec["fps"])
    return max(1, int(fps // L.MIN_KEPT_FPS))


def thin_to(raw: Raw, target: int, start: int = 1) -> Packed:
    """The smallest stride from ``start`` (``STRIDES``, up to ``max_stride``) whose gzip fits ``target``. When none
    does (a large message that is not a frame dominates: u38's volume), the smallest stride within 10 % of the smallest
    size: thinning that saves little would only make the playback jerky."""
    tried = []
    for s in [x for x in STRIDES if start <= x <= max_stride(raw)] or [start]:
        tried.append(pack(raw, s))
        if len(tried[-1].gz) <= target:
            return tried[-1]
    least = min(len(p.gz) for p in tried)
    return next(p for p in tried if len(p.gz) <= 1.1 * least)


def record_world(viz_id: str, out: Path, only: list[str] | None = None) -> tuple[dict, list[str]]:
    """Record every spec of a world (or those named in ``only``), thin them to the budgets, write the files and the
    index. Returns (index, problems): a problem is a budget exceeded or a recording that failed."""
    plan = L.planned_world(viz_id)
    viz = registry.load(viz_id)
    problems = []
    raws, packs = {}, {}
    file_target, file_limit = L.BUDGET["file"]
    world_target, world_limit = L.BUDGET["world"]
    for r in plan["recordings"]:
        if only and r["id"] not in only:
            continue
        _log(f"{viz_id}/{r['id']}: {r['seconds']} s × {r['fps']} fps, preset {r['preset']}")
        try:
            raws[r["id"]] = record(viz_id, r)
        except RecordingFailed as e:
            problems.append(str(e))
            _log(f"  FAILED: {e}")
            continue
        except MemoryError as e:
            problems.append(f"{viz_id}/{r['id']}: out of memory: {e}")
            _log(f"  FAILED: out of memory")
            continue
        packs[r["id"]] = thin_to(raws[r["id"]], file_target)
        p = packs[r["id"]]
        _log(f"  {len(raws[r['id']].frames)} frames, cpu {raws[r['id']].seconds_cpu:.0f} s, stride {p.stride}: "
             f"{len(p.data) / L.MB:.2f} MB, gzip {len(p.gz) / L.MB:.2f} MB")
    # the world's budget: thin the largest recording further while the world is over its target
    while sum(len(p.gz) for p in packs.values()) > world_target:
        cand = [(len(p.gz), rid) for rid, p in packs.items()
                if p.stride < max_stride(raws[rid]) and not raws[rid].spec.get("_no_thin")]
        if not cand:
            break
        _, rid = max(cand)
        nxt = [s for s in STRIDES if s > packs[rid].stride and s <= max_stride(raws[rid])]
        thinner = pack(raws[rid], nxt[0])
        if len(thinner.gz) > 0.97 * len(packs[rid].gz):  # frames are not what makes it large: leave it
            raws[rid].spec["_no_thin"] = True
            _log(f"  world over {world_target / L.MB:.0f} MB: {rid} not thinned (its frames are not what makes it large)")
        else:
            packs[rid] = thinner
            _log(f"  world over {world_target / L.MB:.0f} MB: {rid} to stride {packs[rid].stride}, "
                 f"gzip {len(packs[rid].gz) / L.MB:.2f} MB")
    for rid, p in packs.items():
        if len(p.gz) > file_limit:
            problems.append(f"{viz_id}/{rid}: {len(p.gz) / L.MB:.2f} MB after thinning (stride {p.stride}) is over the "
                            f"hard limit of {file_limit / L.MB:.0f} MB: shorten seconds or lower fps")
        elif len(p.gz) > file_target:
            why = L.accepted(viz_id, rid)
            _log(f"  note: {viz_id}/{rid} is {len(p.gz) / L.MB:.2f} MB, over the target of {file_target / L.MB:.0f} MB "
                 f"(within the hard limit; " + (f"accepted: {why})" if why else "not accepted: shorten seconds)"))
    total = sum(len(p.gz) for p in packs.values())
    if total > world_limit:
        problems.append(f"{viz_id}: {total / L.MB:.2f} MB for the world is over the hard limit of "
                        f"{world_limit / L.MB:.0f} MB")
    folder = Path(out) / viz_id
    folder.mkdir(parents=True, exist_ok=True)
    old = L.read_index(out, viz_id) or {}
    made = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    entries = []
    for r in plan["recordings"]:
        p = packs.get(r["id"])
        if p is None:  # not recorded now (failed or not asked): keep an old entry only when it is still current (its
            # key is the one the registry gives now, so its code, version and spec are today's: review F9)
            prev = next((e for e in old.get("recordings") or [] if e.get("id") == r["id"]), None)
            if prev and prev.get("key") == r["key"] and (folder / prev.get("file", "")).is_file():
                entries.append({"version": plan["version"], "code_hash": plan["code_hash"],
                                "made": old.get("made", ""), **prev})
            elif prev:
                _log(f"  {viz_id}/{r['id']}: its old recording is stale (key {prev.get('key')}, now {r['key']}): dropped")
            continue
        raw = raws[r["id"]]
        sha = hashlib.sha256(p.gz).hexdigest()
        name = f"{r['id']}.{sha[:8]}.lfrec.gz"
        (folder / name).write_bytes(p.gz)
        frames_t = [raw.msgs[raw.frames[k]][1] for k in range(len(raw.frames))]
        entries.append({
            "id": r["id"], "preset": r["preset"], "label": r["label"], "file": name,
            "seconds": r["seconds"], "fps": r["fps"], "speed": r.get("speed"), "seed": r.get("seed", 1),
            "frame_stride": p.stride, "frames": len(p.kept), "frames_recorded": len(raw.frames),
            "bytes": len(p.data), "bytes_gz": len(p.gz),
            "poster": r.get("poster", 0), "poster_t": frames_t[raw.poster_k], "poster_frame": p.poster_frame,
            "t_end": frames_t[-1], "worlds": raw.worlds, "script": r.get("script") or [],
            "checks": check_counts(raw), "cpu_s": round(raw.seconds_cpu, 1), "sha256": sha, "key": r["key"],
            "version": plan["version"], "code_hash": plan["code_hash"], "made": made})
    index = {"world": viz_id, "version": viz.get("version", ""), "recorder": L.RECORDER_VERSION,
             "recorder_hash": plan["recorder_hash"], "code_hash": plan["code_hash"],
             "made": max([e.get("made") or "" for e in entries] or [made]), "recordings": entries}
    keep = {e["file"] for e in entries}
    for f in folder.glob("*.lfrec.gz"):
        if f.name not in keep:
            f.unlink()
    tmp = folder / "index.json.tmp"
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, folder / "index.json")
    return index, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Record the public site's demonstrations offline (design §4.1).")
    ap.add_argument("--world", action="append", default=[], help="a world id (repeatable; an old id works too)")
    ap.add_argument("--all", action="store_true", help="every world that has recording specs")
    ap.add_argument("--stale", action="store_true", help="the worlds whose recordings are missing or stale")
    ap.add_argument("--rec", action="append", default=[], help="only this recording id of the world(s) (repeatable)")
    ap.add_argument("--out", default=str(L.RECORDINGS), help="the recordings folder (default visualizations/recordings)")
    ap.add_argument("--worker-mem-gb", type=float, default=None,
                    help="a hard memory limit for this process, as a server gives its workers (lfviz.limits)")
    a = ap.parse_args(argv)
    if a.worker_mem_gb:
        os.environ[limits.ENV] = str(int(a.worker_mem_gb * limits.GIB))
        limits.apply_hard_limit()
    out = Path(a.out)
    demos = L.demo_worlds()
    worlds = [registry.resolve(w) for w in a.world]
    if a.all:
        worlds += demos
    if a.stale:
        worlds += [w for w in demos if set(L.status(out, L.planned_world(w)).values()) != {"present"}]
    worlds = list(dict.fromkeys(worlds))
    bad = [w for w in worlds if w not in demos]
    if bad:
        _log(f"no recording specs (or no such world): {bad}")
        return 2
    if not worlds:
        _log("nothing to record")
        return 0
    problems = []
    for w in worlds:
        t0 = time.monotonic()
        index, probs = record_world(w, out, a.rec or None)
        problems += probs
        sizes = ", ".join(f"{e['id']} {e['bytes_gz'] / L.MB:.2f} MB" for e in index["recordings"])
        _log(f"{w}: done in {time.monotonic() - t0:.0f} s: {sizes}")
    for p in problems:
        _log(f"PROBLEM: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
