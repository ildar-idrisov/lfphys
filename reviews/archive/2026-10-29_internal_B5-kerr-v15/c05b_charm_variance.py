# Review B5, check c05b: the variance of the shadow's diameters (chords through the centre, 64 orientations) at the
# module's centre (midpoint of the extreme alpha) and at the centre that minimises it (CHARM's step iv), for the Kerr
# curve a = 0.5, theta_o = 30 deg; and the median radius at both. Root and run as c02 (see its header).
import math

import numpy as np

from lfphys.core.gravity import kerr_null as KN
from lfphys.theories.alternatives import johannsen_metric as JP

cur = KN.critical_curve(0.5, math.radians(30), 1441)
al, be = np.asarray(cur["alpha"]), np.asarray(cur["beta"])
al2, be2 = np.append(al, al[0]), np.append(be, be[0])
ang = 2 * math.pi * np.arange(128) / 128
print(f"alpha range [{al.min():.6f}, {al.max():.6f}], beta range [{be.min():.6f}, {be.max():.6f}]")
for cx in (0.5 * (al.max() + al.min()), 0.7, 0.974):
    r = np.array([JP._radius_at(al2, be2, cx, t) for t in ang])
    d = r[:64] + r[64:]
    print(f"centre {cx:.4f}: variance of the diameters {np.var(d):.2e}; median radius {np.median(r):.6f}; radii "
          f"{r.min():.4f} .. {r.max():.4f}")
