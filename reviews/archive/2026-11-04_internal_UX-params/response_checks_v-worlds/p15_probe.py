import sys, math
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/visualizations/tests")
from lfviz import registry
registry.ensure_path()
from harness import Harness
import numpy as np
orig = None
def run(preset, vals, sets):
    h = Harness("v02_double_slit", preset=preset, params=vals)
    def diag(tag):
        s = h.sim
        Gf = s.Gavg
        print(f"  {tag}: g11={Gf[0,0].real:.3g} g22={Gf[1,1].real:.3g} |g12|={abs(Gf[0,1]):.3g} gamma_exp={getattr(s,'gamma_expected',None)}")
    diag("start")
    for st in sets:
        h.set(**st); diag(str(st))
    c = h.checks()
    print("  coh:", {k: (round(v['value'],4) if v['value'] is not None else None, v['ref'], v.get('ok')) for k, v in c.items() if k.startswith('coh')})
    print("  errors", h.errors())
print("302"); run(None, {"el1": "polarizer", "el2": "polarizer", "el1_angle": 0.0, "el2_angle": 90.0}, [])
print("379"); run("photon_eraser", {}, [{"pol_state": "H"}, {"pol_state": "V"}, {"pol_state": "D"}])
print("436"); run("photon_eraser", {}, [{"el1": e} for e in ("none", "polarizer", "hwp", "qwp")])
print("437"); run("photon_eraser_minus", {}, [{"el1": e} for e in ("none", "polarizer")])
print("372"); run("c60_grw", {}, [{"species": "custom"}, {"mass_u": 1e-6}, {"mass_u": 1e9}, {"mass_u": 1.0}])
