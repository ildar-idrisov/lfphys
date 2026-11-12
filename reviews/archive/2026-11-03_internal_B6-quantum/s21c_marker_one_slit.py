"""s21 continued: the which-path preset with only the marked slit open (n_slits = 1, offset +5), and with only the
unmarked one (offset -5): the transmitted probability and, for the marked slit, the marker's P(1) of the transmitted
wave — to separate the marker's turning angle from the share of the marked slit in s21's P(1) = 0.246."""
import copy, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

for off in (5.0, -5.0):
    pr = copy.deepcopy(P.SCHEMA.presets["which_path"]["params"])
    for o in pr["scene"]["objects"]:
        if o["type"] == "slit_wall":
            o["values"].update({"n_slits": 1, "offset": off})
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    t = 0.0
    while qs.t < 14.5 - 0.02:
        t = min(t + sim.max_step(), 14.5 * P.TU)
        h.run_to(t)
    psi = qs.wave(1)
    X = qs.grid.axes[0]
    b = psi[:, X > 2.0, :].reshape(2, -1)
    r = b @ b.conj().T * qs.grid.dV
    print(f"slit at y = {off:+.0f}: kind {qs.particles[1].kind}; transmitted probability (x > 2) {np.trace(r).real:.4f}; "
          f"marker P(1) {r[1, 1].real / np.trace(r).real:.3f}, |coherence| {abs(r[0, 1]) / np.trace(r).real:.3f}")
