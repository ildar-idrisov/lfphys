# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The atlases of the screens: computed points on a grid of controls (design
``lfphys/sources/explore_2026-11-14_design.md`` §1).

    python3 site/atlas.py --world s03_projectile [--atlas explore] [--out DIR]
    python3 site/atlas.py --all | --stale [--out DIR]

An atlas is the set of points of one Explore screen (its id is the screen's) or of one lab step (``<screen>.<step>``) on
the grid of its controls (``registry.atlases_of``). A point is the world's own run (``lfviz.headless.run_spec``): the
screen's preset, its ``fixed`` values and the grid values on top (a compound control's value as the parameters it sets),
the screen's seed, frames every ``frame_dt`` of world time (or ``fps`` frames per played second at the point's own
default speed) from t = 0 until the screen's stop rule (a time, an event, or counted events: EX2 §5 F1–F3). A point the
world refuses (``check_params``) is ``refused`` with its text; a point that fails (an error, an exception, a check
ending ✗, a stop event not reached) fails the atlas.

Files, per world (``<out>/<world>/atlas/<atlas>/``):

* ``base.<hash8>.lfpt.gz``: gzip -9 (mtime 0) of an ``LFVREC1`` stream of one message, the screen's base header: the
  header of the default point (every control at its default), its blobs quantised by the screen's ``quantize``;
* ``p<i>.<hash8>.lfpt.gz``: the point with the flattened index ``i`` (row-major over the controls in their order, the
  last control fastest): its header as a delta against the base header (with ``$base``, the base file's sha256: a
  reader merges it only with that base), then the world's messages in order (frames at
  ``frame_dt``, the screen's dropped message types and frame blobs left out, the ``quantize`` map's blobs quantised:
  ``lfviz.headless.Packer``, ``lfviz.protocol``), then ``end {reason: "atlas"}``;
* ``atlas.<hash8>.json``, the manifest: ``{world, atlas, screen, step, atlas_version, key, version, code_hash,
  recorder_hash, seed, preset, fixed, controls: [{param, values, default, compound?, sets?}] (a compound control's
  ``param`` is its id, its ``sets`` the parameters each value sets: EX2 §5 F3), frame_dt, fps? (frames per played
  second at the world's default speed, then ``frame_dt`` is null: EX2 §5 F1), stop, base: {file, bytes_gz,
  sha256}, points: [[file | null, bytes_gz, state]] (state 0: computed; k ≥ 1: refused, refusals[k-1]), refusals: [T],
  checks: {ok, failed, expected, info, na} (summed over the points), quant: {"<type>.<blob>": {enc, max_err,
  max_rel}}, references: {<law reference id>: {value, unit, label, how, kind}} (lab steps: one per law of the step),
  bytes_gz (base and points)}``. ``hash8`` is the first 8 hex digits of the file's sha256. The manifest holds nothing
  of the build's time or CPU, so the same spec and code give the same bytes and the same name (review R-F F7): the
  build's ``made`` and ``cpu_s`` are in the index entry.

