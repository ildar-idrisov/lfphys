# Review B8-fdtd, script s09b: the leak of a Bloch slab wave with two finite faces (x = 2 and x = 4; y spanned and
# periodic), so that no wave reaches the layers except the leak itself: the scattered-field side x < 2 and x > 4 must
# hold round-off only. The fixed-direction family (2-D box, 30 deg) for comparison; and the slab at k_par = 0.
import argparse
import math
import numpy as np
from lfphys.core.em import fdtd as F
argparse.ArgumentParser(description=__doc__).parse_args()


def leak(pol, f_par, fc=1.2, fw=0.15, both=True):
    dx = 0.05
    w = F.FDTD((6.0, 1.0), dx, pol=pol, boundary={"x": "pml", "y": "periodic"}, pml=16,
               bloch=(0.0, 2 * math.pi * f_par) if f_par else None)
    prof = F.ModulatedGaussian(fc, fwidth=fw)
    hi = 4.0 if both else math.inf
    w.add_source(F.PlaneWave(prof, ((2.0, -math.inf), (hi, math.inf)), direction=0.0))
    c = "ez" if pol == "tm" else "hz"
    x = w.coords(c)[0]
    sf = ((x > 0.2) & (x < 1.8)) | ((x > 4.2) & (x < 5.8))
    tf = (x > 2.2) & (x < 3.8)
    msf = mtf = 0.0
    T = prof.end() + 12
    for _ in range(int(T / w.dt) // 20):
        w.advance(20)
        a = np.abs(w.field(c))
        msf, mtf = max(msf, a[sf].max()), max(mtf, a[tf].max())
    ch = w.checks()["tfsf_1"]
    return msf / mtf, ch["window_tail"], ch["omitted_energy"]


for pol in ("tm", "te"):
    for f_par in (0.0, 0.3, 0.5, 0.6, 0.9):
        try:
            l, tail, om = leak(pol, f_par)
            print(f"  slab {pol} k_par = 2 pi x {f_par}: leak {l:.2e}  (window tail {tail:.1e}, omitted {om:.1e})")
        except ValueError as e:
            print(f"  slab {pol} k_par = 2 pi x {f_par}: refused: {str(e)[:70]}")
    l, tail, om = leak(pol, 0.6, fc=1.2, fw=0.08)
    print(f"  slab {pol} k_par = 2 pi x 0.6, narrower band (fwidth 0.08): leak {l:.2e}  (tail {tail:.1e}, omitted {om:.1e})")
