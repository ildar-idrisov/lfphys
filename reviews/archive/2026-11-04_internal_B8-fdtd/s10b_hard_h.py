# Review B8-fdtd, script s10b: the hard magnetic source away from the magic step. 2-D, S = 0.5, a hard point source of
# a Gaussian pulse: Ez (TM) against its dual Hz (TE) (same grid, the TE source at an Hz node); in vacuum the two
# problems are dual, so |Hz(TE)| at a probe must equal |Ez(TM)| at the mirror probe (eta = 1).
import argparse
import numpy as np
from lfphys.core.em import fdtd as F
argparse.ArgumentParser(description=__doc__).parse_args()
dx = 0.05
out = {}
for pol in ("tm", "te"):
    w = F.FDTD((4.0, 4.0), dx, pol=pol, pml=12, courant=0.5)
    comp = "ez" if pol == "tm" else "hz"
    o = 0.0 if pol == "tm" else dx / 2
    prof = F.GaussianPulse(0.15)
    w.add_source(F.CurrentSource(comp, prof, position=(2.0 + o, 2.0 + o), hard=True))
    pid = w.add_probe((2.8 + o, 2.0 + o), [comp])
    try:
        w.advance(240)
        out[pol] = w.probe(pid)[comp]
        print(f"  hard {comp}: probe peak {np.abs(out[pol]).max():.6f} (source peak 1)")
    except F.Unstable as e:
        print(f"  hard {comp}: {e}")
if len(out) == 2:
    print(f"  max |Hz(TE) - Ez(TM)| / peak = {np.max(np.abs(out['te'] - out['tm'])) / np.abs(out['tm']).max():.3e}")
