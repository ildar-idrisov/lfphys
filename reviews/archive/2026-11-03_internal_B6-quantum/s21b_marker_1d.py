"""The which-path preset's marker as a 1-D slab (transfer matrices, as the engine's marker test): c = 0.18 rad/fs, the
region 3 nm long with the wrapper's default edge, an electron of lambda = 2 nm (and the longitudinal k inside a 2-nm
slit, sqrt(k^2 - (pi/2)^2)): the marker's P(1) of the transmitted wave and its turning angle, and the reflection of the
two marker components (|+y> sees +c, |-y> sees -c)."""
import math
import numpy as np
from lfphys.core.quantum import scene as Q, transfer
from p02_quantum import viz as P

c = 0.18 / P.FS
w = 1.05 * Q.edge_min(80 / 256)
e = Q.edge_eps(w)
z = np.linspace(-1.5 - 8 * e, 1.5 + 8 * e, 8001)
f = Q.smooth_interval(0.5 * (z[1:] + z[:-1]), -1.5, 1.5, w)
for k in (math.pi, math.sqrt(math.pi**2 - (math.pi / 2) ** 2)):
    E = np.array([k * k / 2])
    tp, rp = transfer.staircase_amplitudes(E, (c * f)[None, :], z[1] - z[0])
    tm, rm = transfer.staircase_amplitudes(E, (-c * f)[None, :], z[1] - z[0])
    P1 = float(np.abs(tp - tm)[0] ** 2 / 4)
    P0 = float(np.abs(tp + tm)[0] ** 2 / 4)
    print(f"k = {k:.3f}: c = {c:.3f} units ({c * P.EV:.3f} eV) vs E = {k * k / 2 * P.EV:.3f} eV; transmitted marker "
          f"P(1) = {P1 / (P0 + P1):.3f} (angle {math.degrees(math.asin(math.sqrt(P1 / (P0 + P1)))):.0f} deg); "
          f"R of |+y>, |-y>: {abs(rp[0]) ** 2:.3f}, {abs(rm[0]) ** 2:.3f}")
