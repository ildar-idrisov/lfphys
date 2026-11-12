import sys
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
import numpy as np
from tests.harness import Harness
h = Harness("p01_gravity", "kerr_orbits")
m = h.sim.mode
g = m.geo
rows = [i for i, s in enumerate(g.status()) if s == "active"]
V = m._vel(rows)                       # per G M/c^3
X0 = g.cartesian()[rows]
dt = 1e-4
g.advance(g.t + dt)
X1 = g.cartesian()[rows]
fd = (X1 - X0) / dt
print("max rel diff velocity vs finite difference:", float(np.max(np.linalg.norm(fd - V, axis=1) / np.linalg.norm(V, axis=1))))
# PN body velocities
h2 = Harness("p01_gravity", "pn_inspiral")
pm = h2.sim.mode
b = pm.bin
x, v = b["st"]["x"], b["st"]["v"]
Y0, W, a = pm._body_states(x, v)
import lfphys.core.gravity.pn_binary as PN
res = PN.integrate(b["st"], b["st"]["t"] + 1e-4, b["nu"], b["orders"], n_out=3)
x1, v1 = res["end"]["x"], res["end"]["v"]
Y1 = np.stack(PN.body_positions(x1, v1, b["nu"]))
print("PN body velocity rel diff:", float(np.max(np.linalg.norm((Y1 - Y0) / 1e-4 - W, axis=1) / np.linalg.norm(W, axis=1))))
