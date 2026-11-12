# Review B8-fdtd, script s07c: the stability check's cache is keyed by (id(Medium), dt) (fdtd.py:707-709, 723).
# A Medium checked once and then freed leaves its id in the cache; CPython reuses the address for the next object of
# the same size, so a new, different Medium can skip the check. Pattern: a set-up edited live, each edit a new Medium
# (as a GUI slider would create), e.g. the body's permittivity stepped down 2.0 -> 0.3 (n = 0.55: the 2-D limit at
# S = 0.6 is 0.707 x 0.55 = 0.39, so eps = 0.3 must be refused).
import argparse
import numpy as np
from lfphys.core.em import fdtd as F

argparse.ArgumentParser(description=__doc__).parse_args()
accepted = 0
trials = 200
for t in range(trials):
    w = F.FDTD((1.0, 1.0), 0.05, courant=0.6)
    bid = w.add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=2.0))
    w.update_body(bid, medium=F.Medium(eps=1.5))    # the eps=2.0 Medium is freed here (checked, cached by id)
    try:
        w.update_body(bid, medium=F.Medium(eps=0.3))  # a new object; may get the freed object's address
        accepted += 1
        if accepted == 1:
            w.set_field("ez", lambda x, y: np.exp(-((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.005))
            try:
                w.advance(512)
                print(f"  first acceptance (trial {t}): after 512 steps max|Ez| = {np.abs(w.field('ez')).max():.3e}")
            except F.Unstable as e:
                print(f"  first acceptance (trial {t}): the run blew up: {str(e)[:90]}")
    except F.Unstable:
        pass
print(f"unstable Medium(eps=0.3) accepted in {accepted} of {trials} trials")
w = F.FDTD((1.0, 1.0), 0.05, courant=0.6)
try:
    w.add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=0.3))
    print("control: accepted in a fresh world (unexpected)")
except F.Unstable:
    print("control: a fresh world refuses Medium(eps=0.3) at S = 0.6")
