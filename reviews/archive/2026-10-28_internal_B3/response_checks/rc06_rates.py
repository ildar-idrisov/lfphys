import sys, time
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_tracks": 20}
dev = sys.argv[1]
cases = ([("narrow", {"n_bohm": 100}), ("narrow", {"n_bohm": 2000}), ("mark180", {"n_bohm": 2000})] if dev == "gpu"
         else [("narrow", {**SMALL, "n_bohm": 100}), ("narrow", {**SMALL, "n_bohm": 1000})])
for preset, extra in cases:
    t0 = time.time()
    h = Harness("v11_double_slit_2d", preset, extra)
    s = h.sim
    while not s.done:
        h.run_to(s.t + 2.0 * s.tunit)
    T = time.time() - t0
    print(f"{dev} {preset} N={extra['n_bohm']} spinor={s.spinor} points {s.g.size} pairs {s.n_pairs} (est {s.t_end_est / s.pair:.0f}) "
          f"total {T:.1f} s = {T / s.n_pairs * 1e3:.1f} ms/pair; estimate {s.est_cost:.0f} s", flush=True)
