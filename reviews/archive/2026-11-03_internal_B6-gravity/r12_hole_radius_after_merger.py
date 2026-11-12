# Reviewer script (B6 gravity): the Newtonian "black hole" of p01 has the Schwarzschild radius of its mass as its
# capture radius; after it swallows a star the engine's equal-density merger rule gives it (R_hole^3 + R_star^3)^(1/3),
# i.e. about the star's radius. Preset hole_stars, run until the falling star is captured.
import sys

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from p01_gravity.viz import RS_AU, YR  # noqa: E402


def run(h, t_end, n=200):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


h = Harness("p01_gravity", "hole_stars")
nb = h.sim.mode.nb
i = nb.keys.index("o1")
print(f"before: hole mass {nb.masses()[i]:.6g} Msun, radius {nb.radii()[i]:.4e} au (Schwarzschild {nb.masses()[i] * RS_AU:.4e} au)")
for span in (0.05, 0.1, 0.2, 0.5, 1.0):
    run(h, span * YR, 100)
    if any(e.get("kind") == "merge" for e in h.of("event")):
        break
print("merges:", [e["text"] for e in h.of("event") if e.get("kind") == "merge"])
i = nb.keys.index("o1")
M = nb.masses()[i]
print(f"after: hole mass {M:.6g} Msun, radius {nb.radii()[i]:.4e} au = {nb.radii()[i] / (M * RS_AU):.1f} x its "
      f"Schwarzschild radius {M * RS_AU:.4e} au")
