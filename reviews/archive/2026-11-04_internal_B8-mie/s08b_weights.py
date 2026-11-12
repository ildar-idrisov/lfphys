# Review B8-mie, script s08b: numpy's leggauss docstring on high degrees, and scipy's roots_legendre weights near
# mu = 1 against 40-digit weights (same Newton refinement as s08), n = 1120.
import sys
import numpy as np, scipy
from scipy.special import roots_legendre
sys.path.insert(0, "/out")
doc = np.polynomial.legendre.leggauss.__doc__
print("numpy", np.__version__, "leggauss docstring:", [l.strip() for l in doc.splitlines() if "tested" in l or "problematic" in l])
import mpmath as mp


def refine(n, mu0):
    out_mu, out_w = [], []
    with mp.workdps(40):
        for x0 in mu0:
            x = mp.mpf(float(x0))
            for _ in range(3):
                p0, p1 = mp.mpf(1), x
                for k in range(2, n + 1):
                    p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
                dp = n * (x * p1 - p0) / (x * x - 1)
                x = x - p1 / dp
            p0, p1 = mp.mpf(1), x
            for k in range(2, n + 1):
                p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
            dp = n * (x * p1 - p0) / (x * x - 1)
            out_mu.append(x)
            out_w.append(2 / ((1 - x * x) * dp * dp))
    return out_mu, out_w


n = 1120
mu_s, w_s = roots_legendre(n)
idx = np.argsort(mu_s)[-6:]
mu_r, w_r = refine(n, mu_s[idx])
print("scipy", scipy.__version__, "roots_legendre(1120) near mu = 1: weight rel errors",
      [f"{abs(w_s[i] / float(w_r[k]) - 1):.1e}" for k, i in enumerate(idx)],
      "node errors", [f"{abs(mu_s[i] - float(mu_r[k])):.1e}" for k, i in enumerate(idx)])
mu_n, w_n = np.polynomial.legendre.leggauss(n)
idn = np.argsort(mu_n)[-6:]
mu_r2, w_r2 = refine(n, mu_n[idn])
print("numpy leggauss(1120) near mu = 1: weight rel errors", [f"{abs(w_n[i] / float(w_r2[k]) - 1):.1e}" for k, i in enumerate(idn)])
