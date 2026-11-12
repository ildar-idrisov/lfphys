import sys, math
import numpy as np
from lfphys.core.qcd import running as R
from lfphys.core import data
TH = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
print(TH)
orig = R._evolve
def ev(a0, L0, L1, nf, loops):
    print("  evolve start alpha", 4*math.pi*a0, "mu0", math.exp(0.5*L0), "->", math.exp(0.5*L1), "nf", nf)
    return orig(a0, L0, L1, nf, loops)
R._evolve = ev
try:
    print(R.alpha_s(1.0, 0.19, data.M_Z[0], TH, 4))
except Exception as e:
    print(type(e).__name__, e)
