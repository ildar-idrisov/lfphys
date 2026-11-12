# Reviewer script (B6 gravity): a PN binary that reached its stop distance, saved as a scene file and loaded again
# (p01 PNMode.object_state / _start: the start is refused when |x| <= r_stop).
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402


def run(h, t_end, n=200):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


params = {"laws": "pn", "m_total": 20.0, "scene": {"format": "lfscene", "version": 1, "objects": [
    {"type": "binary", "values": {"q": 1.0, "r0": 14.0, "r_stop": 12.0}}]}}
h = Harness("p01_gravity", None, params)
run(h, 6000 * h.sim.mode.T, 200)
b = h.sim.mode.bin
print(f"status {b['status']}, r = {float(np.linalg.norm(b['st']['x'])):.15g}, events "
      f"{[e['text'][:40] for e in h.of('event') if e.get('kind') == 'merger']}")
h.cmd("scene", op="export")
sc = h.of("scene_export")[-1]["scene"]
try:
    h2 = Harness("p01_gravity", None, {**sc["laws"], "scene": sc})
    print("reloaded:", h2.sim.mode.bin and h2.sim.mode.bin["status"])
except Exception as exc:  # noqa: BLE001
    print("reloading the scene FAILED:", type(exc).__name__, exc)
