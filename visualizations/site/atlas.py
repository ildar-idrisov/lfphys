# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The atlases of the screens: computed points on a grid of controls (design
``lfphys/sources/explore_2026-11-14_design.md`` §1).

    python3 site/atlas.py --world s03_projectile [--atlas explore] [--out DIR]
    python3 site/atlas.py --all | --stale [--out DIR]

An atlas is the set of points of one Explore screen (its id is the screen's) or of one lab step (``<screen>.<step>``)
on the grid of its controls (``registry.atlases_of``). A point is the world's own run (``lfviz.headless.run_spec``):
the screen's preset, its ``fixed`` values and the grid values on top, the screen's seed, frames every ``frame_dt`` of
world time from t = 0 until the screen's stop rule. A point the world refuses (``check_params``) is ``refused`` with its
text; a point that fails (an error, an exception, a check ending ✗, a stop event not reached) fails the atlas.

Files, per world (``<out>/<world>/atlas/<atlas>/``):

* ``base.<hash8>.lfpt.gz``: gzip -9 (mtime 0) of an ``LFVREC1`` stream of one message, the screen's base header: the
  header of the default point (every control at its default), its blobs quantised by the screen's ``quantize``;
* ``p<i>.<hash8>.lfpt.gz``: the point with the flattened index ``i`` (row-major over the controls in their order, the
  last control fastest): its header as a delta against the base header (with ``$base``, the base file's sha256: a
  reader merges it only with that base), then the world's messages in order (frames at
  ``frame_dt``, the screen's dropped message types and frame blobs left out, the ``quantize`` map's blobs quantised:
  ``lfviz.headless.Packer``, ``lfviz.protocol``), then ``end {reason: "atlas"}``;
