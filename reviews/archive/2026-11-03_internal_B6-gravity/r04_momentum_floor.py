# Reviewer script (B6 gravity): the playground's momentum check (p01 NewtonMode.checks): |P - P_ref| <= 1e-12 sum|m v|,
# a fixed tolerance that does not grow with the number of steps. Measured: the round-off drift of the momentum of the
# preset "inner" (Hermite, eta = 0.02) against the number of steps, and when it would cross 1e-12.
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from lfphys.core.gravity import nbody as NB  # noqa: E402

for preset in ("inner", "hole_stars"):
    h = Harness("p01_gravity", preset)
    nb0 = h.sim.mode.nb
    nb = NB.NBody.from_state_dict(nb0.state_dict())
    P0 = nb.momentum().copy()
    t0 = time.time()
    print(f"preset {preset}: N = {nb.n}")
    marks = [1000, 3000, 10000, 30000, 100000]
    done = 0
    for m in marks:
        nb.step(m - done)
        done = m
        P = nb.momentum()
        pscale = float(np.sum(nb.masses()[:, None] * np.abs(nb.velocities())))
        rel = float(np.linalg.norm(P - P0)) / pscale
        print(f"  steps {m:7d}  t = {nb.t:10.4f} yr  |dP|/sum|m v| = {rel:.3e}  (fails the playground's 1e-12: "
              f"{rel > 1e-12})  wall {time.time() - t0:.0f} s", flush=True)
        if time.time() - t0 > 200:
            break
