"""v03, harmonic trap: the period check reports value == reference to all digits (out/05_*_run_0.05_15.txt). Look at
<x>(t) of the stored snapshots (as the check computes it), at the snapshots themselves, and at an independent
float64 evolution of the same packet with lfphys' stepper (one period, the run's dt).
Output: out/10_v03_oscillator_period.txt
"""
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from v03_quantum_1d.viz import HBAR  # noqa: E402

OUT = open("out/10_v03_oscillator_period.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


h = Harness("v03_quantum_1d", "oscillator")
sim = h.sim
g = sim.grid
xm = np.sum(sim.snaps * g.x[None, :], axis=1) / np.sum(sim.snaps, axis=1)
w = sim.params["hw"] / HBAR
T = 2 * math.pi / w
iT = int(round(T / sim.dt_store))
say(f"snapshots: {len(sim.snaps)}, dt_store = {sim.dt_store:.6g} fs, period {T:.6g} fs, i_T = {iT}")
say(f"<x>(t) at i = 0, 75, 150, 225, 300, 450, 600: {[round(float(xm[i]), 6) for i in (0, 75, 150, 225, 300, 450, 600) if i < len(xm)]}")
say(f"<x>(i_T) - <x>(0) = {xm[iT] - xm[0]:.3e} nm; max |snap[i_T] - snap[0]| = {np.max(np.abs(sim.snaps[iT] - sim.snaps[0])):.3e}"
    f" (snap dtype {sim.snaps.dtype}, max of snap[0] {sim.snaps[0].max():.3e})")
check = h.checks()["per0"]
say(f"run's check per0: value {check['value']!r}, ref {check['ref']!r}")

# independent float64 evolution over one period with the run's own time step
psi = g.gaussian(sim.x_start, sim.k0, sim.sigma)
sub = max(1, int(math.ceil(sim.dt_store / sim._dt_max())))
dt = sim.dt_store / sub
step = g.stepper(sim.V, dt)
for _ in range(iT * sub):
    psi = step(psi)
rho = np.abs(psi) ** 2
x_T = float(np.sum(g.x * rho) / np.sum(rho))
say(f"float64 evolution over i_T * sub = {iT * sub} steps: <x>(T) = {x_T!r}, <x>(0) = {float(xm[0])!r}, "
    f"difference {x_T - xm[0]:.3e} nm (relative {abs(x_T - xm[0]) / abs(xm[0]):.1e})")
