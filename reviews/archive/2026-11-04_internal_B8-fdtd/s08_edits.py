# Review B8-fdtd, script s08: edits at a running moment.
# The docstring (fdtd.py lines 52-59): "a polarization is kept at nodes that keep the same medium, starts from 0 at
# nodes that become dispersive and is dropped where a dispersive medium leaves". _build_materials compares the node's
# *index into the rebuilt media list* (fdtd.py:981-983), not the medium itself.
# (1) update_body(medium=<another dispersive medium>) keeps the old medium's polarization at the same nodes;
# (2) removing an earlier body shifts the indices: an unchanged dispersive body loses its polarization;
# (3) the 1/2 delta_eps |E|^2 claim (trivially true for E kept); the field energy with a lossless Lorentz pole.
import argparse

import numpy as np

from lfphys.core.em import fdtd as F

argparse.ArgumentParser(description=__doc__).parse_args()


def world():
    w = F.FDTD((2.0, 2.0), 0.05, pol="tm", pml=8)
    w.add_source(F.CurrentSource("ez", F.ModulatedGaussian(1.0, fwidth=0.3), position=(1.0, 1.0)))
    return w


print("== (1) update_body with a different dispersive medium ==")
w = world()
A = F.Medium(poles=[F.Lorentz(2.0, 1.0, 0.1)], label="A")
B = F.Medium(poles=[F.Drude(3.0, 0.5)], label="B (Drude)")
bid = w.add_body(F.Box((1.2, 0.6), (1.6, 1.4)), A)
w.advance(120)
P_A = w.disp["ez"]["P"].copy()
idx_A = w.disp["ez"]["idx"].copy()
w.update_body(bid, medium=B)
P_after = w.disp["ez"]["P"]
same_nodes = np.array_equal(w.disp["ez"]["idx"], idx_A)
print(f"  nodes unchanged: {same_nodes}; |P| of medium A before: {np.abs(P_A).max():.4e}; "
      f"|P| carried into the Drude pole of B: {np.abs(P_after).max():.4e}; "
      f"identical arrays: {np.array_equal(P_after, P_A)}")
print(f"  pole coefficients now (c1, c2, c3) at one node: {w.disp['ez']['c1'][0, 0]:.6f}, "
      f"{w.disp['ez']['c2'][0, 0]:.6f}, {w.disp['ez']['c3'][0, 0]:.6e} (Drude: w0 = 0)")

print("== (2) removing an earlier body: an unchanged dispersive body after it ==")
w = world()
C = F.Medium(eps=2.0, label="C plain")
D = F.Medium(poles=[F.Lorentz(2.0, 1.0, 0.1)], label="D")
E = F.Medium(poles=[F.Debye(2.0, 0.3)], label="E")
b1 = w.add_body(F.Box((0.2, 0.2), (0.4, 0.4)), E)          # dispersive, index 1
b2 = w.add_body(F.Box((1.2, 0.6), (1.6, 1.4)), D)          # dispersive, index 2
w.advance(120)
idx_D = w.disp["ez"]["idx"].copy()
mid_D = w.disp["ez"]["mid"].copy()
selD = mid_D == 2
P_D = w.disp["ez"]["P"][selD].copy()
w.remove_body(b1)
sel_now = np.isin(w.disp["ez"]["idx"], idx_D[selD])
P_now = w.disp["ez"]["P"][sel_now]
print(f"  D's nodes: {selD.sum()}; |P| before the edit {np.abs(P_D).max():.4e}; after removing body {b1} (E): "
      f"{np.abs(P_now).max():.4e}  (docstring: kept, the medium did not change)")
_ = C

print("== (3) energy: 1/2 delta_eps |E|^2 and a lossless Lorentz medium in a closed PEC box ==")
w = F.FDTD((1.0, 1.0), 0.04, pol="tm", boundary="pec")
w.set_field("ez", lambda x, y: np.sin(np.pi * x) * np.sin(2 * np.pi * y))
w.add_body(F.Box((0.3, 0.3), (0.7, 0.7)), F.Medium(eps=2.0, poles=[F.Lorentz(1.0, 1.0, 0.0)]))
e = [w.energy()["total"]]
for _ in range(10):
    w.advance(200)
    e.append(w.energy()["total"])
e = np.array(e)
print(f"  energy()['total'] with a gamma = 0 Lorentz body: min/max over 2000 steps = {e.min() / e[0]:.4f} / "
      f"{e.max() / e[0]:.4f} of the start (the docstring: 'exactly conserved ... in a closed lossless box')")
