# Review B6-framework, script s02: what a playground's rekey() does at every checkpoint (p01_gravity, Newton).
#  (a) the trail message rekey emits carries reset=True with only the points since the last trail message: the view's
#      onTrail (p01_gravity/web/view.js) clears every trail on reset, so every viewer's trails restart at every
#      checkpoint (every 60 s of play, at a pause after 10 s, at a suspension). The view logic is mirrored here.
#  (b) rekey changes the world's state (trail_new keeps one point instead of none): a world rebuilt by replay (no rekey
#      is repeated: the script holds only frames and commands) emits different trail messages afterwards than the
#      original. (RULES §3: a world restored by replay emits the original's messages byte for byte.)
# Usage: see s01 (PYTHONPATH as there); python3 /out/s02_rekey_trails.py
import queue
import tempfile
from pathlib import Path

import numpy as np

from lfviz import protocol, registry
from lfviz.sim import Runner

WALL = ("cpu_ms", "speed_actual", "lag")


def world(msgs, preset="sun_earth", seed=3, muted=(False,)):
    viz = registry.load("p01_gravity")
    p, errs = viz["schema"].resolve(preset, {})
    assert not errs, errs

    def emit(meta, blobs=None):
        if not muted[0]:
            msgs.append((meta, blobs))
    sim = viz["simulation"](p, seed, emit)
    return sim, Runner(sim, emit, queue.Queue())


def view_trails(msgs):
    """The view's trails after feeding these messages (p01_gravity/web/view.js onTrail): id -> number of points."""
    trails = {}
    for m, b in msgs:
        if m.get("type") != "trail":
            continue
        if m.get("reset"):
            trails = {}
        for i, (tid, n) in enumerate(zip(m["ids"], m["counts"])):
            trails[tid] = trails.get(tid, 0) + n
    return trails


def frames(run, n, rng):
    for _ in range(n):
        run._advance(run.sim.t + run.sim.default_speed / 20 * rng.uniform(0.6, 1.4))
        run._frame(0.0)


def bytes_of(msgs):
    return [protocol.encode({k: v for k, v in m.items() if k not in WALL}, b) for m, b in msgs]


print("=== (a) the view's trails before and after a checkpoint ===")
msgs = []
sim, run = world(msgs)
run._start_world()
frames(run, 1200, np.random.default_rng(1))  # one minute at 20 frames per second
print("trail points held by the view after 1200 frames:", view_trails(msgs))
td = tempfile.mkdtemp()
run.ckpt_dir = Path(td)
run.checkpoint("periodic")  # what the run loop does every PlaygroundSimulation.checkpoint_every = 60 s of play
run.ckpt_writer.wait()
rk = [m for m, _ in msgs if m.get("type") == "trail"][-1]
print("rekey's trail message: reset =", rk.get("reset"), " counts =", rk["counts"])
print("trail points held by the view right after the checkpoint:", view_trails(msgs))
frames(run, 30, np.random.default_rng(2))
print("... and 30 frames later:", view_trails(msgs))
types = [m["type"] for m, _ in msgs]
i = types.index("record_segment")
print("messages at the checkpoint:", types[i:i + 4])

print("=== (b) a world rebuilt by replay after a rekey continues differently ===")
msgs = []
sim, run = world(msgs)
run._start_world()
rng = np.random.default_rng(5)
frames(run, 40, rng)
run.handle({"cmd": "scene", "args": {"op": "add", "type": "test", "values": {"x": 1.5}}})
frames(run, 40, rng)
run.ckpt_dir = Path(tempfile.mkdtemp())
run.checkpoint("suspend")  # the suspension's checkpoint is the record's last message
run.ckpt_writer.wait()
script = []
for m, _ in msgs:
    if m["type"] == "frame":
        script.append({"frame": m["t"]})
    elif m["type"] == "command":
        script.append({"t": m["t"], "cmd": m["cmd"], "args": m["args"]})
t_end = sim.t
n0 = len(msgs)
tail_rng = np.random.default_rng(9)
steps = [sim.default_speed / 20 * tail_rng.uniform(0.6, 1.4) for _ in range(12)]
for dt in steps:  # the original goes on
    run._advance(run.sim.t + dt)
    run._frame(0.0)
orig = msgs[n0:]
m2, muted = [], [False]
_, run2 = world(m2, muted=muted)
run2.restore(1, script, t_end, lambda on: muted.__setitem__(0, on))  # Runner.restore, as the worker does without a checkpoint
for dt in steps:
    run2._advance(run2.sim.t + dt)
    run2._frame(0.0)
a, b = bytes_of(orig), bytes_of(m2)
print("messages after the end of the record: original", len(a), " replayed", len(b))
for k, (x, y) in enumerate(zip(a, b)):
    if x != y:
        mx, my = protocol.decode(x)[0], protocol.decode(y)[0]
        print(f"first difference at message {k}: type {mx['type']}; original counts {mx.get('counts')}, "
              f"replayed counts {my.get('counts')}")
        break
else:
    print("identical")
