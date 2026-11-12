"""Objects at the edge of the world's region (U-place): what the owner sees when he puts an object on the border."""
import sys, json, signal
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness
CASES = [
  ("p02_quantum", {"dim": "2d", "n2": "128"}, "packet", {"x": 35.0}),
  ("p02_quantum", {"dim": "2d", "n2": "128"}, "packet", {"x": 39.0}),
  ("p02_quantum", {"dim": "2d", "n2": "128"}, "box", {"x": 40.0, "sx": 4.0, "sy": 4.0}),
  ("p02_quantum", {"dim": "2d", "n2": "128"}, "detector", {"x": 39.0, "sx": 4.0}),
  ("p03_molecules", {"dim": "2d"}, "atom", {"x": 12.0, "y": 6.0}),
  ("p03_molecules", {"dim": "2d"}, "atom", {"x": 0.0, "y": 0.0}),
  ("p03_molecules", {"dim": "2d", "boundary": "walls"}, "atom", {"x": 12.0, "y": 6.0}),
  ("p03_molecules", {"dim": "2d", "boundary": "walls"}, "atom", {"x": 0.01, "y": 6.0}),
  ("p04_fluids", {"nx": "256"}, "disk", {"x": 2.2, "y": 0.2, "radius": 0.05}),
  ("p04_fluids", {"nx": "256"}, "disk", {"x": 0.2, "y": 0.0, "radius": 0.05}),
  ("p04_fluids", {"nx": "256"}, "probe", {"x": 2.2, "y": 0.41}),
  ("p01_gravity", {"laws": "kerr"}, "body", {"r": 1000.0}),
  ("p01_gravity", {"laws": "kerr"}, "body", {"r": 1.5}),
]
for viz, params, typ, vals in CASES:
    h = Harness(viz, params=params)
    n0 = len(h.msgs)
    h.runner.handle({"cmd": "scene", "args": {"op": "add", "type": typ, "values": vals}})
    errs = [m["text"][:200] for m, _ in h.msgs[n0:] if m.get("type") == "error"]
    adv = "ok"
    try:
        for _ in range(3):
            h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)
    except Exception as e:
        adv = f"{type(e).__name__}: {str(e)[:120]}"
    fr = [m for m, _ in h.msgs if m.get("type") == "frame"]
    now = fr[-1].get("now", {}) if fr else {}
    print(json.dumps({"viz": viz, "type": typ, "values": vals, "refused": errs, "objects": len(h.sim.objects), "advance": adv,
                      "now": {k: v for k, v in list(now.items())[:1]}}, ensure_ascii=False, default=str)[:600], flush=True)
