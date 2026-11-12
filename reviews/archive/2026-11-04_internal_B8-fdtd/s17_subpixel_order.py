# Review B8-fdtd, script s17: the convergence order of the engine's sub-pixel averaging on a curved surface.
# The engine keeps only the diagonal of Farjadpour et al.'s tensor (eq. (1)), i.e. the VP-EP scheme, which
# Farjadpour et al. (Opt. Lett. 31, 2972 (2006)) list among the schemes that "do not satisfy the perturbation
# criterion for diagonal interfaces" and "are therefore expected to have only linear convergence in general".
# Dielectric cylinder (a = 0.5) Q_sca at one frequency against core.optics.cylinder, 20/40/80/160 cells per unit;
# the monitor's normalization bias (s09 (5)) is second order and is reported apart (Q re-normalised by cos(k dx/2)).
import argparse
import math
import numpy as np
from lfphys.core.em import fdtd as F
from lfphys.core.optics import cylinder as cy
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--res", default="20,40,80,160")
args = ap.parse_args()
a = 0.5
fs = np.array([0.6, 0.8])
for eps in (2.25, 6.0):
    for pol in ("te", "tm"):
        ex = np.array([cy.efficiencies(math.sqrt(eps), 2 * np.pi * f * a, pol)["Qsca"] for f in fs])
        prev = None
        for res in [int(r) for r in args.res.split(",")]:
            w = F.FDTD((3.2, 3.2), 1.0 / res, pol=pol, pml=max(12, res // 2))
            prof = F.ModulatedGaussian(0.7, fwidth=0.15)
            w.add_source(F.PlaneWave(prof, ((0.6, 0.6), (2.6, 2.6)), direction=0.0))
            w.add_body(F.Cylinder((1.6, 1.6), a), F.Medium(eps=eps))
            sca = w.add_flux(((0.4, 0.4), (2.8, 2.8)), freqs=fs)
            w.advance(int((prof.end() + 30) / w.dt))
            q = w.cross_sections(sca)["sigma_sca"] / (2 * a)
            err = q / ex - 1
            err_n = q / np.cos(2 * np.pi * fs / res / 2) / ex - 1
            r = "" if prev is None else f"  ratio to previous {np.round(prev / err, 2)}"
            print(f"  eps {eps} {pol} {res:4d} cells/unit: Q/Q_exact - 1 = {np.round(err, 6)}; "
                  f"re-normalised {np.round(err_n, 6)}{r}", flush=True)
            prev = err
