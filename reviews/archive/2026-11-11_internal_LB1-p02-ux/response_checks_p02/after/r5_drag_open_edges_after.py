# Response to Q8: the reviewer's a5 grid of drags with the decision the scene now takes with open edges — only what a
# move carries across a face INTO the window beyond the far side's absorbing layer counts (wrap_fraction with the margin
# of the layers' width); what lands in that layer is absorbed there (reported as far_layer). Same moments as a5.
import numpy as np
from harness import Harness
from lfphys.core.quantum import schrodinger_nd as S
h = Harness("p02_quantum", "double_slit")
pid = 1
for mult in (2, 4, 6, 8, 10):
    t_end = mult * h.sim.default_speed
    while h.sim.t < t_end:
        h.run_to(min(t_end, h.sim.t + 0.5 * h.sim.default_speed)); h.runner._frame(0.0)
    qs = h.sim.qs; psi = qs.wave(pid); g = qs.grid; w = qs.edges.width
    res = []
    for d in (1.0, 3.0, 5.0):
        for sh in ((-d, 0), (d, 0), (0, d), (0, -d)):
            into = S.wrap_fraction(psi, g, np.array(sh), w); far = S.wrap_fraction(psi, g, np.array(sh)) - into
            res.append(("ok" if into <= 1e-6 else "REFUSED") + f"{sh}: into {into:.1e}, far layer {far:.1e}")
    print(f"t = {h.sim.t:.3e} s (norm {qs.norm(pid):.4f}):\n   " + "; ".join(res))
