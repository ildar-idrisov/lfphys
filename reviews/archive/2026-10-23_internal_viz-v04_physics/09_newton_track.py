"""09: the Newtonian track (visualizations/v04_orbits/engine/body.py: NewtonTrack) on eccentric and near-radial orbits,
and the state it hands to a boost.

(a) Launch angle -80 ... -89.99 deg (inward, nearly radial): the periapsis is ~r0 cos^2(angle) deep. Shown: the run's
    'adv', 'period', 'energy' checks, and the closed-form periapsis distance (exact conic from the initial data).
(b) The swept angle psi of the samples: unwrap of atan2 between successive samples; the angle swept per sample
    near periapsis vs pi.
(c) A boost with dv = 0 must continue the same orbit: E and h of the new segment vs the old (exact conic constants).
"""
import math

import numpy as np

from harness import Harness


def bad(h):
    out = []
    for c in h.checks().values():
        if c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]):
            out.append(f"{c['id']}: value={c['value']!r} ref={c['ref']!r} rel={c['rel']!r} tol={c['tol']!r} ok={c.get('ok')}")
    return out


print("(a)+(b) Newton world, r0 = 20 M, speed 1.0 x circular, inward angles")
for ang in (-60.0, -80.0, -85.0, -89.0, -89.9, -89.99):
    h = Harness("v04_orbits", "newton_ellipse", {"angle": ang, "speed": 1.0, "ghost": False})
    tr = h.sim.track
    P = tr.period * tr.T
    h.run_to(3.3 * P * h.sim.T_s)
    # swept angle per stored sample near periapsis: from the trail (thinned) and from the engine samples
    r_peri = tr.info["r_peri"]
    # the largest angle swept between successive fine samples: h / r^2 * dt at periapsis
    dt = tr.period / 4000.0  # scaled sample spacing (4000 per period)
    dpsi_peri = abs(tr.h0) / (r_peri / tr.L) ** 2 * dt
    print(f"  angle {ang:7.2f}: r_peri = {r_peri:.4e} M (r_peri/r0 = {r_peri / 20:.2e}); swept angle per sample at "
          f"periapsis ~ {dpsi_peri:.3g} rad; drift E = {tr.drift['E']:.2e}, h = {tr.drift['h']:.2e}")
    for b in bad(h):
        print("     FAILING", b)
    ap = [m for m in h.of("apsis") if m["kind"] == "peri"]
    print("     periapsis adv per orbit [deg]:", [None if a["adv"] is None else round(math.degrees(a["adv"]), 9)
                                                 for a in ap])

print("\n(c) boost dv = 0: the orbit must continue unchanged")
for law, preset, frac in (("newton", "newton_ellipse", 0.3), ("newton", "newton_ellipse", 0.71),
                          ("GR", "default", 0.3), ("GR", "default", 0.71)):
    h = Harness("v04_orbits", preset, {"ghost": False})
    tr0 = h.sim.track
    if law == "newton":
        E0, h0 = tr0.E0 / tr0.L, tr0.h0 * math.sqrt(tr0.L)
    else:
        E0, h0 = tr0.em1, tr0.l
    Pe = h.sim._period_estimate(tr0) * h.sim.T_s
    h.run_to(frac * Pe)
    h.action("boost", dv=0.0)
    tr1 = h.sim.track
    if law == "newton":
        E1, h1 = tr1.E0 / tr1.L, tr1.h0 * math.sqrt(tr1.L)
    else:
        E1, h1 = tr1.em1, tr1.l
    print(f"  {law:6s} at {frac:.2f} period: specific energy rel change {(E1 - E0) / abs(E0):+.2e}, "
          f"angular momentum rel change {(h1 - h0) / abs(h0):+.2e}")
