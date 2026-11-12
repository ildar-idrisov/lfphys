import math, numpy as np
from lfphys.theories.alternatives import johannsen_metric as JP
dev = JP.Deviation(-3.0, -1.399, 3.612)
chi = 0.0
print("margins", JP.regularity_margins(chi, dev))
for pro in (True, False):
    for r in (2.05, 2.2, 2.5, 3, 3.5, 4, 5, 6, 8, 10, 15):
        (gtt, gtp, gpp), (dtt, dtp, dpp) = JP._equatorial_metric(r, chi, dev)
        disc = dtp*dtp - dtt*dpp
        om, norm, E, L = JP._circular(r, chi, dev, pro)
        print(pro, r, "disc %.3g" % disc, "norm", norm, "E", E)
    break
try:
    print(JP.circular_orbits(chi, dev))
except Exception as e:
    print(type(e).__name__, e)
try:
    print(JP.nonspinning_shadow(dev))
except Exception as e:
    print(type(e).__name__, e)
