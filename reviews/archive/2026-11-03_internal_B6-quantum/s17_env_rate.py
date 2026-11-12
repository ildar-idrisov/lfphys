"""Q: the wrapper keeps lambda dt <= 0.05 in _tune_dt (dt = min(dt, 0.05/lambda)), but on_add / on_set give the new
environment to the scene before _tune runs, and the scene refuses lambda dt > 0.05 — so a strong environment is
refused although the wrapper would have reduced the step. The tunnel preset (dt = 2^-7 units = 0.0675 fs);
environments of 10, 100 and 1000 per ps (lambda dt = 6.7e-4, 6.7e-3, 0.067)."""
import sys
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

for rate in (10.0, 100.0, 1000.0):
    h = Harness("p02_quantum", "tunnel")
    lam = rate * 1e12 * P.TU
    h.cmd("scene", op="add", type="env", values={"rate": rate, "length": 2.0, "region": "all"})
    print(f"rate {rate:6.0f}/ps: lambda dt = {lam * h.sim.qs.dt:.3g}; errors: {h.errors()}; dt now {h.sim.qs.dt}")
h = Harness("p02_quantum", "tunnel")
h.cmd("scene", op="add", type="env", values={"rate": 10.0, "length": 2.0, "region": "all"})
eid = [o for o in h.sim.objects if h.sim.objects[o]["type"] == "env"][0]
h.cmd("scene", op="set", id=eid, values={"rate": 1000.0})
print(f"set rate 10 -> 1000/ps: errors {h.errors()}; rate in the scene now "
      f"{[ob.rate / (1e12 * P.TU) for ob in h.sim.qs.objects.values() if type(ob).__name__ == 'Localization']}")
