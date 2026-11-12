# The dye's second moment across a refinement (review LB1-physics P12): engine, the rescaling switched off, coarse alone.
import sys
import numpy as np
sys.path[:0] = ["/lf/lfphys"]
from lfphys.core import backend
from lfphys.core.fluids import lbm
backend.configure(None)
L, NU, D, S0 = 32.0, 0.1, 0.02, 2.5
PER = {s: "periodic" for s in lbm.SIDES}
def flow(dx, dt):
    fl = lbm.Flow2D((L, L), dx, nu=NU, rho=1.0, dt=dt, sides=PER, device="cpu", dye=D)
    X, Y = fl._X - 0.5 * L, fl._Y - 0.5 * L
    C = np.exp(-(X * X + Y * Y) / (2 * S0 * S0))
    fl._g = np.ascontiguousarray(np.array(lbm.WG)[:, None, None] * C[None])
    return fl
def off(fl):
    C = fl.dye(); X = fl._X - 0.5 * L
    return float(np.sum(C * X * X) / np.sum(C)) - (S0 * S0 + 2 * D * fl.t)
for flag in (True, False):
    lbm.REMAP_NEQ_RESCALE = flag
    fl = flow(1.0, 1.0); fl.advance(100)
    fl.remap(dx=0.5, dt=0.25)
    h = [off(fl)]
    for k in range(4):
        fl.advance(200); h.append(off(fl))
    print("rescale", flag, " ".join(f"{x:+.5e}" for x in h))
lbm.REMAP_NEQ_RESCALE = True
co = flow(1.0, 1.0); co.advance(101); h = [off(co)]
for k in range(4):
    co.advance(50); h.append(off(co))
print("coarse alone", " ".join(f"{x:+.5e}" for x in h))
fi = flow(0.5, 0.25); fi.advance(404); h = [off(fi)]
for k in range(4):
    fi.advance(200); h.append(off(fi))
print("fine alone", " ".join(f"{x:+.5e}" for x in h))
