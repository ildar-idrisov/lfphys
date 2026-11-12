# Review B6-framework, script s10: is a segment of a playground's record drawable on its own (runs.py: "each starting
# where the worker writes a checkpoint (its record_segment marker, then the scene and what the view needs, then the
# checkpoint), so that every segment can be shown from its first message")?
# A world runs, writes two checkpoints (as the run loop does at 60 s of play); a viewer who joins after the window
# dropped the first segment gets the world's header (kept apart) and the record from the second segment's marker on.
# Listed: what the full record holds that this viewer never gets (message types and ids), and the latest approximations
# and box each viewer ends with.
# Usage: see s01; python3 /out/s10_segment_self_contained.py
import queue
import tempfile
from pathlib import Path

import numpy as np

from lfviz import registry
from lfviz.sim import Runner

viz = registry.load("p01_gravity")


def session(preset):
    msgs = []
    p, errs = viz["schema"].resolve(preset, {})
    assert not errs, errs
    sim = viz["simulation"](p, 3, lambda m, b=None: msgs.append((m, b)))
    run = Runner(sim, lambda m, b=None: msgs.append((m, b)), queue.Queue())
    run.ckpt_dir = Path(tempfile.mkdtemp())
    run._start_world()
    rng = np.random.default_rng(1)
    for k in range(3):
        for _ in range(100):
            run._advance(run.sim.t + run.speed / 20 * rng.uniform(0.6, 1.4))
            run._frame(0.0)
        if k < 2:
            run.ckpt_dirty = True
            run.checkpoint("periodic")
            run.ckpt_writer.wait()
    return msgs


def key(m):
    return f"{m['type']}:{m.get('id', '')}" if m["type"] in ("mesh", "lines") else m["type"]


def latest(msgs, pred, field):
    v = None
    for m, _ in msgs:
        if pred(m):
            v = m.get(field)
    return v


for preset in ("kerr_orbits", "inner", "hole_stars"):
    msgs = session(preset)
    marks = [i for i, (m, _) in enumerate(msgs) if m["type"] == "record_segment"]
    full = msgs
    joined = [msgs[0]] + msgs[marks[1]:]  # the header kept apart, then the kept window (from the 2nd segment)
    kinds_full = {key(m) for m, _ in full if m["type"] != "frame"}
    kinds_join = {key(m) for m, _ in joined if m["type"] != "frame"}
    print(f"=== p01 preset {preset} ===")
    print("  never reaches a viewer joining after the first segment left the window:", sorted(kinds_full - kinds_join))
    ap = lambda m: isinstance(m.get("approximations"), list)  # noqa: E731
    print("  approximations: full record", latest(full, ap, "approximations"))
    print("                  joined view ", latest(joined, ap, "approximations"))
    bx = lambda m: m["type"] == "box" or m["type"] == "header"  # noqa: E731
    box_full = latest(full, lambda m: m["type"] == "box", "box") or msgs[0][0]["scene3d"]["box"]
    box_join = latest(joined, lambda m: m["type"] == "box", "box") or msgs[0][0]["scene3d"]["box"]
    print("  scene box:      full record", box_full, " joined view", box_join)
    fr = [m for m, b in msgs if m["type"] == "frame"][-1]
    pos = [b for m, b in msgs if m["type"] == "frame"][-1]["pos"].reshape(-1, 3)
    print("  largest |coordinate| of a body in the last frame:", float(np.max(np.abs(pos))) if len(pos) else None)
