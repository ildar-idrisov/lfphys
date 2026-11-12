import sys
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"]
from harness import Harness
p = {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0}
h = Harness("v12_arrival_times_2d", None, p)
hd = h.of("header")[-1]
live = h.sim.live_values()
print("live_values:", sorted(live))
# what the player sends for «Начать новый мир» without a scenario: header params + live values + the form
h.cmd("new_world", params={**hd["params"], **live})
print("worlds:", [m["world"] for m in h.of("header")], "errors:", h.errors()[-1:])
