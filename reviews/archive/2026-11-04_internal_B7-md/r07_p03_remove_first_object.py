"""p03: velocity_ks() (statistics and the Maxwell check) looks only at the engine's first species. Remove the first
particle object while another stays: the first species has no atoms left."""
import common  # noqa: F401
from harness import Harness


def run(h, ps, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + ps * 1e-12 * k / n)
        h.runner._frame(0.0)


h = Harness("p03_molecules", None, {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic"})
h.cmd("scene", op="add", type="gas", values={"n": 100, "T": 300.0, "x": 3.0, "y": 6.0, "sx": 5.0, "sy": 11.0})
h.cmd("scene", op="add", type="gas", values={"n": 100, "T": 300.0, "x": 9.0, "y": 6.0, "sx": 5.0, "sy": 11.0,
                                             "substance": "custom", "mass": 4.0})
run(h, 1.0, 20)
print("objects:", list(h.sim.objects), "; errors so far:", h.errors())
print("KS uses species:", h.sim.md.species()[0]["name"], "; n =", h.sim.md.velocity_ks()["n"], "of", 2 * h.sim.md.n)
first = list(h.sim.objects)[0]
try:
    h.cmd("scene", op="remove", id=first)
    run(h, 1.0, 20)
    print("after removing", first, ": errors:", h.errors())
except Exception as e:  # noqa: BLE001
    print("after removing", first, ": exception", type(e).__name__, e)
