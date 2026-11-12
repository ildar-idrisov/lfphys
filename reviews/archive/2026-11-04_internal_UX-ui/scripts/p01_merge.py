"""p01 Newton: what a palette click with defaults does in the "inner" preset (objects after a few frames, events)."""
import sys, json
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness
for typ in ("star", "planet", "hole", "test"):
    h = Harness("p01_gravity", preset="inner")
    for _ in range(2):
        h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)
    n0 = len(h.msgs)
    h.runner.handle({"cmd": "scene", "args": {"op": "add", "type": typ, "values": {}}})
    after_add = [o["label"] for o in h.sim.objects.values()]
    for _ in range(20):
        h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)
    evs = [m.get("text") for m, _ in h.msgs[n0:] if m.get("type") in ("event", "error", "notice")]
    print(json.dumps({"type": typ, "objects_after_add": len(after_add), "objects_after_1s": len(h.sim.objects),
                      "labels_after": [o["label"] for o in h.sim.objects.values()], "events": evs}, ensure_ascii=False))
# empty world, star then star at x=0.001 au (inside the first star's radius 0.00465 au)
h = Harness("p01_gravity", params={"laws": "newton"})
h.runner.handle({"cmd": "scene", "args": {"op": "add", "type": "star", "values": {}}})
h.runner.handle({"cmd": "scene", "args": {"op": "add", "type": "star", "values": {"x": 0.001}}})
n_after = len(h.sim.objects)
h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)
print(json.dumps({"case": "two stars 0.001 au apart", "after_add": n_after, "after_frame": len(h.sim.objects),
                  "events": [m.get("text") for m, _ in h.msgs if m.get("type") in ("event", "error")]}, ensure_ascii=False))
