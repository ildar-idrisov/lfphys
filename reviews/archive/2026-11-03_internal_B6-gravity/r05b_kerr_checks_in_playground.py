# Reviewer script (B6 gravity): (a) every "check" message the playground emits during the preset kerr_orbits (the
# p01 test looks only at the last message of each check); (b) the linear growth of Carter's K drift of one body
# against the playground's tolerance 10 rtol sqrt(steps), run until the two cross.
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from lfphys.core.gravity import kerr_newman as KN  # noqa: E402


def run(h, t_end, n=200):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


print("(a) preset kerr_orbits, 200 M in 2000 frames: every emitted check with ok = False")
h = Harness("p01_gravity", "kerr_orbits")
run(h, 200 * h.sim.mode.T, 2000)
bad = [(round(m["t"] / h.sim.mode.T, 2), m["id"], m["value"], m["tol"]) for m in h.of("check") if m.get("ok") is False]
print(f"  {len(h.of('check'))} check messages, {len(bad)} failed:")
for b in bad[:20]:
    print("   t = %s M  %s  value %.3e  tol %.3e" % b)
print("  last message per check (what the p01 test asserts on):",
      {k: v.get("ok") for k, v in h.checks().items()})

print()
print("(b) one inclined orbit at r ~ 20 (a = 0.9, q = 0.3, rtol 1e-10): relative K drift vs 10 rtol sqrt(steps)")
g = KN.Geodesics(0.9, 0.3, rtol=1e-10, capture_eps=1e-4, r_escape=2e3)
g.add_body(20.0, 1.0, 0.0, v=(0.0, 0.05, 0.2), key="wide")
t0 = time.time()
for T in (1e4, 1e5, 1e6, 2e6, 4e6, 8e6):
    g.advance(T)
    c = g.constants()
    K0 = c["K"][0] - c["dK"][0]
    dK = abs(c["dK"][0]) / max(abs(K0), 1.0)
    n = int(c["steps"][0])
    tol = 10 * g.rtol * math.sqrt(n)
    print(f"  t = {T:9.0f} M  steps {n:7d}  K0 = {K0:.4f}  dK_rel = {dK:.3e}  tol = {tol:.3e}  "
          f"fails: {dK > tol}  dK per step {dK / n:.2e}  wall {time.time() - t0:.0f} s", flush=True)
    if time.time() - t0 > 400:
        break
