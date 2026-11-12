"""Review B8 (charges): the 200 random points of c01 at t = 1 s (uniform motion, beta = 0.99): which fail alone."""
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import charges as ch  # noqa: E402
C = ch.C
rng = np.random.default_rng(5)
w = ch.uniform([0, 0, 0], [0.99 * C, 0, 0])
t = 1.0
rp = w.position(np.array(t))
pts = rp + rng.normal(size=(400, 3))
bad = []
for i, p in enumerate(pts):
    try:
        ch.retarded_time(w, p[None], np.array([t]))
    except RuntimeError:
        bad.append(i)
print(f"{len(bad)} of {len(pts)} points fail alone; their distances to the present position (m):",
      np.round(np.linalg.norm(pts[bad] - rp, axis=1), 3))
d = pts - rp
cosang = d[:, 0] / np.linalg.norm(d, axis=1)
print("cos(angle to v) of failing points:", np.round(cosang[bad], 3))
for i in bad[:3]:
    for mi in (200, 2000, 20000):
        try:
            tr = ch.retarded_time(w, pts[i][None], np.array([t]), max_iter=mi)
            print(f"point {i}: converges with max_iter = {mi}")
            break
        except RuntimeError:
            print(f"point {i}: no convergence with max_iter = {mi}")
