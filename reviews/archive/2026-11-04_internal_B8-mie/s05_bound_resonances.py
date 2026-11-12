# Review B8-mie, script s05: is the stated coefficient bound (mie.ACCURACY: every a_n, b_n within 2e-11 of the largest
# coefficient for x <= 2e4) justified away from the six (m, x) points the tests use?
# (a) x placed ON narrow resonances (the docs: "the narrow resonances just above n = x ... are ill-conditioned"):
#     for m = 1.333 near x = 1000 the TE resonances b_n of orders n in (x, N] are located (the real denominator part
#     B_n(x) = (m D_n(mx) + n/x) chi_n(x) - chi_{n-1}(x) crosses zero) and the engine is compared there with a
#     40-digit evaluation of the same series (D_n(mx) downward from far above, Miller's psi, upward chi).
# (b) strongly absorbing and large |m| at large x, not in the tests.
import math
import sys
import time

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie  # noqa: E402


def ref(m, x, N, dps=40):
    with mp.workdps(dps):
        m = mp.mpc(m)
        x = mp.mpf(x)
        mx = m * x
        top = N + int(abs(complex(mx))) + 60
        D = mp.mpc(0)
        Dm = [None] * (N + 1)
        Dx = mp.mpf(0)
        Dxs = [None] * (N + 2)
        for n in range(top, 0, -1):
            if n <= N:
                Dm[n] = D
            if n <= N + 1:
                Dxs[n] = Dx
            D = n / mx - 1 / (D + n / mx)
            Dx = n / x - 1 / (Dx + n / x)
        P = [mp.mpf(0)] * (N + 1)
        P[N] = mp.mpf(1)
        for n in range(N, 0, -1):
            P[n - 1] = P[n] * (Dxs[n] + n / x)
        s = mp.sin(x)
        p1 = s / x - mp.cos(x)
        sc = s / P[0] if abs(s) >= abs(p1) else p1 / P[1]
        P = [p * sc for p in P]
        X = [mp.cos(x)]
        prev = -mp.sin(x)
        for n in range(1, N + 1):
            X.append((2 * n - 1) / x * X[-1] - prev)
            prev = X[-2]
        a, b = [], []
        for n in range(1, N + 1):
            xi, xi1 = P[n] - 1j * X[n], P[n - 1] - 1j * X[n - 1]
            ta, tb = Dm[n] / m + n / x, Dm[n] * m + n / x
            a.append(complex((ta * P[n] - P[n - 1]) / (ta * xi - xi1)))
            b.append(complex((tb * P[n] - P[n - 1]) / (tb * xi - xi1)))
        return np.array(a), np.array(b)


def B_of(m, x, n):
    """The real part of the TE denominator's imaginary component (double): its zero is a resonance."""
    D = mie.log_derivative(np.array([m * x]), n)[n, 0]
    X = mie.chi(np.array([x]), n)[1:, 0]
    return (m * D + n / x) * X[n] - X[n - 1]


print("(a) m = 1.333, TE resonances of orders n in (x, N] between x = 1000 and 1001")
m = 1.333
xs = np.linspace(1000.0, 1001.0, 4001)
N0 = mie.n_terms(1001.0)
D = mie.log_derivative(m * xs, N0)            # (N0+1, len(xs))
X = mie.chi(xs, N0)[1:]                       # chi_0..chi_N0
found = []
for n in range(1001, N0 + 1):
    Bn = (m * D[n] + n / xs) * X[n] - X[n - 1]
    k = np.nonzero(np.sign(Bn[:-1]) != np.sign(Bn[1:]))[0]
    for j in k:
        if abs(Bn[j]) > 1e3 or abs(Bn[j + 1]) > 1e3:   # a pole of D (psi_n(mx) = 0), not a resonance
            continue
        lo, hi = xs[j], xs[j + 1]
        flo = B_of(m, lo, n)
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if mid in (lo, hi):
                break
            fm = B_of(m, mid, n)
            if np.sign(fm) == np.sign(flo):
                lo, flo = mid, fm
            else:
                hi = mid
        found.append((n, lo))
print(f"  {len(found)} TE resonances located; checking up to 10 of them")
worst = 0.0
for n, xr in found[:10]:
    t0 = time.time()
    a, b = mie.coefficients(m, xr)
    ra, rb = ref(m, xr, len(a))
    s = max(np.abs(ra).max(), np.abs(rb).max())
    e_all = max(np.abs(a - ra).max(), np.abs(b - rb).max()) / s
    e_n = abs(b[n - 1] - rb[n - 1]) / s
    # width of the resonance in x: |b_n| = 1/2 at B = +-A, so Gamma ~ 2|A| / |dB/dx|
    h = 1e-9
    dB = (B_of(m, xr + h, n) - B_of(m, xr - h, n)) / (2 * h)
    worst = max(worst, e_all)
    print(f"  n = {n}, x = {xr!r}: |b_n| = {abs(rb[n - 1]):.6f}, |dB/dx| = {abs(dB):.2e}; engine error at b_n "
          f"{e_n:.2e}, over all orders {e_all:.2e} of the largest  -> within 2e-11: {e_all <= 2e-11}  ({time.time() - t0:.0f} s)")
print(f"  worst over the resonances checked: {worst:.2e}")

print("\n(b) large |m| and strong absorption at large x (all orders against 40 digits)")
for m, x in [(10 + 10j, 1000.0), (1.5 + 1.0j, 3000.0), (4.0 + 0.01j, 1000.0), (1.5 + 1e-4j, 3000.0), (0.5, 3000.0),
             (1.05, 3000.0)]:
    t0 = time.time()
    a, b = mie.coefficients(m, x)
    ra, rb = ref(m, x, len(a))
    s = max(np.abs(ra).max(), np.abs(rb).max())
    e = max(np.abs(a - ra).max(), np.abs(b - rb).max()) / s
    print(f"  m = {m}, x = {x:g}: max error {e:.2e} of the largest coefficient -> within 2e-11: {e <= 2e-11} "
          f"({time.time() - t0:.0f} s)")
