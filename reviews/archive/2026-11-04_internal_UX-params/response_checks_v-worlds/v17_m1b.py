import sys, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness
def bad(h):
    return [(c["id"], c["value"], c["tol"]) for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]
for n_re in (1.0 + 2e-6, 1.0 + 1e-5, 1.0 + 3e-5, 1.0 + 3e-4):
    for r in (1.0, 150.0):
        t0 = time.time()
        try:
            h = Harness("v17_mie_scattering", None, {"index": "custom", "n_re": n_re, "n_im": 0.0, "n_medium": 1.0, "radius_um": r, "n_lam": 8})
            print(f"n={n_re!r} r={r}: bad={bad(h)} [{time.time()-t0:.1f}s]", flush=True)
        except ValueError as e:
            print(f"n={n_re!r} r={r}: REFUSED {e}")
