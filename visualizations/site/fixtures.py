# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The recordings and atlases a browser test needs, built now into a folder of its own (integrator, 2026-11-17).

    python3 site/fixtures.py --out DIR [--world s98_atlas_toy] [--world s03_projectile …]

A server's player refuses a recording or an atlas whose key is not the one its code gives (integrator D11:
``GET /api/recordings`` → ``expected``), and every key covers the code of the engine, of ``lfviz`` and of the world. So
the committed fixture ``tests/site_worlds/recordings/`` serves only the player's Node tests (decoding, the header merge,
the fit), which compare no keys; a browser test against a server builds what it needs first, with this script, and
serves that folder (``LFVIZ_RECORDINGS=DIR``, with ``LFVIZ_EXTRA`` naming ``tests/site_worlds`` for the test worlds).

Without ``--world`` it builds the toy world ``s98_atlas_toy`` (its recordings and atlases). The test worlds of
``tests/site_worlds`` are found through ``LFVIZ_EXTRA``, which this script sets when it does not name that folder; a
world of the repository is recorded as ``site/record.py`` records it (on the CPU, ``LFPHYS_NO_GPU=1``). Exit code 0
when everything was built, 1 otherwise.

In Docker (a private folder; the repository read-only):

    docker run --rm --name lf-fixtures --memory=4g --user "$(id -u):$(id -g)" -v "$PWD:/lf:ro" -v "$DIR:/fx" \\
      -w /lf/visualizations lfphys-viz python3 site/fixtures.py --out /fx
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_WORLDS = HERE.parent / "tests" / "site_worlds"
DEFAULT = ("s98_atlas_toy",)


def _extra():
    """``LFVIZ_EXTRA`` with ``tests/site_worlds`` in it (before the registry is used)."""
    have = [p for p in os.environ.get("LFVIZ_EXTRA", "").split(os.pathsep) if p.strip()]
    if not any(Path(p).resolve() == TEST_WORLDS.resolve() for p in have):
        os.environ["LFVIZ_EXTRA"] = os.pathsep.join(have + [str(TEST_WORLDS)])


def build(out: Path, worlds: list[str], log=print) -> list[str]:
    """Record every world of ``worlds`` (its recordings, then its atlases) into ``out``; the problems."""
    _extra()
    os.environ["LFPHYS_NO_GPU"] = "1"
    sys.path.insert(0, str(HERE))
    import record  # noqa: PLC0415 - site/record.py, once LFVIZ_EXTRA is set
    problems = []
    for w in worlds:
        index, probs = record.record_world(record.registry.resolve(w), Path(out))
        problems += probs
        log(f"{w}: {len(index['recordings'])} recordings, {len(index['atlases'])} atlases in {out}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the recordings and atlases a browser test needs into a folder.")
    ap.add_argument("--out", required=True, help="the folder to build into (served with LFVIZ_RECORDINGS)")
    ap.add_argument("--world", action="append", default=[], help="a world id (repeatable; default s98_atlas_toy)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    problems = build(out, a.world or list(DEFAULT))
    for p in problems:
        print(f"PROBLEM: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
