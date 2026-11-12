"""Q: the grid's resolution is checked only for a packet's free wavevector (|k| + 6 sigma_k <= pi/d); inside a well the
local wavenumber is sqrt(k^2 + 2 m |V|). The tunnel preset's electron (lambda = 2 nm, d = 0.3125 nm: k d = 0.98) with a
well of -3 eV (k_local d = 3.0, close to pi) instead of the barrier: the running grid check (info) at the moment the
packet is in the well, and the probability transmitted past the well at t = 14 units against the same scene on a
grid twice as fine (512 points over the same 80 nm)."""
import copy, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core import backend
from p02_quantum import viz as P

out = {}
for n in ("256", "512"):
    pr = copy.deepcopy(P.SCHEMA.presets["tunnel"]["params"])
    pr["n2"] = n
    for o in pr["scene"]["objects"]:
        if o["type"] == "box":
            o["values"].update({"sx": 4.0, "V": -3.0, "edge": 1.0})
        if o["type"] == "packet":
            o["values"]["bohm"] = 0
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    tails = []
    for T in (6.4, 14.0):
        t = sim.t
        while qs.t < T - qs.dt:
            t += sim.max_step()
            h.run_to(min(t, T * P.TU))
        tails.append(qs.checks()[1]["spectral_tail"])
    g = qs.grid
    X = g.axes[0]
    acc = backend.to_numpy(qs.particles[1].acc)
    beyond = float(np.sum((qs.density(1) + acc)[X > 4.0, :])) * g.dV
    out[n] = beyond
    print(f"{n}^2 (d = {g.d[0]}), dt {qs.dt}: spectral tail with the packet in the well {tails[0]:.2e}, at the end "
          f"{tails[1]:.2e}; probability past the well at t = {qs.t:.2f}: {beyond:.5f}")
print(f"difference 256 vs 512: {out['256'] - out['512']:+.2e}")
