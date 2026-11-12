"""v08 (P26): the window search's measured estimates per pad for worlds refused or accepted, and the time."""
import sys, time, json
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry
registry.ensure_path()
import math
import v08_wave_3d.viz as V
from v08_wave_3d.engine import apparatus as A
cases = [{"source": "circle"}, {"source": "circle", "a": 3.0, "zmax": 40.0}, {"source": "circle", "a": 1.5}, {"source": "circle", "a": 0.75, "zmax": 10.0},
         {"a": 0.2}, {"zmax": 80.0}, {}, {"source": "square"}, {"source": "gauss"}, {"source": "circle", "a": 6.0, "zmax": 80.0}]
for c in cases:
    p, err = V.SCHEMA.resolve(None, c)
    n = int(p["n"]); lam = float(p["lam"]); k = 2 * math.pi / lam; dx = lam / 4
    src = A.source(p, n)
    t0 = time.time()
    rows = []
    orig = A._diff
    try:
        w = A.choose_window(src, dx, k, float(p["zmax"]))
        res = f"OK pad {w.pad} bl {w.band_limit} est {w.est:.2e}"; rows = w.rows
    except ValueError as e:
        res = "REFUSED"
    print(json.dumps({"case": c, "res": res, "s": round(time.time() - t0, 1), "rows": [(r[0], r[1], r[2]) for r in rows]}), flush=True)
