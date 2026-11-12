# Review B8-fdtd, script s17b: is the eps = 6 cylinder (m = 2.45, a = 0.5) error at f = 0.8 in s17 the run's time
# window (a resonance ringing beyond the DFT window) rather than the solver? Q_sca at 40 cells per unit with the run
# extended, and the field at a probe near the cylinder at the end of each window.
import argparse
import math
import numpy as np
from lfphys.core.em import fdtd as F
from lfphys.core.optics import cylinder as cy
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--res", type=int, default=40)
args = ap.parse_args()
a = 0.5
fs = np.array([0.6, 0.8])
for pol in ("tm", "te"):
    ex = np.array([cy.efficiencies(math.sqrt(6.0), 2 * np.pi * f * a, pol)["Qsca"] for f in fs])
    w = F.FDTD((3.2, 3.2), 1.0 / args.res, pol=pol, pml=20)
    prof = F.ModulatedGaussian(0.7, fwidth=0.15)
    w.add_source(F.PlaneWave(prof, ((0.6, 0.6), (2.6, 2.6)), direction=0.0))
    w.add_body(F.Cylinder((1.6, 1.6), a), F.Medium(eps=6.0))
    sca = w.add_flux(((0.4, 0.4), (2.8, 2.8)), freqs=fs)
    c = "ez" if pol == "tm" else "hz"
    pid = w.add_probe((1.6, 2.2), [c])
    t_end = prof.end()
    for extra in (30, 60, 120, 240):
        w.advance_to(t_end + extra)
        q = w.cross_sections(sca)["sigma_sca"] / (2 * a)
        tail = np.abs(w.probe(pid)[c][-int(5 / w.dt):]).max()
        peak = np.abs(w.probe(pid)[c]).max()
        print(f"  {pol} eps 6, {args.res} cells/unit, run to pulse end + {extra:3d}: Q/Q_exact - 1 = "
              f"{np.round(q / ex - 1, 5)}; |field| in the last 5 time units / peak = {tail / peak:.1e}", flush=True)
