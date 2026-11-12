# Reviewer script (B6 gravity): the playground's Kerr checks (p01 KerrMode.checks): relative drift of Carter's K and
# the mass-shell error |mu^2 - nominal| against the tolerance 10 rtol sqrt(steps) (rtol 1e-10, capture at r_+ + 1e-4).
# (1) long runs of bound orbits (the drift's growth with the number of steps);
# (2) bodies falling into the hole: the shell error just before the capture (P^2/Delta terms grow as 1/Delta);
# (3) the engine's own budget (test_kerr_newman: steps x sqrt(6) rtol |grad| . scale) for comparison.
import math
import time

import numpy as np

from lfphys.core.gravity import kerr_newman as KN


def wrapper_check(g):
    c = g.constants()
    act = np.array([s == "active" for s in g.status()])
    dK = np.abs(c["dK"]) / np.maximum(np.abs(c["K"] - c["dK"]), 1.0)
    dm = np.abs(c["dmu2"])
    n = np.maximum(c["steps"], 1)
    tol = 10.0 * g.rtol * np.sqrt(n)
    return act, dK, dm, tol, c["steps"]


print("(1) long runs, a = 0.9, q = 0.3: inclined eccentric orbits (wrapper's normalisation and tolerance)")
g = KN.Geodesics(0.9, 0.3, rtol=1e-10, capture_eps=1e-4, r_escape=2e3)
g.add_body(8.0, math.radians(70), 0.0, v=(0.0, 0.08, 0.42), key="incl")      # the preset's body
g.add_body(6.0, 1.2, 0.0, v=(0.2, 0.1, 0.45), key="ecc")
g.add_body(20.0, 1.0, 0.0, v=(0.0, 0.05, 0.2), key="wide")
g.add_body(4.0, math.pi / 2, 0.0, v=(0.0, 0.0, 0.5), key="eq4")
t0 = time.time()
for T in (1e3, 1e4, 3e4, 1e5, 3e5, 1e6):
    g.advance(T)
    act, dK, dm, tol, steps = wrapper_check(g)
    worst = [(k, f"{dK[i]:.2e}/{dm[i]:.2e} vs {tol[i]:.2e} ({steps[i]} st)") for i, k in enumerate(g.keys)]
    fail = any((dK[i] > tol[i] or dm[i] > tol[i]) and act[i] for i in range(g.n))
    print(f"  t = {T:8.0f} M: dK_rel/dmu2 vs tol per body: {worst}  status {g.status()}  any fails: {fail}  "
          f"wall {time.time() - t0:.0f} s", flush=True)
    if time.time() - t0 > 240:
        break

print()
print("(2) radial and plunging infalls, a = 0.9, q = 0.3: the shell error while still active, close to r_+ + 1e-4")
for v in [(-0.0, 0.0, 0.0), (-0.3, 0.0, 0.1), (-0.6, 0.1, 0.3), (0.0, 0.0, 0.05)]:
    g = KN.Geodesics(0.9, 0.3, rtol=1e-10, capture_eps=1e-4, r_escape=2e3)
    g.add_body(12.0, 1.3, 0.0, v=v, key="f")
    worst_ratio, at = 0.0, None
    t = 0.0
    while g.status()[0] == "active" and t < 5e3:
        t += 0.5
        g.advance(t)
        act, dK, dm, tol, steps = wrapper_check(g)
        if act[0]:
            r = g.bl()[0, 0]
            ratio = max(dK[0], dm[0]) / tol[0]
            if ratio > worst_ratio:
                worst_ratio, at = ratio, (r, dK[0], dm[0], tol[0], steps[0])
    print(f"  v = {v}: status {g.status()[0]}; worst (error / tolerance) while active = {worst_ratio:.3g} at "
          f"r - r_+ = {at[0] - g.r_plus:.3e} (dK_rel {at[1]:.2e}, dmu2 {at[2]:.2e}, tol {at[3]:.2e}, steps {at[4]})")
