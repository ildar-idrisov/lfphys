"""v03: wall time of a world's build and of a live change, one process (OMP 2 threads, as the server's worker), and
the checks after the run. Cases: the scenario «ступенька» chosen from the defaults (start form and live), the energy
at its minimum, the barrier's width at its maximum with the sharpest edge."""
import sys, time, queue
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry
from lfviz.sim import Runner
registry.ensure_path()
viz = registry.load("v03_quantum_1d")
sch = viz["schema"]


def build(values):
    msgs = []
    p, e = sch.resolve(None, values)
    t0 = time.time()
    try:
        sim = viz["simulation"](p, 1, lambda m, b=None: msgs.append(m))
    except Exception as ex:
        return None, msgs, time.time() - t0, f"{type(ex).__name__}: {ex}"
    r = Runner(sim, lambda m, b=None: msgs.append(m), queue.Queue())
    r._start_world()
    return r, msgs, time.time() - t0, None


def failed(msgs):
    last = {}
    for m in msgs:
        if m.get("type") == "check":
            last[m["id"]] = m
    return [(c["id"], c["label"][:50], c.get("value"), c.get("ref")) for c in last.values() if c.get("ok") is False]


for name, values in [("defaults", {}), ("scenario=step (start form)", {"scenario": "step"}),
                     ("energy=min", {"energy": 0.05}), ("width=max", {"width": 10.0}),
                     ("width=max, edge=min", {"width": 10.0, "edge": 0.02})]:
    r, msgs, dt, err = build(values)
    print(f"build {name:<30} {dt:7.1f} s  {err or ''}  failed checks: {failed(msgs)}", flush=True)
for name, values in [("scenario=step (live)", {"scenario": "step"}), ("energy=min (live)", {"energy": 0.05}),
                     ("V0=max (live)", {"V0": 10.0})]:
    r, msgs, dt, err = build({})
    n0 = len(msgs)
    t0 = time.time()
    r.handle({"cmd": "set", "args": {"values": values}})
    dt = time.time() - t0
    errs = [m.get("text") for m in msgs[n0:] if m.get("type") == "error"]
    print(f"live  {name:<30} {dt:7.1f} s  errors: {errs}  failed checks: {failed(msgs[n0:])}", flush=True)
