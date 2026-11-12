"""R02: the playground p04 through the test harness: (a) the default laws (no preset) build a world or are refused;
(b) a world from a scene file: the engine's time after the first advances (Flow2D.t was set without Flow2D.steps);
(c) gravity next to an outlet, control with all walls.

Run (from engine/): docker run --rm --name lf-b7rl-r02 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests
-w /lf/lfphys light-funnel-viz python3 /out/r02_playground_world_and_scene_time.py
"""
import numpy as np

from harness import Harness
from lfphys.core.fluids import lbm

V = "p04_fluids"

print("=== (a) the default laws, no preset ===")
try:
    h = Harness(V, None, {})
    print("built; errors:", h.errors()[:3])
except Exception as e:  # noqa: BLE001
    print("refused:", type(e).__name__, str(e)[:300])

print()
print("=== (b) a world from a scene file (karman preset exported at t ~ 0.2 s) ===")
h = Harness(V, "karman", {})
for k in range(1, 3):
    h.run_to(0.1 * k)
    h.runner._frame(0.0)
h.cmd("scene", op="export")
sc = h.of("scene_export")[-1]["scene"]
print("scene time:", sc["t"])
h2 = Harness(V, None, {**sc["laws"], "scene": sc})
fl = h2.sim.fl
print("after load: sim.t = %.6g, fl.t = %.6g, fl.steps = %d, dt = %.4g, inlet t0 = %.6g" % (h2.sim.t, fl.t, fl.steps,
                                                                                         fl.units.dt, fl._inlet_t0))
for k in range(1, 4):
    tt = sc["t"] + 0.01 * k
    h2.run_to(tt)
    h2.runner._frame(0.0)
    print("run_to(%.4f): sim.t = %.6g, fl.t = %.6g, fl.steps = %d (steps expected from the file's time: %d), inlet scale "
          "at fl.t: %.4g" % (tt, h2.sim.t, fl.t, fl.steps, round(0.01 * k / fl.units.dt), fl._inlet_scale(fl.t)))
print("errors:", h2.errors()[:3])

print()
print("=== (c) gravity (0, -0.5) at rest: with an outlet on the right, and the control with walls only ===")
for sides in ({"left": lbm.Wall(), "right": lbm.Outlet(0.0)}, {}):
    fl = lbm.Flow2D((0.4, 0.1), 0.002, nu=1e-3, rho=1.0, u_max=0.05, mach=0.1, device="cpu", sides=sides)
    fl.set_gravity((0.0, -0.5))
    fl.advance_to(20.0)
    ux, uy = fl.velocity()
    sp = np.hypot(ux, uy)
    i, j = np.unravel_index(np.nanargmax(sp), sp.shape)
    print("sides %s: max |u| = %.4g m/s at x = %.3f m, y = %.3f m; mean |u| = %.4g m/s" % (
        {k: v.KIND for k, v in fl._sides.items()}, sp[i, j], fl.x[i], fl.y[j], np.nanmean(sp)))
