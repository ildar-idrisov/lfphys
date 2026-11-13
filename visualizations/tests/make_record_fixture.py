# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Write the recording fixture of player/js/tests/record.test.mjs: a tiny run of the test world p97_osc (one oscillator,
24 frames, a live change in the middle) as a saved recording (``LFVREC1``, gzip -9, DESIGN of the start page §4.1), and
the same messages decoded by ``lfviz.protocol`` as JSON (the meta as the wire carries it, every blob as its dtype, shape
and values), which the browser's ``openRecording`` must reproduce.

    LFVIZ_EXTRA=tests/instruments_worlds python tests/make_record_fixture.py
    python tests/make_record_fixture.py --frames 400 --out <dir>   # a longer one, with its index.json (browser checks)
"""
import argparse
import gzip
import json
import os
import queue
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "player" / "js" / "tests" / "fixtures"
os.environ.setdefault("LFVIZ_EXTRA", str(HERE / "instruments_worlds"))

from lfviz import protocol, registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", type=int, default=24, help="frames at 20 per second (default 24: the unit test's fixture)")
    ap.add_argument("--out", help="write <out>/p97_osc/{one.fixture.lfrec.gz, index.json} (a recordings folder) instead")
    a = ap.parse_args()
    viz = registry.load("p97_osc")
    params, errors = viz["schema"].resolve("one", {})
    assert not errors, errors
    msgs: list[bytes] = []

    def emit(meta, blobs=None):
        msgs.append(protocol.encode(meta, blobs))

    sim = viz["simulation"](params, 1, emit)
    runner = Runner(sim, emit, queue.Queue(), world_info={"preset": "one"})
    runner._start_world()
    runner.handle({"cmd": "play", "args": {}})
    for i in range(1, a.frames + 1):
        runner._advance(i * 0.05)
        runner._frame(0.0)
        if i == a.frames // 2:
            live = [p for p in viz["schema"].to_json()["params"] if p.get("live")]
            if live:
                runner.handle({"cmd": "set", "args": {"values": {live[0]["id"]: live[0]["default"]}}})
    emit({"type": "end", "reason": "recording"})
    # a recording holds no checkpoints and no command log (DESIGN §4.1)
    msgs = [m for m in msgs if protocol.peek_meta(m).get("type") not in ("checkpoint", "command", "resumed", "record_segment")]
    raw = protocol.MAGIC + b"".join(protocol.frame_stream_item(m) for m in msgs)
    if a.out:  # a recordings folder as the site's recorder writes it (CONTRACT: recordings/<world>/index.json)
        import hashlib
        folder = Path(a.out) / "p97_osc"
        folder.mkdir(parents=True, exist_ok=True)
        gz = gzip.compress(raw, compresslevel=9, mtime=0)
        (folder / "one.fixture.lfrec.gz").write_bytes(gz)
        entry = {"id": "one", "preset": "one", "label": viz["schema"].to_json()["presets"][0]["label"],
                 "file": "one.fixture.lfrec.gz", "seconds": a.frames / 20, "fps": 20, "frame_stride": 1, "frames": a.frames,
                 "frames_recorded": a.frames, "bytes": len(raw), "bytes_gz": len(gz), "poster_t": a.frames / 40,
                 "poster_frame": a.frames // 2, "worlds": 1, "seed": 1, "sha256": hashlib.sha256(gz).hexdigest(), "key": "fixture"}
        (folder / "index.json").write_text(json.dumps({"world": "p97_osc", "version": viz.get("version", ""), "recorder": "fixture",
                                                       "code_hash": "fixture0000", "made": "2026-11-13T00:00:00+00:00",
                                                       "recordings": [entry]}, ensure_ascii=False), encoding="utf-8")
        print(folder, len(msgs), "messages", len(gz), "bytes gz")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "p97_osc.lfrec.gz").write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    expected = []
    for m in msgs:
        meta, blobs = protocol.decode(m)
        expected.append({"meta": json.loads(json.dumps(protocol.clean(meta), default=lambda o: o.to_json() if hasattr(o, "to_json") else str(o))),
                         "blobs": {k: {"dtype": protocol._code(v.dtype), "shape": list(v.shape),
                                       "values": [None if x != x else x for x in v.ravel().tolist()]}
                                   for k, v in blobs.items()}})
    (OUT / "p97_osc.expected.json").write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    print(OUT, len(msgs), "messages", len(raw), "bytes")


if __name__ == "__main__":
    main()
