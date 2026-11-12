import sys, time
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness
for preset in sys.argv[1].split(","):
    for factor in (1.0, 10.0):
        h = Harness("p01_gravity", preset)
        speed = h.sim.default_speed * factor
        t0 = time.time(); worst = 0
        for k in range(30):
            a = time.time()
            h.run_to(h.sim.t + speed / 20.0)
            h.runner._frame(0.0)
            worst = max(worst, time.time() - a)
        n = sum(sum(m["counts"]) for m in h.of("trail"))
        print(preset, factor, f"{(time.time()-t0)/30*1e3:.1f} ms/frame worst {worst*1e3:.0f} ms trail points {n}", flush=True)
