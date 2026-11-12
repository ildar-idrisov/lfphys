"""Review check 07b: the near-field map on its own grid (fresnel.near_field_map: z log-spaced from 2a, x = xi w(z))
against the exact 2-D RS integral column by column (both normalised per column to max, as drawn)."""
import math
import numpy as np
from v02_double_slit.engine import fresnel, rs
for lab, lam, a, d in [("photon_young (a=20um, d=100um)", 632.8e-9, 20e-6, 100e-6),
                       ("photon a=3um, d=15um", 632.8e-9, 3e-6, 15e-6)]:
    k = 2 * math.pi / lam
    slits = [-d / 2, d / 2]
    G = np.ones((2, 2), complex)
    mp = fresnel.near_field_map(k, slits, a, math.inf, G, 1.0)
    zs, xi, w = mp["z"], mp["xi"], mp["w"]
    out = []
    for iz in (0, 13, 26, 52, 78, 104, 130, 182, 259):
        X = xi * w[iz]
        U = rs.slit_fields(X, zs[iz], k, slits, a, math.inf)
        Prs = np.abs(U.sum(axis=0)) ** 2
        Prs /= Prs.max()
        dev = float(np.max(np.abs(Prs - mp["I"][iz])))
        frac = math.log(zs[iz] / zs[0]) / math.log(zs[-1] / zs[0])
        out.append(f"z = {zs[iz]:.2e} m ({zs[iz] / a:7.1f} a, {100 * frac:4.1f} % of the map width): max|dev| = {dev:.3f}")
    print(lab)
    for o in out:
        print("   " + o)