The world's ``index.json`` lists its atlases (``atlases: [{id, screen, step, file, key, points, refused, bytes_gz,
checks, cpu_s, version, code_hash, made}]``; ``file`` relative to the world's folder). An atlas not built now keeps its
old entry only while its key is current (review F9's rule, as for recordings).

Budgets (``sitelib.BUDGET``): a point 150 kB target / 400 kB limit, an atlas 6 / 12 MB; over a limit the atlas fails;
over a target it warns (``sitelib.ACCEPTED`` with ``("<world>", "atlas:<id>")`` says why it is accepted). The world's
budget (recordings and atlases together) is ``site/record.py``'s, which calls ``build_world`` after the recordings.

Checks against the world's own declarations that need it built: the Explore screen's ``readouts`` and the lab
instruments' measurables are among the base header's ``measurables``; ``lab_reference(step, fixed, values,
reference=<id>)`` answers each law of a step (integrator D4). The builders run on the CPU (``LFPHYS_NO_GPU=1``, as in
CI: the key does not cover the device; review R-F F10).

The keys name the code that ran (review R2-F F1): every world's code is hashed before any world is imported
(``sitelib.code_signature``), the atlases are written into staging folders (``<atlas>.tmp``), and after the world's last
atlas the code is hashed again and every file of it is checked not to have changed since the script started
(``sitelib.check_unchanged``); when it changed, nothing of the world is installed, its index stays as it was and the
run reports «the code changed during the build … run again».
Exit code: 0 when every atlas was built within its hard limits, 1 otherwise.
"""

from __future__ import annotations

import time

#: when this script started, before it imported the lfviz package and the engine (``sitelib.check_unchanged``: a file
#: modified after it may not be the code that ran; review R2-F F1)
STARTED_NS = time.time_ns()

import argparse  # noqa: E402
import datetime as _dt  # noqa: E402
import hashlib  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitelib as L  # noqa: E402

from lfviz import headless, protocol, registry  # noqa: E402
from lfviz.i18n import T, render_in  # noqa: E402

ATLAS_DIR = "atlas"


def _log(*a):
    print(*a, file=sys.stderr, flush=True)


def grid(controls: list[dict]) -> list[tuple]:
    """Every combination of the controls' values, row-major (the last control fastest): index i is the point's."""
    return list(itertools.product(*[c["values"] for c in controls]))


def flat_index(controls: list[dict], values: dict) -> int:
    """The flattened index of a grid point (ValueError when a value is not on the grid)."""
    i = 0
    for c in controls:
        vals = c["values"]
        v = values.get(c["param"], c.get("default"))
        try:  # the same type first (True is not 1.0), then equal
            k = next((j for j, x in enumerate(vals) if type(x) is type(v) and x == v), None)
            k = next(j for j, x in enumerate(vals) if x == v) if k is None else k
        except StopIteration:
            raise ValueError(f"{c['param']} = {v!r} is not on the grid {vals}") from None
        i = i * len(vals) + k
    return i


def defaults(spec: dict) -> dict:
    return {c["param"]: c.get("default", c["values"][0]) for c in spec["controls"]}


def clock_of(spec: dict) -> dict:
    """An atlas's clock for ``headless.run_spec`` (EX2 §5 F1): ``{"frame_dt": dt}`` (world seconds between frames) or
    ``{"fps": f, "speed": None}`` (frames per played second at the world's default speed: the point's own)."""
    if spec.get("fps") is not None:
        return {"fps": float(spec["fps"]), "speed": None}
    return {"frame_dt": spec["frame_dt"]}


def params_of(spec: dict, values: dict) -> dict:
    """The values a point is run with: the atlas's ``fixed``, then the grid values, a compound control's value replaced
    by the parameters it sets (EX2 §5 F3; ValueError for a compound value off its grid)."""
    return {**spec["fixed"], **registry.expand_values(spec["controls"], values)}


def run_point(vid: str, spec: dict, values: dict, seed: int | None = None, log=_log):
    """One point run headless: (messages [(meta, blobs)], Outcome). Raises ``headless.PointRefused``,
    ``headless.RunFailed`` or ``ValueError`` (the schema refuses the values)."""
    msgs = []
    oc = headless.run_spec(vid, spec["preset"], params_of(spec, values), spec["seed"] if seed is None else seed,
                           clock_of(spec), spec["stop"], emit=lambda m, b=None: msgs.append((m, b)),
                           end_reason="atlas", label=f"{vid}/{spec['id']}", log=log)
    return msgs, oc


def base_header(spec: dict, msgs: list) -> tuple:
    """The packed base header (meta, blobs) from the default point's messages."""
    meta, blobs = next((m, b) for m, b in msgs if m.get("type") == "header")
    return headless.Packer(spec["quantize"], spec["drop"]).pack_base(meta, blobs)


def pack_point(spec: dict, msgs: list, base: tuple | None, base_sha: str | None = None) -> tuple[bytes, headless.Packer]:
    """A point's file (gzip of its packed stream) and the packer (its quantisation's errors): its header a delta against
    ``base`` naming ``base_sha`` (the base file's sha256), or a full header when ``base`` is None."""
    pk = headless.Packer(spec["quantize"], spec["drop"], base, base_sha)
    enc = [b for b in (pk.message(m, bl) for m, bl in msgs) if b is not None]
    return headless.gz(headless.stream(enc)), pk


def pack_items(spec: dict, msgs: list, base: tuple | None, base_sha: str | None = None) -> tuple[list, headless.Packer]:
    """A point's packed messages ``[(meta, blobs)]`` before encoding (``pack_point`` encodes them; the atlas's pool is
    made from them, EX2 §5 F10) and the packer."""
    pk = headless.Packer(spec["quantize"], spec["drop"], base, base_sha)
    return [x for x in (pk.packed(m, bl) for m, bl in msgs) if x is not None], pk


def encode_items(items: list) -> bytes:
    """A point's file from its packed messages (pooled blobs as ``protocol.PoolRef``)."""
    return headless.gz(headless.stream([protocol.encode(m, b) for m, b in items]))


def pack_base_file(base: tuple) -> bytes:
    return headless.gz(headless.stream([protocol.encode(*base)]))


def _merge_quant(into: dict, pk: headless.Packer):
    for k, e in pk.quant.items():
        old = into.get(k)
        if old is None:
            into[k] = dict(e)
            continue
        for f in ("max_err", "max_rel"):
            a, b = old[f], e[f]
            if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
                old[f] = [max(x, y) for x, y in zip(a, b)]
            else:
                old[f] = max(max(a) if isinstance(a, list) else a, max(b) if isinstance(b, list) else b)


def _measurables(header_meta: dict) -> set:
    return {m.get("id") for m in header_meta.get("measurables") or [] if isinstance(m, dict)}


def _screen_of(viz: dict, sid: str) -> dict:
    return next(s for s in viz.get("screens") or [] if s.get("id") == sid)


def check_declarations(viz: dict, spec: dict, header_meta: dict) -> list[str]:
    """What needs the world built (design §2.1, §2.5; EX2 §5 F4, F7): the readouts and the instruments' measurables in
    its header; a measurable's ``sigma`` and ``ref`` name other measurables of the header (its ``ref_label`` a text);
    a readout instrument's ``sigma`` names one; a ``control:`` instrument reads a control of the step (a compound one
    by its id), a parameter a compound control sets, or a fixed value."""
    have = _measurables(header_meta)
    sc = _screen_of(viz, spec["screen"])
    out = []
    for m in header_meta.get("measurables") or []:
        if not isinstance(m, dict):
            continue
        for k in ("sigma", "ref"):
            if m.get(k) is not None and (m[k] not in have or m[k] == m.get("id")):
                out.append(f"measurable {m.get('id')!r}: its {k} {m[k]!r} is not another measurable of the world's "
                           f"header ({sorted(have)})")
        rl = m.get("ref_label")
        if rl is not None and not (isinstance(rl, str) or (isinstance(rl, dict) and "$t" in rl)):
            out.append(f"measurable {m.get('id')!r}: its ref_label is a text (a T)")
    if sc["kind"] == "explore":
        out += [f"readout {r!r} is not a measurable of the world's header ({sorted(have)})"
                for r in sc.get("readouts") or [] if r not in have]
    settable = {c["param"] for c in spec["controls"]} | {p for c in spec["controls"] for p in c.get("sets") or {}}
    for lab, step in steps_of(viz, spec):
        out += [f"step {step['id']}: readout {r!r} is not a measurable of the world's header ({sorted(have)})"
                for r in step.get("readouts") or [] if r not in have]
        sc = lab
        for iid in step["instruments"]:
            reads = sc["instruments"][iid].get("reads")
            if reads and not reads.startswith("control:") and reads not in have:
                out.append(f"instrument {iid} reads {reads!r}, not a measurable of the world's header ({sorted(have)})")
            if reads and reads.startswith("control:") and reads[8:] not in settable and reads[8:] not in spec["fixed"]:
                out.append(f"instrument {iid} reads {reads!r}: not a control, a parameter a compound control sets, or "
                           f"a fixed value of the step")
            sg = sc["instruments"][iid].get("sigma")
            if sg and sg not in have:
                out.append(f"instrument {iid}: its sigma {sg!r} is not a measurable of the world's header "
                           f"({sorted(have)})")
    return out


def steps_of(viz: dict, spec: dict) -> list[tuple[dict, dict]]:
    """The lab steps whose points an atlas holds, as ``(lab screen, step)``: a lab step's own atlas, or the steps on an
    Explore screen's atlas (``atlas: <screen>``, EX2 §5 F9)."""
    out = []
    for sc in viz.get("screens") or []:
        if sc.get("kind") != "lab":
            continue
        for st in sc["steps"]:
            if (spec.get("step") is not None and sc["id"] == spec["screen"] and st["id"] == spec["step"]) \
                    or (spec.get("step") is None and st.get("atlas") == spec["id"]):
                out.append((sc, st))
    return out


def counted(viz: dict, spec: dict) -> set:
    """The measurables a lab step's counters read (EX2 §5 F4): each frame's value must be a whole number or None."""
    return {sc["instruments"][iid].get("reads") for sc, step in steps_of(viz, spec) for iid in step["instruments"]
            if sc["instruments"][iid].get("kind") == "counter"}


def not_counts(msgs: list, names: set) -> list[str]:
    """The counted measurables whose value in a frame is not a whole number ≥ 0 (``counted``)."""
    bad = set()
    for m, _b in msgs:
        if m.get("type") != "frame" or not names:
            continue
        meas = m.get("meas") or {}
        for k in names:
            v = meas.get(k)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                                  or v < 0 or v != int(v)):  # NaN, ±inf: not a count (review R2-F F4)
                bad.add(k)
    return sorted(bad)


