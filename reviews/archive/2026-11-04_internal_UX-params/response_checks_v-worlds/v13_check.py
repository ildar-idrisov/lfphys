import sys, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness
def bad(h):
    return [(c["id"], c["value"], c["ref"]) for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]
for V, cases in (("v13_hydrogen_3d", [{"mode": "super"}, {"n": 1}, {"m": 5}, {"n": 1, "mode": "super"}, {"mode": "super", "l2": 0, "n2": 2},
                                      {"mode": "super", "n2": 2, "l2": 1, "m2": 0}, {"n": 2, "l": 2}, {"l": 11, "m": -11}]),
                 ("v14_quarkonium_3d", [{"mode": "super"}, {"m": 2}, {"mode": "super", "l": 1}, {"mode": "super", "l2": 0}, {"mode": "super", "m2": -2}])):
    for vals in cases:
        t0 = time.time()
        try:
            h = Harness(V, None, {**vals})
            sim = h.sim
            h.run_to(sim.period * 1.0001 if sim.nb > 1 else 1.0)
            hp = h.of("header")[-1]["params"]
            print(f"{V} {vals}: OK state n,l,m={hp['n'],hp['l'],hp['m']} 2nd={hp['n2'],hp['l2'],hp['m2']} errors={h.errors()} bad={bad(h)} notices={[m['text'] for m in h.of('notice')]} cont={h.checks().get('continuity',{}).get('note','')[:60]} [{time.time()-t0:.1f}s]")
        except ValueError as e:
            print(f"{V} {vals}: REFUSED {e} [{time.time()-t0:.1f}s]")
