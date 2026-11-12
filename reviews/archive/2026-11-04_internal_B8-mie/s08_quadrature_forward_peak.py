# Review B8-mie, script s08: v17's README and STATUS record an unexplained 2e-9 (x = 500) - 2e-8 (x = 1700) deviation
# of Q_sca by Gauss-Legendre quadrature in mu = cos(theta) from the series (transparent drop), "cause not found".
# Hypothesis tested here: the forward peak |S(theta)|^2 ~ x^4 varies on a scale delta mu ~ 1/x^2 near mu = 1, so the
# quadrature needs the nodes near mu = 1 to absolute accuracy far below 1/x^2; numpy's leggauss nodes there are off by
# several ulp. Test: (1) the same sum with nodes and weights refined to 40 digits (Newton on P_n in mpmath, nodes then
# rounded to double), amplitudes still from the engine; (2) the nodes' errors near mu = 1.
import sys
import time

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie  # noqa: E402


def refine(n, mu0):
    """Gauss-Legendre nodes (from numpy's guesses) and weights refined by Newton's method in 40 digits."""
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


for x in (100.0, 500.0):
    t0 = time.time()
    m = 1.333
    a, b = mie.coefficients(m, x)
    N = len(a)
    q = mie.efficiencies_from(a, b, x)
    n = 2 * N + 20
    mu, w = np.polynomial.legendre.leggauss(n)
    S1, S2 = mie.amplitudes(a, b, np.arccos(mu))
    I = np.abs(S1) ** 2 + np.abs(S2) ** 2
    q_np = float(w @ I) / x ** 2
    mu_r, w_r = refine(n, mu)
    mu_d = np.array([float(v) for v in mu_r])
    w_d = np.array([float(v) for v in w_r])
    S1r, S2r = mie.amplitudes(a, b, np.arccos(mu_d))
    Ir = np.abs(S1r) ** 2 + np.abs(S2r) ** 2
    q_ref = float(w_d @ Ir) / x ** 2
    # amplitudes evaluated at mu directly (no arccos -> cos round trip), via the angular functions of mu
    PI, TAU = mie.angular(mu_d, N)
    c = (2 * np.arange(1, N + 1) + 1) / (np.arange(1, N + 1) * (np.arange(2, N + 2)))
    s1 = (a * c) @ PI + (b * c) @ TAU
    s2 = (a * c) @ TAU + (b * c) @ PI
    q_dir = float(w_d @ (np.abs(s1) ** 2 + np.abs(s2) ** 2)) / x ** 2
    dmu = np.abs(mu - mu_d)
    top = np.argsort(mu_d)[-5:]
    print(f"x = {x:g} (N = {N}, {n} nodes): Q_ext series {q['Qext']:.15f}")
    print(f"  numpy leggauss nodes, engine amplitudes(theta = arccos mu): rel dev {abs(q_np / q['Qext'] - 1):.2e}")
    print(f"  40-digit nodes and weights rounded to double, same amplitudes: rel dev {abs(q_ref / q['Qext'] - 1):.2e}")
    print(f"  40-digit nodes, angular functions evaluated at mu itself:       rel dev {abs(q_dir / q['Qext'] - 1):.2e}")
    print(f"  numpy's node errors: largest {dmu.max():.1e}, at the 5 nodes nearest mu = 1: "
          f"{[f'{v:.1e}' for v in dmu[top]]}; weight rel errors there {[f'{v:.1e}' for v in np.abs(w[top] / w_d[top] - 1)]}; "
          f"1/x^2 = {1 / x ** 2:.1e}  ({time.time() - t0:.0f} s)")
