"""Review B8 (slit): the TM resonance numbers and their dependence on the number of modes; Rayleigh's limits at v02's
check threshold k a = 0.3; the 'auto' switch between the edge basis and the waveguide modes at k w = 40.
Lengths in wavelengths (k = 2 pi)."""
import math
import sys

import numpy as np
from scipy import optimize

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import slit as S  # noqa: E402

K = 2 * math.pi
G = S.EULER_GAMMA


def peak(w, lo, hi, M):
    r = optimize.minimize_scalar(lambda d: -S.solve(K, [0.0], [w], d, "TM", modes=M).transmission(),
                                 bounds=(lo, hi), method="bounded", options={"xatol": 1e-7})
    return -r.fun, r.x


print("== TM resonance of a narrow slit in a thick screen (m = 1) ==")
for w in (0.02, 0.05):
    for M in (8, 16, 32, 64):
        Tp, dp = peak(w, 0.3, 0.5, M)
        h = w / (2 * dp)
        d_hs = 0.5 * (1 + 4 * h / math.pi * (math.log(h) + math.log(2) + G - 1))
        d_tk = 0.5 * (1 + 4 * h / math.pi * (math.log(h) + math.log(math.pi) - 1.5))
        print(f"w = {w}: M = {M:2d}: peak T = {Tp:.5f} (lambda/(pi w) = {1 / (math.pi * w):.5f}, rel {Tp * math.pi * w - 1:+.1e});"
              f" d_peak = {dp:.5f}; H-S (34) {d_hs:.5f}, Takakura (35) {d_tk:.5f}; shift 0.5 - d: engine "
              f"{0.5 - dp:.5f}, H-S {0.5 - d_hs:.5f}, Takakura {0.5 - d_tk:.5f}")


def circuit(w, d):
    z = 1 / (w * (math.pi - 2j * math.log(1.781 * K * w / 8)))
    Z = -1 / (2 / z * math.cos(K * d) + 1j * (1 + z ** -2) * math.sin(K * d))
    return 4 * abs(Z) ** 2 * (1 / z).real


print("\n-- against Harrington & Auckland's circuit (8-4), (8-7), (8-8), w = 0.02 --")
for d in (0.1, 0.25, 0.45, 0.6):
    for M in (8, 32):
        T = S.solve(K, [0.0], [0.02], d, "TM", modes=M).transmission()
        print(f"d = {d}: M = {M}: engine {T:.5f}, circuit {circuit(0.02, d):.5f}, ratio - 1 = {T / circuit(0.02, d) - 1:+.2e}")

print("\n-- Qi et al. (22) T0 = 0.0096 + 0.3183 s --")
for s in (55.0, 100.0, 260.0):
    Tp, dp = peak(1 / s, 0.42, 0.5, 8)
    print(f"s = {s:g}: engine peak {Tp:.4f}, Qi {0.0096 + 0.3183 * s:.4f}, s/pi {s / math.pi:.4f}; engine - s/pi = "
          f"{Tp - s / math.pi:+.4f}")

print("\n== Rayleigh's narrow-slit limits (thin screen) ==")
for ka in (0.02, 0.1, 0.2, 0.3):  # v02 checks at k a < 0.3 with tolerance 0.05
    for pol in ("TE", "TM"):
        T = S.solve(K, [0.0], [ka / K], 0.0, pol).transmission()
        R = S.rayleigh_narrow_transmission(K, ka / K, pol)
        print(f"k a = {ka}: {pol}: engine/Rayleigh - 1 = {T / R - 1:+.3e}")

print("\n== the 'auto' switch at k w = 40 (thin screen) ==")
for kw in (10.0, 39.9, 40.1, 60.0):
    w = kw / K
    for pol in ("TE", "TM"):
        auto = S.solve(K, [0.0], [w], 0.0, pol)
        ref = S.solve(K, [0.0], [w], 0.0, pol, modes=max(60, int(kw / 2 + 30)), method="edge").transmission()
        print(f"k w = {kw}: {pol}: auto = {auto.method} with {auto.modes[0]} modes, T = {auto.transmission():.7f}; "
              f"edge reference {ref:.7f}; error {auto.transmission() / ref - 1:+.1e}")
