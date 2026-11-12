"""v17: the cost of one wavelength of the sky (the shortest wavelength, the most nodes and terms) against
n_nodes * N * n_angles, to calibrate a guard (review UX-params P16)."""
import sys, time, math
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry
registry.ensure_path()
import numpy as np
from lfphys.core.optics import mie, mie_poly as MP
import v17_mie_scattering.viz as V
from v17_mie_scattering.engine import drops as DR
for r, w, nm in ((150, 0.02, 1.0), (150, 0.3, 1.0), (150, 0.02, 1.6), (300, 0.1, 1.0), (100, 0.005, 1.0), (500, 0.02, 1.0), (1000, 0.0, 1.0), (1000, 0.02, 1.0)):
    lam = 380.0
    p = {"index": "water", "t_c": 10.0, "n_medium": nm}
    m = DR.index(p, lam)
    nodes = MP.size_nodes(r, w, lam * 1e-3, nm, max_nodes=V.MAX_NODES)
    N = mie.n_terms(float(nodes["x"].max()))
    ang = mie.angular(np.cos(V.SKY_TH), N)
    t0 = time.time()
    if nodes["w"].size * N * len(V.SKY_TH) > 3e10:
        print(f"r={r} w={w} nm={nm}: nodes={nodes['w'].size} N={N} work={nodes['w'].size*N*len(V.SKY_TH):.3g} SKIPPED"); continue
    MP.average(m, lam * 1e-3, nodes, V.SKY_TH, nm, angular=ang)
    dt = time.time() - t0
    work = nodes["w"].size * N * len(V.SKY_TH)
    print(f"r={r} w={w} nm={nm}: nodes={nodes['w'].size} N={N} work={work:.3g} t={dt:.2f}s ns/unit={dt/work*1e9:.3f}", flush=True)
