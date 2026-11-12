# Q8 after the leak bound: the same moments and drags as a5, through p02 (what the owner gets)
import numpy as np
from harness import Harness
h = Harness("p02_quantum", "double_slit")
for mult in (6, 8, 10):
    t_end = mult * h.sim.default_speed
    while h.sim.t < t_end:
        h.run_to(min(t_end, h.sim.t + 0.5 * h.sim.default_speed)); h.runner._frame(0.0)
    o = h.sim.qs.observables(1); res = []
    for d in (1.0, 3.0, 5.0):
        for sh in ((-d, 0), (d, 0), (0, d), (0, -d)):
            leak = h.sim._far_leak(h.sim.qs.wave(1), np.array(sh), float(np.linalg.norm(o["k"])), 1.0)
            res.append(("ok" if leak <= 1e-6 else "REFUSED") + f"{sh}: leak {leak:.1e}")
    print(f"t = {h.sim.t:.3e} s: " + "; ".join(res))
