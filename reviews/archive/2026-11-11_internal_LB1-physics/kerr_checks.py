# Reviewer's checks of p01's Kerr-Newman hole as a scene object (LB1, P16.1): the mass as a change of units, the spin
# and charge as a declared "what if". Run in Docker from engine/ (REVIEW.md, "Environment").
import argparse
import math
import sys

import numpy as np

sys.path[:0] = ["/lf/visualizations/tests", "/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys"]
from harness import Harness  # noqa: E402

from lfphys.core.gravity import kerr_newman as KN  # noqa: E402

V = "p01_gravity"


def run(h, seconds, n=4):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + seconds * k / n)
        h.runner._frame(0.0)


def objs(h, typ):
    return [o for o in h.sim.objects.values() if o["type"] == typ]


def part_mass():
    print("== M. the hole's mass 10 -> 20 Msun at t1: what is continuous, what jumps (by design), vs a world never changed ==")
    a, b = Harness(V, "kerr_orbits"), Harness(V, "kerr_orbits")
    for h in (a, b):
        run(h, 2e-3)
    m = a.sim.mode
    obs = objs(a, "observer")[0]["id"]
    bodies = [o["id"] for o in objs(a, "body")]

    def snap(h):
        mm, _ = h.sim.mode.measure_now()
        g = h.sim.mode.geo
        return {"tau_s": g.proper_time() * h.sim.mode.T, "clock_s": mm[f"{obs}.tau"], "rate": mm[f"{obs}.rate"],
                "r_M": g.bl()[:, 0].copy(), "r_km": np.array([mm.get(f"{k}.r_km", np.nan) for k in bodies]),
                "speed": np.array([mm.get(f"{k}.speed", np.nan) for k in bodies]),
                "E": g.constants()["E"].copy(), "Tr": np.array([mm.get(f"{k}.Tr", np.nan) for k in bodies])}
    s0 = snap(a)
    a.cmd("scene", op="set", id=objs(a, "kn_hole")[0]["id"], values={"mass": 20.0})
    s1 = snap(a)
    for k in s0:
        r = np.asarray(s1[k], float) / np.asarray(s0[k], float)
        print(f"  {k:8s} after/before: {np.array2string(r, precision=15, max_line_width=150)}")
    ds = 2e-3
    run(a, ds)
    run(b, ds / 2)
    ga, gb = a.sim.mode.geo, b.sim.mode.geo
    print(f"  geometric time A {ga.t!r} B {gb.t!r}; max |r_A - r_B| {np.max(np.abs(ga.bl() - gb.bl())):.2e} "
          f"(A ran {ds} s at M = 20, B {ds / 2} s at M = 10)")
    print("  proper times in units of M: A - B/2 - (its growth) checks the 'rescale': "
          f"{np.max(np.abs((ga.proper_time() - gb.proper_time()) - (s1['tau_s'] / a.sim.mode.T - s0['tau_s'] / b.sim.mode.T))):.2e}")
    print(f"  checks failed in A: {[c for c in a.checks().values() if c.get('ok') is False]}")


def part_whatif():
    print("== W. the spin 'what if' near the horizon: the ZAMO speed kept, or silently clamped at 0.999 c? ==")
    h = Harness(V, None, {"laws": "kerr", "spin": 0.9})
    h.cmd("scene", op="add", type="body", values={"r": 1.44, "theta": 90.0, "vmode": "zamo", "v_r": -0.99,
                                                  "v_phi": 0.0, "v_theta": 0.0})
    assert not h.errors(), h.errors()
    g = h.sim.mode.geo
    rp = KN.horizons(0.9)[0]
    print(f"  a = 0.9: r+ = {rp:.6f}; capture at r+ + {g.capture_eps:g}")
    T = h.sim.mode.T
    v0 = None
    for k in range(400):
        h.run_to(h.sim.t + 0.02 * T)
        if g.status()[0] != "active":
            break
        v = float(np.linalg.norm(g.zamo_velocity()[0]))
        if v > 0.999:
            v0 = v
            break
    print(f"  body: status {g.status()[0]}, r {g.bl()[0, 0]:.7f}, ZAMO speed {float(np.linalg.norm(g.zamo_velocity()[0])):.7f}, "
          f"E {g.constants()['E'][0]:.6f}")
    if v0 is None:
        print("  (no moment with speed > 0.999 found)")
        return
    vz0 = g.zamo_velocity()[0].copy()
    n_ev = len(h.of("event"))
    h.cmd("scene", op="set", id=objs(h, "kn_hole")[0]["id"], values={"spin": 0.95})
    print(f"  errors: {h.errors()}")
    g2 = h.sim.mode.geo
    vz1 = g2.zamo_velocity()[0]
    print(f"  after a -> 0.95: ZAMO velocity before {np.array2string(vz0, precision=6)} |v| {np.linalg.norm(vz0):.7f}; "
          f"after {np.array2string(vz1, precision=6)} |v| {np.linalg.norm(vz1):.7f}; gamma {1 / math.sqrt(1 - vz0 @ vz0):.2f} -> "
          f"{1 / math.sqrt(1 - vz1 @ vz1):.2f}")
    txt = " | ".join(e.get("text", "") for e in h.of("event")[n_ev:])
    print(f"  does the event mention the clamp (0.999 / 'огранич')? {'0,999' in txt or '0.999' in txt or 'огранич' in txt}")
    print(f"  event: {txt[:400]}")


def part_tr():
    print("== R. the measured radial period across a mass change ==")
    h = Harness(V, None, {"laws": "kerr", "spin": 0.5, "m_hole": 10.0})
    h.cmd("scene", op="add", type="body", values={"r": 30.0, "vmode": "zamo", "v_phi": 0.17, "v_r": 0.0})
    body = objs(h, "body")[0]["id"]
    m = h.sim.mode
    for k in range(400):
        run(h, 2e-3, n=2)
        if len(m.peri.get(body, ())) == 2:
            break
    Tr0 = m.measure_now()[0][f"{body}.Tr"]
    h.cmd("scene", op="set", id=objs(h, "kn_hole")[0]["id"], values={"mass": 20.0})
    Tr1 = m.measure_now()[0][f"{body}.Tr"]
    print(f"  Tr before {Tr0:.6g} s; right after the change (no new periapsis yet) {Tr1:.6g} s; ratio {Tr1 / Tr0:.6g}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("parts", nargs="*", default=["M", "W", "R"])
    a = ap.parse_args()
    for p in a.parts:
        {"M": part_mass, "W": part_whatif, "R": part_tr}[p]()
        sys.stdout.flush()
