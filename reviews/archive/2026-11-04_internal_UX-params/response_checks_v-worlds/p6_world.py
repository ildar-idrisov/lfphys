"""P6: v15's Johannsen-metric combinations of the review (#2, #4, #5, #6, #34, #37, #92) after the fix: the refusal
text (Russian, with the admissible values) or the world built; time of each."""
import sys, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness
cases = [(None, {"metric": "jp", "a13": -10.0}), (None, {"metric": "jp", "a22": -3.0}), (None, {"metric": "jp", "a22": 10.0}),
         (None, {"metric": "jp", "a12": -3.0}), (None, {"metric": "jp", "a13": 10.0, "chi": 0.998}),
         (None, {"metric": "jp", "a22": -3.0, "a12": -3.0, "chi": 0.998}),
         ("whatif", {"metric": "jp", "a13": -1.399, "a22": 3.612, "a12": -3.0, "retro": False, "n_rays": 22}),
         ("whatif", {})]
for pr, vals in cases:
    t0 = time.time()
    try:
        h = Harness("v15_kerr_shadow", preset=pr, params=vals)
        h.run_to(5.0)
        print(f"BUILT {pr} {vals} in {time.time()-t0:.2f}s; errors {h.errors()}; notices {[m['text'][:160] for m in h.of('notice')]}")
        print("   hole", {k: v for k, v in h.of('header')[-1]['hole'].items() if k != 'kerr'})
        print("   checks", {k: (c.get('value'), c.get('ok')) for k, c in h.checks().items()})
    except Exception as e:
        print(f"REFUSED {pr} {vals} in {time.time()-t0:.2f}s: {type(e).__name__}: {e}")