def unread(viz: dict, spec: dict, msgs: list) -> list[str]:
    """The instruments of the atlas's lab steps that have nothing to read at a point's end (RULES §10: «Every instrument
    of a step reads on every point of its atlas»: «Measure» refuses the whole row when one has nothing; review R2-F F5
    (a): only the player knew): an instrument reading a measurable needs its value (and its ``sigma``'s) in the last
    frame and, with ``event``, that event by then; a ``control:`` or ``manual`` instrument always reads."""
    frames = [m for m, _b in msgs if m.get("type") == "frame"]
    if not frames:
        return []
    last = frames[-1]
    meas, t_end = last.get("meas") or {}, last.get("t", 0.0)
    events = {k for m, _b in msgs if m.get("type") == "event" and m.get("t", 0.0) <= t_end + 1e-12 * abs(t_end)
              for k in (m.get("kind"), m.get("name")) if k}
    out = []
    for sc, step in steps_of(viz, spec):
        for iid in step["instruments"]:
            d = sc["instruments"][iid]
            src = str(d.get("reads") or "")
            if d.get("manual") or not src or src.startswith("control:"):
                continue
            why = [f"{src} is null" for _ in [0] if meas.get(src) is None] \
                + [f"its sigma {d['sigma']} is null" for _ in [0] if d.get("sigma") and meas.get(d["sigma"]) is None] \
                + [f"its event {d['event']!r} has not happened" for _ in [0] if d.get("event") and d["event"] not in events]
            if why:
                out.append(f"step {step['id']}: instrument {iid} has nothing to read at the point's end ({'; '.join(why)})")
    return out


