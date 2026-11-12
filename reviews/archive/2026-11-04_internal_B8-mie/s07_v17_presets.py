# Review B8-mie, script s07: v17 presets through visualizations/tests/harness.py (no server), 16 wavelengths as the
# README's "measured on the presets": every check (value, ref, tol, ok), the p = 2/3 maxima and Airy's, the luminance
# maxima of the white-light sky (local maxima of Y over 125-180 deg), the wall time of the world's construction and of
# the whole sky.
import json
import sys
import time

import numpy as np
from scipy.signal import argrelmax

for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from harness import Harness  # noqa: E402
from v17_mie_scattering.viz import SKY_DEG, T_LAM  # noqa: E402

presets = sys.argv[1:] or ["rainbow", "supernumerary", "fogbow", "glory", "near", "absorbing"]
for preset in presets:
    t0 = time.time()
    h = Harness("v17_mie_scattering", preset, {"n_lam": 16} if preset not in ("near",) else None)
    t_build = time.time() - t0
    t1 = time.time()
    h.run_to(h.sim.sky_n * T_LAM + 0.01)
    t_sky = time.time() - t1
    mono = h.of("mono")[-1]
    print(f"\n=== {preset}: x = {mono['x']:.1f} at {mono['lam_nm']} nm, m = {mono['m']}, N = {mono['n_terms']}, "
          f"n_fine = {mono['n_fine']}; build {t_build:.1f} s, sky ({h.sim.sky_n} wavelengths) {t_sky:.1f} s; errors {h.errors()}")
    print(f"  Descartes/Airy: {json.dumps(mono['bows'])}; measured Debye maxima {mono['measured']}")
    for cid, c in sorted(h.checks().items()):
        v, r = c.get("value"), c.get("ref")
        st = "info" if c.get("info") else ("ok" if (c.get("ok") if c.get("ok") is not None else (c.get("rel") is None or abs(c["rel"]) <= c["tol"])) else "FAIL")
        vs = f"{v:.6g}" if isinstance(v, (int, float)) else str(v)
        rs = f"{r:.6g}" if isinstance(r, (int, float)) else str(r)
        print(f"  check {cid}: value {vs} ref {rs} tol {c.get('tol')} [{st}]")
    skies = [b for m, b in h.msgs if m.get("type") == "sky"]
    sm = [m for m, b in h.msgs if m.get("type") == "sky"]
    if skies:
        Y = skies[-1]["Y"].astype(float)
        mx = argrelmax(Y, order=3)[0]
        print(f"  sky: nodes per wavelength {[m['n_nodes'] for m in sm]}, coarse {[m['coarse'] for m in sm if m['coarse']]}")
        print(f"  luminance maxima (deg, Y/Ymax): {[(round(float(SKY_DEG[k]), 1), round(float(Y[k]), 3)) for k in mx]}")
        bow = (SKY_DEG > 132) & (SKY_DEG < 145)
        print(f"  brightest angle 132-145 deg: {SKY_DEG[bow][np.argmax(Y[bow])]:.1f}; brightest over 125-180: "
              f"{SKY_DEG[np.argmax(Y)]:.1f}")
