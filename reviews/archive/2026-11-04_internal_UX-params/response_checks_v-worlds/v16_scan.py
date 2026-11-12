import sys, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness
def bad(h):
    return [(c["id"], c["value"], c["ref"]) for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]
for l in (1, 3, 6):
    for per in (1.2, 1.6, 2.5, 3.5):
        for w0 in (None, 3.0, 5.0):
            vals = {"gen": "fork", "l": l, "period": per}
            if w0: vals["w0"] = w0
            try:
                h = Harness("v16_optical_vortices", None, vals); h.run_to(0.5)
                print(f"l={l} Λ={per} w0 asked {w0}: w0={h.of('header')[-1]['params']['w0']} bad={[b[0] for b in bad(h)]} {[ (b[1],b[2]) for b in bad(h)][:2]}")
            except ValueError as e:
                print(f"l={l} Λ={per} w0 asked {w0}: REFUSED {str(e)[:80]}")
