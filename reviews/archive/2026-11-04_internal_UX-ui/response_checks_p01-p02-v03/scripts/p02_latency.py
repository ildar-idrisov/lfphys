"""Wall time of typical p02 scene edits (U3/P30): before/after. Usage: p02_latency.py <engine root> <label>"""
import sys, time, os, json
root = sys.argv[1]
label = sys.argv[2]
sys.path[:0] = [f"{root}/visualizations", f"{root}/visualizations/server", f"{root}/lfphys", root]
from tests.harness import Harness

def warm(h, n=2):
    for _ in range(n):
        h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)

def pid_of(h, typ):
    return next(k for k, o in h.sim.objects.items() if o["type"] == typ)

def timed(h, name, args, preset):
    la = os.getloadavg()[0]; n0 = len(h.msgs); t0 = time.time()
    h.runner.handle({"cmd": "scene", "args": args})
    dt = time.time() - t0
    errs = [m["text"][:160] for m, _ in h.msgs[n0:] if m.get("type") == "error"]
    rec = {"label": label, "preset": preset, "change": name, "s": round(dt, 3), "load1": round(la, 1), "errors": errs}
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    warm(h, 1)
    return rec

cases = {
    "double_slit": lambda h: [
        ("set packet x -19", {"op": "set", "id": pid_of(h, "packet"), "values": {"x": -19.0}}),
        ("add box far (20,20)", {"op": "add", "type": "box", "values": {"x": 20.0, "y": 20.0}}),
        ("set packet wavelength 2.2", {"op": "set", "id": pid_of(h, "packet"), "values": {"wavelength": 2.2}}),
        ("add detector (20,-20)", {"op": "add", "type": "detector", "values": {"x": 20.0, "y": -20.0}}),
        ("set screen edge 4", {"op": "set", "id": pid_of(h, "detector"), "values": {"edge": 4.0}}),
        ("add marker (0,5)", {"op": "add", "type": "marker", "values": {"x": 2.0, "y": 5.0}}),
        ("add plane at 20", {"op": "add", "type": "plane", "values": {"position": 20.0}}),
        ("rename packet", {"op": "label", "id": pid_of(h, "packet"), "label": "e"}),
    ],
    "tunnel": lambda h: [
        ("set barrier V 0.6", {"op": "set", "id": pid_of(h, "box"), "values": {"V": 0.6}}),
        ("set packet x -18", {"op": "set", "id": pid_of(h, "packet"), "values": {"x": -18.0}}),
    ],
    "ball_3d": lambda h: [
        ("set ball V 1.2", {"op": "set", "id": pid_of(h, "ball"), "values": {"V": 1.2}}),
        ("add detector 3d", {"op": "add", "type": "detector", "values": {"x": 12.0, "sx": 3.0}}),
    ],
}
which = sys.argv[3].split(",") if len(sys.argv) > 3 else list(cases)
for preset in which:
    h = Harness("p02_quantum", preset=preset)
    warm(h)
    for name, args in cases[preset](h):
        timed(h, name, args, preset)
