"""Scan: LJ gas (2-D 12x12 nm, 3-D 12x12x6 nm periodic, 200 atoms, dt = 10 fs) at T: q = (rms step) / (r_min/12),
r_min = (4/T)^(1/12) sigma (where the repulsion reaches kT): crash or the energy error per atom in kT over 3000 steps."""
import sys, math
sys.path[:0] = ["/lf/lfphys"]
import numpy as np
from lfphys.core.md.system import MD
from lfphys.theories.models import interatomic as IA
U = IA.argon_units(); PS = U.to_ps(1.0); K = U.to_kelvin(1.0); NM = U.to_angstrom(1.0) / 10
dt = 10e-3 / PS
for d, box in ((2, [12 / NM] * 2), (3, [12 / NM, 12 / NM, 6 / NM])):
    for TK in (300, 600, 1000, 1500, 2000, 3000, 4500):
        T = TK / K
        q = math.sqrt(d * T) * dt / ((4.0 / T) ** (1 / 12) / 12)
        res = []
        for seed in (1, 2, 3):
            md = MD(dim=d, box=box, boundary="periodic", pair=IA.LennardJones(2.5, shift="force"), dt=dt, seed=seed)
            md.add_species("A")
            md.fill("A", n=200, arrangement="random", T=T)
            E0 = md.energy(); err = 0.0; crash = ""
            try:
                for _ in range(30):
                    md.step(100)
                    err = max(err, abs(md.energy() - E0) / md.n / T)
            except Exception as e:
                crash = "CRASH"
            res.append(f"{err:.3g}{crash}")
        print(f"d={d} T={TK} K q={q:.3f} errors(kT/atom)={res}", flush=True)
