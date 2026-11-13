# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What the site's scripts share (``visualizations/site/``; design of the start page §4, §5): the paths, the recorder's
version, the budgets, the keys of the recordings and the reading of a recordings folder.

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

#: the recorder's version: part of every recording's key; raise it when the recorder writes something different
RECORDER_VERSION = "1"
RECORDINGS = VIZ / "recordings"  # the local recordings (git-ignored; the server serves them at /recordings/)
IMAGES = REPO / "docs" / "images"  # the README's and the cards' pictures (posters.mjs)

MB = 1_000_000
#: the budgets of the design §4.3 (decimal units): (target, hard limit). Over the target the recorder thins frames; over
#: the hard limit the recording, or the site's check, fails.
BUDGET = {
    "file": (3 * MB, 10 * MB),  # one recording file (gzip)
    "world": (12 * MB, 25 * MB),  # one world, all its recordings
    "step": (2 * MB, 6 * MB),  # one school step, all its grid points (AB1)
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
    ("r12_double_slit_2d", "narrow"): "the wave field as 'wave' snapshots (~94 kB each, ~5 per world second, 101 in "
                                      "20 s) that the record keeps so that scrolling back shows the wave of that moment",
    ("r12_double_slit_2d", "mark180"): "the wave field as 'wave' snapshots (~94 kB each, ~5 per world second, 101 in "
                                       "20 s) that the record keeps so that scrolling back shows the wave of that moment",
    ("r12_double_slit_2d", None): "its two recordings of the wave field (see each)",
}


def accepted(world: str, rec: str | None = None) -> str | None:
    """Why a recording (or, with ``rec`` None, a world) is accepted over its target; None when it is not."""
    return ACCEPTED.get((world, rec))


def spec_of(rec: dict) -> dict:
    """The part of a recording spec (``registry.recordings_of``) that decides what is recorded."""
    return {k: rec.get(k) for k in ("id", "preset", "seconds", "fps", "speed", "seed", "poster", "script")}


def spec_key(rec: dict, code_hash: str) -> str:
    """The recording's key: sha256(spec + recorder version + the world's code hash), 16 hex digits."""
    spec = json.dumps(spec_of(rec), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(f"{spec}\n{RECORDER_VERSION}\n{code_hash}".encode()).hexdigest()[:16]


def world_key(keys: list[str]) -> str:
    """A world's key over the keys of all its recordings (the cache key of the CI's record job)."""
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


def demo_worlds() -> list[str]:
    """The worlds that have recordings: every world but the laboratories."""
    out = []
    for vid in registry.viz_ids():
        viz = registry.load(vid)
        if viz.get("kind") != "playground" and viz.get("recordings"):
            out.append(vid)
    return out


def planned_world(vid: str) -> dict:
    """What the registry asks of a world's recordings now: {world, version, code_hash, recordings: [spec + key]}."""
    viz = registry.load(vid)
    code = registry.code_hash(vid)
    recs = []
    for r in registry.recordings_of(viz):
        recs.append({**r, "key": spec_key(r, code)})
    return {"world": vid, "version": viz.get("version", ""), "code_hash": code, "recordings": recs,
            "key": world_key([r["key"] for r in recs])}


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
