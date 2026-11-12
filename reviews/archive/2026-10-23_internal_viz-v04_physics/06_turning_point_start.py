"""06: a segment that starts at (or within rounding of) a turning point with v_r != 0 exactly: the orbit kind and the
turning points of OrbitStream._classify, against 40-digit roots of the same cubic from the same float initial data.

A boost of a circular orbit is the common case: the state from the dense output has v_r ~ 1e-17, not 0, so
_classify takes the general branch (lo = max root <= 1, hi = min root >= 1) and a root that sits at y = 1 +- 1e-15
decides the bracket by its rounding.  The true kind follows from the 40-digit roots and the sign of v_r.
"""
import math

import mpmath as mp

from harness import Harness
from lfphys.core.gravity import orbit_stream as osm

mp.mp.dps = 40


def truth(r0, vr, vp, r_stop=2.0):
    R0, VR, VP = mp.mpf(r0), mp.mpf(vr), mp.mpf(vp)
    v2 = VR**2 + VP**2
    g2 = 1 / (1 - v2)
    EM1, L = g2 * (v2 - 2 / R0), mp.sqrt(g2) * VP * R0
    us = 1 / R0
    A, B = 1 / (L**2 * us), EM1 / (L**2 * us**2)
    ys = sorted([mp.re(z) for z in mp.polyroots([2 * us, -1, 2 * A, B], maxsteps=400, extraprec=400)
                 if abs(mp.im(z)) < mp.mpf(10) ** -25])
    return ys, EM1


def kind_from(ys, vr, r0, r_stop=2.0, em1=None):
    # the allowed interval containing y = 1 (F >= 0), then the motion: bound if both ends are turning points > 0
    y_stop = r0 / (r_stop if r_stop > 2 else 2.0 / (1 - osm.HORIZON_GAP))
    below = [y for y in ys if y <= 1 + mp.mpf(10) ** -30]
    above = [y for y in ys if y >= 1 - mp.mpf(10) ** -30]
    return ys


cases = []
print("boosts of circular orbits in the run (Harness):")
for preset, params, dv in (("bh_isco", {}, -0.05), ("bh_isco", {}, 0.05), ("bh_isco", {}, -2e-7), ("bh_isco", {}, 1e-7),
                           ("default", {"r0": 20.0, "speed": 1.0}, 0.05), ("default", {"r0": 20.0, "speed": 1.0}, -0.05),
                           ("default", {"r0": 20.0, "speed": 1.0}, -0.3), ("default", {"r0": 8.0, "speed": 1.0}, -0.05),
                           ("default", {"r0": 8.0, "speed": 1.0}, 0.05), ("default", {"r0": 1e6, "speed": 1.0}, 0.05),
                           ("default", {"r0": 1e6, "speed": 1.0}, -0.05)):
    for frac in (0.37, 0.61, 1.13):
        h = Harness("v04_orbits", preset, params)
        r0 = h.sim.init["r0"]
        h.run_to(frac * 2 * math.pi * r0**1.5 * h.sim.T_s)
        h.action("boost", dv=dv)
        ini = h.sim.init
        info = h.sim.info
        ys, EM1 = truth(ini["r0"], ini["v_r"], ini["v_phi"])
        rr = sorted(float(ini["r0"] / y) for y in ys if y > 0)
        # true orbit: a start at the periapsis if speeding up tangentially from a circle, apoapsis if slowing down
        print(f"{preset:8s} {str(params):30s} dv={dv:+.1e} at {frac:.2f} turn: v_r={ini['v_r']:+.2e} | run kind "
              f"{info['kind']:8s} r_peri {info['r_peri']!s:22.22s} r_apo {info['r_apo']!s:22.22s} | 40-digit radii of "
              f"turning points {[f'{x:.10g}' for x in rr]}, e^2-1 = {float(EM1):+.4f}")
