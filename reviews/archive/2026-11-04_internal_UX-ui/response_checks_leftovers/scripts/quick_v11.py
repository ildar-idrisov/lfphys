import sys
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"]
from harness import Harness
SMALL = {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse", "n_bohm": 300, "n_tracks": 20}
h = Harness("v11_double_slit_2d", "narrow", SMALL)
print("live", h.sim.live_values())
h.set(a=2.0)
print([m["text"] for m in h.of("event")][-1:])
print("errors", h.errors())
h.set(d=40.0)
print("errors", h.errors()[-1:])
h.set(w=30.0)
h.set(V0=6.0)
print("errors", h.errors()[-1:])
print([m["text"] for m in h.of("event")][-1:])
tu = h.sim.tunit
h.run_to(h.sim.t + 3 * tu)
h.set(w=2.0)
print([m["text"] for m in h.of("event")][-1:])
print(h.of("setup")[-1]["geometry"])
g = Harness("v12_arrival_times_2d", None, {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0})
print("v12 live", g.sim.live_values())
g.set(mu_w=3.0)
print([m["text"] for m in g.of("event")][-1:], g.errors())
g.set(a=3.0)
print(g.errors()[-1:])
g.set(W0=2.0)
print([m["text"] for m in g.of("event")][-1:], g.errors()[-1:])
