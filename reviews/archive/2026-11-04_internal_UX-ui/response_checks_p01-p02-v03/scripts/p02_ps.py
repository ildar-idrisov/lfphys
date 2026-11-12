import sys, time
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness
for preset in ("double_slit", "cyclotron", "ball_3d"):
    h = Harness("p02_quantum", preset)
    for i in range(3):
        t0 = time.perf_counter(); st = h.sim.palette_state(); dt = time.perf_counter() - t0
    t0 = time.perf_counter(); h.cmd("scene", op="add", type="box", values={"x": 20.0, "y": 20.0}); d2 = time.perf_counter() - t0
    print(preset, f"palette_state {dt*1e3:.0f} ms", st, f"add box total {d2*1e3:.0f} ms", flush=True)
