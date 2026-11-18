# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Remake the committed fixtures of the screens and the quantised blobs (design
``lfphys/sources/explore_2026-11-14_design.md`` §8, §9: the player's step works on them):

* ``tests/site_worlds/recordings/s98_atlas_toy/``: the toy world's recordings and atlases as ``site/record.py`` makes
  them (``index.json``, ``*.lfrec.gz``, ``atlas/<atlas>/{atlas.<h>.json, base.<h>.lfpt.gz, p<i>.<h>.lfpt.gz}``); a
  server started with ``LFVIZ_EXTRA=tests/site_worlds LFVIZ_RECORDINGS=tests/site_worlds/recordings`` serves them;
* ``tests/site_worlds/quant/cases.lfrec``: an ``LFVREC1`` stream of messages whose blobs are quantised in every way the
  protocol allows (u1 and u2, lin and sqrt, one range and a range per column, NaN codes), and
  ``tests/site_worlds/quant/cases.json``: for each message and blob, the decoded float32 values as their bit patterns
  (``"%08x"`` of the IEEE single), which ``player/js/api.js decode`` must give bit for bit (``tests/test_protocol_quant.py``
  checks the Python side);
* ``tests/site_worlds/quant/pool_point.lfpt.gz``: the first point of the toy's ``explore`` atlas that has pooled blobs,
  with its pooled blobs put back (``headless.unpool``: the bytes the point would have without a pool, as a live point
  has them), and ``pool_point.json`` naming it; ``player/js/tests/atlas.test.mjs`` decodes the pooled point with the
  atlas's pool and compares (EX2 §5 F10, §7), ``tests/test_atlas.py`` checks it against the committed fixture.

    docker run --rm --memory=4g -e LFPHYS_NO_GPU=1 -e LFVIZ_EXTRA=/lf/visualizations/tests/site_worlds \\
      --user "$(id -u):$(id -g)" -v "$PWD:/lf" -w /lf/visualizations lfphys-viz python3 tests/site_worlds/make_fixture.py

The keys in the fixture's index go stale with any change of the engine, of ``lfviz`` or of the toy world (they cover the
code's hash), and a server's player refuses a recording or an atlas whose key is not the one its code gives (integrator
D11). So the committed fixture serves only the player's Node tests (``player/js/tests``: the decoding, the header
merge, the fit), which compare no keys; a browser test against a server builds what it needs first into a folder of its
own with ``site/fixtures.py`` (integrator, 2026-11-17), and the Python tests that need current keys build their own.
The fixture's files are guarded against drift from the builder: ``tests/test_atlas.py`` checks its format versions and
rebuilds the toy world, comparing every recording, base and point file, and the manifests but for their keys (review
R-F F14); when it fails, run this script.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIZ = HERE.parents[1]
for _p in (str(VIZ / "server"), str(VIZ.parent / "lfphys")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402

from lfviz import headless, protocol  # noqa: E402

WORLD = "s98_atlas_toy"


def quant_cases() -> list[tuple[dict, dict]]:
    """Messages with quantised blobs: every encoding, one range and per-column ranges, NaN codes, a constant column."""
    rng = np.random.default_rng(20261114)
    table = np.column_stack([np.linspace(0, 1.5, 40), rng.normal(3.0, 2.0, 40), rng.uniform(-1e-3, 2e-3, 40),
                             np.full(40, 2.5)])
    with_nan = rng.normal(0, 1, 30)
    with_nan[[3, 17]] = np.nan
    image = rng.uniform(0, 7.5, (12, 20))
    out = []
    for enc in ("u16", "u8", "u16:all", "u8:col"):
        out.append(({"type": "case", "case": f"table {enc}"}, {"a": protocol.quantize(table, enc)}))
    for enc in ("u8sqrt", "u16sqrt"):
        out.append(({"type": "case", "case": f"image {enc}"}, {"a": protocol.quantize(image, enc)}))
    out.append(({"type": "case", "case": "nan u16"}, {"a": protocol.quantize(with_nan, "u16")}))
    out.append(({"type": "case", "case": "nan u8sqrt"}, {"a": protocol.quantize(np.abs(with_nan), "u8sqrt")}))
    out.append(({"type": "case", "case": "mixed: a quantised blob next to a float one"},
                {"x": protocol.quantize(np.linspace(-2, 2, 7), "u16"), "y": np.linspace(-2, 2, 7)}))
    return out


def write_quant(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    msgs = [protocol.encode(m, b) for m, b in quant_cases()]
    data = protocol.MAGIC + b"".join(protocol.frame_stream_item(m) for m in msgs)
    (folder / "cases.lfrec").write_bytes(data)
    expect = []
    for m in msgs:
        meta, blobs = protocol.decode(m)
        expect.append({"case": meta["case"], "blobs": {
            k: {"shape": list(v.shape), "dtype": str(v.dtype),
                "bits": ["%08x" % x for x in np.ascontiguousarray(v, dtype=np.float32).view(np.uint32).ravel()]
                if v.dtype == np.float32 else None,
                "values": None if v.dtype == np.float32 else [float(x) for x in v.ravel()]}
            for k, v in blobs.items()}})
    (folder / "cases.json").write_text(json.dumps(expect, indent=1) + "\n", encoding="utf-8")


def write_world(folder: Path):
    spec = importlib.util.spec_from_file_location("lfsite_record_fixture", VIZ / "site" / "record.py")
    rec = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = rec
    spec.loader.exec_module(rec)
    if (folder / WORLD).exists():
        shutil.rmtree(folder / WORLD)
    index, problems = rec.record_world(WORLD, folder)
    if problems:
        raise SystemExit(f"the fixture failed: {problems}")
    return index


def write_pool_case(folder: Path, recordings: Path, index: dict) -> int:
    """The first point of the toy's ``explore`` atlas with pooled blobs, unpooled, and its name (EX2 §5 F10)."""
    entry = next(a for a in index["atlases"] if a["id"] == "explore")
    man = json.loads((recordings / WORLD / entry["file"]).read_text(encoding="utf-8"))
    d = (recordings / WORLD / entry["file"]).parent
    pool = (d / man["pool"]["file"]).read_bytes()
    for i, (name, _size, state) in enumerate(man["points"]):
        data = (d / name).read_bytes() if not state else b""
        plain = headless.unpool(data, pool) if data else data
        if plain != data:
            (folder / "pool_point.lfpt.gz").write_bytes(plain)
            (folder / "pool_point.json").write_text(json.dumps({"world": WORLD, "atlas": "explore", "point": i}) + "\n",
                                                    encoding="utf-8")
            return i
    raise SystemExit("the toy's explore atlas has no pooled point")


def main() -> int:
    os.environ["LFVIZ_EXTRA"] = str(HERE)  # the toy world (set here only: the tests import this module)
    write_quant(HERE / "quant")
    index = write_world(HERE / "recordings")
    write_pool_case(HERE / "quant", HERE / "recordings", index)
    print(f"quant: {HERE / 'quant'}; {WORLD}: {[e['id'] for e in index['recordings']]} recordings, "
          f"{[(e['id'], e['bytes_gz']) for e in index['atlases']]} atlases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
