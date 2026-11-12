"""05: 'circular' classification (|r_apo - r_peri| <= 1e-6 r_peri in GR, ecc < 1e-6 in Newton) vs the tolerances of the
circular-orbit checks (1e-10 GR, 1e-8 Newton), which assume an exactly circular orbit.

A launch slightly off the circular speed, or a tiny boost of a circular orbit, is classified 'circular'; the run then
compares its own (correct) measurement with the formulas of the exact circle.  Here: the run's checks, and a
50-digit computation of what the circle formulas miss for that orbit (its azimuthal period differs from 2 pi r0^1.5).
"""
import math

from harness import Harness


def bad(h):
    out = []
    for c in h.checks().values():
        if c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]):
            out.append((c["id"], c["label"][:60], c["value"], c["ref"], c["rel"], c["tol"], c.get("ok")))
    return out


def run(params, n_turns=3.3, boost=None, preset="default"):
    h = Harness("v04_orbits", preset, params)
    if boost is not None:
        h.run_to(0.37 * 2 * math.pi * h.sim.init["r0"] ** 1.5 * h.sim.T_s)
        h.action("boost", dv=boost)
    info = h.sim.info
    r0 = h.sim.init["r0"]
    h.run_to(h.sim.t + n_turns * 2 * math.pi * r0**1.5 * h.sim.T_s)
    tr = h.sim.track.info
    print(f"params {params} boost {boost}: kind {info['kind']}, r_peri {tr.get('r_peri')!r}, r_apo {tr.get('r_apo')!r}")
    for b in bad(h):
        print("   FAILING:", b)
    if not bad(h):
        print("   all checks pass;", len(h.checks()), "checks")
    print("   errors:", h.errors())
    return h


print("GR, r0 = 20 M:")
for k in (1.0, 1.0000001, 1.0000002, 0.9999998):
    run({"r0": 20.0, "speed": k, "angle": 0.0})
print("\nGR, bh_isco preset (6.2 M) with a tiny boost:")
for dv in (1e-9, 1e-7, -2e-7):
    run({}, boost=dv, preset="bh_isco")
print("\nNewton, r0 = 50 M:")
for k in (1.0, 1.0000001, 1.0000004):
    run({"gravity": "newton", "r0": 50.0, "speed": k, "angle": 0.0})
print("\nGR, r0 = 20 M, launch 1e-5 deg off the tangent (circular speed):")
run({"r0": 20.0, "speed": 1.0, "angle": 1e-5})
