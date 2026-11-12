# Review B5, check c01: core.elliptic beyond the tests' ranges (|u| <= 20): sn, cn, dn for |u| up to 1e3 and m up to
# 1 - 1e-15, and m down to -1e6; F(phi|m) for |phi| up to 1e3 and m -> 1; R_F with arguments spanning 1e-200..1e200.
# Reference: mpmath at 40 digits. Reported: the largest error against the tests' stated bounds (sn/cn/dn absolute
# 128 u (1 + |u|); for m < 0 times (1 - m) at |v| = |u| sqrt(1 - m); F: 64 u |F| + 4 u |phi| max(1, 1/sqrt(1 - m)); R_F 32 u).
# Root and run as c02 (see its header).
import math

import mpmath as mp
import numpy as np

from lfphys.core import elliptic as EL

mp.mp.dps = 40
U = 2.0 ** -53
rng = np.random.default_rng(5)
print("== sn, cn, dn ==")
for m in (0.5, 0.99, 1 - 1e-6, 1 - 1e-10, 1 - 1e-13, 1 - 1e-15, -10.0, -1e3, -1e6):
    u = np.concatenate((rng.uniform(-1000, 1000, 40), [999.123, -731.5, 123.456]))
    sn, cn, dn = EL.ellipj(u, np.full_like(u, m))
    worst = 0.0
    for name, got in (("sn", sn), ("cn", cn), ("dn", dn)):
        ref = np.array([float(mp.re(mp.ellipfun(name, mp.mpf(x), m=mp.mpf(m)))) for x in u])
        if m >= 0:
            bound = 128 * U * (1 + np.abs(u))
        else:
            v = np.abs(u) * math.sqrt(1 - m)
            bound = 128 * U * (1 + v) * (1 - m)
        worst = max(worst, float(np.max(np.abs(got - ref) / bound)))
    print(f"m = {m!r}: max |error| / stated bound = {worst:.3g}")
print("== F(phi|m) ==")
for m in (0.3, 0.999, 1 - 1e-9, 1 - 1e-13, -1e4):
    phi = np.concatenate((rng.uniform(-1000, 1000, 30), [math.pi / 2 - 1e-9, 1.5707963]))
    F = EL.ellipf(phi, np.full_like(phi, m))
    ref = np.array([float(mp.ellipf(mp.mpf(p), mp.mpf(m))) for p in phi])
    amp = max(1.0, 1.0 / math.sqrt(1.0 - min(m, 1 - 1e-300))) if m < 1 else 1.0
    bound = 64 * U * np.abs(ref) + 4 * U * np.abs(phi) * amp
    print(f"m = {m!r}: max |error| / stated bound = {float(np.max(np.abs(F - ref) / bound)):.3g}")
print("== R_F ==")
x = 10.0 ** rng.uniform(-200, 200, 200)
y = 10.0 ** rng.uniform(-200, 200, 200)
z = 10.0 ** rng.uniform(-200, 200, 200)
got = EL.rf(x, y, z)
ref = np.array([float(mp.elliprf(mp.mpf(a), mp.mpf(b), mp.mpf(c))) for a, b, c in zip(x, y, z)])
ok = np.isfinite(got)
print(f"finite {int(ok.sum())}/200; max rel error / 32u = {float(np.max(np.abs(got[ok] / ref[ok] - 1)) / (32 * U)):.3g}")
