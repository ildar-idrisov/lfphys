"""v01 after the fixes: P12 (every law choice from the defaults, every scenario), P7 (walkers), P9 and P14 (the
review's repro r_v01_flash: flashes by observers in measure_c / measure_c_lab / andromeda)."""
import sys, math, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness

def bad_checks(h):
    out = []
    for c in h.checks().values():
        if c.get("info"):
            continue
        if c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]):
            out.append((c["id"], c["value"], c["ref"], c["rel"], c["tol"]))
    return out

import os
HOR = {"sun_earth": 700.0, "measure_c": 0.04, "lensing": 0.2, "andromeda": 1e14}
for scn in (HOR if os.environ.get("ALL") else []):
    for kin in ("SR", "ether", "emission"):
        for grav in ("GR", "newton", "none"):
            vals = {"scenario": scn, "kinematics": kin, "gravity": grav}
            t0 = time.time()
            try:
                h = Harness("v01_light_travel", None, vals)
            except ValueError as e:
                print(f"  REFUSED {scn:10s} {kin:9s} {grav:7s}: {e}")
                continue
            for k in range(6):
                h.run_to(HOR[scn] * (k + 1) / 6)
                h.sim.frame()
            hp = h.of("header")[-1]["params"]
            print(f"  ok {scn:10s} {kin:9s} {grav:7s} -> {hp['kinematics']}/{hp['gravity']} R={hp['ln_radius_km']:.4g} "
                  f"errors={h.errors()} bad={bad_checks(h)} notices={[m['text'][:90] for m in h.of('notice')][:2]} "
                  f"{time.time()-t0:.1f}s")

print("== P7: walkers")
for vals in ([] if not os.environ.get("ALL") else ({"scenario": "andromeda", "c_factor": 0.5, "an_walk": 2e8}, {"scenario": "andromeda", "c_factor": 0.5, "an_walk": 2e8, "kinematics": "ether"})):
    try:
        h = Harness("v01_light_travel", None, vals); h.run_to(1e14)
        print("  built", vals, h.errors(), bad_checks(h))
    except ValueError as e:
        print("  refused", vals, e)

print("== P9/P14: the review's repro")
for preset, obj in (("measure_c_lab", "obs1"), ("measure_c", "obs1"), ("andromeda", "earth"), ("andromeda_fast", "earth"),
                    ("measure_c_emission", "obs1"), ("measure_c_ether", "obs1")):
    h = Harness("v01_light_travel", preset=preset)
    sp = h.runner.speed
    def frames(n):
        for _ in range(n):
            h.run_to(h.sim.t + sp / 20.0)
    frames(8); h.action("flash", obj=obj); frames(8); h.cmd("next_event"); h.action("flash", obj=obj); frames(8)
    h.run_to(h.sim.t + 20 * sp)
    print(f"  preset {preset}, flash by {obj}")
    for m in h.of("event"):
        if "измерено" in (m.get("text") or "") or "между концами" in (m.get("text") or ""):
            print(f"     t={m['t']:.6g} {m.get('text')}")
    flat = [c for c in h.checks().values() if c["id"].startswith("flat_")]
    if flat:
        print("     flat checks:", len(flat), "max |rel|/tol", max(abs(c["rel"]) / c["tol"] for c in flat if c["rel"] is not None), "tol range", min(c["tol"] for c in flat), max(c["tol"] for c in flat))
    print("     failed:", bad_checks(h))
