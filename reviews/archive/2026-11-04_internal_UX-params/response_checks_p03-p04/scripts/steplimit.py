"""Justify STEP_MAX = 0.1 sigma: LJ gas (p03 defaults: 2-D, 12x12 nm periodic, 200 atoms, dt = 10 fs) at the
temperature where the rms displacement per step is 0.05 / 0.1 / 0.19 sigma: run 3000 steps, record crashes and the
energy error per atom (in units of kT)."""
import sys, math
sys.path[:0] = ["/lf/lfphys"]
import numpy as np
from lfphys.core.md.system import MD
from lfphys.theories.models import interatomic as IA
U = IA.argon_units(); PS = U.to_ps(1.0); K = U.to_kelvin(1.0); NM = U.to_angstrom(1.0) / 10
dt = 10e-3 / PS
for d, box in ((2, [12 / NM] * 2), (3, [12 / NM, 12 / NM, 6 / NM])):
    for delta in (0.05, 0.1, 0.19):
        T = (delta / dt) ** 2 / d
        for seed in (1, 2, 3):
            md = MD(dim=d, box=box, boundary="periodic", pair=IA.LennardJones(2.5, shift="force"), dt=dt, seed=seed)
            md.add_species("A")
            md.fill("A", n=200, arrangement="random", T=T)
            E0 = md.energy(); err = 0.0; crash = None
            try:
                for _ in range(30):
                    md.step(100)
                    err = max(err, abs(md.energy() - E0) / md.n / T)
            except Exception as e:
                crash = f"{type(e).__name__}: {e}"[:80]
            print(f"d={d} delta={delta} T={T*K:.4g} K seed={seed} max|dE|/(N kT)={err:.3g} crash={crash}", flush=True)
