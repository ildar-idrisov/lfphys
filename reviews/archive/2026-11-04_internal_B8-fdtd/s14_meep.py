# Review B8-fdtd, script s14 (runs in the image light-funnel-ext-meep): the Meep comparison re-run with its own
# functions (tests/external/test_ext_fdtd_meep.py), printing per side: the value at 20 and 40 cells, the Richardson
# bound 2|v40 - v20|/3 the tolerance is built from, and the actual distance to the exact value at 40 cells -- is each
# side's error inside its own bound (the basis of "Richardson x 2 per side")? Also the engine's R re-normalised by the
# monitor's cos(k dx/2) (Meep normalises by its own flux of the incident wave through the same plane).
import argparse
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys/tests/external")
import test_ext_fdtd_meep as T  # noqa: E402
from lfphys.core.em import fdtd as F  # noqa: E402
from lfphys.core.optics import cylinder as cy  # noqa: E402
from lfphys.core.optics.interfaces import stack  # noqa: E402
import meep as mp  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
print("meep", mp.__version__)


def report(name, fs, e, m, ex, fac40=None):
    for i, f in enumerate(fs):
        be = 2 * abs(e[40][i] - e[20][i]) / 3
        bm = 2 * abs(m[40][i] - m[20][i]) / 3
        ee, em = abs(e[40][i] - ex[i]), abs(m[40][i] - ex[i])
        d = abs(e[40][i] - m[40][i])
        extra = ""
        if fac40 is not None:
            extra = f" | engine/cos(k dx/2): err {abs(e[40][i] / fac40[i] - ex[i]):.2e}"
        print(f"  {name} f={f:4.2f}: exact {ex[i]:.6f} | eng {e[20][i]:.6f} {e[40][i]:.6f} bound {be:.2e} err {ee:.2e}"
              f"{' OUT' if ee > be else ''} | meep {m[20][i]:.6f} {m[40][i]:.6f} bound {bm:.2e} err {em:.2e}"
              f"{' OUT' if em > bm else ''} | diff {d:.2e} tol {be + bm:.2e} ratio {d / (be + bm):.2f}{extra}")


drude_eng = F.Medium(poles=[F.Drude(2.0, 0.1)])
drude_meep = mp.Medium(epsilon=1.0, E_susceptibilities=[mp.DrudeSusceptibility(frequency=2.0, gamma=0.1, sigma=1.0)])
for name, me, mm, slab in (("slab", F.Medium(eps=4.0), mp.Medium(index=2.0), True),
                           ("drude", drude_eng, drude_meep, False)):
    e = {r: T._engine_1d(r, me, slab) for r in T.RES}
    m = {r: T._meep_1d(r, mm, slab) for r in T.RES}
    if slab:
        ex = np.array([stack([1.0, 2.0, 1.0], [0.5], 1.0 / f, 0.0, "s")["R"] for f in T.FS_1D])
    else:
        n = np.sqrt(drude_eng.epsilon(T.FS_1D) + 0j)
        ex = np.abs((1 - n) / (1 + n)) ** 2
    report(name, T.FS_1D, e, m, ex, fac40=np.cos(2 * np.pi * T.FS_1D / 40 / 2))
for pol in ("tm", "te"):
    e = {r: T._engine_cyl(r, pol) for r in T.RES}
    m = {r: T._meep_cyl(r, pol) for r in T.RES}
    ex = np.array([cy.efficiencies(1.5, 2 * np.pi * f * 0.5, pol)["Qsca"] for f in T.FS_CYL])
    report(f"cyl {pol}", T.FS_CYL, e, m, ex)
