import sys, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness
def bad(h):
    return [(c["id"], c["value"], c["ref"]) for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]
for vals in ({"gen": "fork"}, {"gen": "fork", "period": 1.0}, {"gen": "fork", "period": 1.2}, {"gen": "fork", "period": 1.6}, {"gen": "fork", "period": 4.0},
             {"gen": "fork", "period": 6.0}, {"gen": "fork", "period": 8.0}, {"gen": "fork", "lam": 0.4}, {"gen": "fork", "lam": 1.6, "period": 2.0}, {"gen": "fork", "w0": 6.0, "period": 8.0}):
    t0 = time.time()
    try:
        h = Harness("v16_optical_vortices", None, vals)
        h.run_to(1.0)
        print(f"{vals}: OK w0={h.of('header')[-1]['params']['w0']} z_end={h.sim.z_end:.3g} bad={bad(h)} errors={h.errors()} notice={[m['text'][:100] for m in h.of('notice')]} [{time.time()-t0:.1f}s]")
    except ValueError as e:
        print(f"{vals}: REFUSED {e} [{time.time()-t0:.1f}s]")
h = Harness("v16_optical_vortices", "fork"); h.run_to(1.0); print("preset fork w0", h.of('header')[-1]['params']['w0'], bad(h), [m['text'][:80] for m in h.of('notice')])
