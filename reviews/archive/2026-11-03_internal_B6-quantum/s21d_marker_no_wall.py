"""s21 continued: is the marker's smaller turn in the slit (s21c: P(1) = 0.55, ~48 deg, against 86 deg for the 1-D
slab, s21b) a property of the slit or of the 2-D marker itself? The which-path preset without the wall: the wave that
crossed the marker region (x > 2, 4.5 < y < 5.5) at t = 10; and the same marker region as a slab uniform in y
(sy = 0, the engine test's geometry) in the same 2-D window."""
import copy, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

for label, sy in (("marker box 3 x 3 nm, no wall", 3.0), ("marker slab (uniform in y), no wall", 0.0)):
    pr = copy.deepcopy(P.SCHEMA.presets["which_path"]["params"])
    objs = []
    for o in pr["scene"]["objects"]:
        if o["type"] == "slit_wall":
            continue
        if o["type"] == "marker":
            o["values"]["sy"] = sy
        objs.append(o)
    pr["scene"]["objects"] = objs
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    t = 0.0
    while qs.t < 10.0 - 0.02:
        t = min(t + sim.max_step(), 10.0 * P.TU)
        h.run_to(t)
    psi = qs.wave(1)
    X, Y = qs.grid.axes
    m = (X[:, None] > 2.0) & (np.abs(Y[None, :] - 5.0) < 0.5)
    b = psi[:, m]
    r = b @ b.conj().T
    print(f"{label}: marker P(1) of the wave that crossed it (x > 2, |y - 5| < 0.5): {r[1, 1].real / np.trace(r).real:.3f}")
