"""The preset "which_path" ("Метка пути в одной щели: интерференция гаснет"): the screen's absorbed record per y with the
marker and without it (the marker removed), the fringe visibility near the centre, and the marker's state of the
transmitted wave (the marker's P(1) and coherence when the wave has passed the wall)."""
import copy, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core import backend
from p02_quantum import viz as P

prof = {}
for marker in (True, False):
    pr = copy.deepcopy(P.SCHEMA.presets["which_path"]["params"])
    if not marker:
        pr["scene"]["objects"] = [o for o in pr["scene"]["objects"] if o["type"] != "marker"]
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    t = 0.0
    note = ""
    while qs.t < 40.0 - 0.02:
        t = min(t + sim.max_step(), 40.0 * P.TU)
        h.run_to(t)
        if marker and not note and qs.t > 14.0:
            psi = qs.wave(1)
            X = qs.grid.axes[0]
            beyond = psi[:, X > 2.0, :].reshape(2, -1)
            r = beyond @ beyond.conj().T
            r = r / np.trace(r).real
            note = f"transmitted wave at t = {qs.t:.1f}: marker P(1) = {r[1, 1].real:.3f}, |coherence| {abs(r[0, 1]):.3f}"
    det = [k for k in qs.absorbed(1) if k.startswith("detector")][0]
    u = qs._arr["u"][det]
    acc = backend.to_numpy(qs.particles[1].acc)
    if acc.ndim == 2:
        prof[marker] = np.sum(acc * u, axis=0)
    y = qs.grid.axes[1]
    print(f"marker {marker}: absorbed {qs.absorbed(1)}; {note}")
for marker in (True, False):
    p = prof[marker]
    sel = np.abs(y) < 6
    mx, mn = float(p[sel].max()), float(p[sel].min())
    print(f"marker {marker}: visibility near the centre (|y| < 6 nm) {(mx - mn) / (mx + mn):.3f}")
