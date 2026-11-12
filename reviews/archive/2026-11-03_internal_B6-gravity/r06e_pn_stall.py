# Reviewer script (B6 gravity): does the playground's default binary (all orders, quasi-circular start) ever reach its
# stop distance r_stop = 6? Start at r0 = 11 (q = 1 and q = 0.25) and follow it for a long time; also the preset
# pn_inspiral itself (r0 = 20) through the playground wrapper, sped up.
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from lfphys.core.gravity import pn_binary as PN  # noqa: E402

o = (1, 2, 2.5, 3.5)
for q in (1.0, 0.25):
    nu = q / (1 + q) ** 2
    st = PN.circular_state(11.0, nu, o, quasi=True)
    print(f"q = {q}: start r0 = 11")
    for t_end in (2e3, 5e3, 1e4, 2e4, 4e4):
        res = PN.integrate(st, t_end, nu, o, n_out=401, r_stop=6.0)
        r = np.linalg.norm(res["x"], axis=1)
        last = r[-100:]
        E = float(PN.energy(res["x"][-1], res["v"][-1], nu, 2))
        print(f"   t = {t_end:7.0f}: status {res['status']}, r over the last quarter {last.min():.4f}..{last.max():.4f}, "
              f"E/mu = {E:.6f}", flush=True)

from harness import Harness  # noqa: E402


def run(h, t_end, n=200):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


h = Harness("p01_gravity", "pn_inspiral")
T = h.sim.mode.T
for span in (2e4, 4e4, 6e4, 8e4):
    run(h, span * T, 400)
    b = h.sim.mode.bin
    r = float(np.linalg.norm(b["st"]["x"]))
    ev = [e["text"][:60] for e in h.of("event") if e.get("kind") == "merger"]
    c = h.checks().get("balance", {})
    print(f"preset pn_inspiral at t = {span:.0f} m: r = {r:.4f}, status {b['status']}, merger events {ev}, "
          f"balance check value {c.get('value')} ok {c.get('ok')} tol {c.get('tol')}", flush=True)
