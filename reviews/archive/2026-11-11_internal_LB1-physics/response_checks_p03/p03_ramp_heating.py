"""p03: compress 12 -> 11 nm along x and back (Maxwell preset: 300 argon atoms, 2-D, periodic, 300 K) by a jump or by
ramps of 10 / 50 / 200 ps: the net work of the cycle (= the heat left in the gas, NVE) per atom and as a temperature."""
import sys, time
import numpy as np
sys.path[:0] = ["/lf/visualizations/tests", "/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys"]
from harness import Harness
from p03_molecules.viz import KELVIN, U

def go(tau, seed):
    h = Harness("p03_molecules", "maxwell", seed=seed)
    h.run_to(20e-12)          # 20 ps: the Maxwell distribution established
    h.set(box_time_ps=tau)
    md = h.sim.md
    md.reset_counters()
    E0 = md.energy()
    T0 = h.sim._T_kelvin()
    t = h.sim.t
    h.set(Lx=11.0)
    t += max(tau, 20.0) * 1e-12
    h.run_to(t)
    h.set(Lx=12.0)
    t += max(tau, 20.0) * 1e-12
    h.run_to(t)
    h.run_to(t + 20e-12)
    md = h.sim.md
    W = md.energy_balance()["W_box"]
    n = md.n
    assert not h.errors(), h.errors()
    return W / n, W / n * 2 / 2 * KELVIN, h.sim._T_kelvin() - T0   # per atom (epsilon), as kT (2-D: E = kT per atom)

for tau in (0.0, 10.0, 50.0, 200.0):
    t0 = time.time()
    r = np.array([go(tau, s) for s in (1, 2, 3, 4)])
    print(f"tau {tau:5g} ps: net work per atom {np.round(r[:,0], 4).tolist()} eps; mean {r[:,0].mean():.4f} ± "
          f"{r[:,0].std(ddof=1)/2:.4f} eps = {r[:,0].mean()*KELVIN:.1f} ± {r[:,0].std(ddof=1)/2*KELVIN:.1f} K (as kT per atom); "
          f"T change {np.round(r[:,2],1).tolist()} K  ({time.time()-t0:.0f} s)", flush=True)
