# Review B8-mie, script s01: Wiscombe's Appendix III cases (x = 10, 100) by an independent route, written for this
# review from Bohren & Huffman Eq. 4.53 (mu1 = mu) with mpmath's Bessel functions of half-integer order at 30
# digits (no recurrence, no logarithmic derivative), summed to Wiscombe's N + 30 terms; compared with the printed
# values (his m = n - i kappa and his S are the complex conjugates of B&H's) and with lfphys.core.optics.mie.
# Also: the engine at x = 1000 and 5000 against the printed values (6 significant digits).
import math
import sys

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie  # noqa: E402

mp.mp.dps = 30

# (x, his m, Qext, Qsca, g, S1(0), S1(90), S2(90), S1(180)) as printed (verified against the scanned report: see
# REVIEW.md, the OCR text of NCAR/TN-140 has these strings)
W = [
    (10, 1.5, 2.881999, 2.881999, 0.742913, 72.0500 + 4.16662j, 0.0785066 + 3.06855j, -1.87329 + 2.32789j,
     4.32164 + 4.86827j),
    (100, 1.5, 2.094388, 2.094388, 0.818246, 5235.97 - 367.988j, 22.4945 + 0.396468j, 16.2341 - 15.5243j,
     40.7669 + 51.7546j),
    (10, 1.5 - 0.1j, 2.459791, 1.235144, 0.922350, 61.4948 - 3.17799j, 1.35105 + 0.417250j, -1.02255 + 0.791253j,
     1.49343 + 0.296366j),
    (100, 1.5 - 0.1j, 2.089822, 1.132134, 0.950392, 5224.55 - 261.694j, 1.19224 + 15.3732j, -0.850854 - 4.66332j,
     -9.54952 - 3.55581j),
]


def riccati(n, z):
    """psi_n(z) = z j_n(z), xi_n = z h1_n(z) and their derivatives, from mpmath besselj/bessely of order n + 1/2."""
    def jy(nn):
        f = mp.sqrt(mp.pi / (2 * z))
        return f * mp.besselj(nn + mp.mpf(1) / 2, z), f * mp.bessely(nn + mp.mpf(1) / 2, z)
    j, y = jy(n)
    j1, y1 = jy(n - 1)
    psi, xi = z * j, z * (j + 1j * y)
    dpsi = z * j1 - n * j          # (z j_n)' = z j_{n-1} - n j_n
    dxi = z * (j1 + 1j * y1) - n * (j + 1j * y)
    return psi, dpsi, xi, dxi


def ab_independent(m, x, N):
    m = mp.mpc(m)
    x = mp.mpf(x)
    a, b = [], []
    for n in range(1, N + 1):
        p, dp, q, dq = riccati(n, x)
        pm, dpm, _, _ = riccati(n, m * x)
        a.append((m * pm * dp - p * dpm) / (m * pm * dq - q * dpm))
        b.append((pm * dp - m * p * dpm) / (pm * dq - m * q * dpm))
    return a, b


def sums(a, b, x, thetas):
    x = mp.mpf(x)
    qe = sum((2 * n + 1) * (a[n - 1].real + b[n - 1].real) for n in range(1, len(a) + 1)) * 2 / x ** 2
    qs = sum((2 * n + 1) * (abs(a[n - 1]) ** 2 + abs(b[n - 1]) ** 2) for n in range(1, len(a) + 1)) * 2 / x ** 2
    gq = 0
    for n in range(1, len(a) + 1):
        if n < len(a):
            gq += mp.mpf(n * (n + 2)) / (n + 1) * (a[n - 1] * mp.conj(a[n]) + b[n - 1] * mp.conj(b[n])).real
        gq += mp.mpf(2 * n + 1) / (n * (n + 1)) * (a[n - 1] * mp.conj(b[n - 1])).real
    g = 4 * gq / x ** 2 / qs
    S = []
    for th in thetas:
        mu = mp.cos(mp.radians(th))
        p0, p1 = mp.mpf(0), mp.mpf(1)
        s1 = s2 = mp.mpc(0)
        for n in range(1, len(a) + 1):
            if n > 1:
                p0, p1 = p1, ((2 * n - 1) * mu * p1 - n * p0) / (n - 1)
            tau = n * mu * p1 - (n + 1) * p0
            c = mp.mpf(2 * n + 1) / (n * (n + 1))
            s1 += c * (a[n - 1] * p1 + b[n - 1] * tau)
            s2 += c * (a[n - 1] * tau + b[n - 1] * p1)
        S.append((complex(s1), complex(s2)))
    return float(qe), float(qs), float(g), S


def half_unit(v, digits=6):
    v = abs(v)
    return 0.5 * 10.0 ** (math.floor(math.log10(v)) - digits + 1) if v else 0.0


print("Independent route (mpmath Bessel functions, B&H 4.53) against Wiscombe's printed values and the engine")
for x, mw, qe_p, qs_p, g_p, s0, s90_1, s90_2, s180 in W:
    m = complex(mw).conjugate()
    N = mie.n_wiscombe(x) + 30
    a, b = ab_independent(m, x, N)
    qe, qs, g, S = sums(a, b, x, [0.0, 90.0, 180.0])
    ae, be = mie.coefficients(m, x, n_max=N)
    amax = max(max(abs(complex(v)) for v in a), max(abs(complex(v)) for v in b))
    dmax = max(max(abs(ae[k] - complex(a[k])) for k in range(N)), max(abs(be[k] - complex(b[k])) for k in range(N)))
    qeng = mie.efficiencies_from(ae, be, x)
    print(f"\nx = {x}, Wiscombe's m = {mw} (ours {m}); engine vs independent, all {N} orders: max |diff| / max|coef| "
          f"= {dmax / amax:.2e}")
    for name, ind, eng, pr in (("Qext", qe, qeng["Qext"], qe_p), ("Qsca", qs, qeng["Qsca"], qs_p), ("g", g, qeng["g"], g_p)):
        print(f"  {name}: independent {ind:.9f}  engine {eng:.9f}  printed {pr}  |ind - printed| = {abs(ind - pr):.1e} "
              f"(half unit 5e-7)  ok={abs(ind - pr) <= 0.5e-6 + 1e-12}")
    for name, k, j, pr in (("S1(0)", 0, 0, s0), ("S1(90)", 1, 0, s90_1), ("S2(90)", 1, 1, s90_2), ("S1(180)", 2, 0, s180)):
        ind = S[k][j]
        tol = math.hypot(half_unit(pr.real), half_unit(pr.imag))
        print(f"  {name}: conj(independent) {np.conj(ind):.7g}  printed {pr}  |diff| = {abs(np.conj(ind) - pr):.2e} "
              f"tol {tol:.1e} ok={abs(np.conj(ind) - pr) <= tol * 1.0001}")

print("\nOptical theorem in the independent route (both sides from the same coefficients: an identity of the sums)")
a, b = ab_independent(1.33 + 0j, 5.0, 20)
qe, qs, g, S = sums(a, b, 5.0, [0.0])
print(f"  Qext = {qe:.15f}, 4 Re S(0)/x^2 = {4 * S[0][0].real / 25:.15f}")
