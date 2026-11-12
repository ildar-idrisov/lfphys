import sys, math
import numpy as np
from scipy import integrate
from lfphys.core.qcd import running as R
orig = integrate.solve_ivp
def spy(*a, **k):
    sol = orig(*a, **k)
    if not sol.success:
        print("FAIL", sol.message, sol.t_events, "last t", sol.t[-6:], "alpha", 4*math.pi*sol.y[0,-6:])
    return sol
R.integrate.solve_ivp = spy
for aMZ in (0.185, 0.19, 0.195):
    for m in (1.0, 1.5, 2.0):
        try:
            print(aMZ, m, R.alpha_s(m, aMZ, 91.1876, {"c": 1.27, "b": 4.18, "t": 162.5}, 4))
        except Exception as e:
            print(aMZ, m, type(e).__name__, e)