* ``atlas.<hash8>.json``, the manifest: ``{world, atlas, screen, step, atlas_version, key, version, code_hash,
  recorder_hash, seed, preset, fixed, controls: [{param, values, default}], frame_dt, stop, base: {file, bytes_gz,
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
Exit code: 0 when every atlas was built within its hard limits, 1 otherwise.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import itertools
import json
import os
import shutil
import sys
import time
from pathlib import Path

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


def run_point(vid: str, spec: dict, values: dict, seed: int | None = None, log=_log):
    """One point run headless: (messages [(meta, blobs)], Outcome). Raises ``headless.PointRefused``,
    ``headless.RunFailed`` or ``ValueError`` (the schema refuses the values)."""
    msgs = []
    oc = headless.run_spec(vid, spec["preset"], {**spec["fixed"], **values}, spec["seed"] if seed is None else seed,
                           {"frame_dt": spec["frame_dt"]}, spec["stop"], emit=lambda m, b=None: msgs.append((m, b)),
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
    """What needs the world built (design §2.1, §2.5): the readouts and the instruments' measurables in its header."""
    have = _measurables(header_meta)
    sc = _screen_of(viz, spec["screen"])
    out = []
    if sc["kind"] == "explore":
        out += [f"readout {r!r} is not a measurable of the world's header ({sorted(have)})"
                for r in sc.get("readouts") or [] if r not in have]
    else:
        step = next(s for s in sc["steps"] if s["id"] == spec["step"])
        for iid in step["instruments"]:
            reads = sc["instruments"][iid].get("reads")
            if reads and not reads.startswith("control:") and reads not in have:
                out.append(f"instrument {iid} reads {reads!r}, not a measurable of the world's header ({sorted(have)})")
            if reads and reads.startswith("control:") and reads[8:] not in {c["param"] for c in spec["controls"]} \
                    and reads[8:] not in spec["fixed"]:
                out.append(f"instrument {iid} reads {reads!r}: not a control or a fixed value of the step")
    return out


def reference(viz: dict, spec: dict, params: dict, ref_id: str) -> dict:
    """The reference of one law of a lab step, computed by the world (``Simulation.lab_reference(step_id, fixed, values,
    reference)``, design §2.3, integrator D4)."""
    ref = viz["simulation"].lab_reference(spec["step"], dict(params),
                                          {c["param"]: list(c["values"]) for c in spec["controls"]}, reference=ref_id)
    if not isinstance(ref, dict) or not isinstance(ref.get("value"), (int, float)) or isinstance(ref["value"], bool):
        raise ValueError(f"lab_reference({spec['step']!r}, reference={ref_id!r}) gave {ref!r}: "
                         f"{{value, unit, label, how, kind}}")
    return protocol.clean(ref)


def build_atlas(vid: str, spec: dict, out: Path, plan_entry: dict, log=_log) -> tuple[dict | None, list[str], list[str]]:
    """Compute and write one atlas. Returns (its index entry or None when it failed, problems, warnings)."""
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
        for st, n in oc.check_counts().items():
            checks[st] = checks.get(st, 0) + n
        try:
            data, pk = pack_point(spec, msgs, base, bsha)
        except ValueError as e:  # a blob the quantisation refuses (±inf)
            problems.append(f"{where}: point p{i} {values} cannot be packed: {e}")
            entries.append([None, 0, 0])
            continue
        _merge_quant(quant, pk)
        sha = hashlib.sha256(data).hexdigest()
        name = f"p{i}.{sha[:8]}.lfpt.gz"
        files[name] = data
        entries.append([name, len(data), 0])
        if len(data) > pt_l:
            problems.append(f"{where}: point p{i} {values} is {len(data) / 1e3:.0f} kB, over the hard limit of "
                            f"{pt_l / 1e3:.0f} kB: a coarser display grid, more quantisation or fewer frames")
        elif len(data) > pt_t and not L.accepted(vid, f"atlas:{spec['id']}"):
            warns.append(f"{where}: point p{i} is {len(data) / 1e3:.0f} kB, over the target of {pt_t / 1e3:.0f} kB")
        if time.monotonic() - t0 > 60:
            t0 = time.monotonic()
            log(f"  {where}: point {i + 1} of {len(pts)}")
    base_name = f"base.{bsha[:8]}.lfpt.gz"
    total = len(base_gz) + sum(len(d) for d in files.values())
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
                "controls": [{"param": c["param"], "values": c["values"], "default": c.get("default")}
                             for c in spec["controls"]],
                "frame_dt": spec["frame_dt"], "stop": spec["stop"],
                "base": {"file": base_name, "bytes_gz": len(base_gz), "sha256": bsha},
                "points": entries, "refusals": refusals, "checks": checks, "quant": quant, "references": refs,
                "bytes_gz": total}
    text = json.dumps(protocol.clean(manifest), ensure_ascii=False, separators=(",", ":")) + "\n"
    msha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    man_name = f"atlas.{msha[:8]}.json"
    folder = Path(out) / vid / ATLAS_DIR / spec["id"]
    tmp = folder.with_name(folder.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    for name, data in files.items():
        (tmp / name).write_bytes(data)
    (tmp / base_name).write_bytes(base_gz)
    (tmp / man_name).write_text(text, encoding="utf-8")
    if folder.exists():
        shutil.rmtree(folder)
    os.replace(tmp, folder)
    n_ref = sum(1 for e in entries if e[2])
    log(f"{where}: {len(entries) - n_ref} points, {n_ref} refused, {total / 1e3:.0f} kB gzip "
        f"(largest point {max([len(d) for d in files.values()] or [0]) / 1e3:.1f} kB), cpu {cpu:.1f} s")
    entry = {"id": spec["id"], "screen": spec["screen"], "step": spec["step"],
             "file": f"{ATLAS_DIR}/{spec['id']}/{man_name}", "key": plan_entry["key"], "points": len(entries) - n_ref,
             "refused": n_ref, "bytes_gz": total, "checks": checks, "cpu_s": round(cpu, 1),
             "version": viz.get("version", ""), "code_hash": plan_entry["code_hash"], "made": made}
    return entry, [], warns


def build_world(vid: str, out: Path, only: list[str] | None = None, log=_log) -> tuple[list[dict], list[str], list[str]]:
    """Build a world's atlases (all, or those named in ``only``); old entries of the atlases not built now are kept
    while their key is current. Returns (the index's ``atlases`` entries in the registry's order, problems, warnings).
    The index itself is written by the caller (``write_atlases`` or ``site/record.py``)."""
    plan = L.planned_world(vid)
    old = {e.get("id"): e for e in (L.read_index(out, vid) or {}).get("atlases") or []}
    viz = registry.load(vid)
    specs = {a["id"]: a for a in registry.atlases_of(viz)}
    entries, problems, warns = [], [], []
    for pa in plan["atlases"]:
        aid = pa["id"]
        if only is None or aid in only:
            e, probs, w = build_atlas(vid, specs[aid], out, {**pa, "code_hash": plan["code_hash"],
                                                            "recorder_hash": plan["recorder_hash"]}, log)
            problems += probs
            warns += w
            if e is not None:
                entries.append(e)
                continue
        prev = old.get(aid)
        if prev and prev.get("key") == pa["key"] and (Path(out) / vid / str(prev.get("file", ""))).is_file():
            entries.append(prev)
        elif prev:
            log(f"  {vid}/{aid}: its old atlas is stale (key {prev.get('key')}, now {pa['key']}): dropped")
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
    have = [w for w in L.demo_worlds() if registry.atlases_of(registry.load(w))]
    worlds = [registry.resolve(w) for w in a.world]
    if a.all:
        worlds += have
    if a.stale:
        worlds += [w for w in have if set(L.atlas_status(out, L.planned_world(w)).values()) - {"present"}]
    worlds = list(dict.fromkeys(worlds))
    bad = [w for w in worlds if w not in have]
    if bad:
        _log(f"no atlases (or no such world): {bad}")
        return 2
    problems = []
    for w in worlds:
        entries, probs, warns = build_world(w, out, a.atlas or None)
        write_atlases(out, w, entries)
        problems += probs
        for x in warns:
            _log(f"WARN {x}")
    for p in problems:
        _log(f"PROBLEM: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
