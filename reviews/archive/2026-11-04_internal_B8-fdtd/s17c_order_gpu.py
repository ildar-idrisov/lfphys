# Review B8-fdtd, script s17c (GPU 0): the convergence order of the cylinder Q_sca for a high-contrast cylinder
# (eps = 6, a = 0.5), runs long enough for the field to have decayed (the window of s17 was too short for eps = 6,
# s17b), sub-pixel (the engine's diagonal averaging) against staircase. TE: the in-plane E needs the off-diagonal
# elements that the engine drops; TM: E_z is tangential everywhere, so the diagonal is the full tensor.
import argparse
import math
import time
import numpy as np
from lfphys.core import backend
from lfphys.core.em import fdtd as F
from lfphys.core.optics import cylinder as cy
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--pol", default="te")
ap.add_argument("--res", default="40,80,160,320")
ap.add_argument("--extra", type=float, default=60.0)
ap.add_argument("--modes", default="subpixel,staircase")
args = ap.parse_args()
backend.configure({"kernels": {F.KERNEL: {"device": "gpu"}}})
a = 0.5
fs = np.array([0.5, 0.6, 0.8])
pol = args.pol
ex = np.array([cy.efficiencies(math.sqrt(6.0), 2 * np.pi * f * a, pol)["Qsca"] for f in fs])
for mode in args.modes.split(","):
    prev = None
    for res in [int(r) for r in args.res.split(",")]:
        t0 = time.time()
        w = F.FDTD((3.2, 3.2), 1.0 / res, pol=pol, pml=max(16, res // 2), averaging=mode, device="auto")
        prof = F.ModulatedGaussian(0.7, fwidth=0.15)
        w.add_source(F.PlaneWave(prof, ((0.6, 0.6), (2.6, 2.6)), direction=0.0))
        w.add_body(F.Cylinder((1.6, 1.6), a), F.Medium(eps=6.0))
        sca = w.add_flux(((0.4, 0.4), (2.8, 2.8)), freqs=fs)
        w.advance_to(prof.end() + args.extra)
        q = w.cross_sections(sca)["sigma_sca"] / (2 * a)
        err = q / ex - 1
        r = "" if prev is None else f"  ratio {np.round(prev / err, 2)}"
        print(f"  {pol} eps 6 {mode:9s} {res:4d} cells/unit ({w.device}, {time.time() - t0:.0f} s): "
              f"Q/Q_exact - 1 = {np.round(err, 6)}{r}", flush=True)
        prev = err
backend.configure({})
