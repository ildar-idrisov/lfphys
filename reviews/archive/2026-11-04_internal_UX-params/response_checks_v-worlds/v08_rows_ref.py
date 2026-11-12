"""v08 (P26): the window search's per-level estimates for refused worlds (logged from _diff), and the time per level."""
import sys, time, json, math
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry
registry.ensure_path()
import v08_wave_3d.viz as V
from v08_wave_3d.engine import apparatus as A
log = []
orig = A._diff
def spy(a, b):
    r = orig(a, b); log.append((round(time.time() - T0[0], 1), r[0])); return r
A._diff = spy
T0 = [0.0]
for c in ({"source": "circle"}, {"a": 0.2}, {"zmax": 80.0}, {"source": "circle", "a": 1.5}, {"source": "square"}):
    p, err = V.SCHEMA.resolve(None, c)
    n = int(p["n"]); lam = float(p["lam"]); k = 2 * math.pi / lam; dx = lam / 4
    src = A.source(p, n)
    log.clear(); T0[0] = time.time()
    try:
        w = A.choose_window(src, dx, k, float(p["zmax"])); res = f"OK pad {w.pad} bl {w.band_limit} est {w.est:.2e}"
    except ValueError:
        res = "REFUSED"
    print(json.dumps({"case": c, "res": res, "s": round(time.time() - T0[0], 1), "diffs (t, d) plain/bl per level": log}), flush=True)
