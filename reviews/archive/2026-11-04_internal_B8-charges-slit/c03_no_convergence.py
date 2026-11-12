"""Review B8 (charges): which field points make retarded_time raise 'no convergence' far from the origin."""
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import charges as ch  # noqa: E402
C = ch.C
for beta in (0.5, 0.99):
    w = ch.uniform([0, 0, 0], [beta * C, 0, 0])
    for t in (1e-6, 1e-4, 1e-2, 1.0):
        rp = w.position(np.array(t))
        out = []
        for name, off in (("ahead 2 m", [2.0, 0, 0]), ("behind 2 m", [-2.0, 0, 0]), ("abeam 2 m", [0, 2.0, 0]),
                          ("ahead 0.3 m", [0.3, 0, 0]), ("oblique", [1.0, 0.5, 0.2])):
            try:
                tr = ch.retarded_time(w, (rp + np.array(off))[None], np.array([t]))
                r = w.position(tr)
                res = abs(C * (t - tr[0]) - np.linalg.norm(rp + off - r[0])) / np.linalg.norm(off)
                out.append(f"{name}: ok (|c tau - R|/R = {res:.0e})")
            except Exception as exc:  # noqa: BLE001
                out.append(f"{name}: {type(exc).__name__}")
        print(f"beta = {beta}, t = {t:g} s, |r| = {np.linalg.norm(rp):.2e} m: " + "; ".join(out))
