# Reviewer script (B6 gravity): how long (in the distant observer's time) the playground's shell check of a falling
# body is above its tolerance 10 rtol sqrt(steps) before the capture at r_+ + 1e-4: the preset kerr_orbits' body
# "Падает" (a = 0.9, q = 0, r = 12, phi = 200 deg, ZAMO v_phi = 0.1) and the same with q = 0.4.
import math

import numpy as np

from lfphys.core.gravity import kerr_newman as KN

for chi, q in ((0.9, 0.0), (0.9, 0.4), (0.0, 0.0)):
    g = KN.Geodesics(chi, q, rtol=1e-10, capture_eps=1e-4, r_escape=2e3)
    g.add_body(12.0, math.pi / 2, math.radians(200.0), v=(0.0, 0.0, 0.1), key="f")
    t, first_bad, rows = 0.0, None, []
    while g.status()[0] == "active":
        t += 0.05
        g.advance(t)
        if g.status()[0] != "active":
            break
        c = g.constants()
        n = max(int(c["steps"][0]), 1)
        tol = 10 * g.rtol * math.sqrt(n)
        ratio = abs(c["dmu2"][0]) / tol
        dr = g.bl()[0, 0] - g.r_plus
        if ratio > 1 and first_bad is None:
            first_bad = (t, dr)
        rows.append((t, dr, ratio))
    t_cap = g.info("f")["t"]
    print(f"a = {chi}, q = {q}: captured at t = {t_cap:.3f} M (r_+ = {g.r_plus:.6f});", end=" ")
    if first_bad is None:
        print("the shell check never exceeds its tolerance")
    else:
        print(f"the shell check fails from t = {first_bad[0]:.2f} M (r - r_+ = {first_bad[1]:.2e}) until the capture: "
              f"{t_cap - first_bad[0]:.2f} M of world time")
    for tt, dr, ratio in rows[::max(1, len(rows) // 12)][-8:]:
        print(f"    t = {tt:8.2f} M  r - r_+ = {dr:.3e}  |dmu2| / tol = {ratio:.3g}")