def event_frame_is_last(msgs: list, oc) -> bool:
    """Whether a point stopped by an event ends on the stop event's own frame (review R2-F F3: a cursor a rounding short
    of the last frame then reads the frame before the event; ``headless.run_spec`` makes one more frame, this checks
    it): fewer than two frames at or after the stop event's time."""
    if oc.stop_event_t is None:
        return False
    te = oc.stop_event_t - 1e-12 * max(1.0, abs(oc.stop_event_t))
    return sum(1 for m, _b in msgs if m.get("type") == "frame" and m.get("t", 0.0) >= te) < 2


def reference(viz: dict, spec: dict, params: dict, ref_id: str) -> dict:
    """The reference of one law of a lab step, computed by the world (``Simulation.lab_reference(step_id, fixed, values,
    reference)``, design §2.3, integrator D4): ``values`` the grid's values of each control (a compound control's by its
    id, and the lists of the parameters it sets). On an Explore screen's atlas a step's law is ``<step>/<law>`` (EX2 §5
    F9)."""
    grid = {c["param"]: list(c["values"]) for c in spec["controls"]}
    for c in spec["controls"]:  # a compound control: its id's values and the values it sets (EX2 §5 F3)
        grid.update({p: list(v) for p, v in (c.get("sets") or {}).items()})
    step, law = ref_id.split("/", 1) if "/" in ref_id else (spec["step"], ref_id)  # a step on an Explore's atlas (F9)
    ref = viz["simulation"].lab_reference(step, dict(params), grid, reference=law)
    if not isinstance(ref, dict) or not isinstance(ref.get("value"), (int, float)) or isinstance(ref["value"], bool):
        raise ValueError(f"lab_reference({step!r}, reference={law!r}) gave {ref!r}: "  # the step of a shared atlas
                         f"{{value, unit, label, how, kind}}")  # too (review R2-F F9: it named None)
    return protocol.clean(ref)


