"""Why a p02 inspector edit takes ~9 s on the CPU: cProfile of one `set` (packet x) in the double_slit preset."""
import sys, time, cProfile, pstats, io
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness
h = Harness("p02_quantum", preset="double_slit")
for _ in range(2):
    h.runner._advance(h.sim.t + h.runner.speed / 20); h.runner._frame(0)
pid = next(k for k, o in h.sim.objects.items() if o["type"] == "packet")
for name, args in [("set packet x", {"op": "set", "id": pid, "values": {"x": -19.0}}),
                   ("add box", {"op": "add", "type": "box", "values": {"x": 20.0, "y": 20.0}}),
                   ("set detector edge", {"op": "set", "id": next(k for k, o in h.sim.objects.items() if o["type"] == "detector"), "values": {"edge": 4.0}})]:
    pr = cProfile.Profile(); t0 = time.time(); pr.enable()
    h.runner.handle({"cmd": "scene", "args": args})
    pr.disable(); dt = time.time() - t0
    s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(14)
    print(f"=== {name}: {dt:.2f} s; errors: {[m['text'][:120] for m, _ in h.msgs[-3:] if m.get('type') == 'error']}")
    print("\n".join(l for l in s.getvalue().splitlines() if "/lf" in l or "cumtime" in l)[:2500])
