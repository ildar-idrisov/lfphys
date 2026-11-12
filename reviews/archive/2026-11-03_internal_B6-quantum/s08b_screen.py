"""The double-slit preset's screen (x = 30, 4 nm thick, edge 3 nm, W0 chosen by _auto_W): reflection R and leak T
separately over the packet's waves (README: "the 3-nm-edged screen 1e-11 (with a 1 nm edge it reflected 1.6 %)")."""
import copy, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core.quantum import scene as QS
from p02_quantum import viz as P

for edge in (3.0, 1.0):
    pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
    for o in pr["scene"]["objects"]:
        if o["type"] == "packet":
            o["values"]["bohm"] = 0
        if o["type"] == "detector":
            o["values"]["edge"] = edge
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    for oid, (kind, qid) in sim.ref.items():
        ob = qs.objects.get(qid) if kind == "object" else None
        if isinstance(ob, QS.Detector):
            for k, m in sim._waves():
                R, T = ob.reflection([k], m, axis=0)
                print(f"screen edge {edge} nm, W0 {ob.strength * P.EV:.3g} eV: k = {k:.3f}: R = {R[0]:.2e}, T = {T[0]:.2e}")
