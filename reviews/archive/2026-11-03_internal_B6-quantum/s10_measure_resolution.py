"""Q: an unsharp position measurement with the smallest resolution the scene (and the wrapper's action) admits,
sigma = d: is the post-measurement wave resolved by the grid, and is the time step still adequate? The wrapper does
not re-tune dt after an action (_tune is called only after scene changes).

The double-slit preset's electron (lambda = 2 nm, sigma (2.5, 4) nm, d = 0.3125 nm) measured at sigma = d, 2 d and
the action's default max(1, 2d); after the measurement: the grid check (probability in the outer third of k-space),
the packet admission rule applied to the new width (|k| + 6 sigma_k <= pi/d), the companion's local step error
before and after, and the kinetic phase per step."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
for o in pr["scene"]["objects"]:
    if o["type"] == "packet":
        o["values"]["bohm"] = 0
for sig in (0.3125, 0.625, 1.0):
    h = Harness("p02_quantum", None, pr, seed=2)
    sim, qs = h.sim, h.sim.qs
    d = qs.grid.d[0]
    before = qs.step_error()[1]["local"]
    tail0 = qs.checks()[1]["spectral_tail"]
    h.action("measure", particle="o4", sigma=sig)
    ev = [e for e in h.of("event") if e.get("name") == "measure"]
    err = h.errors()
    c = qs.checks(error=True)[1]
    psi = qs.wave(1)
    F = np.fft.fftn(psi)
    K = qs.grid.kmesh()
    k2 = (K[0] ** 2 + K[1] ** 2)
    w = np.abs(F) ** 2
    Ekin = float(np.sum(k2 * w) / np.sum(w)) / 2
    s_post = 1 / math.sqrt(1 / 2.5**2 + 1 / sig**2)
    rule = math.pi + 6 / (2 * s_post) <= math.pi / d
    print(f"sigma = {sig:.4f} nm (= {sig / d:.2f} d): errors {err}; spectral tail before {tail0:.2e}, after "
          f"{c['spectral_tail']:.2e}; packet rule |k| + 6 sigma_k <= pi/d for the new width {s_post:.3f}: {rule}; "
          f"companion local error before {before:.2e}, after {c['step_error']['local']:.2e}; <E_kin> dt after "
          f"{Ekin * qs.dt:.3f} rad (dt {qs.dt}, unchanged)")
