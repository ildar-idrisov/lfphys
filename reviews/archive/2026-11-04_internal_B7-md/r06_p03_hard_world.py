"""p03 with hard disks (preset "hard_disks: давление против уравнения состояния"):
(a) the pressure in the statistics: emit_stats reads P.get("collision"), a key HardSpheres.pressure() does not have;
(b) the checks shown (is there any pressure / equation-of-state check?);
(c) changing an object's number of atoms (remove + add of the same object id) in the hard world;
(d) a crystal block in a region: HardSpheres.fill(density=...) counts the atoms over the whole box."""
import common  # noqa: F401
from harness import Harness


def run(h, ps, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + ps * 1e-12 * k / n)
        h.runner._frame(0.0)


h = Harness("p03_molecules", "hard_disks")
run(h, 6.0, 60)
st = h.of("stats")
print("(a) stats messages:", len(st), "; pressure values p:", sorted({repr(s.get("p")) for s in st}))
print("    engine pressure():", {k: v for k, v in h.sim.md.pressure().items() if k in ("pressure", "Z", "T")})
print("(b) checks:", {k: (c.get("label"), c.get("ok"), c.get("info"), c.get("value")) for k, c in h.checks().items()})
ne = len(h.errors())
h.cmd("scene", op="set", id="o1", values={"n": 300})
print("(c) set n = 300:", h.errors()[ne:], "; atoms now", h.sim.md.n)
ne = len(h.errors())
h2 = Harness("p03_molecules", None, {"dim": "2d", "model": "hard", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic"})
h2.cmd("scene", op="add", type="crystal", values={"density": 0.7, "T": 300.0, "x": 6.0, "y": 6.0, "sx": 4.0,
                                                  "sy": 4.0})
print("(d) hard crystal 4 x 4 nm at density 0.7 in a 12 x 12 nm box:", h2.errors(), "; atoms", h2.sim.md.n,
      "; expected about", round(0.7 * (4.0 / 0.3405) ** 2))
h3 = Harness("p03_molecules", None, {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic"})
h3.cmd("scene", op="add", type="crystal", values={"density": 0.7, "T": 30.0, "x": 6.0, "y": 6.0, "sx": 4.0,
                                                  "sy": 4.0})
print("    control, the same with LJ:", h3.errors(), "; atoms", h3.sim.md.n)
