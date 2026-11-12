# Review B8-mie, script s05b: all TE resonances of s05 (m = 1.333, x in [1000, 1001], orders n in (x, N]): the
# engine's error on each peak against 40 digits, the resonance's width Gamma (b_n = A/(A - iB): |b_n| = 1/2 at
# |B| = sqrt(3)|A|, so the full width at half power is Gamma = 2|A|/|dB/dx|), and the change of the EXACT b_n when x
# moves by one unit in the last place (40-digit values at x and at nextafter(x)). If the engine's error is of that
# size, the engine behaves backward-stably and its forward error is the problem's conditioning (~ x/Gamma times eps),
# which no fixed bound like 2e-11 covers.
import sys

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie  # noqa: E402


def ref_b(m, x, n, dps=40):
    """b_n alone by the 40-digit recurrences (as s05's ref)."""
    with mp.workdps(dps):
        m = mp.mpc(m)
        x = mp.mpf(x)
        mx = m * x
        top = n + int(abs(complex(mx))) + 60
        D = mp.mpc(0)
        Dx = mp.mpf(0)
        Dm = Dxs = None
        Dxlist = {}
        for k in range(top, 0, -1):
            if k == n:
                Dm = D
            if k <= n + 1:
                Dxlist[k] = Dx
            D = k / mx - 1 / (D + k / mx)
            Dx = k / x - 1 / (Dx + k / x)
        P = {n: mp.mpf(1)}
        for k in range(n, 0, -1):
            P[k - 1] = P[k] * (Dxlist[k] + k / x)
        s = mp.sin(x)
        p1 = s / x - mp.cos(x)
        sc = s / P[0] if abs(s) >= abs(p1) else p1 / P[1]
        X = [mp.cos(x)]
        prev = -mp.sin(x)
        for k in range(1, n + 1):
            X.append((2 * k - 1) / x * X[-1] - prev)
            prev = X[-2]
        pn, pn1 = P[n] * sc, P[n - 1] * sc
        xi, xi1 = pn - 1j * X[n], pn1 - 1j * X[n - 1]
        tb = Dm * m + n / x
        return complex((tb * pn - pn1) / (tb * xi - xi1))


def AB(m, x, n):
    D = mie.log_derivative(np.array([m * x]), n)[n, 0]
    P = mie.psi(np.array([x]), n)[:, 0]
    X = mie.chi(np.array([x]), n)[1:, 0]
    tb = m * D + n / x
    return tb * P[n] - P[n - 1], tb * X[n] - X[n - 1]


m = 1.333
xs = np.linspace(1000.0, 1001.0, 4001)
N0 = mie.n_terms(1001.0)
D = mie.log_derivative(m * xs, N0)
X = mie.chi(xs, N0)[1:]
found = []
for n in range(1001, N0 + 1):
    Bn = (m * D[n] + n / xs) * X[n] - X[n - 1]
    for j in np.nonzero(np.sign(Bn[:-1]) != np.sign(Bn[1:]))[0]:
        if abs(Bn[j]) > 1e3 or abs(Bn[j + 1]) > 1e3:
            continue
        lo, hi = xs[j], xs[j + 1]
        flo = AB(m, lo, n)[1]
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if mid in (lo, hi):
                break
            fm = AB(m, mid, n)[1]
            if np.sign(fm) == np.sign(flo):
                lo, flo = mid, fm
            else:
                hi = mid
        found.append((n, lo))
print(f"m = {m}: {len(found)} TE resonances in x = [1000, 1001], orders up to N = {N0}")
print(" n     x_res                 Gamma(x)   err_engine  |b(x+ulp)-b(x)| exact   eps*x/Gamma")
for n, xr in found:
    A, _ = AB(m, xr, n)
    h = 1e-7
    dB = (AB(m, xr + h, n)[1] - AB(m, xr - h, n)[1]) / (2 * h)
    gam = 2 * abs(A) / abs(dB)
    a, b = mie.coefficients(m, xr)
    if n > len(b):
        print(f" {n}: beyond the engine's trimmed series ({len(b)} terms)")
        continue
    rb = ref_b(m, xr, n)
    rb2 = ref_b(m, float(np.nextafter(xr, 2e3)), n)
    s = 1.0  # the largest coefficient is ~1 (b_n on its peak)
    print(f" {n}  {xr!r:22s} {gam:9.2e}  {abs(b[n - 1] - rb) / s:9.2e}   {abs(rb2 - rb):9.2e}            "
          f"{np.finfo(float).eps * xr / gam:9.2e}")
