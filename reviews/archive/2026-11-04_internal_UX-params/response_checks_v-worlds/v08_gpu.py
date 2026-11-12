"""P26 on GPU 0 (the owner's server runs v08's kernels there, «авто»): the time of the refused circle (defaults) and of
the accepted circle preset."""
import sys, time
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry
registry.ensure_path()
from lfphys.core import backend as B
print("backend", B.settings())
import v08_wave_3d.viz as V
for vals in ({"source": "circle"}, {"source": "circle", "a": 3.0, "zmax": 40.0}):
    p = V.SCHEMA.resolve(None, vals)[0]
    t0 = time.time()
    try:
        V.Simulation(p, 1, lambda *a: None); res = "built"
    except ValueError as e:
        res = "refused: " + str(e)[:90]
    print(vals, res, f"{time.time() - t0:.1f} s", "used", B.used().get("optics.angular_spectrum"), flush=True)
