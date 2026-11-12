"""10: the 'r_peri'/'r_apo' check near the ISCO: which side is off when it fails — the run's event or the reference
orbits.elements(e, l) — and is its tolerance max(1e-9, 4 eps/(|e^2-1| ecc)) adequate there?

Near the ISCO two turning points are close to the third root; the roots of the cubic are ill-conditioned in a way the
Newtonian factor 1/(|e^2-1| ecc) does not capture. 40-digit roots of the same cubic (from the same float launch
data) decide.
"""
import math

import mpmath as mp

from harness import Harness
from lfphys.core.gravity import orbits

mp.mp.dps = 40


def mp_turning(r0, vr, vp):
    R0, VR, VP = mp.mpf(r0), mp.mpf(vr), mp.mpf(vp)
    v2 = VR**2 + VP**2
    g2 = 1 / (1 - v2)
    EM1, L = g2 * (v2 - 2 / R0), mp.sqrt(g2) * VP * R0
    U = sorted([mp.re(z) for z in mp.polyroots([2, -1, 2 / L**2, EM1 / L**2], maxsteps=400, extraprec=400)
                if abs(mp.im(z)) < mp.mpf(10) ** -25])
    return U


def report(h, label):
    ini = h.sim.init
    U = mp_turning(ini["r0"], ini["v_r"], ini["v_phi"])
    el = h.sim.info.get("elements")
    for cid, c in sorted(h.checks().items()):
        key = cid.split(".")[1]
        if key not in ("r_peri", "r_apo"):
            continue
        truth = 1 / U[1] if key == "r_peri" else 1 / U[0]
        ok = abs(c["rel"]) <= c["tol"]
        print(f"  {label}: {cid:9s} event {c['value']!r:22} ref(elements) {c['ref']!r:22} 40-digit {mp.nstr(truth, 17):20} | "
              f"event err {float((c['value'] - truth) / truth):+.1e}, ref err {float((c['ref'] - truth) / truth):+.1e}, "
              f"tol {c['tol']:.1e} {'pass' if ok else 'FAIL'}")


print("launch near the ISCO (start at a turning point, v_r = 0 exactly):")
for r0, k in ((6.2, 1.0001), (6.2, 0.9999), (6.05, 1.00001), (6.5, 1.00001), (6.01, 1.000001), (7.0, 1.000001)):
    h = Harness("v04_orbits", "default", {"r0": r0, "speed": k, "angle": 0.0})
    if h.sim.info["kind"] != "bound":
        print(f"  r0={r0} k={k}: kind {h.sim.info['kind']}")
        continue
    h.run_to(h.sim.t + 3.3 * h.sim._period_estimate(h.sim.track) * h.sim.T_s)
    report(h, f"r0={r0} k={k}")

print("\nbh_isco + boost dv = +1e-7 at 0.61 turn (classified correctly there):")
h = Harness("v04_orbits", "bh_isco")
h.run_to(0.61 * 2 * math.pi * 6.2**1.5 * h.sim.T_s)
h.action("boost", dv=1e-7)
h.run_to(h.sim.t + 3.3 * h.sim._period_estimate(h.sim.track) * h.sim.T_s)
report(h, "boost 1e-7")
