import sys, time
sys.path[:0] = ["/lf/visualizations/tests", "/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from harness import Harness
import p04_fluids.viz as P
for preset in ("cylinder_re20", "karman"):
    for frame_s in (0.04, 10.0):
        P.FRAME_S = frame_s
        h = Harness("p04_fluids", preset)
        dt = h.sim.fl.units.dt
        t0 = time.perf_counter()
        h.run_to(h.sim.t + 600 * dt)
        print(preset, "FRAME_S", frame_s, "steps/call", round(h.sim.max_step() / dt), "600 steps:", round(time.perf_counter() - t0, 2), "s", flush=True)
