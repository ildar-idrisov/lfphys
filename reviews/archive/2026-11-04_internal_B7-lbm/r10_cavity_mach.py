"""R10: the Ghia cavity test says the remaining difference (0.005 u, 0.008 v of the lid speed, the same on 64^2 to 256^2)
is "the difference from Ghia's 129^2 solution itself". All its grids run at the same lattice Mach number 0.1, so the
compressibility error O(Ma^2) does not shrink with the grid either. Here: the same comparison on 64^2 and 128^2 at
Ma = 0.1, 0.05 (and 0.025 on 64^2), and the change of the centre-line profiles with Ma alone.

Run (from engine/): docker run --rm --name lf-b7rl-r10 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys:/lf/lfphys/tests -w /lf/lfphys light-funnel-viz python3 /out/r10_cavity_mach.py
"""
import numpy as np

from lfphys.core.fluids import lbm
from test_lbm_benchmarks import GHIA_U100, GHIA_V100, GHIA_X, GHIA_Y


def cavity(N, mach, T=25.0):
    fl = lbm.Flow2D((1.0, 1.0), 1.0 / N, nu=0.01, rho=1.0, u_max=1.0, mach=mach, tau_max=None,
                    sides={"top": lbm.Wall(1.0)}, device="cpu")
    fl.advance_to(T)
    ux, uy = fl.velocity()
    i = N // 2
    ucol = 0.5 * (ux[i - 1] + ux[i])
    vrow = 0.5 * (uy[:, i - 1] + uy[:, i])
    ye = np.concatenate([[0.0], fl.y, [1.0]])
    u = np.interp(GHIA_Y, ye, np.concatenate([[0.0], ucol, [1.0]]))
    v = np.interp(GHIA_X, ye, np.concatenate([[0.0], vrow, [0.0]]))
    return u, v, fl.tau_p


res = {}
for N, mach in ((64, 0.1), (64, 0.05), (64, 0.025), (128, 0.1), (128, 0.05)):
    u, v, tau = cavity(N, mach)
    res[(N, mach)] = (u, v)
    du, dv = np.abs(u - GHIA_U100)[1:-1], np.abs(v - GHIA_V100)[1:-1]
    print("N = %3d, Ma = %.3f (tau+ = %.4f): max |u - Ghia| = %.4f at y = %.4f, max |v - Ghia| = %.4f at x = %.4f" % (
        N, mach, tau, du.max(), GHIA_Y[1:-1][du.argmax()], dv.max(), GHIA_X[1:-1][dv.argmax()]))
for N in (64, 128):
    a, b = res[(N, 0.1)], res[(N, 0.05)]
    print("N = %d: change of the profiles from Ma 0.1 to 0.05: max |du| = %.4f, max |dv| = %.4f" % (
        N, np.abs(a[0] - b[0]).max(), np.abs(a[1] - b[1]).max()))
a, b = res[(64, 0.05)], res[(64, 0.025)]
print("N = 64: change from Ma 0.05 to 0.025: max |du| = %.4f, max |dv| = %.4f" % (np.abs(a[0] - b[0]).max(),
                                                                               np.abs(a[1] - b[1]).max()))
