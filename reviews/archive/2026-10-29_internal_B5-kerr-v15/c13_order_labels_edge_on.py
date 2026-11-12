# Review B5, check c13: the image order n near edge-on. kerr_null.trace_back counts equatorial crossings (GL-b's
# m-bar); v15 names n = 1 "the lensing ring, after half an orbit". For an observer slightly off the plane, a ray below
# the line of sight first crosses the plane far out (r ~ |beta|/cos theta_o) and then near the hole: the image of the
# disk's lower face is n = 1; exactly edge-on (|cos theta_o| < 1e-12) the observer's own crossing is skipped and the
# same image is n = 0. Root and run as c02 (see its header).
import math

import numpy as np

from lfphys.core.gravity import kerr_shadow as KS

al = np.array([6.0, -6.5, 3.0, 0.5])
be = np.array([-2.0, -1.5, -4.0, -6.0])
for incl in (75.0, 85.0, 89.0, 89.9, 90.0):
    res = KS.trace_screen(al, be, math.radians(incl) if incl != 90.0 else math.pi / 2, 0.99, 2, "cunningham", True)
    rows = []
    for i in range(al.size):
        rn = ", ".join(f"n{n}: r={res['r_n'][n][i]:.4g}" for n in range(3) if not math.isnan(res["r_n"][n][i]))
        rows.append(f"({al[i]}, {be[i]}): {rn}")
    print(f"incl {incl}: " + " | ".join(rows))
