# Reviewer's follow-up: the dye's second moment (variance per axis about the centre) across a diffusive refinement,
# against the exact S0^2 + 2 D t. A transfer that mis-scales the dye's flux shows as a jump of the variance that never
# decays (diffusion only adds 2 D t). Run in Docker from engine/.
import sys
import numpy as np
sys.path[:0] = ["/out", "/lf/lfphys"]
import lbm_dye_check as M  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core.fluids import lbm  # noqa: E402

backend.configure(None)


def var(fl):
    C = fl.dye()
    X = fl._X - 0.5 * M.L
    return float(np.sum(C * X * X) / np.sum(C))


variants = {"engine": lbm, "kgm = 1": M.variant("one", "1.0"), "kgm = kgp": M.variant("kgp", "kgp")}
M.S0 = 2.5
co = M.flow(lbm, 1.0, 1.0)
print("variance minus exact (S0^2 + 2 D t), D = 0.02, S0 = 2.5; the remap at t = 101 (one coarse step), dx 1 -> 0.5")
co.advance(101)
print(f"  coarse alone at t = 101: {var(co) - (M.S0 ** 2 + 2 * M.D * co.t):+.4e}")
co.advance(200)
print(f"  coarse alone at t = 301: {var(co) - (M.S0 ** 2 + 2 * M.D * co.t):+.4e}")
fi = M.flow(lbm, 0.5, 0.25)
fi.advance(404)
print(f"  fine alone   at t = 101: {var(fi) - (M.S0 ** 2 + 2 * M.D * fi.t):+.4e}")
fi.advance(800)
print(f"  fine alone   at t = 301: {var(fi) - (M.S0 ** 2 + 2 * M.D * fi.t):+.4e}")
for name, Lm in variants.items():
    fl = M.flow(Lm, 1.0, 1.0)
    fl.advance(100)
    fl.remap(dx=0.5, dt=0.25)
    h = [var(fl) - (M.S0 ** 2 + 2 * M.D * fl.t)]
    for k in range(4):
        fl.advance(200)
        h.append(var(fl) - (M.S0 ** 2 + 2 * M.D * fl.t))
    print(f"  [{name:9s}] t = 101, 151, 201, 251, 301: " + ", ".join(f"{x:+.4e}" for x in h))
