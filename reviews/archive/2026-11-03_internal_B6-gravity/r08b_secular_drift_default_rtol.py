# Reviewer script (B6 gravity): the secular energy drift left by the default symmetrization tolerance dt_rtol = 1e-3
# on a very eccentric orbit (e = 0.999, eta = 0.02, KYM98 / HMM95's regime), against a strict rule (dt_rtol 1e-8).
import sys
import time

sys.path.insert(0, "/lf/lfphys/tests")
from test_nbody import binary  # noqa: E402

t0 = time.time()
for kw in ({}, {"dt_rtol": 1e-8, "max_passes": 30}):
    nb, P = binary(e=0.999, eta=0.02, **kw)
    E0 = nb.energy()
    row = []
    for k in (1, 10, 100, 200, 400, 600):
        nb.advance((k + 0.5) * P)
        row.append((k, (nb.energy() - E0) / abs(E0)))
    print(f"{kw or 'defaults (dt_rtol 1e-3)'}: signed dE/E at apoapsis after k orbits: "
          + ", ".join(f"{k}: {x:+.3e}" for k, x in row) + f"   wall {time.time() - t0:.0f} s", flush=True)
