# Review B8-mie, script s14: the start of D_n(mx) by Hankel's finite sums (mie._start_D uses them where |m x| > N^2,
# i.e. very large |m| at small x); the tests reach this branch only through the perfect-conductor limit at 1e-5.
# All orders against the 40-digit recurrences (D_n downward from far above |mx|).
import sys
import numpy as np
sys.path.insert(0, "/out"); sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie  # noqa: E402
import mpmath as mp


def ref(m, x, N, dps=40):
    with mp.workdps(dps):
        m = mp.mpc(m); x = mp.mpf(x); mx = m * x
        top = N + int(abs(complex(mx))) + 60
        D = mp.mpc(0); Dm = [None] * (N + 1); Dx = mp.mpf(0); Dxs = [None] * (N + 2)
        for n in range(top, 0, -1):
            if n <= N: Dm[n] = D
            if n <= N + 1: Dxs[n] = Dx
            D = n / mx - 1 / (D + n / mx); Dx = n / x - 1 / (Dx + n / x)
        P = [mp.mpf(0)] * (N + 1); P[N] = mp.mpf(1)
        for n in range(N, 0, -1): P[n - 1] = P[n] * (Dxs[n] + n / x)
        s = mp.sin(x); p1 = s / x - mp.cos(x)
        sc = s / P[0] if abs(s) >= abs(p1) else p1 / P[1]
        P = [q * sc for q in P]
        X = [mp.cos(x)]; prev = -mp.sin(x)
        for n in range(1, N + 1):
            X.append((2 * n - 1) / x * X[-1] - prev); prev = X[-2]
        a, b = [], []
        for n in range(1, N + 1):
            xi, xi1 = P[n] - 1j * X[n], P[n - 1] - 1j * X[n - 1]
            ta, tb = Dm[n] / m + n / x, Dm[n] * m + n / x
            a.append(complex((ta * P[n] - P[n - 1]) / (ta * xi - xi1)))
            b.append(complex((tb * P[n] - P[n - 1]) / (tb * xi - xi1)))
        return np.array(a), np.array(b)


for m, x in [(1e5, 0.5), (300 + 300j, 2.0), (2000.0, 0.5), (50 + 1e4j, 0.3)]:
    N = mie.n_terms(x)
    branch = "Hankel" if abs(m * x) > max(N * N, N + 50) else "continued fraction"
    a, b = mie.coefficients(m, x, n_max=N)
    ra, rb = ref(m, x, N)
    s = max(np.abs(ra).max(), np.abs(rb).max())
    e = max(np.abs(a - ra).max(), np.abs(b - rb).max()) / s
    print(f"m = {m}, x = {x}: |mx| = {abs(m * x):.3g}, N = {N}, start by {branch}: max error {e:.2e} of the largest coefficient")

# The 40-digit recurrence above starts D = 0 only ~60 orders above |mx|; for a real |mx| >> N that start may not have
# decayed (the downward recurrence is neutrally stable below |z|). Second reference for m = 1e5, x = 0.5: D_n(mx) from
# mpmath's Bessel functions directly (psi_n = z j_n, D_n = psi_{n-1}/psi_n - n/z), the rest as above.
def ref_bessel(m, x, N, dps=40):
    with mp.workdps(dps):
        m = mp.mpf(m); x = mp.mpf(x); z = m * x
        def psi(n, zz):
            return zz * mp.sqrt(mp.pi / (2 * zz)) * mp.besselj(n + mp.mpf(1) / 2, zz)
        a0, b0 = ref(complex(m), float(x), N)  # psi(x), chi(x) parts reused through the closed form below
        a, b = [], []
        for n in range(1, N + 1):
            Dm = psi(n - 1, z) / psi(n, z) - n / z
            p, p1 = psi(n, x), psi(n - 1, x)
            yv = lambda k: -x * mp.sqrt(mp.pi / (2 * x)) * mp.bessely(k + mp.mpf(1) / 2, x)
            xi, xi1 = p - 1j * yv(n), p1 - 1j * yv(n - 1)
            ta, tb = Dm / m + n / x, Dm * m + n / x
            a.append(complex((ta * p - p1) / (ta * xi - xi1)))
            b.append(complex((tb * p - p1) / (tb * xi - xi1)))
        return np.array(a), np.array(b)


m, x = 1e5, 0.5
N = mie.n_terms(x)
a, b = mie.coefficients(m, x, n_max=N)
ra, rb = ref_bessel(m, x, N)
r2a, r2b = ref(m, x, N)
s = max(np.abs(ra).max(), np.abs(rb).max())
print(f"m = 1e5, x = 0.5 with D_n(mx) from Bessel functions: engine error {max(np.abs(a - ra).max(), np.abs(b - rb).max()) / s:.2e}; "
      f"the recurrence reference's own error {max(np.abs(r2a - ra).max(), np.abs(r2b - rb).max()) / s:.2e}")

# The continued-fraction start for a REAL |mx| well above N (the fraction is summed through its oscillatory part,
# |mx| - N steps): engine against the Bessel-function reference.
for m, x in [(200.0, 1.0), (50.0, 5.0), (30.0, 10.0), (8.0, 60.0)]:
    N = mie.n_terms(x)
    a, b = mie.coefficients(m, x, n_max=N)
    ra, rb = ref_bessel(m, x, N)
    s = max(np.abs(ra).max(), np.abs(rb).max())
    print(f"m = {m}, x = {x}: |mx| = {m * x:g}, N = {N}, start by continued fraction ({m * x - N:.0f} oscillatory steps): "
          f"engine error {max(np.abs(a - ra).max(), np.abs(b - rb).max()) / s:.2e}")
