# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What the site's scripts share (``visualizations/site/``; design of the start page §4, §5; design of the screens and
atlases ``lfphys/sources/explore_2026-11-14_design.md`` §1.4, §1.8): the paths, the recorder's and the atlases'
versions, the budgets, the keys of the recordings and the atlases, and the reading and writing of a recordings folder.

The scripts run from ``visualizations/`` (``python3 site/<script>.py``), in Docker, on the CPU. This folder is not a
package (``site`` is the name of a standard module), so each script puts this folder and ``server/`` on ``sys.path``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIZ = HERE.parent  # visualizations/
REPO = VIZ.parent
for _p in (str(HERE), str(VIZ / "server")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lfviz import registry  # noqa: E402

#: the recorder's version: part of every recording's key; raise it when the recorder writes something different (2: the
#: frames carry no ``cpu_ms``, the header's kernels are this recording's own; site review F1, F2). The recorder's code and
#: the image's locked dependencies are in the key too (``recorder_hash``), so an edit there needs no raise to be seen.
RECORDER_VERSION = "2"
#: the atlases' version: part of every atlas's key; raise it when the atlas's files change their form (design §1.4; 2:
#: every point's header names its base file's sha256, ``$base``, and the manifest has no ``made`` and ``cpu_s``, which
#: stay in the index entry; review R-F F2, F7; 3: a pool of the blobs the points share, ``pool.<hash8>.lfpt.gz``, named
#: in the manifest as the base is, EX2 §5 F10)
ATLAS_VERSION = "3"
RECORDINGS = VIZ / "recordings"  # the local recordings (git-ignored; the server serves them at /recordings/)
IMAGES = REPO / "docs" / "images"  # the README's and the cards' pictures (posters.mjs)

MB = 1_000_000
#: the budgets of the design §4.3 (decimal units): (target, hard limit). Over the target the recorder thins frames; over
#: the hard limit the recording, or the site's check, fails.
BUDGET = {
    "file": (3 * MB, 10 * MB),  # one recording file (gzip)
    "world": (12 * MB, 25 * MB),  # one world, all its recordings and atlases
    "point": (150_000, 400_000),  # one atlas point file (gzip; design of 2026-11-14 §1.8)
    "atlas": (6 * MB, 12 * MB),  # one atlas: its base and points (an Explore screen or a lab step)
    "poster": (150_000, 400_000),  # one poster picture (JPEG, 1200 px wide)
    "site": (600 * MB, 900 * MB),  # the whole site (Pages allows 1 GB)
}
#: thinning never leaves fewer frames than this per played second
MIN_KEPT_FPS = 2.0
#: recordings (and worlds: rec None) accepted over their target, within the hard limit, with the reason (integrator,
#: 2026-11-13): ``check.py`` and ``record.py`` report them as "over target (accepted)". Frames are not what makes them
#: large, so the frame stride cannot help; only ``seconds`` could, at the cost of what the recording shows.
ACCEPTED = {
    ("u38_wave_3d", "double"): "one 6.3 MB float volume of the whole 3-D field, sent once at the start",
    ("r12_double_slit_2d", "narrow"): "the wave field as 'wave' snapshots (~94 kB each, ~5 per played second, 101 "
                                      "in 20 s) that the record keeps so that scrolling back shows the wave of that "
                                      "moment",
    ("r12_double_slit_2d", "mark180"): "the wave field as 'wave' snapshots (~94 kB each, ~5 per played second, 101 "
                                       "in 20 s) that the record keeps so that scrolling back shows the wave of that "
                                       "moment",
    ("r12_double_slit_2d", None): "its two recordings of the wave field (see each)",
    ("s03_projectile", "atlas:explore"): "940 points of the ball's real forces (EX2 §10): the drawer's values are check "
                                         "messages in every point (about 1.05 MB of its 6.63 MB, 0.45 MB of them the "
                                         "information rows: the constant C_d, the Magnus band, the air's shares, the "
                                         "Earth's rotation, the history force's bound), under the 12 MB limit",
}


def accepted(world: str, rec: str | None = None) -> str | None:
    """Why a recording (or, with ``rec`` None, a world) is accepted over its target; None when it is not."""
    return ACCEPTED.get((world, rec))


def spec_of(rec: dict) -> dict:
    """The part of a recording spec (``registry.recordings_of``) that decides what is recorded (``captions`` and
    ``quantize`` only when the spec has them, so that a spec without them keeps its key's form)."""
    out = {k: rec.get(k) for k in ("id", "preset", "seconds", "fps", "speed", "seed", "poster", "script")}
    for k in ("captions", "quantize"):
        if rec.get(k):
            out[k] = rec[k]
    return out


#: the files besides the world's code that decide a recording's or an atlas's bytes (site review F3): the recorder (its
#: frame clock, ``DROP``, ``STRIDES``, the packing), the atlases' builder, the headless runner and packer, and the image's
#: locked dependencies (numpy, scipy … decide the numbers)
RECORDER_FILES = (HERE / "record.py", HERE / "atlas.py", VIZ / "server" / "lfviz" / "headless.py",
                  VIZ / "docker" / "requirements.lock", VIZ / "docker" / "Dockerfile")


def recorder_hash(files=None) -> str:
    """sha256 over the recorder's files (``RECORDER_FILES``) and the budgets that decide the thinning (``BUDGET``'s file
    and world, ``MIN_KEPT_FPS``), 16 hex digits: part of every recording's key. A missing file counts as its name."""
    h = hashlib.sha256()
    for f in RECORDER_FILES if files is None else files:
        f = Path(f)
        h.update(f.name.encode() + b"\0")
        try:
            h.update(f.read_bytes())
        except OSError:
            h.update(b"<missing>")
        h.update(b"\0")
    h.update(json.dumps([BUDGET["file"], BUDGET["world"], MIN_KEPT_FPS]).encode())
    return h.hexdigest()[:16]


def spec_key(rec: dict, code_hash: str, recorder: str | None = None) -> str:
    """The recording's key: sha256(spec + recorder version + the recorder's hash + the world's code hash), 16 hex
    digits."""
    spec = json.dumps(spec_of(rec), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    rh = recorder_hash() if recorder is None else recorder
    return hashlib.sha256(f"{spec}\n{RECORDER_VERSION}\n{rh}\n{code_hash}".encode()).hexdigest()[:16]


def _control_spec(c: dict, grid: bool = True) -> dict:
    out = {"param": c["param"], "values": c["values"], "default": c.get("default")} if grid \
        else {"param": c["param"], "default": c.get("default")}
    if c.get("sets") is not None:  # a compound control: the parameters it sets decide every point (EX2 §5 F3)
        out["sets"] = c["sets"]
    return out


def atlas_spec_of(a: dict) -> dict:
    """The part of an atlas (``registry.atlases_of``) that decides its files (design §1.4): the preset, the fixed values,
    the controls' values and defaults (a compound control's ``sets`` too), the seed, the clock (``frame_dt``, or ``fps``
    when the atlas takes frames per played second: EX2 §5 F1), the stop rule, what is dropped, the quantisation and the
    ids of the laws' references (the manifest's ``references``). Labels and the playback ``speed`` are not in it: they
    change no byte."""
    out = {"id": a["id"], "preset": a["preset"], "fixed": a["fixed"],
           "controls": [_control_spec(c) for c in a["controls"]],
           "seed": a["seed"], "frame_dt": a.get("frame_dt"), "stop": a["stop"], "drop": a["drop"],
           "quantize": a["quantize"], "laws": list(a.get("laws") or [])}
    if a.get("fps") is not None:
        out["fps"] = a["fps"]
    return out


def atlas_key(a: dict, code_hash: str, recorder: str | None = None, grid: bool = True) -> str:
    """The atlas's key: sha256(atlas spec + ATLAS_VERSION + the recorder's hash + the world's code hash), 16 hex digits.
    ``grid=False``: without the controls' values (the key of the server's live points, design §3.7; the defaults stay:
    they decide the base header)."""
    spec = atlas_spec_of(a)
    if not grid:
        spec["controls"] = [_control_spec(c, grid=False) for c in a["controls"]]
    text = json.dumps(spec, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    rh = recorder_hash() if recorder is None else recorder
    return hashlib.sha256(f"{text}\n{ATLAS_VERSION}\n{rh}\n{code_hash}".encode()).hexdigest()[:16]


def world_key(keys: list[str]) -> str:
    """A world's key over the keys of all its recordings and atlases (the cache key of the CI's record job)."""
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


def demo_worlds() -> list[str]:
    """The worlds that have recordings: every world but the laboratories."""
    out = []
    for vid in registry.viz_ids():
        viz = registry.load(vid)
        if viz.get("kind") != "playground" and viz.get("recordings"):
            out.append(vid)
    return out


def planned_world(vid: str, code: str | None = None, recorder: str | None = None) -> dict:
    """What the registry asks of a world's recordings now: {world, version, code_hash, recordings: [spec + key]}.
    ``code`` and ``recorder``: the world's code hash and the recorder's hash when the caller has them (a server's
    ``registry.code_hash_current``); by default both are computed from the files."""
    viz = registry.load(vid)
    code = registry.code_hash(vid) if code is None else code
    rh = recorder_hash() if recorder is None else recorder
    recs = []
    for r in registry.recordings_of(viz):
        recs.append({**r, "key": spec_key(r, code, rh)})
    atl = [{"id": a["id"], "screen": a["screen"], "step": a["step"], "key": atlas_key(a, code, rh),
            "points": len(list(_product(a["controls"])))} for a in registry.atlases_of(viz)]
    keys = [r["key"] for r in recs] + ([f"atlas:{a['id']}:{a['key']}" for a in atl] if atl else [])
    return {"world": vid, "version": viz.get("version", ""), "code_hash": code, "recorder_hash": rh,
            "recordings": recs, "atlases": atl, "key": world_key(keys)}


def _product(controls):
    import itertools  # noqa: PLC0415
    return itertools.product(*[c["values"] for c in controls])


def read_index(folder: Path, vid: str) -> dict | None:
    """``<folder>/<world>/index.json``, or None."""
    f = Path(folder) / vid / "index.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def status(folder: Path, plan: dict) -> dict:
    """{rec id: "present" | "stale" | "missing"} of a world's recordings against a recordings folder: present when the
    index holds the recording with the same key and its file is there with its size; stale when the index holds it with
    another key (or its file is gone or differs); missing otherwise."""
    idx = read_index(folder, plan["world"]) or {}
    have = {r.get("id"): r for r in idx.get("recordings") or []}
    out = {}
    for r in plan["recordings"]:
        h = have.get(r["id"])
        if h is None:
            out[r["id"]] = "missing"
            continue
        f = Path(folder) / plan["world"] / str(h.get("file", ""))
        ok = h.get("key") == r["key"] and f.is_file() and f.stat().st_size == h.get("bytes_gz")
        out[r["id"]] = "present" if ok else "stale"
    return out


def atlas_files_ok(folder: Path, vid: str, entry: dict) -> bool:
    """Whether an index entry's atlas is all there: its manifest, its base with its size, its pool with its size (EX2 §5
    F10), and every point the manifest names with its size (``stat`` only; review R-F F6: a deleted point left the
    atlas "present" while the build left it out)."""
    mf = Path(folder) / vid / str(entry.get("file", ""))
    try:
        man = json.loads(mf.read_text(encoding="utf-8"))
        base = man["base"]
        files = [(base["file"], base["bytes_gz"])] + [(p[0], p[1]) for p in man["points"] if p and p[0]]
        if man.get("pool"):
            files.append((man["pool"]["file"], man["pool"]["bytes_gz"]))
        return all((mf.parent / str(n)).stat().st_size == b for n, b in files)
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return False


def atlas_status(folder: Path, plan: dict) -> dict:
    """{atlas id: "present" | "stale" | "missing"} of a world's atlases against a recordings folder: present when the
    index holds the atlas with the same key and its manifest, its base and every point it names are there with their
    sizes (``atlas_files_ok``); stale when held with another key (or a file is gone or differs); missing otherwise."""
    idx = read_index(folder, plan["world"]) or {}
    have = {a.get("id"): a for a in idx.get("atlases") or []}
    out = {}
    for a in plan.get("atlases") or []:
        h = have.get(a["id"])
        if h is None:
            out[a["id"]] = "missing"
            continue
        ok = h.get("key") == a["key"] and atlas_files_ok(folder, plan["world"], h)
        out[a["id"]] = "present" if ok else "stale"
    return out


def expected(plan: dict) -> dict:
    """What a world's recordings and atlases are expected to be by the code here (``planned_world``): ``{version,
    code_hash, recordings: {id: key}, atlases: {id: key}}``; ``GET /api/recordings`` and the site's
    ``api/recordings.json`` carry it per world, so that a server's player takes the public site's atlas or recording
    only when its key is this one (integrator D11)."""
    return {"version": plan["version"], "code_hash": plan["code_hash"],
            "recordings": {r["id"]: r["key"] for r in plan["recordings"]},
            "atlases": {a["id"]: a["key"] for a in plan.get("atlases") or []}}


def write_index(folder: Path, vid: str, index: dict):
    """``<folder>/<world>/index.json`` written atomically."""
    import os  # noqa: PLC0415
    d = Path(folder) / vid
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "index.json.tmp"
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, d / "index.json")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
