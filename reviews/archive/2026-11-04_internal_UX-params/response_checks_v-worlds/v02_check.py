"""v02 after the fixes: P8 (dark rate), P15 (coherence), P17 (texts), P18 (probe wavelength, GRW): the review's cases."""
import sys, time, resource
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness
import v02_double_slit.viz as V
print("OPTION_SHOW_IF", V.OPTION_SHOW_IF)
def bad(h):
    return [(c["id"], c["value"], c["ref"]) for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]
def build(pr, vals, ops=()):
    t0 = time.time()
    try:
        h = Harness("v02_double_slit", preset=pr, params=vals)
    except ValueError as e:
        print(f"  REFUSED {pr} {vals}: {e}  [{time.time()-t0:.1f}s]"); return None
    for op in ops:
        if op[0] == "set": h.set(**op[1])
        elif op[0] == "frames":
            for _ in range(op[1]): h.runner._advance(h.sim.t + h.runner.speed / 20, budget=0.05); h.sim.frame()
        elif op[0] == "next": h.cmd("next_event")
    print(f"  OK {pr} {vals} ops={len(ops)} errors={h.errors()} bad={bad(h)} maxrss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024} MB [{time.time()-t0:.1f}s]")
    return h
print("== P8")
build(None, {"dark_rate": 1e12})
build(None, {"dark_rate": 1e5}, [("frames", 6), ("next",), ("frames", 6)])
h = build(None, {}, [("frames", 3), ("set", {"dark_rate": 1e12}), ("set", {"dark_rate": 1e5}), ("frames", 6)])
print("   ", h.errors())
build("triple", {}, [("frames", 3), ("set", {"dark_rate": 1e12})])
build(None, {"dark_rate": 1e12, "rate": 1e10}, [("frames", 6), ("next",), ("frames", 6)])
print("== P15")
for vals, ops in (({"el1": "polarizer", "el2": "polarizer", "el1_angle": 0.0, "el2_angle": 90.0}, [("frames", 6)]),):
    h = build(None, vals, ops)
    print("   coh", {k: (c["value"], c["ref"], c.get("info"), c["note"][:120]) for k, c in h.checks().items() if k.startswith("coh")}, h.sim.frame()[0].get("coh"))
h = build("photon_eraser", {}, [("set", {"pol_state": "H"}), ("set", {"pol_state": "D"})])
print("   coh", {k: (c["value"], c["ref"], c.get("info")) for k, c in h.checks().items() if k.startswith("coh")})
h = build("photon_eraser_minus", {}, [("set", {"el1": "none"})])
h = build("c60_grw", {}, [("set", {"species": "custom"}), ("set", {"mass_u": 1e9}), ("set", {"mass_u": 1.0})])
print("   coh", {k: (c["value"], c["ref"], c.get("info")) for k, c in h.checks().items() if k.startswith("coh")})
print("== P17")
build(None, {"el1": "rot_y"}); build(None, {"el1": "filter"}); build(None, {"wp_mode": "microscope"})
build(None, {"energy_by": "speed"}); build("electron", {"energy_by": "freq"}); build(None, {"wp_mode": "qubit", "wp_slit": 5})
build("c60", {"analyzer": "on"})
h = build("electron", {}, [("set", {"el2": "polarizer"})]); print("   ", h.errors())
print("== P18")
h = build("electron_eraser", {}, [("set", {"wp_mode": "microscope"}), ("set", {"mic_lambda_nm": 0.001}), ("frames", 3)]); print("   ", h.errors())
build("electron_microscope", {"mic_lambda_nm": 0.001})
build(None, {"collapse": "grw", "grw_lambda": 1e12, "grw_rc_nm": 0.001, "species": "c60"})
build("electron_microscope", {}, [("frames", 6)])
