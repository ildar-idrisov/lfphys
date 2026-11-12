"""What a packet / box placed far outside p02's window becomes (accepted without a word)."""
import sys, json
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness
h = Harness("p02_quantum", params={"dim": "2d", "n2": "128"})
h.runner.handle({"cmd": "scene", "args": {"op": "add", "type": "packet", "values": {"x": 1e6}}})
h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)
fr = [m for m, _ in h.msgs if m.get("type") == "frame"][-1]
print(json.dumps({"now": fr.get("now"), "errors": [m["text"][:200] for m, _ in h.msgs if m.get("type") in ("error", "notice")]}, ensure_ascii=False, default=str)[:1500])
