"""The first-law residual of p03's piston preset (r15: +25 eps after the first compression, the check's note says "the
Verlet scheme's error, O(dt^2)") against the time step: dt = 10, 5, 2.5 fs, three seeds each, 20 ps (the first
stroke). O(dt^2) would divide it by 4 per halving. Also the same gas in NVE without the piston (specular walls, the
thermal floor made specular): the integrator's own error at the same dt (energy drift over 20 ps)."""
import common  # noqa: F401
import copy

import numpy as np
from harness import Harness

from p03_molecules.viz import PS, SCHEMA

base = SCHEMA.presets["piston"]["params"]
for dt in (10.0, 5.0, 2.5):
    res, nve = [], []
    for seed in (1, 2, 3):
        p = copy.deepcopy(base)
        p["dt_fs"] = dt
        h = Harness("p03_molecules", None, p, seed=seed)
        md = h.sim.md
        md.advance(20.0 / PS)
        res.append(md.energy_balance()["residual"])
        q = copy.deepcopy(p)
        q["scene"]["objects"] = [o for o in q["scene"]["objects"] if o["type"] == "gas"]
        h2 = Harness("p03_molecules", None, q, seed=seed)
        m2 = h2.sim.md
        E0 = m2.energy()
        m2.advance(20.0 / PS)
        nve.append(m2.energy() - E0)
    print(f"dt = {dt:4.1f} fs: piston-preset residuals {np.round(res, 3).tolist()} (mean |.| {np.mean(np.abs(res)):.3f}); "
          f"NVE gas without piston: energy change {np.round(nve, 4).tolist()}")
