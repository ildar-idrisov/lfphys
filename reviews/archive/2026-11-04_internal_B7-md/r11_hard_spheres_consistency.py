"""Hard spheres at rho = 0.5 (eta = 0.262), N = 500, periodic (the engine's test state point): (1) no overlap ever
appears (closest centres, sampled every 0.05 time units); (2) the virial route Z_vir (the engine's) against the collision-rate route
Z_rate = 1 + gamma(N) sqrt(pi / (2 D N E_kin)) * collisions / time (Kolafa & Rottner 2006, Eq. Zrate, m = sigma = 1;
gamma(N) from the same paper) - equal in expectation for correct event dynamics; (3) Z against Kolafa-Labik-
Malijevsky's 3.2693735 (zfinal.res, "Z(corr.)") minus enscorr/N = 1.02068/500 (their hseos.c corr() on zB6_11348)."""
import common  # noqa: F401
import math

import numpy as np

from lfphys.core.md import cells
from lfphys.core.md.hard import HardSpheres

D, N, rho = 3, 500, 0.5
ref = 3.2693735 - 1.0206801 / N


def gamma_N(n, d):
    return math.exp(math.lgamma((d * (n - 1) + 1) / 2) - math.lgamma(d * (n - 1) / 2)) / math.sqrt(d * n / 2)


rows = []
for seed in range(11, 23):
    L = (N / rho) ** (1 / 3)
    hs = HardSpheres(D, [L] * 3, seed=seed)
    hs.add_species("S")
    hs.fill("S", n=N, T=1.0)
    hs.advance(5.0)
    hs.reset_counters()
    dmin = 9.9
    t_run = 25.0
    for k in range(1, int(t_run / 0.05) + 1):
        hs.advance(5.0 + 0.05 * k)
        x = hs.positions()
        i, j = cells.pair_list(x, hs.L, hs.periodic, 1.02)
        if len(i):
            dx = x[j] - x[i]
            dx -= hs.L * np.rint(dx / hs.L)
            dmin = min(dmin, float(np.sqrt((dx * dx).sum(1)).min()))
    p = hs.pressure()
    E = hs.kinetic_energy()
    z_rate = 1 + gamma_N(N, D) * math.sqrt(math.pi / (2 * D * N * E)) * p["collisions"] / p["interval"]
    rows.append((p["Z"], z_rate))
    print(f"seed {seed}: closest centres {dmin:.12f} (sigma = 1); collisions {p['collisions']}; "
          f"Z_vir {p['Z']:.5f}  Z_rate {z_rate:.5f}  difference {p['Z'] - z_rate:+.5f}")
zv = np.array([r[0] for r in rows])
zr = np.array([r[1] for r in rows])
se = zv.std(ddof=1) / math.sqrt(len(zv))
print(f"mean Z_vir {zv.mean():.5f} +- {se:.5f} ({len(zv)} runs); mean Z_rate {zr.mean():.5f} +- "
      f"{zr.std(ddof=1) / math.sqrt(len(zr)):.5f}; mean Z_vir - Z_rate {np.mean(zv - zr):+.5f} +- {np.std(zv - zr, ddof=1) / math.sqrt(len(zv)):.5f}")
print(f"reference Z_NVT(500) = 3.2693735 - 1.02068/500 = {ref:.5f}; Z_vir - ref = {zv.mean() - ref:+.5f} "
      f"({(zv.mean() / ref - 1) * 100:+.2f} %, {(zv.mean() - ref) / se:+.1f} SE); the engine's note: +0.39 % (3.2800 +- 0.0034)")
