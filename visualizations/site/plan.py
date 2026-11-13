# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What the public site needs recorded (design of the start page §5.1).

    python3 site/plan.py [--recordings DIR]            a table: every (world, recording), its key and its state
    python3 site/plan.py --json [--recordings DIR]     the same as JSON
    python3 site/plan.py --matrix [--rerecord stale|all] [--recordings DIR]
                                                       the CI matrix: {"include": [{world, key, force}]}

A recording's key is ``sha256(spec + recorder version + sitelib.recorder_hash() + registry.code_hash(world))``
(``sitelib.spec_key``; the recorder's hash covers ``record.py``, the image's locked dependencies and Dockerfile, and the
budgets that decide the thinning); its state
against a recordings folder is ``present`` (the index holds it with this key and its file), ``stale`` (held with another
key, or its file differs) or ``missing``. ``code_hash`` covers the world's folder, ``lfviz`` and the engine, so a change of
the engine makes every recording stale (accepted for v1, design §5.1).

The matrix lists every world that has recordings, with its world key (over its recordings' keys): the CI's record job
restores ``rec-<world>-<key>`` from its cache and records only on a miss. ``--rerecord all`` sets ``force`` (the job
then records without looking at the cache); with ``--recordings`` and ``stale`` only the worlds not all present are
listed. The matrix is never empty: with nothing to list it holds one entry ``{"world": "", ...}`` that the job skips.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitelib as L  # noqa: E402


def plan(folder: Path | None) -> list[dict]:
    """[{world, version, code_hash, key, recordings: [{..., key, state}]}] for every world with recordings."""
    out = []
    for vid in L.demo_worlds():
        p = L.planned_world(vid)
        st = L.status(folder, p) if folder is not None else {r["id"]: "missing" for r in p["recordings"]}
        for r in p["recordings"]:
            r["state"] = st[r["id"]]
        out.append(p)
    return out


def matrix(worlds: list[dict], rerecord: str, have_folder: bool) -> dict:
    inc = []
    for w in worlds:
        states = {r["state"] for r in w["recordings"]}
        if rerecord == "stale" and have_folder and states == {"present"}:
            continue
        inc.append({"world": w["world"], "key": w["key"], "force": rerecord == "all"})
    return {"include": inc or [{"world": "", "key": "", "force": False}]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="The recordings the public site needs, their keys and states.")
    ap.add_argument("--recordings", default=None, help="a recordings folder to compare with "
                                                        "(default: visualizations/recordings when it exists)")
    ap.add_argument("--matrix", action="store_true", help="print the CI matrix (JSON, one line)")
    ap.add_argument("--rerecord", choices=("stale", "all"), default="stale")
    ap.add_argument("--json", action="store_true", help="print the plan as JSON")
    a = ap.parse_args(argv)
    folder = Path(a.recordings) if a.recordings else (L.RECORDINGS if L.RECORDINGS.is_dir() else None)
    if a.matrix and not a.recordings:
        folder = None  # CI: the cache decides, not a local folder
    worlds = plan(folder)
    if a.matrix:
        print(json.dumps(matrix(worlds, a.rerecord, folder is not None), separators=(",", ":")))
        return 0
    if a.json:
        print(json.dumps(worlds, ensure_ascii=False, indent=1))
        return 0
    n = {"present": 0, "stale": 0, "missing": 0}
    for w in worlds:
        for r in w["recordings"]:
            n[r["state"]] += 1
            print(f"{w['world']:24} {r['id']:16} {r['seconds']:>5} s {r['fps']:>3} fps  {r['key']}  {r['state']}")
    print(f"# {sum(n.values())} recordings in {len(worlds)} worlds: {n['present']} present, {n['stale']} stale, "
          f"{n['missing']} missing ({folder or 'no folder'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
