"""Review B8 (slit): cost and accuracy of the two bases for a thin screen at v02's cap (two slits, k a = 129, d = 60/13 a,
lambda = 0.6328 um as in v02): 'auto' (waveguide modes beyond k a = 40) against the edge basis (its default count and
+20 modes)."""
import math
import sys
import time

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import slit as S  # noqa: E402

lam = 0.6328
K = 2 * math.pi
a, d = 13.0 / lam, 60.0 / lam
for pol in ("TE", "TM"):
    t0 = time.time()
    sa = S.solve(K, [-d / 2, d / 2], a, 0.0, pol)
    ta = time.time() - t0
    t0 = time.time()
    se = S.solve(K, [-d / 2, d / 2], a, 0.0, pol, method="edge")
    te = time.time() - t0
    se2 = S.solve(K, [-d / 2, d / 2], a, 0.0, pol, modes=se.modes[0] + 20, method="edge")
    print(f"{pol}: auto = {sa.method} ({sa.modes[0]} modes) T = {sa.transmission():.7f} in {ta:.1f} s; edge ({se.modes[0]}) "
          f"T = {se.transmission():.7f} in {te:.1f} s; edge (+20) T = {se2.transmission():.7f}; auto error "
          f"{sa.transmission() / se2.transmission() - 1:+.1e}")
