"""v06: which alpha_s(M_Z) (with the preset «strong»'s other values and the found combination's) make the world refuse
with the raw "RG integration failed". The integration itself (lfphys.core.qcd.running) is called directly for speed."""
import sys
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry
registry.ensure_path()
import numpy as np
from lfphys.core.qcd import running
from lfphys.core import data
import v06_qcd.viz as V
mus = np.geomspace(V.MU_MIN, V.MU_MAX, 160)
bad = {}
for loops in (1, 2, 3, 4):
    for a in np.round(np.arange(0.11, 0.3001, 0.005), 4):
        for aa in (a, a - data.ALPHA_S_MZ[1], a + data.ALPHA_S_MZ[1]):
            for m in mus:
                try:
                    running.alpha_s(m, aa, data.M_Z[0], V.THRESH, loops)
                except running.LandauPole:
                    pass
                except Exception as ex:
                    bad.setdefault((loops, float(a)), f"{type(ex).__name__}: {ex} (alpha_mz used {aa:.4f}, mu {m:.3g})")
                    break
for k, v in sorted(bad.items()):
    print(k, v)
print("n bad (loops, alpha_mz):", len(bad))
