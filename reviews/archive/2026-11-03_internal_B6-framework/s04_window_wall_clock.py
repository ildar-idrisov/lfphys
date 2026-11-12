# Review B6-framework, script s04: the record's window counts wall time, pauses and suspensions included.
# The real lfviz.runs.Run ingests a synthetic playground record (header, frames, the worker's segment markers) with a
# controlled wall clock (lfviz.runs.time.time patched):
#   9 minutes of play (a segment per minute, as checkpoint_every = 60 s), a pause (the pause's checkpoint opens a
#   segment), 20 minutes away (no segments while paused), then play again: at the first periodic checkpoint 60 s later
#   the window (10 min) drops everything computed before the pause except the newest two segments, although only one
#   minute was computed since.
# Usage: see s01; python3 /out/s04_window_wall_clock.py
import tempfile
from pathlib import Path

from lfviz import protocol, runs

clock = [1_000_000.0]
runs.time.time = lambda: clock[0]


class Mgr:  # what Run needs of its manager here
    pass


d = Path(tempfile.mkdtemp())
meta = {"id": "x", "viz": "p99_toy", "restorable": True, "kind": "playground",
        "buffer": {**runs.BUFFER_DEFAULT, "recording": False, "protected": [],
                   "segs": [{"k": 0, "wall0": clock[0], "t0": 0.0, "world": 1}]}}
run = runs.Run(Mgr(), "x", "p99_toy", meta, d)
run.file = open(run.stream_path, "wb")
run.file.write(protocol.MAGIC)
run.file.flush()
t = [0.0]


def ingest(m):
    run._ingest(protocol.encode(m))


def segment():
    ingest({"type": "record_segment", "t": t[0], "world": 1})
    ingest({"type": "scene", "t": t[0], "rev": 0, "objects": []})
    ingest({"type": "checkpoint", "t": t[0], "world": 1, "file": "w1-1.pkl"})


def play(minutes):
    for _ in range(int(minutes * 60 * 20)):  # 20 frames per second
        clock[0] += 0.05
        t[0] += 0.05
        ingest({"type": "frame", "t": t[0]})
        if int(round(clock[0] * 20)) % (60 * 20) == 0:  # a periodic checkpoint every 60 s of play
            segment()


ingest({"type": "header", "t": 0.0, "world": 1})
play(9)
segment()  # the pause: Runner.handle("pause") writes a checkpoint (more than 10 s since the last one)
print("after 9 min of play and a pause: segments", [sg["k"] for sg in meta["buffer"]["segs"]],
      " record from world time", meta["buffer"]["segs"][0]["t0"])
clock[0] += 20 * 60  # twenty minutes away; the world is paused, nothing is computed
play(1.01)
print("after 1 more minute of play:      segments", [sg["k"] for sg in meta["buffer"]["segs"]],
      " record from world time", round(meta["buffer"]["segs"][0]["t0"], 2), "of", round(t[0], 2),
      " trimmed:", meta["buffer"]["trimmed"])
print("world time computed in the last 10 minutes of play: 10 min; kept in the window:",
      round(t[0] - meta["buffer"]["segs"][0]["t0"], 1), "s")
