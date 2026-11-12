"""s08: v16 worlds at the tight corners of the legal parameter space (small w0/lambda), through the harness: which checks
fail or turn into information, and how much of the named LG waist the exact model drops. The exact vector beam keeps
the propagating part of the waist's spectrum only (q <= k, beams.py:208, VortexBeam.theta_max); the fraction of the
waist's power at q > k is int_k^inf |A|^2 q dq / int_0^inf |A|^2 q dq, computed here from lg_waist_spectrum."""
import math
import sys
import time

import numpy as np
from scipy.integrate import quad

for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from harness import Harness  # noqa: E402
from lfphys.core.optics import beams as B  # noqa: E402


def dropped(p, l, w0, lam):
    k = 2 * math.pi / lam
    fn, qmax = B.lg_waist_spectrum(p, l, w0)
    f = lambda q: float(fn(np.array([q]))[0]) ** 2 * q  # noqa: E731
    tot = quad(f, 0, qmax, limit=200)[0]
    return quad(f, k, max(qmax, k), limit=200)[0] / tot if qmax > k else 0.0


for p_, l_, w0, lam in [(0, 1, 0.6, 1.0), (0, 1, 0.3, 1.0), (0, 3, 0.3, 1.0), (3, 6, 0.3, 1.6), (0, 1, 0.3, 1.6)]:
    print(f"LG_{{{p_},{l_}}} w0 = {w0}, lambda = {lam} (w0/lambda = {w0 / lam:.2f}): fraction of the waist's power at q > k "
          f"(dropped by the exact model) = {dropped(p_, l_, w0, lam):.3f}")

worlds = [{"l": 1, "w0": 0.3, "lam": 1.0, "rot": "none"},
          {"l": 6, "p": 3, "w0": 0.3, "lam": 1.6, "rot": "none"},
          {"l": 1, "w0": 0.3, "lam": 1.6, "zspan": 3.0, "rot": "none"},
          {"gen": "spp", "l": 6, "w0": 0.3, "lam": 1.6, "rot": "none"},
          {"gen": "spp", "l": 1, "w0": 0.6, "lam": 1.0, "rot": "none"}]
for prm in worlds:
    t0 = time.time()
    try:
        h = Harness("v16_optical_vortices", None, prm)
    except Exception as e:  # noqa: BLE001
        print(f"=== {prm}: refused/failed at build: {type(e).__name__}: {e}")
        continue
    bad, info = [], []
    for cid, c in h.checks().items():
        if c.get("info"):
            info.append(cid)
        elif c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]):
            bad.append((cid, c["value"], c["ref"], c["tol"]))
    am = h.of("am")[0] if h.of("am") else {}
    print(f"=== {prm}: build {time.time() - t0:.1f} s; errors {h.errors()}")
    print(f"  FAILED checks: {bad}")
    print(f"  information only: {info}")
    print(f"  am: J {am.get('J')}, S {am.get('S')} (ref {am.get('S_ref')}), L {am.get('L')}, miss {am.get('miss')}, "
          f"table_err {h.sim.table_err:.2e}, header approximations {h.of('header')[0]['approximations']}")
