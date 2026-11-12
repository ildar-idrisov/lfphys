"""Q: after a localization jump the wrapper re-seeds a particle's Bohm points (_seed_bohm). Does it keep the points
already registered by the absorbers? The engine keeps the absorbed probabilities across a jump (a jump acts on the
in-flight branch only), so the ensemble should keep its hits and re-draw only the points in flight
(n - hits of them, from |psi|^2 / N).

The double-slit preset, 300 Bohm points, with an environment everywhere (lambda = 20/ps, a = 2 nm) added before the
packet. _seed_bohm is wrapped to print, at each re-seeding, the hits and the absorbed probability before and after."""
import copy, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

orig = P.Simulation._seed_bohm


def traced(self, obj):
    B = self.bohm.get(obj["id"])
    kind, pid = self.ref[obj["id"]]
    before = None if B is None else (len(B["hits"]), len(B["X"]))
    A = sum(self.qs.absorbed(pid).values()) if pid in self.qs.particles else None
    orig(self, obj)
    B = self.bohm.get(obj["id"])
    if before is not None:
        print(f"t = {self.qs.t:6.3f}: re-seeded; absorbed probability {A:.4f}, norm in flight {self.qs.norm(pid):.4f}; "
              f"hits {before[0]} -> {len(B['hits'])}, points in flight {before[1]} -> {len(B['X'])}")


P.Simulation._seed_bohm = traced
pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
objs = pr["scene"]["objects"]
for o in objs:
    if o["type"] == "packet":
        o["values"]["bohm"] = 300
objs.insert(0, {"type": "env", "label": "Среда", "values": {"rate": 20.0, "length": 2.0, "region": "all"}})
h = Harness("p02_quantum", None, pr, seed=4)
sim, qs = h.sim, h.sim.qs
t = 0.0
while qs.t < 20.0:
    t += sim.max_step()
    h.run_to(t)
print("jumps:", [round(tj, 3) for tj, _ in qs.particles[1].jumps])
