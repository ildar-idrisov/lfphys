# Review B6-framework, script s09: the size and the time of a p02 checkpoint, which a playground writes every 60 s of
# play (PlaygroundSimulation.checkpoint_every, half the demonstrations' 120 s) to cut its record into segments.
# The pickling runs in the world's loop (lfviz.checkpoint.dumps), the file is written in the background.
# Usage: see s01; python3 /out/s09_checkpoint_size_3d.py
import queue
import time

from lfviz import checkpoint as C, registry
from lfviz.sim import Runner

viz = registry.load("p02_quantum")
for label, values in [("2-D 256², the double slit (1 electron)", {"n2": "256"}),
                      ("3-D 64³, the ball (1 electron)", {"n3": "64"}),
                      ("3-D 128³, the ball (1 electron)", {"n3": "128"})]:
    preset = "double_slit" if "2-D" in label else "ball_3d"
    p, errs = viz["schema"].resolve(preset, values)
    assert not errs, errs
    sim = viz["simulation"](p, 3, lambda m, b=None: None)
    run = Runner(sim, lambda m, b=None: None, queue.Queue())
    run._start_world()
    t0 = time.monotonic()
    data = C.dumps(run.checkpoint_state(), run.emit)
    print(f"{label}: checkpoint {len(data) / 1e6:.1f} MB, pickled in {time.monotonic() - t0:.2f} s "
          f"(every 60 s of play: {len(data) / 1e6 / 60:.2f} MB/s written)")
    del sim, run, data
