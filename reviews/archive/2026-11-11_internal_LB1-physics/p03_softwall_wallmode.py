# Reviewer's check: p03's box changed in «wall» mode next to a SOFT wall: the engine books work (the wall's potential
# under the atoms near it changes), the event says «работы над системой нет». Run in Docker from engine/ (REVIEW.md).
import sys
sys.path[:0] = ["/lf/visualizations/tests", "/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys"]
from harness import Harness  # noqa: E402

h = Harness("p03_molecules", None, {"dim": "2d", "Lx": 6.0, "Ly": 6.0, "boundary": "walls"})
h.cmd("scene", op="add", type="wall", values={"axis": "y", "side": "hi", "kind": "soft"})
h.cmd("scene", op="add", type="gas", values={"n": 80, "T": 150.0, "x": 3.0, "y": 2.8, "sx": 5.0, "sy": 4.4})
print("errors so far:", h.errors())
for k in range(1, 6):
    h.run_to(h.sim.t + 2e-12 * k / 5)
    h.runner._frame(0.0)
md = h.sim.md
print("walls:", {k: w["kind"] for k, w in md.walls().items()})
E0, W0 = md.energy(), md.energy_balance()["W_box"]
h.set(box_mode="wall", Ly=6.15)
print("errors:", h.errors())
print("energy change", md.energy() - E0, "W_box change", md.energy_balance()["W_box"] - W0, "(reduced units, epsilon)")
print("event:", h.of("event")[-1]["text"])
