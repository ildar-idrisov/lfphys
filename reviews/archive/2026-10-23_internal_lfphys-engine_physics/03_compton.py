"""03: Klein-Nishina total cross-section of lfphys.core.quantum.compton.total_cross_section against a 50-digit
mpmath evaluation of the same closed form (and its series), over x = E/mc^2 in [1e-7, 1e3]. The shipped function
switches from a 3-term series to the closed form at x = 1e-4; the closed form cancels ~ (1/x^2) digits.
Usage: python3 03_compton.py
"""
import argparse

argparse.ArgumentParser(description=__doc__).parse_args()

import mpmath as mp
import numpy as np

from lfphys.core.quantum import compton

mp.mp.dps = 50


def sigma_ref(x):
    x = mp.mpf(x)
    lg = mp.log(1 + 2 * x)
    return 2 * mp.pi * ((1 + x) / x**3 * (2 * x * (1 + x) / (1 + 2 * x) - lg) + lg / (2 * x)
                        - (1 + 3 * x) / (1 + 2 * x) ** 2)


R2 = compton.R_E**2
xs = np.geomspace(1e-7, 1e3, 401)
xs = np.unique(np.concatenate([xs, [0.99e-4, 1.0e-4, 1.0001e-4, 1.5e-4, 2e-4, 3e-4, 5e-4, 1e-3]]))
worst = []
for x in xs:
    E = x * compton.ME_C2
    x_eng = E / compton.ME_C2  # the engine's own x (rounding of E)
    val = compton.total_cross_section(E) / R2
    ref = float(sigma_ref(x_eng))
    worst.append((abs(val / ref - 1), x))
worst.sort(reverse=True)
print("largest relative errors (rel, x):")
for r, x in worst[:8]:
    print(f"  {r:.2e} at x = {x:.4g}")
for lo, hi in ((1e-7, 1e-4), (1e-4, 1e-3), (1e-3, 1e-1), (1e-1, 1e3)):
    m = max(r for r, x in worst if lo <= x < hi)
    print(f"max rel. error for x in [{lo:g}, {hi:g}): {m:.2e}")
# the series is sigma_T (1 - 2x + 26/5 x^2 - 133/10 x^3 + ...); its truncation at the switch:
print("3-term series truncation at x = 1e-4: 133/10 x^3 =", 13.3e-12)

# suggested fix: log1p(2x) instead of log(1 + 2x) (the rounding of 1 + 2x is what is amplified)
import math  # noqa: E402


def fixed(x):
    lg = math.log1p(2 * x)
    return 2 * math.pi * ((1 + x) / x**3 * (2 * x * (1 + x) / (1 + 2 * x) - lg) + lg / (2 * x)
                          - (1 + 3 * x) / (1 + 2 * x) ** 2)


for lo, hi in ((1e-4, 1e-3), (1e-3, 1e-1)):
    m = max(abs(fixed(x) / float(sigma_ref(x)) - 1) for x in xs if lo <= x < hi)
    print(f"with log1p: max rel. error for x in [{lo:g}, {hi:g}): {m:.2e}")
