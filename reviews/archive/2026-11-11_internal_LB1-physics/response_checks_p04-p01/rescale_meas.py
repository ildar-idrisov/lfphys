import sys
sys.path[:0] = ["/lf/lfphys"]
import numpy as np
from lfphys.core.gravity import kerr_newman as KNW
def two():
    g = KNW.Geodesics(0.6, 0.2)
    g.add_body(7.0, 1.3, 0.2, v=[0.05, 0.02, 0.33])
    g.add_body(9.0, 1.6, 1.0, v=[-0.1, 0.0, 0.25])
    g.add_photon(12.0, 1.4, 0.0, n=[1.0, 0.1, 0.05], key="ray")
    g.advance(20.0)
    return g
a, b = two(), two()
tau0 = a.proper_time(); f = 0.37
b.rescale_proper_time(f)
a.advance(60.0); b.advance(60.0)
print("bl", np.max(np.abs(b.bl() - a.bl())) / np.max(np.abs(a.bl())))
print("p", np.max(np.abs(b.momenta() - a.momenta())) / np.max(np.abs(a.momenta())))
d = (b.proper_time() - f * tau0) - (a.proper_time() - tau0)
print("tau", np.max(np.abs(d)) / np.max(np.abs(a.proper_time())), a.status())
