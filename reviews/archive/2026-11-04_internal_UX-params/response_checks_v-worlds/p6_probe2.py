import math, numpy as np, mpmath as mp
from lfphys.theories.alternatives import johannsen_metric as JP
dev = JP.Deviation(-3.0, -1.399, 3.612)
for chi in (0.0, 0.9):
    try:
        co = JP.circular_orbits(chi, dev)
        print(chi, co)
    except Exception as e:
        print(chi, type(e).__name__, e)
# second route at the existence edge (a = 0): Omega^2 = -g_tt'/g_phiphi' = 0  <=>  g_tt' = 0 ; static orbit E = sqrt(-g_tt)
co = JP.circular_orbits(0.0, dev)
with mp.workdps(40):
    a12, a13 = mp.mpf(-3.0), mp.mpf(-1.399)
    gtt = lambda r: -(1 - 2/r) / (1 + a12/r**2 + a13/r**3)**2
    r0 = mp.findroot(lambda r: mp.diff(gtt, r), co["isco_pro"])
    print("mp edge", r0, "E", mp.sqrt(-gtt(r0)))
