# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The recordings and atlases a browser test needs, built now into a folder of its own (integrator, 2026-11-17).

    python3 site/fixtures.py --out DIR [--world s98_atlas_toy] [--world s03_projectile …]

A server's player refuses a recording or an atlas whose key is not the one its code gives (integrator D11:
``GET /api/recordings`` → ``expected``), and every key covers the code of the engine, of ``lfviz`` and of the world. So
the committed fixture ``tests/site_worlds/recordings/`` serves only the player's Node tests (decoding, the header merge,
the fit), which compare no keys; a browser test against a server builds what it needs first, with this script, and
serves that folder (``LFVIZ_RECORDINGS=DIR``, with ``LFVIZ_EXTRA`` naming ``tests/site_worlds`` for the test worlds).

Without ``--world`` it builds the toy worlds ``s98_atlas_toy`` and ``u96_lab_toy`` (their recordings and atlases). The test worlds of
``tests/site_worlds`` are found through ``LFVIZ_EXTRA``, which this script sets when it does not name that folder; a
world of the repository is recorded as ``site/record.py`` records it (on the CPU, ``LFPHYS_NO_GPU=1``). Exit code 0
when everything was built, 1 otherwise.

In Docker (a private folder; the repository read-only):

    docker run --rm --name lf-fixtures --memory=4g --user "$(id -u):$(id -g)" -v "$PWD:/lf:ro" -v "$DIR:/fx" \\
      -w /lf/visualizations lfphys-viz python3 site/fixtures.py --out /fx
"""

from __future__ import annotations

import time

#: when this script started (``sitelib.check_unchanged``; review R2-F F1)
STARTED_NS = time.time_ns()

import argparse  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
TEST_WORLDS = HERE.parent / "tests" / "site_worlds"
#: the toy worlds of the browser tests: the school toy and the university toy (EX2: a step on Explore's atlas, a law
#: parameter, the world's own speed; review R2-F F6)
DEFAULT = ("s98_atlas_toy", "u96_lab_toy")


def _extra():
    """``LFVIZ_EXTRA`` with ``tests/site_worlds`` in it (before the registry is used)."""
    have = [p for p in os.environ.get("LFVIZ_EXTRA", "").split(os.pathsep) if p.strip()]
    if not any(Path(p).resolve() == TEST_WORLDS.resolve() for p in have):
        os.environ["LFVIZ_EXTRA"] = os.pathsep.join(have + [str(TEST_WORLDS)])


def build(out: Path, worlds: list[str], log=print, since_ns: int | None = None) -> list[str]:
    """Record every world of ``worlds`` (its recordings, then its atlases) into ``out``; the problems. Every world's code
    is hashed before any world is imported, and a world whose code changed during its build (or, with ``since_ns``,
    after that time) keeps nothing (``record.record_world``; review R2-F F1)."""
    _extra()
    os.environ["LFPHYS_NO_GPU"] = "1"
    sys.path.insert(0, str(HERE))
    import record  # noqa: PLC0415 - site/record.py, once LFVIZ_EXTRA is set
    ids = [record.registry.resolve(w) for w in worlds]
    sigs = {w: record.L.code_signature(w) for w in dict.fromkeys(ids)}
    problems = []
    for w in ids:
        index, probs = record.record_world(w, Path(out), sig0=sigs[w], since_ns=since_ns)
        problems += probs
        log(f"{w}: {len(index['recordings'])} recordings, {len(index['atlases'])} atlases in {out}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the recordings and atlases a browser test needs into a folder.")
    ap.add_argument("--out", required=True, help="the folder to build into (served with LFVIZ_RECORDINGS)")
    ap.add_argument("--world", action="append", default=[],
                    help="a world id (repeatable; default s98_atlas_toy and u96_lab_toy)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    problems = build(out, a.world or list(DEFAULT), since_ns=STARTED_NS)
    for p in problems:
        print(f"PROBLEM: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
