"""r01: the engine's Fermi-Dirac integrals F(y), J(y) on a dense grid against 40-digit mpmath (independent quadrature
with break points at the branch-point scale y), and the two asymptotic statements of the docstring.

Run (from engine/):
  docker run --rm --name lf-b7rc-r01 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r01_fermi_dirac_sweep.py
"""
import math
import sys

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.cosmology import flrw as F  # noqa: E402

mp.mp.dps = 40
I0 = 7 * mp.pi ** 4 / 120


def ref(y):
    y = mp.mpf(y)
    pts = sorted({mp.mpf(0)} | {v for v in (y / 8, y / 2, y, 2 * y, 8 * y) if 0 < v < 60}
                 | {mp.mpf(v) for v in (0.5, 1, 2, 4, 8, 16, 32, 64)})
    pts = pts + [mp.inf]
    e = mp.quad(lambda x: x ** 2 * mp.sqrt(x * x + y * y) / (mp.exp(x) + 1), pts)
    p = mp.quad(lambda x: x ** 4 / mp.sqrt(x * x + y * y) / (mp.exp(x) + 1) if x > 0 else mp.mpf(0), pts)
    return e / I0, p / (3 * I0)


ys = np.concatenate([[0.0], np.geomspace(1e-10, 1e8, 181), [2.5, 9.9, 357.0, 357.3]])
Fe = F.fermi_dirac_energy(ys)
Je = F.fermi_dirac_pressure(ys)
worstF = worstJ = 0.0
argF = argJ = None
for y, fe, je in zip(ys, Fe, Je):
    rf, rj = ref(float(y))
    ef, ej = abs(fe / float(rf) - 1), abs(je / float(rj) - 1)
    if ef > worstF:
        worstF, argF = ef, y
    if ej > worstJ:
        worstJ, argJ = ej, y
print(f"grid: {ys.size} values of y in [0, 1e8]")
print(f"max |F_engine/F_mp - 1| = {worstF:.3e} at y = {argF:.4g}   (stated bound FD_REL_ERROR = {F.FD_REL_ERROR:.0e};"
      f" docstring 'measured below 2e-15')")
print(f"max |J_engine/J_mp - 1| = {worstJ:.3e} at y = {argJ:.4g}")

# small-y statement: F = 1 + 5 y^2/(7 pi^2) + O(y^4 ln y)
print("\nsmall y: (F - 1 - 5y^2/(7pi^2)) / (y^4 ln y)   [should approach a constant]")
for y in (1e-1, 3e-2, 1e-2, 3e-3, 1e-3):
    rf, _ = ref(y)
    r = (rf - 1 - 5 * mp.mpf(y) ** 2 / (7 * mp.pi ** 2)) / (mp.mpf(y) ** 4 * mp.log(y))
    print(f"  y = {y:7.0e}: {float(r): .6f}")

# large-y statement: w = J/F -> 5 zeta(5)/(zeta(3) y^2)
print("\nlarge y: w y^2 / (5 zeta5/zeta3) - 1")
for y in (30.0, 100.0, 357.0, 1e3, 1e4):
    rf, rj = ref(y)
    print(f"  y = {y:7.0f}: {float(rj / rf * y * y / (5 * mp.zeta(5) / mp.zeta(3)) - 1): .3e}")
print("\ny0 of a 0.06 eV species in the engine's (CAMB) convention, T_cmb = 2.7255, N_eff = 3.046:",
      0.06 / (F.K_B_EV * (3.046 / 3) ** 0.25 * F.T_NU_RATIO * 2.7255))
