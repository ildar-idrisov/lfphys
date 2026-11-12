# Review B6-framework, script s03: a value the schema accepts makes p01's frame() raise; the runner's loop then
# repeats the failing frame without pause (dirty stays set, nothing sleeps when not playing) and floods the record.
# p01's positions have no bounds (Param "x" float, no min/max): x = 1.7e308 is finite, but the scene box 1.15 * |x|
# overflows to inf and 2 ** ceil(log2(inf)) raises OverflowError in NewtonMode.frame().
# The real Runner.run loop is driven in a thread for 2 s of wall time; every emitted message is counted.
# Usage: see s01; python3 /out/s03_frame_error_flood.py
import queue
import threading
import time

from lfviz import protocol, registry
from lfviz.sim import Runner

viz = registry.load("p01_gravity")
p, errs = viz["schema"].resolve("sun_earth", {})
counts, nbytes = {}, [0]


def emit(meta, blobs=None):
    counts[meta["type"]] = counts.get(meta["type"], 0) + 1
    nbytes[0] += len(protocol.encode(meta, blobs)) + 4


q = queue.Queue()
sim = viz["simulation"](p, 3, emit)
run = Runner(sim, emit, q)
th = threading.Thread(target=run.run, daemon=True)
th.start()
time.sleep(0.5)
print("before the change:", dict(counts))
counts.clear(); nbytes[0] = 0
q.put({"cmd": "scene", "args": {"op": "set", "id": "o2", "values": {"x": 1.7e308}}})  # what the inspector's field sends
time.sleep(2.0)
c = dict(counts); b = nbytes[0]
q.put({"cmd": "stop", "args": {}})
th.join(10)
print("2 s after the change (paused world, nobody plays):", c)
print(f"bytes emitted into the record in those 2 s: {b / 1e6:.1f} MB ({b / 2e6:.1f} MB/s)")
