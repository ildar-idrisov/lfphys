# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Instruments (plan P16.3; owner, 2026-11-04 and 2026-11-11): the recorded values of a world's measurable quantities
as time series, read back from the run's record, as JSON or CSV.

A world declares its measurables (``measurables(self) -> [{id, label, unit, of, group}]``; integrator's API of
2026-11-11, §2): the framework sends the list as ``measurables`` in the ``scene`` message, and a demonstration may put
it into its header or any other accumulative message. Every frame carries ``meas: {id: value}`` in the declared display
units (null where a value is undefined, the reason in ``meas_note``). Nothing here computes physics: the series are the
values the run recorded, at the world times of its frames.

    GET /api/runs/{id}/series?ids=a,b[&from=t0][&to=t1][&world=n][&format=csv][&max_points=k]

* the latest world of the record, or world ``n``; the frames with ``t0 <= t <= t1``;
* JSON: ``{run, world, worlds, t_unit, ids, measurables, t, values: {id: [...]}, n_frames, n, stride, cap, notes}``;
  at most ``max_points`` rows (default ``JSON_POINTS``, at most ``JSON_POINTS_MAX``): beyond, every ``stride``-th frame
  of the range and its last one (uniform, as the player's history);
* CSV: streamed in batches; one header line — the world time with its unit, then each quantity's label with its unit
  and its id in brackets; a value that is undefined (null) or a quantity not measured in that frame is an empty cell;
  numbers as Python writes them (shortest round trip, "." as the decimal point); at most ``CSV_MAX_ROWS`` rows and
  ``CSV_MAX_CELLS`` cells: beyond, every ``stride``-th frame, and the time column's header says so.
* an id named twice counts once (review LB1-framework F11).

Reading never blocks the server: the record is scanned in a thread (only the JSON part of each message is read), the
scan of each run is kept and continued as the record grows (an index of where each world's messages are and what it
declared), each batch of a CSV is read and formatted in a thread (F11: formatting 4000 rows of 100 columns in the event
loop held every viewer for 0.36 s; the thread still shares the interpreter lock with the loop, so a large CSV slows the
other requests by up to ~0.1 s at a time: STATUS), and a playground's window is not trimmed while a series is read
(``Run.readers``).
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import math
import struct
from dataclasses import dataclass, field

from .i18n import T, error_body, is_t, render_in

CSV_MAX_ROWS = 2_000_000
CSV_MAX_CELLS = 20_000_000  # rows × columns of one CSV (~0.4 GB): beyond, a stride (review LB1-framework F11)
JSON_POINTS = 5000
JSON_POINTS_MAX = 50000
MAX_IDS = 100
BATCH = 4000  # frames read per step of the thread (a CSV is written batch by batch)


def read_json(files: dict, run, e) -> dict:
    """Only the JSON part of the record's message ``e`` (no arrays): its length, then its text."""
    f = files.get(e.seg)
    if f is None:
        f = files[e.seg] = open(run.seg_path(e.seg), "rb")
    f.seek(e.offset)
    (jlen,) = struct.unpack("<I", f.read(4))
    return json.loads(f.read(jlen))


def t_unit_of(header: dict):
    """The unit of a world's time from its header (``units.t``: a text, or a plain string whose first words count:
    "s", "fs", "M"), seconds by default."""
    u = header.get("units") if isinstance(header, dict) else None
    t = u.get("t") if isinstance(u, dict) else None
    if is_t(t):
        return T(t)
    if isinstance(t, str) and t.strip():
        return t.split(" (")[0].strip()[:40]
    return T("s")


@dataclass
class WorldInfo:
    n: int
    t_unit: object = "s"  # a text (T) or a plain string
    header: bool = False  # its header was seen
    decl: dict = field(default_factory=dict)  # id -> the latest declaration {id, label, unit, of, group}
    objects: dict = field(default_factory=dict)  # obj id -> {type, label, values} (the latest scene message)
    t_last: float | None = None
    # a playground's palette as its header gave it (type -> the type's JSON: label, params, handles); the sections
    # build their palettes per world instance, so the class attribute is empty (review LB1-p02-ux X1)
    palette: dict = field(default_factory=dict)
    # the measurables a playground declares now (its latest scene message); None: not a playground (a demonstration
    # declares in its header or any message, and everything it declared counts) — review LB1-framework F12
    current: set | None = None


class Index:
    """What the record of one run holds, scanned once and continued as it grows: the world of every stretch of
    messages (``spans``: [world, first entry, end]) and, per world, its time unit, its measurables and its scene's
    objects. A new list of entries (a playground's window trimmed) starts the scan again."""

    def __init__(self):
        self.entries = None  # the list object scanned (Run.entries)
        self.n = 0  # entries scanned
        self.cur = None  # the world of the next entry
        self.seg_prev = None
        self.spans: list = []
        self.worlds: dict[int, WorldInfo] = {}

    def _world(self, n: int) -> WorldInfo:
        w = self.worlds.get(n)
        if w is None:
            w = self.worlds[n] = WorldInfo(n)
        return w

    def _note(self, w: WorldInfo, meta: dict):
        typ = meta.get("type")
        if typ == "header":
            w.header = True
            w.t_unit = t_unit_of(meta)
            pg = meta.get("playground")
            if isinstance(pg, dict) and isinstance(pg.get("palette"), list):
                w.palette = {t["type"]: t for t in pg["palette"] if isinstance(t, dict) and isinstance(t.get("type"), str)}
        if typ == "scene":  # a playground's scene message carries the whole list of what it measures now
            ms = meta.get("measurables")
            w.current = {d["id"] for d in ms if isinstance(d, dict) and isinstance(d.get("id"), str)} \
                if isinstance(ms, list) else set()
        if isinstance(meta.get("measurables"), list):
            for d in meta["measurables"]:
                if isinstance(d, dict) and isinstance(d.get("id"), str):
                    w.decl[d["id"]] = {"id": d["id"], "label": _txt(d.get("label") or d["id"]),
                                       "unit": _txt(d.get("unit") or ""), "of": d.get("of"),
                                       "group": _txt(d.get("group") or "")}
        if typ == "scene" and isinstance(meta.get("objects"), list):
            w.objects = {o.get("id"): {"type": o.get("type"), "label": o.get("label"), "values": o.get("values") or {}}
                         for o in meta["objects"] if isinstance(o, dict)}

    def scan(self, run, entries: list, n_end: int):
        """Continue the scan up to ``n_end`` (in a thread: reads the record's files)."""
        if entries is not self.entries:
            self.__init__()
            self.entries = entries
        if self.n >= n_end:
            return
        files: dict = {}
        try:
            for i in range(self.n, n_end):
                e = entries[i]
                if run.buffered and e.seg != self.seg_prev:
                    self.seg_prev = e.seg
                    if e.kind != "header":
                        self.cur = run._world_of_seg(e.seg)
                        w = self._world(self.cur)
                        if not w.header and self.cur in run.headers:  # its header left the window: the kept copy
                            from . import protocol
                            self._note(w, protocol.peek_meta(run.headers[self.cur]))
                if e.kind == "header":
                    meta = read_json(files, run, e)
                    self.cur = int(meta.get("world", 1))
                    self._note(self._world(self.cur), meta)
                elif not e.is_frame and self.cur is not None:
                    meta = read_json(files, run, e)
                    if "measurables" in meta or meta.get("type") == "scene":
                        self._note(self._world(self.cur), meta)
                if self.cur is None:
                    continue
                if e.is_frame and e.t is not None:
                    self._world(self.cur).t_last = e.t
                if self.spans and self.spans[-1][0] == self.cur and self.spans[-1][2] == i:
                    self.spans[-1][2] = i + 1
                else:
                    self.spans.append([self.cur, i, i + 1])
        finally:
            for f in files.values():
                f.close()
        self.n = n_end

    def frames(self, entries: list, world: int, t0: float, t1: float) -> list:
        """The record's frame entries of ``world`` with t0 <= t <= t1, in order."""
        out = []
        for w, a, b in self.spans:
            if w != world:
                continue
            for i in range(a, b):
                e = entries[i]
                if e.is_frame and e.t is not None and t0 <= e.t <= t1:
                    out.append(e)
        return out


_INDEX: dict[str, Index] = {}
_LOCKS: dict[str, asyncio.Lock] = {}


async def indexed(run) -> tuple[Index, list, int]:
    """The run's index brought up to the record's present end, with the entries it describes."""
    lock = _LOCKS.setdefault(run.id, asyncio.Lock())
    async with lock:
        idx = _INDEX.get(run.id)
        if idx is None:
            idx = _INDEX[run.id] = Index()
        entries, n_end = run.entries, len(run.entries)
        run.readers += 1  # the window is not trimmed while the files are read (review B6-F9)
        try:
            await asyncio.to_thread(idx.scan, run, entries, n_end)
        finally:
            run.readers -= 1
        return idx, entries, n_end


def _txt(x):
    """A text of the record: a ``T`` (kept, the player renders it) or a plain string (bounded)."""
    return T(x) if is_t(x) else str(x)[:300]


def display_label(w: WorldInfo, d: dict):
    """A quantity's label for the owner (a text): a probe's quantity names its object ("Probe 1: distance")."""
    lab = d.get("label") or d.get("id")
    of = d.get("of")
    if of is not None and of in w.objects:
        ol = w.objects[of].get("label") or of
        if not is_t(ol):
            ol = str(ol)
        if ol and not (isinstance(ol, str) and isinstance(lab, str) and ol in lab):
            return T("{object}: {label}", object=ol, label=lab)
    return lab


def column_title(w: WorldInfo, d: dict):
    unit = d.get("unit") or ""
    if unit:
        return T("{label}, {unit} [{id}]", label=display_label(w, d), unit=unit, id=d["id"])
    return T("{label} [{id}]", label=display_label(w, d), id=d["id"])


def _num(v):
    """A recorded value as a float (None: undefined)."""
    if v is None or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def csv_batch(run, frames: list, ids: list) -> bytes:
    """The CSV lines of these frame entries (in a thread: read and formatted there, never in the event loop)."""
    ts, rows, _ = read_rows(run, frames, ids)
    buf = io.StringIO()
    wr = csv.writer(buf, lineterminator="\r\n")
    for t, r in zip(ts, rows):
        wr.writerow([repr(t)] + [_cell(x) for x in r])
    return buf.getvalue().encode("utf-8")


def read_rows(run, frames: list, ids: list) -> tuple[list, list, dict]:
    """(times, rows of values, the latest note per id) of these frame entries (in a thread)."""
    files: dict = {}
    ts, rows, notes = [], [], {}
    try:
        for e in frames:
            m = read_json(files, run, e)
            meas = m.get("meas") if isinstance(m.get("meas"), dict) else {}
            ts.append(float(m.get("t", e.t)))
            rows.append([_num(meas.get(k)) for k in ids])
            mn = m.get("meas_note")
            if isinstance(mn, dict):
                for k in ids:
                    if mn.get(k):
                        notes[k] = _txt(mn[k])
    finally:
        for f in files.values():
            f.close()
    return ts, rows, notes


def thin(frames: list, cap: int) -> tuple[list, int]:
    """Every ``stride``-th frame and the last one, so that at most ``cap`` remain."""
    n = len(frames)
    if n <= cap:
        return frames, 1
    stride = -(-n // max(1, cap - 1))
    out = frames[::stride]
    if out[-1] is not frames[-1]:
        out.append(frames[-1])
    return out, stride


class BadRequest(ValueError):
    pass


def _float_arg(q, name, default):
    s = q.get(name)
    if s is None or s == "":
        return default
    try:
        x = float(s)
    except ValueError:
        raise BadRequest(T("“{name}” is a number (the world's time)", name=name)) from None
    if math.isnan(x):
        raise BadRequest(T("“{name}” is a number (the world's time)", name=name))
    return x


def parse_query(q, idx: Index) -> dict:
    """The request's arguments, checked against what the record holds (``BadRequest`` with the owner's text)."""
    worlds = sorted(idx.worlds)
    if not worlds:
        raise BadRequest(T("the record holds no world"))
    ws = q.get("world")
    if ws in (None, ""):
        world = worlds[-1]
    else:
        try:
            world = int(ws)
        except ValueError:
            raise BadRequest(T("“world” is a world's number (a whole number)")) from None
        if world not in idx.worlds:
            raise BadRequest(T("the record has no world {n}; there are: {worlds}", n=world,
                               worlds=", ".join(map(str, worlds))))
    w = idx.worlds[world]
    ids = list(dict.fromkeys(s.strip() for s in (q.get("ids") or "").split(",") if s.strip()))  # once each (F11)
    have = ", ".join(sorted(w.decl)) or T("none: the world reports no measurable quantities")
    if not ids:
        raise BadRequest(T("name the quantities: ids=a,b (world {n:d} has: {have})", n=world, have=have))
    if len(ids) > MAX_IDS or any(len(k) > 200 for k in ids):
        raise BadRequest(T("at most {n:d} quantities at a time", n=MAX_IDS))
    unknown = [k for k in ids if k not in w.decl]
    if unknown:
        raise BadRequest(T("world {n:d} has no quantities {ids} (it has: {have})", n=world, ids=", ".join(unknown),
                           have=have))
    t0 = _float_arg(q, "from", -math.inf)
    t1 = _float_arg(q, "to", math.inf)
    if t1 < t0:
        raise BadRequest(T("“to” is before “from”"))
    fmt = (q.get("format") or "json").lower()
    if fmt not in ("json", "csv"):
        raise BadRequest(T("“format” is json or csv"))
    mp = q.get("max_points")
    if mp in (None, ""):
        cap = JSON_POINTS
    else:
        try:
            cap = int(mp)
        except ValueError:
            raise BadRequest(T("“max_points” is a whole number")) from None
        if not 2 <= cap <= JSON_POINTS_MAX:
            raise BadRequest(T("“max_points” is from 2 to {max:d}", max=JSON_POINTS_MAX))
    return {"world": world, "ids": ids, "t0": t0, "t1": t1, "format": fmt, "cap": cap}


def _csv_line(cells) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerow(cells)
    return buf.getvalue()


def _cell(x) -> str:
    return "" if x is None else repr(float(x))


async def series(request, mgr):
    from aiohttp import web  # noqa: PLC0415

    def err(text, status=400):
        return web.json_response(error_body(text), status=status, dumps=lambda d: json.dumps(d, ensure_ascii=False))

    for rid in [k for k in _INDEX if k not in mgr.runs]:  # deleted runs: their scans go
        _INDEX.pop(rid, None)
        _LOCKS.pop(rid, None)
    try:
        run = mgr.get(request.match_info["id"])
    except KeyError:
        return err(T("there is no such run"), 404)
    try:
        idx, entries, _ = await indexed(run)
        a = parse_query(request.query, idx)
    except BadRequest as e:
        return err(e.args[0] if e.args else str(e))
    except OSError as e:  # a record file gone or unreadable
        return err(T("the record cannot be read: {error}", error=str(e)), 409)
    w = idx.worlds[a["world"]]
    ids = a["ids"]
    frames = idx.frames(entries, a["world"], a["t0"], a["t1"])
    decls = [w.decl[k] for k in ids]
    if a["format"] == "json":
        chosen, stride = thin(frames, a["cap"])
        run.readers += 1
        try:
            ts, rows, notes = await asyncio.to_thread(read_rows, run, chosen, ids)
        except OSError as e:
            return err(T("the record cannot be read: {error}", error=str(e)), 409)
        finally:
            run.readers -= 1
        out = {"run": run.id, "world": a["world"], "worlds": sorted(idx.worlds), "t_unit": w.t_unit, "ids": ids,
               "measurables": [{**d, "title": display_label(w, d)} for d in decls], "t": ts,
               "values": {k: [r[j] for r in rows] for j, k in enumerate(ids)}, "n_frames": len(frames),
               "n": len(ts), "stride": stride, "cap": a["cap"], "notes": notes}
        return web.json_response(out, dumps=lambda d: json.dumps(d, ensure_ascii=False))
    cap = min(CSV_MAX_ROWS, max(2, CSV_MAX_CELLS // (len(ids) + 1)))
    chosen, stride = thin(frames, cap)
    # the CSV's header in the language asked for (?lang=, English by default): a file keeps no T objects
    lang = request.query.get("lang") or "en"
    t_head = render_in(T("t, {unit} (every {k:d}th frame of the record: a limit of {cap:d} rows)", unit=w.t_unit, k=stride,
                         cap=cap) if stride > 1 else T("t, {unit}", unit=w.t_unit), lang)
    name = f"{run.id}-w{a['world']}-series.csv"
    resp = web.StreamResponse(headers={"Content-Type": "text/csv; charset=utf-8",
                                       "Content-Disposition": f'attachment; filename="{name}"',
                                       "X-Lfviz-Rows": str(len(chosen)), "X-Lfviz-Stride": str(stride)})
    await resp.prepare(request)
    await resp.write(_csv_line([t_head] + [render_in(column_title(w, d), lang) for d in decls]).encode("utf-8"))
    run.readers += 1
    try:
        for i in range(0, len(chosen), BATCH):
            await resp.write(await asyncio.to_thread(csv_batch, run, chosen[i:i + BATCH], ids))
    finally:
        run.readers -= 1
    await resp.write_eof()
    return resp


def add_routes(app, mgr):
    async def handler(request):
        return await series(request, mgr)
    app.router.add_get("/api/runs/{id}/series", handler)