def _manifest_control(c: dict) -> dict:
    """A control in the manifest: its key (``param``: a parameter, or a compound control's id), grid and default; a
    compound control also the parameters it sets (EX2 §5 F3: «the manifest records the sets»)."""
    out = {"param": c["param"], "values": c["values"], "default": c.get("default")}
    if c.get("sets") is not None:
        out.update(compound=True, sets=c["sets"])
    return out


def _staged(out: Path, vid: str, aid: str) -> Path:
    """The folder an atlas is written into before it is installed (``build_world``)."""
    return Path(out) / vid / ATLAS_DIR / f"{aid}.tmp"


def build_atlas(vid: str, spec: dict, out: Path, plan_entry: dict, log=_log) -> tuple[dict | None, list[str], list[str]]:
    """Compute one atlas and write it into its staging folder (``_staged``; ``build_world`` installs it). Returns (its
    index entry or None when it failed, problems, warnings)."""
    viz = registry.load(vid)
    where = f"{vid}/{spec['id']}"
    problems, warns = [], []
    pts = grid(spec["controls"])
    params = [c["param"] for c in spec["controls"]]
    dflt = defaults(spec)
    i_def = flat_index(spec["controls"], dflt)
    log(f"{where}: {len(pts)} points ({' × '.join(str(len(c['values'])) for c in spec['controls'])}), "
        f"default p{i_def}")
    pt_t, pt_l = L.BUDGET["point"]
    at_t, at_l = L.BUDGET["atlas"]
    cpu = 0.0
    try:
        msgs0, oc0 = run_point(vid, spec, dflt, log=log)
    except headless.PointRefused as e:
        return None, [f"{where}: the default point {dflt} is refused by the world: {e}"], warns
    except (headless.RunFailed, ValueError) as e:
        return None, [f"{where}: the default point {dflt} failed: {e}"], warns
    try:
        base = base_header(spec, msgs0)
    except ValueError as e:  # a blob the quantisation refuses (±inf)
        return None, [f"{where}: the default point's header cannot be packed: {e}"], warns
    base_gz = pack_base_file(base)
    bsha = hashlib.sha256(base_gz).hexdigest()
    problems += [f"{where}: {x}" for x in check_declarations(viz, spec, base[0])]
    refs = {}
    for ref_id in spec.get("laws") or []:
        try:
            refs[ref_id] = reference(viz, spec, headless.resolve(viz, spec["preset"], spec["fixed"]), ref_id)
        except Exception as e:  # noqa: BLE001 - the world gave no reference: the step cannot be checked
            problems.append(f"{where}: lab_reference({ref_id!r}) failed: {type(e).__name__}: {e}")
    counts = counted(viz, spec)
    packed: dict = {}  # point index -> its packed messages, kept until the pool is made (EX2 §5 F10)
    files: dict[str, bytes] = {}
    entries, refusals, rkeys = [], [], {}
    checks = {"ok": 0, "failed": 0, "expected": 0, "info": 0, "na": 0}
    quant: dict = {}
    t0 = time.monotonic()
    for i, combo in enumerate(pts):
        values = dict(zip(params, combo))
        try:
            if i == i_def:
                msgs, oc = msgs0, oc0
            else:
                msgs, oc = run_point(vid, spec, values, log=log)
        except headless.PointRefused as e:
            owner = T("{text}. What to change: {hint}", text=e.text, hint=e.hint) if e.hint else e.text
            k = json.dumps(protocol.clean(owner), sort_keys=True, ensure_ascii=False)
            if k not in rkeys:
                refusals.append(owner)
                rkeys[k] = len(refusals)
            entries.append([None, 0, rkeys[k]])
            continue
        except (headless.RunFailed, ValueError) as e:
            problems.append(f"{where}: point p{i} {values}: {e}")
            entries.append([None, 0, 0])
            continue
        cpu += oc.cpu_s
        if event_frame_is_last(msgs, oc):
            problems.append(f"{where}: point p{i} {values}: its last frame is the stop event's own (R2-F F3)")
        problems += [f"{where}: point p{i} {values}: {x}" for x in unread(viz, spec, msgs)]
        bad_counts = not_counts(msgs, counts)
        if bad_counts:
            problems.append(f"{where}: point p{i} {values}: a counter reads {bad_counts}, not whole numbers ≥ 0")
        for st, n in oc.check_counts().items():
            checks[st] = checks.get(st, 0) + n
        try:
            items, pk = pack_items(spec, msgs, base, bsha)
            for _m, bl in items:  # the quantisation's refusals (±inf) are raised when a blob is stored
                for arr in bl.values():
                    protocol.stored(arr)
        except ValueError as e:  # a blob the quantisation refuses (±inf)
            problems.append(f"{where}: point p{i} {values} cannot be packed: {e}")
            entries.append([None, 0, 0])
            continue
        _merge_quant(quant, pk)
        packed[i] = items
        entries.append(None)  # filled once the pool is known
        if time.monotonic() - t0 > 60:
            t0 = time.monotonic()
            log(f"  {where}: point {i + 1} of {len(pts)}")
    # the pool (EX2 §5 F10): a blob stored by two or more points is kept once; the points name it
    order = [i for i in range(len(pts)) if i in packed]
    pooled, pool = headless.pool_points([packed[i] for i in order])
    for i, items in zip(order, pooled):
        data = encode_items(items)
        sha = hashlib.sha256(data).hexdigest()
        name = f"p{i}.{sha[:8]}.lfpt.gz"
        files[name] = data
        entries[i] = [name, len(data), 0]
        if len(data) > pt_l:
            problems.append(f"{where}: point p{i} {dict(zip(params, pts[i]))} is {len(data) / 1e3:.0f} kB, over the "
                            f"hard limit of {pt_l / 1e3:.0f} kB: a coarser display grid, more quantisation or fewer "
                            f"frames")
        elif len(data) > pt_t and not L.accepted(vid, f"atlas:{spec['id']}"):
            warns.append(f"{where}: point p{i} is {len(data) / 1e3:.0f} kB, over the target of {pt_t / 1e3:.0f} kB")
    pool_gz = headless.pool_file(pool) if pool else None
    pool_sha = hashlib.sha256(pool_gz).hexdigest() if pool_gz else None
    pool_name = f"pool.{pool_sha[:8]}.lfpt.gz" if pool_gz else None
    base_name = f"base.{bsha[:8]}.lfpt.gz"
    total = len(base_gz) + sum(len(d) for d in files.values()) + (len(pool_gz) if pool_gz else 0)
    if total > at_l:
        problems.append(f"{where}: {total / L.MB:.2f} MB for the atlas is over the hard limit of {at_l / L.MB:.0f} MB")
    elif total > at_t:
        why = L.accepted(vid, f"atlas:{spec['id']}")
        warns.append(f"{where}: {total / L.MB:.2f} MB is over the atlas's target of {at_t / L.MB:.0f} MB"
                     + (f" (accepted: {why})" if why else ""))
    if checks.get("failed"):
        problems.append(f"{where}: {checks['failed']} check(s) end failed")
    if problems:
        return None, problems, warns
    made = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    manifest = {"world": vid, "atlas": spec["id"], "screen": spec["screen"], "step": spec["step"],
                "atlas_version": L.ATLAS_VERSION, "key": plan_entry["key"], "version": viz.get("version", ""),
                "code_hash": plan_entry["code_hash"], "recorder_hash": plan_entry["recorder_hash"],
                "seed": spec["seed"], "preset": spec["preset"], "fixed": spec["fixed"],
                "controls": [_manifest_control(c) for c in spec["controls"]],
                "frame_dt": spec["frame_dt"], **({"fps": spec["fps"]} if spec.get("fps") is not None else {}),
                "stop": spec["stop"],
                "base": {"file": base_name, "bytes_gz": len(base_gz), "sha256": bsha},
                **({"pool": {"file": pool_name, "bytes_gz": len(pool_gz), "sha256": pool_sha}} if pool_gz else {}),
                "points": entries, "refusals": refusals, "checks": checks, "quant": quant, "references": refs,
                "bytes_gz": total}
    text = json.dumps(protocol.clean(manifest), ensure_ascii=False, separators=(",", ":")) + "\n"
    msha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    man_name = f"atlas.{msha[:8]}.json"
    tmp = _staged(out, vid, spec["id"])  # installed by build_world once the code is known unchanged (R2-F F1)
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    for name, data in files.items():
        (tmp / name).write_bytes(data)
    (tmp / base_name).write_bytes(base_gz)
    if pool_gz:
        (tmp / pool_name).write_bytes(pool_gz)
    (tmp / man_name).write_text(text, encoding="utf-8")
    n_ref = sum(1 for e in entries if e[2])
    log(f"{where}: {len(entries) - n_ref} points, {n_ref} refused, {total / 1e3:.0f} kB gzip "
        f"(largest point {max([len(d) for d in files.values()] or [0]) / 1e3:.1f} kB), cpu {cpu:.1f} s")
    entry = {"id": spec["id"], "screen": spec["screen"], "step": spec["step"],
             "file": f"{ATLAS_DIR}/{spec['id']}/{man_name}", "key": plan_entry["key"], "points": len(entries) - n_ref,
             "refused": n_ref, "bytes_gz": total, "checks": checks, "cpu_s": round(cpu, 1),
             "version": viz.get("version", ""), "code_hash": plan_entry["code_hash"], "made": made}
    return entry, [], warns


