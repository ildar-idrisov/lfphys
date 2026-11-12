# Response to B4-7: v12's Bohm first-arrival law (the running maximum of the flux's integral, now by the trapezoid rule
# from J(0) = 0) against the exact law F(0) - min_{s<=t} F(s) from the closed-form P(z < D, t), small free worlds.
# Root: engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine). CPU, ~1 and ~3 min.
import numpy as np
from harness import Harness

for preset, extra in (("gauss", {"grid": "coarse", "n_bohm": 200, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0, "soft": False}),
                      ("backflow", {"grid": "coarse", "n_bohm": 200, "sigma_z": 2.0, "L": 11.0, "sigma_x": 2.0, "soft": False})):
    h = Harness("v12_arrival_times_2d", preset, extra)
    while not h.sim.done:
        h.run_to(h.sim.t + 2.0 * h.sim.tunit)
    s = h.sim._series()
    tau = s["tau"]
    law = np.cumsum(s["bohm_law"]) * h.sim.dt
    F = h.sim.fg.cdf(h.sim.D, tau)
    exact = F[0] - np.minimum.accumulate(np.concatenate([[h.sim.fg.cdf(h.sim.D, 0.0)[0]], F]))[1:]
    print(f"{preset}: max |law - exact| = {np.max(np.abs(law - exact)):.2e} (before the fix: 3.1e-3 gauss, 2.5e-3 backflow)")
