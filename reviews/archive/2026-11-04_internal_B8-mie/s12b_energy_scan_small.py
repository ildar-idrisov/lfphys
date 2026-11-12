# Review B8-mie, script s12b: s12's scan of v17's "energy" check extended to x in [2, 60] (water, 10 C, 550 nm).
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core import data as D  # noqa: E402
from lfphys.core.optics import mie  # noqa: E402
EPS = np.finfo(float).eps
m = complex(float(D.water_index(550.0, 10.0)))
xs = np.linspace(2.0, 60.0, 233)
fails = []
for x in xs:
    a, b = mie.coefficients(m, x)
    N = len(a)
    q = mie.efficiencies_from(a, b, x)
    mu, wq = np.polynomial.legendre.leggauss(2 * N + 20)
    s1, s2 = mie.amplitudes(a, b, np.arccos(mu))
    qs = float(wq @ (np.abs(s1) ** 2 + np.abs(s2) ** 2)) / x ** 2
    rel = abs(qs - q["Qext"]) / q["Qext"]
    if rel > 200 * N * EPS + 1e-12:
        fails.append(round(float(x), 2))
print(f"x in [2, 60]: {len(fails)} of {len(xs)} sizes fail; smallest failing x {min(fails) if fails else None}; failing: {fails[:20]}")