def build_world(vid: str, out: Path, only: list[str] | None = None, log=_log, sig0: tuple | None = None,
                since_ns: int | None = None) -> tuple[list[dict], list[str], list[str]]:
    """Build a world's atlases (all, or those named in ``only``); old entries of the atlases not built now are kept
    while their key is current. Returns (the index's ``atlases`` entries in the registry's order, problems, warnings).
    The index itself is written by the caller (``write_atlases`` or ``site/record.py``).

    The keys are those of ``sig0`` (``sitelib.code_signature``: the code before the world was imported; taken now when
    None). After the world's last atlas the code is compared with it (``sitelib.check_unchanged``, with ``since_ns`` the
    time the builder started): when it changed, nothing built now is installed, the folder is left as it was and
    ``sitelib.CodeChanged`` is raised (review R2-F F1: output of the old code under the new code's key)."""
    sig0 = L.code_signature(vid) if sig0 is None else tuple(sig0)
    plan = L.planned_world(vid, code=sig0[0], recorder=sig0[1])
    old = {e.get("id"): e for e in (L.read_index(out, vid) or {}).get("atlases") or []}
    viz = registry.load(vid)
    specs = {a["id"]: a for a in registry.atlases_of(viz)}
    entries, problems, warns, built = [], [], [], []
    try:
        for pa in plan["atlases"]:
            aid = pa["id"]
            if only is None or aid in only:
                e, probs, w = build_atlas(vid, specs[aid], out, {**pa, "code_hash": plan["code_hash"],
                                                                "recorder_hash": plan["recorder_hash"]}, log)
                problems += probs
                warns += w
                if e is not None:
                    entries.append(e)
                    built.append(aid)
                    continue
            prev = old.get(aid)
            if prev and prev.get("key") == pa["key"] and L.atlas_files_ok(out, vid, prev):  # R2-F F7: every file
                entries.append(prev)
            elif prev:
                log(f"  {vid}/{aid}: its old atlas is stale or incomplete (key {prev.get('key')}, now {pa['key']}): "
                    f"dropped")
        L.check_unchanged(vid, sig0, since_ns)
    except BaseException:
        for aid in built:
            shutil.rmtree(_staged(out, vid, aid), ignore_errors=True)
        raise
    for aid in built:
        folder = Path(out) / vid / ATLAS_DIR / aid
        if folder.exists():
            shutil.rmtree(folder)
        os.replace(_staged(out, vid, aid), folder)
    keep = {e["id"] for e in entries}
    adir = Path(out) / vid / ATLAS_DIR
    for d in sorted(adir.iterdir()) if adir.is_dir() else []:  # atlases the registry no longer asks for, or failed
        if d.is_dir() and d.name not in keep:
            shutil.rmtree(d)
    return entries, problems, warns


