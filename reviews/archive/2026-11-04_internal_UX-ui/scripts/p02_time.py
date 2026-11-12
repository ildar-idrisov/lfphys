"""Wall time of p02 scene changes in the double-slit preset (no profiler), with the host's load average."""
import sys, time, os, json
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness
h = Harness("p02_quantum", preset="double_slit")
for _ in range(2):
    h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)
pid = next(k for k, o in h.sim.objects.items() if o["type"] == "packet")
out = []
for name, args in [("set packet x", {"op": "set", "id": pid, "values": {"x": -19.0}}),
                   ("add box (x=20, y=20)", {"op": "add", "type": "box", "values": {"x": 20.0, "y": 20.0}}),
                   ("set packet wavelength", {"op": "set", "id": pid, "values": {"wavelength": 2.2}})]:
    la = os.getloadavg()[0]; t0 = time.time()
    h.runner.handle({"cmd": "scene", "args": args})
    out.append({"change": name, "s": round(time.time() - t0, 2), "load1_before": round(la, 1), "load1_after": round(os.getloadavg()[0], 1),
                "errors": [m["text"][:100] for m, _ in h.msgs[-2:] if m.get("type") == "error"]})
    print(json.dumps(out[-1], ensure_ascii=False), flush=True)
