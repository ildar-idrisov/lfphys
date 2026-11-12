"""Prototype: net work of a compress-and-return cycle by ramps of growing duration vs a jump (2-D LJ fluid)."""
import sys, time
import numpy as np
sys.path[:0] = ["/lf/lfphys"]
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import LennardJones

def fluid(seed, n=100, L=16.0):
    md = MD(dim=2, box=[L, L], pair=LennardJones(2.5), dt=0.004, seed=seed)
    md.add_species("a")
    md.fill("a", n=n, T=1.5, arrangement="random")
    md.step(500)
    md.reset_counters()
    return md

def cycle(seed, tau, n=100, L=16.0, c=0.85):
    md = fluid(seed, n, L)
    E0 = md.energy()
    if tau == 0:
        md.deform([L * c, L]); md.step(400)
        md.deform([L, L]); md.step(400)
    else:
        md.ramp_box([L * c, L], tau)
        while md.ramp_running(): md.step(1)
        md.ramp_box([L, L], tau)
        while md.ramp_running(): md.step(1)
    b = md.energy_balance()
    return b["W_box"], b["residual"], md.energy() - E0, md.box_ramp()

for n, L in ((100, 16.0), (400, 32.0)):
    for tau in (0, 1, 4, 16, 64):
        t0 = time.time()
        ws = []
        for seed in (3, 4, 5, 6):
            W, res, dE, r = cycle(seed, tau, n, L)
            ws.append(W)
        ws = np.array(ws)
        print(f"n={n} tau={tau:4g}: W_net {np.round(ws, 3).tolist()} mean {ws.mean():.3f} se {ws.std(ddof=1)/2:.3f}  "
              f"per atom {ws.mean()/n:.4f}  res {res:.2e}  ({time.time()-t0:.1f} s)", flush=True)
