import sys, math
sys.path.insert(0, "/lf/lfphys")
import numpy as np
from scipy import integrate
from lfphys.core.qcd import running as R
from lfphys.core import data
import v06_qcd.viz as V
orig = integrate.solve_ivp
def spy(*a, **k):
    sol = orig(*a, **k)
    if not sol.success:
        print("FAIL", sol.message, "t_span", a[1], "last L", sol.t[-1], "a", sol.y[0,-1], "alpha", 4*math.pi*sol.y[0,-1], "nsteps", sol.t.size)
    return sol
R.integrate.solve_ivp = spy
for m in np.geomspace(V.MU_MIN, V.MU_MAX, 160)[:5]:
    try:
        print(m, R.alpha_s(m, 0.19, data.M_Z[0], V.THRESH, 4))
    except Exception as e:
        print(m, type(e).__name__, e)