def write_atlases(out: Path, vid: str, entries: list[dict]):
    """Put a world's atlases into its ``index.json`` (its recordings kept as they are)."""
    idx = L.read_index(out, vid)
    if idx is None:
        plan = L.planned_world(vid)
        idx = {"world": vid, "version": plan["version"], "recorder": L.RECORDER_VERSION,
               "recorder_hash": plan["recorder_hash"], "code_hash": plan["code_hash"], "made": "", "recordings": []}
    idx["atlases"] = entries
    L.write_index(out, vid, idx)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the atlases of the screens (design of 2026-11-14 §1).")
    ap.add_argument("--world", action="append", default=[], help="a world id (repeatable; an old id works too)")
    ap.add_argument("--atlas", action="append", default=[], help="only this atlas id of the world(s) (repeatable)")
    ap.add_argument("--all", action="store_true", help="every world that has screens")
    ap.add_argument("--stale", action="store_true", help="the worlds whose atlases are missing or stale")
    ap.add_argument("--out", default=str(L.RECORDINGS), help="the recordings folder (default visualizations/recordings)")
    a = ap.parse_args(argv)
    os.environ["LFPHYS_NO_GPU"] = "1"  # the CPU, as in CI: an atlas's key does not cover the device (review R-F F10)
    out = Path(a.out)
    # every world's code hashed before any world is imported (review R2-F F1): the keys name the code that runs
    cand = [registry.resolve(w) for w in a.world] + (registry.viz_ids() if a.all or a.stale else [])
    sigs = {}
    for w in dict.fromkeys(cand):
        try:
            sigs[w] = L.code_signature(w)
        except KeyError:  # no such world: refused below
            pass
    have = [w for w in L.demo_worlds() if registry.atlases_of(registry.load(w))]
    worlds = [registry.resolve(w) for w in a.world]
    if a.all:
        worlds += have
    if a.stale:
        worlds += [w for w in have if set(L.atlas_status(out, L.planned_world(w, *sigs[w])).values()) - {"present"}]
    worlds = list(dict.fromkeys(worlds))
    bad = [w for w in worlds if w not in have]
    if bad:
        _log(f"no atlases (or no such world): {bad}")
        return 2
    problems = []
    for w in worlds:
        try:
            entries, probs, warns = build_world(w, out, a.atlas or None, sig0=sigs[w], since_ns=STARTED_NS)
        except L.CodeChanged as e:  # nothing of the world kept, its index as it was
            problems.append(str(e))
            continue
        write_atlases(out, w, entries)
        problems += probs
        for x in warns:
            _log(f"WARN {x}")
    for p in problems:
        _log(f"PROBLEM: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
