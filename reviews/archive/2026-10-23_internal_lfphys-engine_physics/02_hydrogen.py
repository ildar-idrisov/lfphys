"""02: hydrogen levels of lfphys.core.quantum.hydrogen against the measured 1S-2S frequency.

Reference: Parthey et al., PRL 107, 203001 (2011), arXiv:1107.3101, abstract (fetched 2026-10-23):
"f_1S-2S = 2 466 061 413 187 035 (10) Hz for the hyperfine centroid".
The module docstring claims: "Transition frequencies from these formulas therefore differ from measured ones at the
1e-6 level" and ABOUT.validity "отличие от измерений ~1e-6 отн.". We test each function as shipped, and an
independent Dirac + leading-recoil (Barker-Glover) evaluation in mpmath to show what 1e-6 needs.
Usage: python3 02_hydrogen.py
"""
import argparse

argparse.ArgumentParser(description=__doc__).parse_args()

import mpmath as mp
from scipy import constants as sc

from lfphys.core.quantum import hydrogen as Hy

F_MEAS = 2466061413187035.0  # Hz, hyperfine centroid, Parthey 2011

# (a) Schroedinger with the reduced mass (shipped)
fa = Hy.frequency(Hy.schrodinger_level(1), Hy.schrodinger_level(2))
# (b) Dirac, infinite nuclear mass (shipped)
fb = Hy.frequency(Hy.dirac_level(1, 0.5), Hy.dirac_level(2, 0.5))

# (c) independent: Dirac with recoil to leading order (Barker & Glover 1955; Eides, Grotch, Shelyuto, Phys. Rep. 342,
# 63 (2001), Eq. (2.5)): E = mu c^2 (f - 1) - mu^2 c^2 (f - 1)^2 / (2 (m + M)), f the Dirac factor.
mp.mp.dps = 40
a = mp.mpf(sc.fine_structure)
me, mpr = mp.mpf(sc.m_e), mp.mpf(sc.m_p)
c = mp.mpf(sc.c)
mu = me * mpr / (me + mpr)


def fdirac(n, j):
    d = (j + mp.mpf(1) / 2) - mp.sqrt((j + mp.mpf(1) / 2) ** 2 - a * a)
    return 1 / mp.sqrt(1 + (a / (n - d)) ** 2)


def e_recoil(n, j):
    f = fdirac(n, j)
    return mu * c**2 * (f - 1) - mu**2 * c**2 * (f - 1) ** 2 / (2 * (me + mpr))


fc = float((e_recoil(2, mp.mpf(1) / 2) - e_recoil(1, mp.mpf(1) / 2)) / mp.mpf(sc.h))

print(f"measured 1S-2S (hyperfine centroid)        {F_MEAS:.6e} Hz")
for lab, f in (("(a) schrodinger_level, reduced mass", fa), ("(b) dirac_level, infinite mass", fb),
               ("(c) independent Dirac + recoil (mpmath)", fc)):
    print(f"{lab:42s} {f:.6e} Hz   rel. diff {f / F_MEAS - 1:+.3e}")
print("\n(c) differs from the measurement by the 1S/2S Lamb shift (~8.2 GHz -> ~3e-6), i.e. the documented ~1e-6 level")
print("is reachable only with the reduced mass AND the Dirac factor together; neither shipped function does both.")

# fine structure 2P3/2 - 2P1/2 (measured ~10969 MHz) -- the infinite-mass Dirac value
fs = Hy.frequency(Hy.dirac_level(2, 0.5), Hy.dirac_level(2, 1.5))
fs_c = float((e_recoil(2, mp.mpf(3) / 2) - e_recoil(2, mp.mpf(1) / 2)) / mp.mpf(sc.h))
print(f"\n2P3/2-2P1/2: dirac_level (inf. mass) {fs / 1e6:.2f} MHz; with recoil {fs_c / 1e6:.2f} MHz "
      f"(ratio {fs / fs_c - 1:+.2e} ~ m_e/m_p = {sc.m_e / sc.m_p:.2e})")
